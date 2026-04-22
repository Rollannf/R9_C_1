import streamlit as st
import requests
import os
import time

# ============== SCI-FI CONFIG ==============
C2_URL = "https://rollannf-r9-c-2.hf.space"
HF_TOKEN = os.environ.get("HF_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# ============== CUSTOM CSS ==============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

/* Base sci-fi theme */
.stApp {
    background: #050508;
    background-image: 
        linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    font-family: 'JetBrains Mono', monospace;
}

/* Neon text effects */
h1, h2, h3 {
    color: #00f0ff !important;
    text-shadow: 0 0 10px rgba(0, 240, 255, 0.5), 0 0 20px rgba(0, 240, 255, 0.3);
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: 2px;
    text-transform: uppercase;
}

/* Cyberpunk button styling */
.stButton > button {
    background: transparent !important;
    border: 2px solid #00f0ff !important;
    color: #00f0ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    border-radius: 0 !important;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.3), inset 0 0 10px rgba(0, 240, 255, 0.1);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.stButton > button:hover {
    background: rgba(0, 240, 255, 0.1) !important;
    box-shadow: 0 0 20px rgba(0, 240, 255, 0.6), inset 0 0 20px rgba(0, 240, 255, 0.2);
    text-shadow: 0 0 10px #00f0ff;
}

/* Corner brackets for buttons */
.stButton > button::before,
.stButton > button::after {
    content: '';
    position: absolute;
    width: 8px;
    height: 8px;
    border: 2px solid #ff00ff;
    transition: all 0.3s ease;
}

.stButton > button::before {
    top: -2px;
    left: -2px;
    border-right: none;
    border-bottom: none;
}

.stButton > button::after {
    bottom: -2px;
    right: -2px;
    border-left: none;
    border-top: none;
}

/* Input fields - terminal style */
.stTextInput > div > div > input {
    background: rgba(0, 20, 30, 0.8) !important;
    border: 1px solid #00f0ff !important;
    color: #00f0ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    box-shadow: 0 0 5px rgba(0, 240, 255, 0.2), inset 0 0 10px rgba(0, 240, 255, 0.05);
    border-radius: 0 !important;
}

.stTextInput > div > div > input:focus {
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.4), inset 0 0 15px rgba(0, 240, 255, 0.1);
    border-color: #ff00ff !important;
}

/* Success/Error messages with sci-fi styling */
.stSuccess {
    background: rgba(0, 255, 136, 0.1) !important;
    border: 1px solid #00ff88 !important;
    border-left: 4px solid #00ff88 !important;
    color: #00ff88 !important;
    font-family: 'JetBrains Mono', monospace !important;
    box-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
    border-radius: 0 !important;
}

.stError {
    background: rgba(255, 0, 85, 0.1) !important;
    border: 1px solid #ff0055 !important;
    border-left: 4px solid #ff0055 !important;
    color: #ff0055 !important;
    font-family: 'JetBrains Mono', monospace !important;
    box-shadow: 0 0 10px rgba(255, 0, 85, 0.2);
    border-radius: 0 !important;
}

/* JSON output styling */
.stJson {
    background: rgba(0, 10, 20, 0.9) !important;
    border: 1px solid #00f0ff !important;
    color: #00f0ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);
    border-radius: 0 !important;
}

/* Scrollbar sci-fi */
::-webkit-scrollbar {
    width: 8px;
    background: #050508;
}

::-webkit-scrollbar-thumb {
    background: #00f0ff;
    box-shadow: 0 0 5px #00f0ff;
}

/* Remove default padding */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* Divider line */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00f0ff, #ff00ff, transparent);
    margin: 2rem 0;
}

/* Status indicator pulse animation */
@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 5px #00ff88; }
    50% { opacity: 0.5; box-shadow: 0 0 20px #00ff88; }
}

.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #00ff88;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
    box-shadow: 0 0 10px #00ff88;
}

/* Scanline effect overlay */
.scanlines {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(
        to bottom,
        transparent 50%,
        rgba(0, 0, 0, 0.1) 50%
    );
    background-size: 100% 4px;
    pointer-events: none;
    z-index: 9999;
    opacity: 0.3;
}

/* Glitch text effect for title */
.glitch {
    position: relative;
}

.glitch::before,
.glitch::after {
    content: attr(data-text);
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}

.glitch::before {
    left: 2px;
    text-shadow: -1px 0 #ff00ff;
    clip: rect(24px, 550px, 90px, 0);
    animation: glitch-anim-1 3s infinite linear alternate-reverse;
}

.glitch::after {
    left: -2px;
    text-shadow: -1px 0 #00f0ff;
    clip: rect(85px, 550px, 140px, 0);
    animation: glitch-anim-2 2.5s infinite linear alternate-reverse;
}

@keyframes glitch-anim-1 {
    0% { clip: rect(20px, 9999px, 15px, 0); }
    20% { clip: rect(80px, 9999px, 90px, 0); }
    40% { clip: rect(10px, 9999px, 60px, 0); }
    60% { clip: rect(50px, 9999px, 30px, 0); }
    80% { clip: rect(90px, 9999px, 100px, 0); }
    100% { clip: rect(30px, 9999px, 10px, 0); }
}

