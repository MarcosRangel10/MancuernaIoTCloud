import os
import json
import ssl
import time
import paho.mqtt.client as mqtt
import mysql.connector

# =====================================================
# CONFIGURACIÓN MQTT - HIVE MQ CLOUD
# =====================================================
MQTT_BROKER = "d3befa5909cf4595a75259012d836398.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "mancuerna/+/datos"

MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# =====================================================
# CONFIGURACIÓN MYSQL - RAILWAY
# =====================================================
DB_HOST = os.getenv("MYSQLHOST")
DB_PORT = int(os.getenv("MYSQLPORT", "3306"))
DB_USER = os.getenv("MYSQLUSER")
DB_PASSWORD = os.getenv("MYSQLPASSWORD")
DB_NAME = os.getenv("MYSQLDATABASE")

def conectar_mysql():
    try:
        conexion = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conexion
    except mysql.connector.Error as error:
        print("✗ Error conectando a MySQL:", error)
        return None

def al_conectar(client, userdata, flags, rc):
    if rc == 0:
        print("✓ Conectado correctamente a HiveMQ Cloud")
        client.subscribe(MQTT_TOPIC)
        print(f"✓ Suscrito a: {MQTT_TOPIC}")
    else:
        print(f"✗ Error de conexión MQTT. Código: {rc}")

def al_recibir(client, userdata, msg):
    try:
        datos = json.loads(msg.payload.decode())

        dispositivo = datos.get("dispositivo", "Desconocido")
        angulo = datos.get("angulo", 0.0)
        movimiento = datos.get("movimiento", False)
        repeticiones = datos.get("repeticiones", 0)
        cadencia = datos.get("cadencia", 0.0)
        tecnica = datos.get("tecnica", "Optima")

        # Lectura de la sub-estructura "onda" (X, Y, Z)
        onda = datos.get("onda", {})
        ax = onda.get("x", 0.0)
        ay = onda.get("y", 0.0)
        az = onda.get("z", 0.0)

        print(f"[{dispositivo}] Reps: {repeticiones} | Ángulo: {angulo}° | Cadencia: {cadencia}s | Técnica: {tecnica}")

        conexion = conectar_mysql()
        if conexion:
            cursor = conexion.cursor()
            sql = """
                INSERT INTO datos_mancuerna
                (dispositivo, angulo, movimiento, repeticiones, cadencia, tecnica, ax, ay, az)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            valores = (dispositivo, angulo, movimiento, repeticiones, cadencia, tecnica, ax, ay, az)
            cursor.execute(sql, valores)
            conexion.commit()
            cursor.close()
            conexion.close()

    except Exception as error:
        print("✗ Error procesando mensaje:", error)

client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
client.on_connect = al_conectar
client.on_message = al_recibir

print("Conectando a HiveMQ Cloud...")
while True:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        break
    except Exception as error:
        print("Error conectando a HiveMQ. Reintentando en 5s...", error)
        time.sleep(5)

client.loop_forever()