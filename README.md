# 🎯 LLM Excel Studio

> Streamlit 기반 AI 엑셀 자동화 스튜디오 — 다중 LLM 지원, 자연어 프롬프트로 파일 병합·분석·처리

**Basic Software Technology** 과제 구현물

### 🌐 [바로 접속하기 → http://****-ev1.****:33002](http://****-ev1.****:33002)

---

<img width="1241" height="599" alt="image" src="https://github.com/user-attachments/assets/80249373-5437-424f-8dbc-2eb0c378c240" />

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 💬 **자연어 채팅** | 자연어로 엑셀 파일 분석·병합·처리 요청 |
| 🤖 **다중 AI 모델** | Ollama (로컬/원격) · OpenAI · Google Gemini |
| 👤 **페르소나** | 데이터 분석가 · 회계담당자 · 연구원 · 일반사무 |
| 📁 **파일 관리** | Excel/CSV 업로드·미리보기·삭제, 결과 다운로드 |
| 🔁 **자동 재시도** | 코드 실행 실패 시 AI가 자동으로 최대 5회 수정·재실행 |
| 🔒 **샌드박스 실행** | AST 검증 후 격리 실행, 위험 모듈 차단 |
| 💾 **결과 저장** | 숫자 천단위 콤마 포함 Excel 자동 저장 |

---

## 로컬 설치 및 실행

```bash
git clone https://github.com/<your-username>/llm-excel-studio.git
cd llm-excel-studio
pip install -r requirements.txt

# Ollama 로컬 모델 사용 시
ollama pull qwen3:14b

streamlit run app.py
# → http://localhost:8501
```

---

## 서버 배포 (백그라운드 실행)

```bash
chmod +x run.sh stop.sh
./run.sh           # 기본 포트 8501
./run.sh 8080      # 포트 지정

tail -f streamlit.log   # 로그 확인
./stop.sh               # 종료
```

- 파일 수정 시 **자동 새로고침** (hot-reload)
- `0.0.0.0` 바인딩 → 포트포워딩으로 외부 접속 가능

---

## AI 모델 설정

앱 실행 후 사이드바 또는 **⚙️ Settings** 에서 설정합니다.

| 제공자 | 설정 방법 |
|--------|----------|
| **Ollama** | 서버 URL 입력 → 사이드바에서 모델 선택 (자동 로드) |
| **OpenAI** | API Key + 모델 선택 |
| **Gemini** | API Key + 모델 선택 |

> **보안**: API Key는 UI에서만 입력하세요. 코드에 절대 넣지 마세요.

---

## 사용 예시

1. **📁 Files** 에서 엑셀 파일 업로드
2. **💬 Chat** 에서 요청:
   - `"5개 파일을 하나로 합치고 동일 항목은 평균으로 계산해줘"`
   - `"비목별 집행률을 계산해줘"`
   - `"이월예산과 당해예산 잔액이 큰 순으로 정렬해줘"`
3. **▶ 코드 실행** → 실패 시 AI가 자동으로 수정·재실행
4. 결과 파일 다운로드

---

## 프로젝트 구조

```
llm-excel-studio/
├── app.py                  # 메인 채팅 페이지
├── pages/
│   ├── 1_Files.py          # 파일 관리
│   └── 2_Settings.py       # 모델 설정
├── core/
│   ├── llm/                # Ollama · OpenAI · Gemini 클라이언트
│   ├── prompt/             # 페르소나 · 시스템 프롬프트 생성
│   ├── executor/           # AST 샌드박스 + 자동 재시도
│   └── files/              # 파일 I/O · 병합셀 전처리 · LLM 컨텍스트
├── run.sh / stop.sh        # 서버 실행/종료
└── requirements.txt
```
