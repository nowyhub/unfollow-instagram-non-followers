import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from instagrapi import Client

# Load environment variables
load_dotenv()

class Instagram(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_run = None  # Store last run time (global for all users)
        self.last_user = None  # Store who last used it
        self.cooldown_hours = 24
        
        # Load Instagram credentials from .env
        self.ig_username = os.getenv('IG_user')
        self.ig_password = os.getenv('IG_password')
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        pass
    
    def check_cooldown(self) -> tuple[bool, int, str]:
        """
        Check if command is on cooldown (global)
        Returns: (is_on_cooldown, seconds_remaining, last_user)
        """
        if self.last_run is None:
            return False, 0, None
        
        time_passed = datetime.now() - self.last_run
        cooldown_duration = timedelta(hours=self.cooldown_hours)
        
        if time_passed < cooldown_duration:
            seconds_remaining = int((cooldown_duration - time_passed).total_seconds())
            return True, seconds_remaining, self.last_user
        
        return False, 0, None
    
    def format_time(self, seconds: int) -> str:
        """Format seconds into readable time format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"
    
    async def instagram_login(self):
        """
        Login to Instagram and run your code
        Returns: (success, message)
        """
        try:
            # Run in executor to prevent blocking
            loop = asyncio.get_event_loop()
            
            def sync_instagram_work():
                import time
                import random
                
                cl = Client()
                
                # Login
                cl.login(self.ig_username, self.ig_password)
                
                # Get user ID
                user_id = cl.user_id
                
                # Get followers and following with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        followers = cl.user_followers(user_id)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise Exception(f'Failed to get followers: {str(e)}')
                        time.sleep(2)
                
                for attempt in range(max_retries):
                    try:
                        following = cl.user_following(user_id)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise Exception(f'Failed to get following: {str(e)}')
                        time.sleep(2)
                
                # Find who doesn't follow back
                follower_ids = set(followers.keys())
                not_following_back = [user_id for user_id in following.keys() if user_id not in follower_ids]
                
                if len(not_following_back) == 0:
                    cl.logout()
                    return f'✅ Everyone follows you back!\n\n**Stats:**\n• Following: {len(following)}\n• Followers: {len(followers)}'
                
                # Wait before starting
                time.sleep(3)
                
                unfollowed = 0
                failed = 0
                
                for user_id in not_following_back:
                    try:
                        username = following[user_id].username
                        cl.user_unfollow(user_id)
                        unfollowed += 1
                        
                        # Random delay between 4-8 seconds to avoid rate limits
                        delay = 4 + random.random() * 4
                        time.sleep(delay)
                        
                    except Exception:
                        failed += 1
                        time.sleep(10)
                
                # Logout
                try:
                    cl.logout()
                except:
                    pass
                
                # Build result message
                result_msg = f'✅ **Unfollow Complete**\n\n'
                result_msg += f'**Stats:**\n'
                result_msg += f'• Following: {len(following)}\n'
                result_msg += f'• Followers: {len(followers)}\n'
                result_msg += f'• Non-followers: {len(not_following_back)}\n\n'
                result_msg += f'**Results:**\n'
                result_msg += f'• Unfollowed: {unfollowed}\n'
                if failed > 0:
                    result_msg += f'• Failed: {failed}\n'
                
                return result_msg
            
            # Run the blocking Instagram code in a thread pool
            result = await loop.run_in_executor(None, sync_instagram_work)
            return True, result
            
        except Exception as e:
            return False, f"❌ **Error**\n\n{str(e)}"
    
    @app_commands.command(name="unfollow", description="Unfollow Instagram users who don't follow you back (24h cooldown)")
    async def unfollow(self, interaction: discord.Interaction):
        """Instagram automation command with 24-hour cooldown"""
        
        # Check if credentials are loaded
        if not self.ig_username or not self.ig_password:
            embed = discord.Embed(
                title="❌ Configuration Error",
                description="Instagram credentials not found in `.env` file!\n\nMake sure you have:\n```\nIG_user=your_username\nIG_password=your_password\n```",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check cooldown
        on_cooldown, seconds_left, last_user = self.check_cooldown()
        
        if on_cooldown:
            time_str = self.format_time(seconds_left)
            last_user_mention = f"<@{last_user}>" if last_user else "Someone"
            embed = discord.Embed(
                title="⏰ Global Cooldown Active",
                description=f"{last_user_mention} used this command recently.\n\nAvailable again in **{time_str}**",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Defer response since Instagram login takes time
        await interaction.response.defer(ephemeral=True)
        
        # Create loading embed
        loading_embed = discord.Embed(
            title="🔄 Processing",
            description="Logging into Instagram and running automation...\nThis may take a few minutes.",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=loading_embed, ephemeral=True)
        
        # Run Instagram automation
        success, message = await self.instagram_login()
        
        if success:
            # Update last run time (global)
            self.last_run = datetime.now()
            self.last_user = interaction.user.id
            
            embed = discord.Embed(
                description=message,
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Command available again in {self.cooldown_hours} hours")
            await interaction.edit_original_response(embed=embed)
        else:
            embed = discord.Embed(
                description=message,
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed)

async def setup(bot):
    """Required function for loading the cog"""
    await bot.add_cog(Instagram(bot))
