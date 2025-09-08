#!/usr/bin/env python3
"""
Simple test script to run the Telegram bot in polling mode for testing
"""
import os
import asyncio
from bot import TelegramStoreBot
from data_manager import DataManager

async def main():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        print("BOT_TOKEN environment variable not set!")
        return
    
    data_manager = DataManager()
    bot = TelegramStoreBot(bot_token, data_manager)
    
    print("Starting bot in polling mode...")
    print("The bot will now respond to messages on Telegram!")
    print("Send /start to your bot to test it.")
    print("Press Ctrl+C to stop the bot.")
    
    # Run in polling mode
    await bot.application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())