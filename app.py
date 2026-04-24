“””
R9 Central — интерфейс управления C_2 (HF Space node)
Архитектура: R23. Версия: v3.1 (исправленная).

Изменения против v3.0:

- Убран @import url(googleapis) из CSS — причина “Importing a module script failed”
- Форма упрощена: одна submit-кнопка, без st.columns внутри формы
- Pending-паттерн для изменения значения text_area (вместо прямой мутации
  session_state ключа виджета — это бросало StreamlitAPIException)
- Fallback для st.rerun() (совместимость <1.30)
- Простой page_icon
- Кнопки Clear/Повторить/Показать — все вне формы
  “””

import streamlit as st
import requests
import os
import time
import json
from datetime import datetime

# ============== КОНФИГУРАЦИЯ ==============

C2_URL = os.environ.get(“C2_URL”, “https://rollannf-r9-c-2.hf.space”)
HF_TOKEN = os.environ.get(“HF_TOKEN”, “”)
HEADERS = {“Authorization”: f”Bearer {HF_TOKEN}”} if HF_TOKEN else {}
DEFAULT_TIMEOUT = 30

st.set_page_config(
page_title=“R9 Central”,
page_icon=“🛰”,
layout=“centered”,
initial_sidebar_state=“collapsed”,
)

# ============== FALLBACK ДЛЯ st.rerun (совместимость) ==============

def rerun():
if hasattr(st, “rerun”):
st.rerun()
else:
st.experimental_rerun()

# ============== SESSION STATE ==============

def init_state():
defaults = {
“history”: [],
“last_response”: None,
“last_status”: None,
“last_elapsed_ms”: None,
“last_error”: None,
“last_is_json”: True,
“system_log”: [],
“health_ok”: None,
“input_value”: “”,            # хранилище значения text_area (управляется нами)
“pending_input”: None,        # pending-паттерн для перезаписи input_value
“endpoint”: “/request”,
“method”: “POST”,
“timeout”: DEFAULT_TIMEOUT,
“payload_key”: “query”,
}
for k, v in defaults.items():
if k not in st.session_state:
st.session_state[k] = v

init_state()

# Pending-паттерн: применяем изменение ДО рендера виджета

if st.session_state.pending_input is not None:
st.session_state.input_value = st.session_state.pending_input
st.session_state.pending_input = None

# ============== CSS — БЕЗ ВНЕШНИХ ИМПОРТОВ ==============

st.markdown(”””

<style>
/* Системные шрифты — никаких внешних @import (причина Importing module failed) */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 50%, #f0f4f8 100%);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
}
.stApp::before {
    content: ''; position: fixed; inset: 0;
    background-image: radial-gradient(circle at 1px 1px, rgba(0,150,255,0.07) 1px, transparent 0);
    background-size: 36px 36px;
    pointer-events: none; z-index: 0;
}
.orb { position: fixed; border-radius: 50%; filter: blur(80px); opacity: 0.4;
       pointer-events: none; z-index: 0; }
.orb-1 { width: 360px; height: 360px; background: rgba(0,122,255,0.15);
         top: -100px; right: -80px; }
.orb-2 { width: 280px; height: 280px; background: rgba(88,86,214,0.10);
         bottom: -50px; left: -50px; }

h1, h2, h3 { color: #1a1a2e !important; font-weight: 500 !important; letter-spacing: -0.3px; }

/* Компактные кнопки */
.stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: rgba(255,255,255,0.78) !important;
    -webkit-backdrop-filter: blur(14px) saturate(160%);
    backdrop-filter: blur(14px) saturate(160%);
    border: 1px solid rgba(0,122,255,0.2) !important;
    color: #007aff !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border-radius: 10px !important;
    padding: 6px 14px !important;
    min-height: 34px !important;
    line-height: 1.2 !important;
    box-shadow: 0 2px 8px rgba(0,122,255,0.08),
                inset 0 1px 0 rgba(255,255,255,0.6);
    transition: all 0.2s ease;
    width: 100%;
}
.stButton > button:hover, .stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background: rgba(255,255,255,0.98) !important;
    border-color: rgba(0,122,255,0.45) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0,122,255,0.18);
}
.stButton > button:active { transform: translateY(0) scale(0.98); }

