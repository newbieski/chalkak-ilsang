# Mini PJT 과제 규약 메모

출처: 강의 자료 "[Day 8,9,10] mini PJT"
참고(사용법 튜토리얼일 뿐 규약 아님): 강의 자료 "[Day 8,9,10] AI로 개발하기 with Claude Code"

## 1. 개요
- 기간: 3일 (Day8 킥오프·기획 / Day9 개발 / Day10 마감·제출), 각 09:00~18:00
- 형태: 개별 프로젝트
- 목표: Day1~7에서 배운 12개 패턴을 자기 도메인 Agentic RAG 어시스턴트로 구현
- 산출물: 코드 + README + RAGAS 평가 리포트
- 제출: Day10 오후 지정 시각까지 Google Form으로 github 주소 (폼 링크는 강의 자료 참고)
  - ⚠️ 페이지 내 마감 시각 표기가 "최종 정리 + 제출 (15:00)"과 "제출 마감: 14:00 (엄수)"로 엇갈려 있음 — 강사 공지로 재확인 필요
- 총점: 100점, 세부 배점 별도 산정

## 2. 일정별 체크리스트

### Day 8 · 킥오프·기획
원문 블록 제목("기획 마무리 + 인-아웃 세트 + 서비스 스펙")의 세 항목과 1:1 대응:
- [x] **기획 마무리** — SERVICE.md 완성 (5. 성공 기준에 최소 통과율 숫자 명시 포함)
- [x] **인-아웃 세트** — evaluation/test_queries.csv 최소 10건(권장 15~20건) 작성 — 20건 완료
- [x] **서비스 스펙** — 데이터·도구 준비 (`data/photos.json` 30건 · `data/tones.json` · 도구 4개 확정) · 실제 이미지 파일도 이후 수집·커밋 완료 (`data/PHOTO_CREDITS.md` 출처 정리)
- [ ] Day 종료 15분 전 강사에게 진도 공유 (SERVICE.md·CSV 완성 확인) — 실시간 진행 상황 공유라 기록으로 남길 수 없는 항목, Day8 이미 지남

### Day 9 · 개발
- [x] 실제 개발 (에이전트·도구·RAG·가드레일·트레이스 붙이기) — 구현 완료, 이후 실제 Bedrock 호출로 반복 검증함 (자세한 내용은 DEVPLAN.md·PROGRESS.md)
- [x] MCP 연동 (선택) — 생략하기로 확정 (마땅히 연동할 외부 도구가 없음)
- [x] test_queries.csv로 자체 평가 반복 (LLM-as-Judge 방식) · 개선 사이클 — round1(17/20) → round2(18/20 기계 채점·20/20 사람 확인) 완료
- [x] `evaluation/round1_report.md` 저장
- [ ] 강사 1:1 순회 리뷰 (인당 5~10분) — 실시간 리뷰라 기록으로 남길 수 없는 항목, Day9 이미 지남

### Day 10 · 마감·제출·랩업
- [x] 개발 마무리
- [x] `evaluation/round2_report.md` 저장 (1차 대비 개선폭 명시)
- [x] 코드 정리·리팩터링, README.md 완성 (트라이앤에러 회고 포함)
- [x] (선택) Docker 재빌드·클린 환경 재현성 검증 — 하지 않기로 결정 (Dockerfile 자체를 만들지 않음, PoC 규모라 `run.sh`로 충분하다고 판단)
- [ ] Google Form 제출 (github 주소 또는 zip + 구현 시연 캡처본)
- [ ] 마감 전 재제출 가능 — 최종 제출본(동일 이름 기준 최신)만 채점 대상 (제출 관련 유의사항, 별도 액션 아님)

## 3. 필수 산출물 구조 (제출 규약 — CLAUDE.md 폴더 구조와 동일)
```
mini-pjt_{본인이름}/
├── src/
│   ├── agent.py        # 메인 에이전트 그래프
│   ├── tools.py        # 도메인 도구
│   ├── retriever.py    # RAG 파이프라인
│   └── ...
├── data/                       # 사용한 문서·데이터
├── evaluation/
│   ├── test_queries.csv        # 인-아웃 세트
│   ├── round1_report.md        # 1차 자체 평가 (Day 9)
│   └── round2_report.md        # 2차 자체 평가 (Day 10 · 개선 후)
├── SERVICE.md
├── Dockerfile                  # 선택
├── requirements.txt
├── README.md
└── run.sh                      # 선택
```

## 4. API 스펙 (표준 규약)
```
POST /query
Content-Type: application/json
Body: {"question": "사용자 질의"}
Response:
{
  "answer": "근거 기반 응답",
  "contexts": [{"doc_id": "...", "text": "..."}, ...],
  "trace": [{"step": "retrieve", "input": "...", "output": "..."}, ...]
}
```

## 5. test_queries.csv 스키마
- 최소 10건, 권장 15~20건
- 컬럼 7개: `id`(필수) · `category`(필수, positive/negative/edge/guardrail) · `input`(필수) · `expected_traits`(필수) · `forbidden`(선택) · `expected_tools`(선택) · `note`(선택)
- 권장 카테고리 비율: positive 40% · negative 20% · edge 25% · guardrail 15%
- 다중값은 세미콜론(`;`)으로 구분, 여러 줄 필드는 큰따옴표로 감쌈

## 6. 빌드 체크리스트 · 12개 패턴
6개 이상 적용 권장. 필수(산출물 규약상 요구): **1(구조화 출력) · 3(RAG) · 11(트레이스) · 12(평가: RAGAS·LLM-as-Judge)**

| # | 패턴 | Day | 우리 프로젝트 적용 지점 |
|---|---|---|---|
| 1 | LCEL chain (Pydantic 구조화 출력) | Day1 | answer/contexts/trace 구조화 응답 |
| 2 | ReAct (도구 자율 선택) | Day3 | search_photos/generate_caption/get_photo 자율 호출 |
| 3 | RAG (하이브리드 검색·리랭킹·쿼리 확장) | Day2 | 사진 태그·설명 검색 |
| 4 | 도구 다중 결합 | Day4 | 검색+상세조회+캡션생성 조합 |
| 5 | MCP 서버 연동 | Day4 | 선택 |
| 6 | 가드레일 (PII·프롬프트 인젝션 방어) | Day5 | SERVICE.md 4번 정책 |
| 7 | HITL (위험 작업 승인) | Day5 | 공유·내보내기 시 사생활 경고 확인 |
| 8 | 미들웨어 (요약·마스킹·재시도) | Day5 | 선택 |
| 9 | Multi-Agent Supervisor | Day6 | 선택 |
| 10 | Plan-Execute·장기 메모리 | Day7 | 선택 |
| 11 | Observability·Trace | Day7 | API 응답의 trace 필드 |
| 12 | 평가 (RAGAS·LLM-as-Judge) | Day7 | round1/round2 report |

## 7. 채점 기준
- SERVICE.md 품질 (도메인 명확성·인-아웃 세트 구체성·측정 가능성·가드레일 정의)
- 서비스 임팩트 (사용자 문제·가치의 뾰족함)
- 에이전트 개발 완성도 (구현·아키텍처·코드 품질)
- 기획 인-아웃 세트 충족도 (본인 세트 통과율·1차→2차 개선폭)
- 가드레일 준수 여부 (정의한 제약을 실제로 지키는가)
