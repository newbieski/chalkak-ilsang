# 미니 PJT: 찰칵일상 (Chalkak-ilsang)

## 무엇을 푸나
개인 사진첩을 정리하고 싶은 사람이, 사진마다 어울리는 설명 글을 직접 써야 하고 원하는 기준으로 찾기도 어려운 문제를 푼다 — 사진을 올려두면 원하는 톤·분량으로 설명을 자동으로 받고, 자동 태그로 자연어·필터 검색까지 할 수 있다.

## 활용한 패턴 (Day 1~7)
- Day 1: LCEL chain (구조화 출력) — `POST /query` 응답을 `answer`/`contexts`/`trace` 로 구조화
- Day 2: RAG — `src/embeddings.py`(Bedrock Titan Embed Text v2)로 태그·캡션을 임베딩해두고, `retriever.py`가 질의어와의 코사인 유사도(+키워드 보너스)로 의미 검색
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
                      ├─ build_chat_model() (src/model.py) — 기본 모델 호출 실패(스로틀링 등) 시
                      │     후보 모델 목록으로 자동 전환하는 모델을 만듦 (with_fallbacks)
                      ├─ create_agent(model, tools=4개, system_prompt=가드레일+오늘 날짜)
                      │     ├─ index_photos    ─┐
                      │     ├─ generate_caption ─┼─ src/tools.py (도메인 도구, 모델 호출은 model.py 공용)
                      │     ├─ search_photos    ─┤     └─ src/retriever.py (data/photos.json 읽기·쓰기·검색)
                      │     └─ get_photo       ─┘
                      └─ 도구 호출 결과를 answer/contexts/trace 로 구조화해 응답
