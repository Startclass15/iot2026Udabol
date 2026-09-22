from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder,CommandHandler, ContextTypes
import threading

token=""
datos={
    "temperatura":0,
    "humedad":0
}
app=Flask(__name__)
@app.route("/datos",methods=["POST"])
def recibirDatos():
    datos["temperatura"]=request.json["temperatura"]
    datos["humedad"]=request.json["humedad"]
    print("DATOS RECIBIDOS")
    print(datos)
    return "OK"

async def botInicio(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BOT ACTIVO \n\n /datos - Ver Sensores")

async def mostrarDatos(update:Update,context:ContextTypes.DEFAULT_TYPE):
    temperatura=datos["temperatura"]
    humedad=datos["humedad"]
    mensaje=(
        "DATOS ESP32 \n\n "
        f"Temperatura: {temperatura}°C \n"
        f"Humedad: {humedad}%"
    )
    await update.message.reply_text(mensaje)

def Servidor():
    app.run(
        host="0.0.0.0",
        port=5000
    )

if __name__=="__main__":
    hilo=threading.Thread(target=Servidor)
    hilo.start()

    bot=ApplicationBuilder().token(token).build()
    bot.add_handler(
        CommandHandler("start",botInicio)
    )
    bot.add_handler(
        CommandHandler("datos",mostrarDatos)
    )

    print("Bot Funcionando... ")
    bot.run_polling()