/* Primary submit — градиент */
div[data-testid="stFormSubmitButton"] > button[kind="primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #007aff 0%, #5856d6 100%) !important;
    color: #fff !important;
    border: 1px solid rgba(0,122,255,0.5) !important;
    box-shadow: 0 4px 14px rgba(0,122,255,0.35);
}

/* Поля ввода */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.75) !important;
    -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px);
    border: 1px solid rgba(0,122,255,0.15) !important;
    color: #1a1a2e !important; font-size: 14px !important;
    border-radius: 10px !important;
}
.stTextInput > div > div > input { padding: 10px 14px !important; }
.stTextArea > div > div > textarea { padding: 12px 14px !important; min-height: 80px; }
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    background: rgba(255,255,255,0.97) !important;
    border-color: rgba(0,122,255,0.5) !important;
    box-shadow: 0 0 0 3px rgba(0,122,255,0.1) !important;
    outline: none !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
    color: rgba(0,0,0,0.6) !important;
    font-size: 12px !important; font-weight: 500 !important;
    text-transform: uppercase; letter-spacing: 0.8px;
}

/* Code block — встроенная копирка Streamlit в правом верхнем углу */
.stCodeBlock, pre, code {
    background: rgba(26,26,46,0.95) !important;
    border: 1px solid rgba(0,122,255,0.2) !important;
    border-radius: 12px !important;
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace !important;
    font-size: 12.5px !important;
}
.stCodeBlock pre { max-height: 460px; overflow-y: auto; }

/* JSON tree */
.stJson {
    background: rgba(255,255,255,0.6) !important;
    border: 1px solid rgba(0,122,255,0.15) !important;
    border-radius: 12px !important; padding: 14px !important;
    max-height: 460px; overflow-y: auto;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: rgba(255,255,255,0.5);
    padding: 4px; border-radius: 10px;
}
.stTabs [data-baseweb="tab"] {
    padding: 6px 12px !important; height: 32px !important;
    background: transparent !important; border-radius: 7px !important;
    font-size: 13px !important; font-weight: 500 !important;
    color: rgba(0,0,0,0.6) !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,255,255,0.95) !important; color: #007aff !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

/* Expander */
.streamlit-expanderHeader, details > summary {
    background: rgba(255,255,255,0.5) !important;
    border-radius: 10px !important; font-size: 13px !important;
    font-weight: 500 !important; padding: 8px 14px !important;
}

/* Alerts */
.stAlert { border-radius: 10px !important; font-size: 13px !important;
           padding: 10px 14px !important; }

/* Скроллбар */
::-webkit-scrollbar { width: 6px; height: 6px; background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,122,255,0.3); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,122,255,0.5); }

/* Контейнер */
.block-container { padding-top: 2rem !important; padding-bottom: 5rem !important;
                   max-width: 760px !important; }

