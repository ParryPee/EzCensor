# Telegram Censor Bot

A Telegram bot that uses local LLM (Ollama with Llama 3.2) to detect and censor sensitive information in documents and images.

## Features

- Document processing (PDF, DOCX, XLSX, TXT)
- Image processing with OCR
- Local LLM integration via Ollama
- Configurable censoring rules
- Privacy-focused (all processing happens locally)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install and start Ollama:
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3.2:3b
   ollama serve
   ```

3. Create a Telegram bot:
   - Message @BotFather on Telegram
   - Create a new bot and get the token
   - Copy `.env.example` to `.env` and add your bot token

4. Run the bot:
   ```bash
   python src/main.py
   ```

## Project Structure

```
censor_bot/
├── src/
│   ├── main.py              # Bot entry point
│   ├── handlers/            # Telegram message handlers
│   ├── services/            # Business logic (LLM, processing)
│   └── utils/               # Utility functions
├── temp/                    # Temporary file storage
├── requirements.txt         # Python dependencies
└── .env.example            # Configuration template
```

## Usage

1. Start a chat with your bot
2. Send `/start` to begin
3. Upload a document or image
4. The bot will process and return the censored version
