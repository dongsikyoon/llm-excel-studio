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


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """MultiIndex 컬럼을 '상위_하위' 형태로 플래튼. Unnamed는 무시."""
    new_cols, seen = [], {}
    for col in df.columns:
        if isinstance(col, tuple):
            top = str(col[0]).strip()
            sub = str(col[1]).strip()
            top_c = "" if "Unnamed" in top else top
            sub_c = "" if "Unnamed" in sub else sub
            if top_c and sub_c:
                name = f"{top_c}_{sub_c}"
            elif top_c:
                name = top_c
            elif sub_c:
                name = sub_c
            else:
                name = f"col_{len(new_cols)}"
        else:
            name = str(col).strip()

        # 중복 방지
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        new_cols.append(name)

    df.columns = new_cols
    return df


def read_file(filename: str) -> pd.DataFrame | None:
    path = UPLOAD_DIR / filename
    if not path.exists():
        return None
    try:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            # 2행 헤더 여부 판단: 서브헤더에 의미있는 값이 3개 이상이면 멀티레벨로 읽기
            df_try = pd.read_excel(path, header=[0, 1])
            sub_meaningful = sum(
                1 for c in df_try.columns
                if isinstance(c, tuple) and "Unnamed" not in str(c[1]) and str(c[1]).strip()
            )
            if sub_meaningful >= 3:
                df = _flatten_columns(df_try)
            else:
                df = pd.read_excel(path)
                # 단일 헤더: Unnamed → 앞 컬럼명_n 으로 변환
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

        # 비용명_1 → 비용명_내용 으로 rename
        if "비용명_1" in df.columns:
            df = df.rename(columns={"비용명_1": "비용명_내용"})

        # 텍스트 컬럼 병합셀 NaN → forward-fill
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].ffill()

        # 숫자처럼 생긴 object 컬럼 → numeric 변환
        for col in df.select_dtypes(include="object").columns:
            converted = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.strip(),
                errors="coerce",
            )
            if converted.notna().sum() > len(df) * 0.5:
                df[col] = converted

        # 정수로만 이루어진 float 컬럼 → Int64 (121.0 → 121)
        for col in df.select_dtypes(include="float").columns:
            non_null = df[col].dropna()
            if len(non_null) > 0 and (non_null % 1 == 0).all():
                try:
                    df[col] = df[col].astype("Int64")
                except Exception:
                    pass

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
