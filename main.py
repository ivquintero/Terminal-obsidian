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
        
        # 1. Entrada de texto para buscar
        query = st.text_input("BUSCAR PRODUCTO:", placeholder="Ej: Yuan, Palantir, Gold...", key="search_input")

        sugerencias_yahoo = {}
        
        if query:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            try:
                response = requests.get(url, headers=headers)
                data = response.json()
                for res in data.get('quotes', []):
                    if 'symbol' in res and 'shortname' in res:
                        nombre_pantalla = f"{res['shortname']} ({res['symbol']}) - {res.get('quoteType', '')}"
                        sugerencias_yahoo[nombre_pantalla] = res['symbol']
            except:
                st.error("Error conectando con Yahoo.")

        # 2. Selector de resultados
        if sugerencias_yahoo:
            seleccion = st.selectbox("RESULTADOS ENCONTRADOS:", options=[""] + list(sugerencias_yahoo.keys()), key="search_select")
            
            if seleccion != "":
                ticker_final = sugerencias_yahoo[seleccion]
                
                if "mis_activos" not in st.session_state:
                    st.session_state.mis_activos = ["BTC-USD"]
                
                if st.button(f"➕ VINCULAR {ticker_final}", key=f"btn_add_{ticker_final}"):
                    if ticker_final not in st.session_state.mis_activos:
                        st.session_state.mis_activos.append(ticker_final)
                        st.rerun()
        elif query:
            st.warning("No se encontraron coincidencias exactas.")

        if st.button("🗑️ RESET MONITOR", key="btn_reset_monitor"):
            st.session_state.mis_activos = []
            st.rerun()

    # Recuperamos activos guardados en la sesión
    lista_activos = st.session_state.get("mis_activos", ["BTC-USD"])

    # Slider de refresco con key única
    refresh_rate = st.sidebar.slider("REFRESCO (SEG)", 5, 60, 20, key="refresh_slider_scanner")
    
    # --- RENDERIZADO DEL MONITOR ---
    @st.fragment(run_every=refresh_rate)
    def render_live_scanner():
        if not lista_activos:
            st.info("Buscador activo. Escribe un nombre a la izquierda para empezar.")
            return

        cols = st.columns(4)
        for i, ticker in enumerate(lista_activos):
            try:
                # Intento de descarga robusta
                data = yf.download(ticker, period="2d", interval="1m", progress=False)
                if data.empty:
                    data = yf.download(ticker, period="5d", interval="60m", progress=False)

                if not data.empty:
                    # Limpieza de precio
                    last_price_raw = data['Close'].iloc[-1]
                    last_price = float(last_price_raw.iloc[0]) if hasattr(last_price_raw, 'iloc') else float(last_price_raw)
                    
                    # Cálculo de Probabilidades
                    _, ret = get_data(ticker) 
                    mu, sigma = float(ret.mean()), float(ret.std())
                    sims = monte_carlo(last_price, mu, sigma, 7, 500)
                    prob_up = float((np.sum(sims[-1] > last_price) / 500) * 100)

                    # Tarjeta Visual
                    with cols[i % 4]:
                        color = "cyan" if prob_up > 50 else "red"
                        dec = 4 if last_price < 5 else 2
                        
                        st.markdown(f"""
                            <div style="border: 1px solid {color}; padding: 15px; background: #000; border-radius: 10px; margin-bottom: 15px; min-height: 110px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);">
                                <p style="margin:0; font-size:10px; color:#666; font-weight:bold; text-transform:uppercase;">{ticker}</p>
                                <h3 style="margin:5px 0; color:white; font-size:20px; font-family:monospace;">${last_price:,.{dec}f}</h3>
                                <div style="display:flex; align-items:center; gap:5px;">
                                    <div style="width:8px; height:8px; border-radius:50%; background:{color};"></div>
                                    <p style="margin:0; font-size:11px; color:{color}; font-weight:bold;">PROB 7D: {prob_up:.0f}%</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    with cols[i % 4]:
                        st.error(f"Sin datos: {ticker}")
            except:
                continue

    render_live_scanner()
# --- MÓDULO 2: TERMINAL INDIVIDUAL ---
if modo == "TERMINAL INDIVIDUAL":
    st.header("♰ QUANTUM INDIVIDUAL TERMINAL")
    
    with st.sidebar:
        st.subheader("♰ BÚSQUEDA DE ACTIVO")
        # 1. Buscador idéntico al del Escáner para consistencia total
        query_ind = st.text_input("BUSCAR NOMBRE O TICKER:", placeholder="Ej: Palantir, Yuan...", key="search_ind")
        
        sugerencias_ind = {}
        ticker_final_ind = "PLTR" # Ticker por defecto

        if query_ind:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query_ind}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            try:
                resp = requests.get(url, headers=headers)
                data_ind = resp.json()
                for res in data_ind.get('quotes', []):
                    if 'symbol' in res and 'shortname' in res:
                        label = f"{res['shortname']} ({res['symbol']})"
                        sugerencias_ind[label] = res['symbol']
            except:
                st.error("Error de red.")

        if sugerencias_ind:
            seleccion_ind = st.selectbox("SELECCIONA:", options=list(sugerencias_ind.keys()), key="select_ind")
            ticker_final_ind = sugerencias_ind[seleccion_ind]
        
        dias_sim = st.slider("PROYECCIÓN (DÍAS)", 5, 365, 30, key="slider_ind")

    try:
        # 2. Descarga robusta (Intento 1m, luego 60m)
        data = yf.download(ticker_final_ind, period="5d", interval="1m", progress=False)
        if data.empty:
            data = yf.download(ticker_final_ind, period="1mo", interval="60m", progress=False)

        if not data.empty:
            # 3. Extracción de precio ultra-limpia
            last_price_raw = data['Close'].iloc[-1]
            last_price = float(last_price_raw.iloc[0]) if hasattr(last_price_raw, 'iloc') else float(last_price_raw)
            
            # Cálculo de retornos para métricas
            change_pct = data['Close'].pct_change().iloc[-1]
            change_val = float(change_pct.iloc[0]) if hasattr(change_pct, 'iloc') else float(change_pct)

            # --- Layout Superior ---
            c1, c2, c3 = st.columns(3)
            with c1:
                dec_m = 4 if last_price < 5 else 2
                st.metric(f"PRECIO {ticker_final_ind}", f"${last_price:,.{dec_m}f}", f"{change_val:.2%}")
            
            # 4. Procesamiento para Monte Carlo y Gráfica
            # Usamos period="1y" para tener historial suficiente para mu y sigma
            hist, ret = get_data(ticker_final_ind)
            mu, sigma = float(ret.mean()), float(ret.std())
            sims = monte_carlo(last_price, mu, sigma, dias_sim, 100)
            
            with c2:
                prob_up = (np.sum(sims[-1] > last_price) / 100) * 100
                st.metric("PROBABILIDAD ALZA", f"{prob_up:.1f}%")
            
            with c3:
                vol = sigma * np.sqrt(252) * 100
                st.metric("VOLATILIDAD ANUAL", f"{vol:.1f}%")

            # --- Gráfica de Proyección ---
            st.subheader("♰ PROYECCIÓN DE RUTAS CUÁNTICAS")
            fig = go.Figure()
            
            # Dibujar rutas de simulación
            for s in range(min(50, sims.shape[1])):
                fig.add_trace(go.Scatter(y=sims[:, s], mode='lines', 
                                       line=dict(width=1, color='gray'), opacity=0.2, showlegend=False))
            
            # Línea de tendencia media
            fig.add_trace(go.Scatter(y=sims.mean(axis=1), mode='lines', 
                                   line=dict(color='cyan', width=3), name="Tendencia Media"))
            
            fig.update_layout(template="plotly_dark", height=450, 
                             paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                             xaxis_title="Días Proyectados", yaxis_title="Precio Estimado")
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.error(f"El ticker {ticker_final_ind} no devolvió datos. Revisa si es correcto.")
            
    except Exception as e:
        st.warning(f"Esperando configuración de activo... ({e})")
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
