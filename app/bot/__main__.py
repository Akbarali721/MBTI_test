import asyncio
import logging

from app.bot.handlers import run_bot
from app.observability import configure_logging, init_sentry

# Bot alohida jarayon: veb ilova bilan bir xil log formati va xato kuzatuvi kerak,
# aks holda to'lov oqimidagi xatolar Sentry'ga umuman tushmaydi.
configure_logging()
init_sentry()

logger = logging.getLogger(__name__)


def main() -> None:
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot to‘xtatildi")


if __name__ == "__main__":
    main()
