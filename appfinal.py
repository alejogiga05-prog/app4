
import streamlit as st
import pandas as pd
import random
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from sklearn.linear_model import LinearRegression

# ==============================================
# 🔧 CONFIGURACIÓN DE CONEXIÓN A INFLUXDB CLOUD
# ==============================================
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUXDB_TOKEN = "JcKXoXE30JQvV9Ggb4-zv6sQc0Zh6B6Haz5eMRW0FrJEduG2KcFJN9-7RoYvVORcFgtrHR-Q_ly-52pD7IC6JQ=="
INFLUXDB_ORG = "0925ccf91ab36478"
INFLUXDB_BUCKET = "EXTREME_MANUFACTURING"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# ==============================================
# 📈 SIMULAR DATOS SIN NUMPY
# ==============================================
def generar_datos():
    """Genera datos aleatorios de sensores."""
    return {
        "temperatura": round(random.uniform(25, 40), 2),
        "humedad": round(random.uniform(45, 90), 2),
        "vibracion": round(random.uniform(0.5, 5.0), 2),
        "corriente": round(random.uniform(4.0, 10.0), 2),
        "voltaje": round(random.uniform(220, 240), 2)
    }

# ==============================================
# 💾 GUARDAR DATOS EN INFLUXDB
# ==============================================
def guardar_datos_influx(datos):
    point = (
        Point("lecturas_sensores")
        .tag("equipo", "motor_principal")
        .field("temperatura", datos["temperatura"])
        .field("humedad", datos["humedad"])
        .field("vibracion", datos["vibracion"])
        .field("corriente", datos["corriente"])
        .field("voltaje", datos["voltaje"])
        .time(datetime.utcnow(), WritePrecision.NS)
    )
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

# ==============================================
# 📥 LEER DATOS DESDE INFLUXDB
# ==============================================
def leer_datos_influx():
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r["_measurement"] == "lecturas_sensores")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: false)
    '''
    result = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
    if result.empty:
        return pd.DataFrame()
    result["_time"] = pd.to_datetime(result["_time"])
    result.rename(columns={"_time": "tiempo"}, inplace=True)
    return result

# ==============================================
# 🚨 DETECTAR ANOMALÍAS
# ==============================================
def detectar_anomalias(df):
    condiciones = []
    for _, row in df.iterrows():
        if row["temperatura"] > 38 or row["vibracion"] > 4.5 or row["humedad"] > 85:
            condiciones.append("⚠️ Anomalía detectada")
        else:
            condiciones.append("Normal")
    df["estado"] = condiciones
    return df

# ==============================================
# 🧠 REGRESIÓN LINEAL (PREDICCIÓN SIMPLE)
# ==============================================
def predecir_tendencia(df, variable):
    if len(df) < 5:
        return None
    X = [[i] for i in range(len(df))]
    y = df[variable].tolist()
    modelo = LinearRegression().fit(X, y)
    prediccion = modelo.predict([[len(df) + 1]])[0]
    return round(prediccion, 2)

# ==============================================
# 🎛️ INTERFAZ STREAMLIT
# ==============================================
st.title("🌐 Monitoreo Predictivo Industrial con InfluxDB (sin NumPy)")
st.write("""
Sistema de monitoreo predictivo que:
- Simula lecturas de sensores industriales  
- Detecta anomalías y calcula promedios, máximos y mínimos  
- Predice tendencias futuras con **regresión lineal**  
- Usa InfluxDB como base de datos de series temporales
""")

# --- Generar lectura simulada ---
if st.button("🔄 Generar nueva lectura simulada"):
    datos = generar_datos()
    guardar_datos_influx(datos)
    st.success("✅ Nueva lectura registrada correctamente.")

# --- Leer datos de InfluxDB ---
df = leer_datos_influx()

if not df.empty:
    df = detectar_anomalias(df)
    st.subheader("📊 Últimas lecturas de sensores")
    st.dataframe(df.tail(10)[["tiempo", "temperatura", "humedad", "vibracion", "corriente", "voltaje", "estado"]])

    # Estadísticas
    st.subheader("📈 Estadísticas Generales")
    estadisticas = df[["temperatura", "humedad", "vibracion", "corriente", "voltaje"]].agg(["mean", "max", "min"]).T
    estadisticas.columns = ["Promedio", "Máximo", "Mínimo"]
    st.table(estadisticas)

    # Predicción
    st.subheader("🤖 Predicción de Temperatura (Regresión Lineal)")
    pred_temp = predecir_tendencia(df, "temperatura")
    if pred_temp:
        st.info(f"🔮 Temperatura estimada próxima: **{pred_temp} °C**")
    else:
        st.warning("📉 Se necesitan más datos para generar predicciones.")

    # Gráficos
    st.subheader("📉 Tendencias de Variables")
    for var in ["temperatura", "humedad", "vibracion", "corriente", "voltaje"]:
        st.line_chart(df.set_index("tiempo")[var])
else:
    st.info("📭 No hay datos registrados aún. Genera una lectura simulada para comenzar.")

st.caption("Desarrollado por Alejandro Giraldo — Monitoreo Predictivo con InfluxDB y Streamlit (sin NumPy)")
