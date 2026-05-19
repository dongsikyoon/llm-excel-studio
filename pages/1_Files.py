import streamlit as st

from core.state import init
from core.files.manager import (
    save_uploaded, list_files, delete_file, get_file_info, preview_file,
    list_results, delete_result, RESULT_DIR,
)

st.set_page_config(
    page_title="파일 관리 — LLM Excel Studio",
    page_icon="📁",
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
.file-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.file-card:hover { border-color: #58a6ff; }
.file-name { font-weight: 600; color: #e6edf3; font-size: 0.95rem; }
.file-meta { color: #8b949e; font-size: 0.8rem; margin-top: 2px; }
.result-card {
    background: #0d1117;
    border: 1px solid #238636;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ── header ────────────────────────────────────────────────────────────────────

st.markdown("## 📁 파일 관리")

files = list_files()
results = list_results()

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.metric("업로드된 파일", f"{len(files)}개")
with col_s2:
    st.metric("결과 파일", f"{len(results)}개")
with col_s3:
    total_mb = 0.0
    from core.files.manager import UPLOAD_DIR, RESULT_DIR
    for d in [UPLOAD_DIR, RESULT_DIR]:
        for f in d.iterdir():
            try:
                total_mb += f.stat().st_size / 1_048_576
            except OSError:
                pass
    st.metric("전체 용량", f"{total_mb:.1f} MB")

st.divider()

# ── upload ────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">📤 파일 업로드</div>', unsafe_allow_html=True)
uploaded = st.file_uploader(
    "Excel / CSV 파일 (복수 선택 가능)",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)
if uploaded:
    for f in uploaded:
        save_uploaded(f)
    st.rerun()

st.divider()

# ── two columns ───────────────────────────────────────────────────────────────

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-title">📄 업로드된 파일</div>', unsafe_allow_html=True)

    if not files:
        st.markdown(
            "<div style='color:#8b949e; text-align:center; padding:2rem;'>"
            "업로드된 파일이 없습니다.</div>",
            unsafe_allow_html=True,
        )
    else:
        for fname in files:
            info = get_file_info(fname)
            meta = f"{info['rows']}행 × {info['columns']}열" if info else "읽기 실패"

            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f'<div class="file-card">'
                    f'<div class="file-name">📄 {fname}</div>'
                    f'<div class="file-meta">{meta}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown("<div style='padding-top:14px'>", unsafe_allow_html=True)
                if st.button("✕", key=f"del_{fname}", help=f"{fname} 삭제"):
                    delete_file(fname)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        st.markdown('<div class="section-title">🔍 미리보기</div>', unsafe_allow_html=True)
        preview_target = st.selectbox("파일 선택", files, label_visibility="collapsed")
        if preview_target:
            df_preview = preview_file(preview_target)
            if df_preview is not None:
                _safe = df_preview.copy()
                for c in _safe.select_dtypes(include="object").columns:
                    _safe[c] = _safe[c].astype(str)
                st.dataframe(_safe, width="stretch")

with col_right:
    st.markdown('<div class="section-title">📊 결과 파일</div>', unsafe_allow_html=True)

    if not results:
        st.markdown(
            "<div style='color:#8b949e; text-align:center; padding:2rem;'>"
            "Chat에서 코드를 실행하면 결과 파일이 생성됩니다.</div>",
            unsafe_allow_html=True,
        )
    else:
        for fname in results:
            fpath = RESULT_DIR / fname
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(
                    f'<div class="result-card">'
                    f'<div class="file-name">📊 {fname}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown("<div style='padding-top:14px'>", unsafe_allow_html=True)
                st.download_button(
                    "⬇",
                    data=fpath.read_bytes(),
                    file_name=fname,
                    key=f"dl_{fname}",
                    help=f"{fname} 다운로드",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div style='padding-top:14px'>", unsafe_allow_html=True)
                if st.button("✕", key=f"del_result_{fname}", help=f"{fname} 삭제"):
                    delete_result(fname)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
