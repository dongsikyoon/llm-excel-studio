from .manager import list_files, read_file


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
        col_info = ", ".join(f"{col} ({df[col].dtype})" for col in df.columns)
        sample = df.head(3).to_string(index=False, max_cols=10)
        parts.append(
            f"### {fname}\n"
            f"- 크기: {len(df)}행 × {len(df.columns)}열\n"
            f"- 컬럼: {col_info}\n"
            f"- 샘플 (3행):\n```\n{sample}\n```"
        )

    return "\n\n".join(parts)
