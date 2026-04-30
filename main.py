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

# --- MÓDULO 1: ESCÁNER EN TIEMPO REAL ---
if modo == "ESCÁNER":
    st.header("♰ LIVE QUANTUM MONITOR")
    
    # Slider de refresco
    refresh_rate = st.sidebar.slider("REFRESCO AUTOMÁTICO (SEG)", 5, 60, 10)

    # Definimos la función del fragmento
    @st.fragment(run_every=refresh_rate)
    def render_live_scanner():
        # Lista de activos
        activos = ["BTC-USD", "ETH-USD", "SOL-USD", "NVDA", "AAPL", "TSLA", "META", "GOOGL"]
        cols = st.columns(4)
        
        # Este spinner indica que está trabajando en segundo plano
        with st.spinner("Sincronizando con el mercado..."):
            for i, ticker in enumerate(activos):
                try:
                    # Descarga rápida
                    data = yf.download(ticker, period="1d", interval="1m", progress=False)
                    
                    if not data.empty:
                    # 1. Limpieza de datos
                    close_col = data['Close']
                    last_price = float(close_col.iloc[-1, 0]) if isinstance(close_col, pd.DataFrame) else float(close_col.iloc[-1])
                    
                    mu, sigma = float(ret.mean()), float(ret.std())
                    n_sims = 1000
                    
                    # 2. CÁLCULO MULTITEMPORAL
                    # Definimos los horizontes de tiempo (en días de mercado)
                    horizontes = {
                        "7D": 7,
                        "30D": 30,
                        "6M": 126, # ~126 días de trading
                        "1A": 252  # ~252 días de trading
                    }
                    
                    resultados = {}
                    
                    for etiqueta, dias in horizontes.items():
                        # Ejecutamos Monte Carlo para cada horizonte
                        sim_results = monte_carlo(last_price, mu, sigma, dias, n_sims)
                        final_prices = sim_results[-1]
                        prob = (np.sum(final_prices > last_price) / n_sims) * 100
                        resultados[etiqueta] = prob

                    # 3. RENDERIZADO DE TARJETA EXPANDIDA
                    with cols[i % 4]:
                        # Color basado en la tendencia de corto plazo (7D)
                        main_color = "cyan" if resultados["7D"] > 50 else "red"
                        
                        st.markdown(f"""
                            <div style="border: 1px solid {main_color}; padding: 15px; background: #050505; border-radius: 8px; margin-bottom: 15px;">
                                <h3 style="margin:0; color:white; font-size:16px;">{ticker}</h3>
                                <p style="margin:0; color:{main_color}; font-size:20px; font-weight:bold;">${last_price:,.2f}</p>
                                <hr style="border:0.5px solid #222; margin:10px 0;">
                                <div style="display: flex; justify-content: space-between; font-family:monospace;">
                                    <div style="text-align:center;">
                                        <p style="margin:0; font-size:9px; color:#555;">7D</p>
                                        <p style="margin:0; font-size:11px; color:{'cyan' if resultados['7D']>50 else 'red'}">{resultados['7D']:.1f}%</p>
                                    </div>
                                    <div style="text-align:center;">
                                        <p style="margin:0; font-size:9px; color:#555;">30D</p>
                                        <p style="margin:0; font-size:11px; color:{'cyan' if resultados['30D']>50 else 'red'}">{resultados['30D']:.1f}%</p>
                                    </div>
                                    <div style="text-align:center;">
                                        <p style="margin:0; font-size:9px; color:#555;">6M</p>
                                        <p style="margin:0; font-size:11px; color:{'cyan' if resultados['6M']>50 else 'red'}">{resultados['6M']:.1f}%</p>
                                    </div>
                                    <div style="text-align:center;">
                                        <p style="margin:0; font-size:9px; color:#555;">1A</p>
                                        <p style="margin:0; font-size:11px; color:{'cyan' if resultados['1A']>50 else 'red'}">{resultados['1A']:.1f}%</p>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    with cols[i % 4]:
                        st.error("!") # Error minimalista para no romper el diseño

        # Timestamp de actualización
        st.caption(f"♰ Última actualización: {datetime.now().strftime('%H:%M:%S')}")

    # --- ¡ESTA LÍNEA ES LA MÁS IMPORTANTE! ---
    # Si no llamas a la función aquí, no se verá nada.
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
