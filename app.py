"""
R9 Central — интерфейс управления C_2 (HF Space node)
Архитектура: R23 — Формула → Принцип → Аксиома → Слова
"""

import streamlit as st
import requests
import os
import time
import json
from datetime import datetime

# ============== КОНФИГУРАЦИЯ ==============
C2_URL = os.environ.get("C2_URL", "https://rollannf-r9-c-2.hf.space")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
DEFAULT_TIMEOUT = 30  # секунд

st.set_page_config(
    page_title="R9 Central",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============== SESSION STATE ==============
def init_state():
    defaults = {
        "history": [],           # [{ts, endpoint, method, payload, status, resp, elapsed_ms}]
        "last_response": None,   # dict | None
        "last_status": None,     # int | None
        "last_elapsed_ms": None, # float | None
        "last_error": None,      # str | None
        "view_mode": "Форматированный",  # Форматированный | Сырой JSON | Дерево
        "system_log": [],        # список строк для лога (можно копировать целиком)
        "health_ok": None,       # True | False | None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============== CSS — КОМПАКТНАЯ SCI-FI ЭСТЕТИКА ==============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* База */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 50%, #f0f4f8 100%);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Сетка */
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background-image: radial-gradient(circle at 1px 1px, rgba(0, 150, 255, 0.07) 1px, transparent 0);
    background-size: 36px 36px;
    pointer-events: none; z-index: 0;
}

/* Орбиты — фоновая глубина */
.orb { position: fixed; border-radius: 50%; filter: blur(80px); opacity: 0.4; pointer-events: none; z-index: 0; }
.orb-1 { width: 360px; height: 360px; background: rgba(0, 122, 255, 0.15); top: -100px; right: -80px; }
.orb-2 { width: 280px; height: 280px; background: rgba(88, 86, 214, 0.10); bottom: -50px; left: -50px; }

/* Типографика */
h1, h2, h3 { color: #1a1a2e !important; font-weight: 500 !important; letter-spacing: -0.3px; }

/* === КОМПАКТНЫЕ КНОПКИ === */
.stButton > button {
    background: rgba(255, 255, 255, 0.75) !important;
    backdrop-filter: blur(16px) saturate(160%);
    -webkit-backdrop-filter: blur(16px) saturate(160%);
    border: 1px solid rgba(0, 122, 255, 0.18) !important;
    color: #007aff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border-radius: 10px !important;
    padding: 6px 14px !important;
    min-height: 34px !important;
    line-height: 1.2 !important;
    box-shadow:
        0 2px 8px rgba(0, 122, 255, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.6);
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
    width: 100%;
}
.stButton > button:hover {
    background: rgba(255, 255, 255, 0.95) !important;
    border-color: rgba(0, 122, 255, 0.4) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0, 122, 255, 0.18);
}
.stButton > button:active { transform: translateY(0) scale(0.98); }

/* Основная кнопка — акцент */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #007aff 0%, #5856d6 100%) !important;
    color: white !important;
    border: 1px solid rgba(0, 122, 255, 0.5) !important;
    box-shadow: 0 4px 14px rgba(0, 122, 255, 0.35);
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(0, 122, 255, 0.45);
}

/* Поля ввода */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(14px);
    border: 1px solid rgba(0, 122, 255, 0.15) !important;
    color: #1a1a2e !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    border-radius: 10px !important;
}
.stTextInput > div > div > input { padding: 10px 14px !important; }
.stTextArea > div > div > textarea { padding: 12px 14px !important; }

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    background: rgba(255, 255, 255, 0.95) !important;
    border-color: rgba(0, 122, 255, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1) !important;
    outline: none !important;
}

