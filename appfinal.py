import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient
import plotly.express as px

# --- Configuración de conexión ---
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUXDB_TOKEN = "JcKXoXE30JQvV9Ggb4-zv6sQc0Zh6B6Haz5eMRW0FrJEduG2KcFJN9-7RoYvVORcFgtrHR-Q_ly-52pD7IC6JQ=="
INFLUXDB_ORG = "0925ccf91ab36478"
INFLUXDB_BUCKET = "EXTREME_MANUFACTURING"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()


client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# ==========================================
# 📈 FUNCIÓN PARA GENERAR DATOS SIMULADOS
# ==========================================
def generar_datos():
    """Genera valores aleatorios de sensores industriales."""
    return {
        "temperatura": round(random.uniform(25, 40), 2),
        "humedad": round(random.uniform(45, 90), 2),
        "vibracion": round(random.uniform(0.5, 5.0), 2),
        "corriente": round(random.uniform(4.0, 10.0), 2),
        "voltaje": round(random.uniform(220, 240), 2)
    }

# ==========================================
# 💾 GUARDAR DATOS EN INFLUXDB
# ==========================================
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

# ==========================================
# 📥 LEER TODOS LOS DATOS DESDE INFLUXDB
# ==========================================
def leer_todos_los_datos():
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: 0)
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

# ==========================================
# ⚠️ DETECTAR ANOMALÍAS
# ==========================================
def detectar_anomalias(df):
    """Detecta anomalías simples por umbrales definidos."""
    condiciones = []
    for _, row in df.iterrows():
        if row["temperatura"] > 38 or row["vibracion"] > 4.5 or row["humedad"] > 85:
            condiciones.append("⚠️ Anomalía detectada")
        else:
            condiciones.append("Normal")
    df["estado"] = condiciones
    return df

# ==========================================
# 🤖 REGRESIÓN LINEAL (PREDICCIÓN)
# ==========================================
def predecir_tendencia(df, variable):
    """Predice la siguiente lectura usando regresión lineal simple."""
    if len(df) < 5:
        return None
    X = [[i] for i in range(len(df))]
    y = df[variable].tolist()
    modelo = LinearRegression().fit(X, y)
    prediccion = modelo.predict([[len(df) + 1]])[0]
    return round(prediccion, 2)

# ==========================================
# 🎛️ INTERFAZ STREAMLIT
# ==========================================
st.title("🌐 Monitoreo Predictivo Industrial — InfluxDB (sin NumPy)")
st.write("""
Aplicación de simulación y monitoreo en tiempo real que:
- Registra y muestra todos los datos históricos de sensores
- Detecta anomalías
- Calcula promedios, máximos y mínimos
- Predice tendencias con regresión lineal
""")

# --- Botón para generar nueva lectura simulada ---
if st.button("🔄 Generar nueva lectura simulada"):
    datos = generar_datos()
    guardar_datos_influx(datos)
    st.success("✅ Nueva lectura registrada en InfluxDB.")

# --- Consultar todos los datos guardados ---
df = leer_todos_los_datos()

if not df.empty:
    df = detectar_anomalias(df)
    st.subheader("📋 Todos los datos registrados")
    st.dataframe(df[["tiempo", "temperatura", "humedad", "vibracion", "corriente", "voltaje", "estado"]])

    # --- Estadísticas generales ---
    st.subheader("📊 Estadísticas Generales")
    estadisticas = df[["temperatura", "humedad", "vibracion", "corriente", "voltaje"]].agg(["mean", "max", "min"]).T
    estadisticas.columns = ["Promedio", "Máximo", "Mínimo"]
    st.table(estadisticas)

    # --- Predicción ---
    st.subheader("🤖 Predicción de próxima lectura")
    pred_temp = predecir_tendencia(df, "temperatura")
    pred_vib = predecir_tendencia(df, "vibracion")
    if pred_temp and pred_vib:
        st.info(f"🔮 Temperatura estimada próxima: **{pred_temp} °C**")
        st.info(f"🔮 Vibración estimada próxima: **{pred_vib} mm/s**")
    else:
        st.warning("📉 Se necesitan más datos para realizar predicciones.")

    # --- Gráficos de tendencia ---
    st.subheader("📉 Tendencias de las variables")
    for var in ["temperatura", "humedad", "vibracion", "corriente", "voltaje"]:
        st.line_chart(df.set_index("tiempo")[var])

else:
    st.info("📭 No hay datos registrados todavía. Genera una lectura para comenzar.")

st.caption("Desarrollado por Alejandro Giraldo — Monitoreo Predictivo con InfluxDB y Streamlit (sin NumPy)")
