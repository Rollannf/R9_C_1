import streamlit as st
import requests
import os

C2_URL = "https://rollannf-r9-c-2.hf.space"
HF_TOKEN = os.environ.get("HF_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

st.title("R9 — Центральный интерфейс")

if st.button("Проверить статус C_2"):
    try:
        r = requests.get(f"{C2_URL}/health", headers=HEADERS)
        st.success(f"C_2 отвечает: {r.json()}")
    except Exception as e:
        st.error(f"Ошибка подключения: {e}")

user_input = st.text_input("Отправить запрос в C_2")
if st.button("Отправить"):
    try:
        r = requests.post(
            f"{C2_URL}/request",
            json={"query": user_input},
            headers=HEADERS
        )
        st.json(r.json())
    except Exception as e:
        st.error(f"Ошибка: {e}")
