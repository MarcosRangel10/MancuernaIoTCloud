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


# =====================================================
# CONEXIÓN MYSQL
# =====================================================

def conectar_mysql():

    try:

        conexion = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        print("✓ Conectado correctamente a MySQL Railway")

        return conexion

    except mysql.connector.Error as error:

        print("✗ Error conectando a MySQL:")
        print(error)

        return None


# =====================================================
# MQTT - CONEXIÓN
# =====================================================

def al_conectar(client, userdata, flags, rc):

    if rc == 0:

        print("✓ Conectado correctamente a HiveMQ Cloud")

        client.subscribe(MQTT_TOPIC)

        print(f"✓ Suscrito a: {MQTT_TOPIC}")

    else:

        print(f"✗ Error de conexión MQTT. Código: {rc}")


# =====================================================
# MQTT - MENSAJE RECIBIDO
# =====================================================

def al_recibir(client, userdata, msg):

    try:

        datos = json.loads(msg.payload.decode())

        dispositivo = datos["dispositivo"]
        angulo = datos["angulo"]
        movimiento = datos["movimiento"]
        repeticiones = datos["repeticiones"]

        print()
        print("==============================")
        print("       DATO RECIBIDO")
        print("==============================")

        print(f"Dispositivo:  {dispositivo}")
        print(f"Ángulo:       {angulo}")
        print(f"Movimiento:   {movimiento}")
        print(f"Repeticiones: {repeticiones}")

        # =================================================
        # GUARDAR EN MYSQL
        # =================================================

        conexion = conectar_mysql()

        if conexion:

            cursor = conexion.cursor()

            sql = """
                INSERT INTO datos_mancuerna
                (dispositivo, angulo, movimiento, repeticiones)
                VALUES (%s, %s, %s, %s)
            """

            valores = (
                dispositivo,
                angulo,
                movimiento,
                repeticiones
            )

            cursor.execute(sql, valores)

            conexion.commit()

            print("✓ Datos guardados en MySQL Railway")

            cursor.close()
            conexion.close()

    except Exception as error:

        print("✗ Error procesando mensaje:")
        print(error)


# =====================================================
# CREAR CLIENTE MQTT
# =====================================================

client = mqtt.Client()

client.username_pw_set(
    MQTT_USER,
    MQTT_PASSWORD
)

client.tls_set(
    cert_reqs=ssl.CERT_REQUIRED
)

client.on_connect = al_conectar
client.on_message = al_recibir


# =====================================================
# INICIAR
# =====================================================

print("================================")
print("      MANCUERNA IoT CLOUD")
print("================================")

print("Conectando a HiveMQ Cloud...")

while True:

    try:

        client.connect(
            MQTT_BROKER,
            MQTT_PORT,
            60
        )

        break

    except Exception as error:

        print("Error conectando a HiveMQ:")
        print(error)

        print("Reintentando en 5 segundos...")

        time.sleep(5)


client.loop_forever()