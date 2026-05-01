import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import requests

# --- CONFIGURACIÓN ESTÉTICA (TUYA + BLINDAJE) ---
st.set_page_config(page_title="OBSIDIANA QUANT TERMINAL", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #060608; }
    
    /* Tarjetas del Monitor */
    .quant-card {
        background: rgba(10, 10, 12, 0.9);
        border: 1px solid #1e1e26;
        border-radius: 4px;
        padding: 15px;
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
st.title("♰ OBSIDIANA QUANTITATIVE TERMINAL v3.5")
st.caption("PHYSICS-BASED FINANCIAL INTELLIGENCE | ENTORNO PROFESIONAL BLINDADO")

# --- LÓGICA DE SUSCRIPCIÓN (MANTENIDA) ---
if "pro" not in st.session_state:
    st.session_state.pro = False
if "mis_activos" not in st.session_state:
    st.session_state.mis_activos = ["BTC-USD"]

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

# --- MOTOR DE BÚSQUEDA UNIVERSAL (EL QUE EVITA LOS BUGS) ---
def universal_search(key_suffix, placeholder="Ej: Nvidia, Oro, BTC..."):
    """Función de búsqueda estandarizada y blindada"""
    query = st.text_input("BUSCAR PRODUCTO:", placeholder=placeholder, key=f"search_{key_suffix}").strip()
    if query:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers).json()
            return res.get('quotes', [])
        except:
            st.error("Error de conexión con el servidor de búsqueda.")
    return []

# --- FUNCIONES DE CÁLCULO (MANTENIDAS Y MEJORADAS CON BLINDAJE DE COLUMNAS) ---
def get_data(ticker):
    data = yf.download(ticker, period="1y", progress=False)
    if data.empty: raise ValueError(f"No hay datos para {ticker}")
    # Blindaje contra MultiIndex (el error de "NVDIA")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    close_data = data['Close'].dropna().astype(float)
    returns = np.log(close_data / close_data.shift(1)).dropna()
    return close_data, returns

def monte_carlo(last_price, mu, sigma, days, n_sims):
    # Asegurar que mu y sigma sean escalares
    if not isinstance(mu, (int, float)): mu = float(mu)
    if not isinstance(sigma, (int, float)): sigma = float(sigma)
    if not isinstance(last_price, (int, float)): last_price = float(last_price)
    
    res = np.zeros((days, n_sims))
    res[0] = last_price
    for t in range(1, days):
        res[t] = res[t-1] * np.exp(np.random.normal(mu, sigma, n_sims))
    return res

# --- MÓDULO 1: ESCÁNER (RE-INTEGRADO COMPLETAMENTE) ---
if modo == "ESCÁNER":
    st.header("♰ LIVE QUANTUM MONITOR")
    
    with st.sidebar:
        st.subheader("♰ VINCULADOR GLOBAL")
        resultados = universal_search("scan", "Escribe para vincular...")
        
        for res in resultados[:5]:
            label = f"➕ {res.get('shortname', 'N/A')} ({res['symbol']})"
            # Usamos keys únicas para cada botón
            if st.button(label, key=f"add_{res['symbol']}"):
                if res['symbol'] not in st.session_state.mis_activos:
                    st.session_state.mis_activos.append(res['symbol'])
                    st.rerun()
        
        st.markdown("---")
        if st.button("LIMPIAR MONITOR"):
            st.session_state.mis_activos = ["BTC-USD"]
            st.rerun()

    lista_activos = st.session_state.mis_activos
    refresh_rate = st.sidebar.slider("REFRESCO (SEG)", 5, 60, 20)
    
    @st.fragment(run_every=refresh_rate)
    def render_live_scanner():
        if not lista_activos:
            st.info("Monitor vacío. Busca y añade activos en la barra lateral.")
            return

        cols = st.columns(4)
        for i, ticker in enumerate(lista_activos):
            try:
                # Descarga rápida para monitor (intervalo 1m si es posible)
                df_min = yf.download(ticker, period="2d", interval="1m", progress=False)
                if df_min.empty: # Fallback a 15m si no hay 1m (fuera de hora)
                    df_min = yf.download(ticker, period="2d", interval="15m", progress=False)
                
                # Blindaje MultiIndex
                if isinstance(df_min.columns, pd.MultiIndex):
                    df_min.columns = df_min.columns.get_level_values(0)
                
                # Asegurar precio escalar
                last_p = float(df_min['Close'].dropna().iloc[-1])
                
                # RE-INTEGRADO: Cálculo de Probabilidad (Monte Carlo)
                _, ret = get_data(ticker)
                # Forzamos conversión a escalar
                mu = float(ret.mean())
                sigma = float(ret.std())
                
                sims = monte_carlo(last_p, mu, sigma, 7, 200) # 200 sims para rapidez
                prob_up = (np.sum(sims[-1] > last_p) / 200) * 100
                
                color = "#00ffff" if prob_up > 50 else "#ff4b4b"
                dec = 4 if last_p < 5 else 2
                
                with cols[i % 4]:
                    st.markdown(f"""
                        <div class="quant-card" style="border: 1px solid {color}55;">
                            <p style="margin:0; font-size:10px; color:#666; text-transform:uppercase;">{ticker}</p>
                            <h3 style="margin:5px 0; font-size:20px; font-family:monospace;">${last_p:,.{dec}f}</h3>
                            <div style="display:flex; align-items:center; gap:5px;">
                                <div style="width:6px; height:6px; border-radius:50%; background:{color}; box-shadow: 0 0 5px {color};"></div>
                                <p style="margin:0; font-size:11px; color:{color}; font-weight:bold;">PROB. UP 7D: {prob_up:.0f}%</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                with cols[i % 4]:
                    st.error(f"Err {ticker}")
                    st.caption(f"{e}")
    
    render_live_scanner()

# --- MÓDULO 2: TERMINAL INDIVIDUAL (RE-INTEGRADO COMPLETAMENTE CON VELAS Y BOOK) ---
elif modo == "TERMINAL INDIVIDUAL":
    st.header("♰ TRADING TERMINAL")
    with st.sidebar:
        st.subheader("♰ SELECCIÓN ACTIVA")
        resultados = universal_search("terminal", "Escribe para cargar...")
        
        # Guardar la selección en el estado de sesión
        if 'ticker_actual' not in st.session_state:
            st.session_state.ticker_actual = "PLTR"
            
        if resultados:
            opciones = {f"{r.get('shortname', 'N/A')} ({r['symbol']})": r['symbol'] for r in resultados}
            seleccion = st.selectbox("RESULTADOS:", options=list(opciones.keys()))
            st.session_state.ticker_actual = opciones[seleccion]
            st.success(f"CARGADO: {st.session_state.ticker_actual}")

        dias_sim = st.slider("PROYECCIÓN (DÍAS)", 5, 365, 30)

    ticker_final = st.session_state.ticker_actual
    
    try:
        # Descarga de datos históricos y de intervalo (para velas)
        # 1 hora para el gráfico de velas
        data_hist = yf.download(ticker_final, period="1mo", interval="60m", progress=False)
        # Blindaje MultiIndex
        if isinstance(data_hist.columns, pd.MultiIndex):
            data_hist.columns = data_hist.columns.get_level_values(0)
            
        df_close, ret = get_data(ticker_final)
        
        # Asegurar precio actual escalar
        last_price = float(df_close.iloc[-1])
        mu = float(ret.mean())
        sigma = float(ret.std())
        
        # RE-INTEGRADO: Dashboard de Métricas Completas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PRECIO ACTUAL", f"${last_price:,.2f}")
        c2.metric("VOLATILIDAD (ANUALIZADA)", f"{sigma*np.sqrt(252):.1%}")
        # Asegurar Max/Min escalares
        high_30 = data_hist['High'].dropna().max()
        low_30 = data_hist['Low'].dropna().min()
        c3.metric("MAX 30D", f"${float(high_30):,.2f}")
        c4.metric("MIN 30D", f"${float(low_30):,.2f}")

        st.markdown("---")
        col_left, col_right = st.columns([3, 1])
        
        with col_left:
            # RE-INTEGRADO: Gráfico de Velas Japonesas
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

            # RE-INTEGRADO: Análisis Sentimiento basado en Monte Carlo
            st.subheader(f"♰ PROYECCIÓN DE RIESGO ({dias_sim} DÍAS)")
            sims = monte_carlo(last_price, mu, sigma, dias_sim, 200)
            prob_up_sent = (np.sum(sims[-1] > last_price) / 200)
            st.info(f"SENTIMIENTO CUÁNTICO: {'BULLISH' if prob_up_sent > 0.5 else 'BEARISH'} ({prob_up_sent:.1%})")

        with col_right:
            # RE-INTEGRADO: Order Book Simulado (Look Profesional)
            st.subheader("♰ ORDER BOOK")
            # Simulación dinámica basada en el precio real
            bids_p = [last_price * (1 - i/1000) for i in range(5)]
            asks_p = [last_price * (1 + i/1000) for i in range(5)]
            
            st.caption("SELL SIDE (ASKS)")
            df_asks = pd.DataFrame({'Price': asks_p, 'Size': np.random.uniform(0.1, 5, 5)}).sort_values('Price', ascending=False)
            st.dataframe(df_asks, hide_index=True)
            
            st.caption("BUY SIDE (BIDS)")
            st.dataframe(pd.DataFrame({'Price': bids_p, 'Size': np.random.uniform(0.1, 5, 5)}), hide_index=True)
            
    except Exception as e:
        st.error(f"No se pudieron cargar los datos analíticos para '{ticker_final}'.")
        st.caption(f"Detalle técnico: {e}")

# --- MÓDULO 3: COMPARADOR (RE-INTEGRADO COMPLETAMENTE CON SHARPE Y RIESGO) ---
elif modo == "COMPARADOR":
    st.header("♰ MULTI-ASSET QUANT COMPARISON")
    st.subheader("ANÁLISIS DE RIESGO Y EFICIENCIA (Sharpe/MaxDD)")
    
    # Input flexible mantenido
    input_lista = st.text_input("TICKERS O NOMBRES (SEPARADOS POR COMA):", "BTC-USD, NVDA, TSLA, GC=F")
    
    if st.button("GENERAR MATRIZ CUÁNTICA"):
        # Limpiamos la lista
        tickers = [t.strip().upper() for t in input_lista.split(",")]
        resumen = []
        prog = st.progress(0)
        
        for idx, t in enumerate(tickers):
            try:
                # Obtener datos usando tu función blindada
                df, ret = get_data(t)
                
                # RE-INTEGRADO: Cálculos Cuánticos Completos
                mu = float(ret.mean())
                sigma = float(ret.std())
                vol_anual = sigma * np.sqrt(252)
                
                # Sharpe Ratio (asumiendo Risk Free = 0% para simplicidad)
                sharpe = (mu * 252) / vol_anual if vol_anual != 0 else 0
                
                # Drawdown diario máximo histórico (del último año)
                # Es el retorno más bajo en un solo día
                min_return = float(ret.min())
                
                resumen.append({
                    "ACTIVO": t,
                    "PRECIO ACT.": f"${float(df.iloc[-1]):,.2f}",
                    "VOLAT. ANUAL": f"{vol_anual:.1%}",
                    "SHARPE RATIO": round(sharpe, 2),
                    "PEOR DÍA (1y)": f"{min_return:.1%}", # Como MaxDD simplificado
                    "SENTIMIENTO": "BULLISH" if mu > 0 else "BEARISH"
                })
            except:
                st.warning(f"Omitiendo {t}: Formato inválido.")
            
            prog.progress((idx + 1) / len(tickers))
        
        if resumen:
            df_resumen = pd.DataFrame(resumen)
            
            # RE-INTEGRADO: Tabla con Estilo Gótico
            st.table(df_resumen)
            
            # RE-INTEGRADO: Gráfico de Mapa de Riesgo vs Retorno (Sharpe)
            st.subheader("♰ MAPA DE EFICIENCIA (Sharpe vs Volatilidad)")
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
            st.error("No se pudo procesar la matriz.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("TERMINAL OBSIDIANA © 2026 | Powered by Quant Physics Engine")
