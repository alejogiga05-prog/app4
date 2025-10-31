import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient
from sklearn.linear_model import LinearRegression
from dotenv import load_dotenv
import os

# ==============================================================
# CONFIGURACIÓN INICIAL
# ==============================================================
st.title("📊 Monitoreo Predictivo con InfluxDB")
st.write("""
Aplicación de monitoreo inteligente que obtiene datos desde InfluxDB, 
analiza promedios, valores extremos, detecta anomalías y predice 
tendencias futuras en variables industriales.
""")

# Cargar credenciales desde .env o Secrets de Streamlit
load_dotenv()
url = os.getenv("INFLUX_URL")
token = os.getenv("INFLUX_TOKEN")
org = os.getenv("INFLUX_ORG")
bucket = os.getenv("INFLUX_BUCKET")

# ==============================================================
# CONEXIÓN A INFLUXDB
# ==============================================================
try:
    client = InfluxDBClient(url=url, token=token, org=org)
    query_api = client.query_api()
    st.success("✅ Conexión exitosa a InfluxDB")
except Exception as e:
    st.error(f"❌ Error al conectar con InfluxDB: {e}")

# ==============================================================
# CONSULTA DE DATOS
# ==============================================================
query = f'''
from(bucket: "{bucket}")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "sensores")
  |> filter(fn: (r) => r["_field"] =~ /temperatura|humedad|vibracion|corriente|voltaje/)
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "temperatura", "humedad", "vibracion", "corriente", "voltaje"])
'''

try:
    tables = query_api.query_data_frame(query)
    if len(tables) == 0:
        st.warning("⚠️ No se encontraron datos en InfluxDB. Se usarán datos simulados.")
        # Datos de ejemplo si la base está vacía
        fechas = pd.date_range("2025-10-01", periods=10, freq="D")
        data = {
            "_time": fechas,
            "temperatura": [28, 29, 30, 32, 33, 31, 30, 29, 28, 27],
            "humedad": [55, 58, 60, 62, 59, 61, 63, 65, 60, 58],
            "vibracion": [1.2, 1.3, 1.5, 1.7, 1.8, 1.6, 1.5, 1.4, 1.3, 1.2],
            "corriente": [5.5, 5.8, 6.0, 6.2, 6.5, 6.1, 5.9, 5.8, 5.6, 5.7],
            "voltaje": [230, 231, 229, 228, 232, 233, 230, 229, 231, 230]
        }
        df = pd.DataFrame(data)
    else:
        df = tables
except Exception as e:
    st.error(f"❌ Error al consultar datos: {e}")
    st.stop()

df.rename(columns={"_time": "Tiempo"}, inplace=True)
st.subheader("📋 Datos obtenidos")
st.dataframe(df)

# ==============================================================
# ESTADÍSTICAS GENERALES
# ==============================================================
st.subheader("📈 Estadísticas Generales")

variables = ["temperatura", "humedad", "vibracion", "corriente", "voltaje"]
cols = st.columns(5)
for i, var in enumerate(variables):
    prom = df[var].mean()
    minimo = df[var].min()
    maximo = df[var].max()
    cols[i].metric(var.capitalize(), f"{prom:.2f}", f"Min {minimo:.2f} / Max {maximo:.2f}")

# ==============================================================
# DETECCIÓN DE ANOMALÍAS
# ==============================================================
st.subheader("⚠️ Detección de Anomalías")
anomalias = []
for var in variables:
    media = df[var].mean()
    std = df[var].std()
    lim_inf = media - 2 * std
    lim_sup = media + 2 * std
    df[f"Anómalo {var}"] = (df[var] < lim_inf) | (df[var] > lim_sup)

    # Registrar anomalías encontradas
    filas_anom = df[df[f"Anómalo {var}"]]
    for _, row in filas_anom.iterrows():
        anomalias.append({
            "Fecha": row["Tiempo"],
            "Variable": var,
            "Valor": row[var],
            "Descripción": "Valor fuera de rango normal"
        })

if anomalias:
    st.error("🚨 Se detectaron anomalías en las lecturas")
    st.table(pd.DataFrame(anomalias))
else:
    st.success("✅ No se detectaron anomalías")

# ==============================================================
# ANÁLISIS PREDICTIVO (Regresión Lineal)
# ==============================================================
st.subheader("🔮 Predicción de Tendencias Futuras (Regresión Lineal)")

predicciones = []
for var in variables:
    X = pd.DataFrame(range(len(df)))
    y = df[var]
    modelo = LinearRegression()
    modelo.fit(X, y)
    futuro = modelo.predict([[len(df) + 1]])[0]
    predicciones.append((var, futuro))

st.write("**Predicciones para la siguiente lectura:**")
for var, pred in predicciones:
    st.write(f"➡️ {var.capitalize()}: {pred:.2f}")

# ==============================================================
# CONCLUSIÓN FINAL
# ==============================================================
st.markdown("---")
st.caption("Desarrollado por Alejandro Giraldo — Sistema de monitoreo conectado a InfluxDB con análisis predictivo.")
