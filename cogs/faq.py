import discord
from discord.ext import commands
import os
from core.indexer import FAQIndexer
from core.llm import LLMService
import tomli


with open("model.toml", "rb") as f:
    model_config = tomli.load(f)


class Faq(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.indexer = FAQIndexer()
        self.llm = LLMService()


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
                results = await self.indexer.search(question, top_k=5)

                if results:
                    context = "\n".join([f"Question: {r['question']}\nAnswer: {r['answer']}" for r in results])
                    #print(context)
                    llm_answer = self.llm.generate_answer(question, context)
                    
                    embed = discord.Embed(
                        title="💡 Answer",
                        description=llm_answer,
                        color=discord.Color.blue()
                    )
                    
                    await message.reply(embed=embed)


                ## When no context is returned 
                else:
                    context = model_config["unmatched_queries"]

                    llm_answer = self.llm.generate_answer(question, context)
                    embed = discord.Embed(
                        title="Generalized Answer",
                        description=llm_answer,
                        color=discord.Color.orange()
                    )
                    embed.set_footer(text="Tip: Try using different keywords for a more specific reply or contact the support team.")

                    await message.reply(embed=embed)
            elif not self.indexer.get_stats()['index_loaded']:
                await message.reply("⚠️ The FAQ index is not loaded. Please ask an admin to run the `!index` command.")


async def setup(bot):
    await bot.add_cog(Faq(bot))