/* Подписи полей */
.stTextInput label, .stTextArea label, .stSelectbox label {
    color: rgba(0, 0, 0, 0.6) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* Code block — с встроенной кнопкой копирования Streamlit */
.stCodeBlock, pre, code {
    background: rgba(26, 26, 46, 0.95) !important;
    border: 1px solid rgba(0, 122, 255, 0.2) !important;
    border-radius: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12.5px !important;
}
.stCodeBlock pre { max-height: 480px; overflow-y: auto; }

/* JSON display */
.stJson {
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(18px);
    border: 1px solid rgba(0, 122, 255, 0.15) !important;
    border-radius: 12px !important;
    padding: 14px !important;
    max-height: 480px;
    overflow-y: auto;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: rgba(255, 255, 255, 0.5);
    padding: 4px; border-radius: 10px; backdrop-filter: blur(14px);
}
.stTabs [data-baseweb="tab"] {
    padding: 6px 14px !important; height: 32px !important;
    background: transparent !important; border-radius: 7px !important;
    color: rgba(0, 0, 0, 0.6) !important; font-size: 13px !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255, 255, 255, 0.95) !important;
    color: #007aff !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

/* Expander — компактный */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.5) !important;
    border-radius: 10px !important;
    font-size: 13px !important; font-weight: 500 !important;
    padding: 8px 14px !important;
}

/* Alerts */
.stAlert {
    border-radius: 10px !important;
    backdrop-filter: blur(10px);
    font-size: 13px !important;
    padding: 10px 14px !important;
}

/* Скроллбар */
::-webkit-scrollbar { width: 6px; height: 6px; background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0, 122, 255, 0.3); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 122, 255, 0.5); }

/* Контейнер */
.block-container {
    padding-top: 2rem !important; padding-bottom: 5rem !important;
    max-width: 760px !important;
}

/* Glass-card — только для декоративных HTML-блоков */
.glass-card {
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(26px) saturate(150%);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 16px;
    padding: 14px 18px;
    margin: 10px 0;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.8);
    position: relative;
}

.section-label {
    color: rgba(0, 122, 255, 0.8);
    font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 2px;
    margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
}

