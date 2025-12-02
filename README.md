# Trade Hub Discord Bot 🤖

A powerful Discord.py ticket bot for Trade Hub with persistent views, auto-role assignment, and 24/7 uptime support.

## Features ✨

- **5 Ticket Systems**: Middleman, Support, Buy Ranks, Buy Items, Buy Personal Middleman
- **Auto-Role Assignment**: Automatic role management with custom welcome messages
- **Persistent Views**: Buttons work permanently without re-adding the bot
- **Transcript Generation**: Auto-saves ticket conversations
- **Keep Alive 24/7**: Bot stays active without you being online
- **Pydroid/Mobile Ready**: Works on Termux, Pydroid3, and Python on any platform
- **Easy Configuration**: config.json for quick setup changes
- **Admin Controls**: Owner-only commands for /clear and personal middleman tickets

---

## 📋 Prerequisites

You need:
- **Python 3.8+** (installed on your system)
- **Discord Bot Token** (from Discord Developer Portal)
- **Bot Token Secret** (from your Discord server settings)
- **Groq API Key** (optional, for AI features)

---

## 🚀 Quick Start (All Platforms)

### Step 1: Extract Files
Extract the zip file to any folder on your computer or phone.

### Step 2: Create `.env` File
In the same folder as the bot files, create a file named `.env` and add:

```
BOT_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_key_here
```

⚠️ **KEEP THIS FILE SECRET** - Never share your tokens!

### Step 3: Install Dependencies
Open a terminal/command line in the bot folder and run:

```bash
pip install -r requirements.txt
```

On Pydroid3, use:
```bash
pip install --user -r requirements.txt
```

### Step 4: Run the Bot
```bash
python3 run_bot.py
```

Or directly:
```bash
python3 bot.py
```

---

## 💻 Platform-Specific Instructions

### Windows (Command Prompt/PowerShell)
1. Open folder → Right-click → "Open in Terminal"
2. Run: `python -m pip install -r requirements.txt`
3. Run: `python run_bot.py`

### macOS/Linux (Terminal)
1. Open terminal in the bot folder
2. Run: `pip3 install -r requirements.txt`
3. Run: `python3 run_bot.py`

### Android (Termux)
1. Install Termux from Google Play
2. Open Termux and run:
   ```bash
   pkg update && pkg upgrade
   pkg install python3 git
   ```
3. Navigate to bot folder: `cd /path/to/bot`
4. Run: `pip install -r requirements.txt`
5. Run: `python3 run_bot.py`

### Android (Pydroid3)
1. Install Pydroid3 from Google Play
2. Open Pydroid3
3. Install requirements:
   ```bash
   pip install --user -r requirements.txt
   ```
4. Open `run_bot.py` in editor and tap Run ▶️
   - Or in terminal: `python3 run_bot.py`

### Visual Studio Code
1. Open the bot folder in VS Code
2. Open Terminal: `Ctrl+` ` (backtick)
3. Run: `python3 run_bot.py`

---

## 🔄 24/7 Uptime (Keep Alive)

The bot has built-in keep-alive that:
- Automatically pings a server to show "I'm alive!"
- Prevents the bot from going offline if idle
- Works on all platforms including Pydroid/Termux
- **No additional setup needed** - just run the bot normally!

To verify it's working:
- The bot will open a web server on `http://localhost:8080`
- If you visit it, you'll see "I'm alive!" message
- The bot stays active even if Discord connection is idle

---

## ⚙️ Configuration

### `config.json`
Contains bot settings:
- **logo_url**: Change the TFU logo URL (for embeds)
- Add more settings as needed

### `ticket_data.json`
Stores all ticket information. **Don't edit manually** - the bot manages this automatically.

---

## 📁 File Structure

```
trade-hub-bot/
├── bot.py                 # Main bot code
├── bot_pydroid.py         # Pydroid version (copy of bot.py)
├── run_bot.py             # Restart wrapper (handles crashes)
├── keep_alive.py          # 24/7 uptime server
├── requirements.txt       # Python packages needed
├── config.json            # Bot configuration
├── ticket_data.json       # Ticket storage (auto-created)
├── .env.example           # Template for your secrets
├── .gitignore             # Git ignore file
└── README.md              # This file
```

---

## 🛠️ Common Issues & Fixes

### "ModuleNotFoundError: No module named discord"
**Fix**: Run `pip install -r requirements.txt` again

### "Bot token invalid" Error
**Fix**: Check your `.env` file has the correct token without quotes

### Bot crashes after running
**Fix**: Run `python3 run_bot.py` instead of `python3 bot.py` - it auto-restarts!

### Port 8080 already in use (keep alive error)
**Fix**: The bot will still work, it just can't show the status page

### On Pydroid: "Permission denied"
**Fix**: Use `pip install --user` instead of just `pip install`

---

## 🤖 Bot Commands

### Owner Only:
- `/clear` - Instantly clear all messages in channel
- **Buy Personal Middleman** - Create owner-only middleman tickets

### Everyone:
- **Request Middleman** - Create middleman support tickets
- **Make Support** - Create support tickets
- **Buy Ranks** - Create rank purchase tickets
- **Buy Items** - Create item purchase tickets

### Staff (Middleman/Support):
- 🔒 **Claim** - Claim a ticket to work on it
- 🔒 **Close** - Close ticket and save transcript
- 🗑️ **Delete** - Delete ticket without saving

---

## 🔐 Security Tips

1. **Never share your `.env` file** - It contains your bot token
2. **Keep `.env` out of git** - It's already in `.gitignore`
3. **Don't hardcode tokens in code** - Always use `.env`
4. **Rotate tokens** if accidentally exposed
5. **Use strong bot permissions** - Only grant what's needed

---

## 📚 Useful Links

- [Discord.py Docs](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Python Docs](https://docs.python.org/3/)
- [Groq API](https://groq.com/)

---

## 💡 Tips for Mobile (Pydroid/Termux)

- **Keep Alive**: Bot automatically stays online - no need for extra services
- **Long Session**: Keep terminal open or use `screen` command to keep running
- **Battery**: Running on phone will drain battery - use a PC for 24/7
- **WiFi**: Ensure stable connection for best results
- **Errors**: Check `runner.log` file for crash logs

---

## 🎯 Getting Help

If something doesn't work:
1. Check the `runner.log` file for error messages
2. Verify your `.env` file is correct
3. Make sure all requirements are installed: `pip list`
4. Try running on a different platform to isolate issues

---

## 📝 License

This bot is for Trade Hub. All rights reserved.

---

**Made with ❤️ for Trade Hub**

Enjoy your ticket bot! 🚀
