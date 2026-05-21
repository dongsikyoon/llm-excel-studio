import html
import json
import queue
import re
import threading
from datetime import datetime

import streamlit as st

from core.state import init
from core.llm.router import get_client, get_code_client
from core.prompt.enhancer import build_system_prompt
from core.files.context import build_file_context
from core.files.manager import RESULT_DIR, list_files, list_results
from core.files.history import (
    save as save_history, load as load_history, delete as delete_history,
    list_chats, new_id,
)
from core.executor.sandbox import execute, ExecutionResult

st.set_page_config(
    page_title="LLM Excel Studio",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

init()

# ── fixed 퀵 프롬프트 상단바 (iframe → 메인 페이지 DOM 주입) ─────────────────

_QUICK_PROMPTS = [
    ("📂", "예실대비표 파일 통합", """업로드된 예실대비표 파일들을 하나로 통합해줘. 아래 규칙을 지켜줘.

1. 행 분류 (각 파일에서 먼저 분리):
   - 요약 행: 비목분류 값이 '내부흡수액', '외부유출액', '내부흡수', '외부유출', '합 계', '합계' 중 하나인 행
   - 소계 행: 비용명 값이 정확히 '소계'인 행
   - 일반 항목: 위 두 경우가 아닌 나머지 행

2. 일반 항목끼리 합산:
   - (비목분류, 비용명, 비용명_내용) 세 컬럼을 기준(key)으로 groupby 후 수치 컬럼 합산.
   - 비용명_내용은 반드시 groupby key에 포함해서 결과에 살아있어야 한다.
   - 수치 컬럼 = 비목분류, 비용명, 비용명_내용 이외의 모든 컬럼.

3. 비목분류 순서: 내부인건비 → 연구활동비 → 연구수당 → 연구시설장비비 → 연구재료비 → 간접비 → 기타.
   같은 비목분류 안에서는 비용명_내용(숫자) 오름차순 정렬.

4. 소계 행은 각 비목분류 그룹의 마지막 일반 항목 바로 다음에 위치해야 한다.
   결과 행 순서 예시:
     내부인건비 / 121 내부인건비  ← 일반 항목
     내부인건비 / 201 계약직...   ← 일반 항목
     내부인건비 / 소계            ← 소계 (바로 여기)
     연구활동비 / 142 공기구...   ← 다음 그룹 시작
     ...
   소계 행: 비목분류 = 해당 그룹명, 비용명 = '소계', 비용명_내용 = None, 수치 = 해당 그룹 합산.
   소계는 비목분류 그룹당 반드시 딱 한 번만 추가할 것. 절대 중복 추가 금지.

5. 맨 아래 요약 행 3개 추가 (파일별 합산), 순서: 내부흡수액 → 외부유출액 → 합         계.
   요약 행 식별: 비목분류 컬럼에서 공백을 모두 제거(replace(' ',''))한 값이 '내부흡수액', '외부유출액', '합계' 중 하나와 일치하는 행.
   예: df['비목분류'].astype(str).str.replace(' ', '') 로 비교할 것.
   요약 행의 비용명, 비용명_내용은 None으로 설정.

6. 파일명 '통합결과.xlsx'로 저장."""),
    ("📊", "예실대비표 집행률 분석", """업로드된 예실대비표 파일 각각의 집행률을 계산해줘.

각 파일마다 아래 순서로 처리하고, 파일별 결과를 세로로 쌓아서 하나의 DataFrame으로 만들어줘.

[파일 1개 처리 순서]

① 사용할 컬럼만 추출: 비목분류, 비용명, 비용명_내용, 실행예산_합계, 집행계_합계
   비용명_내용 컬럼은 원본 값을 절대 삭제하거나 None으로 바꾸지 말 것.

② 행 종류 구분:
   - 요약 행: 비목분류.str.replace(' ','') 값이 '내부흡수액', '외부유출액', '합계' 중 하나인 행
   - 소계 행: 비용명 값이 '소계'인 행
   - 일반 항목: 나머지 (요약도 소계도 아닌 행)

③ 일반 항목에 집행률(%) 추가:
   집행률(%) = round(집행계_합계 / 실행예산_합계 * 100, 2), 분모가 0이면 0

④ 일반 항목만 정렬 (소계·요약 행은 이 단계에서 건드리지 말 것):
   cat_order = {'내부인건비':0,'연구활동비':1,'연구수당':2,'연구시설장비비':3,'연구재료비':4,'간접비':5,'기타':6}
   일반항목['_o'] = 일반항목['비목분류'].map(cat_order).fillna(99)
   일반항목 = 일반항목.sort_values(['_o','비용명_내용']).drop(columns='_o')

⑤ 소계 행 삽입 (정렬된 일반 항목 기준으로 처리):
   아래 루프로 rows 리스트를 만들 것:
     rows = []
     for cat in 일반항목['비목분류'].unique():  # unique()는 정렬된 순서 유지
         grp = 일반항목[일반항목['비목분류']==cat]
         rows.append(grp)
         sub = {col: grp[col].sum() for col in ['실행예산_합계','집행계_합계']}
         sub['비목분류'] = cat
         sub['비용명'] = '소계'
         sub['비용명_내용'] = None
         sub['집행률(%)'] = round(sub['집행계_합계']/sub['실행예산_합계']*100,2) if sub['실행예산_합계'] else 0
         rows.append(pd.DataFrame([sub]))
     main = pd.concat(rows, ignore_index=True)

⑥ 요약 행을 main 아래에 추가 (절대 건너뛰지 말 것):
   요약행['집행률(%)'] = round(요약행['집행계_합계']/요약행['실행예산_합계']*100,2)
   요약행['비용명'] = None
   요약행['비용명_내용'] = None
   순서: 내부흡수액 → 외부유출액 → 합         계
   result = pd.concat([main, 요약행], ignore_index=True)

⑦ 최종 결과에서 '분류', '_o', '_sort' 등 내부 처리용 컬럼은 모두 삭제.
   최종 컬럼: 비목분류, 비용명, 비용명_내용, 실행예산_합계, 집행계_합계, 집행률(%)

⑧ 소제목 행("▶ 파일명")을 result 맨 위에 추가 후 파일별 결과 쌓기.
   데이터 사이 빈 행 금지.

파일명 '집행률분석.xlsx'로 저장."""),
    ("🔍", "예실대비표 예산 비교", """업로드된 예실대비표 파일에서 이월예산·당해예산·잔액을 비교해줘.

[처리 순서]

① 사용할 컬럼만 추출하고, 맨 오른쪽에 '파일명' 컬럼 추가 (원본 파일명 값):
   비목분류, 비용명, 비용명_내용,
   실행예산_이월예산, 실행예산_당해예산, 실행예산_합계,
   예산잔액_이월잔액, 예산잔액_당해잔액, 예산잔액_합계, 파일명

② 행 종류 구분:
   - 요약 행: 비목분류.str.replace(' ','') 값이 '내부흡수액', '외부유출액', '합계' 중 하나
   - 소계 행: 비용명 값이 '소계'인 행
   - 일반 항목: 나머지

③ 일반 항목 정렬 (두 단계):
   1단계 - 비목분류 고정 순서:
     cat_order = {'내부인건비':0,'연구활동비':1,'연구수당':2,'연구시설장비비':3,'연구재료비':4,'간접비':5,'기타':6}
     일반항목['_o'] = 일반항목['비목분류'].map(cat_order).fillna(99)
   2단계 - 같은 비목분류 안에서 예산잔액_합계 내림차순 정렬
   sort_values(['_o','예산잔액_합계'], ascending=[True, False]).drop(columns='_o')

④ 소계 행 삽입 (비목분류 그룹마다 딱 1개):
   rows = []
   for cat in 일반항목['비목분류'].unique():
       grp = 일반항목[일반항목['비목분류']==cat]
       rows.append(grp)
       sub = {col: grp[col].sum() for col in ['실행예산_이월예산','실행예산_당해예산','실행예산_합계','예산잔액_이월잔액','예산잔액_당해잔액','예산잔액_합계']}
       sub['비목분류'] = cat
       sub['비용명'] = '소계'
       sub['비용명_내용'] = None
       rows.append(pd.DataFrame([sub]))
   main = pd.concat(rows, ignore_index=True)

⑤ 요약 행을 main 아래에 추가 (절대 건너뛰지 말 것):
   요약행['비용명'] = None
   요약행['비용명_내용'] = None
   순서: 내부흡수액 → 외부유출액 → 합         계
   요약행 식별: 비목분류 공백 모두 제거 후 비교
   result = pd.concat([main, 요약행], ignore_index=True)

⑥ '분류', '_o', '_sort' 등 임시 컬럼 모두 삭제.

파일명 '예산비교.xlsx'로 저장."""),
]

# 앱 시작 시 현재 채팅 복원
if not st.session_state.current_chat_id:
    chats = list_chats()
    if chats:
        st.session_state.current_chat_id = chats[0]["id"]
        if not st.session_state.messages:
            st.session_state.messages = load_history(chats[0]["id"])
    else:
        st.session_state.current_chat_id = new_id()

# ── custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

#MainMenu, footer { visibility: hidden; }
[data-testid="collapsedControl"] { visibility: visible !important; }

/* ── 전체 배경 ── */
.stApp { background: #09090b; }
section.main > div { padding-top: 1.5rem; }

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #0f0f12;
    border-right: 1px solid #1e1e24;
}
[data-testid="stSidebar"] .block-container { padding: 1.2rem 1rem; }

/* 사이드바 섹션 레이블 */
.sidebar-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: #52525b;
    text-transform: uppercase;
    margin: 1.2rem 0 0.4rem 0;
}

