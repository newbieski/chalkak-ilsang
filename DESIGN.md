# DESIGN

## 참고 자료 (UI/디자인 관련)
- [Hallmark](https://www.usehallmark.com/)
- [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/) — UI/UX 스킬
- [figma.com](https://figma.com)
- html to design — 떠있는 웹사이트를 바로 익스포트
- Figmato html — 피그마 요소를 html로
- [seed-design.io](https://seed-design.io)

## UI 개편 작업

### 사용할 스킬
[ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — AI 코딩 도구용 디자인 시스템 자동 생성 스킬. 스타일 79종·업계별 색상 팔레트 192종·폰트 페어링 74종·UX 가이드라인 119개 데이터베이스에서 자연어 요청으로 추천·적용해줌.
`npm install -g ui-ux-pro-max-cli` → `uipro init --ai claude` 로 설치 완료 (`.claude/skills/ui-ux-pro-max/` 등). 부가로 `design`·`design-system`·`ui-styling`·`brand`·`banner-design`·`slides` 스킬도 같이 설치됨.

### 방향 (스킬에 요청할 때 기준으로 삼을 것)
- **분위기**: 개인 사진 일기장 느낌 — 따뜻하고 편안한, 마케팅 랜딩페이지처럼 화려하지 않게. Glassmorphism·Neumorphism 같은 장식적인 트렌드 스타일보다는 정갈한 미니멀/소프트 UI 쪽
- **색상**: 사진 자체가 화면의 주인공이 되도록 배경·UI는 차분한 중성 톤 + 포인트 컬러 하나만. 지금 쓰던 파란색 액센트(#2563eb)는 유지해도 되고, 스킬이 추천하는 색상 중 사진 톤을 방해하지 않는 걸로 선택
- **타이포그래피**: 읽기 편한 기본 서체 위주 (지금 system-ui 유지 또는 스킬 추천 중 무난한 것)
- **레이아웃 우선순위**:
  - 사진 그리드(완료/미작업 배지)는 지금 구조 유지, 시각적으로만 다듬기
  - 사진 선택 시 큰 미리보기 + 작업 패널이라는 현재 흐름은 그대로 두고 스타일만 개선
  - 모바일 폭에서도 깨지지 않게 (PoC 데모지만 최소한의 반응형은 고려)
- **하지 않을 것**: 기능·흐름 자체를 바꾸는 리디자인은 아님 — 지금 있는 기능(태그 편집, 캡션 생성·수정·확정, 검색, 톤 등록, 새 사진 불러오기)의 시각적 마감만 개선

### 생성된 디자인 시스템 (`--design-system "personal photo diary tool minimal warm"`)
스킬이 준 결과 중 "Pattern"(Scroll-Triggered Storytelling)은 랜딩페이지용이라 우리 앱(기능성 도구)엔 안 맞아 **채택 안 함**. 스타일·색상·타이포그래피만 채택.

- **스타일**: Soft UI Evolution — 부드러운 그림자, 절제된 깊이감, 접근성 고려된 대비. 우리가 원했던 "정갈한 미니멀/소프트 UI"와 일치
- **색상** (따뜻한 저널 브라운 + 잉크 바이올렛 포인트):
  - Primary `#92400E` (따뜻한 브라운), Background `#FFFBEB`(크림), Card `#FFFFFF`
  - Accent `#6366F1`(인디고 바이올렛) — 버튼 등 주요 액션에만
  - Foreground `#0F172A`, Muted `#F8F3F0`, Border `#F1E8E2`, Destructive `#DC2626`
- **타이포그래피**: 제목엔 `Caveat`(손글씨 느낌, 일기장 분위기), 본문·버튼·라벨 등 실제 읽어야 하는 곳엔 `Quicksand`(둥근 산세리프, 가독성 좋음) — Caveat은 장식용으로만 최소 사용 (가독성 때문에 본문엔 안 씀)
- **효과**: 부드러운 그림자, 200-300ms 트랜지션, 포커스 링 유지, `prefers-reduced-motion` 존중
- **피해야 할 것**: 과한 장식

### 진행 상태
- [x] 스킬 설치 (Node.js를 winget으로 새로 설치한 뒤 진행함)
- [x] 스킬로 디자인 시스템 생성
- [x] `static/index.html`에 실제 적용 — CSS 커스텀 프로퍼티(:root 토큰)로 색상·타이포그래피·그림자·트랜지션 정의, 기존 마크업 구조·id·JS 로직(기능 흐름)은 그대로 두고 `<style>` 블록과 인라인 색상값만 교체
- [x] 실제 화면 확인 — 로컬 서버 기동 후 `/` 응답 200, 소스와 서빙된 페이지 바이트 일치 확인. 접근성 보완으로 사진 그리드 썸네일에 `tabindex`/`role="button"`/Enter·Space 키보드 조작과 `alt` 텍스트를 추가함 (기능·흐름 변경이 아닌 시각/접근성 마감 범위 내 추가)

### 보류 — 2026-09-18
색상·폰트·카드 쉘까지 입혀봤지만 실사용 확인 결과 "특별히 바뀌었다는 느낌이 없다"는 평가. 이 시도(위 디자인 시스템 + app-shell/CSS grid 구조 개선까지 포함한 전체)는 `design/ui-ux-pro-max-v1` 브랜치에 그대로 보존해두고, main의 `static/index.html`은 리디자인 이전 상태로 되돌림. 다른 방식으로 UI 작업을 다시 시도할 예정 — 새 방향이 정해지면 이 문서에 이어서 기록한다.