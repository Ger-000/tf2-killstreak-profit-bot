import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from steam_market_scraper import SteamMarketScraper
import asyncio

load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

scraper = SteamMarketScraper()

# Store user's tracked items
user_tracking = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('------')

@bot.command(name='profit', help='Check profit margin for a TF2 killstreak flip. Usage: !profit <weapon_name>')
async def check_profit(ctx, *, weapon_name: str):
    """
    Check the profit margin for flipping a killstreak weapon.
    Usage: !profit Rocket Launcher
    """
    await ctx.defer()
    
    try:
        # Show that we're searching
        await ctx.send(f"🔍 Searching Steam Market for '{weapon_name}' killstreak items...")
        
        # Run scraping in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Search for kit and weapon prices
        kit_result = await loop.run_in_executor(None, scraper.get_killstreak_kit_price, weapon_name)
        weapon_result = await loop.run_in_executor(None, scraper.get_killstreak_weapon_price, weapon_name)
        
        if not kit_result or not weapon_result:
            await ctx.send(f"❌ Could not find prices for '{weapon_name}' killstreak items on Steam Market.\n"
                          f"Make sure the weapon name is correct (e.g., 'Rocket Launcher', 'Minigun')")
            return
        
        kit_price = kit_result['price']
        weapon_price = weapon_result['price']
        
        # Calculate profit
        profit_data = scraper.calculate_profit(kit_price, weapon_price)
        
        # Create embed
        embed = discord.Embed(
            title=f"💰 Killstreak Profit Analysis: {weapon_name}",
            color=discord.Color.gold() if profit_data['is_profitable'] else discord.Color.red()
        )
        
        embed.add_field(name="Base Weapon Cost", value=f"€{profit_data['base_weapon_cost']:.4f}", inline=False)
        embed.add_field(name="Killstreak Kit Price", value=f"€{profit_data['kit_price']:.2f}", inline=True)
        embed.add_field(name="Total Investment", value=f"€{profit_data['total_cost']:.4f}", inline=True)
        embed.add_field(name="Current Market Price", value=f"€{profit_data['market_price']:.2f}", inline=False)
        embed.add_field(name="Optimal Resale Price (2% below market)", value=f"€{profit_data['optimal_resale_price']:.2f}", inline=True)
        embed.add_field(name="Profit after 13% Steam Tax", value=f"€{profit_data['profit_at_optimal']:.4f}", inline=True)
        embed.add_field(name="Profit Margin", value=f"{profit_data['profit_margin_percent']:.1f}%", inline=False)
        
        status = "✅ **PROFITABLE**" if profit_data['is_profitable'] else "❌ **NOT PROFITABLE**"
        embed.add_field(name="Status", value=status, inline=False)
        
        embed.set_footer(text="Prices fetched from Steam Community Market • 13% Steam tax applied to resale")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")
        print(f"Error in check_profit: {e}")

@bot.command(name='track', help='Track a weapon for price changes. Usage: !track <weapon_name>')
async def track_weapon(ctx, *, weapon_name: str):
    """Track a weapon and get notified of price changes."""
    user_id = ctx.author.id
    
    if user_id not in user_tracking:
        user_tracking[user_id] = []
    
    if weapon_name not in user_tracking[user_id]:
        user_tracking[user_id].append(weapon_name)
        await ctx.send(f"✅ Now tracking: **{weapon_name}**\nUse `!untrack {weapon_name}` to stop tracking.")
    else:
        await ctx.send(f"Already tracking **{weapon_name}**!")

@bot.command(name='untrack', help='Stop tracking a weapon. Usage: !untrack <weapon_name>')
async def untrack_weapon(ctx, *, weapon_name: str):
    """Stop tracking a weapon."""
    user_id = ctx.author.id
    
    if user_id in user_tracking and weapon_name in user_tracking[user_id]:
        user_tracking[user_id].remove(weapon_name)
        await ctx.send(f"✅ Stopped tracking: **{weapon_name}**")
    else:
        await ctx.send(f"Not tracking **{weapon_name}**!")

@bot.command(name='tracked', help='List all weapons you are tracking.')
async def list_tracked(ctx):
    """List all tracked weapons."""
    user_id = ctx.author.id
    
    if user_id not in user_tracking or not user_tracking[user_id]:
        await ctx.send("You're not tracking any weapons yet! Use `!track <weapon_name>` to start.")
        return
    
    weapons = '\n'.join([f"• {w}" for w in user_tracking[user_id]])
    embed = discord.Embed(
        title="📋 Tracked Weapons",
        description=weapons,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command(name='help_ks', help='Show killstreak profit bot help.')
async def help_command(ctx):
    """Show help information."""
    embed = discord.Embed(
        title="💰 TF2 Killstreak Profit Bot",
        description="Find profitable TF2 killstreak weapon flips on Steam Community Market!",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="!profit <weapon>",
        value="Check profit margin for a killstreak weapon\nExample: `!profit Rocket Launcher`",
        inline=False
    )
    embed.add_field(
        name="!track <weapon>",
        value="Track a weapon for price changes\nExample: `!track Minigun`",
        inline=False
    )
    embed.add_field(
        name="!untrack <weapon>",
        value="Stop tracking a weapon\nExample: `!untrack Minigun`",
        inline=False
    )
    embed.add_field(
        name="!tracked",
        value="List all weapons you're tracking",
        inline=False
    )
    embed.add_field(
        name="Popular Weapons to Flip",
        value="Rocket Launcher, Minigun, Shotgun, Sniper Rifle, Spy's Revolver, Scout's Scattergun",
        inline=False
    )
    embed.set_footer(text="Remember: Accounts for 13% Steam tax in profit calculations!")
    
    await ctx.send(embed=embed)

# Run the bot
def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("ERROR: DISCORD_TOKEN not found in .env file!")
        print("Please create a .env file with your Discord bot token.")
        return
    
    bot.run(token)

if __name__ == "__main__":
    main()