# 웹툴박스 (WebToolBox)

Cloudflare Pages에 배포하는 정적 사이트입니다. 빌드 과정이 없는 순수 HTML/CSS/JS로 구성되어 있어,
저장소를 그대로 Cloudflare Pages에 연결하면 별도 빌드 설정 없이 배포할 수 있습니다.
(Build command: 없음 / Build output directory: `/` 저장소 루트)

## 폴더 구조

```
/
├── index.html              # 홈 (기능 목록)
├── about.html               # 사이트 소개
├── privacy.html              # 개인정보처리방침
├── 404.html                  # Cloudflare Pages가 자동으로 사용하는 404 페이지
├── robots.txt
├── sitemap.xml
├── assets/
│   ├── css/style.css         # 공통 스타일 (라이트/다크 테마, 네비게이션, 카드, 버튼 등)
│   └── js/main.js            # 공통 스크립트 (테마 토글, 모바일 메뉴, 활성 메뉴 표시)
└── tools/
    ├── json-formatter.html   # JSON 포매터 기능 페이지
    ├── json-formatter.css    # JSON 포매터 전용 스타일
    └── json-formatter.js     # JSON 포매터 로직 (검증/렌더링/검색/접기펼치기)
```

## 새 기능(도구)을 추가하는 방법

이 프로젝트는 "index 기반으로 기능이 계속 추가되는" 구조를 염두에 두고 만들었습니다.
새 도구를 추가할 때는 아래 순서를 따르면 됩니다.

1. `tools/` 아래에 `새기능.html`, 필요하면 `새기능.css`, `새기능.js`를 추가합니다.
   (`tools/json-formatter.html`을 복사해서 시작하면 헤더/푸터/테마 스크립트를 그대로 재사용할 수 있습니다.)
2. `index.html`의 `.card-grid` 안에 새 기능 카드를 추가합니다. (`is-soon` 클래스가 붙은
   "준비 중" 카드를 실제 링크로 바꾸는 방식이 가장 쉽습니다.)
3. 모든 페이지 상단 `<ul class="nav-links">` 안에 새 메뉴 링크를 추가합니다.
   (헤더/푸터 마크업은 빌드 도구 없이 각 HTML 파일에 그대로 복사되어 있으므로, 메뉴가 바뀌면
   각 페이지에서 동일하게 반영해줘야 합니다.)
4. `sitemap.xml`에 새 페이지 URL을 추가합니다.
5. 새 페이지의 `<head>`에도 다른 페이지처럼 `title`, `meta description`, `canonical`,
   FOUC 방지용 테마 인라인 스크립트를 그대로 넣어줍니다.

## 배포 전에 확인할 것

- 모든 HTML의 `canonical`, `og:url`, `sitemap.xml`, `robots.txt`에 있는
  `https://example.com`을 실제 배포 도메인으로 일괄 치환하세요.
- Google AdSense를 실제로 적용하면 `privacy.html`의 3번 항목(광고 서비스 이용에 관한 사항)
  내용이 실제 운영 방식과 일치하는지 다시 확인하세요.
- 연락처 이메일은 `hongsh119@gmail.com`으로 되어 있습니다. 다른 주소를 쓰려면
  `about.html`, `privacy.html`의 `mailto:` 링크를 함께 변경하세요.

## JSON 포매터 기능 요약

- 입력 즉시(디바운스 250ms) JSON 유효성 검사, 유효하지 않으면 대략적인 줄/열 위치 표시
- 들여쓰기(2/4/Tab)를 적용한 트리 뷰, 키/문자열/숫자/불리언/null 별 색상 구분
- 노드별 접기/펼치기 토글, 전체 펼치기/접기 버튼
- 키·값 텍스트 검색, 일치 항목 강조 및 이전/다음 이동(Enter / Shift+Enter)
- 포맷된 텍스트 복사, 압축(minify) 복사, `.json` 파일 다운로드
- 입력 데이터는 서버로 전송되지 않고 브라우저(자바스크립트) 안에서만 처리됩니다.
