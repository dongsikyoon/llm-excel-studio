import streamlit as st
from core.state import init

st.set_page_config(
    page_title="소개 — LLM Excel Studio",
    page_icon="📋",
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

.section-card {
    background: #0f0f12;
    border: 1px solid #1e1e24;
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 20px;
}
.badge {
    display: inline-block;
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.78rem;
    color: #a1a1aa;
    margin: 2px 3px;
}
.flow-box {
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
    padding: 12px 20px;
    text-align: center;
    font-size: 0.88rem;
    color: #e4e4e7;
    font-weight: 500;
}
.flow-arrow {
    text-align: center;
    color: #3f3f46;
    font-size: 1.2rem;
    margin: 4px 0;
}
.highlight {
    color: #58a6ff;
    font-weight: 600;
}
.tag-green  { border-color: #166534; color: #4ade80; background: #052e16; }
.tag-blue   { border-color: #1e40af; color: #93c5fd; background: #0c1a3d; }
.tag-purple { border-color: #5b21b6; color: #c4b5fd; background: #1a0a3d; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────────────────────────

st.markdown("## 🎯 LLM Excel Studio")
st.markdown("**Basic Software Technology** 과제 | AI 기반 엑셀 자동화 스튜디오")
st.markdown(
    '<span class="badge tag-green">Python 3.12</span>'
    '<span class="badge tag-blue">Streamlit 1.55</span>'
    '<span class="badge tag-blue">Ollama</span>'
    '<span class="badge tag-blue">OpenAI API</span>'
    '<span class="badge tag-purple">pandas · openpyxl</span>',
    unsafe_allow_html=True,
)

st.divider()

# ── 1. LLM 실행 구조 ─────────────────────────────────────────────────────────

st.markdown("### 1. LLM 실행 구조")

col1, col2, col3 = st.columns([1, 0.08, 1])

with col1:
    st.markdown("**① 입력 → 모델 라우팅**")
    for box, is_branch in [
        ("사용자 메시지 입력", False),
        ("파일 업로드 여부 확인", False),
        ("📄 파일 있음\n→ 코드 생성 모델\n(qwen2.5-coder:32b)", False),
        ("💬 파일 없음\n→ 대화 모델\n(qwen3:32b)", False),
        ("시스템 프롬프트 생성\n(파일 컨텍스트 + 코드 규칙)", False),
        ("LLM 스트리밍 응답", False),
    ]:
        st.markdown(f'<div class="flow-box">{box}</div>', unsafe_allow_html=True)
        if box != "LLM 스트리밍 응답":
            st.markdown('<div class="flow-arrow">↓</div>', unsafe_allow_html=True)

with col2:
    st.markdown("")

with col3:
    st.markdown("**② 코드 실행 파이프라인**")
    for box in [
        "응답에서 코드 블록 감지",
        "AST 정적 분석\n(실행 전 코드 보안 검사 — 위험 명령 차단)",
        "샌드박스 실행\n(격리된 가상 환경에서 실행, 30초 타임아웃)",
        "실패 시 LLM 자동 수정\n(최대 5회 재시도)",
        "Excel 저장\n(천단위 콤마, 컬럼 폭, 셀 병합)",
        "채팅 히스토리 저장\n(JSON, 앱 재시작 후에도 유지)",
    ]:
        st.markdown(f'<div class="flow-box">{box}</div>', unsafe_allow_html=True)
        if box != "채팅 히스토리 저장\n(JSON, 앱 재시작 후에도 유지)":
            st.markdown('<div class="flow-arrow">↓</div>', unsafe_allow_html=True)

st.divider()

# ── 2. 시스템 구성요소 ────────────────────────────────────────────────────────

st.markdown("### 2. 시스템 구성요소")

comp_cols = st.columns(3)

components = [
    ("🖼 Streamlit", "tag-blue", [
        "Python 기반 웹앱 프레임워크",
        "멀티페이지 앱 구조 (pages/)",
        "실시간 스트리밍 UI (st.write_stream)",
        "세션 상태로 대화·설정 관리",
        "포트 8501 → 외부 포트포워딩으로 공개 서비스",
    ]),
    ("🤖 LLM 엔진", "tag-green", [
        "Ollama: 로컬/원격 서버에서 오픈소스 모델 실행",
        "OpenAI API: GPT-4o 등 클라우드 모델 연동",
        "Google Gemini: API Key만 입력하면 바로 사용 가능",
        "스마트 라우팅: 질문 키워드 분석 후 대화 ↔ 코드 모델 자동 전환",
        "추천 모델: qwen3:32b (대화) + qwen2.5-coder:32b (코드)",
    ]),
    ("⚙️ 실행 구조", "tag-purple", [
        "scripts/run.sh: nohup 백그라운드 실행",
        "scripts/stop.sh: PID 파일 기반 종료",
        "--server.runOnSave=true: 파일 변경 시 자동 재시작",
        "--server.address=0.0.0.0: 외부 접속 허용",
        "logs/ 폴더에 실행 로그·PID 분리 저장",
    ]),
]

for col, (title, tag, items) in zip(comp_cols, components):
    with col:
        st.markdown(f'<span class="badge {tag}">{title}</span>', unsafe_allow_html=True)
        st.markdown("")
        for item in items:
            st.markdown(f"- {item}")

st.divider()

comp_cols2 = st.columns(3)
components2 = [
    ("📊 데이터 처리", "tag-blue", [
        "pandas: DataFrame 기반 엑셀 분석·병합",
        "openpyxl: 셀 병합·서식·폭 자동 조정",
        "2행 헤더 Excel 자동 파싱 (header=[0,1])",
        "병합셀 NaN → forward-fill 전처리",
        "정수형 자동 변환 (121.0 → 121)",
    ]),
    ("🔒 샌드박스", "tag-green", [
        "AST(Abstract Syntax Tree) 파싱: 실행 전에 코드 구조를 분석해 위험 여부 판단",
        "위험 모듈(os, subprocess 등) import 차단 → 1겹: 실행 전 / 2겹: 런타임",
        "허용 모듈 화이트리스트 (re, math, datetime 등 안전한 것만 허용)",
        "pandas/numpy 내부 동작을 위한 import는 예외 처리",
        "pd.read_excel 호출을 업로드된 파일로 자동 연결",
    ]),
    ("💾 히스토리", "tag-purple", [
        "대화별 JSON 파일로 영구 저장 (data/histories/)",
        "앱 재시작 후 자동 복원",
        "사이드바에서 대화 목록 선택·전환",
        "스트리밍 중 플레이스홀더 저장 (이탈 대응)",
        "채팅 내역 Markdown 파일로 내보내기",
    ]),
]

for col, (title, tag, items) in zip(comp_cols2, components2):
    with col:
        st.markdown(f'<span class="badge {tag}">{title}</span>', unsafe_allow_html=True)
        st.markdown("")
        for item in items:
            st.markdown(f"- {item}")

st.divider()

# ── 3. 구현 특징 ──────────────────────────────────────────────────────────────

st.markdown("### 3. 주요 구현 특징 (차별점)")

feat_cols = st.columns(2)

with feat_cols[0]:
    st.markdown("""
**🔀 스마트 모델 라우팅**
질문 내용을 분석해 대화 모델과 코드 생성 모델을 자동 전환.
파일이 올라가 있어도 "이 파일이 뭐야?" 같은 단순 질문은 대화 모델,
"합산해줘", "분석해줘" 등 데이터 처리 키워드가 있으면 코드 모델 사용.

**🔁 자동 재시도 + 코드 투명성 (최대 5회)**
코드 실행 실패 시 오류 내용·실패 코드를 LLM에 자동 전달해 수정·재실행.
원본과 다른 코드로 성공 시, 수정된 최종 코드를 채팅창에 공개해 검증 가능.

**📥 앱 내 모델 다운로드**
Ollama Hub의 모델을 앱 UI에서 직접 다운로드.
실시간 프로그레스바로 진행 상황 표시.

**🧪 Playground**
인터랙티브 코드(`st.number_input`, `st.button` 등)를 직접 작성·실행하는 전용 환경.
채팅에서 AI가 생성한 인터랙티브 코드는 원클릭으로 Playground로 전송 가능.
`if __name__ == "__main__":` 패턴 포함 일반 Python 스크립트도 실행 지원.
""")

with feat_cols[1]:
    st.markdown("""
**📊 예실대비표 전용 기능**
파일 통합 / 집행률 분석 / 예산 비교 — 3종 전용 프롬프트.
비목분류 고정 순서, 소계 자동 생성, 요약행 보존 등 도메인 규칙 내장.

**🔒 보안 샌드박스 (이중 차단)**
AI가 만든 코드를 실행 전에 AST(Abstract Syntax Tree, 추상 구문 트리) 분석으로 위험 명령을 차단.
`import os`, `subprocess` 등 서버 제어 가능한 모듈은 실행 전에 걸러내고,
런타임에서도 `__import__`를 커스텀 함수로 교체해 허용 목록 외 import를 이중으로 차단.
30초 타임아웃으로 무한루프도 방어.

**💾 Excel 자동 품질**
저장 시 천단위 콤마, 컬럼 너비(한글 2배 폭 계산), 셀 병합 자동 복원.
정수형 컬럼 121.0 → 121 변환.
""")

st.divider()

# ── 4. 파일 구조 ─────────────────────────────────────────────────────────────

st.markdown("### 4. 프로젝트 구조")

st.code("""
llm-excel-studio/
├── app.py                     # 메인 채팅 페이지 (스트리밍, 히스토리, 코드 실행)
├── pages/
│   ├── 1_Files.py             # 파일 업로드·관리·미리보기
│   ├── 2_Settings.py          # 모델 설정 및 Ollama 모델 다운로드
│   ├── 3_About.py             # 시스템 소개 (현재 페이지)
│   └── 4_Playground.py        # 인터랙티브 코드 실행 환경
├── core/
│   ├── llm/
│   │   ├── base.py            # LLM 추상 인터페이스
│   │   ├── ollama_client.py   # Ollama 클라이언트 (/no_think 적용)
│   │   ├── openai_client.py   # OpenAI / Gemini 클라이언트
│   │   └── router.py          # 듀얼 모델 라우팅 (대화 / 코드)
│   ├── prompt/
│   │   ├── personas.py        # 역할 정의
│   │   └── enhancer.py        # 시스템 프롬프트 동적 생성
│   ├── executor/
│   │   └── sandbox.py         # AST 검증 + 샌드박스 실행 + 자동 재시도
│   └── files/
│       ├── manager.py         # 파일 I/O, 2행 헤더 파싱, 전처리
│       ├── context.py         # 파일 → LLM 컨텍스트 변환
│       └── history.py         # 채팅 히스토리 저장·복원
├── scripts/
│   ├── run.sh                 # 백그라운드 실행 (nohup)
│   └── stop.sh                # PID 기반 종료
└── requirements.txt
""", language="")
