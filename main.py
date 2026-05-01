import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import skew, kurtosis
from datetime import datetime
import time # Necesario para el temporizador
import requests

# --- CONFIGURACIÓN ESTÉTICA GÓTICA ---
st.set_page_config(page_title="OBSIDIANA QUANT TERMINAL", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { border: 1px solid #222; padding: 15px; background-color: #050505; }
    div.stButton > button {
        background-color: #000000; color: #00ffff;
        border: 1px solid #00ffff; border-radius: 0px;
        width: 100%; font-family: 'Courier New', monospace;
    }
    div.stButton > button:hover { background-color: #00ffff; color: #000; }
    h1, h2, h3 { font-family: 'Courier New', monospace; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
st.title("♰ OBSIDIANA QUANTITATIVE TERMINAL v3.0")
st.caption("PHYSICS-BASED FINANCIAL INTELLIGENCE | ENTORNO PROFESIONAL")

# --- LÓGICA DE SUSCRIPCIÓN (SIMULADA) ---
if "pro" not in st.session_state:
    st.session_state.pro = False

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("CONTROLES")
    modo = st.radio("MÓDULO", ["ESCÁNER", "TERMINAL INDIVIDUAL", "COMPARADOR"])
    st.markdown("---")
    if not st.session_state.pro:
        st.warning("PLAN BÁSICO")
        if st.button("UPGRADE TO PRO"):
            st.session_state.pro = True
            st.rerun()
    else:
        st.success("♰ ACCESO PRO ACTIVADO")

# --- FUNCIONES DE CÁLCULO ---
def get_data(ticker):
    # Forzamos la descarga y eliminamos el multi-índice que causa el error
    data = yf.download(ticker, period="1y", progress=False)
    
    if data.empty:
        raise ValueError("No hay datos")

    # Si yfinance entrega varias columnas (Close, Adj Close, etc.)
    # nos aseguramos de tomar solo 'Close' y aplanarlo
    if 'Close' in data.columns:
        close_data = data['Close']
    else:
        close_data = data.iloc[:, 0] # Si falla, toma la primera columna disponible

    # Convertimos a Serie de Pandas por si viene como DataFrame de una columna
    if isinstance(close_data, pd.DataFrame):
        close_data = close_data.iloc[:, 0]

    # Limpieza final: eliminamos NaNs y forzamos a float64
    df = close_data.dropna().astype(float)
    
    # Calculamos retornos logarítmicos
    returns = np.log(df / df.shift(1)).dropna()
    
    return df, returns
def monte_carlo(last_price, mu, sigma, days, n_sims):
    res = np.zeros((days, n_sims))
    res[0] = last_price
    for t in range(1, days):
        res[t] = res[t-1] * np.exp(np.random.normal(mu, sigma, n_sims))
    return res


# --- MÓDULO 1: ESCÁNER MULTITEMPORAL ---
if modo == "ESCÁNER":
    st.header("♰ LIVE QUANTUM MONITOR")
    
    with st.sidebar:
        st.subheader("♰ ACCESO GLOBAL YAHOO")
        
        # 1. Entrada de texto para buscar en la base de datos de Yahoo
        query = st.text_input("BUSCAR PRODUCTO (Nombre o Ticker):", placeholder="Ej: Palantir, Yuan, Nintendo...")

        sugerencias_yahoo = []
        
        if query:
            # 2. CONSULTA EN TIEMPO REAL A YAHOO FINANCE
            # Esta URL es la que usa el buscador de Yahoo para autocompletar
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            try:
                response = requests.get(url, headers=headers)
                data = response.json()
                # Extraemos los resultados (quotes)
                # Cada resultado tiene el ticker (symbol) y el nombre (shortname)
                sugerencias_yahoo = [
                    f"{res['shortname']} ({res['symbol']})" 
                    for res in data.get('quotes', []) 
                    if 'symbol' in res and 'shortname' in res
                ]
            except:
                st.error("Error de conexión con la base de datos.")

        # 3. Mostrar los resultados encontrados en Yahoo
        if sugerencias_yahoo:
            seleccion = st.selectbox("RESULTADOS ENCONTRADOS:", options=[""] + sugerencias_yahoo)
            
            if seleccion != "":
                # Extraer el ticker de entre los paréntesis
                ticker_final = seleccion.split("(")[-1].replace(")", "")
                
                # Gestión de la lista del monitor
                if "mis_activos" not in st.session_state:
                    st.session_state.mis_activos = []
                
                if st.button(f"➕ VINCULAR {ticker_final}"):
                    if ticker_final not in st.session_state.mis_activos:
                        st.session_state.mis_activos.append(ticker_final)
                        st.success(f"{ticker_final} añadido.")
                        st.rerun()
        elif query:
            st.warning("No se encontraron productos con ese nombre.")

        # Control del Monitor
        if st.button("🗑️ RESET MONITOR"):
            st.session_state.mis_activos = []
            st.rerun()

    # Los activos que el monitor va a pintar
    lista_activos = st.session_state.get("mis_activos", ["BTC-USD"])

    # --- RENDERIZADO DEL MONITOR ---
    refresh_rate = st.sidebar.slider("REFRESCO (SEG)", 5, 60, 20)
    
    @st.fragment(run_every=refresh_rate)
    def render_live_scanner():
        if not lista_activos:
            st.info("Buscador listo. Accede a cualquier producto de Yahoo Finance.")
            return

        cols = st.columns(4)
        for i, ticker in enumerate(lista_activos):
            try:
                # Aquí descargamos los datos del ticker que Yahoo nos dio
                data = yf.download(ticker, period="1d", interval="1m", progress=False)
                if not data.empty:
                    # (Tu código de Monte Carlo y tarjetas aquí...)
                    with cols[i % 4]:
                        st.write(f"**{ticker}**") 
                        # ... resto de la lógica ...
            except:
                continue

    render_live_scanner()

# --- MÓDULO 3: COMPARADOR ---
elif modo == "COMPARADOR":
    st.header("♰ MULTI-ASSET COMPARISON")
    lista = st.text_input("TICKERS SEPARADOS POR COMA", "BTC-USD, ETH-USD, TSLA")
    
    if st.button("COMPARAR MATRIZ"):
        tickers = [t.strip().upper() for t in lista.split(",")]
        resumen = []
        for t in tickers:
            _, ret = get_data(t)
            resumen.append({
                "ACTIVO": t,
                "VOLATILIDAD": f"{ret.std()*np.sqrt(252)*100:.1f}%",
                "SHARPE": round((ret.mean()*252)/(ret.std()*np.sqrt(252)), 2),
                "MAX DRAWDOWN": f"{(ret.min()*100):.1f}%"
            })
        st.table(pd.DataFrame(resumen))

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("TERMINAL OBSIDIANA © 2026 | Powered by Quant Physics Engine")
