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

# --- MÓDULO 1: ESCÁNER ---
if modo == "ESCÁNER":
    st.header("♰ LIVE QUANTUM MONITOR")
    
    with st.sidebar:
        st.subheader("♰ BUSCADOR YAHOO")
        query = st.text_input("BUSCAR PRODUCTO:", placeholder="Ej: Yuan, Palantir...", key="search_input")
        if query:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
            data_s = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
            for res in data_s.get('quotes', [])[:3]:
                if st.button(f"➕ VINCULAR {res['symbol']}", key=f"add_{res['symbol']}"):
                    if "mis_activos" not in st.session_state: st.session_state.mis_activos = ["BTC-USD"]
                    if res['symbol'] not in st.session_state.mis_activos:
                        st.session_state.mis_activos.append(res['symbol'])
                        st.rerun()

    lista_activos = st.session_state.get("mis_activos", ["BTC-USD"])
    refresh_rate = st.sidebar.slider("REFRESCO (SEG)", 5, 60, 20)
    
    @st.fragment(run_every=refresh_rate)
    def render_live_scanner():
        cols = st.columns(4)
        for i, ticker in enumerate(lista_activos):
            try:
                # Datos rápidos para el monitor
                df_min = yf.download(ticker, period="2d", interval="15m", progress=False)
                last_p = float(df_min['Close'].iloc[-1])
                # Probabilidad (usando tu función get_data)
                _, ret = get_data(ticker)
                mu, sigma = float(ret.mean()), float(ret.std())
                sims = monte_carlo(last_p, mu, sigma, 7, 100)
                prob_up = (np.sum(sims[-1] > last_p) / 100) * 100
                color = "#00ffff" if prob_up > 50 else "#ff4b4b"
                
                with cols[i % 4]:
                    st.markdown(f"""
                        <div class="quant-card">
                            <p style="margin:0; font-size:10px; color:#666;">{ticker}</p>
                            <h3 style="margin:5px 0; font-size:22px;">${last_p:,.2f}</h3>
                            <p style="margin:0; font-size:12px; color:{color}; font-weight:bold;">PROB 7D: {prob_up:.0f}%</p>
                        </div>
                    """, unsafe_allow_html=True)
            except: continue
    render_live_scanner()

# --- MÓDULO 2: TERMINAL INDIVIDUAL (RE-DISEÑADO) ---
elif modo == "TERMINAL INDIVIDUAL":
    st.header("♰ TRADING TERMINAL")
    with st.sidebar:
        t_input = st.text_input("TICKER DIRECTO", "PLTR").upper()
        dias_sim = st.slider("PROYECCIÓN (DÍAS)", 5, 365, 30)

    try:
        # Descarga de datos
        data_hist = yf.download(t_input, period="1mo", interval="60m", progress=False)
        df_full, ret = get_data(t_input)
        last_price = float(data_hist['Close'].iloc[-1])
        
        # Dashboard de cabecera
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PRECIO ACTUAL", f"${last_price:,.2f}")
        c2.metric("VOLATILIDAD", f"{ret.std()*np.sqrt(252):.1%}")
        c3.metric("MAX 30D", f"${data_hist['High'].max():,.2f}")
        c4.metric("MIN 30D", f"${data_hist['Low'].min():,.2f}")

        col_left, col_right = st.columns([3, 1])
        
        with col_left:
            # Gráfico de Velas Japonesas
            fig = go.Figure(data=[go.Candlestick(
                x=data_hist.index, open=data_hist['Open'], high=data_hist['High'],
                low=data_hist['Low'], close=data_hist['Close'],
                increasing_line_color='#00ffff', decreasing_line_color='#ff4b4b'
            )])
            fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("♰ ORDER BOOK")
            # Simulación estética de Libro de Órdenes
            bids = pd.DataFrame({'Price': [last_price * (1-i/1000) for i in range(5)], 'Size': np.random.uniform(1, 10, 5)})
            st.caption("SELL ORDERS")
            st.dataframe(bids.assign(Price=bids['Price']*1.002), hide_index=True)
            st.caption("BUY ORDERS")
            st.dataframe(bids, hide_index=True)
            
    except Exception as e:
        st.error(f"Error en terminal: {e}")

# --- MÓDULO 3: COMPARADOR (TUYO) ---
elif modo == "COMPARADOR":
    st.header("♰ MULTI-ASSET COMPARISON")
    lista = st.text_input("TICKERS SEPARADOS POR COMA", "BTC-USD, ETH-USD, TSLA")
    if st.button("COMPARAR MATRIZ"):
        tickers = [t.strip().upper() for t in lista.split(",")]
        resumen = []
        for t in tickers:
            try:
                _, ret = get_data(t)
                resumen.append({
                    "ACTIVO": t,
                    "VOLATILIDAD": f"{ret.std()*np.sqrt(252)*100:.1f}%",
                    "SHARPE": round((ret.mean()*252)/(ret.std()*np.sqrt(252)), 2),
                    "MAX DRAWDOWN": f"{(ret.min()*100):.1f}%"
                })
            except: continue
        st.table(pd.DataFrame(resumen))

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("TERMINAL OBSIDIANA © 2026 | Powered by Quant Physics Engine")
