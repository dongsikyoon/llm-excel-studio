import streamlit as st

_DEFAULTS: dict = {
    "provider": "ollama",
    "ollama_host": "http://localhost:11434",
    "openai_api_key": "",
    "gemini_api_key": "",
    "selected_model": "qwen3:14b-q4_K_M",
    "persona": "analyst",
    "messages": [],
    "execution_results": {},
}


def init() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
