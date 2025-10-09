import discord
from discord.ext import commands
from core.omi_docs_downloader import download_omi_docs
from core.index_doc import index_docs
import asyncio

class UpdateDoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def update_doc(self, ctx, force: bool = False):
        """Update docs from GitHub. Use `$update_doc true` to force refresh."""
        await ctx.send("⏳ Starting doc update... (this may take a moment)")
        try:
            import functools
            # Run blocking functions in an executor to avoid freezing the bot
            loop = asyncio.get_running_loop()
            func = functools.partial(download_omi_docs, force_update=force)
            await loop.run_in_executor(None, func)
            await ctx.send("✅ Docs downloaded, now indexing...")
            await loop.run_in_executor(None, index_docs)

            # Reload the index in the Faq cog
            faq_cog = self.bot.get_cog("Faq")
            if faq_cog and hasattr(faq_cog, 'doc_searcher'):
                faq_cog.doc_searcher.reload()
                await ctx.send("✅ Document index reloaded in bot.")

            embed = discord.Embed(
                title="✅ Doc Update Complete",
                description="Successfully pulled latest docs from GitHub and re-indexed.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Failed to update docs: {e}")

async def setup(bot):
    await bot.add_cog(UpdateDoc(bot))