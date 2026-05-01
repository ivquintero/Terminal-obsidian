import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import requests

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="OBSIDIANA QUANT TERMINAL", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #060608; }
    [data-testid="stMetric"] {
        background-color: #0d0d12 !important;
        border: 1px solid #1e1e26 !important;
        border-radius: 4px !important;
        padding: 15px !important;
    }
    div.stButton > button {
        background-color: #000000; color: #00ffff;
        border: 1px solid #00ffff; border-radius: 2px;
        width: 100%; font-family: 'Courier New', monospace;
    }
    div.stButton > button:hover { background-color: #00ffff; color: #000; }
    h1, h2, h3 { font-family: 'Courier New', monospace; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE BÚSQUEDA UNIVERSAL ---
def universal_search(key_suffix):
    """Maneja la lógica de búsqueda de Yahoo Finance de forma global"""
    query = st.text_input("BUSCAR ACTIVO:", placeholder="Ej: Nvidia, Oro, BTC...", key=f"search_{key_suffix}").strip()
    if query:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers).json()
            return res.get('quotes', [])
        except:
            st.error("Error de conexión con el servidor de datos.")
    return []

# --- FUNCIONES DE CÁLCULO ---
def get_data(ticker):
    data = yf.download(ticker, period="1y", progress=False)
    if data.empty: raise ValueError("No hay datos")
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
    df = data['Close'].dropna().astype(float)
    returns = np.log(df / df.shift(1)).dropna()
    return df, returns

def monte_carlo(last_price, mu, sigma, days, n_sims):
    res = np.zeros((days, n_sims))
    res[0] = last_price
    for t in range(1, days):
        res[t] = res[t-1] * np.exp(np.random.normal(mu, sigma, n_sims))
    return res

# --- ESTRUCTURA DE NAVEGACIÓN ---
if "mis_activos" not in st.session_state: st.session_state.mis_activos = ["BTC-USD"]
if "pro" not in st.session_state: st.session_state.pro = False

st.title("♰ OBSIDIANA QUANTITATIVE TERMINAL v3.1")

with st.sidebar:
    st.header("CONTROLES")
    modo = st.radio("MÓDULO", ["ESCÁNER", "TERMINAL INDIVIDUAL", "COMPARADOR"])
    st.markdown("---")

# --- MÓDULO 1: ESCÁNER ---
if modo == "ESCÁNER":
    st.header("♰ LIVE QUANTUM MONITOR")
    with st.sidebar:
        st.subheader("♰ VINCULADOR")
        resultados = universal_search("scan")
        for res in resultados[:5]:
            if st.button(f"➕ {res.get('symbol')}", key=f"btn_scan_{res['symbol']}"):
                if res['symbol'] not in st.session_state.mis_activos:
                    st.session_state.mis_activos.append(res['symbol'])
                    st.rerun()
        if st.button("LIMPIAR MONITOR"):
            st.session_state.mis_activos = ["BTC-USD"]; st.rerun()

    # Renderizado del Monitor
    cols = st.columns(4)
    for i, ticker in enumerate(st.session_state.mis_activos):
        try:
            data = yf.download(ticker, period="2d", interval="15m", progress=False)
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            price = float(data['Close'].iloc[-1])
            change = ((price / data['Close'].iloc[0]) - 1) * 100
            color = "#00ffff" if change >= 0 else "#ff4b4b"
            with cols[i % 4]:
                st.markdown(f"""<div style="border:1px solid {color}55; padding:15px; background:#0a0a0c; border-radius:4px; margin-bottom:10px;">
                    <p style="margin:0; font-size:10px; color:#666;">{ticker}</p>
                    <h3 style="margin:5px 0; color:white; font-size:20px;">${price:,.2f}</h3>
                    <p style="margin:0; font-size:11px; color:{color};">CHG: {change:+.2f}%</p>
                </div>""", unsafe_allow_html=True)
        except: continue

# --- MÓDULO 2: TERMINAL INDIVIDUAL ---
elif modo == "TERMINAL INDIVIDUAL":
    st.header("♰ TRADING TERMINAL")
    with st.sidebar:
        st.subheader("♰ SELECCIÓN")
        resultados = universal_search("term")
        ticker_final = st.session_state.get('target', "BTC-USD")
        if resultados:
            opciones = {f"{r.get('shortname')} ({r['symbol']})": r['symbol'] for r in resultados}
            sel = st.selectbox("RESULTADOS:", options=list(opciones.keys()))
            ticker_final = opciones[sel]
            st.session_state.target = ticker_final
    
    # Lógica de Gráfico (Simplificada para estabilidad)
    df, ret = get_data(ticker_final)
    st.metric(f"PRECIO ACTUAL {ticker_final}", f"${df.iloc[-1]:,.2f}")
    fig = go.Figure(data=[go.Scatter(x=df.index, y=df, line=dict(color='#00ffff'))])
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- MÓDULO 3: COMPARADOR ---
elif modo == "COMPARADOR":
    st.header("♰ MULTI-ASSET COMPARISON")
    if "comp_list" not in st.session_state: st.session_state.comp_list = []
    
    with st.sidebar:
        resultados = universal_search("comp")
        for res in resultados[:5]:
            if st.button(f"📊 AÑADIR {res['symbol']}", key=f"btn_comp_{res['symbol']}"):
                if res['symbol'] not in st.session_state.comp_list:
                    st.session_state.comp_list.append(res['symbol'])
        if st.button("RESET"): st.session_state.comp_list = []; st.rerun()

    if st.session_state.comp_list:
        resumen = []
        for t in st.session_state.comp_list:
            try:
                df, ret = get_data(t)
                resumen.append({"ACTIVO": t, "PRECIO": df.iloc[-1], "VOLATILIDAD": ret.std() * np.sqrt(252)})
            except: continue
        st.table(pd.DataFrame(resumen))
    else:
        st.info("Añade activos desde la barra lateral para comparar.")

st.markdown("---")
st.caption("TERMINAL OBSIDIANA © 2026 | Estabilidad Cuántica v3.1")
