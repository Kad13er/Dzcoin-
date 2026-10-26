"""Bot Telegram : la commande /start ouvre la Mini App. Lancer : python bot.py"""
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = os.environ["WEBAPP_URL"]  # adresse HTTPS de ton serveur

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🪙 Jouer", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await update.message.reply_text("Bienvenue sur Dzcoin ! Clique pour gagner des points.", reply_markup=kb)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