```
사진 원본 파일은 로컬에만 두고(`data/*.jpg`, git 미포함), 태그·캡션 등 메타데이터만 `data/photos.json` 에 커밋된다. 톤 프리셋·커스텀 톤 샘플은 `data/tones.json`.

### 사용자 인터페이스 흐름
`static/index.html` 기준. 사진을 고르면 캡션 작업 패널이, 안 고르면 일반 검색창이 뜬다.

```mermaid
flowchart TD
    A[사진 목록 확인 - 완료/미작업 배지] --> B{사진을 선택했는가?}
    B -- 아니오 --> C[일반 질문 입력 예: 바다 사진 보여줘]
    C --> D[POST /query]
    D --> E[검색 결과 answer/contexts/trace 표시]

    B -- 예 --> F[작업 패널: 기존 캡션·태그 표시]
    F --> G[생성 요청 입력 또는 기본값]
    G --> H["문장 생성" 클릭 -> POST /query]
    H --> I[캡션 박스에 결과 채움 - 아직 미저장]
    I --> J[사용자가 캡션 직접 수정]
    J --> K["확정" 클릭 -> PUT /photos/id/caption]
    K --> L[저장 완료, 배지 갱신]
    I -.만족 안 되면 다시 요청.-> G
```

### 요청·데이터 흐름
사진을 선택해 캡션을 생성·확정하는 경우의 전체 호출 경로.

```mermaid
sequenceDiagram
    participant U as 사용자(브라우저)
    participant W as static/index.html
    participant A as agent.py (FastAPI)
    participant G as LangGraph 에이전트
    participant T as tools.py
    participant R as retriever.py
    participant D as data/photos.json

    U->>W: 사진 클릭 + 요청 입력
    W->>A: POST /query {question: "p001::담백하게 2문장"}
    A->>A: _parse_question() - photo_id 분리
    A->>G: agent.invoke(messages)
    G->>T: generate_caption(photo_id, tone, length)
    T->>R: find_by_id(photo_id)
    R->>D: 읽기
    D-->>R: 사진 메타데이터
    T->>T: Bedrock 비전 모델 호출 (이미지+프롬프트, 스로틀링 시 model.py가 대체 모델로 전환)
    T->>R: update_photo(caption=...) - 자동 임시 저장
    R->>D: 쓰기
    T-->>G: 캡션 텍스트 반환 (ToolMessage)
    G-->>A: 메시지 목록
    A->>A: trace/contexts/answer 조립 + 토큰 로그 출력
    A-->>W: {answer, contexts, trace}
    W-->>U: 캡션 박스에 표시 (확정 전)

    U->>W: 내용 수정 후 확정 클릭
    W->>A: PUT /photos/p001/caption {caption: 수정본}
    A->>R: update_photo(caption=수정본)
    R->>D: 쓰기
    A-->>W: 갱신된 사진 레코드
    W-->>U: 배지를 "완료"로 갱신
```

### 데이터 저장 구조
| 파일 | 역할 | 주요 필드 |
|---|---|---|
| `data/photos.json` | 사진별 메타데이터·인덱싱 결과 저장소. `retriever.py`가 유일한 읽기·쓰기 창구 | `id`, `filename`, `taken_at`/`location`(검증 안 되면 `null`), `tags`(리스트), `caption`, `caption_tone`, `embedding`(태그+캡션의 1024차원 의미 검색용 벡터) |
| `data/tones.json` | 톤 프리셋 + 사용자 커스텀 톤 샘플 | `presets[].{id,name,guide,default}`, `custom.{id,guide,samples[]}` |
| `data/PHOTO_CREDITS.md` | 샘플 사진 출처·라이선스 (사진 원본은 git 미포함이라 근거만 기록) | - |

`retriever.py`의 `load_photos`/`save_photos`/`update_photo`가 파일 전체를 읽고 다시 쓰는 방식이라(원자적 트랜잭션 아님), 여러 요청이 동시에 같은 사진을 고치는 상황은 고려하지 않았다 (PoC 범위).

### 응답 출력 형식
`POST /query`는 항상 아래 세 키만 돌려준다 (CLAUDE.md 제출 규약).
```json
{
  "answer": "모델이 만든 최종 답변 문자열",
  "contexts": [
    {"doc_id": "search_photos", "text": "도구가 실제로 반환한 내용"}
  ],
  "trace": [
    {"step": "search_photos", "input": null, "output": "도구가 반환한 원문"}
  ]
}
```
`contexts`/`trace`는 에이전트가 실행 중 호출한 도구(`ToolMessage`) 하나당 한 항목씩 쌓인다. `PUT /photos/{id}/caption`은 이 계약과 무관한 앱 전용 엔드포인트로, 갱신된 사진 레코드(JSON)를 그대로 돌려준다.

**모델 폴백**: Bedrock은 모델별로 별도의 사용량 한도가 있어, 기본 모델(`.env`의 `BEDROCK_MODEL_ID`)이 스로틀링(`ThrottlingException` 등 `ClientError`)에 걸리면 `src/model.py`의 `FALLBACK_MODEL_IDS` 목록(Claude Sonnet/Haiku 최신 버전, Amazon Nova 계열 등)을 순서대로 자동 시도한다. `agent.py`(대화용 모델)·`tools.py`(이미지 인식용 모델) 둘 다 이 모듈을 통해 모델을 만든다. Bedrock을 호출하는 모든 지점(`ask()`, `index_photos`, `generate_caption`)은 실제로 응답한 모델명과 입출력 토큰 수를 `[tokens] ...` 로그로 남긴다.

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
- Bedrock은 계정 전체가 아니라 **모델별로** 사용량 한도가 있어, 기본 모델이 스로틀링되면 대체 모델 목록으로 자동 전환하도록 함 (`src/model.py`)
- `data/photos.json`의 `location`(예: "제주 협재해변") 값이 실제 사진 내용과 무관한 옛 더미 데이터였는데, 그걸 그대로 캡션 프롬프트에 "참고 정보"로 넣어 근거 없는 사실을 캡션에 반영하는 문제가 있었음 — 위치 메타데이터를 전부 제거하고, "메타데이터가 있다고 사실처럼 반영하지 않는다"는 원칙을 SERVICE.md·프롬프트에 명문화

## 핵심 코드 위치
- `src/model.py:21` — `build_chat_model()`: 기본 모델 실패 시 후보 목록으로 자동 전환하는 모델 생성 (`with_fallbacks`)
- `src/agent.py:23` — `_system_prompt()`: 가드레일 + 오늘 날짜(상대 날짜 표현 계산용) 포함한 시스템 프롬프트
- `src/agent.py:43` — `_build_agent()`: 4개 도구를 묶은 에이전트 생성
- `src/agent.py:53` — `_parse_question()`: `photo_id::요청` 파싱
- `src/agent.py:64` — `ask()`: 에이전트 호출 후 answer/contexts/trace 조립 + 토큰 사용량 로깅
- `src/agent.py:104` — `POST /query` 엔드포인트
- `src/agent.py:120` — `PUT /photos/{photo_id}/caption`: 사용자가 고친 캡션 확정 저장 (에이전트 미경유 앱 기능)
- `src/tools.py` — `index_photos`·`generate_caption`·`search_photos`·`get_photo` 4개 도구
- `src/embeddings.py:17` — `embed_text()`: Bedrock Titan Embed Text v2로 텍스트를 벡터로 변환
- `src/retriever.py:66` — `reembed()`: 태그+캡션 기반 임베딩 재계산·저장 (`index_photos`·`generate_caption`이 갱신 시점마다 호출)
- `src/retriever.py:120` — `search()`: 키워드+의미(코사인 유사도) 하이브리드 검색
- `static/index.html` — 데모용 정적 페이지 (사진 목록·선택·요청 입력, PoC 수준). `src/agent.py`의 `GET /`, `GET /data/*` 로 서빙됨
