from flask import Flask, request, jsonify,render_template
import requests
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

#PASO 1. CREAR EL SERVIDOR
app=Flask(__name__)
#PASO 2. CONFIGURAR LAS CREDENDCIALES
tokenTelegram=os.getenv("tokenTelegram")
chatId=os.getenv("chatId")
apiGoogle=os.getenv("apiGoogle")
#PASO 3. CONFIGURAR GEMINI
cliente=genai.Client(api_key=apiGoogle)
#PASO 4. CONFIGURAR LA FUNCION PARA ANALIZAR LOS DATOS
def analizar(datos):
    indicacion=f""" 
        Seras de control de monitorieo IOT.
        Analiza los siguientes datos recibidos desde un 
        ESP32:
        DISTANCIA: {datos['distancia']}
        MOVIMIENTO: {datos['movimiento']}
        PUERTA: {datos['puerta']}
        

        Genera un reporte breve indicando:
        1. Estado general
        2. Valores que deben ser analizados
        3. Posible problema o riesgos
        4. Recomendaciones

        No inventes datos que no esten disponibles

    """
    #RESPUESTA
    respuesta=cliente.models.generate_content(
        model="gemini-3.8-flash",
        contents=indicacion
    )
    return respuesta.text

#PASO 5. ENVIAR EL REPORTE A TELEGRAM
def enviarTelegram(mensaje):
    url=f"https://api.telegram.org/bot{tokenTelegram}/sendMessage"
    datos={
        "chat_id":chatId,
        "text":mensaje
    }
    respuesta=requests.post(url,data=datos)
    return respuesta.json()


#fUNCION PARA PROCESAR LOS DATOS 
def procesarComando(texto):
    global monitoreo,notificaciones
    partes=texto.strip().split(maxsplit=1)
    comando=partes[0].split("@")[0].lower()
    funcionalidad=partes[1] if len(partes)>1 else ""
    if comando in ("/start","/adyuda"):
        return(
            "Bot Monitoreo"
            "/reporte - Consultar "
            "/on - Encender"
            "/ping - comprobar conexion" 
        )
    elif comando=="/ping":
        return "RESPUESTA OBTENIDA"
    elif comando=="/estado":
        return (
            f"Distancia: {ultimoDato['distancia']}\n"
            f"Movimiento: {ultimoDato['movimiento']}\n"
            f"Puerta: {ultimoDato['puerta']}"
        )
    elif comando=="/reporte":
        return ultimoReporte
    if "/Monitorieo":
        return analizar(texto)
    

ultimoDato={
    "distancia":"--",
    "movimiento":"--",
    "puerta":"--"
}
ultimoReporte="Esperando datos del ESP32"
    
#renderizado de la interfaz
@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/estado")
def estado():
    return jsonify({
        "distancia":ultimoDato.get("distancia", "--"),
        "movimineto":ultimoDato.get("movimiento","--"),
        "puerta":ultimoDato.get("puerta", "--"),
        "reporte":ultimoReporte
    })

#PASO 6. RECIBIR LOS MENSAJES DE ESP32
@app.route("/datos",methods=["POST"])
def recibirDatos():
    global ultimoDato,ultimoReporte
    datos=request.json
    print("Datos recibidos ")
    print(datos)
    #Guardar los datos del esp32
    ultimoDato={
            "distancia":datos["distancia"],
            "movimiento":datos["movimiento"],
            "puerta":datos["puerta"]
    }
    reporte=analizar(datos)
    mensaje=f"""
            REPORTE ESP32
            ESP32:
            DISTANCIA: {datos['distancia']}
            MOVIMIENTO: {datos['movimiento']}
            PUERTA: {datos['puerta']}

        {reporte}
            
     """
    enviarTelegram(mensaje)
    ultimoReporte=reporte
    return jsonify({
        "estado":"ok",
        "mensaje":"Reporte enviado a telegram"
    })
    

@app.route("/telegram",methods=["POST"])
def recibirTelegram():
    actualizacion=request.get_json(silent=True) or {}
    mensaje=actualizacion.get("message",{})
    chat=mensaje.get("chat",{})
    texto=mensaje.get("text","")
    if not texto or not chat:
        return jsonify({"ok":True}),200

    if str(chat.get("id"))!=str(chatId):
        return jsonify({"ok":True}),200

    respuesta=procesarComando(texto)
    try: 
        enviarTelegram(respuesta)
    except Exception as error:
        print("Error al procesar el comando ", error)
        return jsonify({"ok":False}),500

if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )