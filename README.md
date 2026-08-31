# TF2 Killstreak Profit Bot 💰

A Discord bot that finds profitable TF2 killstreak weapon flips on the Steam Community Market.

## How It Works

The bot scrapes the Steam Community Market to:
1. Find killstreak kit prices
2. Find finished killstreak weapon prices
3. Calculate profit margins **accounting for Valve's 13% tax**
4. Suggest optimal resale prices to guarantee profit

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Ger-000/tf2-killstreak-profit-bot.git
cd tf2-killstreak-profit-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token

Create a `.env` file in the project root:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

### 4. Invite Bot to Your Server

1. In Developer Portal, go to OAuth2 → URL Generator
2. Select scopes: `bot`
3. Select permissions: `Send Messages`, `Embed Links`, `Read Message History`
4. Copy the generated URL and open it to invite the bot

### 5. Run the Bot
```bash
python bot.py
```

## Commands

### `!profit <weapon_name>`
Check the profit margin for a killstreak weapon flip.

**Example:**
```
!profit Rocket Launcher
```

**Output:**
- Base weapon cost
- Killstreak kit price
- Total investment needed
- Current market price of finished weapon
- Optimal resale price (2% below market for quick sale)
- **Profit after 13% Steam tax**
- Profit margin percentage
- Profitable? ✅ or ❌

### `!track <weapon>`
Track a weapon for future price monitoring.

**Example:**
```
!track Minigun
```

### `!untrack <weapon>`
Stop tracking a weapon.

**Example:**
```
!untrack Minigun
```

### `!tracked`
List all weapons you're currently tracking.

### `!help_ks`
Show bot help and available commands.

## Popular Weapons to Flip

- Rocket Launcher
- Minigun
- Shotgun
- Sniper Rifle
- Spy's Revolver
- Scout's Scattergun

## Profit Formula

```
Total Cost = Base Weapon Price (~€0.0017) + Killstreak Kit Price

Revenue at Optimal Price = Market Price × 0.98 × (1 - 0.13)
                         = Market Price × 0.98 × 0.87

Profit = Revenue at Optimal Price - Total Cost

Margin % = (Profit / Total Cost) × 100
```

## Technical Details

- **Scraper:** Uses BeautifulSoup4 to parse Steam Community Market
- **Rate Limiting:** 2-second delays between requests to avoid rate limiting
- **Async:** Discord.py async/await for non-blocking operations
- **Tax Calculation:** Accounts for Valve's 13% Steam Community Market tax

## Disclaimer

This bot is for informational purposes only. Steam Community Market prices fluctuate rapidly. Always verify prices before making trades. The bot's data may lag behind real-time prices.

## Future Features

- [ ] Periodic price monitoring with notifications
- [ ] Historical price tracking
- [ ] Profit alerts when items become profitable
- [ ] Multi-currency support (currently uses €)
- [ ] Database to store price history

## License

MIT License - feel free to use and modify!

---

**Happy flipping! 🎩💸**
