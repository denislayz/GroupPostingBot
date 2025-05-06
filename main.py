
import json
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

CHOOSING_GROUP, CHOOSING_TOPIC, TYPING_POST, CONFIRMING = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📝 Новый пост", callback_data="new_post")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Что будем делать?", reply_markup=reply_markup)

async def new_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    groups = CONFIG["groups"]
    keyboard = [
        [InlineKeyboardButton(group["name"], callback_data=f'group_{group["id"]}')]
        for group in groups
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите группу:", reply_markup=reply_markup)
    return CHOOSING_GROUP

async def choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = int(query.data.split("_")[1])
    context.user_data["group_id"] = group_id
    group = next((g for g in CONFIG["groups"] if g["id"] == group_id), None)
    if not group:
        await query.edit_message_text("Группа не найдена.")
        return ConversationHandler.END
    topics = group.get("topics", [])
    keyboard = [
        [InlineKeyboardButton(topic["name"], callback_data=f'topic_{topic["thread_id"]}')]
        for topic in topics
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите тему:", reply_markup=reply_markup)
    return CHOOSING_TOPIC

async def choose_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    thread_id = int(query.data.split("_")[1])
    context.user_data["thread_id"] = thread_id
    await query.edit_message_text("Отправьте текст поста и, при необходимости, фото или видео.")
    return TYPING_POST

async def receive_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["text"] = update.message.text or ""
    if update.message.photo:
        context.user_data["media"] = {
            "type": "photo",
            "file_id": update.message.photo[-1].file_id,
        }
    elif update.message.video:
        context.user_data["media"] = {
            "type": "video",
            "file_id": update.message.video.file_id,
        }
    else:
        context.user_data["media"] = None
    await update.message.reply_text("Пост готов к отправке. Подтвердите отправку.")
    return CONFIRMING

async def confirm_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = context.user_data["group_id"]
    thread_id = context.user_data["thread_id"]
    text = context.user_data["text"]
    media = context.user_data["media"]
    if media:
        if media["type"] == "photo":
            await context.bot.send_photo(chat_id=group_id, photo=media["file_id"], caption=text, message_thread_id=thread_id)
        elif media["type"] == "video":
            await context.bot.send_video(chat_id=group_id, video=media["file_id"], caption=text, message_thread_id=thread_id)
    else:
        await context.bot.send_message(chat_id=group_id, text=text, message_thread_id=thread_id)
    await update.message.reply_text("Пост отправлен.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_post_callback, pattern="^new_post$")],
        states={
            CHOOSING_GROUP: [CallbackQueryHandler(choose_group, pattern="^group_")],
            CHOOSING_TOPIC: [CallbackQueryHandler(choose_topic, pattern="^topic_")],
            TYPING_POST: [MessageHandler(filters.ALL, receive_post)],
            CONFIRMING: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_post)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
