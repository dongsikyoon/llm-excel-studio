import streamlit as st

_DEFAULTS: dict = {
    "provider": "ollama",
    "ollama_host": "http://localhost:11434",
    "openai_api_key": "",
    "gemini_api_key": "",
    "selected_model": "qwen3:32b-q4_K_M",
    "code_model": "qwen2.5-coder:32b",
    "current_chat_id": "",
    "messages": [],
    "execution_results": {},
    "final_codes": {},          # 재시도 후 최종 실행된 코드
}


def init() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
