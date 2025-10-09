from discord.ext import commands
import discord
import asyncio

# bot_configs = BotConfigs()

import logging
from rich.logging import RichHandler

logging.basicConfig(format="::: %(message)s", handlers=[RichHandler()])
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OmiDiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        description = """Omi Discord bot """
        super().__init__(
            command_prefix=commands.when_mentioned_or("$"),
            intents=intents,
            description=description,
        )

    async def setup_hook(self) -> None:
        from .omi_docs_downloader import download_omi_docs
        from .index_doc import index_docs
        import functools

        # Run synchronous function in thread-safe way
        loop = asyncio.get_running_loop()
        logger.info("Downloading OMI docs on startup...")
        # Use functools.partial to pass keyword argument to executor
        func = functools.partial(download_omi_docs, force_update=False)
        await loop.run_in_executor(None, func)
        logger.info("Indexing OMI docs on startup...")
        await loop.run_in_executor(None, index_docs)
        logger.info("Doc download and indexing complete.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")
        logger.info("------")
        logger.info("------")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """Handles all command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
