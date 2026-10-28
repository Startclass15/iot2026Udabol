
from flask import Flask, request, jsonify, render_template
import requests
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

# PASO 1. CREAR EL SERVIDOR
app = Flask(__name__)

# PASO 2. CONFIGURAR CREDENCIALES
tokenTelegram = os.getenv("tokenTelegram")
chatId = os.getenv("chatId")
apiGoogle = os.getenv("apiGoogle")

# PASO 3. CONFIGURAR GEMINI
cliente = genai.Client(api_key=apiGoogle) if apiGoogle else None
modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# PASO 4. ALMACENAR LOS DATOS
ultimoDato = {
    "distancia": "--",
    "movimiento": "--",
    "puerta": "--"
}

ultimoReporte = "Esperando datos del ESP32"


# PASO 5. ANALIZAR LOS DATOS CON GEMINI
def analizar(datos):
    if cliente is None:
        return "Error: falta configurar apiGoogle en el archivo .env"

    indicacion = f"""
    Eres un asistente de monitoreo IoT.

    Analiza estos datos recibidos desde un ESP32:

    DISTANCIA: {datos.get('distancia', '--')}
    MOVIMIENTO: {datos.get('movimiento', '--')}
    PUERTA: {datos.get('puerta', '--')}

    Genera un reporte breve indicando:
    1. Estado general.
    2. Valores que requieren atención.
    3. Posibles problemas o riesgos.
    4. Recomendaciones.
    5. No pongas ** en el texto


    No inventes datos ni afirmes que existe una alarma
    si los valores recibidos no permiten determinarlo.
    """

    try:
        respuesta = cliente.models.generate_content(
            model=modelo,
            contents=indicacion
        )

        return respuesta.text or "Gemini no generó un reporte."

    except Exception as error:
        print("Error de Gemini:", error)
        return "No se pudo generar el análisis con Gemini."


# PASO 6. ENVIAR MENSAJES A TELEGRAM
def enviarTelegram(mensaje):
    if not tokenTelegram or not chatId:
        raise ValueError("Faltan tokenTelegram o chatId en .env")

    url = f"https://api.telegram.org/bot{tokenTelegram}/sendMessage"

    datos = {
        "chat_id": chatId,
        "text": str(mensaje)[:4000]
    }

    respuesta = requests.post(
        url,
        data=datos,
        timeout=10
    )

    respuesta.raise_for_status()

    resultado = respuesta.json()

    if not resultado.get("ok"):
        raise RuntimeError("Telegram no pudo enviar el mensaje")

    return resultado


# PASO 7. PROCESAR COMANDOS
def procesarComando(texto):
    global ultimoDato, ultimoReporte

    partes = texto.strip().split(maxsplit=1)

    if not partes:
        return "Escribe /ayuda para ver los comandos."

    comando = partes[0].split("@")[0].lower()

    if comando in ("/start", "/ayuda", "/help"):
        return (
            "BOT DE MONITOREO IOT\n\n"
            "/estado - Consultar sensores\n"
            "/reporte - Ver último reporte\n"
            "/analizar - Analizar datos actuales\n"
            "/ping - Comprobar conexión\n"
            "/on - Solicitar encendido\n"
            "/off - Solicitar apagado"
        )

    elif comando == "/ping":
        return "Conexión correcta con el servidor Flask."

    elif comando == "/estado":
        return (
            f"DATOS DEL ESP32\n\n"
            f"Distancia: {ultimoDato['distancia']}\n"
            f"Movimiento: {ultimoDato['movimiento']}\n"
            f"Puerta: {ultimoDato['puerta']}"
        )

    elif comando == "/reporte":
        return ultimoReporte

    elif comando == "/analizar":
        ultimoReporte = analizar(ultimoDato)
        return ultimoReporte

    elif comando in ("/on", "/off"):
        return (
            f"Comando {comando} recibido, pero el control físico "
            "del ESP32 todavía no está implementado."
        )

    else:
        return "Comando desconocido. Escribe /ayuda."


