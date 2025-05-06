from fastapi import FastAPI
from telegram import Bot
import os

app = FastAPI()

# Чтение токена из переменной окружения
TOKEN = os.getenv('BOT_TOKEN')

# Функция для старта бота
@app.get("/")
async def root():
    return {"message": "Bot is running"}

@app.get("/start-bot")
async def start_bot():
    bot = Bot(TOKEN)
    # Здесь можно добавить любые действия с ботом, например:
    bot.send_message(chat_id="your-chat-id", text="Bot started!")
    return {"message": "Bot started successfully!"}
