# -*- coding: utf-8 -*-

# R9 Central v3.2 - интерфейс управления C_2 (HF Space node)

# Архитектура: R23 (Формула -> Принцип -> Аксиома -> Слова).

# 

# v3.2 vs v3.1:

# [fix]  Убран ведущий тройной docstring - причина SyntaxError U+201C

# (автозамена кавычек в редакторах). Все комментарии теперь через #.

# [new]  Custom headers (построчно Key: Value) + кастомный Authorization

# [new]  Raw body mode (произвольный JSON/text вместо {key: value})

# [new]  Query params отдельно от body (для GET/POST вместе)

# [new]  Curl-эквивалент запроса - копируемый блок

# [new]  Заголовки ответа - отдельная вкладка

# [new]  Retry c exponential backoff (0 -> 1 -> 2 секунды)

# [new]  Фильтр истории (поиск + успех/ошибки)

# [new]  Удаление записи истории, импорт истории из JSON

# [new]  Счётчик попыток в метриках

# 

# Запуск: streamlit run r9_central.py

# Переменные окружения: C2_URL (default: https://rollannf-r9-c-2.hf.space),

# HF_TOKEN (опционально - идёт в Authorization: Bearer)

import streamlit as st
import requests
import os
import time
import json
import shlex
import urllib.parse
from datetime import datetime

# ============== КОНФИГУРАЦИЯ ==============

C2_URL = os.environ.get(“C2_URL”, “https://rollannf-r9-c-2.hf.space”)
HF_TOKEN = os.environ.get(“HF_TOKEN”, “”)
DEFAULT_TIMEOUT = 30
MAX_HISTORY = 50
MAX_LOG = 80

st.set_page_config(
page_title=“R9 Central”,
page_icon=“🛰”,
layout=“centered”,
initial_sidebar_state=“collapsed”,
)

# ============== СОВМЕСТИМОСТЬ st.rerun ==============

def rerun():
if hasattr(st, “rerun”):
st.rerun()
else:
st.experimental_rerun()

# ============== SESSION STATE ==============

def init_state():
defaults = {
# Ответ
“last_response”: None,
“last_status”: None,
“last_elapsed_ms”: None,
“last_error”: None,
“last_is_json”: True,
“last_attempts”: 1,
“last_resp_headers”: {},
“last_request_snapshot”: None,  # для curl
# История и лог
“history”: [],
“system_log”: [],
“hist_filter”: “”,
“hist_show_ok”: True,
“hist_show_err”: True,
# Пинг
“health_ok”: None,
# Ввод
“input_value”: “”,
“pending_input”: None,
# Параметры запроса
“endpoint”: “/request”,
“method”: “POST”,
“timeout”: DEFAULT_TIMEOUT,
“payload_key”: “query”,
“body_mode”: “structured”,  # structured | raw | none
“query_params”: “”,          # multiline key=value
“custom_headers”: “”,        # multiline Key: Value
“use_hf_token”: True,
“custom_auth”: “”,           # если заполнено — перекрывает HF_TOKEN
“retry_enabled”: False,
“retry_count”: 3,
}
for k, v in defaults.items():
if k not in st.session_state:
st.session_state[k] = v

init_state()

# Pending-паттерн: применяем изменение ДО рендера виджета

if st.session_state.pending_input is not None:
st.session_state.input_value = st.session_state.pending_input
st.session_state.pending_input = None

# ============== CSS - БЕЗ ВНЕШНИХ @import ==============

# Одна тройная кавычка внутри st.markdown - безопасна от автозамены (парная скобкой).

st.markdown(”””

<style>
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

.stButton > button, .stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button {
    background: rgba(255,255,255,0.78) !important;
    -webkit-backdrop-filter: blur(14px) saturate(160%);
    backdrop-filter: blur(14px) saturate(160%);
    border: 1px solid rgba(0,122,255,0.2) !important;
    color: #007aff !important;
    font-weight: 500 !important; font-size: 13px !important;
    border-radius: 10px !important;
    padding: 6px 14px !important; min-height: 34px !important;
    line-height: 1.2 !important;
    box-shadow: 0 2px 8px rgba(0,122,255,0.08),
                inset 0 1px 0 rgba(255,255,255,0.6);
    transition: all 0.2s ease; width: 100%;
}
.stButton > button:hover, .stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background: rgba(255,255,255,0.98) !important;
    border-color: rgba(0,122,255,0.45) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0,122,255,0.18);
}
.stButton > button:active { transform: translateY(0) scale(0.98); }

