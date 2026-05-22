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
   파일명에 _수정, _fixed, _v2, _retry 등의 접미사를 붙이지 말 것
3. **`import` 절대 금지** — pd, np, save, files, print 만 사용 가능
4. `open()`, `os`, `sys` 등 시스템 명령 사용 금지
5. `print()` 로 중간 과정 출력 가능

### 파일 병합 규칙
- 수치 집계는 **합산(sum)** 을 기본으로 사용 (평균 요청 시에만 mean 사용)
- 텍스트 컬럼(비목분류, 비용명 등)은 집계하지 말고 첫 번째 파일의 값을 그대로 사용
- 파일 하단의 '내부흡수액', '외부유출액', '합 계' 같은 요약 행은 일반 데이터와 **반드시 분리**해 처리하고 맨 마지막에 추가할 것

### 응답 형식
1. 작업 내용 1~2줄 설명
2. ```python 코드 블록
3. 예상 결과 간단히 설명

파일 작업이 아닌 일반 질문은 코드 없이 답변해도 됩니다."""


def build_system_prompt(persona_key: str, file_context: str = "", needs_code: bool = False) -> str:
    """Build a rich system prompt from persona + file context + code rules."""
    persona: Persona = PERSONAS.get(persona_key, PERSONAS["analyst"])

    parts = [f"## 역할\n{persona.role}"]

    if file_context:
        parts.append(f"## 업로드된 파일\n{file_context}")

    if needs_code:
        # 데이터 처리 요청 → 샌드박스 코드 규칙 포함
        parts.append(_CODE_RULES)
    else:
        # 일반 대화 → 제약 없이 자유롭게 답변
        parts.append(
            "일반 질문에 자유롭게 답변하세요.\n\n"
            "코드 요청 시 중요 규칙:\n"
            "1. 코드는 반드시 ```python 블록 안에 작성할 것\n"
            "2. 이 앱 안에서 직접 실행됨 — 파일 저장, pip install, streamlit run 등 별도 실행 안내 불필요\n"
            "3. `input()` 사용 불가. 인터랙티브 입력은 `st` 위젯 사용\n"
            "4. 모든 st 위젯에 고유한 key 지정 필수 (재실행 시 값 유지)\n\n"
            "사용 가능한 변수: `st` (Streamlit), `pd` (pandas), `np` (numpy), `print()`\n\n"
            "인터랙티브 코드 예시:\n"
            "```python\n"
            "a = st.number_input('숫자 1', value=0.0, key='calc_a')\n"
            "b = st.number_input('숫자 2', value=0.0, key='calc_b')\n"
            "op = st.selectbox('연산', ['+', '-', '×', '÷'], key='calc_op')\n"
            "if st.button('계산', key='calc_btn'):\n"
            "    if op == '+': st.success(f'{a} + {b} = {a+b}')\n"
            "    elif op == '-': st.success(f'{a} - {b} = {a-b}')\n"
            "    elif op == '×': st.success(f'{a} × {b} = {a*b}')\n"
            "    elif op == '÷': st.success(f'{a} ÷ {b} = {a/b}' if b else '0으로 나눌 수 없습니다')\n"
            "```"
        )

    return "\n\n".join(parts)
