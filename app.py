# app.py — DIMEX Dashboard (Ultra UI Edition)
# -------------------------------------------------------
# Requisitos base:
#   pip install streamlit pandas numpy plotly scikit-learn
# Extras opcionales recomendados (gráficos y animaciones):
#   pip install streamlit-lottie pillow
#
# Nota: Sin API ni chatbot. Mantiene la paleta verde DIMEX.

# ==== IMPORTS ==========================================================
import streamlit as st 
import textwrap                  # Framework de UI web rápida en Python
import pandas as pd                      # Manejo de datos tabulares
import numpy as np                       # Utilidades numéricas
import plotly.express as px              # Gráficas de alto nivel
import plotly.graph_objects as go        # Gráficas/objetos de bajo nivel (gauge, etc.)
from pathlib import Path                 # Manejo de rutas cross-OS
import json                              # (reservado) leer/guardar JSON
import io                                # (reservado) buffers en memoria
import base64                            # Para exportar CSV embebido como data URI
from datetime import datetime 
from streamlit_shadcn_ui import card, button
from dotenv import load_dotenv
import os
from openai import OpenAI
import google.generativeai as genai
import base64

def load_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
avatar = load_base64_image("dimi_avatar.png")

import base64

def get_base64_image(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ===== SISTEMA DE LOGIN SIMPLE =====
# ========== LOGIN DE DIMEX (GLASS + AESTHETIC) ==========

import streamlit as st

USERS = {
    "ceo": {"password": "ceo", "rol": "CEO"},
    "director": {"password": "director", "rol": "Director"},
    "ejecutivo": {"password": "ejecutivo", "rol": "Ejecutivo"},
}

PERMISOS = {
    "CEO": ["full"],
    "Director": ["kpis", "mapa", "ranking", "alertas"],
    "Ejecutivo": ["kpis", "alertas", "tabla"],
}

if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.rol = None


def login_screen():
    st.markdown("""
    <style>

    body {
        background: linear-gradient(135deg,#10B98120,#05966920);
        animation: fadeIn 1s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px);}
        to { opacity: 1; transform: translateY(0);}
    }

    .login-card {
        backdrop-filter: blur(18px);
        background: rgba(255,255,255,0.20);
        border: 1px solid rgba(255,255,255,0.35);
        padding: 30px 35px;
        border-radius: 22px;
        width: 380px;
        margin: 80px auto;
        box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        animation: slideUp 0.8s ease;
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(25px);}
        to { opacity: 1; transform: translateY(0);}
    }

    .login-title {
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        color: #065f46;
        margin-bottom: 10px;
    }

    .login-sub {
        text-align: center;
        font-size: 14px;
        color: #0f172a;
        opacity: 0.75;
        margin-bottom: 25px;
    }

    </style>
    """, unsafe_allow_html=True)

    logo_base64 = get_base64_image("dimex_logo.png")

    st.markdown(f"""
    <div class='login-card'>

    <div style="text-align:center; margin-bottom:1px;">
        <img src="data:image/png;base64,{logo_base64}" width="400">
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-title'>Acceso</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-sub'>Panel ejecutivo de riesgo y colocación</div>", unsafe_allow_html=True)

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión", use_container_width=True):
        if user in USERS and USERS[user]["password"] == password:
            st.session_state.auth = True
            st.session_state.rol = USERS[user]["rol"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.markdown("</div>", unsafe_allow_html=True)


# BLOQUEO
if not st.session_state.auth:
    login_screen()
    st.stop()

rol = st.session_state.rol
permisos_usuario = PERMISOS[rol]







# ==== CARGA DE VARIABLES DE ENTORNO / CLIENTE OPENAI ==================

# Limpia cualquier variable global de Windows que interfiera
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

# Cargar .env (forzar a machacar cualquier otra key)
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None  # Para evitar crasheos si no hay key



# PRIMER INTENTO: modelo estable 1.0

# ==== INTENTAR CARGAR EXTRAS (LOTTIE) =================================
try:
    from streamlit_lottie import st_lottie  # Librería para animaciones Lottie
    LOTTI_AVAILABLE = True                   # Flag: hay lottie disponible
except Exception:
    LOTTI_AVAILABLE = False                  # Si falla la importación, lo dejamos apagado

# ==== INTENTAR CARGAR SCIKIT-LEARN ====================================
try:
    from sklearn.tree import DecisionTreeClassifier  # Árbol para drivers de riesgo
    SKLEARN_AVAILABLE = True                         # Flag: sklearn disponible
except ImportError:
    SKLEARN_AVAILABLE = False                        # Si no está instalado, desactivar drivers

# -------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA (título, layout, sidebar)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="DIMEX | Dashboard de Riesgo Sucursales",  # Título de la pestaña
    layout="wide",                                        # Ancho completo
    initial_sidebar_state="collapsed"                     # Sidebar cerrada por defecto
)

# -------------------------------------------------------------------
# PALETA / THEME (colores corporativos y escalas)
# -------------------------------------------------------------------
COLOR_PRIMARY = "#059669"       # Verde DIMEX principal
COLOR_PRIMARY_SOFT = "#6ee7b7"  # Verde suave para fondos
COLOR_PRIMARY_DARK = "#064e3b"  # Verde oscuro para textos/acentos
COLOR_RISK    = "#ef4444"       # Rojo riesgo
COLOR_SUCCESS = "#10b981"       # Verde éxito
COLOR_WARN    = "#f59e0b"       # Ámbar advertencia
COLOR_NEUTRAL = "#0f172a"       # Azul/gris oscuro para texto
SEMAFORO_SCALE = ["#22c55e", "#facc15", "#ef4444"]  # Escala riesgo (verde-amarillo-rojo)

# -------------------------------------------------------------------
# ESTILOS GLOBALES + ANIMACIONES (inyecta CSS en la página)
# -------------------------------------------------------------------


def inject_global_styles():
    # Usamos st.markdown con unsafe_allow_html para insertar <style> global
    st.markdown("""
                
        
    
                

    <style>
        /* ===== TÍTULOS DE SECCIÓN DIMEX UI ===== */

        .section-title {
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
            font-size: 22px !important;
            font-weight: 600 !important;
            color: #0f172a !important;
            text-align: center !important;
            padding-bottom: 6px !important;
            margin-top: 6px !important;
            margin-bottom: 14px !important;
            letter-spacing: -0.3px;
        }

        /* Para títulos h3, h4, h5 nativos de Streamlit */
        h3, h4, h5 {
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
            text-align: center !important;
            font-weight: 600 !important;
            color: #0f172a !important;
        }
    </style>

    <style>

        /* ============================================
       OCULTAR TODO EL CHAT-INPUT PERO DEJAR SU ESPACIO
       ============================================ */

        /* El contenedor completo sigue ocupando lugar, pero no se ve */
        .stChatInputContainer {
        visibility: hidden !important;
        height: 5px !important;        /* ← ajusta este valor a tu gusto */
        padding: 0 !important;
        margin: 0 auto !important;
        }

        /* El textarea dentro también se oculta */
        .stChatInputContainer textarea {
        visibility: hidden !important;
        }

        /* Quita bordes/sombras (aunque no se vean) */
        .stChatInputContainer div {
        box-shadow: none !important;
        border: none !important;
        background: transparent !important;
        }

    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <style>
            /* Tipografía tipo Creative Point */
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
            html, body, [class*="css"] {{
             font-family: "Poppins", system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
                }}

                /* Cards shadcn suavizadas */
                .scui-card, .scui-card * {{
                border-radius: 10px !important;
                }}
                .scui-card{{
                box-shadow: 0 12px 28px rgba(5,150,105,.12) !important;
                border: 1px solid rgba(5,150,105,.12) !important;
                }}

                /* Botones shadcn */
                .scui-button{{
             border-radius: 12px !important;
                box-shadow: 0 10px 22px rgba(5,150,105,.20) !important;
                }}

        /* --- Variables CSS a partir de la paleta Python --- */
        :root {{
            --dimex-green: {COLOR_PRIMARY};
            --dimex-green-soft: {COLOR_PRIMARY_SOFT};
            --dimex-green-dark: {COLOR_PRIMARY_DARK};
            --risk: {COLOR_RISK};
            --ok: {COLOR_SUCCESS};
            --warn: {COLOR_WARN};
            --ink: {COLOR_NEUTRAL};
        }}

        /* --- Layout base del contenedor central de Streamlit --- */
        .block-container {{
            padding-top: 0.6rem;             /* margen arriba para respirar */
            padding-bottom: 1.2rem;          /* margen abajo */
            max-width: 1300px !important;    /* limita ancho máximo */
        }}

       
                    /* === Tabs container centrado === */
            .stTabs [data-baseweb="tab-list"] {{
                justify-content: center !important;
                gap: 32px !important;            /* Más separación */
            }}

            /* === Tabs estilo pill grande === */
            .stTabs [data-baseweb="tab"] {{
                padding: 12px 26px !important;   /* MÁS grande */
                border-radius: 999px !important;

                background: rgba(16,185,129,0.07) !important;
                border: 1px solid rgba(16,185,129,0.22) !important;

                font-size: 40px !important;       /* ← AUMENTA FUENTE */
                font-weight: 600 !important;
                color: #0f172a !important;

                display: flex;
                align-items: center;
                gap: 10px;                        /* Espacio icono-texto */

                transition: all .22s ease;
            }}

            /* Hover premium */
            .stTabs [data-baseweb="tab"]:hover {{
                background: rgba(16,185,129,0.12) !important;
                transform: translateY(-2px) scale(1.02);
                box-shadow: 0 8px 20px rgba(16,185,129,0.20);
            }}

            /* === TAB ACTIVO === */
            .stTabs [data-baseweb="tab"][aria-selected="true"] {{
                background: linear-gradient(180deg,#059669,#10b981) !important;
                color: white !important;
                border: none !important;
                box-shadow: 0 10px 28px rgba(16,185,129,0.35);

                font-size: 17px !important;      /* Más grande el activo */
                padding: 14px 30px !important;
            }}

            /* Íconos dentro del tab */
            .stTabs [data-baseweb="tab"] svg {{
                width: 20px !important;          /* Aumenta tamaño icono */
                height: 20px !important;
            }}


            /* Hover suave */
            .stTabs [data-baseweb="tab"]:hover{{
                background: rgba(16,185,129,0.12) !important;
                transform: translateY(-1px);
                box-shadow: 0 6px 16px rgba(16,185,129,0.15);
            }}

            /* Tab ACTIVO */
            .stTabs [data-baseweb="tab"][aria-selected="true"]{{
                background: linear-gradient(180deg,#059669,#10b981) !important;
                color: white !important;
                border: none !important;
                box-shadow: 0 8px 18px rgba(16,185,129,0.30);
            }}


       

        /* --- Tarjetas KPI --- */
        .kpi {{
            border-radius: 14px;
            border: 1px solid rgba(226,232,240,0.9);
            background: linear-gradient(180deg, rgba(236,253,245,0.95), rgba(240,253,244,0.7));
            box-shadow: 0 2px 8px rgba(16,185,129,0.12);
            padding: 12px 14px;
        }}

        /* --- Barra de salud (llenado animado) --- */
        @keyframes fillWidth {{
            0% {{ width: 0%; }}
            100% {{ width: var(--health-width, 0%); }}
        }}
        .health-bar {{
            height: 10px;
            border-radius: 999px;
            background: #d1fae5;
            overflow: hidden;
            position: relative;
        }}
        .health-bar > span {{
            display: block;
            height: 100%;
            background: linear-gradient(90deg, var(--dimex-green), #34d399);
            animation: fillWidth 1s ease forwards;  /* animación de entrada */
            box-shadow: inset 0 0 8px rgba(255,255,255,0.8);
        }}

        /* --- Botón DIMEX genérico --- */
        -        /* === BOTONES NATIVOS DIMEX (st.button, st.download_button, etc.) === */

        .stButton > button,
        .stDownloadButton > button {{
            border-radius: 999px !important;                     /* pill */
            border: 1px solid rgba(148,163,184,0.55) !important;
            background: #ffffff !important;
            padding: 9px 22px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            color: #0f172a !important;
            box-shadow: 0 4px 14px rgba(15,23,42,0.08) !important;
            transition: transform .14s ease,
                        box-shadow .18s ease,
                        background .18s ease,
                        border-color .18s ease,
                        color .18s ease !important;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 12px 26px rgba(16,185,129,0.30) !important;
            border-color: rgba(16,185,129,0.85) !important;
            background: linear-gradient(90deg,#ecfdf5,#f0fdfa) !important;
            color: #064e3b !important;
        }}

        .stButton > button:active,
        .stDownloadButton > button:active {{
            transform: translateY(0px) scale(.98);
            box-shadow: 0 6px 18px rgba(16,185,129,0.25) !important;
        }}


        /* --- Botones flotantes (FAB) --- */
        .fab-wrap {{
            position: fixed;
            right: 22px;
            bottom: 22px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .fab {{
            width: 54px; height: 54px;
            border-radius: 999px;
            background: radial-gradient(circle at 30% 20%, #34d399, var(--dimex-green));
            display: grid; place-items: center;
            color: white; font-weight: 800;
            border: 1px solid rgba(16,185,129,0.6);
            box-shadow: 0 10px 28px rgba(16,185,129,0.38);
            cursor: pointer;
            transition: transform .15s ease, box-shadow .15s ease, filter .2s ease;
            user-select: none;
        }}
        .fab:hover {{
            transform: translateY(-2px) scale(1.03);
            box-shadow: 0 16px 36px rgba(16,185,129,0.45);
            filter: saturate(1.08);
        }}

        /* --- Badges suaves de aviso --- */
        .badge-soft {{
            display:inline-block;padding:4px 8px;border-radius:999px;
            background:rgba(254,249,195,0.9);border:1px solid #fde68a;color:#92400e;
            font-size:12px;
        }}

        /* --- Header sticky (cinta superior) --- */
        .dimex-header {{
            position: sticky; top: 0;
            z-index: 500;
            backdrop-filter: blur(8px);
            background: linear-gradient(90deg, rgba(255,255,255,0.85), rgba(255,255,255,0.6));
            border-bottom: 1px solid rgba(148,163,184,0.25);
            margin-bottom: .4rem;
        }}

        /* --- Espaciador para que el sticky no tape contenido --- */
        .top-spacer {{ height: 6px; }}

        /* --- DataFrame con bordes redondeados --- */
        .stDataFrame {{ border-radius: 12px; overflow: hidden; }}

        </style>
        """,
        unsafe_allow_html=True  # Permitimos HTML/CSS crudo
    )
    st.markdown("""
<style>
    /* 🔧 Forzar estilo limpio en el árbol predictor */
    .arbol-html-card * {
        font-family: "Poppins", system-ui, sans-serif !important;
        white-space: normal !important;
        overflow-wrap: break-word !important;
        font-size: 13px !important;
        color: #111827 !important;
    }

    .arbol-html-card {
        background: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# Inyectar los estilos al arrancar
inject_global_styles()

# -------------------------------------------------------------------
# CONSTANTES DE COLUMNAS (nombres que vienen en tu Excel)
# -------------------------------------------------------------------
COL_SUCURSAL     = "Región"                           # Nombre de columna de región/sucursal
COL_SALDO        = "Saldo Insoluto Actual"            # Saldo total actual
COL_SALDO_VENC   = "Saldo Insoluto Vencido Actual"    # Saldo vencido
COL_SALDO_VIG    = "Saldo Insoluto Vigente Actual"    # Saldo vigente
COL_COLOCACION   = "Colocación promedio mensual"      # Colocación mensual promedio
COL_ICV          = "ICV"                               # Índice de calidad de venta
COL_MORA         = "Mora Temprana"                     # Proporción de mora temprana
COL_PERDIDAS     = "Pérdidas Tempranas"                # Pérdidas
COL_RECUP        = "Tasa de recuperación Actual"       # Recuperación
COL_FPD          = "FPD"                               # First Payment Default
COL_MARGEN_NETO  = "Margen Financiero Neto Actual"     # Margen financiero
COL_SCORE_RAW    = "Score_Final_S10"                   # Score bruto del modelo
COL_CLUSTER      = "Cluster_Final_S10"                 # Cluster final

# Ruta local al archivo de datos (ajústala a tu archivo)
DATA_PATH = Path(r"Reto_final_limpio_estesi_con_clusters_S10.xlsx")

# -------------------------------------------------------------------
# ESTADO DE CHAT DE DIMI (en memoria de sesión)
# -------------------------------------------------------------------
if "dimi_history" not in st.session_state:
    st.session_state["dimi_history"] = []  # lista de mensajes [{role, content}]
# -------------------------------------------------------------------
# IA DIMI: conecta filtros actuales con modelo de OpenAI
# -------------------------------------------------------------------
def dimi_answer(user_msg: str, df_context: pd.DataFrame) -> str:
    """DIMI nivel analista senior, con contexto completo y comparaciones globales."""

    if client is None:
        msg = "No hay API KEY configurada."
        st.session_state["dimi_history"].append({"role": "assistant", "content": msg})
        return msg

    # === SUMMARY DEL FILTRO ACTUAL ===========================================
    resumen_segmento = {
        "num_sucursales": int(len(df_context)),
        "colocacion_total": float(df_context[COL_COLOCACION].sum()),
        "mora_prom": float(df_context[COL_MORA].mean()),
        "recuperacion_prom": float(df_context[COL_RECUP].mean()),
        "fpd_prom": float(df_context[COL_FPD].mean()),
        "risk_prom": float(df_context["Risk_Score"].mean()),
        "margen_neto_total": float(df_context[COL_MARGEN_NETO].sum()),
    }

    # === SUMMARY GLOBAL POR CLUSTER ==========================================
    cluster_stats = (
        df_full.groupby(COL_CLUSTER)
        .agg(
            num_suc=(COL_SUCURSAL, "count"),
            colocacion=(COL_COLOCACION, "sum"),
            mora=(COL_MORA, "mean"),
            recup=(COL_RECUP, "mean"),
            fpd=(COL_FPD, "mean"),
            risk=("Risk_Score", "mean"),
        )
        .reset_index()
        .to_dict(orient="records")
    )

    # === PERCENTILES GLOBALES ================================================
    percentiles = {
        "mora_p75": float(df_full[COL_MORA].quantile(0.75)),
        "recup_p25": float(df_full[COL_RECUP].quantile(0.25)),
        "risk_p75": float(df_full["Risk_Score"].quantile(0.75)),
        "risk_p25": float(df_full["Risk_Score"].quantile(0.25)),
    }

    # === TOP SUCURSALES GLOBAL ===============================================
    top_sucursales_global = (
        df_full.sort_values("Risk_Score", ascending=False)
        .head(10)[[COL_SUCURSAL, "Risk_Score", COL_MORA, COL_RECUP, COL_FPD]]
        .to_dict(orient="records")
    )

    # === PROMPT NIVEL ANALISTA SENIOR ========================================
    system_prompt = f"""
Eres **DIMI**, analista senior de riesgo de DIMEX.
Tu tono SIEMPRE debe ser:
- Ejecutivo
- Claro y analítico
- Similar a un reporte para comité

Tienes 3 fuentes de información:
1) Segmento filtrado actual (df_context)
2) Estadísticas globales de la red (df_full)
3) Comparativos entre clusters (cluster_stats)

REGLAS:
- Siempre que puedas, compara el segmento con la red completa.
- Detecta riesgos, tendencias, focos rojos, y oportunidades.
- Propón acciones operativas reales: cobranza, originación, auditoría, procesos.
- Usa los percentiles globales para contextualizar si algo está “alto”, “normal” o “crítico”.
- NO inventes datos; todo lo que digas debe poder derivarse de los summaries.
- Ofrece insights, no solo números.

CUANDO EL USUARIO PIDA:
- “cómo calcular”: da fórmulas en pandas.
- “predicción o regresión”: explica cómo hacerla y qué variables usar.
- “comparaciones”: usa cluster_stats.
- “diagnóstico”: combina riesgo, mora, recuperación y fpd.
- “reporte ejecutivo”: resume en bullets.

AQUÍ ESTÁ TU CONTEXTO:

SEGMENTO FILTRADO:
{json.dumps(resumen_segmento, ensure_ascii=False)}

CLUSTERS GLOBALES:
{json.dumps(cluster_stats, ensure_ascii=False)}

PERCENTILES GLOBALES:
{json.dumps(percentiles, ensure_ascii=False)}

TOP SUCURSALES GLOBAL:
{json.dumps(top_sucursales_global, ensure_ascii=False)}
"""

    # === MENSAJES ============================================================
    messages = [{"role": "system", "content": system_prompt}]
    messages += st.session_state["dimi_history"]
    messages.append({"role": "user", "content": user_msg})

    # === LLAMADA AL MODELO ===================================================
    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # o gpt-5-nano (sin temperature)
        messages=messages,
        temperature=0.2,
    )

    answer = response.choices[0].message.content

    # Guarda historial
    st.session_state["dimi_history"].append({"role": "user", "content": user_msg})
    st.session_state["dimi_history"].append({"role": "assistant", "content": answer})

    return answer

# -------------------------------------------------------------------
# CARGA Y PREPARACIÓN DE DATOS (lee Excel, valida y crea métricas)
# -------------------------------------------------------------------
@st.cache_data
def load_data(path: Path):
    if not path.exists():                                   # Si no existe el archivo...
        st.error(f"No se encontró el archivo en la ruta: {path}")  # Mensaje de error
        st.stop()                                           # Detiene la app

    df = pd.read_excel(path)                                # Carga el Excel en DataFrame

    # Columnas requeridas para que todo funcione
    required = [
        COL_SUCURSAL, COL_SALDO, COL_SALDO_VENC, COL_SALDO_VIG,
        COL_COLOCACION, COL_ICV, COL_MORA, COL_PERDIDAS,
        COL_RECUP, COL_FPD, COL_MARGEN_NETO, COL_SCORE_RAW, COL_CLUSTER
    ]
    missing = [c for c in required if c not in df.columns]  # Detecta faltantes
    if missing:
        st.error(f"Faltan columnas requeridas en el Excel: {missing}")  # Avisa cuáles
        st.stop()

    # Forzar tipos numéricos (coerce pone NaN si no se puede convertir)
    numeric_cols = [
        COL_SALDO, COL_SALDO_VENC, COL_SALDO_VIG,
        COL_COLOCACION, COL_ICV, COL_MORA, COL_PERDIDAS,
        COL_RECUP, COL_FPD, COL_MARGEN_NETO, COL_SCORE_RAW
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Elimina filas con NaN críticos que romperían la vista
    df.dropna(
        subset=[COL_SUCURSAL, COL_SALDO, COL_COLOCACION, COL_ICV,
                COL_MORA, COL_RECUP, COL_FPD, COL_SCORE_RAW, COL_CLUSTER],
        inplace=True
    )

    # Normaliza Score_Final_S10 a 0–100 como Health_Index y define Risk_Score inverso
    score_min = df[COL_SCORE_RAW].min()
    score_max = df[COL_SCORE_RAW].max()
    if score_max == score_min:
        df["Health_Index"] = 50.0                          # Caso degenerado: valor fijo
    else:
        df["Health_Index"] = (df[COL_SCORE_RAW] - score_min) / (score_max - score_min) * 100.0
    df["Risk_Score"] = 100.0 - df["Health_Index"]         # Riesgo es inverso a salud

    # Asegura tipos string en claves categóricas
    df[COL_SUCURSAL] = df[COL_SUCURSAL].astype(str)
    df[COL_CLUSTER]  = df[COL_CLUSTER].astype(str)

    return df                                              # Devuelve DataFrame listo

# Carga única (cacheada) del dataset completo
df_full = load_data(DATA_PATH)

# -------------------------------------------------------------------
# FORMATOS Y HELPERS DE TEXTO
# -------------------------------------------------------------------
def fmt_currency(v):                      # Formatea MXN sin decimales con separador de miles
    return f"${v:,.0f}" if pd.notnull(v) else "$0"

def fmt_percent(v):
    if pd.isnull(v):
        return "N/D"
    if v > 1.5:
        v = v / 100.0
    return f"{v*100:.1f}%"

def fmt_ratio(v):                         # Alias semántico (usa fmt_percent)
    return fmt_percent(v)

def get_cluster_color(cluster):           # Mapea texto del cluster a color de fondo
    text = str(cluster).lower()
    if "desarrollo" in text:
        return "#fef9c3"  # amarillo claro
    if "estrella" in text:
        return "#dcfce7"  # verde claro
    if any(w in text for w in ["riesgo", "alto"]):
        return "#fee2e2"
    if any(w in text for w in ["regular", "medio"]):
        return "#fef9c3"
    if any(w in text for w in ["excelente", "bueno", "bajo"]):
        return "#dcfce7"
    return "#e5e7eb"

def get_risk_level(avg_risk):             # Traduce score promedio de riesgo a etiqueta y texto
    if avg_risk < 33:
        return "bajo", "El portafolio filtrado se encuentra en una zona de control, con riesgo bajo y buen desempeño general."
    if avg_risk < 66:
        return "moderado", "El portafolio filtrado muestra señales mixtas: algunas sucursales sanas conviven con focos de riesgo que conviene priorizar."
    return "alto", "El portafolio filtrado concentra una proporción relevante en sucursales de alto riesgo; se recomienda focalizar medidas inmediatas de cobranza."

# -------------------------------------------------------------------
# FILTRADO (aplica filtros seleccionados en UI)
# -------------------------------------------------------------------
@st.cache_data
def apply_filters(df, filters, quick):
    df_f = df.copy()                                      # Trabaja sobre copia
    if filters["cluster"] != "Todos":                     # Filtro por cluster
        df_f = df_f[df_f[COL_CLUSTER] == filters["cluster"]]
    if filters["sucursal"] != "Todas":                    # Filtro por sucursal
        df_f = df_f[df_f[COL_SUCURSAL] == filters["sucursal"]]
    if quick["alto_riesgo"]:                              # Filtro rápido: umbral de riesgo
        df_f = df_f[df_f["Risk_Score"] >= quick["umbral_riesgo"]]
    if quick["mora_alta"]:                                # Filtro rápido: mora > p75 global
        q_mora = df[COL_MORA].quantile(0.75)
        df_f = df_f[df_f[COL_MORA] >= q_mora]
    if quick["recup_baja"]:                               # Filtro rápido: recup < p25 global
        q_rec = df[COL_RECUP].quantile(0.25)
        df_f = df_f[df_f[COL_RECUP] <= q_rec]
    return df_f

# -------------------------------------------------------------------
# THEME PARA PLOTLY (estandariza altura, márgenes y fondos)
# -------------------------------------------------------------------
def apply_plotly_theme(fig, height=340):
    fig.update_layout(
        height=height,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(255,255,255,1)",    # blanco pleno para contraste limpio
        plot_bgcolor="rgba(255,255,255,0.98)",  # casi blanco, elegante
        font=dict(size=13, family="Poppins"),   # tipografía moderna
        legend=dict(
            borderwidth=0,
            bgcolor="rgba(255,255,255,0.0)"
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Poppins"
        )
    )

    fig.update_xaxes(showline=True, linewidth=1, linecolor='rgba(148,163,184,0.3)', mirror=True, zeroline=False)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='rgba(148,163,184,0.3)', mirror=True, zeroline=False)

    return fig

# -------------------------------------------------------------------
# COMPONENTES VISUALES REUSABLES (cards, KPIs, gráficos)
# -------------------------------------------------------------------
def card_container(open_tag=True):                        # Abre/cierra un <div> con clase card
    if open_tag:
        st.markdown("<div class='dimex-card'>", unsafe_allow_html=True)
    else:
        st.markdown("</div>", unsafe_allow_html=True)

  # Renderiza un KPI
def kpi_card(title, value_str, subtitle=None, color=COLOR_PRIMARY):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(180deg, #F0FDF4, #ECFDF5);
            border-radius: 16px;
            border: 1px solid rgba(5,150,105,0.25);
            box-shadow: 0 8px 24px rgba(5,150,105,0.12);
            padding: 20px 18px;
            text-align: left;
            transition: transform .2s ease, box-shadow .2s ease;
        ">
            <p style="margin:0; font-size:18px; font-weight:500; color:#065F46;">
                {title}
            </p>
            <p style="margin:6px 0 0 0; font-size:28px; font-weight:800; color:{color};">
                {value_str}
            </p>
            <p style="margin:4px 0 0 0; font-size:16px; color:#6B7280;">
                {subtitle or ""}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def risk_gauge(avg_risk: float):                         # Medidor semicircular de riesgo
    if avg_risk < 33:
        level, color = "Bajo", COLOR_SUCCESS
    elif avg_risk < 66:
        level, color = "Moderado", COLOR_WARN
    else:
        level, color = "Alto", COLOR_RISK

    # Usamos go.Indicator con modo "gauge+number"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=avg_risk,                                # Valor a mostrar
            title={"text": f"Nivel de riesgo: {level}", "font": {"size": 16, "color": color}},
            number={"suffix": " / 100"},                   # Sufijo del número
            gauge={                                        # Config del gauge (una sola llave)
                "axis": {"range": [0, 100]},               # Rango 0-100
                "bar": {"color": color},                   # Color de la barra
                "bgcolor": "rgba(255,255,255,1)",          # Fondo gauge
                "borderwidth": 1,
                "bordercolor": "#cbd5f5",
                "steps": [                                 # Tramos de color (semaforizados)
                    {"range": [0, 33], "color": "#dcfce7"},
                    {"range": [33, 66], "color": "#fef9c3"},
                    {"range": [66, 100], "color": "#fee2e2"},
                ],
            },
        )
    )
    apply_plotly_theme(fig, height=340)                   # Aplica tema común
    st.plotly_chart(fig, use_container_width=True)        # Renderiza en Streamlit

def bubble_risk_map(df, x_metric, y_metric, size_metric): # Mapa de burbujas riesgo
    if df.empty:
        st.info("No hay datos para mostrar en el mapa de burbujas.")
        return
    fig = px.scatter(
        df,
        x=x_metric["col"],                                # Columna eje X
        y=y_metric["col"],                                # Columna eje Y
        size=size_metric["col"],                          # Tamaño burbuja
        color="Risk_Score",                               # Color por riesgo
        color_continuous_scale=SEMAFORO_SCALE,            # Escala semáforo
        hover_name=COL_SUCURSAL,                          # Tooltip principal
        hover_data={                                      # Tooltip adicional (formateos)
            COL_COLOCACION: ":.0f",
            COL_MORA: ":.3f",
            COL_RECUP: ":.3f",
            COL_FPD: ":.3f",
            COL_ICV: ":.3f",
            "Risk_Score": ":.1f",
            COL_MARGEN_NETO: ":.0f",
            COL_CLUSTER: True,
        },
        labels={                                          # Etiquetas de ejes
            x_metric["col"]: x_metric["label"],
            y_metric["col"]: y_metric["label"],
            "Risk_Score": "Score de riesgo",
        },
        size_max=42,                                      # Tamaño máximo de burbuja
        template="plotly_white"                           # Tema base Plotly
    )
    fig.update_traces(marker=dict(line=dict(width=1.5, color="rgba(15,23,42,0.9)")))  # Borde burbuja
    apply_plotly_theme(fig, height=360)
    fig.update_layout(coloraxis_colorbar=dict(title="Riesgo", ticks="outside"))
    st.plotly_chart(fig, use_container_width=True)

def ranking_barras(df, min_risk, top_n):                 # Ranking horizontal por riesgo
    if df.empty:
        st.info("No hay datos para ranking.")
        return
    df_rank = df[df["Risk_Score"] >= min_risk]           # Filtra por umbral
    if df_rank.empty:
        st.info("No hay sucursales con score de riesgo por encima del umbral seleccionado.")
        return
    df_rank = df_rank.sort_values("Risk_Score", ascending=False).head(top_n)  # Top N
    fig = px.bar(
        df_rank.sort_values("Risk_Score"),                # Orden para barras apiladas
        x="Risk_Score",
        y=COL_SUCURSAL,
        color="Risk_Score",
        color_continuous_scale=SEMAFORO_SCALE,
        orientation="h",
        labels={"Risk_Score": "Score de riesgo"},
        template="plotly_white"
    )
    apply_plotly_theme(fig, height=360)
    fig.update_layout(xaxis_title="Score de riesgo (0-100)", yaxis_title="Sucursal",
                      coloraxis_colorbar=dict(title="Riesgo", ticks="outside"))
    st.plotly_chart(fig, use_container_width=True)

def perfil_kpis_por_decil(df):                           # Serie de líneas por decil de riesgo
    if df.empty:
        st.info("No hay datos para el perfil por deciles.")
        return
    df_dec = df.copy()
    try:
        df_dec["Decil_Riesgo"] = pd.qcut(df_dec["Risk_Score"], 10, labels=False, duplicates="drop")  # Deciles
    except ValueError:
        st.info("No se pudieron generar deciles de riesgo (muy pocos datos distintos).")
        return
    grp = df_dec.groupby("Decil_Riesgo").agg({           # KPIs promedio por decil
        COL_COLOCACION: "mean",
        COL_MORA: "mean",
        COL_RECUP: "mean",
        COL_FPD: "mean"
    }).reset_index()
    grp["Decil_Riesgo"] = grp["Decil_Riesgo"].astype(int) + 1  # 1..10 en lugar de 0..9
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=grp["Decil_Riesgo"], y=grp[COL_COLOCACION], name="Colocación",
                             mode="lines+markers", line=dict(color=COLOR_PRIMARY, width=3)))
    fig.add_trace(go.Scatter(x=grp["Decil_Riesgo"], y=grp[COL_MORA], name="Mora",
                             mode="lines+markers", yaxis="y2", line=dict(color=COLOR_RISK, width=2)))
    fig.add_trace(go.Scatter(x=grp["Decil_Riesgo"], y=grp[COL_RECUP], name="Recuperación",
                             mode="lines+markers", yaxis="y3", line=dict(color="#0ea5e9", width=2)))
    fig.add_trace(go.Scatter(x=grp["Decil_Riesgo"], y=grp[COL_FPD], name="%FPD",
                             mode="lines+markers", yaxis="y4", line=dict(color=COLOR_WARN, width=2)))
    fig.update_layout(
        xaxis=dict(title="Decil de riesgo (1 = menor, 10 = mayor)", domain=[0.1, 0.9]),
        yaxis=dict(title="Colocación (MXN)"),
        yaxis2=dict(title="Mora", overlaying="y", side="right", position=0.9),
        yaxis3=dict(title="Recuperación", overlaying="y", side="left", position=0.0),
        yaxis4=dict(title="%FPD", overlaying="y", side="right", position=1.0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title="Perfil de KPIs por decil de riesgo"
    )
    apply_plotly_theme(fig, height=360)
    st.plotly_chart(fig, use_container_width=True)

def margen_por_cluster(df):                              # Barra horizontal de margen por cluster
    if df.empty:
        st.info("No hay datos para margen por cluster.")
        return
    grp = df.groupby(COL_CLUSTER)[COL_MARGEN_NETO].mean().reset_index()  # Media por cluster
    grp = grp.sort_values(COL_MARGEN_NETO, ascending=True)               # Ordena de menor a mayor
    fig = px.bar(
        grp, x=COL_MARGEN_NETO, y=COL_CLUSTER, orientation="h",
        labels={COL_MARGEN_NETO: "Margen financiero neto promedio (MXN)", COL_CLUSTER: "Cluster"},
        color_discrete_sequence=[COLOR_PRIMARY],
        template="plotly_white"
    )
    apply_plotly_theme(fig, height=260)
    st.plotly_chart(fig, use_container_width=True)

def mapa_riesgo_rentabilidad(df):                        # Dispersión riesgo vs margen
    if df.empty:
        st.info("No hay datos para el mapa riesgo–rentabilidad.")
        return
    risk_med   = df["Risk_Score"].median()               # Mediana de riesgo
    margen_med = df[COL_MARGEN_NETO].median()            # Mediana de margen
    fig = px.scatter(
        df,
        x="Risk_Score",
        y=COL_MARGEN_NETO,
        size=COL_COLOCACION,
        color=COL_CLUSTER,
        hover_name=COL_SUCURSAL,
        hover_data={
            COL_COLOCACION: ":.0f",
            COL_MORA: ":.3f",
            COL_RECUP: ":.3f",
            COL_FPD: ":.3f",
            "Risk_Score": ":.1f"
        },
        labels={"Risk_Score": "Score de riesgo", COL_MARGEN_NETO: "Margen financiero neto (MXN)"},
        size_max=40,
        template="plotly_white"
    )
    # Líneas de referencia (cuadrantes)
    fig.add_vline(x=risk_med, line_width=1, line_dash="dash", line_color="rgba(15,23,42,0.5)")
    fig.add_hline(y=margen_med, line_width=1, line_dash="dash", line_color="rgba(15,23,42,0.5)")
    # Etiquetas de zonas
    fig.add_annotation(x=risk_med * 0.4, y=margen_med * 1.3 if margen_med > 0 else margen_med + abs(margen_med)*0.3,
                       text="Joyas de la cartera", showarrow=False, font=dict(size=11, color="#166534"))
    fig.add_annotation(x=risk_med * 1.6 if risk_med > 0 else risk_med + 10,
                       y=margen_med * 1.3 if margen_med > 0 else margen_med + abs(margen_med)*0.3,
                       text="Focos rojos de alto valor", showarrow=False, font=dict(size=11, color="#b91c1c"))
    fig.add_annotation(x=risk_med * 1.6 if risk_med > 0 else risk_med + 10,
                       y=margen_med * 0.7, text="Sucursales a cuestionar",
                       showarrow=False, font=dict(size=11, color="#92400e"))
    fig.add_annotation(x=risk_med * 0.4, y=margen_med * 0.7, text="Potencial de desarrollo",
                       showarrow=False, font=dict(size=11, color="#0f172a"))
    apply_plotly_theme(fig, height=360)
    st.plotly_chart(fig, use_container_width=True)

def radar_riesgo_multifactor(df_segment):                # Radar comparativo por KPIs
    if df_segment.empty:
        st.info("No hay datos para el radar de riesgo.")
        return
    mode = st.radio("Vista del radar", ["Por cluster", "Por sucursal (Top 5 riesgo)"],
                    horizontal=True, key="radar_mode")    # Selector de modo

    # Definición de métricas y si son "inversas" (alto es bueno) o no
    metrics = {
        "Mora temprana": {"col": COL_MORA, "inverse": False},
        "%FPD": {"col": COL_FPD, "inverse": False},
        "Recuperación": {"col": COL_RECUP, "inverse": True},
        "ICV": {"col": COL_ICV, "inverse": False},
    }
    # Calcula percentiles globales para puntuar comparativamente
    global_risk_scores = {}
    for name, meta in metrics.items():
        col = meta["col"]
        s = df_full[col].copy()
        s = pd.to_numeric(s, errors="coerce").dropna()
        if s.empty:
            continue
        pct = s.rank(method="average", pct=True)          # Percentil 0..1
        global_risk_scores[name] = (1 - pct) if meta["inverse"] else pct

    # Genera series por cluster o por top sucursales
    if mode.startswith("Por cluster"):
        entities = df_segment[COL_CLUSTER].unique().tolist()[:6]
        series_list = []
        for cl in entities:
            sub = df_segment[df_segment[COL_CLUSTER] == cl]
            values = []
            for name, meta in metrics.items():
                if name not in global_risk_scores:
                    values.append(0.0)
                    continue
                g_pct = global_risk_scores[name]
                common_idx = sub.index.intersection(g_pct.index)
                values.append(float(g_pct.loc[common_idx].mean()) if len(common_idx) else 0.0)
            series_list.append({"label": cl, "values": values})
    else:
        top_suc = df_segment.sort_values("Risk_Score", ascending=False)[COL_SUCURSAL].unique().tolist()[:5]
        series_list = []
        for suc in top_suc:
            sub = df_segment[df_segment[COL_SUCURSAL] == suc]
            values = []
            for name, meta in metrics.items():
                if name not in global_risk_scores:
                    values.append(0.0)
                    continue
                g_pct = global_risk_scores[name]
                common_idx = sub.index.intersection(g_pct.index)
                values.append(float(g_pct.loc[common_idx].mean()) if len(common_idx) else 0.0)
            series_list.append({"label": suc, "values": values})

    if not series_list:
        st.info("No se pudieron calcular perfiles de riesgo comparables para el radar.")
        return

    theta = list(metrics.keys())                          # Ejes del radar
    fig = go.Figure()
    base_colors = ["#22c55e", "#0ea5e9", "#f97316", "#a855f7", "#ef4444", "#14b8a6"]
    for i, serie in enumerate(series_list):
        vals = serie["values"]
        r = vals + [vals[0]]                               # Cierra polígono
        th = theta + [theta[0]]
        fig.add_trace(go.Scatterpolar(
            r=r, theta=th, name=serie["label"],
            line=dict(color=base_colors[i % len(base_colors)], width=2),
            fill="toself", opacity=0.3
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickformat=".0%", tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11))
        ),
        showlegend=True, title="Perfil de riesgo relativo por KPI"
    )
    apply_plotly_theme(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Valores cercanos a 100% indican mayor riesgo relativo vs la red.")

def tabla_detalle(df):
    if df.empty:
        st.info("No hay datos para la tabla.")
        return

    # === Selección y renombrado ===
    df_t = df[[
        COL_SUCURSAL, COL_CLUSTER, COL_COLOCACION, COL_ICV, COL_MORA,
        COL_FPD, COL_RECUP, COL_SALDO, COL_MARGEN_NETO, "Risk_Score"
    ]].copy()

    df_t.rename(columns={
        COL_SUCURSAL: "Sucursal",
        COL_CLUSTER: "Cluster",
        COL_COLOCACION: "Colocación mensual",
        COL_ICV: "ICV",
        COL_MORA: "Mora temprana",
        COL_FPD: "%FPD",
        COL_RECUP: "Recuperación",
        COL_SALDO: "Saldo insoluto",
        COL_MARGEN_NETO: "Margen financiero neto",
        "Risk_Score": "Score riesgo"
    }, inplace=True)

    # === FORMATEO VISUAL PRO (TRUNCADO + COMAS + $ + %) ===
    df_fmt = df_t.copy()

    for col in df_fmt.columns:
        col_lower = col.lower()

        # DINERO
        if any(k in col_lower for k in ["colocación", "margen", "saldo"]):
            df_fmt[col] = df_fmt[col].apply(lambda x: f"${x:,.0f}")

        # PORCENTAJES (mora, recuperación, fpd)
        elif any(k in col_lower for k in ["mora", "recuperación", "fpd"]):
            df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1%}")

        # SCORE
        elif "score" in col_lower:
            df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1f}")

        # NÚMEROS NORMALES
        elif pd.api.types.is_numeric_dtype(df_fmt[col]):
            df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:,.2f}")

    # === Mostrar ===
    st.dataframe(df_fmt, use_container_width=True)

    # Estilo por color según cluster
    def style_cluster(col):
        return [f"background-color: {get_cluster_color(v)}; color: #111827;" for v in col]

    styled = df_t.style.apply(style_cluster, subset=["Cluster"])     # Aplica estilo
 # Muestra DataFrame
    st.caption(f"Total de sucursales mostradas: {len(df_t)}")

def drivers_riesgo(df):                                   # Importancias vía árbol de decisión
    st.markdown("""
          
            <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:4px 10px;
                    border-radius:8px;
                    font-size:20px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                    Drivers estadísticos de riesgo
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    if not SKLEARN_AVAILABLE:                              # Si no hay sklearn, avisar
        st.warning("Para calcular drivers de riesgo instala scikit-learn: pip install scikit-learn")
        return
    features = [COL_MORA, COL_FPD, COL_RECUP, COL_ICV, COL_COLOCACION]  # Variables explicativas
    for c in features:
        if c not in df.columns:
            st.info(f"No se puede entrenar el modelo. Falta la columna: {c}")
            return
    df_model = df.dropna(subset=features)                  # Quita filas incompletas
    if df_model.empty:
        st.info("No hay suficientes datos (después de filtros) para calcular drivers.")
        return
    df_model["High_Risk"] = (df_model["Risk_Score"] >= 70).astype(int)  # Target binario
    y = df_model["High_Risk"]
    if y.nunique() < 2:
        st.info("Se necesita al menos una muestra de alto y bajo riesgo para comparar.")
        return
    X = df_model[features]
    clf = DecisionTreeClassifier(max_depth=3, random_state=42)      # Modelo simple
    clf.fit(X, y)
    importances = pd.DataFrame({"Variable": features, "Importancia": clf.feature_importances_}).sort_values("Importancia", ascending=True)
    fig = px.bar(importances, x="Importancia", y="Variable", orientation="h",
                 labels={"Importancia": "Importancia relativa"},
                 color_discrete_sequence=[COLOR_PRIMARY], template="plotly_white")
    apply_plotly_theme(fig, height=240)
    st.plotly_chart(fig, use_container_width=True)

def quick_actions(df_filtered):
    """Acciones rápidas tipo DIMEX."""
    st.markdown(
    """
    <h3 style='
        font-size:30px;
        font-weight:800;
        color:#0f172a;
        letter-spacing:-0.5px;
        margin-bottom:10px;
        text-align:left;
    '>
    Acciones rápidas
    </h3>
    """,
    unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        crit_clicked = st.button("🔍 Ver sucursales críticas", help="Score de riesgo ≥ 80")

    with col2:
        csv = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar reporte",
            data=csv,
            file_name=f"reporte_dimex_sucursales_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

    with col3:
        pred_clicked = st.button("🤖 Análisis predictivo")

    # --- lógica igual que ya tenías ---
    if crit_clicked:
        crit_df = df_filtered[df_filtered["Risk_Score"] >= 80].copy()
        if crit_df.empty:
            st.info("No hay sucursales con Score de riesgo ≥ 80 en los filtros actuales.")
        else:
            st.markdown("### 🔥 Sucursales críticas (Score ≥ 80)")

            # === Seleccionar columnas ===
            df_c = crit_df[[
                COL_SUCURSAL, COL_CLUSTER, "Risk_Score", COL_MORA, COL_FPD, COL_RECUP
            ]].copy()

            # === Renombrar ===
            df_c.rename(columns={
                COL_SUCURSAL: "Sucursal",
                COL_CLUSTER: "Cluster",
                "Risk_Score": "Score",
                COL_MORA: "Mora temprana",
                COL_FPD: "%FPD",
                COL_RECUP: "Recuperación",
            }, inplace=True)

            # ====== FORMATEO VISUAL ======
            df_fmt = df_c.copy()

            # Score
            df_fmt["Score"] = df_fmt["Score"].apply(lambda x: f"{x:.1f}")

            # Porcentajes
            df_fmt["Mora temprana"] = df_fmt["Mora temprana"].apply(lambda x: f"{x:.1%}")
            df_fmt["%FPD"] = df_fmt["%FPD"].apply(lambda x: f"{x:.1f}%")
            df_fmt["Recuperación"] = df_fmt["Recuperación"].apply(lambda x: f"{x:.1%}")

            # ===== ESTILO POR CLUSTER =====
            def style_cluster(col):
                return [f"background-color: {get_cluster_color(v)}; color:#111;" for v in col]

            styled = df_fmt.style.apply(style_cluster, subset=["Cluster"])

            st.dataframe(styled, use_container_width=True, hide_index=True)


    if pred_clicked:
        st.info(
            "La capa de análisis predictivo puede extenderse con modelos de probabilidad "
            "de alto riesgo por sucursal/segmento."
        )


def render_alertas(df, mora_hi, recup_low):
    """Alertas ejecutivas, con diseño más bonito tipo card."""

    alerts = []

    # --- Construcción de mensajes como antes ---
    high_mora = df[df[COL_MORA] > mora_hi]
    n_high_mora = high_mora.shape[0]
    if n_high_mora > 0:
        top_names = ", ".join(high_mora[COL_SUCURSAL].head(3).tolist())
        alerts.append(
            f"{n_high_mora} sucursales con mora temprana por encima del percentil 75 "
            f"({fmt_percent(mora_hi)}). Ejemplos: {top_names}."
        )

    low_recup = df[df[COL_RECUP] < recup_low]
    n_low_recup = low_recup.shape[0]
    if n_low_recup > 0:
        top_names = ", ".join(low_recup[COL_SUCURSAL].head(3).tolist())
        alerts.append(
            f"{n_low_recup} sucursales con recuperación por debajo del percentil 25 "
            f"({fmt_percent(recup_low)}). Ejemplos: {top_names}."
        )

    if not df.empty:
        top_fpd = df.sort_values(COL_FPD, ascending=False).iloc[0]
        alerts.append(
            f"Sucursal con FPD más alto: {top_fpd[COL_SUCURSAL]} "
            f"(FPD {fmt_percent(top_fpd[COL_FPD])})."
        )

    # --- Render bonito ---
    st.markdown(
        """
        <div style="display:flex; justify-content:center; margin-bottom:14px;">
            <span style="
                display:inline-block;
                background:linear-gradient(180deg,#fef2f2,#fff7f7);
                padding:6px 16px;
                border-radius:12px;
                font-size:22px;
                font-weight:700;
                color:#991b1b;
                border:1px solid #fecaca;
                box-shadow:0 4px 12px rgba(248,113,113,0.10);
                letter-spacing:-0.3px;
            ">
            Alertas clave
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


    if not alerts:
        st.info("No se detectaron alertas críticas con los umbrales basados en históricos.")
        return

    # Card contenedor
    st.markdown(
        f"""
        <div style="
            border-radius: 16px;
            padding: 12px 14px 10px 14px;
            background: linear-gradient(180deg,#fef2f2,#fff7f7);
            border: 1px solid #fecaca;
            box-shadow: 0 6px 18px rgba(248,113,113,0.18);
        ">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <div style="
                        width:26px;height:26px;border-radius:999px;
                        background:radial-gradient(circle at 30% 0%, #fed7d7, #ef4444);
                        display:flex;align-items:center;justify-content:center;
                        color:white;font-weight:800;font-size:16px;
                    ">!</div>
                    <div>
                        <div style="font-size:18px;font-weight:600;color:#991b1b;">
                            Riesgos a vigilar en el segmento filtrado
                        </div>
                        <div style="font-size:16px;color:#b91c1c;">
                            {len(alerts)} alerta(s) activa(s) con base en percentiles históricos
                        </div>
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Cada alerta como “pill” con iconito
    for a in alerts:
        st.markdown(
            f"""
            <div style="
                margin-top:6px;
                display:flex;
                align-items:flex-start;
                gap:8px;
                padding:7px 9px;
                border-radius:12px;
                background:rgba(254,242,242,0.95);
                border:1px solid rgba(254,202,202,0.9);
                font-size:18px;
                color:#7f1d1d;
            ">
                <div style="
                    width:18px;height:18px;border-radius:999px;
                    background:#fee2e2;
                    display:flex;align-items:center;justify-content:center;
                    font-size:11px;font-weight:700;color:#b91c1c;
                    flex-shrink:0;
                ">!</div>
                <div style="line-height:1.35;">{a}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Cierre de la card contenedora
    st.markdown("</div>", unsafe_allow_html=True)



def render_arbol_reglas(icv_hi, mora_hi, recup_low):
    import streamlit as st

    st.markdown("""
        <style>
        .dashboard-card {
            border-radius: 16px;
            padding: 20px;
            background: #f9fdfb;
            border: 1px solid #e0f2f1;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        }
        .risk-label {
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
        }
        .low-risk {
            background-color: #d1fae5;
            color: #065f46;
        }
        .mod-risk {
            background-color: #fef9c3;
            color: #92400e;
        }
        .high-risk {
            background-color: #fee2e2;
            color: #991b1b;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### ⚖️ Árbol predictor (reglas de negocio)")
    st.caption("Secuencia sugerida para leer el riesgo del segmento filtrado.")

    with st.container():
        

        # Calidad de venta
        st.markdown("#### 📊 Calidad de la venta (ICV)")
        col1, col2 = st.columns([1, 3])
        col1.markdown("ICV ≤")
        col2.markdown(f"`{icv_hi:.2f}` → <span class='risk-label low-risk'>riesgo bajo</span>", unsafe_allow_html=True)
        col1.markdown("ICV >")
        col2.markdown(f"`{icv_hi:.2f}` → revisar **Mora**")

        st.markdown("---")

        # Mora temprana
        st.markdown("#### ⏱️ Mora temprana")
        col1, col2 = st.columns([1, 3])
        col1.markdown("Mora ≤")
        col2.markdown(f"`{fmt_percent(mora_hi)}` → <span class='risk-label mod-risk'>riesgo moderado</span>", unsafe_allow_html=True)
        col1.markdown("Mora >")
        col2.markdown(f"`{fmt_percent(mora_hi)}` → <span class='risk-label high-risk'>riesgo alto</span>", unsafe_allow_html=True)

        st.markdown("---")

        # Recuperación
        st.markdown("#### 💸 Recuperación")
        col1, col2 = st.columns([1, 3])
        col1.markdown("Recup <")
        col2.markdown(f"`{fmt_percent(recup_low)}` → <span class='risk-label high-risk'>alerta crítica</span> con prioridad máxima", unsafe_allow_html=True)






def render_recomendaciones(df):
    st.markdown("### Recomendaciones operativas")

    # Sucursales con mayor riesgo
    top_risk = df.sort_values("Risk_Score", ascending=False).head(2)[COL_SUCURSAL].tolist()
    suc1 = top_risk[0] if len(top_risk) > 0 else "Sucursal de mayor riesgo"
    suc2 = top_risk[1] if len(top_risk) > 1 else "Siguiente sucursal en riesgo"

    # Recomendaciones visuales
    st.markdown("""
    <div style='line-height: 1.7; font-size: 19px;'>
        <ul style="list-style-type: '✅ '; padding-left: 1.2em;">
            <li>Priorizar auditoría integral en <b>{suc1}</b> y <b>{suc2}</b>, revisando <code>FPD</code>, <code>Mora temprana</code> y <code>Recuperación</code>.</li>
            <li>Plan intensivo de <b>cobranza</b> en sucursales con <span style="color:#b91c1c;"><b>Mora alta</b></span> y <span style="color:#b91c1c;"><b>Recuperación baja</b></span>.</li>
            <li>⚙️ Ajustar <b>reglas de originación</b> donde <code>FPD</code> supere el promedio de la red.</li>
            <li>📘 Documentar y replicar prácticas de <b>sucursales con buen ICV</b> y <b>baja Mora</b>.</li>
        </ul>
    </div>
    """.format(suc1=suc1, suc2=suc2), unsafe_allow_html=True)


def resumen_ejecutivo_story(total_coloc, avg_icv, avg_mora, avg_recup, avg_risk, num_suc):
    nivel, texto = get_risk_level(avg_risk)

    st.markdown(
        f"""
        <div style="
            border-radius: 999px;
            padding: 10px 18px;
            background: linear-gradient(90deg,#ecfdf5,#fefce8);
            border: 1px solid rgba(16,185,129,0.25);
            display:flex;
            align-items:center;
            gap:14px;
            font-size:16px;
            color:#374151;
        ">
            <div style="
                width:26px;height:26px;border-radius:999px;
                background:radial-gradient(circle at 30% 0%, #bbf7d0, #22c55e);
                display:flex;align-items:center;justify-content:center;
                color:white;font-weight:800;font-size:15px;
            ">
                i
            </div>
            <div style="flex:1;">
                <span style="font-weight:600;color:#022c22;">
                    {num_suc} sucursales · riesgo {nivel} · colocación {fmt_currency(total_coloc)}
                </span>
                <br>
                <span style="color:#4b5563;">{texto}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------------------------------------------------------
# HEADER (sticky) con animaciones suaves y barra de salud
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# HEADER (sticky) minimalista con barra de salud
# -------------------------------------------------------------------
def render_header(avg_health: float):
    with st.container():
        st.markdown("<div class='dimex-header'>", unsafe_allow_html=True)

        # 3 columnas: logo | título | chip de salud
        col_logo, col_title, col_health = st.columns([1, 5, 3])

        # Columna 1: Logo DIMEX o fallback
        with col_logo:
            logo_path = Path("dimex_logo.png")
            if logo_path.exists():
                st.image(str(logo_path), use_container_width=True)
            else:
                st.markdown(
                    """
                    <div style="
                        width:20px;height:100px;border-radius:10px;
                        background:#05966910;
                        display:flex;align-items:center;justify-content:center;
                        border:1px solid rgba(5,150,105,0.25);
                    ">
                        <span style="color:#059669;font-weight:700;font-size:20px;">D</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Columna 2: Título + subtítulo (sin tanta decoración)
        with col_title:
            st.markdown(
                """
                <div style="padding:4px 0;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <h1 style="
                            margin:0;
                            font-size:40px;
                            font-weight:800;
                            letter-spacing:-0.03em;
                            color:#020617;
                        ">
                            Salud y Riesgo de Sucursales
                        </h1>
                    </div>
                    <p style="
                        margin:2px 0 0 0;
                        font-size:16px;
                        color:#6B7280;
                    ">
                        Dirección de Cobranza · Cartera de jubilados y pensionados
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Columna 3: Chip de índice de salud (flat, pill)
        with col_health:
            st.markdown(
                f"""
                <div style="
                    margin-top:6px;
                    display:flex;
                    justify-content:flex-end;
                ">
                    <div style="
                        display:flex;align-items:center;gap:10px;
                        padding:8px 14px;
                        border-radius:999px;
                        border:1px solid rgba(22,163,74,0.18);
                        background:rgba(240,253,244,0.9);
                        --health-width:{avg_health:.1f}%;
                    ">
                        <span style="font-size:14px;color:#047857;font-weight:600;">
                            Índice de salud
                        </span>
                        <div class="health-bar" style="width:140px;">
                            <span></span>
                        </div>
                        <span style="
                            font-size:22px;
                            font-weight:700;
                            color:#059669;
                            min-width:64px;
                            text-align:right;
                        ">
                            {avg_health:.1f}
                            <span style="font-size:20px;color:#9CA3AF;">/ 100</span>
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='top-spacer'></div>", unsafe_allow_html=True)

    # (Opcional: sin lottie para que sea todavía más limpio)
    # Si quieres dejar el pulso, quita este comentario:
    # if LOTTI_AVAILABLE:
    #     st_lottie(...)
# -------------------------------------------------------------------
# LAYOUT PRINCIPAL (controles, KPIs, gráficos, tabs, FABs)
# -------------------------------------------------------------------
def main():
    # Estado inicial de filtros si no existen aún en la sesión
    if "filters" not in st.session_state:
        st.session_state["filters"] = {"cluster": "Todos", "sucursal": "Todas"}
    if "quick" not in st.session_state:
        st.session_state["quick"] = {"alto_riesgo": False, "mora_alta": False, "recup_baja": False, "umbral_riesgo": 70}

    # Atajos locales a los dicts de estado
    filters = st.session_state["filters"]
    quick   = st.session_state["quick"]

    # Umbrales automáticos a partir del histórico completo (p75/p25)
    icv_hi    = df_full[COL_ICV].quantile(0.75)
    mora_hi   = df_full[COL_MORA].quantile(0.75)
    recup_low = df_full[COL_RECUP].quantile(0.25)

    # HEADER sticky con barra de salud promedio
    avg_health = df_full["Health_Index"].mean()
    render_header(avg_health)

    # ---- FILTROS SUPERIORES -------------------------------------------------
    col_f1, col_f2, col_f3, col_f4 = st.columns([2.2, 2.2, 2.2, 3.4])
    with col_f1:
        filters["cluster"] = st.selectbox("Cluster", ["Todos"] + sorted(df_full[COL_CLUSTER].unique().tolist()))
    with col_f2:
        filters["sucursal"] = st.selectbox("Sucursal", ["Todas"] + sorted(df_full[COL_SUCURSAL].unique().tolist()))
    with col_f3:
        quick["alto_riesgo"] = st.checkbox("Filtrar alto riesgo", value=quick["alto_riesgo"])
        quick["umbral_riesgo"] = st.slider("Umbral score riesgo", 0, 100, quick["umbral_riesgo"], step=5, label_visibility="collapsed")
    with col_f4:
        c_q1, c_q2 = st.columns(2)
        with c_q1:
            quick["mora_alta"] = st.checkbox("Mora alta", value=quick["mora_alta"])
        with c_q2:
            quick["recup_baja"] = st.checkbox("Recuperación baja", value=quick["recup_baja"])

    # Aplica filtros a la base completa
    df_filtered = apply_filters(df_full, filters, quick)
    if df_filtered.empty:
        st.warning("No hay datos para los filtros seleccionados.")   # Aviso si no hay datos
        return

    # Separador visual
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ---- KPIs PRINCIPALES ---------------------------------------------------
    total_coloc = df_filtered[COL_COLOCACION].sum()
    avg_icv     = df_filtered[COL_ICV].mean()
    avg_mora    = df_filtered[COL_MORA].mean()
    avg_fpd     = df_filtered[COL_FPD].mean()
    avg_recup   = df_filtered[COL_RECUP].mean()
    avg_risk    = df_filtered["Risk_Score"].mean()
    num_suc     = len(df_filtered)
    margen_neto = df_filtered[COL_MARGEN_NETO].sum()

    row1 = st.columns(4)                                   # 4 KPIs en una fila
    with row1[0]:
        kpi_card("Sucursales activas", f"{num_suc}", "Sucursales filtradas", COLOR_PRIMARY_DARK)
    with row1[1]:
        kpi_card("Colocación total", fmt_currency(total_coloc), "Promedio mensual", COLOR_PRIMARY)
    with row1[2]:
        kpi_card("Margen financiero neto total", fmt_currency(margen_neto), "Contribución cartera filtrada", COLOR_SUCCESS)
    with row1[3]:
        kpi_card("%FPD promedio", fmt_percent(avg_fpd), "Incumplimiento primer pago", COLOR_WARN)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ---- STORYTELLING EJECUTIVO --------------------------------------------
    card_container(True)
    resumen_ejecutivo_story(total_coloc, avg_icv, avg_mora, avg_recup, avg_risk, num_suc)
    card_container(False)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)


    # ---- Fila central: Mapa · Ranking · Gauge/Alertas/Acciones --------------
    gcol1, gcol2, gcol3 = st.columns(3)

    # Columna izquierda: Mapa de burbujas
        # Fila central: Mapa · Ranking · Gauge
    # ------------------------------------
    gcol1, gcol2, gcol3 = st.columns([1, 1, 1])  # columnas del mismo ancho

    # Columna 1: Mapa
    with gcol1:
        card_container(True)
        st.markdown(
                """
            <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:4px 10px;
                    border-radius:8px;
                    font-size:20px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                    Mapa de Sucursales Burbujas por Riesgo
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )



        metric_options = {
            "Colocación promedio mensual": {"col": COL_COLOCACION, "label": "Colocación promedio mensual (MXN)"},
            "Mora temprana": {"col": COL_MORA, "label": "Mora temprana (proporción)"},
            "Recuperación": {"col": COL_RECUP, "label": "Tasa de recuperación (proporción)"},
            "%FPD": {"col": COL_FPD, "label": "%FPD"},
            "Saldo insoluto": {"col": COL_SALDO, "label": "Saldo insoluto (MXN)"},
        }
        c_axis1, c_axis2 = st.columns(2)
        with c_axis1:
            x_key = st.selectbox("Eje X", list(metric_options.keys()), index=0, key="bubble_x")
        with c_axis2:
            y_key = st.selectbox("Eje Y", list(metric_options.keys()), index=1, key="bubble_y")
        size_key = "Saldo insoluto"
        bubble_risk_map(
            df_filtered,
            metric_options[x_key],
            metric_options[y_key],
            metric_options[size_key],
        )
        card_container(False)

    # Columna 2: Ranking
    with gcol2:
        card_container(True)
        st.markdown(
                """
            
                
             <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:4px 10px;
                    border-radius:8px;
                    font-size:20px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                    Ranking de Sucursales en Riesgo
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        c_r1, c_r2 = st.columns(2)
        with c_r1:
            min_risk = st.slider("Score mínimo", 0, 100, 70, step=5, key="rank_min_risk")
        with c_r2:
            top_n = st.slider("N sucursales", 5, 30, 10, step=1, key="rank_top_n")
        ranking_barras(df_filtered, min_risk, top_n)
        card_container(False)

    # Columna 3: SOLO gauge + texto corto
    with gcol3:
        card_container(True)
        st.markdown(
                """
            <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:4px 10px;
                    border-radius:8px;
                    font-size:20px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                   Score de Riesgo Cartera Filtrada
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        risk_gauge(avg_risk)
        st.markdown(
            """
            <div style="font-size:12px;color:#64748B;background:rgba(254,249,195,0.9);
                        padding:6px;border-radius:8px;margin-top:4px;">
                Ayuda a dimensionar qué tan concentrada está la cartera en sucursales de alto riesgo y 
                dónde debe enfocarse la Dirección de Cobranza.
            </div>
            """,
            unsafe_allow_html=True
        )
        card_container(False)

    # ------------------------------------
    # Fila debajo: Alertas + Acciones rápidas
    # ------------------------------------
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    card_container(True)
    a_col1, a_col_sp, a_col2 = st.columns([1, 0.06, 1])
  # alertas más ancho que acciones

    with a_col1:
    
        render_alertas(df_filtered, mora_hi, recup_low)

    with a_col2:
       
        quick_actions(df_filtered)

    card_container(False)


    # ---- TABS ANALÍTICOS (en dock flotante debajo del header) ---------------
    dock = st.container()                                       # Contenedor para aplicar sombra/fondo
    with dock:
        st.markdown("<div class='tabs-dock'>", unsafe_allow_html=True)  # Caja flotante
        tab1, tab2, tab3 = st.tabs(["📈 Riesgo & rentabilidad", "🧠 Explicación de riesgo", "📋 Detalle por sucursal"])
        st.markdown("</div>", unsafe_allow_html=True)           # Cierra dock

    # --- Contenido de cada tab -----------------------------------------------
    with tab1:
        card_container(True)
        st.markdown(
                """
            <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:4px 10px;
                    border-radius:8px;
                    font-size:20px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                    Perfil de cartera por riesgo y rentabilidad
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        ac1, ac2 = st.columns([2, 1])
        with ac1:
            perfil_kpis_por_decil(df_filtered)
        with ac2:
            margen_por_cluster(df_filtered)
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown(
                """
            <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:4px 10px;
                    border-radius:8px;
                    font-size:20px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                    Mapa riesgo–rentabilidad por sucursal
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        mapa_riesgo_rentabilidad(df_filtered)
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown(
                """
            <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:4px 10px;
                    border-radius:8px;
                    font-size:20px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                    Radar de riesgo por KPI
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        radar_riesgo_multifactor(df_filtered)
        card_container(False)

    with tab2:
        st.markdown(
                """
            <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:4px 10px;
                    border-radius:8px;
                    font-size:30px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                    Narrativa de Riesgo
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # === Árbol predictor y recomendaciones paralelas ===
        col1, col2 = st.columns([1.2, 1])

        with col1:
            card_container(True)
            
            render_arbol_reglas(icv_hi, mora_hi, recup_low)
            card_container(False)

        with col2:
            card_container(True)
           
            render_recomendaciones(df_filtered)
            card_container(False)

        # === LÍNEA SEPARADORA ELEGANTE ===
        st.markdown("<hr style='margin-top:30px;margin-bottom:20px;border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        # === Gráfico de drivers ===
        card_container(True)
        drivers_riesgo(df_filtered)
        card_container(False)

    with tab3:
        st.markdown("### 📋 Detalle por sucursal")
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # --- SELECTBOX correcto (usa df_full, no df)
        sucursal = st.selectbox(
            "Selecciona una sucursal",
            sorted(df_full[COL_SUCURSAL].unique()),
            key="tab3_suc"
        )

        # Extrae los registros de esa sucursal
        df_suc = df_full[df_full[COL_SUCURSAL] == sucursal]

        if df_suc.empty:
            st.warning("No hay datos para esta sucursal.")
        else:
            # CARD contenedor
            card_container(True)

            st.markdown(
                f"""
                <h4 style='margin-bottom:4px;color:#064e3b;font-weight:700;'>{sucursal}</h4>
                <p style='color:#64748b;font-size:13px;margin-top:-6px;'>
                    Información completa de métricas, riesgo, colocación y desempeño operativo.
                </p>
                """,
                unsafe_allow_html=True,
            )

            # === KPIs individuales por sucursal ===
            sc1, sc2, sc3, sc4 = st.columns(4)
            row = df_suc.iloc[0]

            with sc1:
                kpi_card("Score de riesgo", f"{row['Risk_Score']:.1f}", "0–100", COLOR_RISK)
            with sc2:
                kpi_card("Mora temprana", fmt_percent(row[COL_MORA]), "Último corte", COLOR_WARN)
            with sc3:
                kpi_card("Recuperación", fmt_percent(row[COL_RECUP]), "Efectividad", COLOR_SUCCESS)
            with sc4:
                kpi_card("Colocación mensual", fmt_currency(row[COL_COLOCACION]), "Promedio", COLOR_PRIMARY)

            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

            # === TABLA COMPLETA DETALLADA ===        
            st.markdown("#### Tabla detallada de KPIs")
            tabla_detalle(df_suc)

            card_container(False)


        # ================================================================
    # DIMI · Chatbot de riesgo (sección fija al final del dashboard)
    # ================================================================
    st.markdown("---")
    st.markdown("<div id='dimi_chat'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; gap:12px; margin-top:6px; margin-bottom:12px;'>
            <img src="data:image/png;base64,{avatar}" width="120"
                style="border-radius:120%; border:2px solid #e2e8f0;" />
            <h2 style='margin:0; font-weight:800; letter-spacing:-0.02em; color:#0f172a;'>
                DIMI · Analista virtual de riesgo
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.caption(
        "Hazle preguntas sobre la cartera filtrada: sucursales críticas, escenarios, "
        "regresiones, explicaciones para comité, etc."
    )

    # Historial en formato chat
    for msg in st.session_state["dimi_history"]:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg["content"])

    # Entrada de usuario (estilo chat)
    user_msg = st.chat_input("Escribe tu pregunta para DIMI:")

    if user_msg:
        with st.spinner("DIMI está analizando el segmento filtrado..."):
            _ = dimi_answer(user_msg, df_filtered)
        st.rerun()



    # ----------------------------------------------------------------
    # FABs flotantes (ir arriba y descargar CSV del filtro actual)
    # ----------------------------------------------------------------



    # Botón de reset real (usa widget nativo para poder hacer rerun)
    reset_col = st.columns([10,1,1])[1]                               # Columna pequeña hacia la derecha
                                                  # Recarga la app

# Punto de entrada del script
if __name__ == "__main__":
    main()
