import streamlit as st
from .base import LLMClient
from .ollama_client import OllamaClient
from .openai_client import CloudClient, GEMINI_BASE_URL, OPENAI_MODELS, GEMINI_MODELS


def _build_client(model: str) -> LLMClient | None:
    if not model:
        return None
    provider = st.session_state.get("provider", "ollama")
    if provider == "ollama":
        host = st.session_state.get("ollama_host", "http://localhost:11434")
        return OllamaClient(host=host, model=model)
    if provider == "openai":
        key = st.session_state.get("openai_api_key", "")
        return CloudClient(api_key=key, model=model) if key else None
    if provider == "gemini":
        key = st.session_state.get("gemini_api_key", "")
        return CloudClient(api_key=key, model=model, base_url=GEMINI_BASE_URL) if key else None
    return None


def get_client() -> LLMClient | None:
    """대화용 기본 모델."""
    return _build_client(st.session_state.get("selected_model", ""))


def get_code_client() -> LLMClient | None:
    """코드 생성 전용 모델. 미설정 시 기본 모델 사용."""
    code_model = st.session_state.get("code_model", "").strip()
    model = code_model or st.session_state.get("selected_model", "")
    return _build_client(model)


def get_available_models() -> list[str]:
    provider = st.session_state.get("provider", "ollama")
    if provider == "ollama":
        host = st.session_state.get("ollama_host", "http://localhost:11434")
        client = OllamaClient(host=host, model="")
        return client.list_models()
    if provider == "openai":
        return OPENAI_MODELS
    if provider == "gemini":
        return GEMINI_MODELS
    return []
