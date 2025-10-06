import discord
import asyncio
from github import Github, Auth
import tomli
from dotenv import load_dotenv
import logging
import os


load_dotenv()
Gtoken = os.getenv('GITHUB_ACCESS_TOKEN')
if not Gtoken:
    logging.error("GITHUB ACCESS TOKEN not found in .env file.")
    exit()

with open("config.toml", "rb") as f:
    config = tomli.load(f)

GITHUB_ACCESS_TOKEN=Gtoken

REPO_OWNER = config["REPO_OWNER"]
REPO_NAME = config["REPO_NAME"]



class IssueModal(discord.ui.Modal, title="Omi Issue Report"):
    IssueTitle = discord.ui.TextInput(
        label="Issue Title",
        style=discord.TextStyle.short,
        required=True,
        max_length=100,
    )
    
    IssueDes = discord.ui.TextInput(
        label="Issue Description",
        style=discord.TextStyle.long,
        required=True,
        max_length=300,
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        
        # Defer the response immediately to avoid timeout
        await interaction.response.defer(ephemeral=True)
        
        # Initialize with new auth method
        auth = Auth.Token(GITHUB_ACCESS_TOKEN)
        g = Github(auth=auth)

        # Get the repository
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")


        # Create an issue
        issue = repo.create_issue(
            title=self.IssueTitle.value,
            body=f"## Description\n\n{self.IssueDes.value}\n\n## Reported by\nDiscord User: {interaction.user.name} (ID: {interaction.user.id})"
        )
        
        
        issue_chn = discord.utils.get(
            interaction.guild.channels, id=1053524659200610385)
        
        # Embed
        embed = discord.Embed(
            title=f"🐛 {self.IssueTitle.value}",
            description=f"**Issue #{issue.number}** has been created on GitHub",
            color=discord.Colour(0x238636),  # GitHub green color
            url=issue.html_url
        )
        
        embed.add_field(
            name="📝 Description", 
            value=self.IssueDes.value[:200] + "..." if len(self.IssueDes.value) > 200 else self.IssueDes.value,
            inline=False
        )
        
        embed.add_field(
            name="🔢 Issue Number",
            value=f"#{issue.number}",
            inline=True
        )
        
        embed.add_field(
            name="🔗 GitHub Link",
            value=f"[View on GitHub]({issue.html_url})",
            inline=True
        )
        
        embed.set_author(
            name=f"Reported by {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
        )
        
        embed.set_footer(
            text=f"You'll be contacted in a thread if the dev team needs more info",
            icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        )
        
        # Send the embed with user mention
        message = await issue_chn.send(
            content=f"{interaction.user.mention} Your issue has been created! You'll be notified in a thread if the dev team needs any additional information.",
            embed=embed
        )
        
        # Create a thread for follow-up questions
        thread = await message.create_thread(
            name=f"Issue #{issue.number}: {self.IssueTitle.value[:50]}",
            auto_archive_duration=1440  # 24 hours
        )
        
        await thread.send(f"Hey {interaction.user.mention}, this thread is for any follow-up questions from the dev team about your issue.")
        
        
        # Use followup since we deferred the response
        await interaction.followup.send(
            "**Issue created successfully!**", ephemeral=True
        )
    

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        # Check if interaction is already responded to
        if interaction.response.is_done():
            await interaction.followup.send(
                "Oops! Something went wrong.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Oops! Something went wrong.", ephemeral=True
            )