import streamlit as st

from core.state import init
from core.llm.router import get_available_models
from core.llm.openai_client import OPENAI_MODELS, GEMINI_MODELS

st.set_page_config(
    page_title="설정 — LLM Excel Studio",
    page_icon="⚙️",
    layout="wide",
)

init()

st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
[data-testid="collapsedControl"] { visibility: visible !important; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid #21262d;
}
.provider-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("## ⚙️ 설정")

# ── provider ──────────────────────────────────────────────────────────────────

st.subheader("AI 모델 제공자")

PROVIDER_LABELS = {
    "ollama": "🖥 Ollama (로컬/원격 서버)",
    "openai": "🤖 OpenAI (GPT-4o 등)",
    "gemini": "✨ Google Gemini",
}

st.radio(
    "제공자",
    options=list(PROVIDER_LABELS.keys()),
    format_func=lambda p: PROVIDER_LABELS[p],
    key="provider",
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# ── per-provider config ───────────────────────────────────────────────────────

if st.session_state.provider == "ollama":
    st.subheader("🖥 Ollama 설정")
    st.caption("로컬 또는 원격 Ollama 서버에 연결합니다.")

    st.text_input(
        "서버 URL",
        key="ollama_host",
        placeholder="http://localhost:11434",
    )
    st.caption("원격 서버 예시: `http://<서버IP>:11434`")

    if st.button("🔍 모델 목록 불러오기", type="primary"):
        with st.spinner("Ollama 서버 연결 중..."):
            models = get_available_models()
        if models:
            st.session_state["_ollama_models"] = models
            st.success(f"{len(models)}개 모델 발견")
        else:
            st.error("Ollama 서버에 연결할 수 없습니다. URL을 확인하세요.")

    ollama_models = st.session_state.get("_ollama_models", [])
    if ollama_models:
        cur_idx = (
            ollama_models.index(st.session_state.selected_model)
            if st.session_state.selected_model in ollama_models
            else 0
        )
        selected = st.selectbox("모델 선택", ollama_models, index=cur_idx)
        if st.button("✅ 이 모델로 설정"):
            st.session_state.selected_model = selected
            st.success(f"모델 설정 완료: **{selected}**")

elif st.session_state.provider == "openai":
    st.subheader("🤖 OpenAI 설정")

    st.text_input(
        "API Key",
        key="openai_api_key",
        type="password",
        placeholder="sk-...",
    )

    cur_idx = (
        OPENAI_MODELS.index(st.session_state.selected_model)
        if st.session_state.selected_model in OPENAI_MODELS
        else 0
    )
    model = st.selectbox("모델", OPENAI_MODELS, index=cur_idx)

    if st.button("✅ 저장", type="primary"):
        if not st.session_state.openai_api_key:
            st.error("API Key를 입력하세요.")
        else:
            st.session_state.selected_model = model
            st.success(f"설정 완료: **{model}**")

elif st.session_state.provider == "gemini":
    st.subheader("✨ Google Gemini 설정")

    st.text_input(
        "API Key",
        key="gemini_api_key",
        type="password",
        placeholder="AIza...",
    )

    cur_idx = (
        GEMINI_MODELS.index(st.session_state.selected_model)
        if st.session_state.selected_model in GEMINI_MODELS
        else 0
    )
    model = st.selectbox("모델", GEMINI_MODELS, index=cur_idx)

    if st.button("✅ 저장", type="primary"):
        if not st.session_state.gemini_api_key:
            st.error("API Key를 입력하세요.")
        else:
            st.session_state.selected_model = model
            st.success(f"설정 완료: **{model}**")

# ── current state ─────────────────────────────────────────────────────────────

st.divider()
st.subheader("현재 설정 상태")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("제공자", PROVIDER_LABELS.get(st.session_state.provider, "-"))
with col2:
    st.metric("모델", st.session_state.selected_model or "미설정")
with col3:
    host_display = st.session_state.ollama_host if st.session_state.provider == "ollama" else "N/A"
    st.metric("서버", host_display)