# PASO 8. MOSTRAR EL PANEL WEB
@app.route("/")
def inicio():
    return render_template("index.html")


# PASO 9. DEVOLVER DATOS AL PANEL
@app.route("/estado", methods=["GET"])
def estado():
    return jsonify({
        "datos": ultimoDato,
        "reporte": ultimoReporte
    })


# PASO 10. RECIBIR DATOS DEL ESP32
@app.route("/datos", methods=["POST"])
def recibirDatos():
    global ultimoDato, ultimoReporte

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({
            "estado": "error",
            "mensaje": "Se esperaba un objeto JSON."
        }), 400

    campos = ["distancia", "movimiento", "puerta"]

    if any(campo not in datos for campo in campos):
        return jsonify({
            "estado": "error",
            "mensaje": "Faltan distancia, movimiento o puerta."
        }), 400

    # Guardar datos recibidos
    ultimoDato = {
        "distancia": datos["distancia"],
        "movimiento": datos["movimiento"],
        "puerta": datos["puerta"]
    }

    # Analizar y guardar el reporte
    ultimoReporte = analizar(ultimoDato)

    mensaje = (
        "REPORTE DE MONITOREO IOT\n\n"
        f"Distancia: {ultimoDato['distancia']}\n"
        f"Movimiento: {ultimoDato['movimiento']}\n"
        f"Puerta: {ultimoDato['puerta']}\n\n"
        f"{ultimoReporte}"
    )

    # Si Telegram falla, los datos quedan guardados
    try:
        enviarTelegram(mensaje)
        estadoTelegram = "enviado"

    except Exception as error:
        print("Error de Telegram:", error)
        estadoTelegram = "error"

    return jsonify({
        "estado": "ok",
        "telegram": estadoTelegram,
        "datos": ultimoDato,
        "reporte": ultimoReporte
    }), 200


# PASO 11. RECIBIR COMANDOS DESDE EL PANEL WEB

# RECIBIR COMANDOS DESDE EL PANEL WEB Y ENVIARLOS A TELEGRAM
@app.route("/comando", methods=["POST"])
def comandoWeb():
    datos = request.get_json(silent=True) or {}
    texto = datos.get("comando", "")

    if not isinstance(texto, str) or not texto.strip():
        return jsonify({
            "respuesta": "Escribe un comando."
        }), 400

    # Procesar el comando
    respuesta = procesarComando(texto)

    try:
        # Enviar a Telegram el comando escrito y su respuesta
        mensajeTelegram = (
            "COMANDO DESDE EL PANEL WEB\n\n"
            f"Comando: {texto}\n\n"
            f"Respuesta:\n{respuesta}"
        )

        enviarTelegram(mensajeTelegram)

        estadoTelegram = "Comando enviado a Telegram"

    except Exception as error:
        print("Error al enviar comando a Telegram:", error)
        estadoTelegram = "No se pudo enviar a Telegram"

    return jsonify({
        "comando": texto,
        "respuesta": respuesta,
        "telegram": estadoTelegram
    }), 200



# PASO 12. RECIBIR MENSAJES DEL BOT DE TELEGRAM
@app.route("/telegram", methods=["POST"])
def recibirTelegram():
    actualizacion = request.get_json(silent=True) or {}

    mensaje = actualizacion.get("message", {})
    chat = mensaje.get("chat", {})
    texto = mensaje.get("text", "")

    if not texto or not chat:
        return jsonify({"ok": True}), 200

    # Aceptar solamente mensajes del chat autorizado
    if not chatId or str(chat.get("id")) != str(chatId):
        return jsonify({"ok": True}), 200

    respuesta = procesarComando(texto)

    try:
        enviarTelegram(respuesta)

    except Exception as error:
        print("Error al responder en Telegram:", error)
        return jsonify({"ok": False}), 500

    return jsonify({"ok": True}), 200


# PASO 13. INICIAR EL SERVIDOR
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False
    )
