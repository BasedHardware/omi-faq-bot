import discord
from discord.ext import commands
import os
from core.indexer import FAQIndexer

class Faq(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.indexer = FAQIndexer()

    @commands.command()
    @commands.is_owner()
    async def reload_index(self, ctx):
        """Reloads the FAQ index."""
        if self.indexer.load_index():
            await ctx.send("✅ FAQ index reloaded successfully.")
        else:
            await ctx.send("❌ Error reloading FAQ index.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message):
            question = message.content
            for mention in [f'<@{self.bot.user.id}>', f'<@!{self.bot.user.id}>']:
                question = question.replace(mention, '')
            question = question.strip()

            if not question and message.reference:
                try:
                    tagged_message = await message.channel.fetch_message(message.reference.message_id)
                    question = tagged_message.content
                except:
                    pass

            if question:
                results = await self.indexer.search(question)

                if results:
                    best_result = results[0]
                    embed = discord.Embed(
                        title="💡 Answer",
                        description=best_result['answer'],
                        color=self._get_confidence_color(best_result['score'])
                    )
                    embed.add_field(
                        name="Matched Question",
                        value=best_result['question'],
                        inline=False
                    )
                    embed.set_footer(text=f"Confidence: {best_result['score']:.2f} ({best_result['confidence']})")
                    await message.reply(embed=embed)
                else:
                    embed = discord.Embed(
                        title="❓ No Answer Found",
                        description="I couldn't find a relevant answer to your question. Please try rephrasing or ask a different question.",
                        color=discord.Color.orange()
                    )
                    embed.set_footer(text="Tip: Try using different keywords or be more specific.")
                    await message.reply(embed=embed)
            elif not self.indexer.get_stats()['index_loaded']:
                await message.reply("⚠️ The FAQ index is not loaded. Please ask an admin to run the `!index` command.")

    def _get_confidence_color(self, score):
        if score > 0.8:
            return discord.Color.green()
        elif score > 0.6:
            return discord.Color.blue()
        else:
            return discord.Color.yellow()

    @commands.command(name="faq")
    async def faq_search(self, ctx, *, query: str = None):
        """Search the FAQ database"""
        if not query:
            await ctx.send("Please provide a search query. Example: `!faq what is omi`")
            return

        if not self.indexer.get_stats()['index_loaded']:
            await ctx.send("⚠️ The FAQ index is not loaded. Please run the `!index` command first.")
            return

        results = await self.indexer.search(query)

        if results:
            embed = discord.Embed(
                title="🔍 FAQ Results",
                color=discord.Color.blue()
            )
            for result in results:
                embed.add_field(
                    name=f"Q: {result['question']} (Score: {result['score']:.2f})",
                    value=f"A: {result['answer'][:1024]}",
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❓ No matching FAQ entry found. Try different keywords!")

async def setup(bot):
    await bot.add_cog(Faq(bot))
