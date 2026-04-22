import streamlit as st
import requests
import os
import time

# ============== SCI-FI MINIMAL CONFIG ==============
C2_URL = "https://rollannf-r9-c-2.hf.space"
HF_TOKEN = os.environ.get("HF_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# ============== CUSTOM CSS ==============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600&family=SF+Mono:wght@400;500&display=swap');

/* Base — clean sci-fi white */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 50%, #f0f4f8 100%);
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Soft grid overlay */
.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        radial-gradient(circle at 1px 1px, rgba(0, 150, 255, 0.08) 1px, transparent 0);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* Typography */
h1, h2, h3 {
    color: #1a1a2e !important;
    font-family: 'SF Pro Display', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.5px;
}

/* Glassmorphism buttons */
.stButton > button {
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    color: #007aff !important;
    font-family: 'SF Pro Display', sans-serif !important;
    font-weight: 500 !important;
    font-size: 15px !important;
    border-radius: 16px !important;
    padding: 12px 24px !important;
    box-shadow: 
        0 4px 24px rgba(0, 122, 255, 0.15),
        0 1px 3px rgba(0, 0, 0, 0.05),
        inset 0 1px 0 rgba(255, 255, 255, 0.6);
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    position: relative;
    overflow: hidden;
}

.stButton > button:hover {
    background: rgba(255, 255, 255, 0.9) !important;
    box-shadow: 
        0 8px 32px rgba(0, 122, 255, 0.25),
        0 2px 8px rgba(0, 0, 0, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0) scale(0.98);
    box-shadow: 
        0 2px 12px rgba(0, 122, 255, 0.2),
        inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* Soft neon glow on buttons */
.stButton > button::after {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(135deg, rgba(0, 122, 255, 0.3), rgba(88, 86, 214, 0.3));
    border-radius: 18px;
    z-index: -1;
    opacity: 0;
    transition: opacity 0.4s ease;
    filter: blur(8px);
}

.stButton > button:hover::after {
    opacity: 1;
}

/* Glass input fields */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(0, 122, 255, 0.15) !important;
    color: #1a1a2e !important;
    font-family: 'SF Pro Display', sans-serif !important;
    font-size: 16px !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    box-shadow: 
        0 2px 12px rgba(0, 0, 0, 0.04),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus {
    background: rgba(255, 255, 255, 0.85) !important;
    border-color: rgba(0, 122, 255, 0.4) !important;
    box-shadow: 
        0 4px 20px rgba(0, 122, 255, 0.15),
        0 0 0 4px rgba(0, 122, 255, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.9);
    outline: none !important;
}

/* Placeholder styling */
.stTextInput > div > div > input::placeholder {
    color: rgba(0, 0, 0, 0.3) !important;
    font-weight: 400;
}

/* Success — soft sci-fi green */
.stSuccess {
    background: rgba(52, 199, 89, 0.08) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(52, 199, 89, 0.2) !important;
    border-radius: 16px !important;
    color: #34c759 !important;
    font-family: 'SF Mono', monospace !important;
    font-size: 14px !important;
    box-shadow: 
        0 4px 16px rgba(52, 199, 89, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

/* Error — soft sci-fi red */
.stError {
    background: rgba(255, 59, 48, 0.08) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 59, 48, 0.2) !important;
    border-radius: 16px !important;
    color: #ff3b30 !important;
    font-family: 'SF Mono', monospace !important;
    font-size: 14px !important;
    box-shadow: 
        0 4px 16px rgba(255, 59, 48, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

/* JSON output — glass card */
.stJson {
    background: rgba(255, 255, 255, 0.5) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.6) !important;
    border-radius: 20px !important;
    color: #1a1a2e !important;
    font-family: 'SF Mono', monospace !important;
    font-size: 13px !important;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.06),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
    padding: 20px !important;
}

/* Scrollbar — minimal */
::-webkit-scrollbar {
    width: 6px;
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(0, 122, 255, 0.3);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 122, 255, 0.5);
}

/* Container padding */
.block-container {
    padding-top: 3rem !important;
    padding-bottom: 3rem !important;
    max-width: 680px !important;
}

/* Glass card component */
.glass-card {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(30px) saturate(150%);
    -webkit-backdrop-filter: blur(30px) saturate(150%);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 24px;
    padding: 32px;
    margin: 20px 0;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.06),
        0 1px 3px rgba(0, 0, 0, 0.04),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
    position: relative;
    overflow: hidden;
}

/* Subtle gradient accent line */
.glass-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 20%;
    right: 20%;
    height: 2px;
    background: linear-gradient(90deg, 
        transparent, 
        rgba(0, 122, 255, 0.4), 
        rgba(88, 86, 214, 0.4), 
        transparent
    );
    border-radius: 0 0 2px 2px;
}

