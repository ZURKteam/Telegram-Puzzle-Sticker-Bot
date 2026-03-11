# 🧩 Puzzle Emoji Bot

Turn your photos & short videos into **custom puzzle emoji packs** for Telegram!  
✨ Supports animated videos, static puzzles, and custom grid sizes. Perfect for mosaics, banners, or just fun emoji packs.

---

## ⚡ Features

- 📸 **Photo → Puzzle**: Slice photos into grids (`3x3`, `5x5`, `8x8`, `10x10` or custom like `4x6`)  
- 🎬 **Video → Animated/Static Puzzle**: Use short videos as animated emoji packs or static puzzles from the first frame  
- ✏️ **Custom Grid**: Choose your own puzzle layout  
- 🧩 **Automatic Emoji Pack**: Bot creates the pack and uploads to Telegram  
- 🗑 **Auto Cleanup**: Temporary files removed automatically  

---

## 🛠 Requirements

- 🐍 Python 3.10+  
- 🎞 FFmpeg installed and available in `PATH`  
- 🤖 Telegram bot token from BotFather  
- 💎 Telegram Premium account (to use custom emoji in messages)  

---
BOT_TOKEN=your_bot_token_here
MAX_VIDEO_MB=20
MAX_VIDEO_SEC=10
MAX_STICKERS=120
🚀 Run the Bot
python run.py
The bot will automatically offer to install missing dependencies if needed.

🧩 How It Works
Send a photo or video to the bot

If video → choose animated or static mode

Pick a grid size or enter a custom one

Optionally add the original image as a preview emoji

Enter a title for the emoji pack

Wait for the bot to upload the pack and send the Telegram link

⚠️ Limits
Default values from .env:

🎥 MAX_VIDEO_MB=20

🎬 MAX_VIDEO_SEC=10

🧩 MAX_STICKERS=120

Actual pack size depends on Telegram limits.

📝 Notes
Output folders temp, parts, videos are created automatically

For videos, FFmpeg must be installed correctly

Works best with short videos to fit Telegram limits


---
## 📥 Installation

1️⃣ Clone the repo:  
```bash
git clone https://github.com/ZURKteam/Telegram-Puzzle-Sticker-Bot.git

cd Telegram-Puzzle-Sticker-Bot
2️⃣ Install dependencies:

pip install -r requirements.txt
3️⃣ Check FFmpeg:

ffmpeg -version
4️⃣ Create a .env file next to run.py:


