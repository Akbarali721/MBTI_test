import asyncio
import logging

from app.bot.handlers import run_bot

logging.basicConfig(level=logging.INFO)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