@keyframes glitch-anim-2 {
    0% { clip: rect(60px, 9999px, 70px, 0); }
    20% { clip: rect(10px, 9999px, 50px, 0); }
    40% { clip: rect(90px, 9999px, 100px, 0); }
    60% { clip: rect(30px, 9999px, 20px, 0); }
    80% { clip: rect(70px, 9999px, 80px, 0); }
    100% { clip: rect(40px, 9999px, 60px, 0); }
}

/* Corner brackets for containers */
.corner-box {
    position: relative;
    border: 1px solid rgba(0, 240, 255, 0.3);
    padding: 20px;
    margin: 10px 0;
    background: rgba(0, 20, 30, 0.3);
}

.corner-box::before,
.corner-box::after,
.corner-box > .corner-tl,
.corner-box > .corner-br {
    content: '';
    position: absolute;
    width: 15px;
    height: 15px;
    border: 2px solid #00f0ff;
}

.corner-box::before {
    top: -2px;
    left: -2px;
    border-right: none;
    border-bottom: none;
}

.corner-box::after {
    bottom: -2px;
    right: -2px;
    border-left: none;
    border-top: none;
}

/* Timestamp styling */
.timestamp {
    color: #ff00ff;
    font-size: 0.8em;
    opacity: 0.7;
}

/* Hex decoration */
.hex-deco {
    color: rgba(0, 240, 255, 0.3);
    font-size: 0.7em;
    letter-spacing: 2px;
}
</style>

<div class="scanlines"></div>
""", unsafe_allow_html=True)

# ============== HEADER ==============
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div class="hex-deco">0x52 0x39 0x2D 0x43 0x32 0x2D 0x49 0x4E 0x54 0x45 0x52 0x46 0x41 0x43 0x45</div>
        <h1 class="glitch" data-text="R9 — ЦЕНТРАЛЬНЫЙ ИНТЕРФЕЙС">R9 — ЦЕНТРАЛЬНЫЙ ИНТЕРФЕЙС</h1>
        <div class="timestamp">SYS.TIME: {} | NODE: C_2 | SECURE_CONN: TRUE</div>
    </div>
    """.format(time.strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

st.markdown('<hr>', unsafe_allow_html=True)

# ============== STATUS SECTION ==============
st.markdown("""
<div class="corner-box">
    <div style="color: #00f0ff; font-size: 0.9em; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px;">
        ■ СИСТЕМНЫЙ МОНИТОРИНГ
    </div>
""", unsafe_allow_html=True)

if st.button("▶ ПРОВЕРИТЬ СТАТУС C_2"):
    try:
        r = requests.get(f"{C2_URL}/health", headers=HEADERS)
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 10px 0;">
            <span class="status-dot"></span>
            <span style="color: #00ff88; font-family: 'JetBrains Mono', monospace;">
                [OK] C_2 ОТВЕЧАЕТ: {r.json()}
            </span>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
        <div style="border-left: 3px solid #ff0055; padding-left: 10px; margin: 10px 0; color: #ff0055;">
            [ERR] ОШИБКА ПОДКЛЮЧЕНИЯ: {e}
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<hr>', unsafe_allow_html=True)

# ============== REQUEST SECTION ==============
st.markdown("""
<div class="corner-box">
    <div style="color: #00f0ff; font-size: 0.9em; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px;">
        ■ ПЕРЕДАЧА ДАННЫХ
    </div>
""", unsafe_allow_html=True)

user_input = st.text_input("ВВЕДИТЕ ЗАПРОС ДЛЯ C_2:", placeholder="> _")

if st.button("▶ ОТПРАВИТЬ"):
    if user_input:
        st.markdown(f"""
        <div style="color: rgba(0, 240, 255, 0.5); font-size: 0.8em; margin: 5px 0;">
            > TX: {user_input}<br>
            > ENCRYPTING... [AES-256]<br>
            > ROUTING... [NODE_C2_HF_SPACE]
        </div>
        """, unsafe_allow_html=True)
        
        try:
            r = requests.post(
                f"{C2_URL}/request",
                json={"query": user_input},
                headers=HEADERS
            )
            st.markdown("""
            <div style="color: #00ff88; font-size: 0.8em; margin: 5px 0;">
                > RX: SUCCESS<br>
                > DECRYPTING RESPONSE...
            </div>
            """, unsafe_allow_html=True)
            st.json(r.json())
        except Exception as e:
            st.markdown(f"""
            <div style="border-left: 3px solid #ff0055; padding-left: 10px; margin: 10px 0; color: #ff0055;">
                [ERR] СБОЙ ПЕРЕДАЧИ: {e}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="color: #ffaa00; font-size: 0.8em; margin: 5px 0;">
            [WARN] ПУСТОЙ ЗАПРОС — ОТМЕНА ОПЕРАЦИИ
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============== FOOTER ==============
st.markdown("""
<div style="position: fixed; bottom: 0; left: 0; right: 0; text-align: center; padding: 10px; 
     background: rgba(5, 5, 8, 0.9); border-top: 1px solid rgba(0, 240, 255, 0.3);">
    <span style="color: rgba(0, 240, 255, 0.5); font-size: 0.7em; font-family: 'JetBrains Mono', monospace;">
        R9 SYSTEM v2.077 | SECURE CHANNEL | HF_SPACE NODE
    </span>
</div>
""", unsafe_allow_html=True)
