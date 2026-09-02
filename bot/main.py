"""Telegram bot kirish nuqtasi: python -m bot.main"""

from __future__ import annotations

import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher

from app.bot.handlers import check_bot_configuration, on_unhandled_error, router as legacy_router
from app.bot.outbox_worker import run_worker
from app.config import settings
from app.observability import configure_logging, init_sentry
from bot.handlers.contact import router as contact_router
from bot.handlers.start import router as start_router

configure_logging()
init_sentry()

logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    from app.bot import test_flow

    dp = Dispatcher()
    # Yangi Instagram voronkasi handlerlari birinchi.
    dp.include_router(start_router)
    dp.include_router(contact_router)
    dp.include_router(test_flow.router)
    # To'lov cheklari va premium deeplink (start alohida qoplangan).
    dp.include_router(legacy_router)
    dp.errors.register(on_unhandled_error)
    return dp


async def run_bot() -> None:
    token = settings.bot_token or settings.telegram_bot_token
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN yoki BOT_TOKEN sozlanmagan")

    bot = Bot(token=token)
    worker: asyncio.Task[None] | None = None
    try:
        for problem in await check_bot_configuration(bot):
            logger.warning("Bot sozlamasi ogohlantirishi: %s", problem)
        dp = create_dispatcher()
        worker = asyncio.create_task(run_worker(bot))
        await dp.start_polling(bot)
    finally:
        if worker is not None:
            worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await worker
        await bot.session.close()


def main() -> None:
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot to‘xtatildi")


if __name__ == "__main__":
    main()
