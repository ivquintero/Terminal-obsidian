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
        st.subheader("♰ TERMINAL DE ACCESO GLOBAL")
        # Aquí escribes CUALQUIER Ticker de Yahoo Finance
        raw_input = st.text_input(
            "BUSCADOR DE RED (Ticker):", 
            value="BTC-USD, PLTR, CNYUSD=X",
            help="Escribe los tickers oficiales de Yahoo Finance separados por comas."
        )
        
        # Procesamos la entrada para que sea una lista limpia
        lista_activos = [t.strip().upper() for t in raw_input.split(",") if t.strip()]
        
        st.info("💡 Consejo: Para divisas usa '=X' (ej: CNYUSD=X). Para acciones el código (ej: PLTR).")

    refresh_rate = st.sidebar.slider("REFRESCO (SEG)", 5, 60, 20)
    
    @st.fragment(run_every=refresh_rate)
    def render_live_scanner():
        if not lista_activos:
            st.warning("Introduce un ticker válido para iniciar el escaneo.")
            return

        cols = st.columns(4)
        with st.spinner("Conectando con Yahoo Finance API..."):
            for i, ticker in enumerate(lista_activos):
                try:
                    # Intento de descarga directa de la base de datos de Yahoo
                    data = yf.download(ticker, period="2d", interval="1m", progress=False)
                    
                    if data.empty:
                        # Si no encuentra nada, nos avisa en la tarjeta
                        with cols[i % 4]:
                            st.error(f"Ticker '{ticker}' no hallado.")
                        continue

                    # --- PROCESAMIENTO DE DATOS ---
                    # Manejo de precios para activos con muchos o pocos decimales
                    close_price = data['Close'].iloc[-1]
                    # Si el precio es un objeto (Series), extraemos el valor numérico
                    last_price = float(close_price.iloc[0]) if hasattr(close_price, 'iloc') else float(close_price)
                    
                    # Motor de Probabilidad (Monte Carlo)
                    _, ret = get_data(ticker) 
                    mu, sigma = float(ret.mean()), float(ret.std())
                    
                    # Calculamos solo 7D y 30D para velocidad
                    res = {}
                    for etiqueta, dias in {"7D": 7, "30D": 30}.items():
                        sims = monte_carlo(last_price, mu, sigma, dias, 500)
                        res[etiqueta] = float((np.sum(sims[-1] > last_price) / 500) * 100)

                    # --- TARJETA VISUAL ---
                    with cols[i % 4]:
                        # Color dinámico basado en probabilidad
                        accent = "cyan" if res["7D"] > 50 else "red"
                        # Ajuste de decimales para Forex (Yuan) vs Acciones
                        dec = 4 if last_price < 5 else 2
                        
                        st.markdown(f"""
                            <div style="border-left: 3px solid {accent}; padding: 12px; background: #0a0a0a; border-radius: 4px; margin-bottom: 10px;">
                                <p style="margin:0; font-size:10px; color:#444; letter-spacing:1px;">{ticker}</p>
                                <h3 style="margin:0; color:white; font-size:18px;">${last_price:,.{dec}f}</h3>
                                <div style="margin-top:8px; font-family:monospace; font-size:10px;">
                                    <span style="color:#555;">PROB UP 7D:</span> <span style="color:{accent}">{res['7D']:.0f}%</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
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
