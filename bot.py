from telegram import Update
from telegram.ext import ApplicationBuilder,ContextTypes,CommandHandler
from dotenv import load_dotenv
import os
load_dotenv()

token=os.getenv("tokenTelegram")

async def comandoAlerta(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Activando Alarma...")

async def comandoOn(update:Update,context:ContextTypes.DEFAULT_TYPE):
    with open("sensorULTRA.png","rb") as imagen:
        await update.message.reply_photo(imagen)

def main():
    app=ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("alerta",comandoAlerta))
    app.add_handler(CommandHandler("on",comandoOn))
    print("Bot conectado")
    app.run_polling()

main()
