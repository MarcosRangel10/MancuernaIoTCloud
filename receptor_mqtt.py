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

# Escucha cualquier dispositivo Mancuerna
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

        return conexion

    except mysql.connector.Error as error:

        print("✗ Error conectando a MySQL:", error)

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

        # -------------------------------------------------
        # Convertir JSON
        # -------------------------------------------------

        datos = json.loads(msg.payload.decode())

        print("\n========================================")
        print("       DATOS RECIBIDOS DESDE ESP32")
        print("========================================")

        print("Topic:", msg.topic)

        print("JSON:")
        print(json.dumps(datos, indent=2, ensure_ascii=False))


        # -------------------------------------------------
        # Datos principales
        # -------------------------------------------------

        dispositivo = datos.get("dispositivo", "Desconocido")

        ejercicio = datos.get("ejercicio", "ninguno")

        angulo = datos.get("angulo", 0.0)

        movimiento = datos.get("movimiento", False)

        repeticiones = datos.get("repeticiones", 0)

        objetivo = datos.get("objetivo", 0)

        correctas = datos.get("correctas", 0)

        rapidas = datos.get("rapidas", 0)

        lentas = datos.get("lentas", 0)

        estado = datos.get("estado", "ESPERA")

        subida = datos.get("subida", 0.0)

        bajada = datos.get("bajada", 0.0)

        aceleracion = datos.get("aceleracion", 0.0)

        velocidad_angular = datos.get("velocidad_angular", 0.0)


        # -------------------------------------------------
        # Mostrar resumen
        # -------------------------------------------------

        print("\n--- RESUMEN ---")

        print(f"Dispositivo: {dispositivo}")
        print(f"Ejercicio: {ejercicio}")
        print(f"Ángulo: {angulo}°")
        print(f"Movimiento: {movimiento}")
        print(f"Repeticiones: {repeticiones}")
        print(f"Objetivo: {objetivo}")
        print(f"Correctas: {correctas}")
        print(f"Rápidas: {rapidas}")
        print(f"Lentas: {lentas}")
        print(f"Estado: {estado}")
        print(f"Subida: {subida} s")
        print(f"Bajada: {bajada} s")
        print(f"Aceleración: {aceleracion}")
        print(f"Velocidad angular: {velocidad_angular}")


        # -------------------------------------------------
        # CONECTAR A MYSQL
        # -------------------------------------------------

        conexion = conectar_mysql()

        if conexion:

            cursor = conexion.cursor()

            sql = """
                INSERT INTO datos_mancuerna
                (
                    dispositivo,
                    ejercicio,
                    angulo,
                    movimiento,
                    repeticiones,
                    objetivo,
                    correctas,
                    rapidas,
                    lentas,
                    estado,
                    subida,
                    bajada,
                    aceleracion,
                    velocidad_angular
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
            """

            valores = (
                dispositivo,
                ejercicio,
                angulo,
                movimiento,
                repeticiones,
                objetivo,
                correctas,
                rapidas,
                lentas,
                estado,
                subida,
                bajada,
                aceleracion,
                velocidad_angular
            )

            cursor.execute(sql, valores)

            conexion.commit()

            cursor.close()
            conexion.close()

            print("✓ Datos guardados correctamente en MySQL")

        else:

            print("✗ No se pudieron guardar los datos en MySQL")


    except json.JSONDecodeError:

        print("✗ El mensaje recibido no contiene un JSON válido")

    except Exception as error:

        print("✗ Error procesando mensaje:", error)


# =====================================================
# CONFIGURACIÓN CLIENTE MQTT
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
# CONEXIÓN A HIVE MQ
# =====================================================

print("========================================")
print("       MANCUERNA IoT CLOUD")
print("========================================")

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

        print(
            "Error conectando a HiveMQ. "
            "Reintentando en 5 segundos...",
            error
        )

        time.sleep(5)


# =====================================================
# ESPERAR MENSAJES
# =====================================================

print("Esperando datos del ESP32...")

client.loop_forever()