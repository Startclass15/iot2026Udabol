from flask import Flask, request, jsonify
import requests
from google import genai

#PASO 1. CREAR EL SERVIDOR
app=Flask(__name__)
#PASO 2. CONFIGURAR LAS CREDENDCIALES
tokenTelegram=""
chatId="5"
apiGoogle=""
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
    if comando=="/ping":
        return "RESPUESTA OBTENIDA"
    if "/Monitorieo":
        return analizar(texto)
    

#PASO 6. RECIBIR LOS MENSAJES DE ESP32
@app.route("/datos",methods=["POST"])
def recibirDatos():
    datos=request.json
    print("Datos recibidos ")
    print(datos)
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
    return jsonify({
        "estado":"ok",
        "mensaje":"Reporte enviado a telegram"
    })

if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )