import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import requests

# --- CONFIGURACIÓN ESTÉTICA GÓTICA & EXCHANGE ---
st.set_page_config(page_title="OBSIDIANA QUANT TERMINAL", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #060608; }
    
    /* Tarjetas del Monitor */
    .quant-card {
        background: rgba(10, 10, 12, 0.9);
        border: 1px solid #1e1e26;
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 15px;
    }
    
    /* Métricas estilo Broker */
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
        text-transform: uppercase; letter-spacing: 1px;
    }
    div.stButton > button:hover { background-color: #00ffff; color: #000; }
    
    h1, h2, h3 { font-family: 'Courier New', monospace; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
st.title("♰ OBSIDIANA QUANTITATIVE TERMINAL v3.0")
st.caption("PHYSICS-BASED FINANCIAL INTELLIGENCE | ENTORNO PROFESIONAL")

# --- LÓGICA DE SUSCRIPCIÓN (TUYA) ---
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

# --- FUNCIONES DE CÁLCULO (TUYAS MEJORADAS) ---
def get_data(ticker):
    data = yf.download(ticker, period="1y", progress=False)
    if data.empty: raise ValueError("No hay datos")
    close_data = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
    df = close_data.dropna().astype(float)
    returns = np.log(df / df.shift(1)).dropna()
    return df, returns

def monte_carlo(last_price, mu, sigma, days, n_sims):
    res = np.zeros((days, n_sims))
    res[0] = last_price
    for t in range(1, days):
        res[t] = res[t-1] * np.exp(np.random.normal(mu, sigma, n_sims))
    return res

# --- MÓDULO 1: ESCÁNER MULTITEMPORAL (OPTIMIZADO) ---
if modo == "ESCÁNER":
    st.header("♰ LIVE QUANTUM MONITOR")
    
    with st.sidebar:
        st.subheader("♰ BUSCADOR DE ACTIVOS")
        query_scan = st.text_input("BUSCAR PARA VINCULAR:", placeholder="Ej: Nvidia, Oro, Yuan...", key="search_scan").strip()

        if query_scan:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query_scan}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            try:
                response = requests.get(url, headers=headers).json()
                quotes = response.get('quotes', [])
                if quotes:
                    for res in quotes[:5]:
                        label = f"➕ {res.get('shortname', 'N/A')} ({res['symbol']})"
                        if st.button(label, key=f"scan_btn_{res['symbol']}"):
                            if "mis_activos" not in st.session_state:
                                st.session_state.mis_activos = ["BTC-USD"]
                            if res['symbol'] not in st.session_state.mis_activos:
                                st.session_state.mis_activos.append(res['symbol'])
                                st.rerun()
                else:
                    st.warning("No se encontraron activos.")
            except:
                st.error("Error de red.")

        if st.sidebar.button("LIMPIAR MONITOR"):
            st.session_state.mis_activos = ["BTC-USD"]
            st.rerun()

    lista_activos = st.session_state.get("mis_activos", ["BTC-USD"])
    refresh_rate = st.sidebar.slider("REFRESCO (SEG)", 5, 60, 20)

    @st.fragment(run_every=refresh_rate)
    def render_live_scanner():
        if not lista_activos:
            st.info("Monitor vacío. Busca activos en la barra lateral.")
            return

        cols = st.columns(4)
        for i, ticker in enumerate(lista_activos):
            try:
                # Descarga rápida de 1 minuto
                data = yf.download(ticker, period="2d", interval="1m", progress=False)
                
                if not data.empty:
                    # Aplanar MultiIndex si existe
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                    
                    # Extracción segura de precio escalar
                    last_price = float(data['Close'].dropna().iloc[-1])
                    
                    # Estadísticas rápidas
                    _, ret = get_data(ticker)
                    mu, sigma = float(ret.mean()), float(ret.std())
                    
                    # Probabilidad a 7 días (Monte Carlo simplificado)
                    sims = monte_carlo(last_price, mu, sigma, 7, 100)
                    prob_up = (np.sum(sims[-1] > last_price) / 100) * 100
                    
                    color = "#00ffff" if prob_up > 50 else "#ff4b4b"
                    dec = 4 if last_price < 5 else 2

                    with cols[i % 4]:
                        st.markdown(f"""
                            <div style="border: 1px solid {color}55; padding: 15px; background: #0a0a0c; border-radius: 4px; margin-bottom: 10px;">
                                <p style="margin:0; font-size:10px; color:#666;">{ticker}</p>
                                <h3 style="margin:5px 0; color:white; font-size:20px; font-family:monospace;">${last_price:,.{dec}f}</h3>
                                <div style="display:flex; align-items:center; gap:5px;">
                                    <div style="width:6px; height:6px; border-radius:50%; background:{color};"></div>
                                    <p style="margin:0; font-size:11px; color:{color}; font-weight:bold;">UP: {prob_up:.0f}%</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            except:
                continue

    render_live_scanner()

# --- MÓDULO 2: TERMINAL INDIVIDUAL (OPTIMIZADO) ---
elif modo == "TERMINAL INDIVIDUAL":
    st.header("♰ TRADING TERMINAL")
    
    with st.sidebar:
        st.subheader("♰ BUSCADOR INTELIGENTE")
        # Limpiamos la entrada del usuario para evitar espacios muertos
        query_raw = st.text_input("BUSCAR POR NOMBRE:", placeholder="Ej: Nvidia, Apple, BTC...", key="term_search").strip()
        
        ticker_final = "PLTR" # Default
        
        if query_raw:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query_raw}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            try:
                res = requests.get(url, headers=headers).json()
                quotes = res.get('quotes', [])
                
                if quotes:
                    # Mapeamos sugerencias reales de Yahoo
                    search_options = {
                        f"{q.get('shortname', 'N/A')} ({q['symbol']})": q['symbol'] 
                        for q in quotes if 'symbol' in q
                    }
                    seleccion = st.selectbox("RESULTADOS ENCONTRADOS:", options=list(search_options.keys()))
                    ticker_final = search_options[seleccion]
                else:
                    # Si no hay resultados (error de dedo), usamos el texto tal cual en mayúsculas
                    ticker_final = query_raw.upper()
                    st.caption(f"Sin sugerencias. Probando con ticker: {ticker_final}")
            except:
                ticker_final = query_raw.upper()
        
        st.success(f"ACTIVO: {ticker_final}")
        st.markdown("---")
        dias_sim = st.slider("PROYECCIÓN (DÍAS)", 5, 365, 30)

    # --- LÓGICA DE RENDERIZADO ROBUSTA ---
    try:
        # Descarga con manejo de errores para tickers inválidos
        data_hist = yf.download(ticker_final, period="1mo", interval="60m", progress=False)
        
        if not data_hist.empty:
            # Corregimos el problema de los niveles de columnas (MultiIndex)
            if isinstance(data_hist.columns, pd.MultiIndex):
                data_hist.columns = data_hist.columns.get_level_values(0)
            
            # Aseguramos que Close sea una Serie limpia
            close_series = data_hist['Close'].dropna()
            if close_series.empty:
                st.error("Datos de precio no disponibles para este activo.")
            else:
                last_price = float(close_series.iloc[-1])
                df_full, ret = get_data(ticker_final)
                mu, sigma = float(ret.mean()), float(ret.std())

                # Métricas Principales
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("TICKER", ticker_final)
                c2.metric("PRECIO", f"${last_price:,.2f}")
                c3.metric("VOLATILIDAD (ANUAL)", f"{sigma*np.sqrt(252):.1%}")
                c4.metric("MAX 30D", f"${float(data_hist['High'].max()):,.2f}")

                st.markdown("---")
                col_left, col_right = st.columns([3, 1])
                
                with col_left:
                    # Gráfico de Velas
                    fig = go.Figure(data=[go.Candlestick(
                        x=data_hist.index,
                        open=data_hist['Open'], high=data_hist['High'],
                        low=data_hist['Low'], close=data_hist['Close'],
                        increasing_line_color='#00ffff', decreasing_line_color='#ff4b4b'
                    )])
                    fig.update_layout(
                        template="plotly_dark", height=500, margin=dict(l=0,r=0,t=0,b=0),
                        xaxis_rangeslider_visible=False,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_right:
                    st.subheader("♰ ORDER BOOK")
                    # Simulación dinámica basada en el precio real
                    bids_p = [last_price * (1 - i/1000) for i in range(5)]
                    asks_p = [last_price * (1 + i/1000) for i in range(5)]
                    
                    st.caption("SELL SIDE")
                    st.dataframe(pd.DataFrame({'Price': asks_p, 'Size': np.random.uniform(0.1, 5, 5)}).sort_values('Price', ascending=False), hide_index=True)
                    
                    st.caption("BUY SIDE")
                    st.dataframe(pd.DataFrame({'Price': bids_p, 'Size': np.random.uniform(0.1, 5, 5)}), hide_index=True)
                    
                    # Probabilidad con Monte Carlo
                    sims = monte_carlo(last_price, mu, sigma, dias_sim, 100)
                    prob_up = (np.sum(sims[-1] > last_price) / 100)
                    st.info(f"PROB. ALCISTA ({dias_sim}d): {prob_up:.1%}")
        else:
            st.warning(f"No se encontraron datos para '{ticker_final}'. Revisa el ticker o busca por nombre.")

    except Exception as e:
        st.error(f"Error en el sistema: {e}")
# --- MÓDULO 3: COMPARADOR (OPTIMIZADO) ---
elif modo == "COMPARADOR":
    st.header("♰ MULTI-ASSET QUANT COMPARISON")
    st.subheader("ANÁLISIS DE CORRELACIÓN Y RIESGO")
    
    # Input más flexible
    input_lista = st.text_input("TICKERS O NOMBRES (SEPARADOS POR COMA):", "BTC-USD, NVDA, TSLA, GC=F")
    
    if st.button("GENERAR MATRIZ CUÁNTICA"):
        # Limpiamos la lista
        tickers = [t.strip().upper() for t in input_lista.split(",")]
        resumen = []
        
        # Barra de progreso para dar feedback al usuario
        prog = st.progress(0)
        
        for idx, t in enumerate(tickers):
            try:
                # Obtener datos usando tu función base
                df, ret = get_data(t)
                
                # Cálculos escalares seguros
                mu = float(ret.mean())
                sigma = float(ret.std())
                vol_anual = sigma * np.sqrt(252)
                sharpe = (mu * 252) / vol_anual if vol_anual != 0 else 0
                max_dd = float(ret.min()) # Drawdown diario máximo
                
                resumen.append({
                    "ACTIVO": t,
                    "PRECIO": f"${float(df.iloc[-1]):,.2f}",
                    "VOLAT. ANUAL": f"{vol_anual:.1%}",
                    "SHARPE RATIO": round(sharpe, 2),
                    "MAX DAILY DD": f"{max_dd:.1%}",
                    "SENTIMIENTO": "BULLISH" if mu > 0 else "BEARISH"
                })
            except Exception as e:
                st.warning(f"Omitiendo {t}: No se encontraron datos o formato inválido.")
            
            prog.progress((idx + 1) / len(tickers))
        
        if resumen:
            df_resumen = pd.DataFrame(resumen)
            
            # Mostrar tabla con estilo gótico
            st.table(df_resumen)
            
            # Gráfico comparativo de Volatilidad vs Sharpe
            st.subheader("♰ MAPA DE RIESGO / RETORNO")
            fig_comp = go.Figure()
            for item in resumen:
                # Limpiamos los strings para el gráfico
                vol_val = float(item["VOLAT. ANUAL"].replace('%',''))
                fig_comp.add_trace(go.Scatter(
                    x=[vol_val], 
                    y=[item["SHARPE RATIO"]],
                    mode='markers+text',
                    name=item["ACTIVO"],
                    text=[item["ACTIVO"]],
                    textposition="top center",
                    marker=dict(size=15, color='#00ffff', line=dict(width=2, color='white'))
                ))
            
            fig_comp.update_layout(
                template="plotly_dark",
                xaxis_title="VOLATILIDAD ANUAL (%)",
                yaxis_title="SHARPE RATIO (EFICIENCIA)",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.error("No se pudo procesar ningún activo de la lista.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("TERMINAL OBSIDIANA © 2026 | Powered by Quant Physics Engine")
