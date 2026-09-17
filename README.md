# 미니 PJT: 찰칵일상 (Chalkak-ilsang)

## 무엇을 푸나
개인 사진첩을 정리하고 싶은 사람이, 사진마다 어울리는 설명 글을 직접 써야 하고 원하는 기준으로 찾기도 어려운 문제를 푼다 — 사진을 올려두면 원하는 톤·분량으로 설명을 자동으로 받고, 자동 태그로 자연어·필터 검색까지 할 수 있다.

## 활용한 패턴 (Day 1~7)
- Day 1: LCEL chain (구조화 출력) — `POST /query` 응답을 `answer`/`contexts`/`trace` 로 구조화
- Day 2: RAG — `retriever.py` 의 태그·텍스트 검색으로 사진을 찾음
- Day 3: ReAct (도구 자율 선택) — `create_agent` 가 상황에 따라 4개 도구 중 필요한 것만 부름
- Day 4: 도구 다중 결합 — 검색 → 상세조회 → 캡션생성을 한 대화 안에서 조합
- Day 5: 가드레일 — 등록되지 않은 사진에 대해 지어내지 않기, 지정하지 않은 톤·분량 임의 변경 금지 (SERVICE.md 4번)
- Day 7: Observability — 도구 호출 내역을 `trace` 필드로 노출
- Day 7: 평가 — `evaluation/test_queries.csv` 인-아웃 세트로 자체 평가 (아래 결과 참고)

## 아키텍처
```
사용자(웹 UI, PoC)
  └─ 사진 클릭 + 요청 문구 입력
       └─ "photo_id::요청문구" 형태로 조립
            └─ POST /query { "question": "..." }
                 └─ src/agent.py
                      ├─ _parse_question(): photo_id 분리
                      ├─ create_agent(ChatBedrockConverse, tools=4개, system_prompt=가드레일)
                      │     ├─ index_photos    ─┐
                      │     ├─ generate_caption ─┼─ src/tools.py (도메인 도구)
                      │     ├─ search_photos    ─┤     └─ src/retriever.py (data/photos.json 읽기·쓰기·검색)
                      │     └─ get_photo       ─┘
                      └─ 도구 호출 결과를 answer/contexts/trace 로 구조화해 응답
```
사진 원본 파일은 로컬에만 두고(`data/*.jpg`, git 미포함), 태그·캡션 등 메타데이터만 `data/photos.json` 에 커밋된다. 톤 프리셋·커스텀 톤 샘플은 `data/tones.json`.

## 실행 방법
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # BEDROCK_MODEL_ID, AWS_REGION, AWS 자격증명 채우기
uvicorn src.agent:app --host 0.0.0.0 --port 8000   # 서버로 실행
# 또는 CLI로 빠르게 확인
python -m src.agent "작년 여름 제주도 사진 보여줘"
```
`run.sh` 도 위 과정을 그대로 수행한다. 서버 실행 후 브라우저로 `http://localhost:8000/` 에 접속하면 사진 목록·선택·요청 입력이 되는 데모 페이지(`static/index.html`, PoC 수준)가 뜬다.

## RAGAS 평가 결과
_(Day9 자체 평가 진행 후 채움)_
- context_recall:
- context_precision:
- faithfulness:
- answer_relevancy:

## 인-아웃 세트 통과율 (자체 평가)
_(Day9/Day10 자체 평가 진행 후 채움 — evaluation/round1_report.md, round2_report.md 참고)_
- 1차 (Day 9 종료): XX / 20 통과
- 2차 (Day 10 개선 후): XX / 20 통과
- 개선폭:

## 트라이앤에러 회고
_(진행하며 채워나감 — 자세한 경위는 PROGRESS.md 참고)_
- 패키지를 처음에 전역 파이썬에 설치했다가 가상환경(.venv)으로 정정
- "샘플 사진은 풍경 위주로만" 결정을 한 번 내렸다가, SERVICE.md의 가드레일 정책(인물·GPS 감지 시 경고)과 앞뒤가 안 맞아 되돌림
- Bedrock 호출은 코드상 문제 없이 도달했지만 계정 하루 토큰 한도(ThrottlingException)에 걸려 재시도 대기 중

## 핵심 코드 위치
- `src/agent.py:37` — `_build_agent()`: 4개 도구를 묶은 에이전트 생성
- `src/agent.py:47` — `_parse_question()`: `photo_id::요청` 파싱
- `src/agent.py:58` — `ask()`: 에이전트 호출 후 answer/contexts/trace 조립
- `src/agent.py:86` — `POST /query` 엔드포인트
- `src/tools.py:70` — `index_photos`: 사진 일괄 태깅
- `src/tools.py:118` — `generate_caption`: 톤·분량 반영 캡션 생성
- `src/tools.py:156` — `search_photos`, `src/tools.py:177` — `get_photo`
- `src/retriever.py:41` — `search()`: 태그·텍스트·기간 기반 검색
- `static/index.html` — 데모용 정적 페이지 (사진 목록·선택·요청 입력, PoC 수준). `src/agent.py`의 `GET /`, `GET /data/*` 로 서빙됨
