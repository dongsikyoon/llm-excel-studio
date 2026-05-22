import streamlit as st
import pandas as pd
import numpy as np
import math
import traceback

from core.state import init

st.set_page_config(
    page_title="Playground — LLM Excel Studio",
    page_icon="🧪",
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
textarea { font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
           font-size: 0.85rem !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🧪 Playground")
st.caption("코드를 직접 작성하고 실행하세요. `st`, `pd`, `np`, `math` 사용 가능.")

# ── 예제 코드 ─────────────────────────────────────────────────────────────────

EXAMPLES = {
    "빈 화면": "",
    "계산기": """\
a = st.number_input('숫자 1', value=0.0, key='calc_a')
op = st.selectbox('연산', ['+', '-', '×', '÷', '√'], key='calc_op')
b = st.number_input('숫자 2', value=0.0, key='calc_b',
                    disabled=(op == '√'))

if st.button('계산', key='calc_btn'):
    if op == '+':   st.success(f'{a} + {b} = {a + b}')
    elif op == '-': st.success(f'{a} - {b} = {a - b}')
    elif op == '×': st.success(f'{a} × {b} = {a * b}')
    elif op == '÷':
        if b == 0: st.error('0으로 나눌 수 없습니다')
        else: st.success(f'{a} ÷ {b} = {a / b:.6g}')
    elif op == '√': st.success(f'√{a} = {math.sqrt(max(a,0)):.6g}')
""",
    "단위 변환기": """\
category = st.selectbox('변환 종류', ['길이', '무게', '온도'], key='unit_cat')
val = st.number_input('값', key='unit_val')

if category == '길이':
    frm = st.selectbox('단위', ['km', 'm', 'cm', 'mile', 'inch'], key='u_from')
    to  = st.selectbox('→',   ['km', 'm', 'cm', 'mile', 'inch'], key='u_to')
    f = {'km':1000,'m':1,'cm':0.01,'mile':1609.34,'inch':0.0254}
    st.info(f'{val} {frm} = **{val * f[frm] / f[to]:.6g} {to}**')
elif category == '무게':
    frm = st.selectbox('단위', ['kg', 'g', 'lb', 'oz'], key='u_from')
    to  = st.selectbox('→',   ['kg', 'g', 'lb', 'oz'], key='u_to')
    f = {'kg':1,'g':0.001,'lb':0.453592,'oz':0.0283495}
    st.info(f'{val} {frm} = **{val * f[frm] / f[to]:.6g} {to}**')
elif category == '온도':
    frm = st.selectbox('단위', ['°C', '°F', 'K'], key='u_from')
    to  = st.selectbox('→',   ['°C', '°F', 'K'], key='u_to')
    def c(v,u): return v if u=='°C' else (v-32)*5/9 if u=='°F' else v-273.15
    def r(v,u): return v if u=='°C' else v*9/5+32 if u=='°F' else v+273.15
    st.info(f'{val} {frm} = **{r(c(val,frm),to):.4g} {to}**')
""",
}

# ── 상단: 에디터 + 컨트롤 ─────────────────────────────────────────────────────

col_label, col_ex, col_clr = st.columns([3, 2, 1])
with col_label:
    st.markdown("**코드 입력**")
with col_ex:
    selected_ex = st.selectbox("예제", list(EXAMPLES.keys()),
                               label_visibility="collapsed", key="ex_select")
    if selected_ex != st.session_state.get("_last_ex"):
        st.session_state["_last_ex"] = selected_ex
        st.session_state["playground_code"] = EXAMPLES[selected_ex]
        st.session_state["playground_run"] = selected_ex != "빈 화면"
        st.rerun()
with col_clr:
    if st.button("🗑", use_container_width=True, help="초기화"):
        st.session_state["playground_code"] = ""
        st.session_state["playground_run"] = False
        st.session_state["_last_ex"] = "빈 화면"
        st.rerun()

code = st.text_area(
    "code_input",
    value=st.session_state.get("playground_code", ""),
    height=200,
    label_visibility="collapsed",
    placeholder="여기에 Python 코드를 입력하세요...",
)

if st.button("▶  실행", type="primary", use_container_width=True):
    st.session_state["playground_code"] = code
    st.session_state["playground_run"] = True
    st.rerun()

st.divider()

# ── 출력: 페이지 최상위 레벨에서 실행 (위젯 안정성 보장) ─────────────────────

if st.session_state.get("playground_run") and st.session_state.get("playground_code", "").strip():
    st.markdown("**출력**")
    ns = {"st": st, "pd": pd, "np": np, "math": math, "print": print,
          "__name__": "__main__"}
    try:
        exec(st.session_state["playground_code"], ns)  # noqa: S102
    except Exception:
        st.error("코드 실행 중 오류가 발생했습니다.")
        st.code(traceback.format_exc(), language="python")
        st.info("💡 채팅창에서 AI에게 오류를 붙여넣고 수정을 요청해보세요.")
else:
    st.markdown(
        '<div style="color:#3f3f46;text-align:center;padding:3rem 0">'
        '▶ 실행 버튼을 눌러주세요'
        '</div>',
        unsafe_allow_html=True,
    )
