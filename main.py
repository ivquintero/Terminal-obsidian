import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import skew, kurtosis
from datetime import datetime
import time # Necesario para el temporizador

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
        st.subheader("♰ BUSCADOR INTELIGENTE")
        
        # 1. Base de datos de "Correlación" (Nombres vs Tickers)
        # Esta lista es la que el buscador usará para darte opciones abajo
        db_global = {
            "Yuan Chino (CNYUSD=X)": "CNYUSD=X",
            "Palantir Technologies (PLTR)": "PLTR",
            "Bitcoin (BTC-USD)": "BTC-USD",
            "Ethereum (ETH-USD)": "ETH-USD",
            "NVIDIA Corp (NVDA)": "NVDA",
            "Apple Inc (AAPL)": "AAPL",
            "Tesla Inc (TSLA)": "TSLA",
            "Oro Comex (GC=F)": "GC=F",
            "Plata (SI=F)": "SI=F",
            "Peso Mexicano (USDMXN=X)": "USDMXN=X",
            "Euro / US Dollar (EURUSD=X)": "EURUSD=X",
            "S&P 500 Index (^GSPC)": "^GSPC",
            "Nasdaq 100 (^IXIC)": "^IXIC",
            "Amazon (AMZN)": "AMZN",
            "Microsoft (MSFT)": "MSFT",
            "Google Alphabet (GOOGL)": "GOOGL",
            "Netflix (NFLX)": "NFLX",
            "MicroStrategy (MSTR)": "MSTR"
        }

        # 2. El Buscador (Filtra mientras escribes)
        opcion_busqueda = st.selectbox(
            "ESCRIBE NOMBRE O PRODUCTO:",
            options=[""] + list(db_global.keys()),
            format_func=lambda x: "🔎 Buscar..." if x == "" else x,
            help="Escribe 'yuan', 'palantir' o cualquier nombre aquí."
        )

        # 3. Lista de activos seleccionados (Aquí se guardan los que elijas)
        if "mis_activos" not in st.session_state:
            st.session_state.mis_activos = ["BTC-USD", "PLTR"]

        # Botón para añadir la opción seleccionada arriba
        if opcion_busqueda != "":
            ticker_elegido = db_global[opcion_busqueda]
            if ticker_elegido not in st.session_state.mis_activos:
                if st.button(f"➕ AÑADIR {ticker_elegido}"):
                    st.session_state.mis_activos.append(ticker_elegido)
                    st.rerun()

        # Botón para limpiar la lista
        if st.button("🗑️ LIMPIAR MONITOR"):
            st.session_state.mis_activos = []
            st.rerun()

    lista_activos = st.session_state.mis_activos
    refresh_rate = st.sidebar.slider("REFRESCO (SEG)", 5, 60, 20)
    
    # --- LA FUNCIÓN DE RENDERIZADO SE MANTIENE IGUAL ---
    @st.fragment(run_every=refresh_rate)
    def render_live_scanner():
        if not lista_activos:
            st.info("La terminal está en espera. Busca y añade activos desde la barra lateral.")
            return

        cols = st.columns(4)
        for i, ticker in enumerate(lista_activos):
            try:
                data = yf.download(ticker, period="1d", interval="1m", progress=False)
                if not data.empty:
                    # (Aquí va toda tu lógica de Monte Carlo y renderizado de tarjetas que ya tienes)
                    # ...
                    with cols[i % 4]:
                        st.markdown(f"**{ticker}**") # Ejemplo simple para que veas que funciona
            except:
                continue

    render_live_scanner()
# --- MÓDULO 2: TERMINAL INDIVIDUAL ---
elif modo == "TERMINAL INDIVIDUAL":
    col1, col2 = st.columns([1, 3])
    with col1:
        ticker = st.text_input("TICKER", "NVDA").upper()
        dias = st.slider("DÍAS", 7, 90, 30)
        sims = st.slider("SIMULACIONES", 50, 500, 100)
        go_btn = st.button("ANALIZAR")

    if go_btn:
        df, ret = get_data(ticker)
        last_p = df.iloc[-1]
        results = monte_carlo(last_p, ret.mean(), ret.std(), dias, sims)
        
        # Métricas Avanzadas
        m1, m2, m3 = st.columns(3)
        m1.metric("SHARPE RATIO", round((ret.mean()*252)/(ret.std()*np.sqrt(252)), 2))
        m2.metric("SKEWNESS", round(skew(ret), 2))
        m3.metric("KURTOSIS", round(kurtosis(ret), 2))
        
        # Gráfico Pro
        fig = go.Figure()
        for i in range(min(sims, 100)):
            fig.add_trace(go.Scatter(y=results[:, i], mode='lines', line=dict(width=0.5, color='rgba(0, 255, 255, 0.1)'), showlegend=False))
        
        fig.update_layout(template="plotly_dark", paper_bgcolor="black", plot_bgcolor="black", title=f"PROYECCIÓN ESTOCÁSTICA {ticker}")
        st.plotly_chart(fig, use_container_width=True)

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