/* Section label */
.section-label {
    color: rgba(0, 122, 255, 0.7);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 16px;
    font-family: 'SF Mono', monospace;
}

/* Status indicator — soft pulse */
@keyframes softPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(0.95); }
}

.status-ring {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #34c759;
    box-shadow: 0 0 0 4px rgba(52, 199, 89, 0.2);
    animation: softPulse 3s ease-in-out infinite;
    margin-right: 10px;
}

/* Mono data display */
.data-mono {
    font-family: 'SF Mono', monospace;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.6);
    line-height: 1.6;
}

/* Subtle floating orbs for depth */
.orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.4;
    pointer-events: none;
    z-index: 0;
}

.orb-1 {
    width: 400px;
    height: 400px;
    background: rgba(0, 122, 255, 0.15);
    top: -100px;
    right: -100px;
}

.orb-2 {
    width: 300px;
    height: 300px;
    background: rgba(88, 86, 214, 0.1);
    bottom: -50px;
    left: -50px;
}

/* Footer */
.glass-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-top: 1px solid rgba(255, 255, 255, 0.8);
    padding: 12px 24px;
    text-align: center;
    z-index: 100;
}

.glass-footer span {
    color: rgba(0, 0, 0, 0.4);
    font-size: 12px;
    font-family: 'SF Mono', monospace;
    letter-spacing: 1px;
}
</style>

<!-- Floating orbs for ambient depth -->
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
""", unsafe_allow_html=True)

# ============== HEADER ==============
st.markdown("""
<div style="text-align: center; margin: 2rem 0 3rem 0; position: relative; z-index: 1;">
    <div style="color: rgba(0, 122, 255, 0.5); font-size: 12px; font-family: 'SF Mono', monospace; 
         letter-spacing: 3px; margin-bottom: 12px; text-transform: uppercase;">
        System Interface v2.0
    </div>
    <h1 style="font-size: 32px; font-weight: 600; color: #1a1a2e; margin: 0; letter-spacing: -1px;">
        R9 Central
    </h1>
    <div style="color: rgba(0, 0, 0, 0.4); font-size: 14px; margin-top: 8px; font-weight: 400;">
        Neural Link Established · Secure Channel
    </div>
</div>
""", unsafe_allow_html=True)

# ============== STATUS SECTION ==============
st.markdown("""
<div class="glass-card">
    <div class="section-label">System Health</div>
""", unsafe_allow_html=True)

if st.button("Check C_2 Status"):
    try:
        r = requests.get(f"{C2_URL}/health", headers=HEADERS)
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 12px 0;">
            <div class="status-ring"></div>
            <span style="color: #34c759; font-family: 'SF Mono', monospace; font-size: 14px;">
                Online · Response: {r.json()}
            </span>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 12px 0;">
            <div style="width: 10px; height: 10px; border-radius: 50%; background: #ff3b30; 
                 box-shadow: 0 0 0 4px rgba(255, 59, 48, 0.2); margin-right: 10px;"></div>
            <span style="color: #ff3b30; font-family: 'SF Mono', monospace; font-size: 14px;">
                Offline · {e}
            </span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============== REQUEST SECTION ==============
st.markdown("""
<div class="glass-card">
    <div class="section-label">Data Transmission</div>
""", unsafe_allow_html=True)

user_input = st.text_input("Enter command for C_2:", placeholder="Type query...")

if st.button("Transmit"):
    if user_input:
        st.markdown(f"""
        <div class="data-mono" style="margin: 12px 0; color: rgba(0, 122, 255, 0.7);">
            › Encoding payload...<br>
            › Routing to C_2 node...<br>
            › Awaiting response...
        </div>
        """, unsafe_allow_html=True)
        
        try:
            r = requests.post(
                f"{C2_URL}/request",
                json={"query": user_input},
                headers=HEADERS
            )
            st.markdown("""
            <div class="data-mono" style="margin: 8px 0; color: #34c759;">
                › Transmission complete
            </div>
            """, unsafe_allow_html=True)
            st.json(r.json())
        except Exception as e:
            st.markdown(f"""
            <div class="data-mono" style="margin: 8px 0; color: #ff3b30;">
                › Connection failed: {e}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="data-mono" style="margin: 8px 0; color: #ff9500;">
            › No payload detected — operation cancelled
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============== FOOTER ==============
st.markdown("""
<div class="glass-footer">
    <span>R9 SYSTEM · HF SPACE NODE · SECURE</span>
</div>
""", unsafe_allow_html=True)

# Spacer for fixed footer
st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)
