import discord
from discord.ext import commands
from core.indexer import FAQIndexer
from core.query_doc import DocSearcher
from core.llm import LLMService
import tomli
import asyncio
import logging
import re

logger = logging.getLogger(__name__)

with open("model.toml", "rb") as f:
    model_config = tomli.load(f)


def extract_url(text):
    """Extract the first URL from text"""
    url_pattern = r'https?://[^\s\)\]`]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

class Faq(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.indexer = FAQIndexer()
        self.doc_searcher = DocSearcher()
        self.llm = LLMService()


    @commands.command()
    @commands.is_owner()
    async def reload_index(self, ctx):
        """Reloads the FAQ and Document indexes."""
        faq_reloaded = await self.indexer.load_index()
        if faq_reloaded:
            await ctx.send("✅ FAQ index reloaded successfully.")
        else:
            await ctx.send("❌ Error reloading FAQ index.")

        try:
            self.doc_searcher.reload()
            await ctx.send("✅ Document index reloaded successfully.")
        except Exception as e:
            await ctx.send(f"❌ Error reloading document index: {e}")

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
                results_doc = self.doc_searcher.search(question)
                results = await self.indexer.search(question, top_k=5)

                if results_doc or results:

                    context_json = "\n".join([f"Question: {r['question']}\nAnswer from json: {r['answer']}" for r in results])
                    
                    context_doc = "\n".join([
                                f"Document: {r['filename']}\nExcerpt: {r['text']}"
                                for r in results_doc
                            ])

                    llm_answer = self.llm.generate_answer(question, context_doc, context_json)
                    
                    embed = discord.Embed(
                        title="💡 Answer",
                        description=llm_answer,
                        color=discord.Color.blue()
                    )
                    

                    # Check for URL and add field only if it exists
                    url = extract_url(llm_answer)

                    if url:
                        embed.add_field(
                            name="🔗",
                            value=f"[Link]({url})",
                            inline=True
                        )

                    await message.reply(embed=embed)

                
                elif not question:
                    pass

                ## When no context is returned
                else:

                    context = model_config["unmatched_queries"]

                    llm_answer = self.llm.generate_answer(question, context, context)

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
                        await asyncio.sleep(10)  # Wait 10 seconds
                        await message.reply(f"<@{mod_id}> - A user needs your assistance. **Please update `FAQ.json` with the new information if needed.**")

            elif not self.indexer.get_stats()['index_loaded']:
                await message.reply("⚠️ The FAQ index is not loaded. Please ask an admin to run the `$index` command.")


async def setup(bot):
    await bot.add_cog(Faq(bot))