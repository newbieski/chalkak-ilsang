# DESIGN

## 사용 방식
UI 디자인은 방식(스킬·도구)별로 브랜치를 따서 시도한다. main의 이 문서에는 시도와 무관하게 공통으로 유지할 참고 자료·방향만 두고, 각 브랜치에서 그 방식에 맞는 세부 내용(사용 스킬, 생성된 디자인 시스템, 적용 과정, 진행 상태)을 이어서 기록한다. 시도가 끝나면(채택하든 보류하든) 아래 "시도 이력"에 결과를 한 줄로 남긴다.

## 참고 자료 (UI/디자인 관련)
- [Hallmark](https://www.usehallmark.com/)
- [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/) — UI/UX 스킬
- [figma.com](https://figma.com)
- html to design — 떠있는 웹사이트를 바로 익스포트
- Figmato html — 피그마 요소를 html로
- [seed-design.io](https://seed-design.io)

## 방향 (모든 시도에 공통으로 적용할 기준)
- **분위기**: 개인 사진 일기장 느낌 — 따뜻하고 편안한, 마케팅 랜딩페이지처럼 화려하지 않게. Glassmorphism·Neumorphism 같은 장식적인 트렌드 스타일보다는 정갈한 미니멀/소프트 UI 쪽
- **색상**: 사진 자체가 화면의 주인공이 되도록 배경·UI는 차분한 중성 톤 + 포인트 컬러 하나만
- **타이포그래피**: 읽기 편한 기본 서체 위주
- **레이아웃 우선순위**:
  - 사진 그리드(완료/미작업 배지)는 지금 구조 유지, 시각적으로만 다듬기
  - 사진 선택 시 큰 미리보기 + 작업 패널이라는 현재 흐름은 그대로 두고 스타일만 개선
  - 모바일 폭에서도 깨지지 않게 (PoC 데모지만 최소한의 반응형은 고려)
- **하지 않을 것**: 기능·흐름 자체를 바꾸는 리디자인은 아님 — 지금 있는 기능(태그 편집, 캡션 생성·수정·확정, 검색, 톤 등록, 새 사진 불러오기)의 시각적 마감만 개선

## 시도 이력
### 1차 — ui-ux-pro-max 스킬 (보류)
- 브랜치: `design/ui-ux-pro-max-v1`
- Soft UI Evolution 스타일(웜 브라운 프라이머리 + 인디고 액센트, Caveat/Quicksand 타이포그래피)로 색상·폰트·app-shell 카드 구조까지 적용했으나, 실사용 확인 결과 "특별히 바뀐 느낌이 없다"는 평가로 보류. 세부 내용·생성된 디자인 시스템은 해당 브랜치의 DESIGN.md 참고

### 2차 — Hallmark 스킬 (진행 중)
- 브랜치: `design/hallmark-v1`
- 스킬: [Hallmark](https://github.com/nutlope/hallmark) — "anti-AI-slop" 디자인 스킬. `npx skills add nutlope/hallmark`로 설치(`.agents/skills/hallmark/`, `.claude/skills/hallmark`는 심볼릭 링크). `hallmark redesign ./static/index.html --mood "warm, soft, minimal personal photo diary"` 형태로 호출, 기존 구현(id·JS 로직) 경계 안에서만 시각/구성 레이어를 다시 설계하는 `redesign` verb의 single-page flow를 따름.
- 적용 내용:
  - **팔레트**: 커스텀(tuned) OKLCH 톤 — vibe "quiet warm paper journal, soft ink, unhurried". paper `oklch(94% 0.014 70)`(따뜻한 크림), accent `oklch(44% 0.13 35)`(차분한 클레이/테라코타 단일 포인트). 1차 시도의 브라운+인디고 투톤과 달리 단일 웜톤 계열로 통일
  - **타이포그래피**: 제목 `Newsreader`(로만 세리프, 일기장 같은 문학적 느낌) + 본문 `Switzer`(중립 산세리프) 2폰트 페어링 — 손글씨체(Caveat)를 썼던 1차 시도와는 완전히 다른 방향
  - **레이아웃**: "card-in-card" 금지 원칙에 따라 중첩 카드 박스를 없애고, 헤어라인 구분선(`<hr class="section-rule">`)과 여백 리듬으로 섹션을 구분. 사진 그리드는 flex-wrap → CSS grid로, 매크로스트럭처 카탈로그 중 "Portfolio Grid"(작업물이 곧 컨텐츠인 그리드) 보이스를 차용해 적용 — 다만 실제 매크로스트럭처는 마케팅 페이지 전용이라 우리 앱(단일 화면 유틸리티 도구)엔 그대로 맞지 않아 보이스만 참고하고 구조(사진 그리드→선택→패널 흐름)는 그대로 유지
  - **접근성**: 스킬의 색 대비 기준(WCAG 4.5:1 텍스트/3:1 UI 경계)에 맞춰 초안의 accent·muted 값을 더 어둡게 재조정함(대비 계산 후 수정). 사진 그리드에 키보드 포커스(tabindex/role/Enter·Space)와 alt 텍스트 추가
  - **버튼**: Hallmark의 "accent는 하이라이트지 배경 칠이 아니다" 원칙에 따라 기본 상태는 accent 테두리+텍스트, hover 시에만 accent로 채움 (1차 시도의 상시 필박스 버튼과 다른 보이스)
- 상태: 로컬 서버로 렌더링 확인 완료(`static/index.html`이 서빙된 페이지와 바이트 일치). 사용자 최종 확인 대기 중