div[data-testid="stFormSubmitButton"] > button[kind="primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #007aff 0%, #5856d6 100%) !important;
    color: #fff !important;
    border: 1px solid rgba(0,122,255,0.5) !important;
    box-shadow: 0 4px 14px rgba(0,122,255,0.35);
}

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

.stCheckbox label { font-size: 13px !important; color: rgba(0,0,0,0.75) !important; }

.stCodeBlock, pre, code {
    background: rgba(26,26,46,0.95) !important;
    border: 1px solid rgba(0,122,255,0.2) !important;
    border-radius: 12px !important;
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace !important;
    font-size: 12.5px !important;
}
.stCodeBlock pre { max-height: 460px; overflow-y: auto; }

.stJson {
    background: rgba(255,255,255,0.6) !important;
    border: 1px solid rgba(0,122,255,0.15) !important;
    border-radius: 12px !important; padding: 14px !important;
    max-height: 460px; overflow-y: auto;
}

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

.streamlit-expanderHeader, details > summary {
    background: rgba(255,255,255,0.5) !important;
    border-radius: 10px !important; font-size: 13px !important;
    font-weight: 500 !important; padding: 8px 14px !important;
}

.stAlert { border-radius: 10px !important; font-size: 13px !important;
           padding: 10px 14px !important; }

::-webkit-scrollbar { width: 6px; height: 6px; background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,122,255,0.3); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,122,255,0.5); }

