"""
System prompt enhancer.

SheetPilot uses a single fixed string as a system prompt.
Here we build a richer prompt dynamically from:
  1. Persona  → domain-specific role and response style
  2. File context → what files are loaded and their structure
  3. Code-generation rules → how to produce executable pandas code
"""

from .personas import PERSONAS, Persona

_CODE_RULES = """\
## 코드 생성 규칙

파일 작업 요청에는 반드시 ```python 코드 블록으로 응답하세요.

### 사용 가능한 변수/모듈
- `files`: dict[str, pd.DataFrame] — 업로드된 파일 (키: 파일명)
  예시: `files["data.xlsx"]` → DataFrame 반환
- `pd`: pandas 모듈
- `np`: numpy 모듈
- `save(filename)`: result DataFrame을 파일로 저장 (.xlsx / .csv)
- `save(filename, df)`: 특정 DataFrame 저장

### 필수 규칙
1. 최종 결과는 반드시 `result = ...` 변수에 저장
2. 파일 저장 시 `save("파일명.xlsx")` 호출 — 파일명은 작업 내용을 반영해 지을 것
   (예: `save("병합결과.xlsx")`, `save("집행률분석.xlsx")`, `save("예산비교.xlsx")`)
3. **`import` 절대 금지** — pd, np, save, files, print 만 사용 가능
4. `open()`, `os`, `sys` 등 시스템 명령 사용 금지
5. `print()` 로 중간 과정 출력 가능

### 응답 형식
1. 작업 내용 1~2줄 설명
2. ```python 코드 블록
3. 예상 결과 간단히 설명

파일 작업이 아닌 일반 질문은 코드 없이 답변해도 됩니다."""


def build_system_prompt(persona_key: str, file_context: str = "") -> str:
    """Build a rich system prompt from persona + file context + code rules."""
    persona: Persona = PERSONAS.get(persona_key, PERSONAS["analyst"])

    parts = [
        f"## 역할\n{persona.role}",
        (
            f"## 업로드된 파일\n{file_context}"
            if file_context
            else "## 업로드된 파일\n현재 업로드된 파일이 없습니다. 일반 질문에 답변하세요."
        ),
        _CODE_RULES,
    ]

    return "\n\n".join(parts)
