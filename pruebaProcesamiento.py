import requests

datos={
    "distancia":5,
    "movimiento":True,
    "puerta":"Puerta abierto sin autorizacion - alarma activa "

    
}

respuesta=requests.post(
    "http://127.0.0.1:5000/datos",
    json=datos
)

print("Respuesta del servidor")
print(respuesta.json())