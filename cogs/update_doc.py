import discord
from discord.ext import commands
from core.omi_docs_downloader import download_omi_docs
from core.index_doc import index_docs

class UpdateDoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def update_doc(self, ctx, force: bool = True):
        """Update docs from GitHub. Use `$update_doc true` to force refresh."""
        try:
            download_omi_docs(force_update=force)
            index_docs()

            embed = discord.Embed(
                title="✅ Doc Update Complete",
                description="Successfully pulled latest docs from GitHub.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Failed to update docs: {str(e)}")

async def setup(bot):
    await bot.add_cog(UpdateDoc(bot))