/* 앱 타이틀 */
.app-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.3px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.app-tagline {
    font-size: 0.72rem;
    color: #52525b;
    margin-top: 2px;
}

/* 모델 배지 */
.model-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 0.78rem;
    color: #a1a1aa;
    width: 100%;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.model-badge.active { border-color: #3f3f46; color: #e4e4e7; }
.model-badge.warn   { border-color: #78350f44; color: #d97706; background: #78350f11; }

/* 페르소나 라디오 */
[data-testid="stRadio"] label {
    padding: 5px 8px;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #a1a1aa;
    transition: all 0.1s;
}
[data-testid="stRadio"] label:hover { background: #18181b; color: #e4e4e7; }
[data-testid="stRadio"] [data-checked="true"] label { color: #fafafa; }

/* ── 예시 버튼 ── */
[data-testid="stButton"] button {
    border-radius: 10px;
    font-size: 0.84rem;
    font-weight: 500;
    transition: all 0.15s;
}

/* 예시 버튼 (기본) */
button[kind="secondary"] {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    color: #a1a1aa !important;
    border-radius: 10px !important;
}
button[kind="secondary"]:hover {
    background: #27272a !important;
    border-color: #3f3f46 !important;
    color: #e4e4e7 !important;
}

/* 실행 버튼 */
button[kind="secondary"][data-testid*="exec"] {
    background: #052e16 !important;
    border: 1px solid #166534 !important;
    color: #4ade80 !important;
}
button[kind="secondary"][data-testid*="exec"]:hover {
    background: #14532d !important;
}

/* ── 어시스턴트 말풍선 ── */
[data-testid="stChatMessage"] {
    background: #0f0f12;
    border: 1px solid #1e1e24;
    border-radius: 14px;
    padding: 4px 8px;
    margin-bottom: 8px;
}

/* ── 유저 말풍선 (오른쪽) ── */
.user-row {
    display: flex;
    justify-content: flex-end;
    margin: 8px 0 16px 0;
}
.user-bubble {
    background: #18181b;
    border: 1px solid #3f3f46;
    color: #fafafa;
    padding: 11px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 72%;
    word-wrap: break-word;
    white-space: pre-wrap;
    font-size: 0.92rem;
    line-height: 1.6;
}

/* ── 인풋 박스 ── */
[data-testid="stChatInput"] {
    border-radius: 14px !important;
    border: 1px solid #27272a !important;
    background: #18181b !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3f3f46 !important;
}

/* ── 구분선 ── */
hr { border-color: #1e1e24 !important; }

/* ── 채팅 목록 버튼 ── */
[data-testid="stSidebar"] button[kind="primary"] {
    background: #27272a !important;
    border: 1px solid #3f3f46 !important;
    color: #fafafa !important;
    text-align: left !important;
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    color: #52525b !important;
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: #18181b !important;
    color: #a1a1aa !important;
}

/* ── 스크롤바 ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #27272a; border-radius: 4px; }

/* ── 메트릭 ── */
[data-testid="stMetric"] {
    background: #0f0f12;
    border: 1px solid #1e1e24;
    border-radius: 10px;
    padding: 12px 16px;
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
                persona_key="analyst",
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


def _execute_with_retry(code: str, max_retries: int = 5) -> tuple[ExecutionResult, int, str]:
    """최대 max_retries 회 자동 재시도. (결과, 시도 횟수, 최종 코드) 반환."""
    original = code
    for attempt in range(1, max_retries + 1):
        result = execute(code)
        if result.success:
            return result, attempt, code
        if attempt < max_retries:
            fixed = _ai_fix_code(code, result.error)
            if not fixed:
                break
            code = fixed
    return result, attempt, code


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
    # ── 타이틀 ──
    st.markdown(
        '<div class="app-title">🎯 LLM Excel Studio</div>'
        '<div class="app-tagline">AI-powered Excel automation</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── 모델 ──
    st.markdown('<div class="sidebar-label">Model</div>', unsafe_allow_html=True)
    provider = st.session_state.get("provider", "ollama")
    model = st.session_state.get("selected_model", "")
    provider_icon = {"ollama": "🖥", "openai": "🤖", "gemini": "✨"}.get(provider, "🔌")

    if provider == "ollama":
        from core.llm.router import get_available_models
        if not st.session_state.get("_ollama_models"):
            fetched = get_available_models()
            if fetched:
                st.session_state["_ollama_models"] = fetched
        ollama_models = st.session_state.get("_ollama_models", [])
        if ollama_models:
            cur_idx = ollama_models.index(model) if model in ollama_models else 0
            st.selectbox(
                "모델", ollama_models, index=cur_idx,
                key="selected_model", label_visibility="collapsed",
            )
            code_model = st.session_state.get("code_model", "")
            if code_model:
                st.caption(f"🔧 코드: `{code_model}`")
            else:
                st.caption("🔧 코드: 대화 모델과 동일")
            if st.button("↺  새로고침", use_container_width=True):
                st.session_state["_ollama_models"] = get_available_models()
                st.rerun()
        else:
            st.markdown('<div class="model-badge warn">⚠ Ollama 연결 실패</div>', unsafe_allow_html=True)
    else:
        badge_cls = "active" if model else "warn"
        badge_txt = f"{provider_icon} {model}" if model else "⚠ 모델 미설정 — Settings"
        st.markdown(f'<div class="model-badge {badge_cls}">{badge_txt}</div>', unsafe_allow_html=True)

    # ── 파일 현황 (클릭 → Files 페이지) ──
    n_files, n_results = len(list_files()), len(list_results())
    st.markdown(
        f'<a href="/Files" target="_self" style="text-decoration:none">'
        f'<div style="display:flex;gap:8px;margin:8px 0;cursor:pointer">'
        f'<div style="flex:1;background:#0f0f12;border:1px solid #27272a;border-radius:8px;padding:8px 10px;text-align:center;transition:border-color 0.15s" '
        f'onmouseover="this.style.borderColor=\'#3f3f46\'" onmouseout="this.style.borderColor=\'#27272a\'">'
        f'<div style="font-size:1rem;font-weight:700;color:#fafafa">{n_files}</div>'
        f'<div style="font-size:0.68rem;color:#52525b;margin-top:1px">입력 파일</div>'
        f'</div>'
        f'<div style="flex:1;background:#0f0f12;border:1px solid #27272a;border-radius:8px;padding:8px 10px;text-align:center;transition:border-color 0.15s" '
        f'onmouseover="this.style.borderColor=\'#3f3f46\'" onmouseout="this.style.borderColor=\'#27272a\'">'
        f'<div style="font-size:1rem;font-weight:700;color:#fafafa">{n_results}</div>'
        f'<div style="font-size:0.68rem;color:#52525b;margin-top:1px">출력 파일</div>'
        f'</div>'
        f'</div></a>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.divider()

    # ── 채팅 목록 ──
    st.markdown('<div class="sidebar-label">Chats</div>', unsafe_allow_html=True)

    if st.button("＋  새 채팅", use_container_width=True):
        st.session_state.current_chat_id = new_id()
        st.session_state.messages = []
        st.session_state.execution_results = {}
        st.rerun()

    chats = list_chats()
    current_id = st.session_state.current_chat_id

    for chat in chats:
        is_current = chat["id"] == current_id
        title = chat["title"] or "새 채팅"
        c1, c2 = st.columns([5, 1])
        with c1:
            if st.button(
                title,
                key=f"chat_{chat['id']}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                if not is_current:
                    st.session_state.current_chat_id = chat["id"]
                    st.session_state.messages = load_history(chat["id"])
                    st.session_state.execution_results = {}
                    st.rerun()
        with c2:
            if st.button("✕", key=f"del_{chat['id']}", help="삭제"):
                delete_history(chat["id"])
                if is_current:
                    remaining = [c for c in chats if c["id"] != chat["id"]]
                    if remaining:
                        st.session_state.current_chat_id = remaining[0]["id"]
                        st.session_state.messages = load_history(remaining[0]["id"])
                    else:
                        st.session_state.current_chat_id = new_id()
                        st.session_state.messages = []
                    st.session_state.execution_results = {}
                st.rerun()

    if st.session_state.messages:
        st.divider()
        st.download_button(
            "↓ 내보내기",
            data=_export_md(),
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )



# ── quick prompts ─────────────────────────────────────────────────────────────

_qcols = st.columns(3)
for _col, (icon, title, prompt_text) in zip(_qcols, _QUICK_PROMPTS):
    with _col:
        if st.button(f"{icon}  {title}", use_container_width=True,
                     key=f"qp_{title}", help=prompt_text):
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
                # float이지만 실제 정수인 컬럼 → 정수로 강제 변환 (121.0 → 121)
                for c in _safe.select_dtypes(include=["float64", "float32"]).columns:
                    _nn = _safe[c].dropna()
                    if len(_nn) > 0 and (_nn % 1 == 0).all():
                        try:
                            _safe[c] = _safe[c].astype("Int64")
                        except Exception:
                            pass
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
            # 재시도로 수정된 코드가 있으면 표시
            final_code = st.session_state.final_codes.get(idx)
            original_codes = _extract_code(content)
            if final_code and original_codes and final_code.strip() != original_codes[0].strip():
                with st.expander("🔧 AI가 자동 수정한 최종 코드"):
                    st.code(final_code, language="python")
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

    # 결과 여부와 무관하게 재실행 버튼 항상 표시
    if _extract_code(content):
        if st.button("🔄 재실행", key=f"exec_{idx}", type="secondary"):
            with st.spinner("코드 실행 중..."):
                try:
                    r, attempts, final_code = _execute_with_retry(_extract_code(content)[0])
                    st.session_state.final_codes[idx] = final_code
                    if not r.success:
                        r.error = f"[{attempts}회 시도 후 실패]\n\n{r.error}"
                except Exception as e:
                    from core.executor.sandbox import ExecutionResult
                    r = ExecutionResult(success=False, error=str(e))
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
    save_history(st.session_state.current_chat_id, st.session_state.messages)
    _user_bubble(prompt)

    file_ctx = build_file_context()

    # 파일 있어도 단순 대화면 대화 모델, 데이터 처리 요청이면 코드 모델
    _CODE_KEYWORDS = {
        "합산", "합치", "통합", "병합", "계산", "정렬", "분석", "추출",
        "필터", "변환", "집계", "비교", "처리", "저장", "출력", "뽑아",
        "평균", "합계", "집행률", "더해", "나눠", "곱해", "빼", "구해",
        "만들어", "작성", "생성", "코드", "엑셀", "파일로",
    }
    _needs_code = file_ctx and any(kw in prompt for kw in _CODE_KEYWORDS)
    client = get_code_client() if _needs_code else get_client()
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
            persona_key="analyst",
            file_context=file_ctx,
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

        # 스트리밍 시작 전 플레이스홀더를 히스토리에 저장 → 화면 이탈 후 복귀해도 유지
        _placeholder_idx = len(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": "⏳ _생성 중..._"})
        save_history(st.session_state.current_chat_id, st.session_state.messages)

        threading.Thread(target=_do_stream, daemon=True).start()

        with st.chat_message("assistant"):
            status_ph = st.empty()
            content_ph = st.empty()
            stop_ph = st.empty()

            status_ph.markdown("⏳ _생성 중..._")
            _stop_key = f"_stop_{_placeholder_idx}"
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

        # 플레이스홀더를 실제 응답으로 교체
        response_content = (full or "_응답 없음_") + suffix
        st.session_state.messages[_placeholder_idx] = {"role": "assistant", "content": response_content}
        save_history(st.session_state.current_chat_id, st.session_state.messages)

        # 코드 블록 있으면 자동 실행
        codes = _extract_code(response_content)
        if codes:
            msg_idx = len(st.session_state.messages) - 1
            with st.spinner("코드 자동 실행 중..."):
                r, attempts, final_code = _execute_with_retry(codes[0])
            if not r.success:
                r.error = f"[{attempts}회 시도 후 실패]\n\n{r.error}"
            st.session_state.execution_results[msg_idx] = r
            st.session_state.final_codes[msg_idx] = final_code

        st.rerun()
