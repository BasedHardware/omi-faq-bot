import discord
from discord.ext import commands
from core.indexer import FAQIndexer
from core.llm import LLMService
import tomli
import asyncio



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


                
                elif not question:
                    pass

                ## When no context is returned
                else:

                    context = model_config["unmatched_queries"]

                    llm_answer = self.llm.generate_answer(question, context)

                    # Check if LLM suggests mentioning Moderator
                    mention_moderator = "[MENTION_MODERATOR]" in llm_answer
                    llm_answer = llm_answer.replace("[MENTION_MODERATOR]", "").strip()


                    embed = discord.Embed(
                        title="OMI",
                        description=llm_answer,
                        color=discord.Color.orange()
                    )
                    embed.set_footer(text="Tip: Try using different keywords for a more specific reply or contact the support team.")
                    
                    await message.reply(embed=embed)

                    mod_id = model_config["MODERATOR_ID"]
                    if (mention_moderator): 
                        await asyncio.sleep(20)  # Wait 20 seconds
                        await message.reply(f"<@{mod_id}> - A user needs your assistance. **Please update `FAQ.json` with the new information if needed.**")

            elif not self.indexer.get_stats()['index_loaded']:
                await message.reply("⚠️ The FAQ index is not loaded. Please ask an admin to run the `$index` command.")


async def setup(bot):
    await bot.add_cog(Faq(bot))
