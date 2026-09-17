# DEVPLAN · 개발 진행 계획 (초안)

무엇을 왜 만드는지는 SERVICE.md, 과제 규약은 MINIPJT.md, 끝난 일의 기록은 PROGRESS.md 참고.
이 문서는 **앞으로 일을 어떤 순서·구조로 진행할지**를 담고, 진행하면서 계속 고쳐 쓴다. 완료된 일의 기록이 아니라 계획이라 PROGRESS.md와 분리했다.

## 두 축

### 트랙 A — 사진 인덱싱 ("사진을 올리는 부분")
사용자가 파일을 올리는 UI가 아니라, **`data/` 밑에 이미 놓인 사진을 읽어 태그·메타를 채우는 백엔드 파이프라인**이다. 사용자 업로드 기능은 이번 범위 밖(SERVICE.md 2번 확장 관점 참고).
- 담당 도구: `index_photos`
- 담당 파일: `src/tools.py`(도구 로직), `src/retriever.py`(태그·설명 기반 검색 인덱스)
- 산출물: `data/photos.json`의 각 사진 항목에 `tags`, `caption` 자동 채움 (또는 캡션은 트랙 B에서 생성 시점에 채움 — 아래 열린 질문 참고)

### 트랙 B — 캡션 생성·조회 ("문장을 생성하는 부분")
사용자가 사진을 지목해 캡션을 만들거나, 사진을 찾는 쪽.
- 담당 도구: `generate_caption`, `search_photos`, `get_photo`
- 담당 파일: `src/tools.py`(도구 로직), `src/agent.py`(에이전트 그래프로 도구 연결, 구조화 응답, trace)

## 트랙 간 관계
`search_photos`는 트랙 A가 채운 태그에 의존한다. 그래서 **트랙 A를 먼저 최소한으로 돌려 `data/photos.json`에 태그를 채운 뒤, 트랙 B를 붙이는 순서**를 제안한다. 다만 `generate_caption`(이미지를 직접 보고 문장을 만드는 도구)은 트랙 A와 독립적이라 순서를 바꿔도 무방하다.

## 우선순위 원칙 (강사 리뷰 반영, Day9)
이미지 기반 태그 추출은 프롬프트 특성상 정확도가 들쭉날쭉할 수 있다는 지적을 받았다. 그래서:
- 트랙 A는 **딱 돌아가는 최소 버전**으로 끝내고, 애매한 태그는 SERVICE.md 정책대로 "추정 표시"로 남기는 선에서 멈춘다 — 여기서 정확도를 더 끌어올리려고 시간을 쓰지 않는다
- 대신 트랙 B(`generate_caption`, `search_photos`)를 안정화하는 데 더 공을 들인다
- `test_queries.csv` 통과율은 트랙 B가 안정된 뒤에 확인한다 (자세한 배경은 PROGRESS.md Day9 강사 리뷰 참고)

## 오늘 진행 순서 (Day9 진행 상황)
1. ✅ 실제 사진 파일 확보 → `data/`에 배치 — 30장(위키미디어 공용, 라이선스 확인됨)
2. ⏳ 트랙 A: `retriever.py`, `index_photos` 구현 완료 · **실행은 p001 1건만 성공, 나머지 29장은 Bedrock 계정 하루 한도로 대기 중**
3. ✅ 트랙 B: `generate_caption` → `search_photos` → `get_photo` 구현 완료 (실제 호출 검증은 Bedrock 한도 풀려야 가능)
4. ✅ `agent.py`: 4개 도구를 묶는 에이전트 그래프 + 가드레일 + trace + `POST /query` 구현 완료. mock 모델로 메시지 조립 로직(trace/contexts/answer)까지는 검증됨
5. ⏳ `test_queries.csv` 20건 자체 평가 → `evaluation/run_eval.py` 채점 스크립트는 완성, **실행은 Bedrock 한도 풀려야 가능**
6. ✅ (계획에 없었지만 추가) `static/index.html` PoC 데모 페이지 + `GET /`, `GET /data/*` 정적 서빙

## 열린 질문
- ~~사진 실제 파일 10장 확보 여부~~ → 해결: 30장, 위키미디어 공용 라이선스 확인(`data/PHOTO_CREDITS.md`)
- ~~UI에서 고른 사진 ID를 `question`에 어떻게 실을지~~ → 해결: `photo_id::요청` 구분자 형식, `static/index.html`에 구현
- ~~`index_photos`가 캡션까지 미리 만들지~~ → 해결: 태그만 채우고, 캡션은 `generate_caption` 요청 시점에만 생성
- **MCP 연동 여부** (12개 패턴 중 5번, 선택) — 아직 미정. 남은 시간·토큰(Bedrock 한도) 감안하면 생략 쪽으로 기울어 있음, 최종 결정 필요
- Bedrock 계정 하루 한도 해제 시점 — 풀리는 대로 2·3·5번 항목 실행 이어감