/* Glass card (только для декоративных HTML-блоков) */
.glass-card {
    background: rgba(255,255,255,0.55);
    -webkit-backdrop-filter: blur(20px); backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.6); border-radius: 14px;
    padding: 10px 14px; margin: 10px 0;
    box-shadow: 0 4px 18px rgba(0,0,0,0.05), inset 0 1px 0 rgba(255,255,255,0.8);
}
.section-label {
    color: rgba(0,122,255,0.8);
    font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 2px;
    margin: 18px 0 6px 0;
    font-family: ui-monospace, monospace;
}
.status-row {
    display: flex; align-items: center; gap: 10px;
    font-family: ui-monospace, monospace; font-size: 12.5px;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-dot.ok   { background: #34c759; box-shadow: 0 0 0 3px rgba(52,199,89,0.2); }
.status-dot.err  { background: #ff3b30; box-shadow: 0 0 0 3px rgba(255,59,48,0.2); }
.status-dot.idle { background: #8e8e93; box-shadow: 0 0 0 3px rgba(142,142,147,0.2); }
@keyframes pulse { 0%,100% {opacity:1;} 50% {opacity:0.5;} }
.status-dot.ok, .status-dot.err { animation: pulse 2.4s ease-in-out infinite; }

.metrics-row { display: flex; gap: 8px; flex-wrap: wrap;
               font-family: ui-monospace, monospace; font-size: 11.5px;
               color: rgba(0,0,0,0.55); margin: 6px 0; }
.metric-chip { background: rgba(255,255,255,0.65);
               border: 1px solid rgba(0,122,255,0.15);
               padding: 3px 10px; border-radius: 6px; }
.metric-chip b { color: #007aff; font-weight: 600; }

.glass-footer {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: rgba(255,255,255,0.75);
    -webkit-backdrop-filter: blur(16px); backdrop-filter: blur(16px);
    border-top: 1px solid rgba(255,255,255,0.8);
    padding: 8px 20px; text-align: center; z-index: 100;
    font-family: ui-monospace, monospace;
    color: rgba(0,0,0,0.5); font-size: 11px; letter-spacing: 1px;
}

[data-testid="InputInstructions"] { display: none !important; }
[data-testid="stForm"] { border: none !important; padding: 0 !important; }
</style>

<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
""", unsafe_allow_html=True)

# ============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==============

def log(msg: str, level: str = “info”):
ts = datetime.now().strftime(”%H:%M:%S”)
st.session_state.system_log.append({“ts”: ts, “level”: level, “msg”: msg})
if len(st.session_state.system_log) > 50:
st.session_state.system_log = st.session_state.system_log[-50:]

def ping_health(timeout: int = 8):
t0 = time.perf_counter()
try:
r = requests.get(f”{C2_URL}/health”, headers=HEADERS, timeout=timeout)
elapsed = (time.perf_counter() - t0) * 1000
try:
payload = r.json()
except ValueError:
payload = {“raw_text”: r.text[:500]}
return r.ok, payload, elapsed, None
except requests.exceptions.Timeout:
return False, None, (time.perf_counter() - t0) * 1000, “Таймаут соединения”
except requests.exceptions.ConnectionError:
return False, None, (time.perf_counter() - t0) * 1000, “Нет соединения”
except Exception as e:
return False, None, (time.perf_counter() - t0) * 1000, f”{type(e).**name**}: {e}”

def send_request(endpoint: str, method: str, payload: dict, timeout: int):
url = f”{C2_URL}{endpoint}”
t0 = time.perf_counter()
try:
if method == “GET”:
r = requests.get(url, headers=HEADERS, params=payload, timeout=timeout)
else:
r = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
elapsed = (time.perf_counter() - t0) * 1000
try:
data = r.json()
is_json = True
except ValueError:
data = r.text
is_json = False
return {“ok”: r.ok, “status_code”: r.status_code, “elapsed_ms”: elapsed,
“data”: data, “is_json”: is_json, “size_bytes”: len(r.content),
“error”: None}
except requests.exceptions.Timeout:
return {“ok”: False, “status_code”: None,
“elapsed_ms”: (time.perf_counter() - t0) * 1000,
“data”: None, “is_json”: False, “size_bytes”: 0,
“error”: “Таймаут запроса”}
except requests.exceptions.ConnectionError:
return {“ok”: False, “status_code”: None,
“elapsed_ms”: (time.perf_counter() - t0) * 1000,
“data”: None, “is_json”: False, “size_bytes”: 0,
“error”: “Нет соединения”}
except Exception as e:
return {“ok”: False, “status_code”: None,
“elapsed_ms”: (time.perf_counter() - t0) * 1000,
“data”: None, “is_json”: False, “size_bytes”: 0,
“error”: f”{type(e).**name**}: {e}”}

def format_bytes(n: int) -> str:
n = float(n)
for unit in [“Б”, “КБ”, “МБ”]:
if n < 1024:
return f”{n:.0f} {unit}” if unit == “Б” else f”{n:.1f} {unit}”
n /= 1024
return f”{n:.1f} ГБ”

def set_input_pending(value: str):
“”“Безопасная запись в input_value — через pending, применится на следующий ран.”””
st.session_state.pending_input = value

# ============== ХЕДЕР ==============

st.markdown(”””

<div style="text-align:center; margin: 1.2rem 0 1.6rem 0; position: relative; z-index: 1;">
    <div style="color: rgba(0,122,255,0.6); font-size: 11px;
         font-family: ui-monospace, monospace;
         letter-spacing: 3px; margin-bottom: 8px; text-transform: uppercase;">
        Системный интерфейс · v3.1
    </div>
    <h1 style="font-size: 30px; font-weight: 600; color: #1a1a2e;
         margin: 0; letter-spacing: -1px;">◈ R9 Central</h1>
    <div style="color: rgba(0,0,0,0.5); font-size: 13px; margin-top: 6px;">
        Канал связи с узлом C_2 · защищённый
    </div>
</div>
""", unsafe_allow_html=True)

if not HF_TOKEN:
st.warning(“HF_TOKEN не установлен. Защищённые endpoint’ы вернут 401/403.”,
icon=“⚠”)

# ============== СТАТУС C_2 ==============

dot_class, status_text = “idle”, “Статус не определён — нажмите «Пинг»”
if st.session_state.health_ok is True:
dot_class, status_text = “ok”, f”C_2 онлайн · {C2_URL.split(’//’)[-1]}”
elif st.session_state.health_ok is False:
dot_class, status_text = “err”, f”C_2 недоступен · {C2_URL.split(’//’)[-1]}”

c1, c2, c3 = st.columns([3, 1, 1])
with c1:
st.markdown(f”””
<div class="glass-card" style="padding: 10px 14px;">
<div class="status-row">
<div class="status-dot {dot_class}"></div>
<span>{status_text}</span>
</div>
</div>
“””, unsafe_allow_html=True)
with c2:
if st.button(“🛰 Пинг”, key=“btn_ping”):
with st.spinner(“Проверка…”):
ok, payload, elapsed, err = ping_health()
st.session_state.health_ok = ok
if ok:
log(f”Health OK · {elapsed:.0f} мс · {payload}”, “ok”)
else:
log(f”Health FAIL · {err or ‘non-2xx’}”, “err”)
rerun()
with c3:
if st.button(“⟲ Сброс”, key=“btn_reset”, help=“Очистить историю и лог”):
st.session_state.history = []
st.session_state.system_log = []
st.session_state.last_response = None
st.session_state.last_error = None
log(“Состояние очищено”, “info”)
rerun()

# ============== ПАРАМЕТРЫ ==============

st.markdown(’<div class="section-label">◉ Передача команды</div>’, unsafe_allow_html=True)

with st.expander(“⚙ Параметры запроса”, expanded=False):
ca, cb, cc = st.columns([2, 1, 1])
with ca:
st.session_state.endpoint = st.text_input(
“Endpoint”, value=st.session_state.endpoint,
help=“Путь на C_2: /request, /health, /status, …”
)
with cb:
st.session_state.method = st.selectbox(
“Метод”, [“POST”, “GET”],
index=0 if st.session_state.method == “POST” else 1,
)
with cc:
st.session_state.timeout = st.number_input(
“Таймаут (с)”, min_value=1, max_value=300,
value=int(st.session_state.timeout), step=1,
)
st.session_state.payload_key = st.text_input(
“Имя поля payload”, value=st.session_state.payload_key,
help=“Под каким ключом передать ввод (для POST — в теле JSON; для GET — в query-string)”
)

# ============== ФОРМА (одна submit-кнопка, без st.columns внутри) ==============

with st.form(key=“request_form”, clear_on_submit=False):
user_input = st.text_area(
“Команда для C_2”,
value=st.session_state.input_value,
key=“input_widget”,
placeholder=“Введите запрос…\nCtrl+Enter — отправить”,
height=100,
)
submitted = st.form_submit_button(“▶ Отправить”, type=“primary”,
use_container_width=True)

# После рендера формы сохраняем текущее значение виджета (если пользователь печатал)

if “input_widget” in st.session_state:
st.session_state.input_value = st.session_state.input_widget

# ============== КНОПКИ ВНЕ ФОРМЫ ==============

ac1, ac2, ac3 = st.columns([1, 1, 3])
with ac1:
if st.button(“⌫ Очистить”, key=“btn_clear”):
set_input_pending(””)
rerun()
with ac2:
if st.button(“📋 Копия”, key=“btn_copy_input”,
help=“Показать ввод блоком для копирования”):
if st.session_state.input_value:
st.code(st.session_state.input_value, language=“text”)

# ============== ОБРАБОТКА ОТПРАВКИ ==============

if submitted:
input_text = st.session_state.input_value
method = st.session_state.method
endpoint = st.session_state.endpoint
payload_key = st.session_state.payload_key
timeout = int(st.session_state.timeout)

```
if not input_text.strip() and method == "POST":
    log("Пустой ввод — отмена", "warn")
    st.warning("Введите команду перед отправкой")
else:
    log(f"→ {method} {endpoint}", "info")
    with st.spinner(f"Отправка {method} {endpoint}..."):
        payload = {payload_key: input_text} if input_text else {}
        result = send_request(endpoint, method, payload, timeout)

    st.session_state.last_response = result["data"]
    st.session_state.last_status = result["status_code"]
    st.session_state.last_elapsed_ms = result["elapsed_ms"]
    st.session_state.last_error = result["error"]
    st.session_state.last_is_json = result["is_json"]

    if result["error"]:
        log(f"✗ {result['error']}", "err")
    elif result["ok"]:
        log(f"✓ {result['status_code']} · {result['elapsed_ms']:.0f} мс · "
            f"{format_bytes(result['size_bytes'])}", "ok")
    else:
        log(f"✗ HTTP {result['status_code']} · {result['elapsed_ms']:.0f} мс", "err")

    st.session_state.history.insert(0, {
        "ts": datetime.now().strftime("%H:%M:%S"),
        "method": method,
        "endpoint": endpoint,
        "input": input_text,
        "status": result["status_code"],
        "elapsed_ms": result["elapsed_ms"],
        "ok": result["ok"],
        "is_json": result["is_json"],
        "response": result["data"] if result["is_json"]
                   else {"text": str(result["data"])[:500]},
    })
    st.session_state.history = st.session_state.history[:20]
```

# ============== ОТВЕТ ==============

if st.session_state.last_response is not None or st.session_state.last_error:
st.markdown(’<div class="section-label">◉ Ответ C_2</div>’,
unsafe_allow_html=True)

```
status = st.session_state.last_status
elapsed = st.session_state.last_elapsed_ms
err = st.session_state.last_error

metrics = '<div class="metrics-row">'
if status is not None:
    metrics += f'<span class="metric-chip">HTTP <b>{status}</b></span>'
if elapsed is not None:
    metrics += f'<span class="metric-chip">Время <b>{elapsed:.0f} мс</b></span>'
if st.session_state.last_response is not None:
    try:
        size = len(json.dumps(st.session_state.last_response,
                              ensure_ascii=False, default=str).encode("utf-8"))
        metrics += f'<span class="metric-chip">Размер <b>{format_bytes(size)}</b></span>'
    except (TypeError, ValueError):
        pass
metrics += '</div>'
st.markdown(metrics, unsafe_allow_html=True)

if err:
    st.error(f"Ошибка: {err}")

if st.session_state.last_response is not None:
    try:
        pretty_json = json.dumps(st.session_state.last_response,
                                 ensure_ascii=False, indent=2, default=str)
        compact_json = json.dumps(st.session_state.last_response,
                                  ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        pretty_json = str(st.session_state.last_response)
        compact_json = str(st.session_state.last_response)

    tab1, tab2, tab3 = st.tabs(["📋 JSON копируемый", "🌳 Дерево", "📝 Компактный"])

    with tab1:
        # У st.code есть встроенная кнопка копирования (правый верх)
        st.code(pretty_json, language="json")
        dc1, dc2 = st.columns(2)
        ts_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        with dc1:
            st.download_button("⬇ JSON", data=pretty_json,
                               file_name=f"c2_response_{ts_now}.json",
                               mime="application/json",
                               use_container_width=True,
                               key=f"dl_json_{ts_now}")
        with dc2:
            st.download_button("⬇ TXT", data=pretty_json,
                               file_name=f"c2_response_{ts_now}.txt",
                               mime="text/plain",
                               use_container_width=True,
                               key=f"dl_txt_{ts_now}")

    with tab2:
        if isinstance(st.session_state.last_response, (dict, list)):
            st.json(st.session_state.last_response, expanded=True)
        else:
            st.text(str(st.session_state.last_response))

    with tab3:
        st.code(compact_json, language="json")
```

# ============== ИСТОРИЯ ==============

if st.session_state.history:
with st.expander(f”◷ История запросов ({len(st.session_state.history)})”,
expanded=False):
for i, item in enumerate(st.session_state.history):
status_mark = “✓” if item[“ok”] else “✗”
status_color = “#34c759” if item[“ok”] else “#ff3b30”
preview = (item[“input”][:60] + “…”) if len(item[“input”]) > 60 else item[“input”]
preview = preview or “(пусто)”

```
        st.markdown(f"""
        <div style="padding: 8px 12px; margin: 4px 0; border-radius: 8px;
             background: rgba(255,255,255,0.55);
             font-family: ui-monospace, monospace; font-size: 12px;">
            <span style="color: {status_color};">{status_mark}</span>
            <span style="color: rgba(0,0,0,0.5);"> {item['ts']} </span>
            <span style="color: #007aff;">{item['method']} {item['endpoint']}</span>
            <span style="color: rgba(0,0,0,0.4);"> · {item['elapsed_ms']:.0f} мс · HTTP {item['status']}</span>
            <div style="color: rgba(0,0,0,0.6); margin-top: 3px;">↳ {preview}</div>
        </div>
        """, unsafe_allow_html=True)

        hc1, hc2, _ = st.columns([1, 1, 4])
        with hc1:
            if st.button("Повторить", key=f"rep_{i}", use_container_width=True):
                set_input_pending(item["input"])
                rerun()
        with hc2:
            if st.button("Показать", key=f"shw_{i}", use_container_width=True):
                st.session_state.last_response = item["response"]
                st.session_state.last_status = item["status"]
                st.session_state.last_elapsed_ms = item["elapsed_ms"]
                st.session_state.last_error = None
                st.session_state.last_is_json = item.get("is_json", True)
                rerun()

    try:
        hist_json = json.dumps(st.session_state.history,
                               ensure_ascii=False, indent=2, default=str)
        st.download_button("⬇ Экспорт истории (JSON)",
                           data=hist_json,
                           file_name=f"c2_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                           mime="application/json",
                           key="dl_history")
    except (TypeError, ValueError) as e:
        st.caption(f"Не удалось сериализовать историю: {e}")
```

# ============== СИСТЕМНЫЙ ЛОГ ==============

if st.session_state.system_log:
with st.expander(f”◈ Системный лог ({len(st.session_state.system_log)})”,
expanded=False):
log_text = “\n”.join(
f”[{e[‘ts’]}] [{e[‘level’].upper():4}] {e[‘msg’]}”
for e in st.session_state.system_log
)
st.code(log_text, language=“text”)
st.download_button(“⬇ Скачать лог”, data=log_text,
file_name=f”c2_log_{datetime.now().strftime(’%Y%m%d_%H%M%S’)}.log”,
mime=“text/plain”, key=“dl_log”)

# ============== ФУТЕР ==============

st.markdown(f”””

<div class="glass-footer">
    R9 SYSTEM · НОД C_2 · {C2_URL.split('//')[-1]} · {'TOKEN ✓' if HF_TOKEN else 'NO TOKEN'}
</div>
<div style="height: 50px;"></div>
""", unsafe_allow_html=True)
