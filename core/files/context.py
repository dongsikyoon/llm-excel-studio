import pandas as pd
from .manager import list_files, read_file


def _to_int_display(df: pd.DataFrame) -> pd.DataFrame:
    """float 컬럼 중 실제로 정수인 것들을 Int64로 변환해 121.0 → 121 표시."""
    df = df.copy()
    for col in df.select_dtypes(include=["float64", "float32"]).columns:
        non_null = df[col].dropna()
        if len(non_null) > 0 and (non_null % 1 == 0).all():
            try:
                df[col] = df[col].astype("Int64")
            except Exception:
                pass
    return df


def build_file_context() -> str:
    """Convert uploaded files into a text summary for the LLM system prompt."""
    files = list_files()
    if not files:
        return ""

    parts = []
    for fname in files:
        df = read_file(fname)
        if df is None:
            continue
        df_disp = _to_int_display(df)
        col_info = ", ".join(f"{col} ({df_disp[col].dtype})" for col in df_disp.columns)
        sample = df_disp.head(3).to_string(index=False, max_cols=10)
        parts.append(
            f"### {fname}\n"
            f"- 크기: {len(df)}행 × {len(df.columns)}열\n"
            f"- 컬럼: {col_info}\n"
            f"- 샘플 (3행):\n```\n{sample}\n```"
        )

    return "\n\n".join(parts)