/* Статусная строка */
.status-row {
    display: flex; align-items: center; gap: 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 12.5px;
}
.status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    flex-shrink: 0;
}
.status-dot.ok  { background: #34c759; box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.2); }
.status-dot.err { background: #ff3b30; box-shadow: 0 0 0 3px rgba(255, 59, 48, 0.2); }
.status-dot.idle{ background: #8e8e93; box-shadow: 0 0 0 3px rgba(142, 142, 147, 0.2); }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.status-dot.ok, .status-dot.err { animation: pulse 2.4s ease-in-out infinite; }

/* Метрики */
.metrics-row {
    display: flex; gap: 10px; flex-wrap: wrap;
    font-family: 'JetBrains Mono', monospace; font-size: 11.5px;
    color: rgba(0, 0, 0, 0.55);
    margin: 6px 0;
}
.metric-chip {
    background: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(0, 122, 255, 0.15);
    padding: 3px 10px; border-radius: 6px;
}
.metric-chip b { color: #007aff; font-weight: 600; }

/* Лог-линии */
.log-line { font-family: 'JetBrains Mono', monospace; font-size: 12px; margin: 2px 0; }
.log-line.ok   { color: #34c759; }
.log-line.err  { color: #ff3b30; }
.log-line.info { color: rgba(0, 122, 255, 0.8); }
.log-line.warn { color: #ff9500; }

/* Футер */
.glass-footer {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(18px);
    border-top: 1px solid rgba(255, 255, 255, 0.8);
    padding: 8px 20px; text-align: center; z-index: 100;
    font-family: 'JetBrains Mono', monospace;
    color: rgba(0, 0, 0, 0.45); font-size: 11px; letter-spacing: 1px;
}

/* Скрыть "Press Enter to apply" подсказку */
[data-testid="InputInstructions"] { display: none !important; }

/* Компактный st.form */
[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
}
</style>

<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
""", unsafe_allow_html=True)


# ============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==============
def log(msg: str, level: str = "info"):
    """Добавляет строку в системный лог (видим пользователю, копируемый)."""
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.system_log.append({"ts": ts, "level": level, "msg": msg})
    # Держим только последние 50 строк
    if len(st.session_state.system_log) > 50:
        st.session_state.system_log = st.session_state.system_log[-50:]


def ping_health(timeout: int = 8):
    """Проверка живости C_2. Возвращает (ok: bool, payload, elapsed_ms, error)."""
    t0 = time.perf_counter()
    try:
        r = requests.get(f"{C2_URL}/health", headers=HEADERS, timeout=timeout)
        elapsed = (time.perf_counter() - t0) * 1000
        try:
            payload = r.json()
        except json.JSONDecodeError:
            payload = {"raw_text": r.text[:500]}
        return r.ok, payload, elapsed, None
    except requests.exceptions.Timeout:
        return False, None, (time.perf_counter() - t0) * 1000, "Таймаут соединения"
    except requests.exceptions.ConnectionError as e:
        return False, None, (time.perf_counter() - t0) * 1000, f"Нет соединения: {e}"
    except Exception as e:
        return False, None, (time.perf_counter() - t0) * 1000, f"{type(e).__name__}: {e}"


def send_request(endpoint: str, method: str, payload: dict, timeout: int):
    """Отправка запроса. Возвращает унифицированный результат."""
    url = f"{C2_URL}{endpoint}"
    t0 = time.perf_counter()
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, params=payload, timeout=timeout)
        else:
            r = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
        elapsed = (time.perf_counter() - t0) * 1000
        try:
            data = r.json()
            is_json = True
        except json.JSONDecodeError:
            data = r.text
            is_json = False
        return {
            "ok": r.ok,
            "status_code": r.status_code,
            "elapsed_ms": elapsed,
            "data": data,
            "is_json": is_json,
            "size_bytes": len(r.content),
            "error": None,
        }
    except requests.exceptions.Timeout:
        return {"ok": False, "status_code": None, "elapsed_ms": (time.perf_counter()-t0)*1000,
                "data": None, "is_json": False, "size_bytes": 0, "error": "Таймаут запроса"}
    except requests.exceptions.ConnectionError as e:
        return {"ok": False, "status_code": None, "elapsed_ms": (time.perf_counter()-t0)*1000,
                "data": None, "is_json": False, "size_bytes": 0, "error": f"Нет соединения"}
    except Exception as e:
        return {"ok": False, "status_code": None, "elapsed_ms": (time.perf_counter()-t0)*1000,
                "data": None, "is_json": False, "size_bytes": 0,
                "error": f"{type(e).__name__}: {e}"}


def format_bytes(n: int) -> str:
    for unit in ["Б", "КБ", "МБ"]:
        if n < 1024: return f"{n:.0f} {unit}" if unit == "Б" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} ГБ"


# ============== ХЕДЕР ==============
st.markdown("""
<div style="text-align: center; margin: 1.5rem 0 2rem 0; position: relative; z-index: 1;">
    <div style="color: rgba(0, 122, 255, 0.6); font-size: 11px; font-family: 'JetBrains Mono', monospace;
         letter-spacing: 3px; margin-bottom: 8px; text-transform: uppercase;">
        Системный интерфейс · v3.0
    </div>
    <h1 style="font-size: 30px; font-weight: 600; color: #1a1a2e; margin: 0; letter-spacing: -1px;">
        ◈ R9 Central
    </h1>
    <div style="color: rgba(0, 0, 0, 0.5); font-size: 13px; margin-top: 6px;">
        Канал связи с узлом C_2 · защищённый
    </div>
</div>
""", unsafe_allow_html=True)

# Предупреждение об отсутствии токена
if not HF_TOKEN:
    st.warning("⚠ `HF_TOKEN` не установлен в переменных окружения. "
               "Запросы к защищённым endpoint'ам могут вернуть 401/403.", icon="⚠")

# ============== СТАТУС C_2 ==============
status_col1, status_col2, status_col3 = st.columns([3, 1, 1])

with status_col1:
    dot_class = "idle"
    status_text = "Статус неизвестен — выполните проверку"
    if st.session_state.health_ok is True:
        dot_class, status_text = "ok", f"C_2 онлайн · {C2_URL.split('//')[-1]}"
    elif st.session_state.health_ok is False:
        dot_class, status_text = "err", f"C_2 недоступен · {C2_URL.split('//')[-1]}"
    st.markdown(f"""
    <div class="glass-card" style="padding: 10px 14px;">
        <div class="status-row">
            <div class="status-dot {dot_class}"></div>
            <span>{status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with status_col2:
    if st.button("🛰 Пинг", key="btn_ping"):
        with st.spinner("Проверка..."):
            ok, payload, elapsed, err = ping_health()
        st.session_state.health_ok = ok
        if ok:
            log(f"Health OK · {elapsed:.0f} мс · {payload}", "ok")
        else:
            log(f"Health FAIL · {err or 'статус-код не 2xx'}", "err")
        st.rerun()

with status_col3:
    if st.button("⟲ Сброс", key="btn_reset", help="Очистить историю и лог"):
        st.session_state.history = []
        st.session_state.system_log = []
        st.session_state.last_response = None
        st.session_state.last_error = None
        log("Состояние очищено", "info")
        st.rerun()


# ============== ФОРМА ЗАПРОСА ==============
st.markdown('<div class="section-label" style="margin-top: 18px;">◉ Передача команды</div>', unsafe_allow_html=True)

with st.expander("⚙ Параметры запроса", expanded=False):
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        endpoint = st.text_input("Endpoint", value="/request", key="endpoint",
                                 help="Путь на C_2, например: /request, /health, /status")
    with col_b:
        method = st.selectbox("Метод", ["POST", "GET"], index=0, key="method")
    with col_c:
        timeout = st.number_input("Таймаут (с)", min_value=1, max_value=300,
                                  value=DEFAULT_TIMEOUT, step=1, key="timeout")
    payload_key = st.text_input("Имя поля payload", value="query", key="payload_key",
                                help="Для POST — под каким ключом передать ввод. Обычно 'query'")

with st.form("request_form", clear_on_submit=False):
    user_input = st.text_area(
        "Команда для C_2",
        placeholder="Введите запрос...\nEnter для переноса строки · Ctrl+Enter для отправки",
        height=100,
        key="user_input",
    )
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
    with btn_col1:
        submitted = st.form_submit_button("▶ Отправить", type="primary",
                                          use_container_width=True)
    with btn_col2:
        clear = st.form_submit_button("⌫ Очистить", use_container_width=True)

if clear:
    st.session_state.user_input = ""
    st.rerun()

if submitted:
    if not user_input.strip() and method == "POST":
        log("Пустой ввод — отмена", "warn")
        st.warning("Введите команду перед отправкой")
    else:
        log(f"→ {method} {endpoint}", "info")
        with st.spinner(f"Отправка {method} {endpoint}..."):
            payload = {payload_key: user_input} if method == "POST" else ({payload_key: user_input} if user_input else {})
            result = send_request(endpoint, method, payload, int(timeout))

        # Сохранение последнего ответа
        st.session_state.last_response = result["data"]
        st.session_state.last_status = result["status_code"]
        st.session_state.last_elapsed_ms = result["elapsed_ms"]
        st.session_state.last_error = result["error"]

        # Лог
        if result["error"]:
            log(f"✗ {result['error']}", "err")
        elif result["ok"]:
            log(f"✓ {result['status_code']} · {result['elapsed_ms']:.0f} мс · {format_bytes(result['size_bytes'])}", "ok")
        else:
            log(f"✗ HTTP {result['status_code']} · {result['elapsed_ms']:.0f} мс", "err")

        # История
        st.session_state.history.insert(0, {
            "ts": datetime.now().strftime("%H:%M:%S"),
            "method": method,
            "endpoint": endpoint,
            "input": user_input,
            "status": result["status_code"],
            "elapsed_ms": result["elapsed_ms"],
            "ok": result["ok"],
            "response": result["data"] if result["is_json"] else {"text": str(result["data"])[:500]},
        })
        st.session_state.history = st.session_state.history[:20]


# ============== ОТОБРАЖЕНИЕ ОТВЕТА ==============
if st.session_state.last_response is not None or st.session_state.last_error:
    st.markdown('<div class="section-label" style="margin-top: 18px;">◉ Ответ C_2</div>',
                unsafe_allow_html=True)

    # Метрики
    status = st.session_state.last_status
    elapsed = st.session_state.last_elapsed_ms
    err = st.session_state.last_error

    metrics_html = '<div class="metrics-row">'
    if status is not None:
        color = "ok" if 200 <= status < 300 else "err"
        metrics_html += f'<span class="metric-chip">HTTP <b>{status}</b></span>'
    if elapsed is not None:
        metrics_html += f'<span class="metric-chip">Время <b>{elapsed:.0f} мс</b></span>'
    if st.session_state.last_response is not None:
        try:
            size = len(json.dumps(st.session_state.last_response, ensure_ascii=False).encode("utf-8"))
            metrics_html += f'<span class="metric-chip">Размер <b>{format_bytes(size)}</b></span>'
        except (TypeError, ValueError):
            pass
    metrics_html += '</div>'
    st.markdown(metrics_html, unsafe_allow_html=True)

    if err:
        st.error(f"Ошибка: {err}")

    if st.session_state.last_response is not None:
        # Сериализация для копирования
        try:
            pretty_json = json.dumps(st.session_state.last_response,
                                     ensure_ascii=False, indent=2, default=str)
            compact_json = json.dumps(st.session_state.last_response,
                                      ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            pretty_json = str(st.session_state.last_response)
            compact_json = str(st.session_state.last_response)

        # Табы: JSON (с копированием) / Дерево / Сырой текст
        tab1, tab2, tab3 = st.tabs(["📋 JSON · копируемый", "🌳 Дерево", "📝 Компактный"])

        with tab1:
            # st.code имеет встроенную кнопку копирования в правом верхнем углу
            st.code(pretty_json, language="json")
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    "⬇ Скачать JSON",
                    data=pretty_json,
                    file_name=f"c2_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with dl_col2:
                st.download_button(
                    "⬇ Скачать как .txt",
                    data=pretty_json,
                    file_name=f"c2_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        with tab2:
            if isinstance(st.session_state.last_response, (dict, list)):
                st.json(st.session_state.last_response, expanded=True)
            else:
                st.text(str(st.session_state.last_response))

        with tab3:
            st.code(compact_json, language="json")


# ============== ИСТОРИЯ ЗАПРОСОВ ==============
if st.session_state.history:
    with st.expander(f"◷ История запросов ({len(st.session_state.history)})", expanded=False):
        for i, item in enumerate(st.session_state.history):
            status_mark = "✓" if item["ok"] else "✗"
            status_color = "#34c759" if item["ok"] else "#ff3b30"
            input_preview = (item["input"][:60] + "…") if len(item["input"]) > 60 else item["input"]
            input_preview = input_preview or "(пусто)"

            st.markdown(f"""
            <div style="padding: 8px 12px; margin: 4px 0; border-radius: 8px;
                 background: rgba(255,255,255,0.5); font-family: 'JetBrains Mono', monospace;
                 font-size: 12px;">
                <span style="color: {status_color};">{status_mark}</span>
                <span style="color: rgba(0,0,0,0.5);"> {item['ts']} </span>
                <span style="color: #007aff;">{item['method']} {item['endpoint']}</span>
                <span style="color: rgba(0,0,0,0.4);"> · {item['elapsed_ms']:.0f} мс · HTTP {item['status']}</span>
                <div style="color: rgba(0,0,0,0.6); margin-top: 3px;">↳ {input_preview}</div>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns([1, 1, 4])
            with cols[0]:
                if st.button("Повторить", key=f"repeat_{i}", use_container_width=True):
                    st.session_state.user_input = item["input"]
                    st.rerun()
            with cols[1]:
                if st.button("Показать", key=f"show_{i}", use_container_width=True):
                    st.session_state.last_response = item["response"]
                    st.session_state.last_status = item["status"]
                    st.session_state.last_elapsed_ms = item["elapsed_ms"]
                    st.session_state.last_error = None
                    st.rerun()

        # Экспорт всей истории
        history_json = json.dumps(st.session_state.history, ensure_ascii=False,
                                  indent=2, default=str)
        st.download_button(
            "⬇ Экспорт истории (JSON)",
            data=history_json,
            file_name=f"c2_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


# ============== СИСТЕМНЫЙ ЛОГ ==============
if st.session_state.system_log:
    with st.expander(f"◈ Системный лог ({len(st.session_state.system_log)})", expanded=False):
        log_text = "\n".join(
            f"[{entry['ts']}] [{entry['level'].upper():4}] {entry['msg']}"
            for entry in st.session_state.system_log
        )
        # st.code даёт кнопку копирования всего лога
        st.code(log_text, language="log")
        st.download_button(
            "⬇ Скачать лог",
            data=log_text,
            file_name=f"c2_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            mime="text/plain",
        )


# ============== ФУТЕР ==============
st.markdown(f"""
<div class="glass-footer">
    R9 SYSTEM · НОД C_2 · {C2_URL.split('//')[-1]} · {'TOKEN ✓' if HF_TOKEN else 'NO TOKEN'}
</div>
""", unsafe_allow_html=True)
