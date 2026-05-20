import streamlit as st
import ollama as _ollama

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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
[data-testid="collapsedControl"] { visibility: visible !important; }
.stApp { background: #09090b; }
[data-testid="stSidebar"] { background: #0f0f12; border-right: 1px solid #1e1e24; }
hr { border-color: #1e1e24 !important; }
[data-testid="stMetric"] {
    background: #0f0f12; border: 1px solid #1e1e24;
    border-radius: 10px; padding: 12px 16px;
}
.model-row {
    display: flex; align-items: center; justify-content: space-between;
    background: #0f0f12; border: 1px solid #27272a; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 8px;
}
.model-info { flex: 1; }
.model-name { font-weight: 600; color: #fafafa; font-size: 0.9rem; }
.model-desc { color: #71717a; font-size: 0.78rem; margin-top: 2px; }
.model-size { color: #52525b; font-size: 0.75rem; white-space: nowrap; margin-left: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown("## ⚙️ 설정")

# ── 제공자 선택 ────────────────────────────────────────────────────────────────

PROVIDER_LABELS = {
    "ollama": "🖥  Ollama (로컬/원격)",
    "openai": "🤖  OpenAI",
    "gemini": "✨  Google Gemini",
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

# ── Ollama ─────────────────────────────────────────────────────────────────────

if st.session_state.provider == "ollama":

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("서버 연결")
        st.text_input("서버 URL", key="ollama_host", placeholder="http://localhost:11434")
        st.caption("원격 서버: `http://<서버IP>:11434`")

        # 자동 로드
        if not st.session_state.get("_ollama_models"):
            with st.spinner("모델 목록 불러오는 중..."):
                fetched = get_available_models()
            if fetched:
                st.session_state["_ollama_models"] = fetched

        if st.button("🔍  연결 및 모델 목록 새로고침", type="primary", use_container_width=True):
            with st.spinner("연결 중..."):
                models = get_available_models()
            if models:
                st.session_state["_ollama_models"] = models
                st.success(f"{len(models)}개 모델 확인됨")
            else:
                st.error("연결 실패. 서버 URL을 확인하세요.")

        ollama_models = st.session_state.get("_ollama_models", [])
        if ollama_models:
            st.subheader("모델 선택")
            cur_idx = (
                ollama_models.index(st.session_state.selected_model)
                if st.session_state.selected_model in ollama_models else 0
            )
            st.caption("💬 대화 모델")
            selected = st.selectbox("대화 모델", ollama_models, index=cur_idx, label_visibility="collapsed")
            if st.button("✅  대화 모델로 설정", use_container_width=True):
                st.session_state.selected_model = selected
                st.success(f"대화 모델: **{selected}**")

            st.caption("🔧 코드 생성 모델 (파일 업로드 시 자동 적용)")
            code_model_options = ["(대화 모델과 동일)"] + ollama_models
            cur_code = st.session_state.get("code_model", "")
            code_idx = ollama_models.index(cur_code) + 1 if cur_code in ollama_models else 0
            selected_code = st.selectbox("코드 모델", code_model_options, index=code_idx, label_visibility="collapsed")
            if st.button("✅  코드 모델로 설정", use_container_width=True):
                st.session_state.code_model = "" if selected_code == "(대화 모델과 동일)" else selected_code
                st.success(f"코드 모델: **{selected_code}**")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            def _pick_list(title, picks):
                st.markdown(f"**{title}**")
                for mid, badge, reason in picks:
                    installed = any(mid in m for m in ollama_models)
                    dot = "🟢" if installed else "⚪"
                    st.markdown(
                        f'<div style="display:flex;align-items:flex-start;gap:10px;'
                        f'padding:8px 12px;margin-bottom:4px;background:#0f0f12;'
                        f'border:1px solid #27272a;border-radius:8px">'
                        f'<span style="font-size:0.8rem;margin-top:1px">{dot}</span>'
                        f'<div>'
                        f'<span style="font-size:0.85rem;font-weight:600;color:#e4e4e7">{mid}</span>'
                        f'&nbsp;<span style="font-size:0.72rem;color:#52525b">{badge}</span><br>'
                        f'<span style="font-size:0.75rem;color:#71717a">{reason}</span>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

            _pick_list("💬 대화 모델 추천", [
                ("qwen3:32b-q4_K_M",  "⭐ 현재 기본값", "한국어·추론 최강. 복잡한 질문도 정확하게 이해"),
                ("qwen3.6:35b",       "🆕 신버전",      "Qwen 3.6 MoE, 32b보다 빠르고 성능 동급 이상"),
                ("gemma4:26b",        "🌐 멀티모달",    "Google 최신. 이미지도 이해 가능, 한국어 양호"),
                ("qwen3:14b-q4_K_M",  "⚡ 경량",        "빠른 응답. 간단한 대화엔 충분"),
            ])

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            _pick_list("🔧 코드 생성 모델 추천", [
                ("qwen2.5-coder:32b", "⭐ 현재 기본값", "오픈소스 코드 벤치마크 최상위. pandas 코드 압도적 품질"),
                ("qwen2.5-coder:14b", "💡 경량",        "32b 대비 절반 크기, 빠른 코드 생성"),
                ("qwen2.5-coder:7b",  "⚡ 초경량",      "간단한 코드는 충분. 복잡한 병합 작업엔 부족"),
                ("qwen2.5:14b-instruct-q4_K_M", "🔄 범용", "코드 특화는 아니지만 지시 따르기 우수"),
            ])

    with col_right:
        st.subheader("모델 다운로드")
        st.caption("Ollama Hub에서 모델을 받아 바로 사용할 수 있습니다.")

        # 추천 모델 목록
        RECOMMENDED = [
            ("qwen3:32b",             "💬 대화 — 한국어·추론 최강",         "~20 GB"),
            ("qwen3:14b",             "💬 대화 — 경량, 빠른 응답",          "~9 GB"),
            ("qwen2.5-coder:32b",     "🔧 코드 — 오픈소스 코드 1위",        "~19 GB"),
            ("qwen2.5-coder:14b",     "🔧 코드 — 경량, 실용적 선택",        "~9 GB"),
            ("gemma4:26b",            "💬 대화 — Google 최신 멀티모달",     "~17 GB"),
            ("qwen2.5-coder:7b",      "🔧 코드 — 초경량, 간단한 작업용",    "~4 GB"),
        ]

        for model_id, desc, size in RECOMMENDED:
            already = model_id in st.session_state.get("_ollama_models", [])
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f'<div style="padding:2px 0">'
                        f'<div style="font-size:0.88rem;font-weight:600;color:#e4e4e7">{model_id}</div>'
                        f'<div style="font-size:0.75rem;color:#71717a">{desc} · {size}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    label = "✓ 보유" if already else "↓ 받기"
                    if st.button(label, key=f"pull_{model_id}", disabled=already, use_container_width=True):
                        st.session_state["_pulling"] = model_id

        st.divider()

        # 직접 입력
        st.markdown("**직접 입력**")
        custom_col, btn_col = st.columns([3, 1])
        with custom_col:
            custom = st.text_input("모델명", placeholder="예: phi3:mini", label_visibility="collapsed")
        with btn_col:
            pull_custom = st.button("↓ 받기", key="pull_custom", use_container_width=True)
        if pull_custom and custom.strip():
            st.session_state["_pulling"] = custom.strip()

        # 다운로드 실행
        pulling = st.session_state.pop("_pulling", None)
        if pulling:
            st.info(f"**{pulling}** 다운로드 중...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                client = _ollama.Client(host=st.session_state.ollama_host)
                for resp in client.pull(pulling, stream=True):
                    status = getattr(resp, "status", "")
                    completed = getattr(resp, "completed", 0) or 0
                    total = getattr(resp, "total", 0) or 0
                    if total > 0:
                        pct = min(int(completed / total * 100), 100)
                        progress_bar.progress(pct)
                        status_text.caption(f"{status} — {pct}%")
                    else:
                        status_text.caption(status)
                progress_bar.progress(100)
                status_text.empty()
                st.success(f"**{pulling}** 다운로드 완료!")
                # 모델 목록 갱신
                st.session_state["_ollama_models"] = get_available_models()
                st.rerun()
            except Exception as e:
                st.error(f"다운로드 실패: {e}")

# ── OpenAI ─────────────────────────────────────────────────────────────────────

elif st.session_state.provider == "openai":
    st.subheader("🤖 OpenAI 설정")
    st.text_input("API Key", key="openai_api_key", type="password", placeholder="sk-...")
    cur_idx = OPENAI_MODELS.index(st.session_state.selected_model) if st.session_state.selected_model in OPENAI_MODELS else 0
    model = st.selectbox("모델", OPENAI_MODELS, index=cur_idx)
    if st.button("✅ 저장", type="primary"):
        if not st.session_state.openai_api_key:
            st.error("API Key를 입력하세요.")
        else:
            st.session_state.selected_model = model
            st.success(f"설정 완료: **{model}**")

# ── Gemini ─────────────────────────────────────────────────────────────────────

elif st.session_state.provider == "gemini":
    st.subheader("✨ Google Gemini 설정")
    st.text_input("API Key", key="gemini_api_key", type="password", placeholder="AIza...")
    cur_idx = GEMINI_MODELS.index(st.session_state.selected_model) if st.session_state.selected_model in GEMINI_MODELS else 0
    model = st.selectbox("모델", GEMINI_MODELS, index=cur_idx)
    if st.button("✅ 저장", type="primary"):
        if not st.session_state.gemini_api_key:
            st.error("API Key를 입력하세요.")
        else:
            st.session_state.selected_model = model
            st.success(f"설정 완료: **{model}**")

# ── 현재 상태 ──────────────────────────────────────────────────────────────────

st.divider()
st.subheader("현재 설정")
c1, c2, c3 = st.columns(3)
c1.metric("제공자", PROVIDER_LABELS.get(st.session_state.provider, "-").split("  ")[-1])
c2.metric("모델", st.session_state.selected_model or "미설정")
c3.metric("서버", st.session_state.ollama_host if st.session_state.provider == "ollama" else "N/A")
