from discord.ext import commands
import discord
from discord import app_commands 


from view.modal.issue_modal import IssueModal

class Issue(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.index = 0

    @app_commands.command(name="issue", description="issue report")
    async def announce(self, interaction: discord.Interaction):
        """ /issue """
        modal = IssueModal()
        await interaction.response.send_modal(modal)
                

async def setup(bot):
    await bot.add_cog(Issue(bot))