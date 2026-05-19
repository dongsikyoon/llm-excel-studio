from pathlib import Path
import pandas as pd

UPLOAD_DIR = Path("uploads")
RESULT_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)

_SUPPORTED = {".xlsx", ".xls", ".csv"}


def save_uploaded(file) -> None:
    (UPLOAD_DIR / file.name).write_bytes(file.getbuffer())


def list_files() -> list[str]:
    return sorted(f.name for f in UPLOAD_DIR.iterdir() if f.suffix.lower() in _SUPPORTED)


def read_file(filename: str) -> pd.DataFrame | None:
    path = UPLOAD_DIR / filename
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)

        # 1) Unnamed 컬럼 → 앞 컬럼명 기반으로 변환 (병합 헤더 처리)
        cols, last, counter = list(df.columns), "col", {}
        new_cols = []
        for col in cols:
            if str(col).startswith("Unnamed:"):
                n = counter.get(last, 0) + 1
                counter[last] = n
                new_cols.append(f"{last}_{n}")
            else:
                last = str(col)
                counter = {}
                new_cols.append(col)
        df.columns = new_cols

        # 2) 텍스트 컬럼 병합셀 NaN → forward-fill (간접비간접비... 방지)
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].ffill()

        # 3) 숫자처럼 생긴 object 컬럼 → numeric 변환 (쉼표 포함 숫자 처리)
        for col in df.select_dtypes(include="object").columns:
            converted = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.strip(),
                errors="coerce",
            )
            if converted.notna().sum() > len(df) * 0.5:
                df[col] = converted

        return df
    except Exception:
        return None


def delete_file(filename: str) -> None:
    (UPLOAD_DIR / filename).unlink(missing_ok=True)


def get_file_info(filename: str) -> dict | None:
    df = read_file(filename)
    return {"rows": len(df), "columns": len(df.columns)} if df is not None else None


def preview_file(filename: str, n: int = 5) -> pd.DataFrame | None:
    df = read_file(filename)
    return df.head(n) if df is not None else None


def list_results() -> list[str]:
    return sorted(f.name for f in RESULT_DIR.iterdir() if f.suffix.lower() in {".xlsx", ".csv"})


def delete_result(filename: str) -> None:
    (RESULT_DIR / filename).unlink(missing_ok=True)
