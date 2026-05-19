import html
import queue
import re
import threading
from datetime import datetime

import streamlit as st

from core.state import init
from core.llm.router import get_client
from core.prompt.enhancer import build_system_prompt
from core.prompt.personas import PERSONAS
from core.files.context import build_file_context
from core.files.manager import RESULT_DIR, list_files, list_results
from core.executor.sandbox import execute, ExecutionResult

st.set_page_config(
    page_title="LLM Excel Studio",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

init()

# ── custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* 햄버거 메뉴·푸터만 숨기고, 사이드바 토글은 살려둠 */
#MainMenu, footer {visibility: hidden;}
/* 사이드바 접혔을 때 열기 버튼은 항상 보이도록 */
[data-testid="collapsedControl"] { visibility: visible !important; }

/* sidebar branding */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* persona radio */
[data-testid="stRadio"] label {
    padding: 6px 10px;
    border-radius: 8px;
    transition: background 0.15s;
}
[data-testid="stRadio"] label:hover { background: #21262d; }

/* assistant bubble (left) */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    margin-bottom: 4px;
    border: 1px solid #21262d;
}

/* user bubble (right) */
.user-row {
    display: flex;
    justify-content: flex-end;
    margin: 6px 0 12px 0;
}
.user-bubble {
    background: #1f6feb;
    color: #ffffff;
    padding: 10px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 70%;
    word-wrap: break-word;
    white-space: pre-wrap;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* execute button */
button[kind="secondary"] {
    border: 1px solid #238636 !important;
    color: #3fb950 !important;
    background: transparent !important;
    border-radius: 6px !important;
}
button[kind="secondary"]:hover {
    background: #238636 !important;
    color: #fff !important;
}

/* download button */
button[kind="secondary"][data-testid="stDownloadButton"] {
    border: 1px solid #1f6feb !important;
    color: #58a6ff !important;
}

/* status chip */
.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #8b949e;
    margin: 2px 0;
}
.status-chip.online { border-color: #238636; color: #3fb950; }
.status-chip.warn   { border-color: #9e6a03; color: #d29922; }

/* app title gradient */
.app-title {
    font-size: 1.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, #58a6ff 0%, #bc8cff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_code(text: str) -> list[str]:
    return re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)


def _ai_fix_code(failed_code: str, error: str) -> str | None:
    """오류난 코드를 LLM에 보내 수정된 코드를 받아옴."""
    client = get_client()
    if not client:
        return None
    messages = [
        {
            "role": "system",
            "content": build_system_prompt(
                persona_key=st.session_state.persona,
                file_context=build_file_context(),
            ),
        },
        {
            "role": "user",
            "content": (
                "코드 실행 중 오류가 발생했습니다. 원인을 파악하고 수정된 코드를 작성해주세요.\n\n"
                f"**오류:**\n```\n{error}\n```\n\n"
                f"**실패한 코드:**\n```python\n{failed_code}\n```"
            ),
        },
    ]
    try:
        response = "".join(client.chat_stream(messages))
        codes = _extract_code(response)
        return codes[0] if codes else None
    except Exception:
        return None


def _execute_with_retry(code: str, max_retries: int = 5) -> tuple[ExecutionResult, int]:
    """최대 max_retries 회 자동 재시도. (결과, 시도 횟수) 반환."""
    for attempt in range(1, max_retries + 1):
        result = execute(code)
        if result.success:
            return result, attempt
        if attempt < max_retries:
            fixed = _ai_fix_code(code, result.error)
            if not fixed:
                break
            code = fixed
    return result, attempt


def _export_md() -> str:
    lines = [
        "# LLM Excel Studio 채팅 내역",
        f"_{datetime.now().strftime('%Y-%m-%d %H:%M')}_\n",
    ]
    for msg in st.session_state.messages:
        role = "**사용자**" if msg["role"] == "user" else "**AI**"
        lines.append(f"{role}\n\n{msg['content']}")
    return "\n\n---\n\n".join(lines)


# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="app-title">🎯 LLM Excel Studio</div>', unsafe_allow_html=True)
    st.caption("AI 기반 엑셀 자동화 스튜디오")

    st.divider()

    # model status & quick selector
    provider = st.session_state.get("provider", "ollama")
    model = st.session_state.get("selected_model", "")
    provider_icon = {"ollama": "🖥", "openai": "🤖", "gemini": "✨"}.get(provider, "🔌")
    provider_label = {"ollama": "Ollama", "openai": "OpenAI", "gemini": "Gemini"}.get(provider, provider)

    st.markdown(f"**{provider_icon} 모델** <span style='color:#8b949e;font-size:0.8rem'>({provider_label})</span>",
                unsafe_allow_html=True)

    if provider == "ollama":
        from core.llm.router import get_available_models
        # 캐시 없으면 자동 로드
        if not st.session_state.get("_ollama_models"):
            fetched = get_available_models()
            if fetched:
                st.session_state["_ollama_models"] = fetched

        ollama_models = st.session_state.get("_ollama_models", [])
        if ollama_models:
            cur_idx = ollama_models.index(model) if model in ollama_models else 0
            st.selectbox(
                "모델 선택",
                ollama_models,
                index=cur_idx,
                key="selected_model",
                label_visibility="collapsed",
            )
            if st.button("🔄", help="모델 목록 새로고침", use_container_width=False):
                st.session_state["_ollama_models"] = get_available_models()
                st.rerun()
        else:
            st.warning("Ollama 연결 실패")
    else:
        # OpenAI / Gemini — 모델명만 표시, 변경은 Settings에서
        if model:
            st.markdown(
                f'<div class="status-chip online">{model}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-chip warn">⚠ 모델 미설정</div>',
                unsafe_allow_html=True,
            )
            st.caption("⚙️ Settings에서 API Key 및 모델 설정")

    # file / result count
    n_files = len(list_files())
    n_results = len(list_results())
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f'<div class="status-chip">📄 파일 {n_files}개</div>',
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f'<div class="status-chip">📊 결과 {n_results}개</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # persona — key= 로 session_state 직접 바인딩 (더블클릭 방지)
    st.markdown("**페르소나**")
    st.radio(
        "persona",
        options=list(PERSONAS.keys()),
        format_func=lambda k: f"{PERSONAS[k].icon} {PERSONAS[k].name}",
        key="persona",
        label_visibility="collapsed",
    )
    st.caption(PERSONAS[st.session_state.persona].description)

    st.divider()

    # actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 새 채팅", use_container_width=True):
            st.session_state.messages = []
            st.session_state.execution_results = {}
            st.rerun()
    with col2:
        if st.session_state.messages:
            st.download_button(
                "💾 MD",
                data=_export_md(),
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True,
            )


# ── quick examples (항상 상단 고정) ──────────────────────────────────────────

cols = st.columns(3)
examples = [
    ("📂 파일 통합", "5개 엑셀 파일을 하나로 합치고 동일 항목은 평균으로 계산해줘"),
    ("📊 데이터 분석", "업로드한 파일에서 비목별 집행률을 계산해줘"),
    ("🔍 비교 분석", "이월예산과 당해예산을 비교해서 잔액이 큰 항목 순으로 정렬해줘"),
]
for col, (icon_title, prompt_text) in zip(cols, examples):
    with col:
        if st.button(icon_title, use_container_width=True, key=f"ex_{icon_title}", help=prompt_text):
            st.session_state["_queued_prompt"] = prompt_text
            st.rerun()

st.divider()

# ── chat messages ─────────────────────────────────────────────────────────────


def _render_code_controls(idx: int, content: str) -> None:
    result = st.session_state.execution_results.get(idx)

    if result is not None:
        if result.success:
            if result.output:
                st.code(result.output, language="")
            if result.result_df is not None:
                _safe = result.result_df.copy()
                for c in _safe.select_dtypes(include="object").columns:
                    _safe[c] = _safe[c].astype(str)
                st.dataframe(_safe, width="stretch")
            for fname in result.saved_files:
                fpath = RESULT_DIR / fname
                if fpath.exists():
                    st.download_button(
                        f"⬇ {fname} 다운로드",
                        data=fpath.read_bytes(),
                        file_name=fname,
                        key=f"dl_{fname}_{idx}",
                    )
            st.success("✅ 실행 완료")
        else:
            st.error(f"❌ 오류\n\n{result.error}")
            codes = _extract_code(content)
            if codes and st.button("🔄 AI 자동 수정", key=f"autofix_{idx}"):
                fix_prompt = (
                    "코드 실행 중 오류가 발생했습니다. 원인을 파악하고 수정된 코드를 작성해주세요.\n\n"
                    f"**오류 내용:**\n```\n{result.error}\n```\n\n"
                    f"**실패한 코드:**\n```python\n{codes[0]}\n```"
                )
                st.session_state["_queued_prompt"] = fix_prompt
                st.rerun()
        return

    if _extract_code(content):
        if st.button("▶ 코드 실행", key=f"exec_{idx}", type="secondary"):
            with st.spinner("실행 중... (최대 5회 자동 재시도)"):
                r, attempts = _execute_with_retry(_extract_code(content)[0])
            if not r.success:
                r.error = f"[{attempts}회 시도 후 실패]\n\n{r.error}"
            st.session_state.execution_results[idx] = r
            st.rerun()


def _user_bubble(text: str) -> None:
    st.markdown(
        f'<div class="user-row"><div class="user-bubble">{html.escape(text)}</div></div>',
        unsafe_allow_html=True,
    )


for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        _user_bubble(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
            _render_code_controls(idx, msg["content"])


# ── input ─────────────────────────────────────────────────────────────────────

# 버튼으로 큐잉된 프롬프트 또는 직접 입력
_queued = st.session_state.pop("_queued_prompt", None)
prompt = st.chat_input("메시지를 입력하세요...") or _queued

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    _user_bubble(prompt)

    client = get_client()
    if not client:
        provider = st.session_state.get("provider", "?")
        model = st.session_state.get("selected_model", "")
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                f"⚠️ 모델이 설정되지 않았습니다.\n\n"
                f"- 현재 제공자: `{provider}`\n"
                f"- 현재 모델: `{model or '(없음)'}`\n\n"
                f"**⚙️ Settings** 페이지에서 모델을 선택하세요."
            ),
        })
        st.rerun()
    else:
        system_prompt = build_system_prompt(
            persona_key=st.session_state.persona,
            file_context=build_file_context(),
        )
        llm_messages = [
            {"role": "system", "content": system_prompt},
            *st.session_state.messages,
        ]
        stop_event = threading.Event()
        token_queue: queue.Queue = queue.Queue()

        def _do_stream():
            try:
                for token in client.chat_stream(llm_messages):
                    if stop_event.is_set():
                        break
                    token_queue.put(("token", token))
                token_queue.put(("done", None))
            except Exception as exc:
                token_queue.put(("error", str(exc)))

        threading.Thread(target=_do_stream, daemon=True).start()

        with st.chat_message("assistant"):
            status_ph = st.empty()
            content_ph = st.empty()
            stop_ph = st.empty()

            status_ph.markdown("⏳ _생성 중..._")
            _stop_key = f"_stop_{len(st.session_state.messages)}"
            if stop_ph.button("⏹ 중지", key=_stop_key):
                stop_event.set()

            full = ""
            stopped = False

            while True:
                try:
                    kind, value = token_queue.get(timeout=60)
                except queue.Empty:
                    full = full or "_(시간 초과)_"
                    break
                if kind == "token":
                    full += value
                    status_ph.empty()
                    content_ph.markdown(full + "▌")
                elif kind == "done":
                    break
                elif kind == "error":
                    full = f"❌ **LLM 오류**\n\n```\n{value}\n```"
                    break
                if stop_event.is_set():
                    stopped = True
                    break

            stop_ph.empty()
            suffix = "\n\n_(중지됨)_" if stopped else ""
            content_ph.markdown((full or "_응답 없음_") + suffix)

        st.session_state.messages.append({
            "role": "assistant",
            "content": (full or "_응답 없음_") + suffix,
        })
        st.rerun()
