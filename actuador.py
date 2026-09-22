import requests
from telegram import Update
from telegram.ext import ApplicationBuilder,CommandHandler,ContextTypes

token=""
esp32="192.168.56.1"

async def encenderLed(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        respuesta=requests.get(f"http://{esp32}/led/on",timeout=5)
        await update.message.reply_text("LED ENCENDIDO - ESP32: ",respuesta.text)
    except Exception as error:
        await update.message.reply_text("No se pudo conectar al ESP32")

#FUNCION PARA APAGAR 
async def apagarLed(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        respuesta=requests.get(f"http://{esp32}/led/off",timeout=5)
        await update.message.reply_text("LED APAGADO - ESP32: ",respuesta.text)
    except Exception as error:
        await update.message.reply_text("No se pudo conectar")

#Consultar estado
async def estado(update:Update, context:ContextTypes.DEFAULT_TYPE):
    try:
        respuesta=requests.get(f"http://{esp32}/led/estado",timeout=5)
        await update.message.reply_text("Estado actuador:",respuesta.text)
    except Exception as error:
        await update.message.reply_text("No se pudo conectar")


def main():
    app=ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("ledOn",encenderLed))
    app.add_handler(CommandHandler("ledOff",apagarLed))
    app.add_handler(CommandHandler("estado",estado))
    print("Bot encendido")
    app.run_polling()

if __name__=="__main__":
    main()