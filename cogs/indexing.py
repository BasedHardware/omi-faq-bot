import discord
from discord.ext import commands
import os
from core.indexer import FAQIndexer

# Get the absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Indexing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.indexer = FAQIndexer()

    @commands.command()
    @commands.is_owner()
    async def index(self, ctx):
        """Indexes the FAQ data using Sentence Transformers."""
        try:
            # The index creation is now handled by the FAQIndexer class
            if self.indexer.create_index():
                stats = self.indexer.get_stats()
                embed = discord.Embed(
                    title="✅ Indexing Complete",
                    description=f"Successfully indexed {stats['documents']} FAQ entries with Sentence Transformers!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Documents", value=stats['documents'], inline=True)
                embed.add_field(name="Algorithm", value="Sentence Transformers", inline=True)
                embed.set_footer(text="Ready to answer questions!")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ An error occurred during indexing.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred during indexing: {str(e)}")

    @commands.command()
    @commands.is_owner()
    async def test_index(self, ctx, *, query: str = None):
        """Test the index with a sample query"""
        if not query:
            await ctx.send("Please provide a query to test. Example: `!test_index what is omi`")
            return

        try:
            results = await self.indexer.search(query)

            embed = discord.Embed(
                title="🔍 Index Test Results",
                description=f"Query: **{query}**",
                color=discord.Color.blue()
            )

            if not results:
                embed.description += "\n\nNo relevant results found."
            else:
                for i, result in enumerate(results, 1):
                    embed.add_field(
                        name=f"{i}. Score: {result['score']:.2f} - Confidence: {result['confidence']}",
                        value=f"**Q:** {result['question']}\n**A:** {result['answer'][:100]}...",
                        inline=False
                    )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error testing index: {str(e)}")

async def setup(bot):
    await bot.add_cog(Indexing(bot))