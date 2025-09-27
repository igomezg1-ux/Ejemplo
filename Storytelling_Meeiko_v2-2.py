# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 12:35:49 2025

@author: Sala_603
"""

# app.py
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="CLV Chat & Storytelling", layout="wide")

# --------- Config y util ----------
DATA_PATH = "clv.csv"   # coloca aquí tu archivo CSV
CHAT_LOGS = "chat_logs.csv"

def ensure_chat_logs():
    if not os.path.exists(CHAT_LOGS):
        df = pd.DataFrame(columns=["timestamp","user_id","message","source"])
        df.to_csv(CHAT_LOGS, index=False)

def log_chat(user_id, message, source="widget"):
    ensure_chat_logs()
    df = pd.read_csv(CHAT_LOGS)
    df = df.append({
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "message": message,
        "source": source
    }, ignore_index=True)
    df.to_csv(CHAT_LOGS, index=False)

# ------- Sidebar nav -------
st.sidebar.title("Proyecto CLV - Marketing Analytics")
page = st.sidebar.radio("Ir a:", ["Chat","Storytelling","Admin / Logs"])

# ------------- PAGE: Chat (embed) -------------
if page == "Chat":
    st.title("ChatBot: Soporte & Detección de oportunidades")
    st.markdown(
        """
        **Instrucciones:** este espacio incrusta el widget público de ChatBot.com.
        - Si ya tienes el *snippet* (script/iframe) pégalo más abajo.
        - Si quieres que las conversaciones se guarden, activa el logging.
        """
    )

    # ----------------- CONFIG: pega tu snippet aquí -----------------
    chatbot_snippet = """
    <!-- REEMPLAZA ESTE BLOQUE CON EL SNIPPET EXACTO QUE TE PROPORCIONA app.chatbot.com -->
    <!-- Ejemplo (PARA REEMPLAZAR): <script src="https://widget.chatbot.com/..."></script> -->
    """
    # ----------------------------------------------------------------

    st.markdown("**Widget (preview)**")
    components.html(chatbot_snippet, height=600, scrolling=True)

    # Logging manual: si deseas guardar interacciones, puedes proporcionar un campo
    st.markdown("---")
    st.write("Registrar interacción manual (útil para pruebas con testers)")
    tester_id = st.text_input("Tu identificador (email o id de tester)", value="tester_1")
    tester_msg = st.text_input("Mensaje para loguear (solo para registro de prueba)")
    if st.button("Guardar log de prueba"):
        if tester_msg.strip():
            log_chat(tester_id, tester_msg, source="manual_test")
            st.success("Log guardado.")
        else:
            st.error("Ingresa un mensaje para guardar.")

    st.info("**Si quieres que el widget envíe logs automáticamente a este app, revisa la 'Chat Widget API' en app.chatbot.com para pasar eventos al frontend (requiere modificar el snippet y activar postMessage).**")

# ------------- PAGE: Storytelling -------------
elif page == "Storytelling":
    st.title("Storytelling - Insights a partir del dataset CLV")
    st.markdown("Cargue el CSV si desea usar otro archivo distinto a `clv.csv` en la carpeta.")

    uploaded = st.file_uploader("Sube un clv.csv (opcional)", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
    else:
        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH)
        else:
            st.warning(f"No encontré `{DATA_PATH}` en la carpeta. Puedes subir un CSV.")
            st.stop()

    st.write("**Vista previa (primeras filas)**")
    st.dataframe(df.head())

    # --- Asumimos columnas típicas; ajusta si tus nombres cambian ---
    # Columna esperada: customer_id, CLV (numérico), months_overdue (int), last_purchase_date, region, product_segment, age, avg_ticket
    # Si no las tienes, cambia estos nombres aquí:
    clv_col = "CLV"
    months_col = "months_overdue"
    region_col = "region"
    seg_col = "product_segment"
    age_col = "age"
    ticket_col = "avg_ticket"

    # Slide selector
    slide = st.selectbox("Selecciona slide / insight", ["1. Distribución de CLV", "2. Mora vs CLV (oportunidades)", "3. Segmentación por Región / Producto"])

    # --- Slide 1: Distribución de CLV ---
    if slide.startswith("1"):
        st.subheader("Slide 1 — Distribución de CLV")
        if clv_col not in df.columns:
            st.error(f"No encuentro la columna '{clv_col}' en tu dataset. Edita el nombre en el código si difiere.")
        else:
            fig = px.histogram(df, x=clv_col, nbins=40, marginal="box", title="Distribución de CLV")
            st.plotly_chart(fig, use_container_width=True)
            q1 = df[clv_col].quantile(0.25)
            q3 = df[clv_col].quantile(0.75)
            st.markdown(f"- **Media CLV:** {df[clv_col].mean():.2f}  \n- **Mediana:** {df[clv_col].median():.2f}  \n- **Q1:** {q1:.2f}, **Q3:** {q3:.2f}")
            st.markdown("**Insight sugerido:** identifica el tercio superior de clientes (high CLV) y crea ofertas para retención; revisa si están concentrados en segmentos/productos específicos.")

    # --- Slide 2: Mora vs CLV ---
    elif slide.startswith("2"):
        st.subheader("Slide 2 — Mora (months_overdue) vs CLV")
        if months_col not in df.columns or clv_col not in df.columns:
            st.error(f"Revisa que existan las columnas '{months_col}' y '{clv_col}'.")
        else:
            fig = px.scatter(df, x=months_col, y=clv_col, trendline="ols",
                             labels={months_col: "Meses vencidos", clv_col: "CLV"},
                             title="Relacion: Meses vencidos vs CLV")
            st.plotly_chart(fig, use_container_width=True)
            corr = df[[months_col, clv_col]].dropna().corr().iloc[0,1]
            st.markdown(f"- **Correlación Pearson (months_overdue vs CLV):** {corr:.3f}")
            st.markdown("**Insight sugerido:** si la correlación es negativa, clientes con mayor CLV tienden a tener menor mora — prioriza recuperaciones por segmentos de baja CLV con alta mora.")

    # --- Slide 3: Segmentación ---
    elif slide.startswith("3"):
        st.subheader("Slide 3 — Segmentación por Región y Producto")
        if region_col not in df.columns:
            st.error(f"No encuentro '{region_col}'.")
        else:
            # Top regiones por CLV medio
            df_region = df.groupby(region_col).agg(mean_clv=(clv_col,"mean"), count=("customer_id","count")).reset_index().sort_values("mean_clv", ascending=False)
            fig1 = px.bar(df_region, x=region_col, y="mean_clv", title="CLV medio por Región", hover_data=["count"])
            st.plotly_chart(fig1, use_container_width=True)

            # Segmento-producto: heatmap of mean CLV
            if seg_col in df.columns:
                pivot = df.pivot_table(values=clv_col, index=seg_col, columns=region_col, aggfunc="mean")
                st.write("CLV medio por Segmento x Región (tabla):")
                st.dataframe(pivot.fillna(0).round(2))
                st.markdown("**Insight sugerido:** detectar combinaciones región-segmento con alto CLV y baja inversión/comunicación — oportunidad para escalar.")
            else:
                st.info("No se encontró columna de segmentación de producto; omitiendo heatmap.")

    # Allow download of charts data
    st.markdown("---")
    if st.button("Exportar resumen (CSV)"):
        summary_path = "story_summary_export.csv"
        # small export: estadísticas por región
        if region_col in df.columns and clv_col in df.columns:
            summary = df.groupby(region_col).agg(mean_clv=(clv_col,"mean"), customers=("customer_id","count")).reset_index()
            summary.to_csv(summary_path, index=False)
            st.success(f"Exportado a {summary_path}")
        else:
            st.error("No hay columnas suficientes para exportar resumen.")

# ------------- PAGE: Admin / Logs -------------
elif page == "Admin / Logs":
    st.title("Admin - Logs y métricas")
    st.subheader("Chat logs (últimas entradas)")
    ensure_chat_logs()
    logs = pd.read_csv(CHAT_LOGS)
    st.dataframe(logs.tail(50))
    st.markdown("**Métricas básicas:**")
    st.metric("Total interacciones registradas", len(logs))
    st.metric("Usuarios únicos (log)", logs["user_id"].nunique() if not logs.empty else 0)
    if st.button("Descargar logs (.csv)"):
        st.download_button("Descargar", data=logs.to_csv(index=False), file_name="chat_logs.csv")