.block-container { padding-top: 2rem !important; padding-bottom: 5rem !important;
                   max-width: 780px !important; }

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
.status-row { display: flex; align-items: center; gap: 10px;
              font-family: ui-monospace, monospace; font-size: 12.5px; }
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
.metric-chip.err b { color: #ff3b30; }
.metric-chip.ok  b { color: #34c759; }

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

def log(msg, level=“info”):
ts = datetime.now().strftime(”%H:%M:%S”)
st.session_state.system_log.append({“ts”: ts, “level”: level, “msg”: msg})
if len(st.session_state.system_log) > MAX_LOG:
st.session_state.system_log = st.session_state.system_log[-MAX_LOG:]

def parse_headers_text(text):
# Парсит многострочный текст “Key: Value” построчно в dict.
# Пропускает пустые строки и строки без двоеточия.
out = {}
if not text:
return out
for line in text.splitlines():
line = line.strip()
if not line or line.startswith(”#”):
continue
if “:” not in line:
continue
key, _, value = line.partition(”:”)
key, value = key.strip(), value.strip()
if key:
out[key] = value
return out

def parse_query_params(text):
# Парсит многострочный текст “key=value” построчно в dict.
out = {}
if not text:
return out
for line in text.splitlines():
line = line.strip()
if not line or line.startswith(”#”):
continue
if “=” not in line:
continue
key, _, value = line.partition(”=”)
key, value = key.strip(), value.strip()
if key:
out[key] = value
return out

def build_headers():
# Собирает финальные заголовки: HF_TOKEN + custom_auth + custom_headers.
# Приоритет: custom_auth > HF_TOKEN. custom_headers перезаписывает Authorization если задан.
headers = {}
if st.session_state.custom_auth.strip():
headers[“Authorization”] = st.session_state.custom_auth.strip()
elif st.session_state.use_hf_token and HF_TOKEN:
headers[“Authorization”] = f”Bearer {HF_TOKEN}”
# Custom headers могут перезаписать
headers.update(parse_headers_text(st.session_state.custom_headers))
return headers

def build_body(body_mode, payload_key, input_text):
# Возвращает (json_body, data_body) - используется один или другой.
# structured -> json={payload_key: input_text}
# raw        -> пытается распарсить как JSON; если не получилось, шлёт как text
# none       -> пусто
if body_mode == “none” or not input_text:
return None, None
if body_mode == “raw”:
try:
parsed = json.loads(input_text)
return parsed, None
except (ValueError, json.JSONDecodeError):
return None, input_text.encode(“utf-8”)
# structured
return {payload_key: input_text}, None

def ping_health(timeout=8):
t0 = time.perf_counter()
try:
headers = build_headers()
r = requests.get(f”{C2_URL}/health”, headers=headers, timeout=timeout)
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

def send_request_once(url, method, headers, params, json_body, data_body, timeout):
# Одна попытка. Возвращает ответ или бросает исключение.
if method == “GET”:
return requests.get(url, headers=headers, params=params, timeout=timeout)
# POST / PUT / PATCH / DELETE - все через один интерфейс
return requests.request(
method, url, headers=headers, params=params,
json=json_body if data_body is None else None,
data=data_body,
timeout=timeout,
)

def send_request(endpoint, method, headers, params, json_body, data_body,
timeout, retry_enabled=False, retry_count=3):
# С retry + exponential backoff.
# Повтор только при сетевых ошибках и 5xx.
url = f”{C2_URL}{endpoint}”
attempts = 0
last_exc = None
last_response = None
t0 = time.perf_counter()

```
max_attempts = retry_count if retry_enabled else 1

for i in range(max_attempts):
    attempts += 1
    try:
        r = send_request_once(url, method, headers, params, json_body, data_body, timeout)
        last_response = r
        # Повтор только при 5xx
        if retry_enabled and 500 <= r.status_code < 600 and i < max_attempts - 1:
            log(f"  попытка {attempts}: HTTP {r.status_code}, повтор через {2**i} с", "warn")
            time.sleep(2 ** i)
            continue
        break
    except (requests.exceptions.Timeout,
            requests.exceptions.ConnectionError) as e:
        last_exc = e
        if retry_enabled and i < max_attempts - 1:
            log(f"  попытка {attempts}: {type(e).__name__}, повтор через {2**i} с", "warn")
            time.sleep(2 ** i)
            continue
        break
    except Exception as e:
        last_exc = e
        break

elapsed = (time.perf_counter() - t0) * 1000

if last_response is not None:
    try:
        data = last_response.json()
        is_json = True
    except ValueError:
        data = last_response.text
        is_json = False
    return {
        "ok": last_response.ok,
        "status_code": last_response.status_code,
        "elapsed_ms": elapsed,
        "data": data,
        "is_json": is_json,
        "size_bytes": len(last_response.content),
        "error": None,
        "attempts": attempts,
        "resp_headers": dict(last_response.headers),
    }

# Исключение
if isinstance(last_exc, requests.exceptions.Timeout):
    err_msg = "Таймаут запроса"
elif isinstance(last_exc, requests.exceptions.ConnectionError):
    err_msg = "Нет соединения"
else:
    err_msg = f"{type(last_exc).__name__}: {last_exc}"

return {
    "ok": False, "status_code": None, "elapsed_ms": elapsed,
    "data": None, "is_json": False, "size_bytes": 0,
    "error": err_msg, "attempts": attempts, "resp_headers": {},
}
```

def build_curl(method, url, headers, params, json_body, data_body):
# Собирает копируемый curl-эквивалент.
parts = [“curl”, “-X”, method]
full_url = url
if params:
qs = urllib.parse.urlencode(params)
sep = “&” if “?” in full_url else “?”
full_url = f”{full_url}{sep}{qs}”
parts.append(shlex.quote(full_url))
for k, v in headers.items():
parts.extend([”-H”, shlex.quote(f”{k}: {v}”)])
if json_body is not None:
parts.extend([”-H”, “‘Content-Type: application/json’”])
body_str = json.dumps(json_body, ensure_ascii=False)
parts.extend([”-d”, shlex.quote(body_str)])
elif data_body is not None:
try:
body_str = data_body.decode(“utf-8”)
except (AttributeError, UnicodeDecodeError):
body_str = str(data_body)
parts.extend([”-d”, shlex.quote(body_str)])
return “ \\n  “.join(parts)

def format_bytes(n):
n = float(n)
for unit in [“Б”, “КБ”, “МБ”]:
if n < 1024:
return f”{n:.0f} {unit}” if unit == “Б” else f”{n:.1f} {unit}”
n /= 1024
return f”{n:.1f} ГБ”

def set_input_pending(value):
st.session_state.pending_input = value

# ============== ХЕДЕР ==============

st.markdown(”””

<div style="text-align:center; margin: 1.2rem 0 1.4rem 0; position: relative; z-index: 1;">
    <div style="color: rgba(0,122,255,0.6); font-size: 11px;
         font-family: ui-monospace, monospace;
         letter-spacing: 3px; margin-bottom: 8px; text-transform: uppercase;">
        Системный интерфейс · v3.2
    </div>
    <h1 style="font-size: 30px; font-weight: 600; color: #1a1a2e;
         margin: 0; letter-spacing: -1px;">◈ R9 Central</h1>
    <div style="color: rgba(0,0,0,0.5); font-size: 13px; margin-top: 6px;">
        Канал связи с узлом C_2 · защищённый
    </div>
</div>
""", unsafe_allow_html=True)

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
if st.button(“⟲ Сброс”, key=“btn_reset”, help=“Очистить ответ, историю и лог”):
st.session_state.history = []
st.session_state.system_log = []
st.session_state.last_response = None
st.session_state.last_error = None
st.session_state.last_resp_headers = {}
st.session_state.last_request_snapshot = None
log(“Состояние очищено”, “info”)
rerun()

# ============== ПАРАМЕТРЫ ==============

st.markdown(’<div class="section-label">◉ Передача команды</div>’, unsafe_allow_html=True)

with st.expander(“⚙ Параметры запроса”, expanded=False):
tab_basic, tab_headers, tab_query, tab_retry = st.tabs(
[“Основное”, “Заголовки”, “Query-параметры”, “Повторы”]
)

```
with tab_basic:
    ca, cb, cc = st.columns([2, 1, 1])
    with ca:
        st.session_state.endpoint = st.text_input(
            "Endpoint", value=st.session_state.endpoint,
            help="Путь на C_2: /request, /health, /status, ..."
        )
    with cb:
        st.session_state.method = st.selectbox(
            "Метод", ["POST", "GET", "PUT", "PATCH", "DELETE"],
            index=["POST", "GET", "PUT", "PATCH", "DELETE"].index(
                st.session_state.method
            ) if st.session_state.method in ["POST", "GET", "PUT", "PATCH", "DELETE"] else 0,
        )
    with cc:
        st.session_state.timeout = st.number_input(
            "Таймаут (с)", min_value=1, max_value=300,
            value=int(st.session_state.timeout), step=1,
        )

    cd, ce = st.columns([1, 2])
    with cd:
        st.session_state.body_mode = st.selectbox(
            "Тело запроса",
            ["structured", "raw", "none"],
            index=["structured", "raw", "none"].index(st.session_state.body_mode),
            help=(
                "structured: {ключ: ввод}  |  "
                "raw: ввод как есть (JSON или text)  |  "
                "none: без тела"
            ),
        )
    with ce:
        if st.session_state.body_mode == "structured":
            st.session_state.payload_key = st.text_input(
                "Ключ payload", value=st.session_state.payload_key,
                help="Под каким ключом обернуть введённый текст в JSON-тело"
            )
        else:
            st.caption(
                "В режиме 'raw' ввод отправляется как JSON (если парсится) "
                "или как plain text. В 'none' тело пустое."
            )

with tab_headers:
    st.session_state.use_hf_token = st.checkbox(
        f"Использовать HF_TOKEN (Authorization: Bearer …{HF_TOKEN[-6:] if HF_TOKEN else 'нет'})",
        value=st.session_state.use_hf_token,
        disabled=not HF_TOKEN,
    )
    if not HF_TOKEN:
        st.caption("HF_TOKEN не установлен в переменных окружения")

    st.session_state.custom_auth = st.text_input(
        "Кастомный Authorization (перекрывает HF_TOKEN)",
        value=st.session_state.custom_auth,
        placeholder="Bearer sk-... или Basic ...",
        type="password",
    )

    st.session_state.custom_headers = st.text_area(
        "Дополнительные заголовки (Key: Value построчно)",
        value=st.session_state.custom_headers,
        placeholder="Content-Type: application/json\nX-Request-ID: abc123\n# строки с # пропускаются",
        height=90,
    )

    # Превью итоговых заголовков
    final_hdrs = build_headers()
    if final_hdrs:
        preview_hdrs = {
            k: (v[:20] + "…") if k.lower() == "authorization" and len(v) > 20 else v
            for k, v in final_hdrs.items()
        }
        st.caption("Итоговые заголовки:")
        st.code(json.dumps(preview_hdrs, ensure_ascii=False, indent=2), language="json")

with tab_query:
    st.session_state.query_params = st.text_area(
        "Query-параметры (key=value построчно)",
        value=st.session_state.query_params,
        placeholder="limit=10\nsort=desc\n# пустые и # строки пропускаются",
        height=90,
    )
    qp = parse_query_params(st.session_state.query_params)
    if qp:
        st.caption(f"Будет добавлено к URL: ?{urllib.parse.urlencode(qp)}")

with tab_retry:
    st.session_state.retry_enabled = st.checkbox(
        "Включить повторы при сбоях",
        value=st.session_state.retry_enabled,
        help="Повтор при таймауте, сетевой ошибке или HTTP 5xx"
    )
    st.session_state.retry_count = st.number_input(
        "Количество попыток (всего)",
        min_value=1, max_value=10, step=1,
        value=int(st.session_state.retry_count),
        disabled=not st.session_state.retry_enabled,
    )
    if st.session_state.retry_enabled:
        delays = " → ".join(f"{2**i}с" for i in range(st.session_state.retry_count - 1))
        st.caption(f"Задержки между попытками (exponential backoff): {delays}")
```

# ============== ФОРМА ==============

with st.form(key=“request_form”, clear_on_submit=False):
placeholder_text = {
“structured”: ‘Введите запрос…\nБудет обёрнут: {”’ + st.session_state.payload_key + ‘”: “…”}’,
“raw”:        ‘Введите тело запроса (JSON или plain text)…’,
“none”:       ‘Тело запроса не отправляется (режим none)’,
}[st.session_state.body_mode]

```
user_input = st.text_area(
    "Команда для C_2",
    value=st.session_state.input_value,
    key="input_widget",
    placeholder=placeholder_text,
    height=100,
    disabled=(st.session_state.body_mode == "none"),
)
submitted = st.form_submit_button("▶ Отправить", type="primary",
                                  use_container_width=True)
```

if “input_widget” in st.session_state:
st.session_state.input_value = st.session_state.input_widget

# ============== КНОПКИ ВНЕ ФОРМЫ ==============

ac1, ac2, ac3, ac4 = st.columns([1, 1, 1, 2])
with ac1:
if st.button(“⌫ Очистить”, key=“btn_clear”):
set_input_pending(””)
rerun()
with ac2:
show_input_btn = st.button(“📋 Копия”, key=“btn_copy_input”,
help=“Показать ввод блоком для копирования”)
with ac3:
show_curl_btn = st.button(“⌨ Curl”, key=“btn_curl_preview”,
help=“Сгенерировать curl-эквивалент будущего запроса”)

if show_input_btn and st.session_state.input_value:
st.code(st.session_state.input_value, language=“text”)

if show_curl_btn:
method = st.session_state.method
endpoint = st.session_state.endpoint
headers = build_headers()
params = parse_query_params(st.session_state.query_params)
json_body, data_body = build_body(
st.session_state.body_mode,
st.session_state.payload_key,
st.session_state.input_value,
)
curl_str = build_curl(method, f”{C2_URL}{endpoint}”, headers, params, json_body, data_body)
st.caption(“curl-эквивалент будущего запроса:”)
st.code(curl_str, language=“bash”)

# ============== ОБРАБОТКА ОТПРАВКИ ==============

if submitted:
method = st.session_state.method
endpoint = st.session_state.endpoint
body_mode = st.session_state.body_mode
payload_key = st.session_state.payload_key
timeout = int(st.session_state.timeout)
input_text = st.session_state.input_value

```
# Валидация
abort = False
if body_mode == "structured" and not input_text.strip() and method in ("POST", "PUT", "PATCH"):
    log("Пустой ввод при structured body — отмена", "warn")
    st.warning("Введите команду перед отправкой или смените режим тела на 'none'")
    abort = True

if not abort:
    headers = build_headers()
    params = parse_query_params(st.session_state.query_params)
    json_body, data_body = build_body(body_mode, payload_key, input_text)

    log(f"→ {method} {endpoint}"
        + (f"  (params={len(params)})" if params else "")
        + (f"  [retry ON x{st.session_state.retry_count}]"
           if st.session_state.retry_enabled else ""),
        "info")

    with st.spinner(f"Отправка {method} {endpoint}..."):
        result = send_request(
            endpoint, method, headers, params, json_body, data_body, timeout,
            retry_enabled=st.session_state.retry_enabled,
            retry_count=int(st.session_state.retry_count),
        )

    st.session_state.last_response = result["data"]
    st.session_state.last_status = result["status_code"]
    st.session_state.last_elapsed_ms = result["elapsed_ms"]
    st.session_state.last_error = result["error"]
    st.session_state.last_is_json = result["is_json"]
    st.session_state.last_attempts = result["attempts"]
    st.session_state.last_resp_headers = result["resp_headers"]
    st.session_state.last_request_snapshot = {
        "method": method,
        "url": f"{C2_URL}{endpoint}",
        "headers": headers,
        "params": params,
        "json_body": json_body,
        "data_body": data_body.decode("utf-8", errors="replace") if data_body else None,
    }

    if result["error"]:
        log(f"✗ {result['error']} · попыток: {result['attempts']}", "err")
    elif result["ok"]:
        log(f"✓ {result['status_code']} · {result['elapsed_ms']:.0f} мс · "
            f"{format_bytes(result['size_bytes'])} · попыток: {result['attempts']}", "ok")
    else:
        log(f"✗ HTTP {result['status_code']} · {result['elapsed_ms']:.0f} мс · "
            f"попыток: {result['attempts']}", "err")

    st.session_state.history.insert(0, {
        "ts": datetime.now().strftime("%H:%M:%S"),
        "method": method,
        "endpoint": endpoint,
        "input": input_text,
        "body_mode": body_mode,
        "status": result["status_code"],
        "elapsed_ms": result["elapsed_ms"],
        "ok": result["ok"],
        "is_json": result["is_json"],
        "attempts": result["attempts"],
        "response": (result["data"] if result["is_json"]
                    else {"text": str(result["data"])[:1000]}),
    })
    st.session_state.history = st.session_state.history[:MAX_HISTORY]
```

# ============== ОТВЕТ ==============

if st.session_state.last_response is not None or st.session_state.last_error:
st.markdown(’<div class="section-label">◉ Ответ C_2</div>’, unsafe_allow_html=True)

```
status = st.session_state.last_status
elapsed = st.session_state.last_elapsed_ms
err = st.session_state.last_error
attempts = st.session_state.last_attempts

metrics = '<div class="metrics-row">'
if status is not None:
    status_cls = "ok" if 200 <= status < 300 else "err"
    metrics += f'<span class="metric-chip {status_cls}">HTTP <b>{status}</b></span>'
if elapsed is not None:
    metrics += f'<span class="metric-chip">Время <b>{elapsed:.0f} мс</b></span>'
if st.session_state.last_response is not None:
    try:
        size = len(json.dumps(st.session_state.last_response,
                              ensure_ascii=False, default=str).encode("utf-8"))
        metrics += f'<span class="metric-chip">Размер <b>{format_bytes(size)}</b></span>'
    except (TypeError, ValueError):
        pass
if attempts and attempts > 1:
    metrics += f'<span class="metric-chip">Попыток <b>{attempts}</b></span>'
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 JSON", "🌳 Дерево", "📝 Компактный", "📨 Headers", "⌨ Curl"
    ])

    with tab1:
        # Встроенная кнопка копирования у st.code - правый верхний угол
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

    with tab4:
        hdrs = st.session_state.last_resp_headers or {}
        if hdrs:
            hdrs_json = json.dumps(hdrs, ensure_ascii=False, indent=2)
            st.code(hdrs_json, language="json")
        else:
            st.caption("Заголовки ответа недоступны (ошибка запроса)")

    with tab5:
        snap = st.session_state.last_request_snapshot
        if snap:
            # Восстанавливаем data_body из строки
            db = snap["data_body"].encode("utf-8") if snap["data_body"] else None
            curl_str = build_curl(
                snap["method"], snap["url"],
                snap["headers"], snap["params"],
                snap["json_body"], db,
            )
            st.code(curl_str, language="bash")
            st.download_button("⬇ Скачать curl", data=curl_str,
                               file_name=f"c2_curl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh",
                               mime="text/x-shellscript",
                               key="dl_curl")
        else:
            st.caption("Снимок запроса недоступен")
```

# ============== ИСТОРИЯ ==============

if st.session_state.history:
with st.expander(f”◷ История запросов ({len(st.session_state.history)})”,
expanded=False):
# Фильтры
fc1, fc2, fc3 = st.columns([3, 1, 1])
with fc1:
st.session_state.hist_filter = st.text_input(
“Поиск по истории (endpoint / ввод)”,
value=st.session_state.hist_filter,
placeholder=“Подстрока…”,
label_visibility=“collapsed”,
)
with fc2:
st.session_state.hist_show_ok = st.checkbox(
“✓ Успех”, value=st.session_state.hist_show_ok
)
with fc3:
st.session_state.hist_show_err = st.checkbox(
“✗ Ошибки”, value=st.session_state.hist_show_err
)

```
    # Применяем фильтры
    flt = st.session_state.hist_filter.lower().strip()
    filtered = []
    for item in st.session_state.history:
        if item["ok"] and not st.session_state.hist_show_ok:
            continue
        if not item["ok"] and not st.session_state.hist_show_err:
            continue
        if flt:
            hay = (item["endpoint"] + " " + item["input"]).lower()
            if flt not in hay:
                continue
        filtered.append(item)

    if not filtered:
        st.caption("Записи не найдены по текущим фильтрам")
    else:
        st.caption(f"Показано: {len(filtered)} из {len(st.session_state.history)}")

    for item in filtered:
        orig_idx = st.session_state.history.index(item)
        status_mark = "✓" if item["ok"] else "✗"
        status_color = "#34c759" if item["ok"] else "#ff3b30"
        preview = (item["input"][:70] + "…") if len(item["input"]) > 70 else item["input"]
        preview = preview or "(пусто)"
        attempts_str = f" · x{item.get('attempts', 1)}" if item.get("attempts", 1) > 1 else ""

        st.markdown(f"""
        <div style="padding: 8px 12px; margin: 4px 0; border-radius: 8px;
             background: rgba(255,255,255,0.55);
             font-family: ui-monospace, monospace; font-size: 12px;">
            <span style="color: {status_color};">{status_mark}</span>
            <span style="color: rgba(0,0,0,0.5);"> {item['ts']} </span>
            <span style="color: #007aff;">{item['method']} {item['endpoint']}</span>
            <span style="color: rgba(0,0,0,0.4);"> · {item['elapsed_ms']:.0f} мс · HTTP {item['status']}{attempts_str}</span>
            <div style="color: rgba(0,0,0,0.6); margin-top: 3px;">↳ {preview}</div>
        </div>
        """, unsafe_allow_html=True)

        hc1, hc2, hc3, _ = st.columns([1, 1, 1, 3])
        with hc1:
            if st.button("Повторить", key=f"rep_{orig_idx}", use_container_width=True):
                set_input_pending(item["input"])
                rerun()
        with hc2:
            if st.button("Показать", key=f"shw_{orig_idx}", use_container_width=True):
                st.session_state.last_response = item["response"]
                st.session_state.last_status = item["status"]
                st.session_state.last_elapsed_ms = item["elapsed_ms"]
                st.session_state.last_error = None
                st.session_state.last_is_json = item.get("is_json", True)
                st.session_state.last_attempts = item.get("attempts", 1)
                st.session_state.last_resp_headers = {}
                rerun()
        with hc3:
            if st.button("Удалить", key=f"del_{orig_idx}", use_container_width=True):
                st.session_state.history.pop(orig_idx)
                log(f"Удалена запись #{orig_idx}", "info")
                rerun()

    # Экспорт / импорт
    ec1, ec2 = st.columns(2)
    with ec1:
        try:
            hist_json = json.dumps(st.session_state.history,
                                   ensure_ascii=False, indent=2, default=str)
            st.download_button(
                "⬇ Экспорт истории",
                data=hist_json,
                file_name=f"c2_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                key="dl_history",
            )
        except (TypeError, ValueError) as e:
            st.caption(f"Ошибка сериализации: {e}")

    with ec2:
        uploaded = st.file_uploader(
            "⬆ Импорт истории",
            type=["json"],
            key="hist_upload",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            try:
                loaded = json.loads(uploaded.read().decode("utf-8"))
                if isinstance(loaded, list):
                    st.session_state.history = loaded + st.session_state.history
                    st.session_state.history = st.session_state.history[:MAX_HISTORY]
                    log(f"Импортировано записей: {len(loaded)}", "info")
                    rerun()
                else:
                    st.error("Ожидался список записей")
            except (ValueError, UnicodeDecodeError) as e:
                st.error(f"Не удалось разобрать JSON: {e}")
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
st.download_button(
“⬇ Скачать лог”, data=log_text,
file_name=f”c2_log_{datetime.now().strftime(’%Y%m%d_%H%M%S’)}.log”,
mime=“text/plain”, key=“dl_log”,
)

# ============== ФУТЕР ==============

st.markdown(f”””

<div class="glass-footer">
    R9 SYSTEM · НОД C_2 · {C2_URL.split('//')[-1]} · {'TOKEN ✓' if HF_TOKEN else 'NO TOKEN'} · v3.2
</div>
<div style="height: 50px;"></div>
""", unsafe_allow_html=True)
