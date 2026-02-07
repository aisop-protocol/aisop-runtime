import asyncio
import sys
import os

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.bot import run_bot

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("Bot stopped by user.")
