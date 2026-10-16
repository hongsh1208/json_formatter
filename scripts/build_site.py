#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Formix 다국어 정적 사이트 생성기.

- 이 스크립트는 "빌드 타임" 도구입니다. 실행 결과로 나온 완전한 정적 HTML 파일들이
  실제로 Cloudflare Pages에 배포되는 산출물이며, 배포 자체에는 Node/Python 등
  어떤 서버 로직도 필요하지 않습니다 (순수 정적 사이트 유지).
- 기능/페이지를 추가하거나 문구를 수정하려면:
    1) 아래 CONTENT 딕셔너리(또는 urls_for 함수가 참조하는 언어 목록)를 수정
    2) `python3 scripts/build_site.py` 실행
    3) site/ 아래에 새로 생성된 정적 파일을 그대로 배포 폴더에 반영
  이렇게 하면 4개 언어(en/ko/ja/zh) 버전을 매번 손으로 동기화하지 않아도 됩니다.

출력 구조:
  /index.html, /about.html, /privacy.html, /404.html, /tools/json-formatter.html   (English, 기본)
  /ko/index.html, /ko/about.html, /ko/privacy.html, /ko/404.html, /ko/tools/json-formatter.html
  /ja/...  /zh/...  (동일 구조)
모든 내부 링크·에셋 경로는 도메인 루트 기준 절대경로("/...")를 사용하므로
페이지 깊이에 따른 상대경로 계산이 필요 없습니다.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # json_formatter/
SITE_DOMAIN = "https://formix.site"

LANGS = ["en", "ko", "ja", "zh", "es", "vi", "pt", "id", "de"]
DEFAULT_LANG = "en"

# "flag_cc"는 /assets/img/flags/{flag_cc}.svg 파일명(국가 코드, flag-icons 프로젝트 기준).
# 국기 이모지(유니코드 Regional Indicator 쌍)는 Windows(특히 Chrome)에서 글꼴이 지원하지
# 않아 빈 사각형이나 아무것도 표시되지 않는 경우가 많아, 실제 SVG 국기 아이콘을 쓴다.
# "flag" 키는 더 이상 화면에 렌더링하지 않고, 접근성용 보조 텍스트로만 남겨둔다.
LANG_META = {
    "en": {"label": "English", "flag": "\U0001F1FA\U0001F1F8", "flag_cc": "us", "html_lang": "en"},
    "ko": {"label": "한국어", "flag": "\U0001F1F0\U0001F1F7", "flag_cc": "kr", "html_lang": "ko"},
    "ja": {"label": "日本語", "flag": "\U0001F1EF\U0001F1F5", "flag_cc": "jp", "html_lang": "ja"},
    "zh": {"label": "中文", "flag": "\U0001F1E8\U0001F1F3", "flag_cc": "cn", "html_lang": "zh-CN"},
    "es": {"label": "Español", "flag": "\U0001F1EA\U0001F1F8", "flag_cc": "es", "html_lang": "es"},
    "vi": {"label": "Tiếng Việt", "flag": "\U0001F1FB\U0001F1F3", "flag_cc": "vn", "html_lang": "vi"},
    "pt": {"label": "Português", "flag": "\U0001F1E7\U0001F1F7", "flag_cc": "br", "html_lang": "pt-BR"},
    "id": {"label": "Bahasa Indonesia", "flag": "\U0001F1EE\U0001F1E9", "flag_cc": "id", "html_lang": "id"},
    "de": {"label": "Deutsch", "flag": "\U0001F1E9\U0001F1EA", "flag_cc": "de", "html_lang": "de"},
}

# 숫자 읽기 변환기는 단순 번역이 아니라 언어별 숫자 문법(기수·서수·시간·날짜·화폐 표기)을
# 새로 구현해야 하는 도구라서, 1차 다국어 확장(es/vi/pt/id/de)에서는 제외한다.
# 이 목록에 없는 언어에서는 "숫자 읽기 변환기" 링크가 영어판 페이지로 연결된다.
NUMBER_READER_LANGS = ["en", "ko", "ja", "zh"]
# 페이지별로 LANGS 전체가 아니라 일부 언어만 존재할 때 사용하는 예외 테이블.
# (hreflang/sitemap/언어 전환 메뉴가 실제로 존재하는 페이지만 가리키도록 한다.)
PAGE_LANGS = {"tool_number": NUMBER_READER_LANGS}


def langs_for_page(page_key):
    return PAGE_LANGS.get(page_key, LANGS)


SITE_NAME = {l: "Formix" for l in LANGS}

CONTACT_EMAIL = "hongsh119@gmail.com"

# 검색엔진 소유 확인용 메타 태그 (필요한 값만 채우면 모든 페이지 <head>에 자동 삽입됩니다).
# - Google Search Console: "설정 > 소유권 확인 > HTML 태그" 방식에서 나오는 content 값만 넣으면 됨
#   (도메인 전체를 한 번에 확인하려면 Cloudflare DNS에 TXT 레코드를 추가하는 방법도 가능 — 그 경우 이 값은 비워둬도 됨)
# - Bing Webmaster Tools: Search Console에서 가져오기(Import) 하면 별도 설정 불필요
# - Naver 서치어드바이저: 이미 navere88de02083cfff01e4c5a3cf913b0e9c.html 파일로 소유 확인 완료 (별도 설정 불필요)
SEARCH_ENGINE_VERIFICATION = {
    "google": "",  # 예: "abcDEF123..."
    "bing": "",    # 예: "ABCDEF1234567890..."
}

ICON_DATA_URI = (
    'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22>'
    '<rect width=%22100%22 height=%22100%22 rx=%2222%22 fill=%22%232f6feb%22/>'
    '<text x=%2250%22 y=%2266%22 font-size=%2258%22 font-family=%22sans-serif%22 font-weight=%22800%22 '
    'text-anchor=%22middle%22 fill=%22white%22>F</text></svg>'
)


def lang_prefix(lang):
    return "" if lang == DEFAULT_LANG else "/" + lang


def urls_for(lang):
    p = lang_prefix(lang)
    return {
        "home": p + "/",
        "about": p + "/about.html",
        "privacy": p + "/privacy.html",
        "faq": p + "/faq.html",
        "contact": p + "/contact.html",
        "terms": p + "/terms.html",
        "updates": p + "/updates.html",
        "tool": p + "/tools/json-formatter.html",
        "tool_xml": p + "/tools/xml-formatter.html",
        "tool_converter": p + "/tools/json-xml-converter.html",
        "tool_sql": p + "/tools/sql-formatter.html",
        "tool_code": p + "/tools/code-viewer.html",
        "tool_number": (p if lang in NUMBER_READER_LANGS else "") + "/tools/number-reader.html",
        "tool_typing": p + "/games/typing-test.html",
        "game_syntax": p + "/games/syntax-quiz.html",
        "notfound": p + "/404.html",
    }


# 헤더 내비게이션에 노출할 도구 목록. 새 도구를 추가할 때 이 리스트에 (urls_for 키, NAV 라벨 키)만
# 추가하면 헤더/푸터/언어 스위처가 모두 자동으로 반영된다.
TOOL_NAV_ITEMS = [("tool", "tool"), ("tool_xml", "tool_xml"), ("tool_converter", "tool_converter"),
                   ("tool_sql", "tool_sql"), ("tool_code", "tool_code"), ("tool_number", "tool_number")]

# 헤더 내비게이션의 "게임" 드롭다운에 노출할 게임 목록. 포맷터/변환기류와는 성격이 달라
# (재구성이 아니라 재미/도전 요소 위주) 도구 드롭다운과 분리된 전용 드롭다운으로 노출한다.
# 새 게임을 추가할 때도 이 리스트에 (urls_for 키, NAV 라벨 키)만 추가하면 헤더/푸터/
# 관련 링크가 모두 자동으로 반영된다.
GAME_NAV_ITEMS = [("tool_typing", "tool_typing"), ("game_syntax", "game_syntax")]

# 푸터에 노출할 일반 페이지(도구가 아닌 페이지) 목록. 새 페이지를 추가할 때 이 리스트에
# (urls_for 키, NAV 라벨 키)만 추가하면 푸터/사이트맵이 자동으로 반영된다.
FOOTER_NAV_ITEMS = [("about", "about"), ("faq", "faq"), ("updates", "updates"), ("contact", "contact"),
                     ("terms", "terms"), ("privacy", "privacy")]

NAV = {
    "en": {"home": "Home", "tool": "JSON Formatter", "tool_xml": "XML Formatter",
           "tool_converter": "JSON ↔ XML Converter", "tool_sql": "SQL Formatter", "tool_code": "Code Viewer",
           "tool_number": "Number Reader", "tool_typing": "Typing Speed Test", "about": "About",
           "privacy": "Privacy Policy", "faq": "FAQ", "contact": "Contact", "related_h2": "Related",
           "cookie_settings": "Cookie preferences", "terms": "Terms of Service", "updates": "What's New",
           "menu": "Open menu", "dark": "Switch to dark mode", "light": "Switch to light mode",
           "lang": "Select language", "skip": "Skip to content",
           "tools_group": "Tools", "games_group": "Games", "game_syntax": "Coding Syntax Quiz",
           "breadcrumb_aria": "Breadcrumb"},
    "ko": {"home": "홈", "tool": "JSON 포매터", "tool_xml": "XML 포매터",
           "tool_converter": "JSON ↔ XML 변환기", "tool_sql": "SQL 포매터", "tool_code": "코드 뷰어",
           "tool_number": "숫자 읽기 변환기", "tool_typing": "타자 속도 테스트", "about": "사이트 소개",
           "privacy": "개인정보처리방침", "faq": "자주 묻는 질문", "contact": "문의하기", "related_h2": "관련 링크",
           "cookie_settings": "쿠키 설정", "terms": "이용약관", "updates": "업데이트 소식",
           "menu": "메뉴 열기", "dark": "다크 모드로 전환", "light": "라이트 모드로 전환",
           "lang": "언어 선택", "skip": "본문으로 건너뛰기",
           "tools_group": "도구", "games_group": "게임", "game_syntax": "코딩 문법 퀴즈",
           "breadcrumb_aria": "현재 위치"},
    "ja": {"home": "ホーム", "tool": "JSONフォーマッター", "tool_xml": "XMLフォーマッター",
           "tool_converter": "JSON ↔ XML 変換ツール", "tool_sql": "SQLフォーマッター", "tool_code": "コードビューア",
           "tool_number": "数字の読み方変換", "tool_typing": "タイピング速度テスト", "about": "サイト紹介",
           "privacy": "プライバシーポリシー", "faq": "よくある質問", "contact": "お問い合わせ", "related_h2": "関連リンク",
           "cookie_settings": "Cookie設定", "terms": "利用規約", "updates": "更新情報",
           "menu": "メニューを開く", "dark": "ダークモードに切り替え", "light": "ライトモードに切り替え",
           "lang": "言語選択", "skip": "本文へスキップ",
           "tools_group": "ツール", "games_group": "ゲーム", "game_syntax": "コーディング文法クイズ",
           "breadcrumb_aria": "パンくずリスト"},
    "zh": {"home": "首页", "tool": "JSON 格式化", "tool_xml": "XML 格式化",
           "tool_converter": "JSON ↔ XML 转换工具", "tool_sql": "SQL 格式化", "tool_code": "代码查看器",
           "tool_number": "数字读法转换", "tool_typing": "打字速度测试", "about": "关于本站",
           "privacy": "隐私政策", "faq": "常见问题", "contact": "联系我们", "related_h2": "相关链接",
           "cookie_settings": "Cookie 设置", "terms": "使用条款", "updates": "更新日志",
           "menu": "打开菜单", "dark": "切换到深色模式", "light": "切换到浅色模式",
           "lang": "选择语言", "skip": "跳转到正文",
           "tools_group": "工具", "games_group": "游戏", "game_syntax": "编程语法测验",
           "breadcrumb_aria": "面包屑导航"},
    "es": {"home": "Inicio", "tool": "Formateador JSON", "tool_xml": "Formateador XML",
           "tool_converter": "Convertidor JSON ↔ XML", "tool_sql": "Formateador SQL", "tool_code": "Visor de código",
           "tool_number": "Lector de números", "tool_typing": "Prueba de velocidad de escritura", "about": "Acerca de",
           "privacy": "Política de privacidad", "faq": "Preguntas frecuentes", "contact": "Contacto", "related_h2": "Relacionado",
           "cookie_settings": "Preferencias de cookies", "terms": "Términos de servicio", "updates": "Novedades",
           "menu": "Abrir menú", "dark": "Cambiar a modo oscuro", "light": "Cambiar a modo claro",
           "lang": "Seleccionar idioma", "skip": "Saltar al contenido",
           "tools_group": "Herramientas", "games_group": "Juegos", "game_syntax": "Quiz de sintaxis de código",
           "breadcrumb_aria": "Ruta de navegación"},
    "vi": {"home": "Trang chủ", "tool": "Công cụ định dạng JSON", "tool_xml": "Công cụ định dạng XML",
           "tool_converter": "Chuyển đổi JSON ↔ XML", "tool_sql": "Công cụ định dạng SQL", "tool_code": "Xem mã nguồn",
           "tool_number": "Đọc số thành chữ", "tool_typing": "Kiểm tra tốc độ đánh máy", "about": "Giới thiệu",
           "privacy": "Chính sách bảo mật", "faq": "Câu hỏi thường gặp", "contact": "Liên hệ", "related_h2": "Liên quan",
           "cookie_settings": "Tùy chọn cookie", "terms": "Điều khoản dịch vụ", "updates": "Cập nhật mới",
           "menu": "Mở menu", "dark": "Chuyển sang chế độ tối", "light": "Chuyển sang chế độ sáng",
           "lang": "Chọn ngôn ngữ", "skip": "Chuyển đến nội dung",
           "tools_group": "Công cụ", "games_group": "Trò chơi", "game_syntax": "Đố vui cú pháp lập trình",
           "breadcrumb_aria": "Đường dẫn điều hướng"},
    "pt": {"home": "Início", "tool": "Formatador de JSON", "tool_xml": "Formatador de XML",
           "tool_converter": "Conversor JSON ↔ XML", "tool_sql": "Formatador de SQL", "tool_code": "Visualizador de código",
           "tool_number": "Leitor de números", "tool_typing": "Teste de velocidade de digitação", "about": "Sobre",
           "privacy": "Política de privacidade", "faq": "Perguntas frequentes", "contact": "Contato", "related_h2": "Relacionados",
           "cookie_settings": "Preferências de cookies", "terms": "Termos de serviço", "updates": "Novidades",
           "menu": "Abrir menu", "dark": "Mudar para modo escuro", "light": "Mudar para modo claro",
           "lang": "Selecionar idioma", "skip": "Ir para o conteúdo",
           "tools_group": "Ferramentas", "games_group": "Jogos", "game_syntax": "Quiz de sintaxe de código",
           "breadcrumb_aria": "Trilha de navegação"},
    "id": {"home": "Beranda", "tool": "Pemformat JSON", "tool_xml": "Pemformat XML",
           "tool_converter": "Konverter JSON ↔ XML", "tool_sql": "Pemformat SQL", "tool_code": "Penampil Kode",
           "tool_number": "Pembaca Angka", "tool_typing": "Tes Kecepatan Mengetik", "about": "Tentang",
           "privacy": "Kebijakan Privasi", "faq": "Pertanyaan Umum", "contact": "Kontak", "related_h2": "Terkait",
           "cookie_settings": "Preferensi cookie", "terms": "Ketentuan Layanan", "updates": "Pembaruan",
           "menu": "Buka menu", "dark": "Beralih ke mode gelap", "light": "Beralih ke mode terang",
           "lang": "Pilih bahasa", "skip": "Lompat ke konten",
           "tools_group": "Alat", "games_group": "Permainan", "game_syntax": "Kuis Sintaks Koding",
           "breadcrumb_aria": "Navigasi remah roti"},
    "de": {"home": "Start", "tool": "JSON-Formatierer", "tool_xml": "XML-Formatierer",
           "tool_converter": "JSON ↔ XML Konverter", "tool_sql": "SQL-Formatierer", "tool_code": "Code-Viewer",
           "tool_number": "Zahlen-Vorleser", "tool_typing": "Schreibgeschwindigkeitstest", "about": "Über uns",
           "privacy": "Datenschutzerklärung", "faq": "Häufige Fragen", "contact": "Kontakt", "related_h2": "Verwandt",
           "cookie_settings": "Cookie-Einstellungen", "terms": "Nutzungsbedingungen", "updates": "Neuigkeiten",
           "menu": "Menü öffnen", "dark": "Zum Dunkelmodus wechseln", "light": "Zum Hellmodus wechseln",
           "lang": "Sprache wählen", "skip": "Zum Inhalt springen",
           "tools_group": "Werkzeuge", "games_group": "Spiele", "game_syntax": "Coding-Syntax-Quiz",
           "breadcrumb_aria": "Breadcrumb-Navigation"},
}

# ---------------------------------------------------------------------------
# 페이지별 콘텐츠. {placeholder} 는 urls_for(lang) 값으로 치환됩니다.
# ---------------------------------------------------------------------------
CONTENT = {}

CONTENT["index"] = {
    "en": dict(
        title="Formix – Free Online JSON & XML Formatter, Validator & Developer Tools",
        description="Free online JSON formatter and XML formatter you can use right in your browser — no sign-up required. Validate, beautify, and view JSON/XML instantly. Your data is processed locally and never sent to a server.",
        keywords="json formatter, json validator, json viewer online, format json online, beautify json, xml formatter online, xml validator, free online developer tools",
        og_title="Formix – Free Online JSON & XML Formatter",
        og_description="Free online tools including a JSON Formatter, usable right in your browser. Your data is never stored on our servers.",
        eyebrow="FREE ONLINE TOOLS",
        h1="Browser-based online tools.<br />No install, no sign-up.",
        hero_p="Formix is a free collection of online utilities for the small, everyday tasks that come up during development and work. Everything you enter is processed only on your own computer (in your browser) and is never sent to a server.",
        features_h2="Available tools",
        features_p="Try the tool below right away — more tools are on the way.",
        card1_title="JSON Formatter / Viewer",
        card1_desc="Checks whether your input is valid JSON and displays it as a readable, syntax-highlighted tree. Includes collapsible nodes and key/value search.",
        card1_tag="JSON · Formatter · Validator",
        card2_title="XML Formatter / Viewer",
        card2_desc="Checks whether your input is valid XML and displays it as a readable, syntax-highlighted tree. Includes collapsible nodes and tag/attribute/text search.",
        card2_tag="XML · Formatter · Validator",
        card3_title="JSON ↔ XML Converter",
        card3_desc="Converts JSON to XML or XML to JSON, with automatic format detection. Includes line/column error hints and configurable indentation.",
        card3_tag="JSON · XML · Converter",
        card4_title="SQL Formatter / Beautifier",
        card4_desc="Beautifies SQL queries with proper indentation and keyword casing. Supports multiple dialects including MySQL, PostgreSQL, SQL Server, and BigQuery.",
        card4_tag="SQL · Formatter · Beautifier",
        card5_title="Code Viewer",
        card5_desc="Paste source code, pick a language (Java, C#, Python, Go, and 15+ more), and view it with syntax highlighting for easier reading and sharing.",
        card5_tag="Code · Syntax Highlighting · Viewer",
        card6_title="Number Reader",
        card6_desc="Converts numbers into words — cardinal, ordinal, phone/account digits, time, date, and currency, with multiple reading styles per language.",
        card6_tag="Numbers · Reader · Converter",
        card7_title="Typing Speed Test",
        card7_desc="Measure your typing speed (WPM) and accuracy with short practice passages, then share your score. All scoring happens locally in your browser.",
        card7_tag="Typing · WPM · Game",
        card8_title="Coding Syntax Quiz",
        card8_desc="A multiple-choice quiz covering basic syntax for JavaScript, Python, Java, and C. Pick a language and see how many you get right.",
        card8_tag="Quiz · Syntax · Game",
        games_h2="Games",
        games_p="Short, browser-only games for a quick break — no sign-up, no leaderboard pressure (except the one you choose to join).",
        why_h2="Why Formix?",
        why_items=[
            ("No install or sign-up", "Just open the link and start using it right away."),
            ("Processed in your browser", "Your input is handled entirely on the client side and is never sent to a server."),
            ("Dark mode support", "Switch between light and dark themes anytime using the toggle in the top right."),
            ("Continuously expanding", "We plan to keep adding tools that are useful for everyday development and work."),
        ],
    ),
    "ko": dict(
        title="JSON·XML 포맷터 무료 온라인 도구 - Formix",
        description="회원가입 없이 브라우저에서 바로 사용하는 무료 JSON·XML 포맷터. JSON/XML 문자열을 검증하고 보기 좋게 정리하세요. 데이터는 서버로 전송되지 않고 내 브라우저 안에서만 처리됩니다.",
        keywords="JSON 포맷터, JSON 뷰어, JSON 정리, JSON 검증, 온라인 JSON 도구, XML 포맷터, 무료 개발자 도구, JSON 예쁘게 만들기",
        og_title="JSON·XML 포맷터 무료 온라인 도구 - Formix",
        og_description="JSON 포매터를 비롯해 브라우저에서 바로 쓰는 무료 온라인 도구를 제공합니다. 데이터는 서버에 저장되지 않습니다.",
        eyebrow="FREE ONLINE TOOLS",
        h1="설치도, 가입도 필요 없는<br />브라우저 기반 온라인 도구 모음",
        hero_p="Formix는 개발과 업무 중 자주 필요한 자잔한 작업들을 브라우저에서 바로 끝낼 수 있게 만든 무료 온라인 유틸리티 모음입니다. 입력한 데이터는 서버로 전송되지 않고 내 컴퓨터(브라우저) 안에서만 처리되어 안전하게 사용할 수 있습니다.",
        features_h2="제공 기능",
        features_p="아래 기능을 바로 사용해보세요. 새로운 도구는 계속 추가될 예정입니다.",
        card1_title="JSON 포매터 / 뷰어",
        card1_desc="입력한 문자열이 올바른 JSON인지 검사하고, 들여쓰기와 문법 강조를 적용해 가독성 좋게 보여줍니다. 트리 접기/펼치기와 키·값 검색 기능을 제공합니다.",
        card1_tag="JSON · Formatter · Validator",
        card2_title="XML 포매터 / 뷰어",
        card2_desc="입력한 문자열이 올바른 XML인지 검사하고, 들여쓰기와 문법 강조를 적용해 가독성 좋게 보여줍니다. 트리 접기/펼치기와 태그·속성·텍스트 검색 기능을 제공합니다.",
        card2_tag="XML · Formatter · Validator",
        card3_title="JSON ↔ XML 변환기",
        card3_desc="JSON을 XML로, XML을 JSON으로 변환합니다. 형식을 자동으로 감지하며, 오류 줄/열 안내와 들여쓰기 설정을 지원합니다.",
        card3_tag="JSON · XML · Converter",
        card4_title="SQL 포매터 / 정렬기",
        card4_desc="SQL 쿼리를 알아보기 쉽게 들여쓰기하고 키워드 대소문자를 정리합니다. MySQL, PostgreSQL, SQL Server, BigQuery 등 여러 방언을 지원합니다.",
        card4_tag="SQL · Formatter · Beautifier",
        card5_title="코드 뷰어",
        card5_desc="소스 코드를 붙여넣고 언어(Java, C#, Python, Go 등 20여 개)를 선택하면 문법 강조가 적용된 화면으로 보기 좋게 표시합니다.",
        card5_tag="Code · Syntax Highlighting · Viewer",
        card6_title="숫자 읽기 변환기",
        card6_desc="숫자를 문자로 변환합니다. 일반(기수), 서수, 전화·계좌번호, 시간, 날짜, 화폐 모드를 지원하며 언어별로 여러 표기 방식(예: 한자어/고유어/갖은자)을 제공합니다.",
        card6_tag="숫자 · 읽기 · 변환기",
        card7_title="타자 속도 테스트",
        card7_desc="짧은 연습 문장으로 타자 속도(WPM)와 정확도를 측정하고 결과를 공유할 수 있습니다. 모든 채점은 브라우저 안에서만 이뤄집니다.",
        card7_tag="타자연습 · WPM · 게임",
        card8_title="코딩 문법 퀴즈",
        card8_desc="JavaScript, Python, Java, C의 기본 문법을 묻는 객관식 퀴즈입니다. 언어를 선택하고 몇 문제나 맞추는지 확인해보세요.",
        card8_tag="퀴즈 · 문법 · 게임",
        games_h2="게임",
        games_p="가볍게 즐기는 브라우저 게임들입니다 — 회원가입도, 부담스러운 랭킹도 없습니다(직접 참여를 선택한 경우는 예외입니다).",
        why_h2="왜 Formix인가요?",
        why_items=[
            ("설치·가입 불필요", "링크만 열면 바로 사용할 수 있습니다."),
            ("브라우저 내 처리", "입력한 데이터를 서버로 전송하지 않고 클라이언트에서만 처리합니다."),
            ("다크 모드 지원", "화면 우측 상단 토글로 언제든 라이트/다크 테마를 전환할 수 있습니다."),
            ("지속적인 기능 추가", "자주 쓰는 개발/업무 도구를 계속 확장해 나갈 예정입니다."),
        ],
    ),
    "ja": dict(
        title="JSON・XML 整形（フォーマッター）無料オンラインツール - Formix",
        description="会員登録不要でブラウザ上ですぐ使える無料の JSON・XML フォーマッター。JSON/XML 文字列を検証し、読みやすく整形して表示します。データはサーバーに送信されず、ブラウザ内でのみ処理されます。",
        keywords="JSON 整形, JSONフォーマッター, JSONビューア, JSON 検証, XML 整形, オンライン JSON ツール, 無料 開発者ツール",
        og_title="JSON・XML 整形（フォーマッター）無料オンラインツール - Formix",
        og_description="JSONフォーマッターをはじめ、ブラウザですぐ使える無料オンラインツールを提供します。データはサーバーに保存されません。",
        eyebrow="FREE ONLINE TOOLS",
        h1="インストールも登録も不要な<br />ブラウザ完結型オンラインツール集",
        hero_p="Formixは、開発や業務中によく必要になる細かな作業をブラウザ上ですぐに済ませられるようにした無料のオンラインユーティリティ集です。入力したデータはサーバーに送信されず、お使いのコンピューター（ブラウザ）内でのみ処理されるため、安心してご利用いただけます。",
        features_h2="提供機能",
        features_p="下記の機能をすぐにお試しください。新しいツールも順次追加していく予定です。",
        card1_title="JSONフォーマッター / ビューア",
        card1_desc="入力した文字列が正しいJSONかどうかを検証し、インデントとシンタックスハイライトを適用して読みやすく表示します。ツリーの折りたたみ/展開とキー・値の検索機能を提供します。",
        card1_tag="JSON · Formatter · Validator",
        card2_title="XMLフォーマッター / ビューア",
        card2_desc="入力した文字列が正しいXMLかどうかを検証し、インデントとシンタックスハイライトを適用して読みやすく表示します。ツリーの折りたたみ/展開とタグ・属性・テキストの検索機能を提供します。",
        card2_tag="XML · Formatter · Validator",
        card3_title="JSON ↔ XML 変換ツール",
        card3_desc="JSONをXMLに、XMLをJSONに変換します。形式を自動検出し、エラーの行/列表示とインデント設定に対応しています。",
        card3_tag="JSON · XML · Converter",
        card4_title="SQLフォーマッター / 整形ツール",
        card4_desc="SQLクエリを見やすくインデント・整形します。MySQL、PostgreSQL、SQL Server、BigQueryなど複数の方言に対応しています。",
        card4_tag="SQL · Formatter · Beautifier",
        card5_title="コードビューア",
        card5_desc="ソースコードを貼り付けて言語(Java、C#、Python、Goなど20以上)を選択すると、シンタックスハイライト付きで見やすく表示します。",
        card5_tag="Code · Syntax Highlighting · Viewer",
        card6_title="数字の読み方変換",
        card6_desc="数字を文字に変換します。基数・序数・電話/口座番号・時刻・日付・通貨に対応し、言語ごとに複数の表記方式(標準/大字など)を提供します。",
        card6_tag="数字 · 読み方 · 変換",
        card7_title="タイピング速度テスト",
        card7_desc="短い練習文でタイピング速度(WPM)と正確率を測定し、結果をシェアできます。採点はすべてブラウザ内で行われます。",
        card7_tag="タイピング · WPM · ゲーム",
        card8_title="コーディング文法クイズ",
        card8_desc="JavaScript、Python、Java、Cの基本文法を問う選択式クイズです。言語を選んで何問正解できるか試してみましょう。",
        card8_tag="クイズ · 文法 · ゲーム",
        games_h2="ゲーム",
        games_p="ちょっとした息抜きに楽しめる、ブラウザだけで完結するゲームです — 登録不要、ランキングへの参加も任意です。",
        why_h2="なぜFormixなのか?",
        why_items=[
            ("インストール・登録不要", "リンクを開くだけですぐに利用できます。"),
            ("ブラウザ内処理", "入力したデータをサーバーに送信せず、クライアント側だけで処理します。"),
            ("ダークモード対応", "画面右上のトグルでライト/ダークテーマをいつでも切り替えられます。"),
            ("継続的な機能追加", "よく使う開発・業務ツールを今後も追加していく予定です。"),
        ],
    ),
    "zh": dict(
        title="JSON/XML 在线格式化工具（免费） - Formix",
        description="无需注册，直接在浏览器中使用的免费 JSON/XML 格式化工具。验证并以易读方式展示 JSON/XML 字符串。数据不会发送到服务器，仅在您的浏览器中处理。",
        keywords="JSON 格式化, JSON 在线格式化, JSON 校验, JSON 查看器, XML 格式化, 在线开发者工具, 免费在线工具",
        og_title="JSON/XML 在线格式化工具（免费） - Formix",
        og_description="提供 JSON 格式化等可在浏览器中直接使用的免费在线工具，数据不会保存在服务器上。",
        eyebrow="FREE ONLINE TOOLS",
        h1="无需安装、无需注册的<br />浏览器端在线工具集",
        hero_p="Formix是一套免费的在线实用工具集合，帮助你在开发和工作中快速完成各种琐碎任务。你输入的数据不会发送到服务器，只会在你自己的电脑（浏览器）中处理，可以放心使用。",
        features_h2="提供的功能",
        features_p="立即体验下面的功能，我们会持续添加新的工具。",
        card1_title="JSON 格式化 / 查看器",
        card1_desc="检查输入的字符串是否为有效的 JSON，并以带缩进和语法高亮的树形结构清晰展示。支持节点折叠/展开以及键值搜索功能。",
        card1_tag="JSON · Formatter · Validator",
        card2_title="XML 格式化 / 查看器",
        card2_desc="检查输入的字符串是否为有效的 XML，并以带缩进和语法高亮的树形结构清晰展示。支持节点折叠/展开以及标签·属性·文本搜索功能。",
        card2_tag="XML · Formatter · Validator",
        card3_title="JSON ↔ XML 转换工具",
        card3_desc="将 JSON 转换为 XML，或将 XML 转换为 JSON，支持自动检测格式、错误行/列提示以及自定义缩进。",
        card3_tag="JSON · XML · Converter",
        card4_title="SQL 格式化 / 美化工具",
        card4_desc="为 SQL 查询语句添加清晰的缩进和关键字大小写格式化。支持 MySQL、PostgreSQL、SQL Server、BigQuery 等多种方言。",
        card4_tag="SQL · Formatter · Beautifier",
        card5_title="代码查看器",
        card5_desc="粘贴源代码并选择语言(Java、C#、Python、Go 等 20 多种)，即可获得带语法高亮的易读展示。",
        card5_tag="Code · Syntax Highlighting · Viewer",
        card6_title="数字读法转换",
        card6_desc="将数字转换为文字。支持基数、序数、电话/账号、时间、日期、货币模式，并为每种语言提供多种读法(如小写/大写)。",
        card6_tag="数字 · 读法 · 转换",
        card7_title="打字速度测试",
        card7_desc="通过简短的练习句子测量打字速度(WPM)和准确率，并可分享成绩。所有计分均在浏览器本地完成。",
        card7_tag="打字 · WPM · 游戏",
        card8_title="编程语法测验",
        card8_desc="一个关于 JavaScript、Python、Java 和 C 基础语法的选择题测验。选择一种语言，看看你能答对多少题。",
        card8_tag="测验 · 语法 · 游戏",
        games_h2="游戏",
        games_p="轻松一下的纯浏览器小游戏 — 无需注册，排行榜也完全自愿参加。",
        why_h2="为什么选择Formix?",
        why_items=[
            ("无需安装、无需注册", "打开链接即可立即使用。"),
            ("浏览器端处理", "输入的数据完全在客户端处理，不会发送到服务器。"),
            ("支持深色模式", "随时通过右上角的按钮切换浅色/深色主题。"),
            ("持续更新功能", "我们会持续添加在开发和工作中常用的实用工具。"),
        ],
    ),
    "es": dict(
        title="Formix – Formateador JSON y XML gratuito en línea, validador y herramientas para desarrolladores",
        description="Formateador JSON y XML gratuito que puedes usar directamente en tu navegador, sin registro. Valida, embellece y visualiza JSON/XML al instante. Tus datos se procesan localmente y nunca se envían a un servidor.",
        keywords="formateador json, validador json, visor json en línea, formatear json online, embellecer json, formateador xml online, validador xml, herramientas gratuitas para desarrolladores",
        og_title="Formix – Formateador JSON y XML gratuito en línea",
        og_description="Herramientas gratuitas en línea, incluido un formateador JSON, que puedes usar directamente en tu navegador. Tus datos nunca se almacenan en nuestros servidores.",
        eyebrow="HERRAMIENTAS GRATUITAS EN LÍNEA",
        h1="Herramientas en línea basadas en el navegador.<br />Sin instalación, sin registro.",
        hero_p="Formix es una colección gratuita de utilidades en línea para las tareas pequeñas pero frecuentes del desarrollo y el trabajo diario. Todo lo que ingresas se procesa solo en tu propio equipo (en tu navegador) y nunca se envía a un servidor.",
        features_h2="Herramientas disponibles",
        features_p="Prueba la herramienta a continuación ahora mismo — vienen más en camino.",
        card1_title="Formateador / Visor JSON",
        card1_desc="Verifica si tu entrada es JSON válido y lo muestra como un árbol legible con resaltado de sintaxis. Incluye nodos colapsables y búsqueda de claves/valores.",
        card1_tag="JSON · Formateador · Validador",
        card2_title="Formateador / Visor XML",
        card2_desc="Verifica si tu entrada es XML válido y lo muestra como un árbol legible con resaltado de sintaxis. Incluye nodos colapsables y búsqueda de etiquetas/atributos/texto.",
        card2_tag="XML · Formateador · Validador",
        card3_title="Convertidor JSON ↔ XML",
        card3_desc="Convierte JSON a XML o XML a JSON, con detección automática de formato. Incluye indicaciones de error por línea/columna y sangría configurable.",
        card3_tag="JSON · XML · Convertidor",
        card4_title="Formateador / Embellecedor SQL",
        card4_desc="Embellece consultas SQL con sangría adecuada y formato de palabras clave. Compatible con varios dialectos, incluidos MySQL, PostgreSQL, SQL Server y BigQuery.",
        card4_tag="SQL · Formateador · Embellecedor",
        card5_title="Visor de código",
        card5_desc="Pega código fuente, elige un lenguaje (Java, C#, Python, Go y más de 15 adicionales) y míralo con resaltado de sintaxis para facilitar la lectura y el compartir.",
        card5_tag="Código · Resaltado de sintaxis · Visor",
        card6_title="Lector de números",
        card6_desc="Convierte números en palabras — cardinales, ordinales, dígitos de teléfono/cuenta, hora, fecha y moneda, con varios estilos de lectura por idioma.",
        card6_tag="Números · Lector · Convertidor",
        card7_title="Prueba de velocidad de escritura",
        card7_desc="Mide tu velocidad de escritura (PPM) y precisión con pasajes cortos de práctica, y comparte tu puntuación. Todo el cálculo se hace localmente en tu navegador.",
        card7_tag="Escritura · PPM · Juego",
        card8_title="Quiz de sintaxis de código",
        card8_desc="Un quiz de opción múltiple sobre la sintaxis básica de JavaScript, Python, Java y C. Elige un lenguaje y descubre cuántas aciertas.",
        card8_tag="Quiz · Sintaxis · Juego",
        games_h2="Juegos",
        games_p="Juegos cortos, solo en el navegador, para un descanso rápido — sin registro, sin presión de tabla de clasificación (salvo la que decidas aceptar).",
        why_h2="¿Por qué Formix?",
        why_items=[
            ("Sin instalación ni registro", "Solo abre el enlace y empieza a usarlo de inmediato."),
            ("Procesado en tu navegador", "Tu entrada se maneja completamente del lado del cliente y nunca se envía a un servidor."),
            ("Soporte para modo oscuro", "Cambia entre temas claro y oscuro en cualquier momento con el botón de la parte superior derecha."),
            ("Expansión continua", "Planeamos seguir añadiendo herramientas útiles para el desarrollo y el trabajo diario."),
        ],
    ),
    "vi": dict(
        title="Formix – Công cụ định dạng JSON & XML trực tuyến miễn phí, công cụ kiểm tra và tiện ích cho lập trình viên",
        description="Công cụ định dạng JSON và XML trực tuyến miễn phí, dùng ngay trên trình duyệt — không cần đăng ký. Kiểm tra, làm đẹp và xem JSON/XML ngay lập tức. Dữ liệu của bạn được xử lý cục bộ và không bao giờ gửi lên máy chủ.",
        keywords="định dạng json, kiểm tra json, xem json trực tuyến, định dạng json online, làm đẹp json, định dạng xml online, kiểm tra xml, công cụ lập trình miễn phí",
        og_title="Formix – Công cụ định dạng JSON & XML trực tuyến miễn phí",
        og_description="Các công cụ trực tuyến miễn phí, bao gồm công cụ định dạng JSON, dùng ngay trên trình duyệt. Dữ liệu của bạn không bao giờ được lưu trên máy chủ của chúng tôi.",
        eyebrow="CÔNG CỤ TRỰC TUYẾN MIỄN PHÍ",
        h1="Công cụ trực tuyến chạy trên trình duyệt.<br />Không cần cài đặt, không cần đăng ký.",
        hero_p="Formix là bộ tiện ích trực tuyến miễn phí cho những tác vụ nhỏ nhưng thường gặp trong lúc phát triển và làm việc. Mọi thứ bạn nhập vào chỉ được xử lý trên máy của bạn (trong trình duyệt) và không bao giờ được gửi lên máy chủ.",
        features_h2="Công cụ hiện có",
        features_p="Hãy thử ngay công cụ bên dưới — nhiều công cụ khác sắp ra mắt.",
        card1_title="Định dạng / Xem JSON",
        card1_desc="Kiểm tra xem nội dung bạn nhập có phải JSON hợp lệ không và hiển thị dưới dạng cây dễ đọc, có tô màu cú pháp. Hỗ trợ thu/mở rộng nút và tìm kiếm khóa/giá trị.",
        card1_tag="JSON · Định dạng · Kiểm tra",
        card2_title="Định dạng / Xem XML",
        card2_desc="Kiểm tra xem nội dung bạn nhập có phải XML hợp lệ không và hiển thị dưới dạng cây dễ đọc, có tô màu cú pháp. Hỗ trợ thu/mở rộng nút và tìm kiếm thẻ/thuộc tính/văn bản.",
        card2_tag="XML · Định dạng · Kiểm tra",
        card3_title="Chuyển đổi JSON ↔ XML",
        card3_desc="Chuyển JSON sang XML hoặc XML sang JSON, tự động nhận diện định dạng. Có gợi ý lỗi theo dòng/cột và tùy chỉnh thụt lề.",
        card3_tag="JSON · XML · Chuyển đổi",
        card4_title="Định dạng / Làm đẹp SQL",
        card4_desc="Làm đẹp câu lệnh SQL với thụt lề hợp lý và viết hoa từ khóa đúng chuẩn. Hỗ trợ nhiều phương ngữ như MySQL, PostgreSQL, SQL Server và BigQuery.",
        card4_tag="SQL · Định dạng · Làm đẹp",
        card5_title="Xem mã nguồn",
        card5_desc="Dán mã nguồn, chọn ngôn ngữ (Java, C#, Python, Go và hơn 15 ngôn ngữ khác) và xem với tô màu cú pháp để dễ đọc và chia sẻ hơn.",
        card5_tag="Mã nguồn · Tô màu cú pháp · Xem",
        card6_title="Đọc số thành chữ",
        card6_desc="Chuyển số thành chữ — số đếm, số thứ tự, số điện thoại/tài khoản, thời gian, ngày tháng và tiền tệ, với nhiều kiểu đọc theo từng ngôn ngữ.",
        card6_tag="Số · Đọc · Chuyển đổi",
        card7_title="Kiểm tra tốc độ đánh máy",
        card7_desc="Đo tốc độ đánh máy (WPM) và độ chính xác qua các đoạn luyện tập ngắn, rồi chia sẻ điểm số của bạn. Mọi phép tính diễn ra ngay trên trình duyệt.",
        card7_tag="Đánh máy · WPM · Trò chơi",
        card8_title="Đố vui cú pháp lập trình",
        card8_desc="Một bài trắc nghiệm về cú pháp cơ bản của JavaScript, Python, Java và C. Chọn một ngôn ngữ và xem bạn trả lời đúng được bao nhiêu câu.",
        card8_tag="Đố vui · Cú pháp · Trò chơi",
        games_h2="Trò chơi",
        games_p="Những trò chơi ngắn, chỉ chạy trên trình duyệt, để giải lao nhanh — không cần đăng ký, không áp lực bảng xếp hạng (trừ khi bạn chọn tham gia).",
        why_h2="Vì sao chọn Formix?",
        why_items=[
            ("Không cần cài đặt hay đăng ký", "Chỉ cần mở liên kết và sử dụng ngay."),
            ("Xử lý ngay trên trình duyệt", "Dữ liệu bạn nhập được xử lý hoàn toàn ở phía trình duyệt và không bao giờ gửi lên máy chủ."),
            ("Hỗ trợ chế độ tối", "Chuyển đổi giữa giao diện sáng và tối bất cứ lúc nào bằng nút ở góc trên phải."),
            ("Liên tục mở rộng", "Chúng tôi sẽ tiếp tục bổ sung các công cụ hữu ích cho công việc và phát triển hằng ngày."),
        ],
    ),
    "pt": dict(
        title="Formix – Formatador JSON e XML online gratuito, validador e ferramentas para desenvolvedores",
        description="Formatador JSON e XML online gratuito que você pode usar diretamente no navegador — sem necessidade de cadastro. Valide, formate e visualize JSON/XML instantaneamente. Seus dados são processados localmente e nunca enviados a um servidor.",
        keywords="formatador json, validador json, visualizador json online, formatar json online, embelezar json, formatador xml online, validador xml, ferramentas gratuitas para desenvolvedores",
        og_title="Formix – Formatador JSON e XML online gratuito",
        og_description="Ferramentas online gratuitas, incluindo um formatador JSON, utilizáveis diretamente no navegador. Seus dados nunca são armazenados em nossos servidores.",
        eyebrow="FERRAMENTAS ONLINE GRATUITAS",
        h1="Ferramentas online baseadas no navegador.<br />Sem instalação, sem cadastro.",
        hero_p="O Formix é uma coleção gratuita de utilitários online para as pequenas tarefas do dia a dia no desenvolvimento e no trabalho. Tudo o que você digita é processado apenas no seu próprio computador (no navegador) e nunca é enviado a um servidor.",
        features_h2="Ferramentas disponíveis",
        features_p="Experimente a ferramenta abaixo agora mesmo — mais ferramentas estão a caminho.",
        card1_title="Formatador / Visualizador JSON",
        card1_desc="Verifica se sua entrada é um JSON válido e a exibe como uma árvore legível com destaque de sintaxe. Inclui nós recolhíveis e busca de chave/valor.",
        card1_tag="JSON · Formatador · Validador",
        card2_title="Formatador / Visualizador XML",
        card2_desc="Verifica se sua entrada é um XML válido e a exibe como uma árvore legível com destaque de sintaxe. Inclui nós recolhíveis e busca de tag/atributo/texto.",
        card2_tag="XML · Formatador · Validador",
        card3_title="Conversor JSON ↔ XML",
        card3_desc="Converte JSON para XML ou XML para JSON, com detecção automática de formato. Inclui dicas de erro por linha/coluna e recuo configurável.",
        card3_tag="JSON · XML · Conversor",
        card4_title="Formatador / Embelezador SQL",
        card4_desc="Embeleza consultas SQL com recuo adequado e formatação de palavras-chave. Compatível com vários dialetos, incluindo MySQL, PostgreSQL, SQL Server e BigQuery.",
        card4_tag="SQL · Formatador · Embelezador",
        card5_title="Visualizador de código",
        card5_desc="Cole o código-fonte, escolha uma linguagem (Java, C#, Python, Go e mais de 15 outras) e veja com destaque de sintaxe para facilitar a leitura e o compartilhamento.",
        card5_tag="Código · Destaque de sintaxe · Visualizador",
        card6_title="Leitor de números",
        card6_desc="Converte números em palavras — cardinais, ordinais, dígitos de telefone/conta, hora, data e moeda, com vários estilos de leitura por idioma.",
        card6_tag="Números · Leitor · Conversor",
        card7_title="Teste de velocidade de digitação",
        card7_desc="Meça sua velocidade de digitação (PPM) e precisão com trechos curtos de prática, depois compartilhe sua pontuação. Toda a pontuação é calculada localmente no seu navegador.",
        card7_tag="Digitação · PPM · Jogo",
        card8_title="Quiz de sintaxe de código",
        card8_desc="Um quiz de múltipla escolha sobre a sintaxe básica de JavaScript, Python, Java e C. Escolha uma linguagem e veja quantas você acerta.",
        card8_tag="Quiz · Sintaxe · Jogo",
        games_h2="Jogos",
        games_p="Jogos curtos, só no navegador, para uma pausa rápida — sem cadastro, sem pressão de ranking (exceto o que você escolher participar).",
        why_h2="Por que o Formix?",
        why_items=[
            ("Sem instalação nem cadastro", "Basta abrir o link e começar a usar imediatamente."),
            ("Processado no seu navegador", "Sua entrada é tratada inteiramente no lado do cliente e nunca é enviada a um servidor."),
            ("Suporte a modo escuro", "Alterne entre os temas claro e escuro a qualquer momento pelo botão no canto superior direito."),
            ("Expansão contínua", "Planejamos continuar adicionando ferramentas úteis para o trabalho e o desenvolvimento do dia a dia."),
        ],
    ),
    "id": dict(
        title="Formix – Pemformat JSON & XML Online Gratis, Validator, dan Alat Pengembang",
        description="Pemformat JSON dan XML online gratis yang dapat Anda gunakan langsung di browser — tanpa perlu mendaftar. Validasi, perindah, dan lihat JSON/XML secara instan. Data Anda diproses secara lokal dan tidak pernah dikirim ke server.",
        keywords="pemformat json, validator json, penampil json online, format json online, perindah json, pemformat xml online, validator xml, alat pengembang gratis",
        og_title="Formix – Pemformat JSON & XML Online Gratis",
        og_description="Alat online gratis, termasuk pemformat JSON, yang dapat digunakan langsung di browser Anda. Data Anda tidak pernah disimpan di server kami.",
        eyebrow="ALAT ONLINE GRATIS",
        h1="Alat online berbasis browser.<br />Tanpa instalasi, tanpa pendaftaran.",
        hero_p="Formix adalah kumpulan utilitas online gratis untuk tugas-tugas kecil namun sering muncul selama pengembangan dan pekerjaan sehari-hari. Semua yang Anda masukkan hanya diproses di komputer Anda sendiri (di browser) dan tidak pernah dikirim ke server.",
        features_h2="Alat yang tersedia",
        features_p="Coba alat di bawah ini sekarang — lebih banyak alat akan segera hadir.",
        card1_title="Pemformat / Penampil JSON",
        card1_desc="Memeriksa apakah input Anda adalah JSON yang valid dan menampilkannya sebagai pohon yang mudah dibaca dengan penyorotan sintaks. Dilengkapi node yang dapat dilipat dan pencarian kunci/nilai.",
        card1_tag="JSON · Pemformat · Validator",
        card2_title="Pemformat / Penampil XML",
        card2_desc="Memeriksa apakah input Anda adalah XML yang valid dan menampilkannya sebagai pohon yang mudah dibaca dengan penyorotan sintaks. Dilengkapi node yang dapat dilipat dan pencarian tag/atribut/teks.",
        card2_tag="XML · Pemformat · Validator",
        card3_title="Konverter JSON ↔ XML",
        card3_desc="Mengonversi JSON ke XML atau XML ke JSON, dengan deteksi format otomatis. Dilengkapi petunjuk error baris/kolom dan indentasi yang dapat disesuaikan.",
        card3_tag="JSON · XML · Konverter",
        card4_title="Pemformat / Perapi SQL",
        card4_desc="Merapikan kueri SQL dengan indentasi yang tepat dan penulisan kata kunci. Mendukung berbagai dialek termasuk MySQL, PostgreSQL, SQL Server, dan BigQuery.",
        card4_tag="SQL · Pemformat · Perapi",
        card5_title="Penampil Kode",
        card5_desc="Tempel kode sumber, pilih bahasa (Java, C#, Python, Go, dan 15+ lainnya), lalu lihat dengan penyorotan sintaks agar lebih mudah dibaca dan dibagikan.",
        card5_tag="Kode · Penyorotan Sintaks · Penampil",
        card6_title="Pembaca Angka",
        card6_desc="Mengonversi angka menjadi kata — kardinal, ordinal, digit telepon/rekening, waktu, tanggal, dan mata uang, dengan beberapa gaya pembacaan per bahasa.",
        card6_tag="Angka · Pembaca · Konverter",
        card7_title="Tes Kecepatan Mengetik",
        card7_desc="Ukur kecepatan mengetik (WPM) dan akurasi Anda dengan paragraf latihan singkat, lalu bagikan skor Anda. Semua penilaian dilakukan secara lokal di browser Anda.",
        card7_tag="Mengetik · WPM · Permainan",
        card8_title="Kuis Sintaks Koding",
        card8_desc="Kuis pilihan ganda tentang sintaks dasar JavaScript, Python, Java, dan C. Pilih satu bahasa dan lihat berapa banyak yang bisa Anda jawab dengan benar.",
        card8_tag="Kuis · Sintaks · Permainan",
        games_h2="Permainan",
        games_p="Permainan singkat berbasis browser untuk istirahat sejenak — tanpa pendaftaran, tanpa tekanan papan peringkat (kecuali yang Anda pilih sendiri untuk ikuti).",
        why_h2="Mengapa Formix?",
        why_items=[
            ("Tanpa instalasi atau pendaftaran", "Cukup buka tautannya dan langsung gunakan."),
            ("Diproses di browser Anda", "Input Anda ditangani sepenuhnya di sisi klien dan tidak pernah dikirim ke server."),
            ("Mendukung mode gelap", "Beralih antara tema terang dan gelap kapan saja menggunakan tombol di kanan atas."),
            ("Terus berkembang", "Kami berencana terus menambahkan alat yang bermanfaat untuk pengembangan dan pekerjaan sehari-hari."),
        ],
    ),
    "de": dict(
        title="Formix – Kostenloser Online JSON- & XML-Formatierer, Validator und Entwicklertools",
        description="Kostenloser Online-JSON- und XML-Formatierer, direkt im Browser nutzbar — keine Registrierung nötig. JSON/XML sofort validieren, formatieren und anzeigen. Ihre Daten werden lokal verarbeitet und nie an einen Server gesendet.",
        keywords="json formatierer, json validator, json viewer online, json online formatieren, json beautify, xml formatierer online, xml validator, kostenlose entwicklertools",
        og_title="Formix – Kostenloser Online JSON- & XML-Formatierer",
        og_description="Kostenlose Online-Tools, darunter ein JSON-Formatierer, direkt im Browser nutzbar. Ihre Daten werden nie auf unseren Servern gespeichert.",
        eyebrow="KOSTENLOSE ONLINE-TOOLS",
        h1="Browserbasierte Online-Tools.<br />Keine Installation, keine Registrierung.",
        hero_p="Formix ist eine kostenlose Sammlung von Online-Dienstprogrammen für die kleinen, alltäglichen Aufgaben in Entwicklung und Arbeit. Alles, was Sie eingeben, wird nur auf Ihrem eigenen Computer (im Browser) verarbeitet und nie an einen Server gesendet.",
        features_h2="Verfügbare Tools",
        features_p="Probieren Sie das Tool unten direkt aus — weitere Tools sind in Arbeit.",
        card1_title="JSON-Formatierer / Viewer",
        card1_desc="Prüft, ob Ihre Eingabe gültiges JSON ist, und zeigt es als lesbaren, syntaxhervorgehobenen Baum an. Mit einklappbaren Knoten und Schlüssel-/Wert-Suche.",
        card1_tag="JSON · Formatierer · Validator",
        card2_title="XML-Formatierer / Viewer",
        card2_desc="Prüft, ob Ihre Eingabe gültiges XML ist, und zeigt es als lesbaren, syntaxhervorgehobenen Baum an. Mit einklappbaren Knoten und Tag-/Attribut-/Text-Suche.",
        card2_tag="XML · Formatierer · Validator",
        card3_title="JSON ↔ XML Konverter",
        card3_desc="Konvertiert JSON in XML oder XML in JSON, mit automatischer Formaterkennung. Mit Fehlerhinweisen zu Zeile/Spalte und konfigurierbarer Einrückung.",
        card3_tag="JSON · XML · Konverter",
        card4_title="SQL-Formatierer / Beautifier",
        card4_desc="Formatiert SQL-Abfragen mit korrekter Einrückung und Schlüsselwort-Schreibweise. Unterstützt mehrere Dialekte, darunter MySQL, PostgreSQL, SQL Server und BigQuery.",
        card4_tag="SQL · Formatierer · Beautifier",
        card5_title="Code-Viewer",
        card5_desc="Quellcode einfügen, eine Sprache wählen (Java, C#, Python, Go und 15+ weitere) und mit Syntaxhervorhebung zum leichteren Lesen und Teilen anzeigen.",
        card5_tag="Code · Syntaxhervorhebung · Viewer",
        card6_title="Zahlen-Vorleser",
        card6_desc="Wandelt Zahlen in Wörter um — Grund- und Ordnungszahlen, Telefon-/Kontoziffern, Uhrzeit, Datum und Währung, mit mehreren Lesestilen je Sprache.",
        card6_tag="Zahlen · Vorleser · Konverter",
        card7_title="Schreibgeschwindigkeitstest",
        card7_desc="Messen Sie Ihre Schreibgeschwindigkeit (WPM) und Genauigkeit mit kurzen Übungstexten und teilen Sie Ihr Ergebnis. Die gesamte Auswertung erfolgt lokal in Ihrem Browser.",
        card7_tag="Tippen · WPM · Spiel",
        card8_title="Coding-Syntax-Quiz",
        card8_desc="Ein Multiple-Choice-Quiz zur Grundsyntax von JavaScript, Python, Java und C. Wählen Sie eine Sprache und sehen Sie, wie viele Sie richtig beantworten.",
        card8_tag="Quiz · Syntax · Spiel",
        games_h2="Spiele",
        games_p="Kurze, reine Browser-Spiele für eine schnelle Pause — keine Registrierung, kein Ranglisten-Druck (außer dem, dem Sie selbst beitreten möchten).",
        why_h2="Warum Formix?",
        why_items=[
            ("Keine Installation oder Registrierung", "Einfach den Link öffnen und sofort losnutzen."),
            ("Im Browser verarbeitet", "Ihre Eingabe wird vollständig clientseitig verarbeitet und nie an einen Server gesendet."),
            ("Dunkelmodus-Unterstützung", "Jederzeit mit dem Schalter oben rechts zwischen Hell- und Dunkelmodus wechseln."),
            ("Stetig wachsend", "Wir planen, weiterhin nützliche Tools für Entwicklung und Alltag hinzuzufügen."),
        ],
    ),
}

CONTENT["about"] = {
    "en": dict(
        title="About | Formix",
        description="Formix is a free collection of online developer tools you can use right in your browser, no sign-up required. Learn about the service, its principles, and available features.",
        og_title="About | Formix",
        og_description="An introduction to Formix and the principles behind it.",
        h1="About", lead="An introduction to what Formix is and the principles it's run by.",
        s1_h2="What is Formix?",
        s1_p='Formix is a free collection of online utilities that lets you handle small but tedious tasks you often run into during development or work, directly in your web browser — no separate program to install, no sign-up required. The first tool we offer is the <a href="{tool}">JSON Formatter</a>, and we plan to keep adding tools that are genuinely useful in everyday work.',
        s2_h2="Our principles",
        s2_items=[
            ("Use it instantly, no sign-up", "Anyone can start using it immediately — no account or login required."),
            ("Client-side processing", 'Most tools process your input entirely in the browser (JavaScript) and never send it to a server. See our <a href="{privacy}">Privacy Policy</a> for details.'),
            ("Light and fast", "We aim for a simple screen that cuts unnecessary elements and focuses on the features you actually need."),
            ("Dark mode built in", "Choose between light and dark themes, either automatically from your system settings or manually with the toggle."),
        ],
        s3_h2="Available features",
        s3_item='<a href="{tool}">JSON Formatter / Viewer</a> — Validates JSON strings and displays them as an indented, syntax-highlighted tree. Supports collapsing/expanding nodes and searching keys and values.',
        s3_item2='<a href="{tool_xml}">XML Formatter / Viewer</a> — Validates XML strings and displays them as an indented, syntax-highlighted tree. Supports collapsing/expanding nodes and searching tags, attributes, and text.',
        s3_item3='<a href="{tool_converter}">JSON ↔ XML Converter</a> — Converts JSON to XML or XML to JSON, with automatic format detection and configurable indentation.',
        s3_item4='<a href="{tool_sql}">SQL Formatter</a> — Beautifies SQL queries with proper indentation and keyword casing, supporting multiple dialects (MySQL, PostgreSQL, SQL Server, BigQuery, and more).',
        s3_item5='<a href="{tool_code}">Code Viewer</a> — Paste source code and pick a language to view it with syntax highlighting, supporting 20+ languages including Java, C#, Python, and Go.',
        s3_item6='<a href="{tool_number}">Number Reader</a> — Converts numbers into words for cardinal, ordinal, phone/account digits, time, date, and currency, with multiple reading styles per language.',
        s3_item7='<a href="{tool_typing}">Typing Speed Test</a> — Measures your typing speed (WPM) and accuracy on short practice passages and lets you share your score. Scoring runs entirely in your browser.',
        s3_item8='<a href="{game_syntax}">Coding Syntax Quiz</a> — A multiple-choice quiz on basic syntax for JavaScript, Python, Java, and C.',
        s3_p='Suggestions for new features or improvements are always welcome. The SQL Formatter uses the open-source <a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> library (MIT License), and the Code Viewer uses <a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> (MIT License), both bundled locally so processing still runs entirely in your browser. The Number Reader and Typing Speed Test are implemented with our own code and use no external library.',
        s4_h2="About advertising and running this service",
        s4_p='Formix may introduce advertising services such as Google AdSense in the future to help support running the site. If we do, how related data is handled will be explained transparently on the <a href="{privacy}">Privacy Policy</a> page, and the core functionality of our tools (e.g. JSON processing) will remain free regardless of whether ads are shown.',
        s5_h2="Contact",
        s5_p="For bug reports, feature requests, or any other inquiries, please reach out at the email below.",
    ),
    "ko": dict(
        title="사이트 소개 | Formix",
        description="Formix는 회원가입 없이 브라우저에서 바로 쓰는 무료 온라인 개발자 도구 모음입니다. 서비스 소개와 운영 철학, 제공 중인 기능을 안내합니다.",
        og_title="사이트 소개 | Formix",
        og_description="Formix 서비스 소개와 운영 철학을 안내합니다.",
        h1="사이트 소개", lead="Formix가 어떤 서비스인지, 어떤 원칙으로 운영되는지 소개합니다.",
        s1_h2="Formix란?",
        s1_p='Formix는 개발이나 업무 중 자주 마주하지만 번거로운 작업을 별도 프로그램 설치나 회원가입 없이, 웹 브라우저에서 바로 처리할 수 있도록 만든 무료 온라인 유틸리티 모음입니다. 첫 번째로 제공하는 기능은 <a href="{tool}">JSON 포매터</a>이며, 앞으로도 실무에 도움이 되는 도구를 지속적으로 추가할 예정입니다.',
        s2_h2="운영 원칙",
        s2_items=[
            ("가입 없이 바로 사용", "별도의 계정이나 로그인 없이 누구나 즉시 이용할 수 있습니다."),
            ("클라이언트 사이드 처리", '대부분의 도구는 입력값을 서버로 전송하지 않고 브라우저(자바스크립트) 안에서만 처리합니다. 자세한 내용은 <a href="{privacy}">개인정보처리방침</a>을 참고해주세요.'),
            ("가벼고 빠른 화면", "불필요한 요소를 줄이고 필요한 기능에 집중한 단순한 화면을 지향합니다."),
            ("다크 모드 기본 지원", "시스템 설정 또는 수동 전환으로 라이트/다크 테마를 선택할 수 있습니다."),
        ],
        s3_h2="제공 중인 기능",
        s3_item='<a href="{tool}">JSON 포매터 / 뷰어</a> — JSON 문자열의 유효성을 검사하고, 들여쓰기·문법 강조가 적용된 트리 형태로 보여줍니다. 노드 접기/펼치기와 키·값 검색을 지원합니다.',
        s3_item2='<a href="{tool_xml}">XML 포매터 / 뷰어</a> — XML 문자열의 유효성을 검사하고, 들여쓰기·문법 강조가 적용된 트리 형태로 보여줍니다. 노드 접기/펼치기와 태그·속성·텍스트 검색을 지원합니다.',
        s3_item3='<a href="{tool_converter}">JSON ↔ XML 변환기</a> — JSON을 XML로, XML을 JSON으로 변환합니다. 형식 자동 감지와 들여쓰기 설정을 지원합니다.',
        s3_item4='<a href="{tool_sql}">SQL 포매터</a> — SQL 쿼리를 알아보기 쉽게 들여쓰기하고 키워드 대소문자를 정리합니다. MySQL, PostgreSQL, SQL Server, BigQuery 등 여러 방언을 지원합니다.',
        s3_item5='<a href="{tool_code}">코드 뷰어</a> — 소스 코드를 붙여넣고 언어를 선택하면 문법 강조가 적용된 화면으로 보여줍니다. Java, C#, Python, Go 등 20여 개 언어를 지원합니다.',
        s3_item6='<a href="{tool_number}">숫자 읽기 변환기</a> — 숫자를 일반(기수), 서수, 전화·계좌번호, 시간, 날짜, 화폐 등으로 변환해 읽는 법을 보여줍니다. 언어별로 여러 표기 방식을 지원합니다.',
        s3_item7='<a href="{tool_typing}">타자 속도 테스트</a> — 짧은 연습 문장으로 타자 속도(WPM)와 정확도를 측정하고 결과를 공유할 수 있습니다. 채점은 모두 브라우저 안에서 이뤄집니다.',
        s3_item8='<a href="{game_syntax}">코딩 문법 퀴즈</a> — JavaScript, Python, Java, C의 기본 문법을 묻는 객관식 퀴즈입니다.',
        s3_p='새로운 기능 제안이나 개선 의견은 언제든 환영합니다. SQL 포매터는 오픈소스 <a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> 라이브러리(MIT 라이선스)를, 코드 뷰어는 <a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a>(MIT 라이선스)를 사용하며, 둘 다 로컬에 내장(vendor)하여 여전히 모든 처리가 브라우저 안에서만 이뤄집니다. 숫자 읽기 변환기와 타자 속도 테스트는 외부 라이브러리 없이 자체 구현했습니다.',
        s4_h2="광고 및 서비스 운영에 대해",
        s4_p='Formix는 서비스 운영을 위해 향후 Google AdSense 등 광고 서비스를 도입할 수 있습니다. 광고 도입 시 관련 데이터 처리 방식은 <a href="{privacy}">개인정보처리방침</a> 페이지를 통해 투명하게 안내하며, 도구의 핵심 기능(예: JSON 처리)은 광고 여부와 무관하게 계속 무료로 제공됩니다.',
        s5_h2="문의", s5_p="버그 제보, 기능 제안, 기타 문의는 아래 이메일로 연락해 주세요.",
    ),
    "ja": dict(
        title="サイト紹介 | Formix",
        description="Formixは会員登録不要でブラウザ上ですぐ使える無料のオンライン開発者ツール集です。サービス紹介、運営方針、提供機能をご案内します。",
        og_title="サイト紹介 | Formix",
        og_description="Formixのサービス紹介と運営方針をご案内します。",
        h1="サイト紹介", lead="Formixがどのようなサービスか、どのような方針で運営されているかをご紹介します。",
        s1_h2="Formixとは?",
        s1_p='Formixは、開発や業務でよく発生する細かくて面倒な作業を、別途プログラムのインストールや会員登録なしに、ウェブブラウザ上ですぐに処理できるようにした無料のオンラインユーティリティ集です。最初に提供する機能は<a href="{tool}">JSONフォーマッター</a>で、今後も実務に役立つツールを継続的に追加していく予定です。',
        s2_h2="運営方針",
        s2_items=[
            ("登録不要ですぐ使える", "アカウントやログインなしで誰でもすぐに利用できます。"),
            ("クライアントサイド処理", 'ほとんどのツールは入力値をサーバーに送信せず、ブラウザ(JavaScript)内でのみ処理します。詳しくは<a href="{privacy}">プライバシーポリシー</a>をご覚ください。'),
            ("軸くて速い画面", "不要な要素を減らし、必要な機能に集中したシンプルな画面を目指しています。"),
            ("ダークモード標準対応", "システム設定または手動切り替えでライト/ダークテーマを選択できます。"),
        ],
        s3_h2="提供中の機能",
        s3_item='<a href="{tool}">JSONフォーマッター / ビューア</a> — JSON文字列の妥当性を検証し、インデントとシンタックスハイライトを適用したツリー形式で表示します。ノードの折りたたみ/展開、キー・値の検索に対応しています。',
        s3_item2='<a href="{tool_xml}">XMLフォーマッター / ビューア</a> — XML文字列の妥当性を検証し、インデントとシンタックスハイライトを適用したツリー形式で表示します。ノードの折りたたみ/展開、タグ・属性・テキストの検索に対応しています。',
        s3_item3='<a href="{tool_converter}">JSON ↔ XML 変換ツール</a> — JSONをXMLに、XMLをJSONに変換します。形式の自動検出とインデント設定に対応しています。',
        s3_item4='<a href="{tool_sql}">SQLフォーマッター</a> — SQLクエリを見やすくインデント・整形します。MySQL、PostgreSQL、SQL Server、BigQueryなど複数の方言に対応しています。',
        s3_item5='<a href="{tool_code}">コードビューア</a> — ソースコードを貼り付けて言語を選択すると、シンタックスハイライト付きで表示します。Java、C#、Python、Goなど20以上の言語に対応しています。',
        s3_item6='<a href="{tool_number}">数字の読み方変換</a> — 数字を基数・序数・電話/口座番号・時刻・日付・通貨などに変換して読み方を表示します。言語ごとに複数の表記方式に対応しています。',
        s3_item7='<a href="{tool_typing}">タイピング速度テスト</a> — 短い練習文でタイピング速度(WPM)と正確率を測定し、結果をシェアできます。採点はすべてブラウザ内で行われます。',
        s3_item8='<a href="{game_syntax}">コーディング文法クイズ</a> — JavaScript、Python、Java、Cの基本文法を問う選択式クイズです。',
        s3_p='新機能のご提案や改善のご意見はいつでも歓迎します。SQLフォーマッターはオープンソースの<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a>ライブラリ(MITライセンス)を、コードビューアは<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a>(MITライセンス)を使用しており、どちらもローカルにバンドル(vendor)しているため処理はすべてブラウザ内で完結します。数字の読み方変換とタイピング速度テストは外部ライブラリを使わず独自に実装しています。',
        s4_h2="広告およびサービス運営について",
        s4_p='Formixはサービス運営のため、今後 Google AdSense などの広告サービスを導入する場合があります。導入時の関連データの取り扱いは<a href="{privacy}">プライバシーポリシー</a>ページで透明性を持ってご案内し、ツールの中核機能(JSON処理など)は広告の有無にかかわらず引き続き無料で提供します。',
        s5_h2="お問い合わせ", s5_p="不具合報告、機能提案、その他のお問い合わせは下記メールアドレスまでご連絡ください。",
    ),
    "zh": dict(
        title="关于本站 | Formix",
        description="Formix是无需注册即可在浏览器中直接使用的免费在线开发者工具集。介绍服务内容、运营理念和已提供的功能。",
        og_title="关于本站 | Formix",
        og_description="介绍Formix的服务内容与运营理念。",
        h1="关于本站", lead="介绍Formix是一项怎样的服务，以及它的运营理念。",
        s1_h2="什么是Formix?",
        s1_p='Formix是一套免费的在线实用工具集，让你无需安装额外程序、无需注册账号，就能在网页浏览器中直接处理开发或工作中常见的琐碎任务。首个提供的功能是<a href="{tool}">JSON 格式化工具</a>，未来还会持续添加对实际工作有帮助的工具。',
        s2_h2="运营理念",
        s2_items=[
            ("无需注册，立即使用", "任何人无需账号或登录即可立即使用。"),
            ("客户端处理", '大多数工具不会将输入内容发送到服务器，仅在浏览器(JavaScript)中处理。详情请参阅<a href="{privacy}">隐私政策</a>。'),
            ("轻量快速的界面", "减少不必要的元素，专注于真正需要的功能，力求界面简洁。"),
            ("默认支持深色模式", "可根据系统设置自动切换，或手动在浅色/深色主题之间切换。"),
        ],
        s3_h2="已提供的功能",
        s3_item='<a href="{tool}">JSON 格式化 / 查看器</a> — 验证 JSON 字符串的有效性，并以带缩进和语法高亮的树形结构展示。支持节点折叠/展开以及键值搜索。',
        s3_item2='<a href="{tool_xml}">XML 格式化 / 查看器</a> — 验证 XML 字符串的有效性，并以带缩进和语法高亮的树形结构展示。支持节点折叠/展开以及标签·属性·文本搜索。',
        s3_item3='<a href="{tool_converter}">JSON ↔ XML 转换工具</a> — 将 JSON 转换为 XML，或将 XML 转换为 JSON，支持自动检测格式与自定义缩进。',
        s3_item4='<a href="{tool_sql}">SQL 格式化工具</a> — 为 SQL 查询语句添加清晰的缩进和关键字大小写格式化，支持 MySQL、PostgreSQL、SQL Server、BigQuery 等多种方言。',
        s3_item5='<a href="{tool_code}">代码查看器</a> — 粘贴源代码并选择语言，即可获得带语法高亮的展示，支持 Java、C#、Python、Go 等 20 多种语言。',
        s3_item6='<a href="{tool_number}">数字读法转换</a> — 将数字转换为基数、序数、电话/账号、时间、日期、货币等读法。每种语言均支持多种表示方式。',
        s3_item7='<a href="{tool_typing}">打字速度测试</a> — 通过简短的练习句子测量打字速度(WPM)和准确率，并可分享成绩。所有计分均在浏览器本地完成。',
        s3_item8='<a href="{game_syntax}">编程语法测验</a> — 一个关于 JavaScript、Python、Java 和 C 基础语法的选择题测验。',
        s3_p='欢迎随时提出新功能建议或改进意见。SQL 格式化工具使用了开源的 <a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> 库(MIT 许可)，代码查看器使用了 <a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a>(MIT 许可)，两者均已本地打包(vendor)，因此所有处理仍完全在您的浏览器中进行。数字读法转换和打字速度测试未使用任何外部库，均为我们自行实现。',
        s4_h2="关于广告与服务运营",
        s4_p='为了维持服务运营，Formix未来可能会引入 Google AdSense 等广告服务。如果引入广告，相关数据的处理方式将在<a href="{privacy}">隐私政策</a>页面中透明说明，工具的核心功能(如 JSON 处理)将始终免费提供，不受广告影响。',
        s5_h2="联系方式", s5_p="如有错误反馈、功能建议或其他咨询，请通过以下邮箱联系我们。",
    ),
    "es": dict(
        title="Acerca de | Formix",
        description="Formix es una colección gratuita de herramientas en línea para desarrolladores que puedes usar directamente en tu navegador, sin registro. Conoce el servicio, sus principios y las funciones disponibles.",
        og_title="Acerca de | Formix",
        og_description="Una introducción a Formix y los principios detrás de él.",
        h1="Acerca de", lead="Una introducción a qué es Formix y los principios por los que se rige.",
        s1_h2="¿Qué es Formix?",
        s1_p='Formix es una colección gratuita de utilidades en línea que te permite manejar tareas pequeñas pero tediosas que suelen surgir durante el desarrollo o el trabajo, directamente en tu navegador web — sin instalar ningún programa aparte, sin necesidad de registro. La primera herramienta que ofrecemos es el <a href="{tool}">Formateador JSON</a>, y planeamos seguir añadiendo herramientas realmente útiles para el trabajo diario.',
        s2_h2="Nuestros principios",
        s2_items=[
            ("Úsalo al instante, sin registro", "Cualquiera puede empezar a usarlo de inmediato — no se necesita cuenta ni inicio de sesión."),
            ("Procesamiento del lado del cliente", 'La mayoría de las herramientas procesan tu entrada completamente en el navegador (JavaScript) y nunca la envían a un servidor. Consulta nuestra <a href="{privacy}">Política de privacidad</a> para más detalles.'),
            ("Ligero y rápido", "Buscamos una pantalla simple que elimine elementos innecesarios y se enfoque en las funciones que realmente necesitas."),
            ("Modo oscuro incorporado", "Elige entre temas claro y oscuro, automáticamente según la configuración de tu sistema o manualmente con el interruptor."),
        ],
        s3_h2="Funciones disponibles",
        s3_item='<a href="{tool}">Formateador / Visor JSON</a> — Valida cadenas JSON y las muestra como un árbol con sangría y resaltado de sintaxis. Permite colapsar/expandir nodos y buscar claves y valores.',
        s3_item2='<a href="{tool_xml}">Formateador / Visor XML</a> — Valida cadenas XML y las muestra como un árbol con sangría y resaltado de sintaxis. Permite colapsar/expandir nodos y buscar etiquetas, atributos y texto.',
        s3_item3='<a href="{tool_converter}">Convertidor JSON ↔ XML</a> — Convierte JSON a XML o XML a JSON, con detección automática de formato y sangría configurable.',
        s3_item4='<a href="{tool_sql}">Formateador SQL</a> — Embellece consultas SQL con sangría adecuada y formato de palabras clave, compatible con varios dialectos (MySQL, PostgreSQL, SQL Server, BigQuery y más).',
        s3_item5='<a href="{tool_code}">Visor de código</a> — Pega código fuente y elige un lenguaje para verlo con resaltado de sintaxis, compatible con más de 20 lenguajes, incluidos Java, C#, Python y Go.',
        s3_item6='<a href="{tool_number}">Lector de números</a> — Convierte números en palabras para cardinales, ordinales, dígitos de teléfono/cuenta, hora, fecha y moneda, con varios estilos de lectura por idioma.',
        s3_item7='<a href="{tool_typing}">Prueba de velocidad de escritura</a> — Mide tu velocidad de escritura (PPM) y precisión en pasajes cortos de práctica y te permite compartir tu puntuación. El cálculo ocurre completamente en tu navegador.',
        s3_item8='<a href="{game_syntax}">Quiz de sintaxis de código</a> — Un quiz de opción múltiple sobre la sintaxis básica de JavaScript, Python, Java y C.',
        s3_p='Las sugerencias de nuevas funciones o mejoras siempre son bienvenidas. El Formateador SQL usa la biblioteca de código abierto <a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> (licencia MIT), y el Visor de código usa <a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> (licencia MIT), ambas incluidas localmente para que el procesamiento siga ocurriendo enteramente en tu navegador. El Lector de números y la Prueba de velocidad de escritura están implementados con código propio y no usan ninguna biblioteca externa.',
        s4_h2="Sobre la publicidad y el funcionamiento de este servicio",
        s4_p='Formix podría introducir servicios publicitarios como Google AdSense en el futuro para ayudar a sostener el sitio. Si lo hacemos, cómo se manejan los datos relacionados se explicará de forma transparente en la página de <a href="{privacy}">Política de privacidad</a>, y la funcionalidad principal de nuestras herramientas (p. ej. el procesamiento de JSON) seguirá siendo gratuita independientemente de si se muestran anuncios.',
        s5_h2="Contacto",
        s5_p="Para reportar errores, sugerir funciones o cualquier otra consulta, escríbenos al correo electrónico de abajo.",
    ),
    "vi": dict(
        title="Giới thiệu | Formix",
        description="Formix là bộ công cụ trực tuyến miễn phí cho lập trình viên, dùng ngay trên trình duyệt, không cần đăng ký. Tìm hiểu về dịch vụ, nguyên tắc hoạt động và các tính năng hiện có.",
        og_title="Giới thiệu | Formix",
        og_description="Giới thiệu về Formix và những nguyên tắc vận hành của nó.",
        h1="Giới thiệu", lead="Giới thiệu Formix là gì và nguyên tắc vận hành của nó.",
        s1_h2="Formix là gì?",
        s1_p='Formix là bộ tiện ích trực tuyến miễn phí giúp bạn xử lý những việc nhỏ nhưng phiền phức thường gặp trong lúc phát triển hoặc làm việc, ngay trên trình duyệt web — không cần cài đặt phần mềm riêng, không cần đăng ký. Công cụ đầu tiên chúng tôi cung cấp là <a href="{tool}">Công cụ định dạng JSON</a>, và chúng tôi dự định tiếp tục bổ sung những công cụ thực sự hữu ích cho công việc hằng ngày.',
        s2_h2="Nguyên tắc của chúng tôi",
        s2_items=[
            ("Dùng ngay, không cần đăng ký", "Bất kỳ ai cũng có thể bắt đầu sử dụng ngay lập tức — không cần tài khoản hay đăng nhập."),
            ("Xử lý phía máy khách", 'Hầu hết công cụ xử lý dữ liệu của bạn hoàn toàn trên trình duyệt (JavaScript) và không bao giờ gửi lên máy chủ. Xem <a href="{privacy}">Chính sách bảo mật</a> để biết chi tiết.'),
            ("Nhẹ và nhanh", "Chúng tôi hướng đến một giao diện đơn giản, loại bỏ yếu tố không cần thiết và tập trung vào những tính năng bạn thực sự cần."),
            ("Có sẵn chế độ tối", "Chọn giữa giao diện sáng và tối, tự động theo cài đặt hệ thống hoặc thủ công bằng nút chuyển đổi."),
        ],
        s3_h2="Tính năng hiện có",
        s3_item='<a href="{tool}">Định dạng / Xem JSON</a> — Kiểm tra tính hợp lệ của chuỗi JSON và hiển thị dưới dạng cây có thụt lề, tô màu cú pháp. Hỗ trợ thu/mở rộng nút và tìm kiếm khóa/giá trị.',
        s3_item2='<a href="{tool_xml}">Định dạng / Xem XML</a> — Kiểm tra tính hợp lệ của chuỗi XML và hiển thị dưới dạng cây có thụt lề, tô màu cú pháp. Hỗ trợ thu/mở rộng nút và tìm kiếm thẻ/thuộc tính/văn bản.',
        s3_item3='<a href="{tool_converter}">Chuyển đổi JSON ↔ XML</a> — Chuyển JSON sang XML hoặc XML sang JSON, tự động nhận diện định dạng và tùy chỉnh thụt lề.',
        s3_item4='<a href="{tool_sql}">Định dạng SQL</a> — Làm đẹp câu lệnh SQL với thụt lề hợp lý và viết hoa từ khóa, hỗ trợ nhiều phương ngữ (MySQL, PostgreSQL, SQL Server, BigQuery và hơn nữa).',
        s3_item5='<a href="{tool_code}">Xem mã nguồn</a> — Dán mã nguồn và chọn ngôn ngữ để xem với tô màu cú pháp, hỗ trợ hơn 20 ngôn ngữ bao gồm Java, C#, Python và Go.',
        s3_item6='<a href="{tool_number}">Đọc số thành chữ</a> — Chuyển số thành chữ cho số đếm, số thứ tự, số điện thoại/tài khoản, thời gian, ngày tháng và tiền tệ, với nhiều kiểu đọc theo từng ngôn ngữ.',
        s3_item7='<a href="{tool_typing}">Kiểm tra tốc độ đánh máy</a> — Đo tốc độ đánh máy (WPM) và độ chính xác qua các đoạn luyện tập ngắn và cho phép chia sẻ điểm số. Mọi phép tính diễn ra hoàn toàn trên trình duyệt.',
        s3_item8='<a href="{game_syntax}">Đố vui cú pháp lập trình</a> — Một bài trắc nghiệm về cú pháp cơ bản của JavaScript, Python, Java và C.',
        s3_p='Chúng tôi luôn hoan nghênh các góp ý về tính năng mới hoặc cải tiến. Công cụ định dạng SQL sử dụng thư viện mã nguồn mở <a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> (giấy phép MIT), và công cụ xem mã nguồn sử dụng <a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> (giấy phép MIT), cả hai đều được đóng gói cục bộ nên quá trình xử lý vẫn diễn ra hoàn toàn trên trình duyệt của bạn. Công cụ đọc số thành chữ và kiểm tra tốc độ đánh máy do chúng tôi tự xây dựng, không dùng thư viện ngoài.',
        s4_h2="Về quảng cáo và việc vận hành dịch vụ",
        s4_p='Trong tương lai, Formix có thể giới thiệu các dịch vụ quảng cáo như Google AdSense để hỗ trợ vận hành trang web. Nếu có, cách xử lý dữ liệu liên quan sẽ được giải thích minh bạch trên trang <a href="{privacy}">Chính sách bảo mật</a>, và các tính năng cốt lõi của công cụ (ví dụ xử lý JSON) sẽ luôn miễn phí bất kể có hiển thị quảng cáo hay không.',
        s5_h2="Liên hệ",
        s5_p="Để báo lỗi, đề xuất tính năng hoặc bất kỳ thắc mắc nào khác, vui lòng liên hệ qua email bên dưới.",
    ),
    "pt": dict(
        title="Sobre | Formix",
        description="O Formix é uma coleção gratuita de ferramentas online para desenvolvedores, utilizável diretamente no navegador, sem necessidade de cadastro. Conheça o serviço, seus princípios e as funcionalidades disponíveis.",
        og_title="Sobre | Formix",
        og_description="Uma introdução ao Formix e aos princípios por trás dele.",
        h1="Sobre", lead="Uma introdução ao que é o Formix e aos princípios que o guiam.",
        s1_h2="O que é o Formix?",
        s1_p='O Formix é uma coleção gratuita de utilitários online que permite lidar com pequenas tarefas, mas tediosas, comuns no desenvolvimento ou no trabalho, diretamente no seu navegador — sem instalar nenhum programa separado, sem necessidade de cadastro. A primeira ferramenta que oferecemos é o <a href="{tool}">Formatador JSON</a>, e planejamos continuar adicionando ferramentas realmente úteis para o dia a dia.',
        s2_h2="Nossos princípios",
        s2_items=[
            ("Use instantaneamente, sem cadastro", "Qualquer pessoa pode começar a usar imediatamente — nenhuma conta ou login é necessário."),
            ("Processamento no lado do cliente", 'A maioria das ferramentas processa sua entrada inteiramente no navegador (JavaScript) e nunca a envia a um servidor. Veja nossa <a href="{privacy}">Política de privacidade</a> para detalhes.'),
            ("Leve e rápido", "Buscamos uma tela simples que elimina elementos desnecessários e foca nas funcionalidades que você realmente precisa."),
            ("Modo escuro incluso", "Escolha entre temas claro e escuro, automaticamente pelas configurações do sistema ou manualmente com o botão."),
        ],
        s3_h2="Funcionalidades disponíveis",
        s3_item='<a href="{tool}">Formatador / Visualizador JSON</a> — Valida strings JSON e as exibe como uma árvore com recuo e destaque de sintaxe. Permite recolher/expandir nós e buscar chaves e valores.',
        s3_item2='<a href="{tool_xml}">Formatador / Visualizador XML</a> — Valida strings XML e as exibe como uma árvore com recuo e destaque de sintaxe. Permite recolher/expandir nós e buscar tags, atributos e texto.',
        s3_item3='<a href="{tool_converter}">Conversor JSON ↔ XML</a> — Converte JSON para XML ou XML para JSON, com detecção automática de formato e recuo configurável.',
        s3_item4='<a href="{tool_sql}">Formatador SQL</a> — Embeleza consultas SQL com recuo adequado e formatação de palavras-chave, compatível com vários dialetos (MySQL, PostgreSQL, SQL Server, BigQuery e mais).',
        s3_item5='<a href="{tool_code}">Visualizador de código</a> — Cole o código-fonte e escolha uma linguagem para visualizá-lo com destaque de sintaxe, compatível com mais de 20 linguagens, incluindo Java, C#, Python e Go.',
        s3_item6='<a href="{tool_number}">Leitor de números</a> — Converte números em palavras para cardinais, ordinais, dígitos de telefone/conta, hora, data e moeda, com vários estilos de leitura por idioma.',
        s3_item7='<a href="{tool_typing}">Teste de velocidade de digitação</a> — Mede sua velocidade de digitação (PPM) e precisão em trechos curtos de prática e permite compartilhar sua pontuação. O cálculo ocorre inteiramente no seu navegador.',
        s3_item8='<a href="{game_syntax}">Quiz de sintaxe de código</a> — Um quiz de múltipla escolha sobre a sintaxe básica de JavaScript, Python, Java e C.',
        s3_p='Sugestões de novas funcionalidades ou melhorias são sempre bem-vindas. O Formatador SQL usa a biblioteca de código aberto <a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> (licença MIT), e o Visualizador de código usa <a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> (licença MIT), ambos empacotados localmente para que o processamento continue ocorrendo inteiramente no seu navegador. O Leitor de números e o Teste de velocidade de digitação foram implementados com código próprio, sem bibliotecas externas.',
        s4_h2="Sobre publicidade e a operação deste serviço",
        s4_p='O Formix pode introduzir serviços de publicidade como o Google AdSense no futuro para ajudar a sustentar o site. Se o fizermos, a forma como os dados relacionados são tratados será explicada de forma transparente na página de <a href="{privacy}">Política de privacidade</a>, e a funcionalidade principal de nossas ferramentas (como o processamento de JSON) permanecerá gratuita independentemente da exibição de anúncios.',
        s5_h2="Contato",
        s5_p="Para relatar erros, sugerir funcionalidades ou qualquer outra dúvida, entre em contato pelo e-mail abaixo.",
    ),
    "id": dict(
        title="Tentang | Formix",
        description="Formix adalah kumpulan alat online gratis untuk pengembang yang dapat digunakan langsung di browser Anda, tanpa pendaftaran. Pelajari tentang layanan ini, prinsipnya, dan fitur yang tersedia.",
        og_title="Tentang | Formix",
        og_description="Pengantar tentang Formix dan prinsip di baliknya.",
        h1="Tentang", lead="Pengantar tentang apa itu Formix dan prinsip yang mendasarinya.",
        s1_h2="Apa itu Formix?",
        s1_p='Formix adalah kumpulan utilitas online gratis yang membantu Anda menangani tugas-tugas kecil namun merepotkan yang sering muncul saat pengembangan atau bekerja, langsung di browser web Anda — tanpa perlu menginstal program terpisah, tanpa perlu mendaftar. Alat pertama yang kami tawarkan adalah <a href="{tool}">Pemformat JSON</a>, dan kami berencana untuk terus menambahkan alat yang benar-benar bermanfaat untuk pekerjaan sehari-hari.',
        s2_h2="Prinsip kami",
        s2_items=[
            ("Gunakan langsung, tanpa pendaftaran", "Siapa pun dapat langsung menggunakannya — tidak perlu akun atau login."),
            ("Pemrosesan di sisi klien", 'Sebagian besar alat memproses input Anda sepenuhnya di browser (JavaScript) dan tidak pernah mengirimkannya ke server. Lihat <a href="{privacy}">Kebijakan Privasi</a> kami untuk detailnya.'),
            ("Ringan dan cepat", "Kami bertujuan menghadirkan tampilan sederhana yang menghilangkan elemen yang tidak perlu dan berfokus pada fitur yang benar-benar Anda butuhkan."),
            ("Mode gelap bawaan", "Pilih antara tema terang dan gelap, baik secara otomatis dari pengaturan sistem Anda maupun secara manual dengan tombol pengalih."),
        ],
        s3_h2="Fitur yang tersedia",
        s3_item='<a href="{tool}">Pemformat / Penampil JSON</a> — Memvalidasi string JSON dan menampilkannya sebagai pohon dengan indentasi dan penyorotan sintaks. Mendukung melipat/membuka node serta mencari kunci dan nilai.',
        s3_item2='<a href="{tool_xml}">Pemformat / Penampil XML</a> — Memvalidasi string XML dan menampilkannya sebagai pohon dengan indentasi dan penyorotan sintaks. Mendukung melipat/membuka node serta mencari tag, atribut, dan teks.',
        s3_item3='<a href="{tool_converter}">Konverter JSON ↔ XML</a> — Mengonversi JSON ke XML atau XML ke JSON, dengan deteksi format otomatis dan indentasi yang dapat disesuaikan.',
        s3_item4='<a href="{tool_sql}">Pemformat SQL</a> — Merapikan kueri SQL dengan indentasi yang tepat dan penulisan kata kunci, mendukung berbagai dialek (MySQL, PostgreSQL, SQL Server, BigQuery, dan lainnya).',
        s3_item5='<a href="{tool_code}">Penampil Kode</a> — Tempel kode sumber dan pilih bahasa untuk melihatnya dengan penyorotan sintaks, mendukung lebih dari 20 bahasa termasuk Java, C#, Python, dan Go.',
        s3_item6='<a href="{tool_number}">Pembaca Angka</a> — Mengonversi angka menjadi kata untuk kardinal, ordinal, digit telepon/rekening, waktu, tanggal, dan mata uang, dengan beberapa gaya pembacaan per bahasa.',
        s3_item7='<a href="{tool_typing}">Tes Kecepatan Mengetik</a> — Mengukur kecepatan mengetik (WPM) dan akurasi Anda pada paragraf latihan singkat dan memungkinkan Anda membagikan skor. Penilaian berjalan sepenuhnya di browser Anda.',
        s3_item8='<a href="{game_syntax}">Kuis Sintaks Koding</a> — Kuis pilihan ganda tentang sintaks dasar JavaScript, Python, Java, dan C.',
        s3_p='Saran untuk fitur baru atau perbaikan selalu kami sambut. Pemformat SQL menggunakan pustaka sumber terbuka <a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> (Lisensi MIT), dan Penampil Kode menggunakan <a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> (Lisensi MIT), keduanya dibundel secara lokal sehingga pemrosesan tetap berjalan sepenuhnya di browser Anda. Pembaca Angka dan Tes Kecepatan Mengetik dibuat dengan kode kami sendiri tanpa pustaka eksternal.',
        s4_h2="Tentang iklan dan pengoperasian layanan ini",
        s4_p='Formix mungkin memperkenalkan layanan iklan seperti Google AdSense di masa depan untuk membantu mendukung operasional situs. Jika demikian, cara penanganan data terkait akan dijelaskan secara transparan di halaman <a href="{privacy}">Kebijakan Privasi</a>, dan fungsi inti alat kami (misalnya pemrosesan JSON) akan tetap gratis terlepas dari ditampilkannya iklan.',
        s5_h2="Kontak",
        s5_p="Untuk melaporkan bug, menyarankan fitur, atau pertanyaan lainnya, silakan hubungi kami melalui email di bawah ini.",
    ),
    "de": dict(
        title="Über uns | Formix",
        description="Formix ist eine kostenlose Sammlung von Online-Entwicklertools, die Sie direkt im Browser nutzen können, ohne Registrierung. Erfahren Sie mehr über den Dienst, seine Prinzipien und die verfügbaren Funktionen.",
        og_title="Über uns | Formix",
        og_description="Eine Einführung in Formix und die Prinzipien dahinter.",
        h1="Über uns", lead="Eine Einführung, was Formix ist und nach welchen Prinzipien es betrieben wird.",
        s1_h2="Was ist Formix?",
        s1_p='Formix ist eine kostenlose Sammlung von Online-Dienstprogrammen, mit denen Sie kleine, aber lästige Aufgaben, die bei Entwicklung oder Arbeit häufig vorkommen, direkt in Ihrem Webbrowser erledigen können — ohne separates Programm zu installieren, ohne Registrierung. Das erste angebotene Tool ist der <a href="{tool}">JSON-Formatierer</a>, und wir planen, weiterhin Tools hinzuzufügen, die im Arbeitsalltag wirklich nützlich sind.',
        s2_h2="Unsere Prinzipien",
        s2_items=[
            ("Sofort nutzbar, keine Registrierung", "Jeder kann sofort damit beginnen — es ist kein Konto und keine Anmeldung erforderlich."),
            ("Clientseitige Verarbeitung", 'Die meisten Tools verarbeiten Ihre Eingabe vollständig im Browser (JavaScript) und senden sie nie an einen Server. Details finden Sie in unserer <a href="{privacy}">Datenschutzerklärung</a>.'),
            ("Leicht und schnell", "Wir streben eine einfache Oberfläche an, die unnötige Elemente weglässt und sich auf die wirklich benötigten Funktionen konzentriert."),
            ("Integrierter Dunkelmodus", "Wählen Sie zwischen Hell- und Dunkelmodus, automatisch nach Ihren Systemeinstellungen oder manuell über den Schalter."),
        ],
        s3_h2="Verfügbare Funktionen",
        s3_item='<a href="{tool}">JSON-Formatierer / Viewer</a> — Validiert JSON-Strings und zeigt sie als eingerückten, syntaxhervorgehobenen Baum an. Unterstützt das Ein-/Ausklappen von Knoten sowie die Suche nach Schlüsseln und Werten.',
        s3_item2='<a href="{tool_xml}">XML-Formatierer / Viewer</a> — Validiert XML-Strings und zeigt sie als eingerückten, syntaxhervorgehobenen Baum an. Unterstützt das Ein-/Ausklappen von Knoten sowie die Suche nach Tags, Attributen und Text.',
        s3_item3='<a href="{tool_converter}">JSON ↔ XML Konverter</a> — Konvertiert JSON in XML oder XML in JSON, mit automatischer Formaterkennung und konfigurierbarer Einrückung.',
        s3_item4='<a href="{tool_sql}">SQL-Formatierer</a> — Formatiert SQL-Abfragen mit korrekter Einrückung und Schlüsselwort-Schreibweise, unterstützt mehrere Dialekte (MySQL, PostgreSQL, SQL Server, BigQuery und mehr).',
        s3_item5='<a href="{tool_code}">Code-Viewer</a> — Quellcode einfügen und eine Sprache wählen, um ihn mit Syntaxhervorhebung anzuzeigen, unterstützt über 20 Sprachen, darunter Java, C#, Python und Go.',
        s3_item6='<a href="{tool_number}">Zahlen-Vorleser</a> — Wandelt Zahlen in Wörter um, für Grund- und Ordnungszahlen, Telefon-/Kontoziffern, Uhrzeit, Datum und Währung, mit mehreren Lesestilen je Sprache.',
        s3_item7='<a href="{tool_typing}">Schreibgeschwindigkeitstest</a> — Misst Ihre Schreibgeschwindigkeit (WPM) und Genauigkeit bei kurzen Übungstexten und ermöglicht das Teilen Ihres Ergebnisses. Die Auswertung erfolgt vollständig in Ihrem Browser.',
        s3_item8='<a href="{game_syntax}">Coding-Syntax-Quiz</a> — Ein Multiple-Choice-Quiz zur Grundsyntax von JavaScript, Python, Java und C.',
        s3_p='Vorschläge für neue Funktionen oder Verbesserungen sind immer willkommen. Der SQL-Formatierer nutzt die Open-Source-Bibliothek <a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> (MIT-Lizenz), und der Code-Viewer nutzt <a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> (MIT-Lizenz), beide lokal eingebunden, sodass die Verarbeitung weiterhin vollständig in Ihrem Browser erfolgt. Der Zahlen-Vorleser und der Schreibgeschwindigkeitstest sind mit eigenem Code implementiert und nutzen keine externe Bibliothek.',
        s4_h2="Zu Werbung und dem Betrieb dieses Dienstes",
        s4_p='Formix könnte in Zukunft Werbedienste wie Google AdSense einführen, um den Betrieb der Website zu unterstützen. Falls dies geschieht, wird der Umgang mit den entsprechenden Daten transparent auf der Seite <a href="{privacy}">Datenschutzerklärung</a> erläutert, und die Kernfunktionen unserer Tools (z. B. die JSON-Verarbeitung) bleiben unabhängig von angezeigter Werbung kostenlos.',
        s5_h2="Kontakt",
        s5_p="Für Fehlermeldungen, Funktionswünsche oder sonstige Anfragen erreichen Sie uns über die unten stehende E-Mail-Adresse.",
    ),
}

CONTENT["privacy"] = {
    "en": dict(
        title="Privacy Policy | Formix",
        description="Formix's privacy policy. Explains what information we collect, our use of cookies/local storage, and how data is handled in relation to advertising (Google AdSense).",
        og_title="Privacy Policy | Formix",
        og_description="Information on Formix's collection and use of personal data and our use of cookies.",
        h1="Privacy Policy", effective="Effective date: September 20, 2026",
        intro='Formix (the "Site") values its users\' privacy and strives to comply with applicable data protection laws. This policy explains what information the Site collects and how it is used.',
        s1_h2="1. Information processed and how",
        s1_p1="Tools provided on the Site, such as the JSON Formatter, process the text you enter entirely within your browser (JavaScript) and never send it to a server. In other words, the JSON data or text you input is never transmitted to or stored by the Site operator.",
        s1_p2="Simple preference settings, such as your theme choice (light/dark mode), are stored only in your browser's local storage (localStorage) and are never transmitted externally.",
        s1_p3='The Typing Speed Test is an exception: if you choose to submit your score to the public leaderboard, the nickname you enter along with your WPM and accuracy are sent to and stored on our server so they can be shown to other visitors. We do not require or collect your name, email, or any other identifying information for this — only the nickname you type. Your IP address is used only momentarily, in hashed form, to apply basic rate-limiting against spam submissions, and is not stored in a form that identifies you. If you do not submit a score, nothing about the test is sent anywhere.',
        s2_h2="2. Use of cookies and similar technologies",
        s2_p1="The Site may use cookies for service analytics and advertising purposes. A cookie is a small piece of information a website stores in your browser; you can refuse or delete cookies through your browser settings. Note that refusing cookies may limit some features.",
        s2_p2='If you appear to be visiting from the EEA, UK, or Switzerland, a consent banner is shown on your first visit so you can accept or reject non-essential (advertising/analytics) cookies. Your choice is stored in your browser and you can change it anytime using the "Cookie preferences" link in the footer.',
        s3_h2="3. Use of advertising services (Google AdSense)",
        s3_p1="To help operate and maintain the Site, we may display advertisements from third-party providers, including Google.",
        s3_li1="Third-party vendors, including Google, may use cookies to serve ads based on a user's prior visits to this or other websites.",
        s3_li2="Google's use of advertising cookies enables Google and its partners to serve ads based on a user's visits to this Site and/or other sites on the Internet.",
        s3_li3='Users may opt out of personalized advertising by visiting <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">Google Ads Settings</a>, or opt out of third-party vendor cookies used for personalized advertising by visiting <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a>.',
        s3_p2="The timing and extent to which advertising is actually implemented may vary depending on how the Site is operated, and any changes will be announced through this policy.",
        s4_h2="4. Disclosure of personal information to third parties",
        s4_p1="The Site does not, in principle, share users' personal information with outside parties, except where required by law or requested by an investigative authority through lawful procedure.",
        s5_h2="5. User rights",
        s5_p1="Users may delete cookies and local storage data at any time through their browser settings, and may direct any questions about data handling to the contact below.",
        s6_h2="6. Contact", s6_p1="For questions about how personal data is handled, please contact us at the email address below.",
        s7_h2="7. Changes to this policy",
        s7_p1="This Privacy Policy may be revised in response to changes in law, policy, or the Site's services, and any changes will be announced through the Site.",
    ),
    "ko": dict(
        title="개인정보처리방침 | Formix",
        description="Formix의 개인정보처리방침입니다. 수집하는 정보, 쿠키·로컬스토리지 사용, 광고(Google AdSense) 관련 데이터 처리 방식을 안내합니다.",
        og_title="개인정보처리방침 | Formix",
        og_description="Formix의 개인정보 수집·이용 및 쿠키 사용에 대한 안내입니다.",
        h1="개인정보처리방침", effective="시행일자: 2026년 9월 20일",
        intro='Formix(이하 "사이트")는 이용자의 개인정보를 소중히 여기며, 개인정보 보호법 등 관련 법령을 준수하기 위해 노력합니다. 본 방침은 사이트가 어떤 정보를 어떻게 수집·이용하는지 설명합니다.',
        s1_h2="1. 처리하는 정보 및 처리 방식",
        s1_p1="사이트에서 제공하는 JSON 포매터 등 도구는 입력하신 텍스트를 서버로 전송하지 않고 이용자의 브라우저(자바스크립트) 내에서만 처리합니다. 즉, 입력한 JSON 데이터나 텍스트는 사이트 운영자에게 전달되거나 저장되지 않습니다.",
        s1_p2="다만 화면 테마 설정(라이트/다크 모드)과 같은 단순 환경설정 값은 이용자의 브라우저 로컬 스토리지(localStorage)에만 저장되며, 이 정보는 외부로 전송되지 않습니다.",
        s1_p3="타자 속도 테스트는 예외입니다. 이용자가 결과를 공개 랭킹에 직접 제출할 경우, 입력한 닉네임과 WPM·정확도가 서버로 전송되어 저장되며 다른 방문자에게 공개됩니다. 이를 위해 이름, 이메일 등 별도의 신원 정보는 요구하거나 수집하지 않으며, 이용자가 직접 입력한 닉네임만 저장됩니다. IP 주소는 스팸성 반복 제출을 막기 위한 간단한 빈도 제한 목적으로만 해시(hash) 처리되어 순간적으로 사용되며, 이용자를 특정할 수 있는 형태로 저장되지 않습니다. 결과를 제출하지 않으면 테스트와 관련된 어떤 정보도 서버로 전송되지 않습니다.",
        s2_h2="2. 쿠키(Cookie) 및 유사 기술의 사용",
        s2_p1="사이트는 서비스 이용 분석 및 광고 제공을 위해 쿠키를 사용할 수 있습니다. 쿠키는 웹사이트가 이용자의 브라우저에 저장하는 소량의 정보로, 이용자는 브라우저 설정을 통해 쿠키 저장을 거부하거나 삭제할 수 있습니다. 다만 쿠키 저장을 거부할 경우 일부 기능 이용에 어려움이 있을 수 있습니다.",
        s2_p2="EEA(유럽경제지역)·영국·스위스에서 접속하신 것으로 추정되는 경우, 최초 방문 시 동의 배너가 표시되어 필수 외(광고·분석) 쿠키에 대한 동의 여부를 선택하실 수 있습니다. 선택하신 내용은 브라우저에 저장되며, 화면 하단 \"쿠키 설정\" 링크를 통해 언제든 다시 변경할 수 있습니다.",
        s3_h2="3. 광고 서비스(Google AdSense) 이용에 관한 사항",
        s3_p1="사이트는 서비스 운영 및 유지를 위해 Google을 포함한 제3자 광고 사업자의 광고를 게재할 수 있습니다.",
        s3_li1="Google과 같은 제3자 공급업체는 쿠키를 사용하여 이용자의 이전 사이트 방문 기록을 기반으로 광고를 게재할 수 있습니다.",
        s3_li2="Google의 광고 쿠키 사용을 통해 Google과 파트너사는 이용자가 본 사이트 및/또는 인터넷상의 다른 사이트를 방문한 기록을 바탕으로 광고를 게재할 수 있습니다.",
        s3_li3='이용자는 <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">Google 광고 설정 페이지</a>를 방문하여 맞춤 광고를 비활성화할 수 있습니다. (또는 <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a>에서 맞춤형 광고에 사용되는 제3자 공급업체의 쿠키를 비활성화할 수 있습니다.)',
        s3_p2="광고 서비스가 실제로 적용되는 시점과 범위는 사이트 운영 상황에 따라 달라질 수 있으며, 변경 시 본 방침을 통해 안내합니다.",
        s4_h2="4. 개인정보의 제3자 제공",
        s4_p1="사이트는 이용자의 개인정보를 원칙적으로 외부에 제공하지 않습니다. 다만 법령에 근거가 있거나 수사기관이 적법한 절차에 따라 요구하는 경우는 예외로 합니다.",
        s5_h2="5. 이용자의 권리",
        s5_p1="이용자는 언제든지 브라우저 설정을 통해 쿠키 및 로컬 스토리지 데이터를 삭제할 수 있으며, 개인정보 처리와 관련한 문의 사항은 아래 연락처로 문의할 수 있습니다.",
        s6_h2="6. 문의처", s6_p1="개인정보 처리에 관한 문의는 아래 이메일로 연락해 주시기 바랍니다.",
        s7_h2="7. 방침의 변경",
        s7_p1="본 개인정보처리방침은 법령, 정책 또는 서비스 변경에 따라 개정될 수 있으며, 변경 시 사이트를 통해 공지합니다.",
    ),
    "ja": dict(
        title="プライバシーポリシー | Formix",
        description="Formixのプライバシーポリシーです。収集する情報、Cookie・ローカルストレージの利用、広告(Google AdSense)に関するデータの取り扱いについてご案内します。",
        og_title="プライバシーポリシー | Formix",
        og_description="Formixの個人情報の収集・利用およびCookieの使用に関するご案内です。",
        h1="プライバシーポリシー", effective="施行日: 2026年9月20日",
        intro='Formix(以下「本サイト」)は、利用者のプライバシーを重視し、関連法令の遵守に努めます。本ポリシーでは、本サイトがどのような情報をどのように収集・利用するかを説明します。',
        s1_h2="1. 処理する情報と処理方法",
        s1_p1="本サイトが提供するJSONフォーマッターなどのツールは、入力されたテキストをサーバーに送信せず、利用者のブラウザ(JavaScript)内でのみ処理します。つまり、入力されたJSONデータやテキストがサイト運営者に送信・保存されることはありません。",
        s1_p2="画面テーマ設定(ライト/ダークモード)などの単純な環境設定値のみ、利用者のブラウザのローカルストレージ(localStorage)に保存され、この情報が外部に送信されることはありません。",
        s1_p3="タイピング速度テストは例外です。利用者が結果を公開ランキングに送信することを選択した場合、入力したニックネームとWPM・正確率がサーバーに送信・保存され、他の訪問者に公開されます。これに際して氏名やメールアドレスなどの身元情報を要求・収集することはなく、利用者が入力したニックネームのみが保存されます。IPアドレスはスパム的な連続送信を防ぐための簡易的な頻度制限の目的でのみハッシュ化された状態で一時的に使用され、利用者個人を特定できる形では保存されません。結果を送信しない場合、テストに関する情報は一切サーバーに送信されません。",
        s2_h2="2. Cookie(クッキー)および類似技術の使用",
        s2_p1="本サイトはサービス利用分析および広告配信のためにCookieを使用する場合があります。Cookieとはウェブサイトが利用者のブラウザに保存する少量の情報で、利用者はブラウザの設定でCookieの保存を拒否または削除できます。ただし、Cookieの保存を拒否した場合、一部機能のご利用に支障が生じる可能性があります。",
        s2_p2="EEA(欧州経済領域)・英国・スイスからアクセスされたと推定される場合、初回訪問時に同意バナーが表示され、必須以外(広告・分析)のCookieについて同意するかどうかを選択できます。選択内容はブラウザに保存され、画面下部の「Cookie設定」リンクからいつでも変更できます。",
        s3_h2="3. 広告サービス(Google AdSense)の利用について",
        s3_p1="本サイトはサービスの運営・維持のため、Googleを含む第三者広告事業者の広告を掲載する場合があります。",
        s3_li1="Googleなどの第三者ベンダーはCookieを使用し、利用者の本サイトまたは他のサイトへの過去のアクセス情報に基づいて広告を配信することがあります。",
        s3_li2="GoogleはCookieを使用することにより、Googleおよびそのパートナーが本サイトおよび/またはインターネット上の他のサイトへの利用者のアクセス情報に基づいて広告を配信できるようにします。",
        s3_li3='利用者は<a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">Google広告設定ページ</a>にアクセスすることでパーソナライズ広告を無効にできます。(または<a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a>でパーソナライズ広告に使用される第三者ベンダーのCookieを無効にできます。)',
        s3_p2="広告サービスが実際に適用される時期や範囲は、サイトの運営状況により変動する場合があり、変更時は本ポリシーを通じてご案内します。",
        s4_h2="4. 個人情報の第三者提供",
        s4_p1="本サイトは原則として利用者の個人情報を外部に提供しません。ただし、法令に根拠がある場合や捐査機関が適法な手続きに従って要求する場合はこの限りではありません。",
        s5_h2="5. 利用者の権利",
        s5_p1="利用者はいつでもブラウザの設定を通じてCookieおよびローカルストレージのデータを削除でき、個人情報の取り扱いに関するお問い合わせは下記の連絡先までご連絡ください。",
        s6_h2="6. お問い合わせ先", s6_p1="個人情報の取り扱いに関するお問い合わせは、下記のメールアドレスまでご連絡ください。",
        s7_h2="7. ポリシーの変更",
        s7_p1="本プライバシーポリシーは、法令、方針またはサービスの変更に伴い改定されることがあり、変更時は本サイトを通じて告知します。",
    ),
    "zh": dict(
        title="隐私政策 | Formix",
        description="Formix的隐私政策，说明我们收集的信息、Cookie 与本地存储的使用方式，以及与广告服务(Google AdSense)相关的数据处理方式。",
        og_title="隐私政策 | Formix",
        og_description="关于Formix收集与使用个人信息及使用 Cookie 的说明。",
        h1="隐私政策", effective="生效日期：2026年9月20日",
        intro='Formix(以下简称"本网站")重视用户隐私，并致力于遵守相关法律法规。本政策说明本网站收集哪些信息以及如何使用这些信息。',
        s1_h2="1. 处理的信息及处理方式",
        s1_p1="本网站提供的 JSON 格式化等工具，会将您输入的文本完全在您的浏览器(JavaScript)中处理，不会发送到服务器。也就是说，您输入的 JSON 数据或文本不会被传送给网站运营者或被保存。",
        s1_p2="仅主题设置(浅色/深色模式)等简单的偏好设置值会保存在您浏览器的本地存储(localStorage)中，该信息不会对外传输。",
        s1_p3="打字速度测试是一个例外。如果您选择将成绩提交到公开排行榜，您输入的昵称以及 WPM、准确率会被发送并保存到服务器，并展示给其他访问者。为此我们不会要求或收集您的姓名、邮箱等身份信息，仅保存您自行输入的昵称。IP 地址仅用于防止垃圾刷分的简单频率限制，会以哈希(hash)形式短暂使用，不会以可识别您身份的形式保存。如果您不提交成绩，测试相关的任何信息都不会发送到服务器。",
        s2_h2="2. Cookie 及类似技术的使用",
        s2_p1="本网站可能会为服务分析和广告投放使用 Cookie。Cookie 是网站保存在您浏览器中的少量信息，您可以通过浏览器设置拒绝或删除 Cookie。但拒绝 Cookie 可能会影响部分功能的使用。",
        s2_p2="如果系统判断您是从 EEA(欧洲经济区)、英国或瑞士访问本站，首次访问时会显示同意横幅，供您选择是否同意使用非必要(广告/分析)Cookie。您的选择会保存在浏览器中，您可以随时通过页面底部的“Cookie 设置”链接重新更改。",
        s3_h2="3. 关于广告服务(Google AdSense)使用的说明",
        s3_p1="为维持网站运营，本网站可能会展示包括 Google 在内的第三方广告商投放的广告。",
        s3_li1="包括 Google 在内的第三方供应商可能会使用 Cookie，根据用户过去访问本网站或其他网站的记录投放广告。",
        s3_li2="通过 Google 广告 Cookie 的使用，Google 及其合作伙伴可以根据用户访问本网站和/或互联网上其他网站的记录投放广告。",
        s3_li3='用户可以访问 <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">Google 广告设置页面</a> 停用个性化广告。(或在 <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a> 停用用于个性化广告的第三方供应商 Cookie。)',
        s3_p2="广告服务的实际应用时间和范围可能会根据网站运营情况而变化，如有变更将通过本政策告知。",
        s4_h2="4. 个人信息向第三方的提供",
        s4_p1="本网站原则上不会将用户的个人信息提供给外部，但法律另有规定或侦查机关依据合法程序要求提供的情况除外。",
        s5_h2="5. 用户权利",
        s5_p1="用户可以随时通过浏览器设置删除 Cookie 及本地存储数据，如对个人信息处理有任何疑问，可通过下方联系方式咨询。",
        s6_h2="6. 联系方式", s6_p1="如对个人信息处理有任何疑问，请通过以下邮箱联系我们。",
        s7_h2="7. 政策的变更",
        s7_p1="本隐私政策可能会因法律、政策或服务变更而修订，变更时将通过本网站公告。",
    ),
    "es": dict(
        title="Política de privacidad | Formix",
        description="Política de privacidad de Formix. Explica qué información recopilamos, nuestro uso de cookies/almacenamiento local, y cómo se manejan los datos en relación con la publicidad (Google AdSense).",
        og_title="Política de privacidad | Formix",
        og_description="Información sobre la recopilación y uso de datos personales por parte de Formix y nuestro uso de cookies.",
        h1="Política de privacidad", effective="Fecha de vigencia: 20 de septiembre de 2026",
        intro='Formix (el "Sitio") valora la privacidad de sus usuarios y se esfuerza por cumplir con las leyes de protección de datos aplicables. Esta política explica qué información recopila el Sitio y cómo se usa.',
        s1_h2="1. Información procesada y cómo",
        s1_p1="Las herramientas que ofrece el Sitio, como el Formateador JSON, procesan el texto que ingresas completamente dentro de tu navegador (JavaScript) y nunca lo envían a un servidor. En otras palabras, los datos JSON o el texto que ingresas nunca se transmiten ni se almacenan por el operador del Sitio.",
        s1_p2="Configuraciones simples de preferencia, como tu elección de tema (modo claro/oscuro), se almacenan solo en el almacenamiento local de tu navegador (localStorage) y nunca se transmiten externamente.",
        s1_p3='La Prueba de velocidad de escritura es una excepción: si decides enviar tu puntuación a la tabla de clasificación pública, el apodo que ingreses junto con tu PPM y precisión se envían y almacenan en nuestro servidor para poder mostrarlos a otros visitantes. No requerimos ni recopilamos tu nombre, correo electrónico ni ninguna otra información identificable para esto — solo el apodo que escribes. Tu dirección IP se usa solo momentáneamente, en forma de hash, para aplicar una limitación básica de frecuencia contra envíos de spam, y no se almacena en una forma que te identifique. Si no envías una puntuación, nada sobre la prueba se envía a ningún lugar.',
        s2_h2="2. Uso de cookies y tecnologías similares",
        s2_p1="El Sitio puede usar cookies para análisis del servicio y fines publicitarios. Una cookie es un pequeño fragmento de información que un sitio web almacena en tu navegador; puedes rechazar o eliminar cookies a través de la configuración de tu navegador. Ten en cuenta que rechazar cookies puede limitar algunas funciones.",
        s2_p2='Si pareces estar visitando desde el EEE, el Reino Unido o Suiza, se muestra un banner de consentimiento en tu primera visita para que puedas aceptar o rechazar cookies no esenciales (publicidad/análisis). Tu elección se almacena en tu navegador y puedes cambiarla en cualquier momento usando el enlace "Preferencias de cookies" en el pie de página.',
        s3_h2="3. Uso de servicios de publicidad (Google AdSense)",
        s3_p1="Para ayudar a operar y mantener el Sitio, podemos mostrar anuncios de proveedores externos, incluido Google.",
        s3_li1="Proveedores externos, incluido Google, pueden usar cookies para mostrar anuncios basados en las visitas previas del usuario a este u otros sitios web.",
        s3_li2="El uso de cookies publicitarias de Google permite a Google y sus socios mostrar anuncios basados en las visitas del usuario a este Sitio y/u otros sitios en Internet.",
        s3_li3='Los usuarios pueden desactivar la publicidad personalizada visitando <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">la Configuración de anuncios de Google</a>, o desactivar las cookies de proveedores externos usadas para publicidad personalizada visitando <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a>.',
        s3_p2="El momento y el alcance con que se implemente realmente la publicidad puede variar según cómo se opere el Sitio, y cualquier cambio se anunciará a través de esta política.",
        s4_h2="4. Divulgación de información personal a terceros",
        s4_p1="El Sitio, en principio, no comparte la información personal de los usuarios con terceros, excepto cuando lo exija la ley o lo solicite una autoridad investigadora mediante un procedimiento legal.",
        s5_h2="5. Derechos del usuario",
        s5_p1="Los usuarios pueden eliminar cookies y datos de almacenamiento local en cualquier momento a través de la configuración de su navegador, y pueden dirigir cualquier pregunta sobre el manejo de datos al contacto que figura a continuación.",
        s6_h2="6. Contacto", s6_p1="Para preguntas sobre cómo se manejan los datos personales, contáctanos a la dirección de correo electrónico de abajo.",
        s7_h2="7. Cambios a esta política",
        s7_p1="Esta Política de privacidad puede revisarse en respuesta a cambios en la ley, la política o los servicios del Sitio, y cualquier cambio se anunciará a través del Sitio.",
    ),
    "vi": dict(
        title="Chính sách bảo mật | Formix",
        description="Chính sách bảo mật của Formix. Giải thích thông tin chúng tôi thu thập, việc sử dụng cookie/lưu trữ cục bộ, và cách xử lý dữ liệu liên quan đến quảng cáo (Google AdSense).",
        og_title="Chính sách bảo mật | Formix",
        og_description="Thông tin về việc thu thập và sử dụng dữ liệu cá nhân của Formix và việc sử dụng cookie của chúng tôi.",
        h1="Chính sách bảo mật", effective="Ngày hiệu lực: 20 tháng 9 năm 2026",
        intro='Formix (gọi tắt là "Trang web") coi trọng quyền riêng tư của người dùng và cố gắng tuân thủ các luật bảo vệ dữ liệu áp dụng. Chính sách này giải thích Trang web thu thập thông tin gì và sử dụng thông tin đó như thế nào.',
        s1_h2="1. Thông tin được xử lý và cách xử lý",
        s1_p1="Các công cụ trên Trang web, như Công cụ định dạng JSON, xử lý văn bản bạn nhập hoàn toàn trong trình duyệt của bạn (JavaScript) và không bao giờ gửi lên máy chủ. Nói cách khác, dữ liệu JSON hoặc văn bản bạn nhập không bao giờ được truyền đến hoặc lưu trữ bởi nhà vận hành Trang web.",
        s1_p2="Các thiết lập tùy chọn đơn giản, như lựa chọn giao diện (sáng/tối), chỉ được lưu trong bộ nhớ cục bộ của trình duyệt (localStorage) và không bao giờ được truyền ra ngoài.",
        s1_p3='Kiểm tra tốc độ đánh máy là một ngoại lệ: nếu bạn chọn gửi điểm số của mình lên bảng xếp hạng công khai, biệt danh bạn nhập cùng với WPM và độ chính xác sẽ được gửi và lưu trên máy chủ của chúng tôi để hiển thị cho những người truy cập khác. Chúng tôi không yêu cầu hoặc thu thập tên, email hay bất kỳ thông tin nhận dạng nào khác cho việc này — chỉ biệt danh bạn nhập. Địa chỉ IP của bạn chỉ được sử dụng tạm thời, dưới dạng mã hóa băm (hash), để áp dụng giới hạn tần suất cơ bản chống gửi spam, và không được lưu dưới dạng có thể nhận dạng bạn. Nếu bạn không gửi điểm số, không có thông tin nào về bài kiểm tra được gửi đi bất cứ đâu.',
        s2_h2="2. Việc sử dụng cookie và công nghệ tương tự",
        s2_p1="Trang web có thể sử dụng cookie cho mục đích phân tích dịch vụ và quảng cáo. Cookie là một đoạn thông tin nhỏ mà trang web lưu trong trình duyệt của bạn; bạn có thể từ chối hoặc xóa cookie qua cài đặt trình duyệt. Lưu ý rằng việc từ chối cookie có thể hạn chế một số tính năng.",
        s2_p2='Nếu bạn có vẻ đang truy cập từ EEA, Vương quốc Anh hoặc Thụy Sĩ, một banner xin đồng ý sẽ hiển thị trong lần truy cập đầu tiên để bạn có thể chấp nhận hoặc từ chối cookie không thiết yếu (quảng cáo/phân tích). Lựa chọn của bạn được lưu trong trình duyệt và bạn có thể thay đổi bất cứ lúc nào bằng liên kết "Tùy chọn cookie" ở chân trang.',
        s3_h2="3. Việc sử dụng dịch vụ quảng cáo (Google AdSense)",
        s3_p1="Để giúp vận hành và duy trì Trang web, chúng tôi có thể hiển thị quảng cáo từ các nhà cung cấp bên thứ ba, bao gồm Google.",
        s3_li1="Các nhà cung cấp bên thứ ba, bao gồm Google, có thể sử dụng cookie để hiển thị quảng cáo dựa trên lịch sử truy cập trước đó của người dùng vào trang web này hoặc các trang web khác.",
        s3_li2="Việc Google sử dụng cookie quảng cáo cho phép Google và các đối tác hiển thị quảng cáo dựa trên lịch sử truy cập của người dùng vào Trang web này và/hoặc các trang web khác trên Internet.",
        s3_li3='Người dùng có thể từ chối quảng cáo được cá nhân hóa bằng cách truy cập <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">Cài đặt quảng cáo của Google</a>, hoặc từ chối cookie của nhà cung cấp bên thứ ba dùng cho quảng cáo cá nhân hóa bằng cách truy cập <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a>.',
        s3_p2="Thời điểm và mức độ thực tế triển khai quảng cáo có thể thay đổi tùy theo cách Trang web được vận hành, và bất kỳ thay đổi nào sẽ được thông báo qua chính sách này.",
        s4_h2="4. Tiết lộ thông tin cá nhân cho bên thứ ba",
        s4_p1="Về nguyên tắc, Trang web không chia sẻ thông tin cá nhân của người dùng với bên ngoài, trừ khi pháp luật yêu cầu hoặc cơ quan điều tra yêu cầu thông qua thủ tục hợp pháp.",
        s5_h2="5. Quyền của người dùng",
        s5_p1="Người dùng có thể xóa cookie và dữ liệu lưu trữ cục bộ bất cứ lúc nào qua cài đặt trình duyệt, và có thể gửi bất kỳ câu hỏi nào về việc xử lý dữ liệu đến địa chỉ liên hệ bên dưới.",
        s6_h2="6. Liên hệ", s6_p1="Nếu có câu hỏi về cách xử lý dữ liệu cá nhân, vui lòng liên hệ với chúng tôi qua địa chỉ email bên dưới.",
        s7_h2="7. Thay đổi đối với chính sách này",
        s7_p1="Chính sách bảo mật này có thể được chỉnh sửa để phản ánh các thay đổi về luật pháp, chính sách hoặc dịch vụ của Trang web, và mọi thay đổi sẽ được thông báo qua Trang web.",
    ),
    "pt": dict(
        title="Política de privacidade | Formix",
        description="Política de privacidade do Formix. Explica quais informações coletamos, o uso de cookies/armazenamento local e como os dados são tratados em relação à publicidade (Google AdSense).",
        og_title="Política de privacidade | Formix",
        og_description="Informações sobre a coleta e uso de dados pessoais pelo Formix e nosso uso de cookies.",
        h1="Política de privacidade", effective="Data de vigência: 20 de setembro de 2026",
        intro='O Formix (o "Site") valoriza a privacidade de seus usuários e se esforça para cumprir as leis de proteção de dados aplicáveis. Esta política explica quais informações o Site coleta e como são usadas.',
        s1_h2="1. Informações processadas e como",
        s1_p1="As ferramentas oferecidas pelo Site, como o Formatador JSON, processam o texto que você insere inteiramente dentro do seu navegador (JavaScript) e nunca o enviam a um servidor. Em outras palavras, os dados JSON ou o texto que você insere nunca são transmitidos ou armazenados pelo operador do Site.",
        s1_p2="Configurações simples de preferência, como sua escolha de tema (modo claro/escuro), são armazenadas apenas no armazenamento local do seu navegador (localStorage) e nunca são transmitidas externamente.",
        s1_p3='O Teste de velocidade de digitação é uma exceção: se você optar por enviar sua pontuação ao ranking público, o apelido que você digitar junto com seu PPM e precisão são enviados e armazenados em nosso servidor para serem exibidos a outros visitantes. Não exigimos nem coletamos seu nome, e-mail ou qualquer outra informação de identificação para isso — apenas o apelido que você digita. Seu endereço IP é usado apenas momentaneamente, em forma de hash, para aplicar uma limitação básica de frequência contra envios de spam, e não é armazenado de forma que o identifique. Se você não enviar uma pontuação, nada sobre o teste é enviado a lugar algum.',
        s2_h2="2. Uso de cookies e tecnologias semelhantes",
        s2_p1="O Site pode usar cookies para análise do serviço e fins publicitários. Um cookie é uma pequena informação que um site armazena no seu navegador; você pode recusar ou excluir cookies nas configurações do seu navegador. Observe que recusar cookies pode limitar algumas funcionalidades.",
        s2_p2='Se você parecer estar visitando do EEE, Reino Unido ou Suíça, um banner de consentimento é exibido na sua primeira visita para que você possa aceitar ou rejeitar cookies não essenciais (publicidade/análise). Sua escolha é armazenada no seu navegador e você pode alterá-la a qualquer momento usando o link "Preferências de cookies" no rodapé.',
        s3_h2="3. Uso de serviços de publicidade (Google AdSense)",
        s3_p1="Para ajudar a operar e manter o Site, podemos exibir anúncios de fornecedores terceirizados, incluindo o Google.",
        s3_li1="Fornecedores terceirizados, incluindo o Google, podem usar cookies para exibir anúncios com base em visitas anteriores do usuário a este ou a outros sites.",
        s3_li2="O uso de cookies de publicidade do Google permite que o Google e seus parceiros exibam anúncios com base nas visitas do usuário a este Site e/ou a outros sites na Internet.",
        s3_li3='Os usuários podem optar por não receber publicidade personalizada visitando as <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">Configurações de anúncios do Google</a>, ou optar por não receber cookies de fornecedores terceirizados usados para publicidade personalizada visitando <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a>.',
        s3_p2="O momento e a extensão em que a publicidade é efetivamente implementada podem variar conforme a operação do Site, e quaisquer alterações serão anunciadas por meio desta política.",
        s4_h2="4. Divulgação de informações pessoais a terceiros",
        s4_p1="Em princípio, o Site não compartilha informações pessoais dos usuários com terceiros, exceto quando exigido por lei ou solicitado por autoridade investigativa mediante procedimento legal.",
        s5_h2="5. Direitos do usuário",
        s5_p1="Os usuários podem excluir cookies e dados de armazenamento local a qualquer momento por meio das configurações do navegador, e podem direcionar quaisquer dúvidas sobre o tratamento de dados ao contato abaixo.",
        s6_h2="6. Contato", s6_p1="Para dúvidas sobre como os dados pessoais são tratados, contate-nos pelo e-mail abaixo.",
        s7_h2="7. Alterações a esta política",
        s7_p1="Esta Política de privacidade pode ser revisada em resposta a mudanças na lei, política ou serviços do Site, e quaisquer alterações serão anunciadas através do Site.",
    ),
    "id": dict(
        title="Kebijakan Privasi | Formix",
        description="Kebijakan privasi Formix. Menjelaskan informasi apa yang kami kumpulkan, penggunaan cookie/penyimpanan lokal kami, dan bagaimana data ditangani terkait iklan (Google AdSense).",
        og_title="Kebijakan Privasi | Formix",
        og_description="Informasi tentang pengumpulan dan penggunaan data pribadi oleh Formix serta penggunaan cookie kami.",
        h1="Kebijakan Privasi", effective="Tanggal berlaku: 20 September 2026",
        intro='Formix ("Situs") menghargai privasi penggunanya dan berupaya mematuhi hukum perlindungan data yang berlaku. Kebijakan ini menjelaskan informasi apa yang dikumpulkan Situs dan bagaimana digunakan.',
        s1_h2="1. Informasi yang diproses dan caranya",
        s1_p1="Alat yang disediakan di Situs, seperti Pemformat JSON, memproses teks yang Anda masukkan sepenuhnya di dalam browser Anda (JavaScript) dan tidak pernah mengirimkannya ke server. Dengan kata lain, data JSON atau teks yang Anda masukkan tidak pernah ditransmisikan ke atau disimpan oleh operator Situs.",
        s1_p2="Pengaturan preferensi sederhana, seperti pilihan tema (mode terang/gelap), hanya disimpan di penyimpanan lokal browser Anda (localStorage) dan tidak pernah ditransmisikan ke luar.",
        s1_p3='Tes Kecepatan Mengetik adalah pengecualian: jika Anda memilih untuk mengirimkan skor Anda ke papan peringkat publik, nama panggilan yang Anda masukkan beserta WPM dan akurasi Anda akan dikirim dan disimpan di server kami agar dapat ditampilkan kepada pengunjung lain. Kami tidak mewajibkan atau mengumpulkan nama, email, atau informasi identitas lain untuk ini — hanya nama panggilan yang Anda ketik. Alamat IP Anda hanya digunakan sesaat, dalam bentuk hash, untuk menerapkan pembatasan frekuensi dasar terhadap pengiriman spam, dan tidak disimpan dalam bentuk yang mengidentifikasi Anda. Jika Anda tidak mengirimkan skor, tidak ada informasi tentang tes yang dikirim ke mana pun.',
        s2_h2="2. Penggunaan cookie dan teknologi serupa",
        s2_p1="Situs dapat menggunakan cookie untuk analitik layanan dan tujuan periklanan. Cookie adalah sebagian kecil informasi yang disimpan situs web di browser Anda; Anda dapat menolak atau menghapus cookie melalui pengaturan browser Anda. Perhatikan bahwa menolak cookie dapat membatasi beberapa fitur.",
        s2_p2='Jika Anda tampaknya mengunjungi dari EEA, Inggris, atau Swiss, spanduk persetujuan ditampilkan pada kunjungan pertama Anda agar Anda dapat menerima atau menolak cookie non-esensial (periklanan/analitik). Pilihan Anda disimpan di browser Anda dan Anda dapat mengubahnya kapan saja menggunakan tautan "Preferensi cookie" di footer.',
        s3_h2="3. Penggunaan layanan periklanan (Google AdSense)",
        s3_p1="Untuk membantu mengoperasikan dan memelihara Situs, kami dapat menampilkan iklan dari penyedia pihak ketiga, termasuk Google.",
        s3_li1="Vendor pihak ketiga, termasuk Google, dapat menggunakan cookie untuk menayangkan iklan berdasarkan kunjungan sebelumnya pengguna ke situs ini atau situs web lain.",
        s3_li2="Penggunaan cookie periklanan Google memungkinkan Google dan mitranya menayangkan iklan berdasarkan kunjungan pengguna ke Situs ini dan/atau situs lain di Internet.",
        s3_li3='Pengguna dapat memilih keluar dari iklan yang dipersonalisasi dengan mengunjungi <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">Setelan Iklan Google</a>, atau memilih keluar dari cookie vendor pihak ketiga yang digunakan untuk iklan yang dipersonalisasi dengan mengunjungi <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a>.',
        s3_p2="Waktu dan sejauh mana periklanan benar-benar diterapkan dapat bervariasi tergantung pada cara Situs dioperasikan, dan setiap perubahan akan diumumkan melalui kebijakan ini.",
        s4_h2="4. Pengungkapan informasi pribadi kepada pihak ketiga",
        s4_p1="Situs pada prinsipnya tidak membagikan informasi pribadi pengguna kepada pihak luar, kecuali jika diwajibkan oleh hukum atau diminta oleh otoritas investigasi melalui prosedur hukum.",
        s5_h2="5. Hak pengguna",
        s5_p1="Pengguna dapat menghapus cookie dan data penyimpanan lokal kapan saja melalui pengaturan browser mereka, dan dapat mengarahkan pertanyaan apa pun tentang penanganan data ke kontak di bawah ini.",
        s6_h2="6. Kontak", s6_p1="Untuk pertanyaan tentang bagaimana data pribadi ditangani, silakan hubungi kami di alamat email di bawah ini.",
        s7_h2="7. Perubahan pada kebijakan ini",
        s7_p1="Kebijakan Privasi ini dapat direvisi sebagai tanggapan atas perubahan hukum, kebijakan, atau layanan Situs, dan setiap perubahan akan diumumkan melalui Situs.",
    ),
    "de": dict(
        title="Datenschutzerklärung | Formix",
        description="Formix' Datenschutzerklärung. Erläutert, welche Informationen wir sammeln, unsere Nutzung von Cookies/lokalem Speicher und wie Daten im Zusammenhang mit Werbung (Google AdSense) behandelt werden.",
        og_title="Datenschutzerklärung | Formix",
        og_description="Informationen zur Erhebung und Nutzung personenbezogener Daten durch Formix und zur Nutzung von Cookies.",
        h1="Datenschutzerklärung", effective="Datum des Inkrafttretens: 20. September 2026",
        intro='Formix (die „Website") legt Wert auf die Privatsphäre ihrer Nutzer und bemüht sich, geltende Datenschutzgesetze einzuhalten. Diese Richtlinie erläutert, welche Informationen die Website sammelt und wie sie verwendet werden.',
        s1_h2="1. Verarbeitete Informationen und wie",
        s1_p1="Die auf der Website angebotenen Tools, wie der JSON-Formatierer, verarbeiten den von Ihnen eingegebenen Text vollständig innerhalb Ihres Browsers (JavaScript) und senden ihn nie an einen Server. Mit anderen Worten, die von Ihnen eingegebenen JSON-Daten oder Texte werden niemals an den Betreiber der Website übermittelt oder von ihm gespeichert.",
        s1_p2="Einfache Einstellungen wie Ihre Themenwahl (Hell-/Dunkelmodus) werden nur im lokalen Speicher Ihres Browsers (localStorage) gespeichert und niemals extern übertragen.",
        s1_p3='Der Schreibgeschwindigkeitstest ist eine Ausnahme: Wenn Sie sich entscheiden, Ihr Ergebnis an die öffentliche Rangliste zu senden, werden der von Ihnen eingegebene Spitzname zusammen mit Ihrem WPM-Wert und Ihrer Genauigkeit an unseren Server gesendet und dort gespeichert, damit sie anderen Besuchern angezeigt werden können. Wir verlangen oder erfassen dafür weder Ihren Namen, Ihre E-Mail-Adresse noch andere identifizierende Informationen — nur den von Ihnen eingegebenen Spitznamen. Ihre IP-Adresse wird nur kurzzeitig in gehashter Form verwendet, um eine grundlegende Ratenbegrenzung gegen Spam-Einsendungen anzuwenden, und wird nicht in einer Form gespeichert, die Sie identifiziert. Wenn Sie kein Ergebnis einsenden, wird nichts zum Test irgendwohin gesendet.',
        s2_h2="2. Verwendung von Cookies und ähnlichen Technologien",
        s2_p1="Die Website kann Cookies für Dienstanalysen und Werbezwecke verwenden. Ein Cookie ist eine kleine Information, die eine Website in Ihrem Browser speichert; Sie können Cookies über Ihre Browsereinstellungen ablehnen oder löschen. Beachten Sie, dass das Ablehnen von Cookies einige Funktionen einschränken kann.",
        s2_p2='Wenn Sie offenbar aus dem EWR, dem Vereinigten Königreich oder der Schweiz zugreifen, wird bei Ihrem ersten Besuch ein Einwilligungsbanner angezeigt, damit Sie nicht notwendige (Werbe-/Analyse-)Cookies akzeptieren oder ablehnen können. Ihre Wahl wird in Ihrem Browser gespeichert, und Sie können sie jederzeit über den Link „Cookie-Einstellungen" in der Fußzeile ändern.',
        s3_h2="3. Nutzung von Werbediensten (Google AdSense)",
        s3_p1="Um den Betrieb und die Wartung der Website zu unterstützen, zeigen wir möglicherweise Anzeigen von Drittanbietern, einschließlich Google, an.",
        s3_li1="Drittanbieter, einschließlich Google, können Cookies verwenden, um Anzeigen basierend auf früheren Besuchen des Nutzers auf dieser oder anderen Websites auszuspielen.",
        s3_li2="Durch die Verwendung von Google-Werbe-Cookies können Google und seine Partner Anzeigen basierend auf den Besuchen des Nutzers auf dieser Website und/oder anderen Websites im Internet ausspielen.",
        s3_li3='Nutzer können personalisierte Werbung deaktivieren, indem sie die <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer">Google-Anzeigeneinstellungen</a> besuchen, oder Cookies von Drittanbietern für personalisierte Werbung deaktivieren, indem sie <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer">www.aboutads.info</a> besuchen.',
        s3_p2="Zeitpunkt und Umfang der tatsächlichen Umsetzung von Werbung können je nach Betrieb der Website variieren, und etwaige Änderungen werden über diese Richtlinie bekannt gegeben.",
        s4_h2="4. Weitergabe personenbezogener Daten an Dritte",
        s4_p1="Die Website gibt grundsätzlich keine personenbezogenen Daten der Nutzer an Dritte weiter, außer wenn dies gesetzlich vorgeschrieben ist oder von einer Ermittlungsbehörde im Rahmen eines rechtmäßigen Verfahrens verlangt wird.",
        s5_h2="5. Rechte der Nutzer",
        s5_p1="Nutzer können Cookies und lokale Speicherdaten jederzeit über ihre Browsereinstellungen löschen und sich bei Fragen zur Datenverarbeitung an den unten stehenden Kontakt wenden.",
        s6_h2="6. Kontakt", s6_p1="Bei Fragen zum Umgang mit personenbezogenen Daten kontaktieren Sie uns bitte unter der unten stehenden E-Mail-Adresse.",
        s7_h2="7. Änderungen dieser Richtlinie",
        s7_p1="Diese Datenschutzerklärung kann aufgrund von Änderungen der Gesetzgebung, der Richtlinien oder der Dienste der Website überarbeitet werden, und etwaige Änderungen werden über die Website bekannt gegeben.",
    ),
}

CONTENT["faq"] = {
    "en": dict(
        title="FAQ | Formix",
        description="Frequently asked questions about Formix — pricing, data handling, browser support, and how the JSON/XML Formatter tools work.",
        og_title="FAQ | Formix",
        og_description="Answers to common questions about Formix and its tools.",
        h1="Frequently Asked Questions",
        lead="Common questions about Formix, how it handles your data, and how the tools work.",
        items=[
            ("Is Formix free to use?", "Yes. All tools are completely free, and there is no sign-up or account required. We may show ads in the future to help cover hosting costs, but the tools themselves will remain free."),
            ("Is my data sent to a server?", 'No. Tools like the JSON Formatter and XML Formatter process everything locally in your browser using JavaScript. The text you paste in is never transmitted to or stored on our servers. See our <a href="{privacy}">Privacy Policy</a> for details.'),
            ("Do I need to create an account?", "No account or login is required for any tool. Just open the page and start using it."),
            ("Which browsers are supported?", "Any modern browser (Chrome, Edge, Firefox, Safari) on desktop or mobile works. The tools rely on standard, widely-supported JavaScript APIs like DOMParser and JSON.parse."),
            ("Can I use these tools on my phone?", "Yes, the site is fully responsive and works on mobile browsers, though a larger screen makes it easier to work with long JSON or XML documents."),
            ("What happens if my JSON or XML is invalid?", "The tool shows a status badge and an approximate line/column where the problem was found, so you can locate and fix the issue quickly. The JSON Formatter can also auto-correct some common mistakes, like missing quotes."),
            ("Will more tools be added?", 'Yes. Formix started with a JSON Formatter and now also offers an <a href="{tool_xml}">XML Formatter</a>, a <a href="{tool_converter}">JSON ↔ XML Converter</a>, a <a href="{tool_sql}">SQL Formatter</a>, a <a href="{tool_code}">Code Viewer</a>, and a <a href="{tool_number}">Number Reader</a>, plus two games — a <a href="{tool_typing}">Typing Speed Test</a> and a <a href="{game_syntax}">Coding Syntax Quiz</a>. We plan to keep adding small, genuinely useful browser-based tools and games over time — see our <a href="{about}">About</a> page for our guiding principles.'),
            ("How do I report a bug or suggest a feature?", 'Please reach out through our <a href="{contact}">Contact page</a>. We read every message.'),
        ],
    ),
    "ko": dict(
        title="자주 묻는 질문 | Formix",
        description="Formix 이용 요금, 데이터 처리 방식, 브라우저 지원, JSON/XML 포매터 사용법 등 자주 묻는 질문에 대한 답변입니다.",
        og_title="자주 묻는 질문 | Formix",
        og_description="Formix와 제공 도구에 대한 자주 묻는 질문과 답변입니다.",
        h1="자주 묻는 질문",
        lead="Formix 이용, 데이터 처리 방식, 도구 사용법에 대해 자주 묻는 질문들을 모았습니다.",
        items=[
            ("Formix는 무료인가요?", "네, 모든 도구는 완전히 무료이며 회원가입이나 계정 생성이 필요하지 않습니다. 운영비 충당을 위해 향후 광고를 게재할 수 있지만, 도구 자체는 계속 무료로 제공됩니다."),
            ("입력한 데이터가 서버로 전송되나요?", '아니요. JSON 포매터, XML 포매터 등의 도구는 모든 처리를 브라우저 안에서(자바스크립트로) 수행합니다. 입력한 텍스트는 서버로 전송되거나 저장되지 않습니다. 자세한 내용은 <a href="{privacy}">개인정보처리방침</a>을 참고해주세요.'),
            ("회원가입이 필요한가요?", "필요하지 않습니다. 어떤 도구든 계정이나 로그인 없이 바로 사용할 수 있습니다."),
            ("어떤 브라우저를 지원하나요?", "PC와 모바일의 최신 브라우저(Chrome, Edge, Firefox, Safari)에서 모두 사용할 수 있습니다. DOMParser, JSON.parse 등 널리 지원되는 표준 자바스크립트 API를 사용합니다."),
            ("모바일에서도 사용할 수 있나요?", "네, 모바일 브라우저에서도 반응형으로 정상 동작합니다. 다만 긴 JSON·XML 문서를 다룰 때는 화면이 큰 기기가 더 편리합니다."),
            ("JSON이나 XML이 유효하지 않으면 어떻게 되나요?", "상태 배지와 함께 문제가 발생한 대략적인 줄/열 위치를 알려줘 빠르게 확인하고 수정할 수 있습니다. JSON 포매터는 따옴표 누락 같은 흔한 실수를 자동으로 보정하기도 합니다."),
            ("앞으로 도구가 더 추가되나요?", '네. Formix는 JSON 포매터로 시작해 현재는 <a href="{tool_xml}">XML 포매터</a>, <a href="{tool_converter}">JSON ↔ XML 변환기</a>, <a href="{tool_sql}">SQL 포매터</a>, <a href="{tool_code}">코드 뷰어</a>, <a href="{tool_number}">숫자 읽기 변환기</a>를 제공하며, 게임으로는 <a href="{tool_typing}">타자 속도 테스트</a>와 <a href="{game_syntax}">코딩 문법 퀴즈</a>도 제공하고 있습니다. 앞으로도 실무에 유용한 브라우저 기반 도구와 게임을 계속 추가할 예정입니다. 운영 철학은 <a href="{about}">사이트 소개</a> 페이지를 참고해주세요.'),
            ("버그 제보나 기능 제안은 어떻게 하나요?", '<a href="{contact}">문의하기</a> 페이지를 통해 연락해주세요. 보내주시는 의견은 모두 확인하고 있습니다.'),
        ],
    ),
    "ja": dict(
        title="よくある質問 | Formix",
        description="Formixの料金、データの取り扱い、ブラウザ対応、JSON/XMLフォーマッターの使い方など、よくある質問への回答です。",
        og_title="よくある質問 | Formix",
        og_description="Formixと提供ツールに関するよくある質問への回答です。",
        h1="よくある質問",
        lead="Formixの利用方法、データの取り扱い、ツールの使い方に関するよくある質問をまとめました。",
        items=[
            ("Formixは無料ですか?", "はい、すべてのツールは完全に無料で、会員登録やアカウント作成は不要です。運営費を賄うため今後広告を掲載する場合がありますが、ツール自体は引き続き無料で提供します。"),
            ("入力したデータはサーバーに送信されますか?", 'いいえ。JSONフォーマッターやXMLフォーマッターなどのツールは、すべての処理をブラウザ内(JavaScript)で行います。入力したテキストがサーバーに送信・保存されることはありません。詳しくは<a href="{privacy}">プライバシーポリシー</a>をご覧ください。'),
            ("会員登録は必要ですか?", "不要です。どのツールもアカウントやログインなしですぐに利用できます。"),
            ("対応ブラウザは?", "パソコン・モバイルの最新ブラウザ(Chrome、Edge、Firefox、Safari)であれば問題なくご利用いただけます。DOMParserやJSON.parseなど、広くサポートされている標準のJavaScript APIを使用しています。"),
            ("スマートフォンでも使えますか?", "はい、モバイルブラウザでもレスポンシブに動作します。ただし長いJSON・XML文書を扱う場合は、画面の大きい端末の方が作業しやすくなります。"),
            ("JSONやXMLが無効な場合はどうなりますか?", "ステータスバッジとともに、問題が発生したおおよその行/列位置が表示されるため、すぐに確認・修正できます。JSONフォーマッターは引用符の欠落など、よくあるミスを自動修正することもあります。"),
            ("今後もツールは追加されますか?", 'はい。FormixはJSONフォーマッターから始まり、現在は<a href="{tool_xml}">XMLフォーマッター</a>、<a href="{tool_converter}">JSON ↔ XML 変換ツール</a>、<a href="{tool_sql}">SQLフォーマッター</a>、<a href="{tool_code}">コードビューア</a>、<a href="{tool_number}">数字の読み方変換</a>を提供し、ゲームとして<a href="{tool_typing}">タイピング速度テスト</a>と<a href="{game_syntax}">コーディング文法クイズ</a>も提供しています。今後も実務に役立つブラウザ完結型のツールやゲームを継続的に追加していく予定です。運営方針は<a href="{about}">サイト紹介</a>ページをご覧ください。'),
            ("不具合報告や機能提案はどうすればいいですか?", '<a href="{contact}">お問い合わせ</a>ページからご連絡ください。いただいたご意見はすべて確認しています。'),
        ],
    ),
    "zh": dict(
        title="常见问题 | Formix",
        description="关于Formix的费用、数据处理方式、浏览器支持，以及 JSON/XML 格式化工具使用方法等常见问题解答。",
        og_title="常见问题 | Formix",
        og_description="关于Formix及其提供工具的常见问题解答。",
        h1="常见问题",
        lead="汇总了关于Formix的使用、数据处理方式以及工具用法的常见问题。",
        items=[
            ("Formix是免费的吗?", "是的，所有工具完全免费，无需注册或创建账号。为了补贴运营成本，未来可能会展示广告，但工具本身将始终保持免费。"),
            ("我输入的数据会发送到服务器吗?", '不会。JSON 格式化、XML 格式化等工具的所有处理都在您的浏览器中(通过 JavaScript)完成。您输入的文本不会被发送到服务器或被保存。详情请参阅<a href="{privacy}">隐私政策</a>。'),
            ("需要注册账号吗?", "不需要。任何工具都无需账号或登录即可直接使用。"),
            ("支持哪些浏览器?", "电脑和手机上的主流最新浏览器(Chrome、Edge、Firefox、Safari)均可正常使用。工具使用的是 DOMParser、JSON.parse 等广泛支持的标准 JavaScript API。"),
            ("可以在手机上使用吗?", "可以，本站在移动浏览器上也能自适应正常显示。不过在处理较长的 JSON/XML 文档时，使用大屏幕设备会更方便。"),
            ("如果我的 JSON 或 XML 无效会怎样?", "工具会显示状态标记，并告知大致的错误行/列位置，方便您快速定位并修正问题。JSON 格式化工具还能自动修正部分常见错误，例如缺失的引号。"),
            ("以后会添加更多工具吗?", '会的。Formix从 JSON 格式化工具起步，目前也提供 <a href="{tool_xml}">XML 格式化工具</a>、<a href="{tool_converter}">JSON ↔ XML 转换工具</a>、<a href="{tool_sql}">SQL 格式化工具</a>、<a href="{tool_code}">代码查看器</a>和 <a href="{tool_number}">数字读法转换</a>，此外还有两款游戏 —— <a href="{tool_typing}">打字速度测试</a>和 <a href="{game_syntax}">编程语法测验</a>。我们会持续添加对实际工作有帮助的浏览器端工具和游戏，运营理念请参阅<a href="{about}">关于本站</a>页面。'),
            ("如何反馈错误或提出功能建议?", '请通过<a href="{contact}">联系我们</a>页面与我们联系，我们会查看每一条反馈。'),
        ],
    ),
    "es": dict(
        title="Preguntas frecuentes | Formix",
        description="Preguntas frecuentes sobre Formix — precios, manejo de datos, compatibilidad con navegadores y cómo funcionan las herramientas de formateo JSON/XML.",
        og_title="Preguntas frecuentes | Formix",
        og_description="Respuestas a preguntas comunes sobre Formix y sus herramientas.",
        h1="Preguntas frecuentes",
        lead="Preguntas comunes sobre Formix, cómo maneja tus datos y cómo funcionan las herramientas.",
        items=[
            ("¿Formix es gratis?", "Sí. Todas las herramientas son completamente gratuitas y no se requiere registro ni cuenta. Podríamos mostrar anuncios en el futuro para ayudar a cubrir los costos de hospedaje, pero las herramientas en sí seguirán siendo gratuitas."),
            ("¿Mis datos se envían a un servidor?", 'No. Herramientas como el Formateador JSON y el Formateador XML procesan todo localmente en tu navegador usando JavaScript. El texto que pegas nunca se transmite ni se almacena en nuestros servidores. Consulta nuestra <a href="{privacy}">Política de privacidad</a> para más detalles.'),
            ("¿Necesito crear una cuenta?", "No se necesita cuenta ni inicio de sesión para ninguna herramienta. Solo abre la página y empieza a usarla."),
            ("¿Qué navegadores son compatibles?", "Cualquier navegador moderno (Chrome, Edge, Firefox, Safari) en escritorio o móvil funciona. Las herramientas dependen de APIs de JavaScript estándar y ampliamente compatibles como DOMParser y JSON.parse."),
            ("¿Puedo usar estas herramientas en mi teléfono?", "Sí, el sitio es totalmente responsivo y funciona en navegadores móviles, aunque una pantalla más grande facilita trabajar con documentos JSON o XML largos."),
            ("¿Qué pasa si mi JSON o XML no es válido?", "La herramienta muestra una insignia de estado y una línea/columna aproximada donde se encontró el problema, para que puedas localizarlo y corregirlo rápidamente. El Formateador JSON también puede autocorregir algunos errores comunes, como comillas faltantes."),
            ("¿Se añadirán más herramientas?", 'Sí. Formix comenzó con un Formateador JSON y ahora también ofrece un <a href="{tool_xml}">Formateador XML</a>, un <a href="{tool_converter}">Convertidor JSON ↔ XML</a>, un <a href="{tool_sql}">Formateador SQL</a> y un <a href="{tool_code}">Visor de código</a>, además de dos juegos — una <a href="{tool_typing}">Prueba de velocidad de escritura</a> y un <a href="{game_syntax}">Quiz de sintaxis de código</a>. Planeamos seguir añadiendo pequeñas herramientas y juegos realmente útiles basados en el navegador — consulta nuestra página <a href="{about}">Acerca de</a> para conocer los principios que nos guían.'),
            ("¿Cómo reporto un error o sugiero una función?", 'Contáctanos a través de nuestra <a href="{contact}">página de Contacto</a>. Leemos cada mensaje.'),
        ],
    ),
    "vi": dict(
        title="Câu hỏi thường gặp | Formix",
        description="Các câu hỏi thường gặp về Formix — giá cả, xử lý dữ liệu, hỗ trợ trình duyệt, và cách hoạt động của các công cụ định dạng JSON/XML.",
        og_title="Câu hỏi thường gặp | Formix",
        og_description="Câu trả lời cho các câu hỏi thường gặp về Formix và các công cụ của nó.",
        h1="Câu hỏi thường gặp",
        lead="Những câu hỏi thường gặp về Formix, cách xử lý dữ liệu của bạn và cách các công cụ hoạt động.",
        items=[
            ("Formix có miễn phí không?", "Có. Tất cả công cụ hoàn toàn miễn phí và không cần đăng ký hay tài khoản. Chúng tôi có thể hiển thị quảng cáo trong tương lai để hỗ trợ chi phí vận hành, nhưng các công cụ sẽ luôn miễn phí."),
            ("Dữ liệu của tôi có được gửi lên máy chủ không?", 'Không. Các công cụ như Định dạng JSON và Định dạng XML xử lý mọi thứ cục bộ trong trình duyệt của bạn bằng JavaScript. Văn bản bạn dán vào không bao giờ được truyền đến hoặc lưu trên máy chủ của chúng tôi. Xem <a href="{privacy}">Chính sách bảo mật</a> để biết chi tiết.'),
            ("Tôi cần tạo tài khoản không?", "Không cần tài khoản hay đăng nhập cho bất kỳ công cụ nào. Chỉ cần mở trang và sử dụng ngay."),
            ("Trình duyệt nào được hỗ trợ?", "Bất kỳ trình duyệt hiện đại nào (Chrome, Edge, Firefox, Safari) trên máy tính hoặc di động đều hoạt động tốt. Các công cụ dựa trên các API JavaScript tiêu chuẩn, được hỗ trợ rộng rãi như DOMParser và JSON.parse."),
            ("Tôi có thể dùng các công cụ này trên điện thoại không?", "Có, trang web hoàn toàn responsive và hoạt động trên trình duyệt di động, tuy nhiên màn hình lớn hơn sẽ giúp làm việc với các tài liệu JSON hoặc XML dài dễ hơn."),
            ("Điều gì xảy ra nếu JSON hoặc XML của tôi không hợp lệ?", "Công cụ sẽ hiển thị huy hiệu trạng thái và vị trí dòng/cột gần đúng nơi phát hiện lỗi, giúp bạn nhanh chóng tìm và sửa vấn đề. Công cụ định dạng JSON cũng có thể tự động sửa một số lỗi thường gặp, như thiếu dấu ngoặc kép."),
            ("Có thêm công cụ mới không?", 'Có. Formix khởi đầu với Công cụ định dạng JSON và hiện cũng cung cấp <a href="{tool_xml}">Công cụ định dạng XML</a>, <a href="{tool_converter}">Chuyển đổi JSON ↔ XML</a>, <a href="{tool_sql}">Công cụ định dạng SQL</a> và <a href="{tool_code}">Xem mã nguồn</a>, cùng với hai trò chơi — <a href="{tool_typing}">Kiểm tra tốc độ đánh máy</a> và <a href="{game_syntax}">Đố vui cú pháp lập trình</a>. Chúng tôi có kế hoạch tiếp tục bổ sung các công cụ và trò chơi nhỏ, thực sự hữu ích dựa trên trình duyệt — xem trang <a href="{about}">Giới thiệu</a> để biết các nguyên tắc định hướng của chúng tôi.'),
            ("Làm sao để báo lỗi hoặc đề xuất tính năng?", 'Vui lòng liên hệ qua <a href="{contact}">trang Liên hệ</a> của chúng tôi. Chúng tôi đọc mọi tin nhắn.'),
        ],
    ),
    "pt": dict(
        title="Perguntas frequentes | Formix",
        description="Perguntas frequentes sobre o Formix — preços, tratamento de dados, suporte a navegadores e como funcionam as ferramentas de formatação JSON/XML.",
        og_title="Perguntas frequentes | Formix",
        og_description="Respostas para perguntas comuns sobre o Formix e suas ferramentas.",
        h1="Perguntas frequentes",
        lead="Perguntas comuns sobre o Formix, como ele trata seus dados e como as ferramentas funcionam.",
        items=[
            ("O Formix é gratuito?", "Sim. Todas as ferramentas são completamente gratuitas e não é necessário cadastro ou conta. Podemos exibir anúncios no futuro para ajudar a cobrir custos de hospedagem, mas as próprias ferramentas permanecerão gratuitas."),
            ("Meus dados são enviados a um servidor?", 'Não. Ferramentas como o Formatador JSON e o Formatador XML processam tudo localmente no seu navegador usando JavaScript. O texto que você cola nunca é transmitido ou armazenado em nossos servidores. Veja nossa <a href="{privacy}">Política de privacidade</a> para detalhes.'),
            ("Preciso criar uma conta?", "Nenhuma conta ou login é necessário para nenhuma ferramenta. Basta abrir a página e começar a usar."),
            ("Quais navegadores são compatíveis?", "Qualquer navegador moderno (Chrome, Edge, Firefox, Safari) em desktop ou celular funciona. As ferramentas dependem de APIs JavaScript padrão e amplamente suportadas, como DOMParser e JSON.parse."),
            ("Posso usar essas ferramentas no celular?", "Sim, o site é totalmente responsivo e funciona em navegadores móveis, embora uma tela maior facilite o trabalho com documentos JSON ou XML longos."),
            ("O que acontece se meu JSON ou XML for inválido?", "A ferramenta exibe um indicador de status e uma linha/coluna aproximada de onde o problema foi encontrado, para que você possa localizá-lo e corrigi-lo rapidamente. O Formatador JSON também pode corrigir automaticamente alguns erros comuns, como aspas faltantes."),
            ("Mais ferramentas serão adicionadas?", 'Sim. O Formix começou com um Formatador JSON e agora também oferece um <a href="{tool_xml}">Formatador XML</a>, um <a href="{tool_converter}">Conversor JSON ↔ XML</a>, um <a href="{tool_sql}">Formatador SQL</a> e um <a href="{tool_code}">Visualizador de código</a>, além de dois jogos — um <a href="{tool_typing}">Teste de velocidade de digitação</a> e um <a href="{game_syntax}">Quiz de sintaxe de código</a>. Planejamos continuar adicionando ferramentas e jogos pequenos e realmente úteis baseados no navegador — veja nossa página <a href="{about}">Sobre</a> para os princípios que nos guiam.'),
            ("Como relato um erro ou sugiro uma funcionalidade?", 'Entre em contato pela nossa <a href="{contact}">página de Contato</a>. Lemos todas as mensagens.'),
        ],
    ),
    "id": dict(
        title="Pertanyaan Umum | Formix",
        description="Pertanyaan umum tentang Formix — harga, penanganan data, dukungan browser, dan cara kerja alat pemformatan JSON/XML.",
        og_title="Pertanyaan Umum | Formix",
        og_description="Jawaban atas pertanyaan umum tentang Formix dan alat-alatnya.",
        h1="Pertanyaan Umum",
        lead="Pertanyaan umum tentang Formix, cara menangani data Anda, dan cara kerja alat-alatnya.",
        items=[
            ("Apakah Formix gratis digunakan?", "Ya. Semua alat sepenuhnya gratis, dan tidak perlu pendaftaran atau akun. Kami mungkin menampilkan iklan di masa depan untuk membantu menutupi biaya hosting, tetapi alat-alatnya sendiri akan tetap gratis."),
            ("Apakah data saya dikirim ke server?", 'Tidak. Alat seperti Pemformat JSON dan Pemformat XML memproses semuanya secara lokal di browser Anda menggunakan JavaScript. Teks yang Anda tempel tidak pernah ditransmisikan ke atau disimpan di server kami. Lihat <a href="{privacy}">Kebijakan Privasi</a> kami untuk detailnya.'),
            ("Apakah saya perlu membuat akun?", "Tidak perlu akun atau login untuk alat apa pun. Cukup buka halamannya dan mulai gunakan."),
            ("Browser apa yang didukung?", "Browser modern apa pun (Chrome, Edge, Firefox, Safari) di desktop atau seluler berfungsi dengan baik. Alat-alat ini mengandalkan API JavaScript standar yang didukung secara luas seperti DOMParser dan JSON.parse."),
            ("Bisakah saya menggunakan alat ini di ponsel saya?", "Ya, situs ini sepenuhnya responsif dan berfungsi di browser seluler, meskipun layar yang lebih besar memudahkan pengerjaan dokumen JSON atau XML yang panjang."),
            ("Apa yang terjadi jika JSON atau XML saya tidak valid?", "Alat akan menampilkan lencana status dan perkiraan baris/kolom tempat masalah ditemukan, sehingga Anda dapat dengan cepat menemukan dan memperbaiki masalah tersebut. Pemformat JSON juga dapat secara otomatis memperbaiki beberapa kesalahan umum, seperti tanda kutip yang hilang."),
            ("Apakah akan ada lebih banyak alat yang ditambahkan?", 'Ya. Formix dimulai dengan Pemformat JSON dan sekarang juga menawarkan <a href="{tool_xml}">Pemformat XML</a>, <a href="{tool_converter}">Konverter JSON ↔ XML</a>, <a href="{tool_sql}">Pemformat SQL</a>, dan <a href="{tool_code}">Penampil Kode</a>, ditambah dua permainan — <a href="{tool_typing}">Tes Kecepatan Mengetik</a> dan <a href="{game_syntax}">Kuis Sintaks Koding</a>. Kami berencana untuk terus menambahkan alat dan permainan kecil berbasis browser yang benar-benar bermanfaat — lihat halaman <a href="{about}">Tentang</a> kami untuk prinsip yang memandu kami.'),
            ("Bagaimana cara melaporkan bug atau menyarankan fitur?", 'Silakan hubungi kami melalui <a href="{contact}">halaman Kontak</a>. Kami membaca setiap pesan.'),
        ],
    ),
    "de": dict(
        title="Häufige Fragen | Formix",
        description="Häufig gestellte Fragen zu Formix — Preise, Datenverarbeitung, Browser-Unterstützung und wie die JSON/XML-Formatierungstools funktionieren.",
        og_title="Häufige Fragen | Formix",
        og_description="Antworten auf häufige Fragen zu Formix und seinen Tools.",
        h1="Häufige Fragen",
        lead="Häufige Fragen zu Formix, wie es mit Ihren Daten umgeht und wie die Tools funktionieren.",
        items=[
            ("Ist Formix kostenlos nutzbar?", "Ja. Alle Tools sind völlig kostenlos, und es ist keine Registrierung oder Konto erforderlich. Wir zeigen möglicherweise in Zukunft Werbung an, um Hosting-Kosten zu decken, aber die Tools selbst bleiben kostenlos."),
            ("Werden meine Daten an einen Server gesendet?", 'Nein. Tools wie der JSON-Formatierer und der XML-Formatierer verarbeiten alles lokal in Ihrem Browser mit JavaScript. Der Text, den Sie einfügen, wird niemals an unsere Server übermittelt oder dort gespeichert. Details finden Sie in unserer <a href="{privacy}">Datenschutzerklärung</a>.'),
            ("Muss ich ein Konto erstellen?", "Für kein Tool ist ein Konto oder eine Anmeldung erforderlich. Öffnen Sie einfach die Seite und nutzen Sie es sofort."),
            ("Welche Browser werden unterstützt?", "Jeder moderne Browser (Chrome, Edge, Firefox, Safari) auf Desktop oder Mobilgerät funktioniert. Die Tools basieren auf weit verbreiteten Standard-JavaScript-APIs wie DOMParser und JSON.parse."),
            ("Kann ich diese Tools auf meinem Smartphone nutzen?", "Ja, die Website ist vollständig responsiv und funktioniert in mobilen Browsern, wobei ein größerer Bildschirm die Arbeit mit langen JSON- oder XML-Dokumenten erleichtert."),
            ("Was passiert, wenn mein JSON oder XML ungültig ist?", "Das Tool zeigt ein Statusabzeichen und eine ungefähre Zeile/Spalte an, an der das Problem gefunden wurde, damit Sie es schnell lokalisieren und beheben können. Der JSON-Formatierer kann auch einige häufige Fehler automatisch korrigieren, wie fehlende Anführungszeichen."),
            ("Werden weitere Tools hinzugefügt?", 'Ja. Formix begann mit einem JSON-Formatierer und bietet jetzt auch einen <a href="{tool_xml}">XML-Formatierer</a>, einen <a href="{tool_converter}">JSON ↔ XML Konverter</a>, einen <a href="{tool_sql}">SQL-Formatierer</a> und einen <a href="{tool_code}">Code-Viewer</a>, sowie zwei Spiele — einen <a href="{tool_typing}">Schreibgeschwindigkeitstest</a> und ein <a href="{game_syntax}">Coding-Syntax-Quiz</a>. Wir planen, weiterhin kleine, wirklich nützliche browserbasierte Tools und Spiele hinzuzufügen — die Prinzipien, die uns leiten, finden Sie auf unserer Seite <a href="{about}">Über uns</a>.'),
            ("Wie melde ich einen Fehler oder schlage eine Funktion vor?", 'Bitte kontaktieren Sie uns über unsere <a href="{contact}">Kontaktseite</a>. Wir lesen jede Nachricht.'),
        ],
    ),
}

CONTENT["contact"] = {
    "en": dict(
        title="Contact | Formix",
        description="Contact Formix for bug reports, feature requests, or any other inquiries about the site or its tools.",
        og_title="Contact | Formix",
        og_description="How to get in touch with Formix.",
        h1="Contact",
        lead="Have a bug report, feature request, or question? We'd like to hear from it.",
        s1_h2="Email",
        s1_p="The fastest way to reach us is by email. We read every message, though replies may take a few days depending on volume.",
        s2_h2="What to include",
        s2_items=[
            "A short description of the issue or suggestion",
            "Which tool and language/page you were using (e.g. JSON Formatter, English)",
            "Steps to reproduce, if you're reporting a bug, along with the input that caused it (please remove any sensitive data first)",
        ],
        s3_h2="Other questions",
        s3_p='For questions about data handling, see our <a href="{privacy}">Privacy Policy</a>. For general questions about the site, check the <a href="{faq}">FAQ</a> first — your question may already be answered there.',
    ),
    "ko": dict(
        title="문의하기 | Formix",
        description="버그 제보, 기능 제안, 기타 문의 사항은 Formix로 연락해주세요.",
        og_title="문의하기 | Formix",
        og_description="Formix에 문의하는 방법을 안내합니다.",
        h1="문의하기",
        lead="버그를 발견하셨거나 새로운 기능을 제안하고 싶으신가요? 언제든 편하게 연락해주세요.",
        s1_h2="이메일",
        s1_p="가장 빠르게 연락하는 방법은 이메일입니다. 보내주시는 모든 메시지를 확인하고 있으며, 문의량에 따라 답변까지 며칠 걸릴 수 있습니다.",
        s2_h2="이런 내용을 포함해주시면 좋습니다",
        s2_items=[
            "문제 상황이나 제안 내용에 대한 간단한 설명",
            "사용 중이던 도구와 언어/페이지 (예: JSON 포매터, 한국어)",
            "버그 제보라면 재현 방법과 원인이 된 입력값 (민감한 정보는 미리 제거해주세요)",
        ],
        s3_h2="그 밖의 문의",
        s3_p='데이터 처리 방식이 궁금하시다면 <a href="{privacy}">개인정보처리방침</a>을 참고해주세요. 사이트 이용에 대한 일반적인 궁금증은 <a href="{faq}">자주 묻는 질문</a>에서 먼저 확인해보시면 빠르게 답을 찾으실 수 있습니다.',
    ),
    "ja": dict(
        title="お問い合わせ | Formix",
        description="不具合報告、機能提案、その他のお問い合わせはFormixまでご連絡ください。",
        og_title="お問い合わせ | Formix",
        og_description="Formixへのお問い合わせ方法をご案内します。",
        h1="お問い合わせ",
        lead="不具合を見つけた、新機能を提案したいなど、お気軽にご連絡ください。",
        s1_h2="メール",
        s1_p="最も早くご連絡いただける方法はメールです。いただいたメッセージはすべて確認しておりますが、状況によりご返信までに数日かかる場合があります。",
        s2_h2="含めていただきたい内容",
        s2_items=[
            "問題や提案内容の簡単な説明",
            "ご利用中のツールと言語/ページ(例: JSONフォーマッター、日本語)",
            "不具合報告の場合は再現手順と原因となった入力内容(機密情報は事前に削除してください)",
        ],
        s3_h2="その他のご質問",
        s3_p='データの取り扱いについては<a href="{privacy}">プライバシーポリシー</a>をご覧ください。サイトの利用に関する一般的なご質問は、まず<a href="{faq}">よくある質問</a>をご確認いただくと早く解決する場合があります。',
    ),
    "zh": dict(
        title="联系我们 | Formix",
        description="如有错误反馈、功能建议或其他咨询，请通过以下方式联系Formix。",
        og_title="联系我们 | Formix",
        og_description="介绍如何联系Formix。",
        h1="联系我们",
        lead="发现了错误，或想提出新功能建议？欢迎随时与我们联系。",
        s1_h2="电子邮箱",
        s1_p="通过邮件联系我们是最快的方式。我们会查看每一条消息，但根据咨询量的不同，回复可能需要几天时间。",
        s2_h2="建议包含以下内容",
        s2_items=[
            "问题或建议的简要说明",
            "使用的工具及语言/页面(例如：JSON 格式化，中文)",
            "如果是错误反馈，请附上复现步骤及导致问题的输入内容(请提前移除任何敏感信息)",
        ],
        s3_h2="其他问题",
        s3_p='关于数据处理方式，请参阅<a href="{privacy}">隐私政策</a>。关于网站使用的常见问题，建议先查看<a href="{faq}">常见问题</a>页面，您的问题可能已有答案。',
    ),
    "es": dict(
        title="Contacto | Formix",
        description="Contacta a Formix para reportar errores, sugerir funciones o cualquier otra consulta sobre el sitio o sus herramientas.",
        og_title="Contacto | Formix",
        og_description="Cómo ponerte en contacto con Formix.",
        h1="Contacto",
        lead="¿Tienes un reporte de error, una sugerencia de función o una pregunta? Nos encantaría saberlo.",
        s1_h2="Correo electrónico",
        s1_p="La forma más rápida de contactarnos es por correo electrónico. Leemos cada mensaje, aunque las respuestas pueden tardar unos días según el volumen.",
        s2_h2="Qué incluir",
        s2_items=[
            "Una breve descripción del problema o sugerencia",
            "Qué herramienta y idioma/página estabas usando (p. ej., Formateador JSON, español)",
            "Pasos para reproducir el problema, si estás reportando un error, junto con la entrada que lo causó (elimina primero cualquier dato sensible)",
        ],
        s3_h2="Otras preguntas",
        s3_p='Para preguntas sobre el manejo de datos, consulta nuestra <a href="{privacy}">Política de privacidad</a>. Para preguntas generales sobre el sitio, revisa primero las <a href="{faq}">Preguntas frecuentes</a> — tu pregunta podría ya estar respondida ahí.',
    ),
    "vi": dict(
        title="Liên hệ | Formix",
        description="Liên hệ với Formix để báo lỗi, đề xuất tính năng, hoặc bất kỳ thắc mắc nào khác về trang web hoặc các công cụ của nó.",
        og_title="Liên hệ | Formix",
        og_description="Cách liên hệ với Formix.",
        h1="Liên hệ",
        lead="Bạn có báo lỗi, đề xuất tính năng, hay câu hỏi nào không? Chúng tôi rất muốn nghe từ bạn.",
        s1_h2="Email",
        s1_p="Cách nhanh nhất để liên hệ với chúng tôi là qua email. Chúng tôi đọc mọi tin nhắn, dù việc trả lời có thể mất vài ngày tùy vào lượng liên hệ.",
        s2_h2="Nên bao gồm những gì",
        s2_items=[
            "Mô tả ngắn gọn về vấn đề hoặc đề xuất",
            "Công cụ và ngôn ngữ/trang bạn đang sử dụng (ví dụ: Định dạng JSON, Tiếng Việt)",
            "Các bước để tái hiện lỗi, nếu bạn đang báo lỗi, cùng với nội dung nhập vào gây ra lỗi (vui lòng loại bỏ mọi dữ liệu nhạy cảm trước)",
        ],
        s3_h2="Câu hỏi khác",
        s3_p='Về cách xử lý dữ liệu, xem <a href="{privacy}">Chính sách bảo mật</a> của chúng tôi. Về các câu hỏi chung liên quan đến trang web, hãy xem trước <a href="{faq}">Câu hỏi thường gặp</a> — câu hỏi của bạn có thể đã được trả lời ở đó.',
    ),
    "pt": dict(
        title="Contato | Formix",
        description="Contate o Formix para relatar erros, sugerir funcionalidades ou qualquer outra dúvida sobre o site ou suas ferramentas.",
        og_title="Contato | Formix",
        og_description="Como entrar em contato com o Formix.",
        h1="Contato",
        lead="Tem um relatório de erro, sugestão de funcionalidade ou pergunta? Gostaríamos de saber.",
        s1_h2="E-mail",
        s1_p="A maneira mais rápida de nos contatar é por e-mail. Lemos todas as mensagens, embora as respostas possam levar alguns dias dependendo do volume.",
        s2_h2="O que incluir",
        s2_items=[
            "Uma breve descrição do problema ou sugestão",
            "Qual ferramenta e idioma/página você estava usando (ex.: Formatador JSON, Português)",
            "Passos para reproduzir o problema, se estiver relatando um bug, junto com a entrada que o causou (remova primeiro quaisquer dados sensíveis)",
        ],
        s3_h2="Outras dúvidas",
        s3_p='Para dúvidas sobre o tratamento de dados, veja nossa <a href="{privacy}">Política de privacidade</a>. Para dúvidas gerais sobre o site, confira primeiro as <a href="{faq}">Perguntas frequentes</a> — sua pergunta pode já estar respondida lá.',
    ),
    "id": dict(
        title="Kontak | Formix",
        description="Hubungi Formix untuk melaporkan bug, menyarankan fitur, atau pertanyaan lain tentang situs atau alat-alatnya.",
        og_title="Kontak | Formix",
        og_description="Cara menghubungi Formix.",
        h1="Kontak",
        lead="Ada laporan bug, saran fitur, atau pertanyaan? Kami ingin mendengarnya.",
        s1_h2="Email",
        s1_p="Cara tercepat untuk menghubungi kami adalah melalui email. Kami membaca setiap pesan, meskipun balasan dapat memakan waktu beberapa hari tergantung volume.",
        s2_h2="Apa yang harus disertakan",
        s2_items=[
            "Deskripsi singkat tentang masalah atau saran",
            "Alat dan bahasa/halaman apa yang Anda gunakan (misalnya, Pemformat JSON, Bahasa Indonesia)",
            "Langkah-langkah untuk mereproduksi masalah, jika Anda melaporkan bug, beserta input yang menyebabkannya (harap hapus data sensitif apa pun terlebih dahulu)",
        ],
        s3_h2="Pertanyaan lain",
        s3_p='Untuk pertanyaan tentang penanganan data, lihat <a href="{privacy}">Kebijakan Privasi</a> kami. Untuk pertanyaan umum tentang situs, periksa dulu <a href="{faq}">Pertanyaan Umum</a> — pertanyaan Anda mungkin sudah terjawab di sana.',
    ),
    "de": dict(
        title="Kontakt | Formix",
        description="Kontaktieren Sie Formix für Fehlermeldungen, Funktionswünsche oder sonstige Anfragen zur Website oder ihren Tools.",
        og_title="Kontakt | Formix",
        og_description="Wie Sie Formix kontaktieren können.",
        h1="Kontakt",
        lead="Haben Sie eine Fehlermeldung, einen Funktionswunsch oder eine Frage? Wir würden gerne davon hören.",
        s1_h2="E-Mail",
        s1_p="Der schnellste Weg, uns zu erreichen, ist per E-Mail. Wir lesen jede Nachricht, Antworten können jedoch je nach Anfragevolumen einige Tage dauern.",
        s2_h2="Was Sie angeben sollten",
        s2_items=[
            "Eine kurze Beschreibung des Problems oder Vorschlags",
            "Welches Tool und welche Sprache/Seite Sie verwendet haben (z. B. JSON-Formatierer, Deutsch)",
            "Schritte zur Reproduktion, falls Sie einen Fehler melden, zusammen mit der Eingabe, die ihn verursacht hat (bitte entfernen Sie zuvor alle sensiblen Daten)",
        ],
        s3_h2="Weitere Fragen",
        s3_p='Fragen zur Datenverarbeitung finden Sie in unserer <a href="{privacy}">Datenschutzerklärung</a>. Für allgemeine Fragen zur Website schauen Sie zuerst in unsere <a href="{faq}">Häufigen Fragen</a> — Ihre Frage ist dort vielleicht schon beantwortet.',
    ),
}

CONTENT["terms"] = {
    "en": dict(
        title="Terms of Service | Formix",
        description="Terms of Service for Formix — acceptance of terms, service description, user responsibilities, disclaimer of warranty, and limitation of liability.",
        og_title="Terms of Service | Formix",
        og_description="The terms that apply to using Formix and its tools.",
        h1="Terms of Service", effective="Effective date: September 21, 2026",
        intro='These Terms of Service ("Terms") govern your use of Formix (the "Site") and the tools it provides. By using the Site, you agree to these Terms.',
        s1_h2="1. Acceptance of terms",
        s1_p1="By accessing or using the Site, you agree to be bound by these Terms. If you do not agree, please do not use the Site.",
        s2_h2="2. Description of the service",
        s2_p1='Formix provides free, browser-based utilities (such as the <a href="{tool}">JSON Formatter</a> and <a href="{tool_xml}">XML Formatter</a>) that run entirely on the client side. No account is required, and no fee is currently charged for using the tools.',
        s3_h2="3. User responsibilities",
        s3_p1="You agree not to:",
        s3_li1="Use the Site for any unlawful purpose, or to process content that is illegal, infringing, or harmful to others.",
        s3_li2="Attempt to disrupt the Site's operation, including through excessive automated requests, scraping at a scale that degrades service for others, or attempts to bypass security measures.",
        s3_li3="Reverse-engineer, decompile, or attempt to extract the source code of the Site except as permitted by applicable law.",
        s4_h2="4. Intellectual property",
        s4_p1="The Site's design, code, layout, and branding are the property of the Site operator unless otherwise noted. Since the tools process your input entirely in your browser and never transmit it to our servers, you retain all rights to the data you enter — we make no claim to it.",
        s5_h2="5. Disclaimer of warranty",
        s5_p1='The Site and its tools are provided "as is" and "as available," without warranties of any kind, express or implied, including but not limited to accuracy, reliability, or fitness for a particular purpose. While we aim for correctness, you are responsible for verifying any output (such as formatted JSON or XML) before relying on it for important or production use.',
        s6_h2="6. Limitation of liability",
        s6_p1="To the fullest extent permitted by law, the Site operator shall not be liable for any indirect, incidental, or consequential damages arising from your use of, or inability to use, the Site or its tools.",
        s7_h2="7. Changes to the service",
        s7_p1="We may add, modify, or discontinue any tool or feature of the Site at any time, with or without notice.",
        s8_h2="8. Changes to these terms",
        s8_p1="We may revise these Terms from time to time. Continued use of the Site after changes take effect constitutes acceptance of the revised Terms. Significant changes will be noted on our <a href=\"{updates}\">What's New</a> page.",
        s9_h2="9. Contact",
        s9_p1='Questions about these Terms can be directed to us via our <a href="{contact}">Contact page</a> or the email address below.',
    ),
    "ko": dict(
        title="이용약관 | Formix",
        description="Formix 이용약관 — 약관 동의, 서비스 설명, 이용자의 의무, 면책조항, 책임 제한에 관한 안내입니다.",
        og_title="이용약관 | Formix",
        og_description="Formix와 제공 도구 이용에 적용되는 약관입니다.",
        h1="이용약관", effective="시행일자: 2026년 9월 21일",
        intro='본 이용약관(이하 "약관")은 Formix(이하 "사이트")와 사이트가 제공하는 도구의 이용 조건을 규정합니다. 사이트를 이용함으로써 이용자는 본 약관에 동의하는 것으로 간주됩니다.',
        s1_h2="1. 약관의 동의",
        s1_p1="사이트에 접속하거나 이를 이용함으로써 이용자는 본 약관에 구속되는 것에 동의합니다. 약관에 동의하지 않으시는 경우 사이트를 이용하실 수 없습니다.",
        s2_h2="2. 서비스 설명",
        s2_p1='Formix는 <a href="{tool}">JSON 포매터</a>, <a href="{tool_xml}">XML 포매터</a> 등 브라우저에서 완전히 동작하는 무료 유틸리티를 제공합니다. 별도의 회원가입이 필요하지 않으며, 현재 도구 이용에 따른 요금은 부과되지 않습니다.',
        s3_h2="3. 이용자의 의무",
        s3_p1="이용자는 다음 행위를 해서는 안 됩니다.",
        s3_li1="불법적인 목적으로 사이트를 이용하거나, 위법·침해적이거나 타인에게 피해를 주는 콘텐츠를 처리하는 행위",
        s3_li2="과도한 자동화 요청, 다른 이용자의 서비스 이용을 저해할 정도의 대규모 스크래핑, 보안 조치를 우회하려는 시도 등 사이트 운영을 방해하는 행위",
        s3_li3="관련 법령이 허용하는 경우를 제외하고 사이트를 역설계, 디컴파일하거나 소스 코드를 추출하려는 행위",
        s4_h2="4. 지적재산권",
        s4_p1="별도로 명시하지 않는 한 사이트의 디자인, 코드, 레이아웃, 브랜딩에 대한 권리는 사이트 운영자에게 있습니다. 도구는 입력값을 브라우저 안에서만 처리하고 서버로 전송하지 않으므로, 이용자가 입력한 데이터에 대한 권리는 전적으로 이용자에게 있으며 사이트 운영자는 이에 대해 어떠한 권리도 주장하지 않습니다.",
        s5_h2="5. 면책조항",
        s5_p1='사이트와 도구는 "있는 그대로(as is)", "제공 가능한 상태로(as available)" 제공되며, 정확성·신뢰성·특정 목적 적합성 등에 대한 명시적·묵시적 보증을 하지 않습니다. 정확성을 위해 최선을 다하고 있으나, 중요한 업무나 프로덕션 환경에 결과물(정리된 JSON·XML 등)을 사용하시기 전에는 이용자가 직접 검증해야 합니다.',
        s6_h2="6. 책임의 제한",
        s6_p1="관련 법령이 허용하는 최대한의 범위 내에서, 사이트 운영자는 사이트 또는 도구의 이용(또는 이용 불가)으로 인해 발생하는 간접적, 부수적, 결과적 손해에 대해 책임을 지지 않습니다.",
        s7_h2="7. 서비스의 변경",
        s7_p1="사이트 운영자는 사전 고지 여부와 관계없이 언제든지 사이트의 도구나 기능을 추가, 변경 또는 중단할 수 있습니다.",
        s8_h2="8. 약관의 변경",
        s8_p1='본 약관은 필요에 따라 개정될 수 있으며, 변경된 약관이 적용된 이후에도 사이트를 계속 이용하는 경우 변경된 약관에 동의한 것으로 간주됩니다. 중요한 변경 사항은 <a href="{updates}">업데이트 소식</a> 페이지를 통해 안내합니다.',
        s9_h2="9. 문의",
        s9_p1='본 약관에 대한 문의는 <a href="{contact}">문의하기</a> 페이지 또는 아래 이메일로 연락해 주시기 바랍니다.',
    ),
    "ja": dict(
        title="利用規約 | Formix",
        description="Formixの利用規約です。規約への同意、サービス内容、利用者の義務、免責事項、責任の制限についてご案内します。",
        og_title="利用規約 | Formix",
        og_description="Formixおよび提供ツールの利用に適用される規約です。",
        h1="利用規約", effective="施行日: 2026年9月21日",
        intro='本利用規約(以下「本規約」)は、Formix(以下「本サイト」)および本サイトが提供するツールの利用条件を定めるものです。本サイトを利用することにより、利用者は本規約に同意したものとみなされます。',
        s1_h2="1. 規約への同意",
        s1_p1="本サイトにアクセスまたは利用することにより、利用者は本規約に拘束されることに同意するものとします。本規約に同意されない場合、本サイトをご利用いただけません。",
        s2_h2="2. サービスの内容",
        s2_p1='Formixは、<a href="{tool}">JSONフォーマッター</a>、<a href="{tool_xml}">XMLフォーマッター</a>など、ブラウザ上で完結する無料のユーティリティを提供しています。会員登録は不要で、現時点ではツールの利用に料金は発生しません。',
        s3_h2="3. 利用者の義務",
        s3_p1="利用者は、以下の行為を行ってはなりません。",
        s3_li1="違法な目的で本サイトを利用すること、または違法・侵害的、もしくは第三者に損害を与えるコンテンツを処理すること",
        s3_li2="過度な自動リクエスト、他の利用者のサービス利用を妨げる規模のスクレイピング、セキュリティ対策を回避しようとする行為など、本サイトの運営を妨害すること",
        s3_li3="関連法令で許容される場合を除き、本サイトをリバースエンジニアリング、逆コンパイルし、またはソースコードを抽出しようとすること",
        s4_h2="4. 知的財産権",
        s4_p1="特に明記されていない限り、本サイトのデザイン、コード、レイアウト、ブランディングに関する権利はサイト運営者に帰属します。ツールは入力内容をブラウザ内でのみ処理しサーバーに送信しないため、利用者が入力したデータに関する権利は利用者に帰属し、サイト運営者はこれに対していかなる権利も主張しません。",
        s5_h2="5. 免責事項",
        s5_p1='本サイトおよびツールは「現状有姿(as is)」「提供可能な状態(as available)」で提供され、正確性、信頼性、特定目的への適合性等について明示的にも黙示的にも保証しません。正確性の確保に努めていますが、重要な業務や本番環境で結果(整形されたJSON・XMLなど)を利用される前に、利用者ご自身で検証してください。',
        s6_h2="6. 責任の制限",
        s6_p1="関連法令で許容される最大限の範囲において、サイト運営者は本サイトまたはツールの利用(または利用不能)から生じる間接的、付随的、結果的損害について責任を負いません。",
        s7_h2="7. サービスの変更",
        s7_p1="サイト運営者は、事前の通知の有無にかかわらず、いつでも本サイトのツールや機能を追加、変更、または中止することができます。",
        s8_h2="8. 規約の変更",
        s8_p1='本規約は必要に応じて改定される場合があり、変更後も本サイトの利用を継続した場合、変更後の規約に同意したものとみなされます。重要な変更は<a href="{updates}">更新情報</a>ページでご案内します。',
        s9_h2="9. お問い合わせ",
        s9_p1='本規約に関するお問い合わせは、<a href="{contact}">お問い合わせ</a>ページまたは下記のメールアドレスまでご連絡ください。',
    ),
    "zh": dict(
        title="使用条款 | Formix",
        description="Formix使用条款 — 条款接受、服务说明、用户责任、免责声明及责任限制说明。",
        og_title="使用条款 | Formix",
        og_description="使用Formix及其提供工具所适用的条款。",
        h1="使用条款", effective="生效日期：2026年9月21日",
        intro='本使用条款(以下简称"本条款")规范您对Formix(以下简称"本网站")及其提供工具的使用。使用本网站即表示您同意本条款。',
        s1_h2="1. 条款的接受",
        s1_p1="访问或使用本网站，即表示您同意受本条款约束。如果您不同意本条款，请不要使用本网站。",
        s2_h2="2. 服务说明",
        s2_p1='Formix提供完全在浏览器端运行的免费工具，如 <a href="{tool}">JSON 格式化工具</a>、<a href="{tool_xml}">XML 格式化工具</a>等。无需注册账号，目前使用这些工具不收取任何费用。',
        s3_h2="3. 用户责任",
        s3_p1="您同意不进行以下行为：",
        s3_li1="将本网站用于任何非法目的，或处理非法、侵权或可能对他人造成损害的内容",
        s3_li2="通过过度的自动化请求、可能影响其他用户使用体验的大规模抓取，或试图绕过安全措施等方式干扰本网站的正常运行",
        s3_li3="在适用法律允许的范围之外，对本网站进行逆向工程、反编译或试图提取源代码",
        s4_h2="4. 知识产权",
        s4_p1="除另有说明外，本网站的设计、代码、布局及品牌相关权利归网站运营者所有。由于工具仅在您的浏览器中处理输入内容，不会发送到服务器，您输入的数据的所有权利完全归您所有，网站运营者不对此主张任何权利。",
        s5_h2="5. 免责声明",
        s5_p1='本网站及其工具按"现状"和"可用性"提供，不对准确性、可靠性或特定用途的适用性作出任何明示或暗示的保证。我们努力确保准确性，但在将结果(如格式化后的 JSON、XML)用于重要业务或生产环境之前，请您自行核实。',
        s6_h2="6. 责任限制",
        s6_p1="在法律允许的最大范围内，网站运营者对因使用或无法使用本网站或其工具而产生的任何间接、附带或后果性损害不承担责任。",
        s7_h2="7. 服务的变更",
        s7_p1="网站运营者可能随时新增、修改或终止本网站的任何工具或功能，恕不另行通知。",
        s8_h2="8. 条款的变更",
        s8_p1='本条款可能会不定期修订，变更生效后继续使用本网站即视为您同意修订后的条款。重大变更将在<a href="{updates}">更新日志</a>页面公布。',
        s9_h2="9. 联系方式",
        s9_p1='如对本条款有任何疑问，请通过<a href="{contact}">联系我们</a>页面或以下邮箱与我们联系。',
    ),
    "es": dict(
        title="Términos de servicio | Formix",
        description="Términos de servicio de Formix — aceptación de términos, descripción del servicio, responsabilidades del usuario, exención de garantía y limitación de responsabilidad.",
        og_title="Términos de servicio | Formix",
        og_description="Los términos que se aplican al uso de Formix y sus herramientas.",
        h1="Términos de servicio", effective="Fecha de vigencia: 21 de septiembre de 2026",
        intro='Estos Términos de servicio ("Términos") rigen tu uso de Formix (el "Sitio") y las herramientas que ofrece. Al usar el Sitio, aceptas estos Términos.',
        s1_h2="1. Aceptación de términos",
        s1_p1="Al acceder o usar el Sitio, aceptas quedar vinculado por estos Términos. Si no estás de acuerdo, no uses el Sitio.",
        s2_h2="2. Descripción del servicio",
        s2_p1='Formix ofrece utilidades gratuitas basadas en el navegador (como el <a href="{tool}">Formateador JSON</a> y el <a href="{tool_xml}">Formateador XML</a>) que funcionan completamente del lado del cliente. No se requiere cuenta, y actualmente no se cobra ninguna tarifa por usar las herramientas.',
        s3_h2="3. Responsabilidades del usuario",
        s3_p1="Aceptas no:",
        s3_li1="Usar el Sitio para ningún propósito ilegal, ni procesar contenido que sea ilegal, infractor o dañino para otros.",
        s3_li2="Intentar interrumpir el funcionamiento del Sitio, incluso mediante solicitudes automatizadas excesivas, extracción de datos a una escala que degrade el servicio para otros, o intentos de eludir medidas de seguridad.",
        s3_li3="Realizar ingeniería inversa, descompilar o intentar extraer el código fuente del Sitio, excepto en la medida permitida por la ley aplicable.",
        s4_h2="4. Propiedad intelectual",
        s4_p1="El diseño, código, diseño visual y marca del Sitio son propiedad del operador del Sitio salvo que se indique lo contrario. Dado que las herramientas procesan tu entrada completamente en tu navegador y nunca la transmiten a nuestros servidores, conservas todos los derechos sobre los datos que ingresas — no reclamamos ningún derecho sobre ellos.",
        s5_h2="5. Exención de garantía",
        s5_p1='El Sitio y sus herramientas se proporcionan "tal cual" y "según disponibilidad", sin garantías de ningún tipo, expresas o implícitas, incluidas, entre otras, la precisión, la confiabilidad o la idoneidad para un propósito particular. Aunque buscamos la corrección, eres responsable de verificar cualquier resultado (como JSON o XML formateado) antes de confiar en él para un uso importante o de producción.',
        s6_h2="6. Limitación de responsabilidad",
        s6_p1="En la máxima medida permitida por la ley, el operador del Sitio no será responsable de ningún daño indirecto, incidental o consecuente que surja de tu uso, o incapacidad de uso, del Sitio o sus herramientas.",
        s7_h2="7. Cambios al servicio",
        s7_p1="Podemos agregar, modificar o descontinuar cualquier herramienta o función del Sitio en cualquier momento, con o sin aviso.",
        s8_h2="8. Cambios a estos términos",
        s8_p1='Podemos revisar estos Términos de vez en cuando. El uso continuado del Sitio después de que los cambios entren en vigor constituye la aceptación de los Términos revisados. Los cambios importantes se indicarán en nuestra página de <a href="{updates}">Novedades</a>.',
        s9_h2="9. Contacto",
        s9_p1='Las preguntas sobre estos Términos pueden dirigirse a nosotros a través de nuestra <a href="{contact}">página de Contacto</a> o la dirección de correo electrónico de abajo.',
    ),
    "vi": dict(
        title="Điều khoản dịch vụ | Formix",
        description="Điều khoản dịch vụ của Formix — chấp nhận điều khoản, mô tả dịch vụ, trách nhiệm người dùng, từ chối bảo đảm và giới hạn trách nhiệm.",
        og_title="Điều khoản dịch vụ | Formix",
        og_description="Các điều khoản áp dụng cho việc sử dụng Formix và các công cụ của nó.",
        h1="Điều khoản dịch vụ", effective="Ngày hiệu lực: 21 tháng 9 năm 2026",
        intro='Các Điều khoản dịch vụ này ("Điều khoản") điều chỉnh việc bạn sử dụng Formix ("Trang web") và các công cụ mà nó cung cấp. Bằng cách sử dụng Trang web, bạn đồng ý với các Điều khoản này.',
        s1_h2="1. Chấp nhận điều khoản",
        s1_p1="Bằng cách truy cập hoặc sử dụng Trang web, bạn đồng ý bị ràng buộc bởi các Điều khoản này. Nếu bạn không đồng ý, vui lòng không sử dụng Trang web.",
        s2_h2="2. Mô tả dịch vụ",
        s2_p1='Formix cung cấp các tiện ích miễn phí dựa trên trình duyệt (như <a href="{tool}">Công cụ định dạng JSON</a> và <a href="{tool_xml}">Công cụ định dạng XML</a>) hoạt động hoàn toàn ở phía máy khách. Không cần tài khoản, và hiện tại không có phí sử dụng các công cụ này.',
        s3_h2="3. Trách nhiệm của người dùng",
        s3_p1="Bạn đồng ý không:",
        s3_li1="Sử dụng Trang web cho bất kỳ mục đích bất hợp pháp nào, hoặc xử lý nội dung bất hợp pháp, vi phạm, hoặc gây hại cho người khác.",
        s3_li2="Cố gắng làm gián đoạn hoạt động của Trang web, bao gồm thông qua các yêu cầu tự động quá mức, thu thập dữ liệu ở quy mô làm giảm chất lượng dịch vụ cho người khác, hoặc cố gắng vượt qua các biện pháp bảo mật.",
        s3_li3="Dịch ngược, giải mã, hoặc cố gắng trích xuất mã nguồn của Trang web, trừ khi được pháp luật hiện hành cho phép.",
        s4_h2="4. Sở hữu trí tuệ",
        s4_p1="Thiết kế, mã nguồn, bố cục và thương hiệu của Trang web là tài sản của nhà vận hành Trang web trừ khi có ghi chú khác. Vì các công cụ xử lý dữ liệu đầu vào của bạn hoàn toàn trong trình duyệt và không bao giờ truyền đến máy chủ của chúng tôi, bạn giữ toàn bộ quyền đối với dữ liệu bạn nhập — chúng tôi không có bất kỳ yêu sách nào đối với nó.",
        s5_h2="5. Từ chối bảo đảm",
        s5_p1='Trang web và các công cụ của nó được cung cấp "nguyên trạng" và "theo tình trạng có sẵn", không có bất kỳ bảo đảm nào, rõ ràng hay ngụ ý, bao gồm nhưng không giới hạn ở tính chính xác, độ tin cậy hoặc sự phù hợp cho một mục đích cụ thể. Mặc dù chúng tôi hướng đến sự chính xác, bạn có trách nhiệm xác minh bất kỳ kết quả nào (như JSON hoặc XML đã định dạng) trước khi dựa vào đó cho mục đích quan trọng hoặc sản xuất.',
        s6_h2="6. Giới hạn trách nhiệm",
        s6_p1="Trong phạm vi tối đa được pháp luật cho phép, nhà vận hành Trang web sẽ không chịu trách nhiệm đối với bất kỳ thiệt hại gián tiếp, ngẫu nhiên hoặc hệ quả nào phát sinh từ việc bạn sử dụng, hoặc không thể sử dụng, Trang web hoặc các công cụ của nó.",
        s7_h2="7. Thay đổi đối với dịch vụ",
        s7_p1="Chúng tôi có thể thêm, sửa đổi hoặc ngừng cung cấp bất kỳ công cụ hoặc tính năng nào của Trang web vào bất kỳ lúc nào, có hoặc không có thông báo trước.",
        s8_h2="8. Thay đổi đối với các điều khoản này",
        s8_p1='Chúng tôi có thể sửa đổi các Điều khoản này theo thời gian. Việc tiếp tục sử dụng Trang web sau khi các thay đổi có hiệu lực cấu thành sự chấp nhận các Điều khoản đã sửa đổi. Các thay đổi quan trọng sẽ được ghi chú trên trang <a href="{updates}">Cập nhật mới</a> của chúng tôi.',
        s9_h2="9. Liên hệ",
        s9_p1='Các câu hỏi về các Điều khoản này có thể được gửi đến chúng tôi qua <a href="{contact}">trang Liên hệ</a> hoặc địa chỉ email bên dưới.',
    ),
    "pt": dict(
        title="Termos de serviço | Formix",
        description="Termos de serviço do Formix — aceitação dos termos, descrição do serviço, responsabilidades do usuário, isenção de garantia e limitação de responsabilidade.",
        og_title="Termos de serviço | Formix",
        og_description="Os termos que se aplicam ao uso do Formix e suas ferramentas.",
        h1="Termos de serviço", effective="Data de vigência: 21 de setembro de 2026",
        intro='Estes Termos de serviço ("Termos") regem seu uso do Formix (o "Site") e as ferramentas que ele oferece. Ao usar o Site, você concorda com estes Termos.',
        s1_h2="1. Aceitação dos termos",
        s1_p1="Ao acessar ou usar o Site, você concorda em estar vinculado a estes Termos. Se você não concordar, não use o Site.",
        s2_h2="2. Descrição do serviço",
        s2_p1='O Formix oferece utilitários gratuitos baseados no navegador (como o <a href="{tool}">Formatador JSON</a> e o <a href="{tool_xml}">Formatador XML</a>) que funcionam inteiramente no lado do cliente. Nenhuma conta é necessária, e atualmente não é cobrada nenhuma taxa pelo uso das ferramentas.',
        s3_h2="3. Responsabilidades do usuário",
        s3_p1="Você concorda em não:",
        s3_li1="Usar o Site para qualquer finalidade ilegal, ou processar conteúdo ilegal, infrator ou prejudicial a terceiros.",
        s3_li2="Tentar interromper o funcionamento do Site, inclusive por meio de solicitações automatizadas excessivas, extração de dados em escala que degrade o serviço para outros, ou tentativas de contornar medidas de segurança.",
        s3_li3="Realizar engenharia reversa, descompilar ou tentar extrair o código-fonte do Site, exceto conforme permitido pela lei aplicável.",
        s4_h2="4. Propriedade intelectual",
        s4_p1="O design, código, layout e marca do Site são propriedade do operador do Site, salvo indicação em contrário. Como as ferramentas processam sua entrada inteiramente no seu navegador e nunca a transmitem aos nossos servidores, você retém todos os direitos sobre os dados que insere — não reivindicamos nenhum direito sobre eles.",
        s5_h2="5. Isenção de garantia",
        s5_p1='O Site e suas ferramentas são fornecidos "como estão" e "conforme disponíveis", sem garantias de qualquer tipo, expressas ou implícitas, incluindo, mas não se limitando a, precisão, confiabilidade ou adequação a um propósito específico. Embora busquemos a correção, você é responsável por verificar qualquer resultado (como JSON ou XML formatado) antes de confiar nele para uso importante ou em produção.',
        s6_h2="6. Limitação de responsabilidade",
        s6_p1="Na máxima extensão permitida por lei, o operador do Site não será responsável por quaisquer danos indiretos, incidentais ou consequenciais decorrentes do seu uso, ou incapacidade de uso, do Site ou suas ferramentas.",
        s7_h2="7. Alterações no serviço",
        s7_p1="Podemos adicionar, modificar ou descontinuar qualquer ferramenta ou funcionalidade do Site em qualquer momento, com ou sem aviso.",
        s8_h2="8. Alterações a estes termos",
        s8_p1='Podemos revisar estes Termos periodicamente. O uso continuado do Site após as alterações entrarem em vigor constitui aceitação dos Termos revisados. Alterações significativas serão indicadas em nossa página de <a href="{updates}">Novidades</a>.',
        s9_h2="9. Contato",
        s9_p1='Dúvidas sobre estes Termos podem ser direcionadas a nós através da nossa <a href="{contact}">página de Contato</a> ou pelo endereço de e-mail abaixo.',
    ),
    "id": dict(
        title="Ketentuan Layanan | Formix",
        description="Ketentuan Layanan Formix — penerimaan ketentuan, deskripsi layanan, tanggung jawab pengguna, penyangkalan garansi, dan batasan tanggung jawab.",
        og_title="Ketentuan Layanan | Formix",
        og_description="Ketentuan yang berlaku untuk penggunaan Formix dan alat-alatnya.",
        h1="Ketentuan Layanan", effective="Tanggal berlaku: 21 September 2026",
        intro='Ketentuan Layanan ini ("Ketentuan") mengatur penggunaan Anda atas Formix ("Situs") dan alat-alat yang disediakannya. Dengan menggunakan Situs, Anda menyetujui Ketentuan ini.',
        s1_h2="1. Penerimaan ketentuan",
        s1_p1="Dengan mengakses atau menggunakan Situs, Anda setuju untuk terikat oleh Ketentuan ini. Jika Anda tidak setuju, harap jangan gunakan Situs.",
        s2_h2="2. Deskripsi layanan",
        s2_p1='Formix menyediakan utilitas gratis berbasis browser (seperti <a href="{tool}">Pemformat JSON</a> dan <a href="{tool_xml}">Pemformat XML</a>) yang berjalan sepenuhnya di sisi klien. Tidak diperlukan akun, dan saat ini tidak ada biaya untuk menggunakan alat-alat ini.',
        s3_h2="3. Tanggung jawab pengguna",
        s3_p1="Anda setuju untuk tidak:",
        s3_li1="Menggunakan Situs untuk tujuan yang melanggar hukum, atau memproses konten yang ilegal, melanggar hak, atau berbahaya bagi orang lain.",
        s3_li2="Mencoba mengganggu operasional Situs, termasuk melalui permintaan otomatis yang berlebihan, scraping dalam skala yang menurunkan kualitas layanan bagi orang lain, atau upaya untuk melewati langkah-langkah keamanan.",
        s3_li3="Melakukan rekayasa balik, dekompilasi, atau mencoba mengekstrak kode sumber Situs kecuali sejauh diizinkan oleh hukum yang berlaku.",
        s4_h2="4. Kekayaan intelektual",
        s4_p1="Desain, kode, tata letak, dan merek Situs adalah milik operator Situs kecuali dinyatakan lain. Karena alat-alat ini memproses input Anda sepenuhnya di browser Anda dan tidak pernah mengirimkannya ke server kami, Anda tetap memegang semua hak atas data yang Anda masukkan — kami tidak mengklaim hak apa pun atasnya.",
        s5_h2="5. Penyangkalan garansi",
        s5_p1='Situs dan alat-alatnya disediakan "sebagaimana adanya" dan "sebagaimana tersedia", tanpa jaminan apa pun, baik tersurat maupun tersirat, termasuk namun tidak terbatas pada keakuratan, keandalan, atau kesesuaian untuk tujuan tertentu. Meskipun kami berupaya untuk akurasi, Anda bertanggung jawab untuk memverifikasi setiap hasil (seperti JSON atau XML yang diformat) sebelum mengandalkannya untuk penggunaan penting atau produksi.',
        s6_h2="6. Batasan tanggung jawab",
        s6_p1="Sejauh diizinkan oleh hukum, operator Situs tidak akan bertanggung jawab atas kerugian tidak langsung, insidental, atau konsekuensial yang timbul dari penggunaan Anda, atau ketidakmampuan Anda menggunakan, Situs atau alat-alatnya.",
        s7_h2="7. Perubahan pada layanan",
        s7_p1="Kami dapat menambah, mengubah, atau menghentikan alat atau fitur apa pun di Situs kapan saja, dengan atau tanpa pemberitahuan.",
        s8_h2="8. Perubahan pada ketentuan ini",
        s8_p1='Kami dapat merevisi Ketentuan ini dari waktu ke waktu. Penggunaan Situs yang berlanjut setelah perubahan berlaku merupakan penerimaan atas Ketentuan yang direvisi. Perubahan signifikan akan dicatat di halaman <a href="{updates}">Pembaruan</a> kami.',
        s9_h2="9. Kontak",
        s9_p1='Pertanyaan tentang Ketentuan ini dapat diarahkan kepada kami melalui <a href="{contact}">halaman Kontak</a> kami atau alamat email di bawah ini.',
    ),
    "de": dict(
        title="Nutzungsbedingungen | Formix",
        description="Nutzungsbedingungen für Formix — Annahme der Bedingungen, Dienstbeschreibung, Pflichten der Nutzer, Gewährleistungsausschluss und Haftungsbeschränkung.",
        og_title="Nutzungsbedingungen | Formix",
        og_description="Die Bedingungen, die für die Nutzung von Formix und seinen Tools gelten.",
        h1="Nutzungsbedingungen", effective="Datum des Inkrafttretens: 21. September 2026",
        intro='Diese Nutzungsbedingungen ("Bedingungen") regeln Ihre Nutzung von Formix (der „Website") und den von ihr angebotenen Tools. Durch die Nutzung der Website stimmen Sie diesen Bedingungen zu.',
        s1_h2="1. Annahme der Bedingungen",
        s1_p1="Durch den Zugriff auf oder die Nutzung der Website erklären Sie sich damit einverstanden, an diese Bedingungen gebunden zu sein. Wenn Sie nicht einverstanden sind, nutzen Sie die Website bitte nicht.",
        s2_h2="2. Beschreibung des Dienstes",
        s2_p1='Formix bietet kostenlose, browserbasierte Dienstprogramme (wie den <a href="{tool}">JSON-Formatierer</a> und den <a href="{tool_xml}">XML-Formatierer</a>) an, die vollständig clientseitig laufen. Es ist kein Konto erforderlich, und derzeit wird keine Gebühr für die Nutzung der Tools erhoben.',
        s3_h2="3. Pflichten der Nutzer",
        s3_p1="Sie stimmen zu, Folgendes nicht zu tun:",
        s3_li1="Die Website für rechtswidrige Zwecke zu nutzen oder Inhalte zu verarbeiten, die rechtswidrig, rechtsverletzend oder für andere schädlich sind.",
        s3_li2="Zu versuchen, den Betrieb der Website zu stören, einschließlich durch übermäßige automatisierte Anfragen, Scraping in einem Umfang, der den Dienst für andere verschlechtert, oder Versuche, Sicherheitsmaßnahmen zu umgehen.",
        s3_li3="Die Website zurückzuentwickeln, zu dekompilieren oder zu versuchen, ihren Quellcode zu extrahieren, außer soweit dies nach geltendem Recht zulässig ist.",
        s4_h2="4. Geistiges Eigentum",
        s4_p1="Design, Code, Layout und Markenzeichen der Website sind, sofern nicht anders angegeben, Eigentum des Website-Betreibers. Da die Tools Ihre Eingabe vollständig in Ihrem Browser verarbeiten und niemals an unsere Server übermitteln, behalten Sie alle Rechte an den von Ihnen eingegebenen Daten — wir erheben darauf keinen Anspruch.",
        s5_h2="5. Gewährleistungsausschluss",
        s5_p1='Die Website und ihre Tools werden „wie besehen" und „wie verfügbar" bereitgestellt, ohne jegliche ausdrückliche oder stillschweigende Gewährleistung, einschließlich, aber nicht beschränkt auf Genauigkeit, Zuverlässigkeit oder Eignung für einen bestimmten Zweck. Obwohl wir uns um Korrektheit bemühen, sind Sie dafür verantwortlich, jede Ausgabe (wie formatiertes JSON oder XML) zu überprüfen, bevor Sie sich für wichtige oder produktive Zwecke darauf verlassen.',
        s6_h2="6. Haftungsbeschränkung",
        s6_p1="Im größtmöglichen gesetzlich zulässigen Umfang haftet der Website-Betreiber nicht für indirekte, beiläufige oder Folgeschäden, die aus Ihrer Nutzung oder Nichtnutzungsfähigkeit der Website oder ihrer Tools entstehen.",
        s7_h2="7. Änderungen des Dienstes",
        s7_p1="Wir können jederzeit, mit oder ohne Vorankündigung, Tools oder Funktionen der Website hinzufügen, ändern oder einstellen.",
        s8_h2="8. Änderungen dieser Bedingungen",
        s8_p1='Wir können diese Bedingungen von Zeit zu Zeit überarbeiten. Die fortgesetzte Nutzung der Website nach Inkrafttreten von Änderungen gilt als Annahme der überarbeiteten Bedingungen. Wesentliche Änderungen werden auf unserer Seite <a href="{updates}">Neuigkeiten</a> vermerkt.',
        s9_h2="9. Kontakt",
        s9_p1='Fragen zu diesen Bedingungen können Sie über unsere <a href="{contact}">Kontaktseite</a> oder die unten stehende E-Mail-Adresse an uns richten.',
    ),
}

CONTENT["updates"] = {
    "en": dict(
        title="What's New | Formix",
        description="A changelog of what's new on Formix — new tools, language support, and site improvements.",
        og_title="What's New | Formix",
        og_description="See what's recently been added or improved on Formix.",
        h1="What's New",
        lead="A running log of new tools and improvements on Formix.",
        outro='Have an idea for a tool or feature you\'d like to see? Let us know on the <a href="{contact}">Contact page</a> — see our <a href="{about}">About</a> page for the principles guiding what we build next.',
        entries=[
            ("September 21, 2026", "XML Formatter, FAQ, and Contact page added",
             ["Added a new XML Formatter / Viewer tool alongside the JSON Formatter, with the same validation, tree view, and search experience.",
              "Added an FAQ page answering common questions about pricing, data handling, and browser support.",
              "Added a dedicated Contact page for bug reports and feature requests.",
              "Added a cookie/ad consent banner for visitors from the EEA, UK, and Switzerland."]),
            ("September 20, 2026", "Formix launches with the JSON Formatter",
             ["Launched Formix with our first tool: the JSON Formatter / Viewer, with validation, an indented syntax-highlighted tree, collapsing/expanding nodes, and key/value search.",
              "Added light and dark theme support with automatic detection.",
              "Published our Privacy Policy and About page.",
              "Added English, Korean, Japanese, and Chinese language support with automatic browser-language detection."]),
        ],
    ),
    "ko": dict(
        title="업데이트 소식 | Formix",
        description="Formix의 업데이트 소식 — 새로운 도구, 언어 지원, 사이트 개선 사항을 기록합니다.",
        og_title="업데이트 소식 | Formix",
        og_description="Formix에 최근 추가되거나 개선된 내용을 확인하세요.",
        h1="업데이트 소식",
        lead="Formix에 추가된 새로운 도구와 개선 사항을 시간순으로 기록합니다.",
        outro='추가되었으면 하는 도구나 기능이 있으신가요? <a href="{contact}">문의하기</a> 페이지로 알려주세요. 앞으로의 방향은 <a href="{about}">사이트 소개</a> 페이지에서 확인하실 수 있습니다.',
        entries=[
            ("2026년 9월 21일", "XML 포매터, FAQ, 문의하기 페이지 추가",
             ["JSON 포매터와 동일한 검증·트리 뷰·검색 경험을 제공하는 XML 포매터 / 뷰어를 새로 추가했습니다.",
              "요금, 데이터 처리 방식, 브라우저 지원 등 자주 묻는 질문에 답하는 FAQ 페이지를 추가했습니다.",
              "버그 제보와 기능 제안을 위한 문의하기 페이지를 별도로 만들었습니다.",
              "EEA·영국·스위스 방문자를 위한 쿠키·광고 동의 배너를 추가했습니다."]),
            ("2026년 9월 20일", "JSON 포매터와 함께 Formix 오픈",
             ["첫 번째 도구인 JSON 포매터 / 뷰어로 Formix를 시작했습니다. 유효성 검사, 들여쓰기·문법 강조 트리, 노드 접기/펼치기, 키·값 검색을 제공합니다.",
              "시스템 설정에 따라 자동으로 전환되는 라이트/다크 테마를 지원합니다.",
              "개인정보처리방침과 사이트 소개 페이지를 공개했습니다.",
              "영어를 기본으로 한국어·일본어·중국어를 지원하며, 브라우저 언어를 자동으로 감지합니다."]),
        ],
    ),
    "ja": dict(
        title="更新情報 | Formix",
        description="Formixの更新情報 — 新しいツール、言語対応、サイトの改善内容を記録します。",
        og_title="更新情報 | Formix",
        og_description="Formixに最近追加・改善された内容をご確認ください。",
        h1="更新情報",
        lead="Formixに追加された新しいツールや改善内容を時系列でまとめています。",
        outro='追加してほしいツールや機能がありましたら、<a href="{contact}">お問い合わせ</a>ページからお知らせください。今後の方針は<a href="{about}">サイト紹介</a>ページをご覧ください。',
        entries=[
            ("2026年9月21日", "XMLフォーマッター、よくある質問、お問い合わせページを追加",
             ["JSONフォーマッターと同じ検証・ツリービュー・検索機能を備えたXMLフォーマッター / ビューアを新たに追加しました。",
              "料金、データの取り扱い、対応ブラウザなど、よくある質問に答えるFAQページを追加しました。",
              "不具合報告や機能提案のための専用お問い合わせページを新設しました。",
              "EEA・英国・スイスからの訪問者向けにCookie・広告の同意バナーを追加しました。"]),
            ("2026年9月20日", "JSONフォーマッターとともにFormixがオープン",
             ["最初のツールであるJSONフォーマッター / ビューアでFormixを開始しました。検証、インデント付きシンタックスハイライトツリー、ノードの折りたたみ/展開、キー・値の検索に対応しています。",
              "システム設定に応じて自動切り替えされるライト/ダークテーマに対応しました。",
              "プライバシーポリシーとサイト紹介ページを公開しました。",
              "英語を基本に、韓国語・日本語・中国語に対応し、ブラウザの言語を自動検出します。"]),
        ],
    ),
    "zh": dict(
        title="更新日志 | Formix",
        description="Formix更新日志 — 记录新增工具、语言支持及网站改进内容。",
        og_title="更新日志 | Formix",
        og_description="查看Formix近期新增或改进的内容。",
        h1="更新日志",
        lead="按时间顺序记录Formix新增的工具和改进内容。",
        outro='有想让我们添加的工具或功能吗？欢迎通过<a href="{contact}">联系我们</a>页面告诉我们。未来的方向请参阅<a href="{about}">关于本站</a>页面。',
        entries=[
            ("2026年9月21日", "新增 XML 格式化工具、常见问题及联系我们页面",
             ["新增 XML 格式化 / 查看器工具，提供与 JSON 格式化工具相同的验证、树形视图和搜索体验。",
              "新增常见问题页面，解答关于费用、数据处理方式和浏览器支持等问题。",
              "新增独立的联系我们页面，用于错误反馈和功能建议。",
              "为来自 EEA、英国和瑞士的访客新增了 Cookie/广告同意横幅。"]),
            ("2026年9月20日", "Formix正式上线，推出 JSON 格式化工具",
             ["首个工具 JSON 格式化 / 查看器上线，支持验证、带缩进的语法高亮树形视图、节点折叠/展开以及键值搜索。",
              "支持根据系统设置自动切换的浅色/深色主题。",
              "发布了隐私政策和关于本站页面。",
              "默认提供英文，同时支持韩语、日语、中文，并可自动检测浏览器语言。"]),
        ],
    ),
    "es": dict(
        title="Novedades | Formix",
        description="Un registro de cambios de las novedades en Formix — nuevas herramientas, soporte de idiomas y mejoras del sitio.",
        og_title="Novedades | Formix",
        og_description="Mira qué se ha añadido o mejorado recientemente en Formix.",
        h1="Novedades",
        lead="Un registro continuo de nuevas herramientas y mejoras en Formix.",
        outro='¿Tienes una idea para una herramienta o función que te gustaría ver? Cuéntanos en nuestra <a href="{contact}">página de Contacto</a> — consulta nuestra página <a href="{about}">Acerca de</a> para los principios que guían lo que construimos a continuación.',
        entries=[
            ("21 de septiembre de 2026", "Se añadieron el Formateador XML, FAQ y la página de Contacto",
             ["Se añadió una nueva herramienta Formateador / Visor XML junto al Formateador JSON, con la misma validación, vista de árbol y experiencia de búsqueda.",
              "Se añadió una página de preguntas frecuentes que responde preguntas comunes sobre precios, manejo de datos y compatibilidad con navegadores.",
              "Se añadió una página de Contacto dedicada para reportes de errores y solicitudes de funciones.",
              "Se añadió un banner de consentimiento de cookies/anuncios para visitantes del EEE, Reino Unido y Suiza."]),
            ("20 de septiembre de 2026", "Formix se lanza con el Formateador JSON",
             ["Se lanzó Formix con nuestra primera herramienta: el Formateador / Visor JSON, con validación, un árbol indentado con resaltado de sintaxis, nodos colapsables/expandibles, y búsqueda de claves/valores.",
              "Se añadió soporte para temas claro y oscuro con detección automática.",
              "Se publicaron nuestra Política de privacidad y la página Acerca de.",
              "Se añadió soporte para inglés, coreano, japonés y chino con detección automática del idioma del navegador."]),
        ],
    ),
    "vi": dict(
        title="Cập nhật mới | Formix",
        description="Nhật ký những điều mới trên Formix — công cụ mới, hỗ trợ ngôn ngữ, và các cải tiến trang web.",
        og_title="Cập nhật mới | Formix",
        og_description="Xem những gì gần đây đã được thêm vào hoặc cải thiện trên Formix.",
        h1="Cập nhật mới",
        lead="Nhật ký liên tục về các công cụ mới và cải tiến trên Formix.",
        outro='Bạn có ý tưởng về một công cụ hoặc tính năng muốn thấy không? Cho chúng tôi biết qua <a href="{contact}">trang Liên hệ</a> — xem trang <a href="{about}">Giới thiệu</a> của chúng tôi để biết các nguyên tắc định hướng những gì chúng tôi xây dựng tiếp theo.',
        entries=[
            ("21 tháng 9 năm 2026", "Thêm Công cụ định dạng XML, FAQ và trang Liên hệ",
             ["Đã thêm công cụ Định dạng / Xem XML mới bên cạnh Định dạng JSON, với cùng trải nghiệm kiểm tra, xem dạng cây và tìm kiếm.",
              "Đã thêm trang Câu hỏi thường gặp trả lời các câu hỏi phổ biến về giá cả, xử lý dữ liệu và hỗ trợ trình duyệt.",
              "Đã thêm trang Liên hệ riêng để báo lỗi và đề xuất tính năng.",
              "Đã thêm banner đồng ý cookie/quảng cáo cho khách truy cập từ EEA, Vương quốc Anh và Thụy Sĩ."]),
            ("20 tháng 9 năm 2026", "Formix ra mắt với Công cụ định dạng JSON",
             ["Ra mắt Formix với công cụ đầu tiên: Định dạng / Xem JSON, với kiểm tra tính hợp lệ, cây có thụt lề tô màu cú pháp, thu/mở rộng nút, và tìm kiếm khóa/giá trị.",
              "Đã thêm hỗ trợ giao diện sáng và tối với tự động phát hiện.",
              "Đã công bố Chính sách bảo mật và trang Giới thiệu của chúng tôi.",
              "Đã thêm hỗ trợ tiếng Anh, Hàn, Nhật và Trung với tự động phát hiện ngôn ngữ trình duyệt."]),
        ],
    ),
    "pt": dict(
        title="Novidades | Formix",
        description="Um changelog das novidades no Formix — novas ferramentas, suporte de idiomas e melhorias no site.",
        og_title="Novidades | Formix",
        og_description="Veja o que foi adicionado ou melhorado recentemente no Formix.",
        h1="Novidades",
        lead="Um registro contínuo de novas ferramentas e melhorias no Formix.",
        outro='Tem uma ideia para uma ferramenta ou funcionalidade que gostaria de ver? Conte-nos na nossa <a href="{contact}">página de Contato</a> — veja nossa página <a href="{about}">Sobre</a> para os princípios que guiam o que construímos a seguir.',
        entries=[
            ("21 de setembro de 2026", "Adicionados o Formatador XML, FAQ e a página de Contato",
             ["Adicionada uma nova ferramenta Formatador / Visualizador XML junto ao Formatador JSON, com a mesma validação, visualização em árvore e experiência de busca.",
              "Adicionada uma página de Perguntas frequentes respondendo perguntas comuns sobre preços, tratamento de dados e suporte a navegadores.",
              "Adicionada uma página de Contato dedicada para relatórios de erros e solicitações de funcionalidades.",
              "Adicionado um banner de consentimento de cookies/anúncios para visitantes do EEE, Reino Unido e Suíça."]),
            ("20 de setembro de 2026", "Formix é lançado com o Formatador JSON",
             ["Lançamos o Formix com nossa primeira ferramenta: o Formatador / Visualizador JSON, com validação, uma árvore com recuo e destaque de sintaxe, nós recolhíveis/expansíveis, e busca de chave/valor.",
              "Adicionado suporte para temas claro e escuro com detecção automática.",
              "Publicamos nossa Política de privacidade e a página Sobre.",
              "Adicionado suporte para inglês, coreano, japonês e chinês com detecção automática do idioma do navegador."]),
        ],
    ),
    "id": dict(
        title="Pembaruan | Formix",
        description="Catatan perubahan tentang apa yang baru di Formix — alat baru, dukungan bahasa, dan peningkatan situs.",
        og_title="Pembaruan | Formix",
        og_description="Lihat apa yang baru-baru ini ditambahkan atau ditingkatkan di Formix.",
        h1="Pembaruan",
        lead="Catatan berkelanjutan tentang alat baru dan peningkatan di Formix.",
        outro='Punya ide untuk alat atau fitur yang ingin Anda lihat? Beri tahu kami di <a href="{contact}">halaman Kontak</a> kami — lihat halaman <a href="{about}">Tentang</a> kami untuk prinsip yang memandu apa yang kami bangun selanjutnya.',
        entries=[
            ("21 September 2026", "Ditambahkan Pemformat XML, FAQ, dan halaman Kontak",
             ["Menambahkan alat baru Pemformat / Penampil XML di samping Pemformat JSON, dengan pengalaman validasi, tampilan pohon, dan pencarian yang sama.",
              "Menambahkan halaman Pertanyaan Umum yang menjawab pertanyaan umum tentang harga, penanganan data, dan dukungan browser.",
              "Menambahkan halaman Kontak khusus untuk laporan bug dan permintaan fitur.",
              "Menambahkan spanduk persetujuan cookie/iklan untuk pengunjung dari EEA, Inggris, dan Swiss."]),
            ("20 September 2026", "Formix diluncurkan dengan Pemformat JSON",
             ["Meluncurkan Formix dengan alat pertama kami: Pemformat / Penampil JSON, dengan validasi, pohon beranotasi dengan penyorotan sintaks, node yang dapat dilipat/diperluas, dan pencarian kunci/nilai.",
              "Menambahkan dukungan tema terang dan gelap dengan deteksi otomatis.",
              "Menerbitkan Kebijakan Privasi dan halaman Tentang kami.",
              "Menambahkan dukungan bahasa Inggris, Korea, Jepang, dan Mandarin dengan deteksi otomatis bahasa browser."]),
        ],
    ),
    "de": dict(
        title="Neuigkeiten | Formix",
        description="Ein Änderungsprotokoll zu Neuigkeiten bei Formix — neue Tools, Sprachunterstützung und Website-Verbesserungen.",
        og_title="Neuigkeiten | Formix",
        og_description="Sehen Sie, was bei Formix kürzlich hinzugefügt oder verbessert wurde.",
        h1="Neuigkeiten",
        lead="Ein laufendes Protokoll neuer Tools und Verbesserungen bei Formix.",
        outro='Haben Sie eine Idee für ein Tool oder eine Funktion, die Sie gerne sehen würden? Teilen Sie es uns auf unserer <a href="{contact}">Kontaktseite</a> mit — die Prinzipien, die unsere weitere Entwicklung leiten, finden Sie auf unserer Seite <a href="{about}">Über uns</a>.',
        entries=[
            ("21. September 2026", "XML-Formatierer, FAQ und Kontaktseite hinzugefügt",
             ["Ein neues Tool XML-Formatierer / Viewer wurde neben dem JSON-Formatierer hinzugefügt, mit derselben Validierung, Baumansicht und Sucherfahrung.",
              "Eine FAQ-Seite wurde hinzugefügt, die häufige Fragen zu Preisen, Datenverarbeitung und Browser-Unterstützung beantwortet.",
              "Eine eigene Kontaktseite für Fehlermeldungen und Funktionswünsche wurde hinzugefügt.",
              "Ein Cookie-/Werbe-Einwilligungsbanner für Besucher aus dem EWR, dem Vereinigten Königreich und der Schweiz wurde hinzugefügt."]),
            ("20. September 2026", "Formix startet mit dem JSON-Formatierer",
             ["Formix wurde mit unserem ersten Tool gestartet: dem JSON-Formatierer / Viewer, mit Validierung, einem eingerückten, syntaxhervorgehobenen Baum, ein-/ausklappbaren Knoten und Schlüssel-/Wert-Suche.",
              "Unterstützung für Hell- und Dunkelmodus mit automatischer Erkennung wurde hinzugefügt.",
              "Unsere Datenschutzerklärung und die Seite Über uns wurden veröffentlicht.",
              "Unterstützung für Englisch, Koreanisch, Japanisch und Chinesisch mit automatischer Erkennung der Browsersprache wurde hinzugefügt."]),
        ],
    ),
}

CONTENT["notfound"] = {
    "en": dict(title="Page Not Found | Formix", eyebrow="404", h1="Page Not Found",
                p="The page you requested may have been removed or its address may have changed.", back="Back to Home"),
    "ko": dict(title="페이지를 찾을 수 없습니다 | Formix", eyebrow="404", h1="페이지를 찾을 수 없습니다",
                p="요청하신 페이지가 삭제되었거나 주소가 변경되었을 수 있습니다.", back="홈으로 돌아가기"),
    "ja": dict(title="ページが見つかりません | Formix", eyebrow="404", h1="ページが見つかりません",
                p="お探しのページは削除されたか、URLが変更された可能性があります。", back="ホームに戻る"),
    "zh": dict(title="页面未找到 | Formix", eyebrow="404", h1="页面未找到",
                p="您访问的页面可能已被删除或地址已更改。", back="返回首页"),
    "es": dict(title="Página no encontrada | Formix", eyebrow="404", h1="Página no encontrada",
                p="La página que solicitaste puede haber sido eliminada o su dirección puede haber cambiado.", back="Volver al inicio"),
    "vi": dict(title="Không tìm thấy trang | Formix", eyebrow="404", h1="Không tìm thấy trang",
                p="Trang bạn yêu cầu có thể đã bị xóa hoặc địa chỉ của nó đã thay đổi.", back="Về trang chủ"),
    "pt": dict(title="Página não encontrada | Formix", eyebrow="404", h1="Página não encontrada",
                p="A página solicitada pode ter sido removida ou seu endereço pode ter mudado.", back="Voltar ao início"),
    "id": dict(title="Halaman Tidak Ditemukan | Formix", eyebrow="404", h1="Halaman Tidak Ditemukan",
                p="Halaman yang Anda minta mungkin telah dihapus atau alamatnya mungkin telah berubah.", back="Kembali ke Beranda"),
    "de": dict(title="Seite nicht gefunden | Formix", eyebrow="404", h1="Seite nicht gefunden",
                p="Die von Ihnen angeforderte Seite wurde möglicherweise entfernt oder ihre Adresse hat sich geändert.", back="Zurück zur Startseite"),
}

CONTENT["tool"] = {
    "en": dict(
        title="JSON Formatter / Viewer - Validate and Beautify JSON Online | Formix",
        description="Online JSON formatter. Checks whether your input is valid JSON and displays it as a readable, syntax-highlighted tree. Supports collapsing/expanding and key/value search; your data is processed only in your browser.",
        keywords="JSON formatter, JSON viewer, JSON validator, JSON beautify, JSON pretty print, online JSON tool",
        og_title="JSON Formatter / Viewer | Formix",
        og_description="A free online JSON formatter with validation, a readable tree view, search, and collapse/expand.",
        jsonld_name="JSON Formatter / Viewer",
        jsonld_description="A free online tool that validates JSON strings and displays them as a readable tree. Includes search and collapse/expand.",
        h1="JSON Formatter / Viewer",
        lead="Enter a JSON string to validate it and see it laid out as an indented, syntax-highlighted tree. Your input is never sent to a server — everything happens in your browser.",
        btn_format="Format", btn_sample="Load sample", btn_clear="Clear",
        indent_label="Indent size", indent2="2-space indent", indent4="4-space indent", indenttab="Tab indent",
        btn_copy="Copy", btn_copy_minify="Copy minified", btn_download="Download .json",
        tabs_aria="Switch between input and output", tab_input="Input", tab_output="Output",
        status_idle="Enter some JSON",
        input_search_mode_label="Search mode", opt_contains="Contains", opt_exact_line="Exact (line)", opt_regex="Regex",
        input_search_placeholder="Search the input text…", prev_title="Previous match", next_title="Next match", clear_title="Clear search",
        input_placeholder="Paste your JSON string here. Missing quotes around keys or values will still be recognized where possible.",
        output_label="Output", expand_all="▾ Expand all", collapse_all="▸ Collapse all",
        opt_exact="Exact", output_search_placeholder="Search keys or values…",
        hint='Tip. When you stop typing, the input is validated and, if valid, the view switches automatically to the "Output" tab. The dot on the Output tab shows the current validity status. The ▾/▸ buttons for collapsing/expanding objects and arrays sit next to the line numbers (left margin) for easy clicking. The search box is focused automatically when the Output tab opens, and you can choose a search mode (Contains/Exact/Regex) to find keys and values the way you want. Line numbers on the output are renumbered to match only the visible lines, so you can still tell where you are even when parts of the structure are collapsed. The input panel has the same kind of search (Contains/Exact/Regex) so you can locate and highlight text directly in the original input. Press Enter (next) / Shift+Enter (previous) to move between matches. Even if some quotes (") are missing around keys or string values, we do our best to recognize the text as JSON anyway.',
        usage_h2="How to use this tool",
        usage_items=[
            "Paste a JSON string into the input box on the left and it's validated automatically, with the result rendered right away.",
            "If the JSON isn't valid, you'll get an approximate line/column for where the problem is.",
            'Clicking "Format" also reformats the input box\'s content using the selected indent size.',
            'When the output is long, use "Collapse all" to get an overview of the structure first, then expand only the nodes you need with the ▾/▸ buttons next to the line numbers.',
            "Everything happens in your browser — the data you enter is never sent to a server.",
            'Even if quotes are missing around some keys or string values, we do our best to auto-correct and recognize them. In that case the status badge shows "Fixed", and the corrected lines are highlighted in the input panel\'s line numbers.',
            'Once your input is confirmed valid (or fixed), the view switches automatically to the "Output" tab and focus moves to the search box so you can start typing right away.',
            'Choose a search mode: "Contains" (partial match), "Exact" (exact match), or "Regex" (regular expression).',
            "The input panel has the same search feature (Contains/Exact/Regex, previous/next navigation, highlighting) so you can search directly in the original text.",
        ],
        tips_h2="Related tips",
        tips_items=[
            'Use "Copy minified" instead of "Copy" when you need a compact payload for an API request or a config value — no extra whitespace or line breaks.',
            "Switch the indent size to Tab if your project's style guide calls for tabs instead of spaces.",
            "The Regex search mode can match a pattern across every key or value at once — handy for auditing IDs, dates, or emails in a large document.",
            "For deeply nested JSON, click \"Collapse all\" first to see the overall shape, then expand only the branch you actually need to inspect.",
        ],
    ),
    "ko": dict(
        title="JSON 포매터 / 뷰어 - 온라인 JSON 검증 및 정리 | Formix",
        description="온라인 JSON 포매터. 입력한 문자열이 올바른 JSON인지 검증하고, 들여쓰기와 문법 강조를 적용해 가독성 좋게 보여줍니다. 트리 접기/펼치기와 키·값 검색을 지원하며 데이터는 브라우저 안에서만 처리됩니다.",
        keywords="JSON 포매터, JSON 뷰어, JSON validator, JSON beautify, JSON pretty print, 온라인 JSON 도구",
        og_title="JSON 포매터 / 뷰어 | Formix",
        og_description="JSON 문자열 유효성 검사와 가독성 좋은 트리 뷰, 검색, 접기/펼치기를 지원하는 무료 온라인 JSON 포매터.",
        jsonld_name="JSON 포매터 / 뷰어",
        jsonld_description="JSON 문자열의 유효성을 검사하고 보기 좋은 트리 형태로 정리해주는 무료 온라인 도구. 검색과 접기/펼치기 기능을 제공합니다.",
        h1="JSON 포매터 / 뷰어",
        lead="JSON 문자열을 입력하면 유효성을 검사하고, 들여쓰기와 문법 강조가 적용된 트리로 정리해 보여줍니다. 입력값은 서버로 전송되지 않고 브라우저 안에서만 처리됩니다.",
        btn_format="정렬(Format)", btn_sample="예시 불러오기", btn_clear="지우기",
        indent_label="들여쓰기 크기", indent2="들여쓰기 2칸", indent4="들여쓰기 4칸", indenttab="들여쓰기 Tab",
        btn_copy="복사", btn_copy_minify="압축 복사", btn_download=".json 다운로드",
        tabs_aria="입력/결과 전환", tab_input="입력", tab_output="결과",
        status_idle="JSON을 입력해주세요",
        input_search_mode_label="검색 방식", opt_contains="포함", opt_exact_line="일치(줄)", opt_regex="정규식",
        input_search_placeholder="입력한 텍스트에서 검색…", prev_title="이전 일치 항목", next_title="다음 일치 항목", clear_title="검색어 지우기",
        input_placeholder="여기에 JSON 문자열을 붙여넣으세요. 키나 값의 따옴표가 빠져 있어도 최대한 인식합니다.",
        output_label="결과", expand_all="▾ 모두 펼치기", collapse_all="▸ 모두 접기",
        opt_exact="일치", output_search_placeholder="키 또는 값 검색…",
        hint='Tip. 입력을 멈추면 유효성을 검사해 정상이면 자동으로 "결과" 탭으로 전환합니다. 결과 탭의 점은 현재 유효성 상태를 보여줍니다. 객체/배열을 접거나 펼치는 ▾/▸ 버튼은 줄 번호 옆(왼쪽 여백)에 있어 클릭하기 편합니다. 검색창은 결과 탭이 열리면 자동으로 포커스되며, 검색 방식(포함/일치/정규식)을 선택해 원하는 방식으로 키와 값을 찾을 수 있습니다. 결과 화면 왼쪽의 줄 번호는 접기/펼치기 상태에 맞춰 보이는 줄만 다시 매겨져, 구조가 접혀 있어도 위치를 가늠하기 쉽습니다. 입력창에도 동일한 방식의 검색(포함/일치/정규식)이 있어 원본 텍스트에서 바로 위치를 찾고 강조 표시로 확인할 수 있습니다. Enter(다음) / Shift+Enter(이전)로 일치 항목을 이동할 수 있습니다. 키나 문자열 값의 큰따옴표(")가 일부 빠져 있어도 가능한 한 JSON으로 인식해서 보여줍니다.',
        usage_h2="이 도구는 이렇게 사용하세요",
        usage_items=[
            "왼쪽 입력창에 JSON 문자열을 붙여넣으면 자동으로 유효성을 검사하고 결과를 그려줍니다.",
            "유효하지 않은 JSON이면 오류가 발생한 대략적인 줄/열 위치를 함께 알려줍니다.",
            '"정렬(Format)" 버튼을 누르면 입력창의 내용도 선택한 들여쓰기 기준으로 정리됩니다.',
            '결과가 길 때는 "모두 접기"로 전체 구조를 먼저 훑어본 뒤, 줄 번호 옆의 ▾/▸ 버튼으로 필요한 노드만 펼쳐볼 수 있습니다.',
            "모든 처리는 브라우저 안에서만 이뤄지며, 입력한 데이터는 서버로 전송되지 않습니다.",
            '키나 문자열 값의 큰따옴표가 일부 누락된 경우에도 최대한 자동으로 보정해서 인식합니다. 이 경우 상태 배지에 "보정됨"으로 표시되고, 입력창 왼쪽 줄 번호 중 보정이 일어난 줄이 강조 표시됩니다.',
            '입력을 마치고 결과가 정상(유효 또는 보정됨)으로 확인되면 자동으로 "결과" 탭으로 전환되고, 검색창에 바로 입력할 수 있도록 포커스가 이동합니다.',
            '검색 방식을 "포함"(부분 일치), "일치"(정확히 같은 값), "정규식"(정규 표현식) 중에서 선택할 수 있습니다.',
            "입력창 상단에도 같은 검색 기능(포함/일치/정규식, 이전·다음 이동, 강조 표시)이 있어 원본 텍스트에서 바로 찾을 수 있습니다.",
        ],
        tips_h2="관련 팁",
        tips_items=[
            "API 요청 바디나 설정 값처럼 공백 없는 압축된 형태가 필요할 때는 '복사' 대신 '압축 복사'를 사용해보세요.",
            "프로젝트 스타일 가이드가 탭을 요구한다면 들여쓰기 크기를 'Tab'으로 바꿔보세요.",
            "정규식 검색 모드는 문서 전체에서 특정 패턴의 키나 값을 한 번에 찾을 때 유용합니다. (예: 아이디, 날짜, 이메일 형식 점검)",
            "깊게 중첩된 JSON은 먼저 '모두 접기'로 전체 구조를 파악한 뒤, 실제로 살펴봐야 할 부분만 펼쳐보면 훨씬 편합니다.",
        ],
    ),
    "ja": dict(
        title="JSONフォーマッター / ビューア - オンラインJSON検証・整形 | Formix",
        description="オンラインJSONフォーマッター。入力した文字列が正しいJSONかを検証し、インデントとシンタックスハイライトを適用して読みやすく表示します。折りたたみ/展開とキー・値検索に対応し、データはブラウザ内でのみ処理されます。",
        keywords="JSONフォーマッター, JSONビューア, JSON validator, JSON beautify, JSON pretty print, オンラインJSONツール",
        og_title="JSONフォーマッター / ビューア | Formix",
        og_description="JSON文字列の検証と読みやすいツリービュー、検索、折りたたみ/展開に対応した無料オンラインJSONフォーマッター。",
        jsonld_name="JSONフォーマッター / ビューア",
        jsonld_description="JSON文字列の妥当性を検証し、読みやすいツリー形式に整理する無料オンラインツール。検索と折りたたみ/展開機能を提供します。",
        h1="JSONフォーマッター / ビューア",
        lead="JSON文字列を入力すると妥当性を検証し、インデントとシンタックスハイライトを適用したツリーで表示します。入力値はサーバーに送信されずブラウザ内でのみ処理されます。",
        btn_format="整列(Format)", btn_sample="サンプルを読み込む", btn_clear="クリア",
        indent_label="インデントサイズ", indent2="インデント2桁", indent4="インデント4桁", indenttab="インデントTab",
        btn_copy="コピー", btn_copy_minify="圧縮コピー", btn_download=".jsonをダウンロード",
        tabs_aria="入力/出力の切り替え", tab_input="入力", tab_output="出力",
        status_idle="JSONを入力してください",
        input_search_mode_label="検索方式", opt_contains="部分一致", opt_exact_line="完全一致(行)", opt_regex="正規表現",
        input_search_placeholder="入力テキストを検索…", prev_title="前の一致項目", next_title="次の一致項目", clear_title="検索語をクリア",
        input_placeholder="ここにJSON文字列を貼り付けてください。キーや値の引用符が一部欠けていてもできるだけ認識します。",
        output_label="出力", expand_all="▾ すべて展開", collapse_all="▸ すべて折りたたむ",
        opt_exact="完全一致", output_search_placeholder="キーまたは値を検索…",
        hint='Tip. 入力を止めると検証が行われ、正常なら自動的に「出力」タブに切り替わります。出力タブのドットは現在の妥当性ステータスを示します。オブジェクト/配列を折りたたむ/展開する▾/▸ボタンは行番号の隣(左余白)にあり、クリックしやすくなっています。検索ボックスは出力タブが開くと自動的にフォーカスされ、検索方式(部分一致/完全一致/正規表現)を選べば希望の方法でキーと値を探せます。出力画面左側の行番号は折りたたみ状態に合わせて表示中の行だけに振り直されるため、構造が折りたたまれていても位置を把握しやすくなっています。入力ボックスにも同じ方式の検索(部分一致/完全一致/正規表現)があり、元のテキストで直接位置を探してハイライトで確認できます。Enter(次へ) / Shift+Enter(前へ)で一致項目を移動できます。キーや文字列値の引用符(")が一部欠けていても、できるだけJSONとして認識して表示します。',
        usage_h2="このツールの使い方",
        usage_items=[
            "左側の入力ボックスにJSON文字列を貼り付けると、自動的に妥当性を検証し結果を描画します。",
            "無効なJSONの場合は、エラーが発生したおおまかな行/列位置も合わせてお知らせします。",
            "「整列(Format)」ボタンを押すと、入力ボックスの内容も選択したインデント基準で整形されます。",
            "結果が長い場合は「すべて折りたたむ」で全体の構造を先に把握し、行番号隣の▾/▸ボタンで必要なノードだけ展開できます。",
            "すべての処理はブラウザ内でのみ行われ、入力したデータがサーバーに送信されることはありません。",
            "キーや文字列値の引用符が一部欠けている場合でも、できるだけ自動で修正して認識します。この場合、ステータスバッジに「修正済み」と表示され、入力ボックス左側の行番号のうち修正が行われた行が強調表示されます。",
            "入力を終えて結果が正常(有効または修正済み)と確認されると自動的に「出力」タブに切り替わり、検索ボックスにすぐ入力できるようフォーカスが移動します。",
            "検索方式を「部分一致」(部分一致)、「完全一致」(完全一致)、「正規表現」(正規表現)から選べます。",
            "入力ボックス上部にも同じ検索機能(部分一致/完全一致/正規表現、前・次移動、ハイライト表示)があり、元のテキストで直接検索できます。",
        ],
        tips_h2="関連のヒント",
        tips_items=[
            "APIリクエストの本文や設定値など、余白のないコンパクトな形式が必要なときは「コピー」の代わりに「圧縮コピー」を使いましょう。",
            "プロジェクトのスタイルガイドでタブが指定されている場合は、インデントサイズを「Tab」に切り替えてください。",
            "正規表現の検索モードは、文書全体から特定パターンのキーや値をまとめて探したいとき(IDや日付、メール形式のチェックなど)に便利です。",
            "深くネストされたJSONは、まず「すべて折りたたむ」で全体の構造を把握してから、実際に確認したい部分だけ展開すると効率的です。",
        ],
    ),
    "zh": dict(
        title="JSON 格式化 / 查看器 - 在线 JSON 验证与整理 | Formix",
        description="在线 JSON 格式化工具。检查输入的字符串是否为有效 JSON，并带缩进和语法高亮清晰展示。支持折叠/展开以及键值搜索，数据仅在浏览器中处理。",
        keywords="JSON 格式化, JSON 查看器, JSON validator, JSON beautify, JSON pretty print, 在线 JSON 工具",
        og_title="JSON 格式化 / 查看器 | Formix",
        og_description="支持验证、易读树形视图、搜索及折叠/展开的免费在线 JSON 格式化工具。",
        jsonld_name="JSON 格式化 / 查看器",
        jsonld_description="验证 JSON 字符串并以易读树形结构整理展示的免费在线工具。提供搜索与折叠/展开功能。",
        h1="JSON 格式化 / 查看器",
        lead="输入 JSON 字符串即可验证其有效性，并以带缩进和语法高亮的树形结构展示。输入内容不会发送到服务器，仅在浏览器中处理。",
        btn_format="格式化(Format)", btn_sample="加载示例", btn_clear="清除",
        indent_label="缩进大小", indent2="2 空格缩进", indent4="4 空格缩进", indenttab="Tab 缩进",
        btn_copy="复制", btn_copy_minify="复制压缩版", btn_download="下载 .json",
        tabs_aria="切换输入/输出", tab_input="输入", tab_output="输出",
        status_idle="请输入 JSON",
        input_search_mode_label="搜索方式", opt_contains="包含", opt_exact_line="精确(整行)", opt_regex="正则表达式",
        input_search_placeholder="在输入文本中搜索…", prev_title="上一个匹配项", next_title="下一个匹配项", clear_title="清除搜索词",
        input_placeholder="在此粘贴 JSON 字符串。即使键或值的引号缺失，也会尽可能识别。",
        output_label="输出", expand_all="▾ 全部展开", collapse_all="▸ 全部折叠",
        opt_exact="精确", output_search_placeholder="搜索键或值…",
        hint='提示：停止输入后会自动验证，若有效则自动切换到"输出"标签页。输出标签上的圆点表示当前的有效性状态。用于折叠/展开对象/数组的 ▾/▸ 按钮位于行号旁边(左侧留白)，方便点击。打开输出标签页时搜索框会自动获得焦点，可选择搜索模式(包含/精确/正则)按需要查找键和值。输出区域左侧的行号会根据折叠状态重新编号，只显示当前可见的行，即使结构被折叠也能轻松定位。输入面板也有相同方式的搜索(包含/精确/正则)，可直接在原始文本中定位并高亮显示。按 Enter(下一个) / Shift+Enter(上一个) 可在匹配项之间移动。即使键或字符串值的引号(")有部分缺失，也会尽可能识别为 JSON 并展示。',
        usage_h2="使用方法",
        usage_items=[
            "在左侧输入框中粘贴 JSON 字符串，将自动验证并绘制结果。",
            "如果 JSON 无效，会告知您大致的错误行/列位置。",
            '点击"格式化(Format)"按钮后，输入框中的内容也会按所选缩进量重新整理。',
            '当结果较长时，可先用"全部折叠"浏览整体结构，再通过行号旁的 ▾/▸ 按钮展开需要的节点。',
            "所有处理都在浏览器中进行，输入的数据不会发送到服务器。",
            "即使键或字符串值的引号有部分缺失，也会尽可能自动修正并识别。此时状态彽形会显示为“已修正”，并在输入框左侧的行号中高亮显示发生修正的行。",
            '输入完成且结果确认正常(有效或已修正)后，会自动切换到"输出"标签页，并将焦点移至搜索框以便直接输入。',
            '可在"包含"(部分匹配)、"精确"(完全匹配)、"正则"(正则表达式)中选择搜索模式。',
            "输入框上方也有相同的搜索功能(包含/精确/正则、上一个·下一个导航、高亮显示)，可直接在原始文本中搜索。",
        ],
        tips_h2="相关小技巧",
        tips_items=[
            "需要用于 API 请求体或配置项等不含多余空白的紧凑格式时，使用“复制压缩版”而不是“复制”。",
            "如果项目的代码风格要求使用 Tab，可将缩进大小切换为 Tab。",
            "正则表达式搜索模式可以一次性匹配整个文档中符合特定模式的键或值，适合用于检查 ID、日期或邮箱格式。",
            "面对层级很深的 JSON，建议先点击“全部折叠”了解整体结构，再展开真正需要查看的部分。",
        ],
    ),
    "es": dict(
        title="Formateador / Visor JSON - Valida y Embellece JSON en Línea | Formix",
        description="Formateador JSON en línea. Verifica si tu entrada es JSON válido y lo muestra como un árbol legible con resaltado de sintaxis. Soporta colapsar/expandir y búsqueda de claves/valores; tus datos se procesan solo en tu navegador.",
        keywords="formateador json, visor json, validador json, embellecer json, json pretty print, herramienta json en línea",
        og_title="Formateador / Visor JSON | Formix",
        og_description="Un formateador JSON en línea gratuito con validación, vista de árbol legible, búsqueda y colapsar/expandir.",
        jsonld_name="Formateador / Visor JSON",
        jsonld_description="Una herramienta en línea gratuita que valida cadenas JSON y las muestra como un árbol legible. Incluye búsqueda y colapsar/expandir.",
        h1="Formateador / Visor JSON",
        lead="Ingresa una cadena JSON para validarla y verla organizada como un árbol con sangría y resaltado de sintaxis. Tu entrada nunca se envía a un servidor — todo ocurre en tu navegador.",
        btn_format="Formatear", btn_sample="Cargar ejemplo", btn_clear="Limpiar",
        indent_label="Tamaño de sangría", indent2="Sangría de 2 espacios", indent4="Sangría de 4 espacios", indenttab="Sangría con Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar minificado", btn_download="Descargar .json",
        tabs_aria="Alternar entre entrada y salida", tab_input="Entrada", tab_output="Salida",
        status_idle="Ingresa un JSON",
        input_search_mode_label="Modo de búsqueda", opt_contains="Contiene", opt_exact_line="Exacto (línea)", opt_regex="Regex",
        input_search_placeholder="Buscar en el texto de entrada…", prev_title="Coincidencia anterior", next_title="Siguiente coincidencia", clear_title="Limpiar búsqueda",
        input_placeholder="Pega tu cadena JSON aquí. Las comillas faltantes alrededor de claves o valores se reconocerán cuando sea posible.",
        output_label="Salida", expand_all="▾ Expandir todo", collapse_all="▸ Colapsar todo",
        opt_exact="Exacto", output_search_placeholder="Buscar claves o valores…",
        hint='Consejo. Cuando dejas de escribir, la entrada se valida y, si es válida, la vista cambia automáticamente a la pestaña "Salida". El punto en la pestaña Salida muestra el estado de validez actual. Los botones ▾/▸ para colapsar/expandir objetos y arreglos están junto a los números de línea (margen izquierdo) para facilitar el clic. El cuadro de búsqueda recibe el foco automáticamente cuando se abre la pestaña Salida, y puedes elegir un modo de búsqueda (Contiene/Exacto/Regex) para encontrar claves y valores como quieras. Los números de línea en la salida se renumeran para coincidir solo con las líneas visibles, así puedes seguir ubicándote aunque partes de la estructura estén colapsadas. El panel de entrada tiene el mismo tipo de búsqueda (Contiene/Exacto/Regex) para que puedas localizar y resaltar texto directamente en la entrada original. Presiona Enter (siguiente) / Shift+Enter (anterior) para moverte entre coincidencias. Aunque falten algunas comillas (") alrededor de claves o valores de cadena, hacemos lo posible por reconocer el texto como JSON de todos modos.',
        usage_h2="Cómo usar esta herramienta",
        usage_items=[
            "Pega una cadena JSON en el cuadro de entrada de la izquierda y se valida automáticamente, mostrando el resultado al instante.",
            "Si el JSON no es válido, obtendrás una línea/columna aproximada de dónde está el problema.",
            'Hacer clic en "Formatear" también reformatea el contenido del cuadro de entrada usando el tamaño de sangría seleccionado.',
            'Cuando la salida es larga, usa "Colapsar todo" para obtener una vista general de la estructura primero, luego expande solo los nodos que necesitas con los botones ▾/▸ junto a los números de línea.',
            "Todo ocurre en tu navegador — los datos que ingresas nunca se envían a un servidor.",
            'Aunque falten comillas alrededor de algunas claves o valores de cadena, hacemos lo posible por autocorregirlas y reconocerlas. En ese caso la insignia de estado muestra "Corregido", y las líneas corregidas se resaltan en los números de línea del panel de entrada.',
            'Una vez que tu entrada se confirma válida (o corregida), la vista cambia automáticamente a la pestaña "Salida" y el foco se mueve al cuadro de búsqueda para que puedas empezar a escribir de inmediato.',
            'Elige un modo de búsqueda: "Contiene" (coincidencia parcial), "Exacto" (coincidencia exacta), o "Regex" (expresión regular).',
            "El panel de entrada tiene la misma función de búsqueda (Contiene/Exacto/Regex, navegación anterior/siguiente, resaltado) para que puedas buscar directamente en el texto original.",
        ],
        tips_h2="Consejos relacionados",
        tips_items=[
            'Usa "Copiar minificado" en lugar de "Copiar" cuando necesites un payload compacto para una solicitud de API o un valor de configuración — sin espacios ni saltos de línea extra.',
            "Cambia el tamaño de sangría a Tab si la guía de estilo de tu proyecto requiere tabs en lugar de espacios.",
            "El modo de búsqueda Regex puede coincidir con un patrón en cada clave o valor a la vez — útil para auditar IDs, fechas o correos en un documento grande.",
            'Para JSON profundamente anidado, haz clic primero en "Colapsar todo" para ver la forma general, luego expande solo la rama que realmente necesitas inspeccionar.',
        ],
    ),
    "vi": dict(
        title="Định dạng / Xem JSON - Kiểm tra và Làm đẹp JSON Trực tuyến | Formix",
        description="Công cụ định dạng JSON trực tuyến. Kiểm tra xem nội dung bạn nhập có phải JSON hợp lệ không và hiển thị dưới dạng cây dễ đọc, có tô màu cú pháp. Hỗ trợ thu/mở rộng và tìm kiếm khóa/giá trị; dữ liệu của bạn chỉ được xử lý trong trình duyệt.",
        keywords="định dạng json, xem json, kiểm tra json, làm đẹp json, json pretty print, công cụ json trực tuyến",
        og_title="Định dạng / Xem JSON | Formix",
        og_description="Công cụ định dạng JSON trực tuyến miễn phí với kiểm tra tính hợp lệ, xem dạng cây dễ đọc, tìm kiếm và thu/mở rộng.",
        jsonld_name="Định dạng / Xem JSON",
        jsonld_description="Công cụ trực tuyến miễn phí kiểm tra chuỗi JSON và hiển thị dưới dạng cây dễ đọc. Bao gồm tìm kiếm và thu/mở rộng.",
        h1="Định dạng / Xem JSON",
        lead="Nhập một chuỗi JSON để kiểm tra tính hợp lệ và xem nó được trình bày dưới dạng cây có thụt lề, tô màu cú pháp. Nội dung bạn nhập không bao giờ được gửi lên máy chủ — mọi thứ diễn ra trong trình duyệt của bạn.",
        btn_format="Định dạng", btn_sample="Tải ví dụ", btn_clear="Xóa",
        indent_label="Kích thước thụt lề", indent2="Thụt lề 2 khoảng trắng", indent4="Thụt lề 4 khoảng trắng", indenttab="Thụt lề Tab",
        btn_copy="Sao chép", btn_copy_minify="Sao chép rút gọn", btn_download="Tải xuống .json",
        tabs_aria="Chuyển đổi giữa nhập và kết quả", tab_input="Nhập", tab_output="Kết quả",
        status_idle="Hãy nhập JSON",
        input_search_mode_label="Chế độ tìm kiếm", opt_contains="Chứa", opt_exact_line="Chính xác (dòng)", opt_regex="Regex",
        input_search_placeholder="Tìm trong văn bản nhập…", prev_title="Kết quả trước", next_title="Kết quả tiếp theo", clear_title="Xóa tìm kiếm",
        input_placeholder="Dán chuỗi JSON của bạn vào đây. Dấu ngoặc kép bị thiếu quanh khóa hoặc giá trị vẫn sẽ được nhận diện khi có thể.",
        output_label="Kết quả", expand_all="▾ Mở rộng tất cả", collapse_all="▸ Thu gọn tất cả",
        opt_exact="Chính xác", output_search_placeholder="Tìm khóa hoặc giá trị…",
        hint='Mẹo. Khi bạn dừng gõ, nội dung nhập sẽ được kiểm tra và nếu hợp lệ, màn hình sẽ tự động chuyển sang tab "Kết quả". Dấu chấm trên tab Kết quả cho biết trạng thái hợp lệ hiện tại. Các nút ▾/▸ để thu/mở rộng đối tượng và mảng nằm cạnh số dòng (lề trái) để dễ nhấp. Hộp tìm kiếm tự động được focus khi tab Kết quả mở, và bạn có thể chọn chế độ tìm kiếm (Chứa/Chính xác/Regex) để tìm khóa và giá trị theo cách bạn muốn. Số dòng ở kết quả được đánh số lại chỉ theo các dòng đang hiển thị, nên bạn vẫn biết vị trí ngay cả khi một phần cấu trúc bị thu gọn. Khung nhập cũng có cùng loại tìm kiếm (Chứa/Chính xác/Regex) để bạn định vị và tô sáng trực tiếp trong nội dung gốc. Nhấn Enter (tiếp theo) / Shift+Enter (trước đó) để di chuyển giữa các kết quả khớp. Dù một số dấu ngoặc kép (") quanh khóa hoặc giá trị chuỗi bị thiếu, chúng tôi vẫn cố gắng nhận diện văn bản đó là JSON.',
        usage_h2="Cách sử dụng công cụ này",
        usage_items=[
            "Dán một chuỗi JSON vào khung nhập bên trái và nó sẽ được kiểm tra tự động, kết quả hiển thị ngay lập tức.",
            "Nếu JSON không hợp lệ, bạn sẽ nhận được dòng/cột gần đúng của vị trí gặp vấn đề.",
            'Nhấp "Định dạng" cũng sẽ định dạng lại nội dung trong khung nhập theo kích thước thụt lề đã chọn.',
            'Khi kết quả dài, dùng "Thu gọn tất cả" để xem tổng quan cấu trúc trước, sau đó chỉ mở rộng các nút cần thiết bằng nút ▾/▸ cạnh số dòng.',
            "Mọi thứ diễn ra trong trình duyệt của bạn — dữ liệu bạn nhập không bao giờ được gửi lên máy chủ.",
            'Dù thiếu dấu ngoặc kép quanh một số khóa hoặc giá trị chuỗi, chúng tôi vẫn cố gắng tự sửa và nhận diện. Khi đó huy hiệu trạng thái sẽ hiển thị "Đã sửa", và các dòng được sửa sẽ được tô sáng trong số dòng của khung nhập.',
            'Khi nội dung nhập được xác nhận hợp lệ (hoặc đã sửa), màn hình tự động chuyển sang tab "Kết quả" và focus chuyển đến hộp tìm kiếm để bạn có thể gõ ngay.',
            'Chọn chế độ tìm kiếm: "Chứa" (khớp một phần), "Chính xác" (khớp hoàn toàn), hoặc "Regex" (biểu thức chính quy).',
            "Khung nhập có cùng tính năng tìm kiếm (Chứa/Chính xác/Regex, điều hướng trước/tiếp theo, tô sáng) để bạn tìm trực tiếp trong văn bản gốc.",
        ],
        tips_h2="Mẹo liên quan",
        tips_items=[
            'Dùng "Sao chép rút gọn" thay vì "Sao chép" khi cần payload gọn cho yêu cầu API hoặc giá trị cấu hình — không có khoảng trắng hay xuống dòng dư.',
            "Chuyển kích thước thụt lề sang Tab nếu quy chuẩn code của dự án bạn yêu cầu dùng tab thay vì khoảng trắng.",
            "Chế độ tìm kiếm Regex có thể khớp một mẫu trên toàn bộ khóa hoặc giá trị cùng lúc — tiện để kiểm tra ID, ngày tháng hoặc email trong một tài liệu lớn.",
            'Với JSON lồng nhiều cấp, hãy nhấp "Thu gọn tất cả" trước để xem hình dạng tổng thể, rồi chỉ mở rộng nhánh bạn thực sự cần kiểm tra.',
        ],
    ),
    "pt": dict(
        title="Formatador / Visualizador JSON - Validar e Formatar JSON Online | Formix",
        description="Formatador JSON online. Verifica se sua entrada é um JSON válido e a exibe como uma árvore legível com destaque de sintaxe. Suporta recolher/expandir e busca de chave/valor; seus dados são processados apenas no seu navegador.",
        keywords="formatador json, visualizador json, validador json, embelezar json, json pretty print, ferramenta json online",
        og_title="Formatador / Visualizador JSON | Formix",
        og_description="Um formatador JSON online gratuito com validação, visualização em árvore legível, busca e recolher/expandir.",
        jsonld_name="Formatador / Visualizador JSON",
        jsonld_description="Uma ferramenta online gratuita que valida strings JSON e as exibe como uma árvore legível. Inclui busca e recolher/expandir.",
        h1="Formatador / Visualizador JSON",
        lead="Insira uma string JSON para validá-la e vê-la organizada como uma árvore com recuo e destaque de sintaxe. Sua entrada nunca é enviada a um servidor — tudo acontece no seu navegador.",
        btn_format="Formatar", btn_sample="Carregar exemplo", btn_clear="Limpar",
        indent_label="Tamanho do recuo", indent2="Recuo de 2 espaços", indent4="Recuo de 4 espaços", indenttab="Recuo com Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar minificado", btn_download="Baixar .json",
        tabs_aria="Alternar entre entrada e saída", tab_input="Entrada", tab_output="Saída",
        status_idle="Insira um JSON",
        input_search_mode_label="Modo de busca", opt_contains="Contém", opt_exact_line="Exato (linha)", opt_regex="Regex",
        input_search_placeholder="Buscar no texto de entrada…", prev_title="Correspondência anterior", next_title="Próxima correspondência", clear_title="Limpar busca",
        input_placeholder="Cole sua string JSON aqui. Aspas faltantes em chaves ou valores ainda serão reconhecidas quando possível.",
        output_label="Saída", expand_all="▾ Expandir tudo", collapse_all="▸ Recolher tudo",
        opt_exact="Exato", output_search_placeholder="Buscar chaves ou valores…",
        hint='Dica. Quando você para de digitar, a entrada é validada e, se válida, a visualização muda automaticamente para a aba "Saída". O ponto na aba Saída mostra o status de validade atual. Os botões ▾/▸ para recolher/expandir objetos e arrays ficam junto aos números de linha (margem esquerda) para facilitar o clique. A caixa de busca recebe foco automaticamente quando a aba Saída abre, e você pode escolher um modo de busca (Contém/Exato/Regex) para encontrar chaves e valores como quiser. Os números de linha na saída são renumerados para corresponder apenas às linhas visíveis, então você ainda sabe onde está mesmo com partes da estrutura recolhidas. O painel de entrada tem o mesmo tipo de busca (Contém/Exato/Regex) para que você localize e destaque texto diretamente na entrada original. Pressione Enter (próximo) / Shift+Enter (anterior) para navegar entre as correspondências. Mesmo que faltem algumas aspas (") em chaves ou valores de string, fazemos o possível para reconhecer o texto como JSON mesmo assim.',
        usage_h2="Como usar esta ferramenta",
        usage_items=[
            "Cole uma string JSON na caixa de entrada à esquerda e ela é validada automaticamente, com o resultado renderizado imediatamente.",
            "Se o JSON não for válido, você receberá uma linha/coluna aproximada de onde está o problema.",
            'Clicar em "Formatar" também reformata o conteúdo da caixa de entrada usando o tamanho de recuo selecionado.',
            'Quando a saída for longa, use "Recolher tudo" para ter uma visão geral da estrutura primeiro, depois expanda apenas os nós necessários com os botões ▾/▸ junto aos números de linha.',
            "Tudo acontece no seu navegador — os dados que você insere nunca são enviados a um servidor.",
            'Mesmo que faltem aspas em algumas chaves ou valores de string, fazemos o possível para autocorrigir e reconhecê-las. Nesse caso o indicador de status mostra "Corrigido", e as linhas corrigidas são destacadas nos números de linha do painel de entrada.',
            'Depois que sua entrada é confirmada como válida (ou corrigida), a visualização muda automaticamente para a aba "Saída" e o foco vai para a caixa de busca para você começar a digitar imediatamente.',
            'Escolha um modo de busca: "Contém" (correspondência parcial), "Exato" (correspondência exata), ou "Regex" (expressão regular).',
            "O painel de entrada tem a mesma função de busca (Contém/Exato/Regex, navegação anterior/próximo, destaque) para você buscar diretamente no texto original.",
        ],
        tips_h2="Dicas relacionadas",
        tips_items=[
            'Use "Copiar minificado" em vez de "Copiar" quando precisar de um payload compacto para uma requisição de API ou valor de configuração — sem espaços ou quebras de linha extras.',
            "Mude o tamanho do recuo para Tab se o guia de estilo do seu projeto exigir tabs em vez de espaços.",
            "O modo de busca Regex pode corresponder a um padrão em todas as chaves ou valores de uma vez — útil para auditar IDs, datas ou e-mails em um documento grande.",
            'Para JSON profundamente aninhado, clique em "Recolher tudo" primeiro para ver a forma geral, depois expanda apenas o ramo que você realmente precisa inspecionar.',
        ],
    ),
    "id": dict(
        title="Pemformat / Penampil JSON - Validasi dan Perindah JSON Online | Formix",
        description="Pemformat JSON online. Memeriksa apakah input Anda adalah JSON yang valid dan menampilkannya sebagai pohon yang mudah dibaca dengan penyorotan sintaks. Mendukung melipat/membuka dan pencarian kunci/nilai; data Anda hanya diproses di browser Anda.",
        keywords="pemformat json, penampil json, validator json, json beautify, json pretty print, alat json online",
        og_title="Pemformat / Penampil JSON | Formix",
        og_description="Pemformat JSON online gratis dengan validasi, tampilan pohon yang mudah dibaca, pencarian, dan lipat/buka.",
        jsonld_name="Pemformat / Penampil JSON",
        jsonld_description="Alat online gratis yang memvalidasi string JSON dan menampilkannya sebagai pohon yang mudah dibaca. Termasuk pencarian dan lipat/buka.",
        h1="Pemformat / Penampil JSON",
        lead="Masukkan string JSON untuk memvalidasinya dan melihatnya ditata sebagai pohon dengan indentasi dan penyorotan sintaks. Input Anda tidak pernah dikirim ke server — semuanya terjadi di browser Anda.",
        btn_format="Format", btn_sample="Muat contoh", btn_clear="Hapus",
        indent_label="Ukuran indentasi", indent2="Indentasi 2 spasi", indent4="Indentasi 4 spasi", indenttab="Indentasi Tab",
        btn_copy="Salin", btn_copy_minify="Salin yang diminifikasi", btn_download="Unduh .json",
        tabs_aria="Beralih antara input dan output", tab_input="Input", tab_output="Output",
        status_idle="Masukkan JSON",
        input_search_mode_label="Mode pencarian", opt_contains="Berisi", opt_exact_line="Tepat (baris)", opt_regex="Regex",
        input_search_placeholder="Cari di teks input…", prev_title="Hasil sebelumnya", next_title="Hasil berikutnya", clear_title="Hapus pencarian",
        input_placeholder="Tempel string JSON Anda di sini. Tanda kutip yang hilang di sekitar kunci atau nilai akan tetap dikenali bila memungkinkan.",
        output_label="Output", expand_all="▾ Buka semua", collapse_all="▸ Lipat semua",
        opt_exact="Tepat", output_search_placeholder="Cari kunci atau nilai…",
        hint='Tips. Saat Anda berhenti mengetik, input akan divalidasi dan, jika valid, tampilan secara otomatis beralih ke tab "Output". Titik pada tab Output menunjukkan status validitas saat ini. Tombol ▾/▸ untuk melipat/membuka objek dan array berada di sebelah nomor baris (margin kiri) agar mudah diklik. Kotak pencarian otomatis mendapat fokus saat tab Output terbuka, dan Anda dapat memilih mode pencarian (Berisi/Tepat/Regex) untuk menemukan kunci dan nilai sesuai keinginan. Nomor baris pada output dinomori ulang agar hanya sesuai dengan baris yang terlihat, sehingga Anda tetap tahu posisi meski sebagian struktur dilipat. Panel input memiliki jenis pencarian yang sama (Berisi/Tepat/Regex) agar Anda bisa menemukan dan menyorot teks langsung di input asli. Tekan Enter (berikutnya) / Shift+Enter (sebelumnya) untuk berpindah antar hasil. Meskipun beberapa tanda kutip (") di sekitar kunci atau nilai string hilang, kami tetap berusaha mengenali teks tersebut sebagai JSON.',
        usage_h2="Cara menggunakan alat ini",
        usage_items=[
            "Tempel string JSON ke kotak input di sebelah kiri dan akan divalidasi secara otomatis, dengan hasil langsung ditampilkan.",
            "Jika JSON tidak valid, Anda akan mendapatkan perkiraan baris/kolom tempat masalah berada.",
            'Mengklik "Format" juga memformat ulang konten kotak input menggunakan ukuran indentasi yang dipilih.',
            'Saat output panjang, gunakan "Lipat semua" untuk melihat gambaran struktur terlebih dahulu, lalu buka hanya node yang Anda perlukan dengan tombol ▾/▸ di sebelah nomor baris.',
            "Semuanya terjadi di browser Anda — data yang Anda masukkan tidak pernah dikirim ke server.",
            'Meskipun tanda kutip hilang di sekitar beberapa kunci atau nilai string, kami tetap berusaha memperbaiki dan mengenalinya secara otomatis. Dalam hal itu lencana status menunjukkan "Diperbaiki", dan baris yang diperbaiki disorot pada nomor baris panel input.',
            'Setelah input Anda dikonfirmasi valid (atau diperbaiki), tampilan secara otomatis beralih ke tab "Output" dan fokus berpindah ke kotak pencarian agar Anda dapat langsung mengetik.',
            'Pilih mode pencarian: "Berisi" (kecocokan sebagian), "Tepat" (kecocokan tepat), atau "Regex" (ekspresi reguler).',
            "Panel input memiliki fitur pencarian yang sama (Berisi/Tepat/Regex, navigasi sebelumnya/berikutnya, penyorotan) agar Anda bisa mencari langsung di teks asli.",
        ],
        tips_h2="Tips terkait",
        tips_items=[
            'Gunakan "Salin yang diminifikasi" daripada "Salin" saat Anda membutuhkan payload ringkas untuk permintaan API atau nilai konfigurasi — tanpa spasi atau baris baru tambahan.',
            "Ganti ukuran indentasi ke Tab jika gaya proyek Anda mengharuskan penggunaan tab daripada spasi.",
            "Mode pencarian Regex dapat mencocokkan pola di semua kunci atau nilai sekaligus — berguna untuk mengaudit ID, tanggal, atau email dalam dokumen besar.",
            'Untuk JSON yang sangat bertingkat, klik "Lipat semua" terlebih dahulu untuk melihat bentuk keseluruhan, lalu buka hanya cabang yang benar-benar perlu Anda periksa.',
        ],
    ),
    "de": dict(
        title="JSON-Formatierer / Viewer - JSON Online Validieren und Formatieren | Formix",
        description="Online-JSON-Formatierer. Prüft, ob Ihre Eingabe gültiges JSON ist, und zeigt es als lesbaren, syntaxhervorgehobenen Baum an. Unterstützt Ein-/Ausklappen und Schlüssel-/Wert-Suche; Ihre Daten werden nur in Ihrem Browser verarbeitet.",
        keywords="json formatierer, json viewer, json validator, json beautify, json pretty print, online json tool",
        og_title="JSON-Formatierer / Viewer | Formix",
        og_description="Ein kostenloser Online-JSON-Formatierer mit Validierung, lesbarer Baumansicht, Suche und Ein-/Ausklappen.",
        jsonld_name="JSON-Formatierer / Viewer",
        jsonld_description="Ein kostenloses Online-Tool, das JSON-Strings validiert und als lesbaren Baum anzeigt. Mit Suche und Ein-/Ausklappen.",
        h1="JSON-Formatierer / Viewer",
        lead="Geben Sie einen JSON-String ein, um ihn zu validieren und als eingerückten, syntaxhervorgehobenen Baum anzuzeigen. Ihre Eingabe wird nie an einen Server gesendet — alles geschieht in Ihrem Browser.",
        btn_format="Formatieren", btn_sample="Beispiel laden", btn_clear="Leeren",
        indent_label="Einrückungsgröße", indent2="2-Leerzeichen-Einrückung", indent4="4-Leerzeichen-Einrückung", indenttab="Tab-Einrückung",
        btn_copy="Kopieren", btn_copy_minify="Minifiziert kopieren", btn_download=".json herunterladen",
        tabs_aria="Zwischen Eingabe und Ausgabe wechseln", tab_input="Eingabe", tab_output="Ausgabe",
        status_idle="JSON eingeben",
        input_search_mode_label="Suchmodus", opt_contains="Enthält", opt_exact_line="Exakt (Zeile)", opt_regex="Regex",
        input_search_placeholder="Im Eingabetext suchen…", prev_title="Vorherige Übereinstimmung", next_title="Nächste Übereinstimmung", clear_title="Suche leeren",
        input_placeholder="Fügen Sie hier Ihren JSON-String ein. Fehlende Anführungszeichen um Schlüssel oder Werte werden, wenn möglich, trotzdem erkannt.",
        output_label="Ausgabe", expand_all="▾ Alle ausklappen", collapse_all="▸ Alle einklappen",
        opt_exact="Exakt", output_search_placeholder="Schlüssel oder Werte suchen…",
        hint='Tipp. Wenn Sie aufhören zu tippen, wird die Eingabe validiert und, falls gültig, wechselt die Ansicht automatisch zum Tab „Ausgabe". Der Punkt auf dem Ausgabe-Tab zeigt den aktuellen Gültigkeitsstatus. Die Schaltflächen ▾/▸ zum Ein-/Ausklappen von Objekten und Arrays befinden sich neben den Zeilennummern (linker Rand) für einfaches Klicken. Das Suchfeld erhält automatisch den Fokus, wenn der Ausgabe-Tab geöffnet wird, und Sie können einen Suchmodus (Enthält/Exakt/Regex) wählen, um Schlüssel und Werte nach Wunsch zu finden. Die Zeilennummern in der Ausgabe werden neu nummeriert, sodass sie nur zu den sichtbaren Zeilen passen, damit Sie sich auch bei eingeklappten Strukturteilen orientieren können. Das Eingabepanel hat die gleiche Art von Suche (Enthält/Exakt/Regex), damit Sie Text direkt in der ursprünglichen Eingabe finden und markieren können. Drücken Sie Enter (nächste) / Shift+Enter (vorherige), um zwischen Treffern zu wechseln. Auch wenn einige Anführungszeichen (") um Schlüssel oder Stringwerte fehlen, versuchen wir, den Text trotzdem als JSON zu erkennen.',
        usage_h2="So verwenden Sie dieses Tool",
        usage_items=[
            "Fügen Sie einen JSON-String in das Eingabefeld links ein, er wird automatisch validiert und das Ergebnis sofort angezeigt.",
            "Wenn das JSON ungültig ist, erhalten Sie eine ungefähre Zeile/Spalte, an der sich das Problem befindet.",
            'Ein Klick auf „Formatieren" formatiert auch den Inhalt des Eingabefelds mit der ausgewählten Einrückungsgröße neu.',
            'Wenn die Ausgabe lang ist, verwenden Sie „Alle einklappen", um zunächst einen Überblick über die Struktur zu erhalten, und klappen Sie dann nur die benötigten Knoten mit den Schaltflächen ▾/▸ neben den Zeilennummern aus.',
            "Alles geschieht in Ihrem Browser — die von Ihnen eingegebenen Daten werden nie an einen Server gesendet.",
            'Auch wenn Anführungszeichen um einige Schlüssel oder Stringwerte fehlen, versuchen wir, sie automatisch zu korrigieren und zu erkennen. In diesem Fall zeigt das Statusabzeichen „Korrigiert" an, und die korrigierten Zeilen werden in den Zeilennummern des Eingabepanels hervorgehoben.',
            'Sobald Ihre Eingabe als gültig (oder korrigiert) bestätigt ist, wechselt die Ansicht automatisch zum Tab „Ausgabe", und der Fokus springt ins Suchfeld, damit Sie sofort zu tippen beginnen können.',
            'Wählen Sie einen Suchmodus: „Enthält" (Teilübereinstimmung), „Exakt" (genaue Übereinstimmung) oder „Regex" (regulärer Ausdruck).',
            "Das Eingabepanel verfügt über die gleiche Suchfunktion (Enthält/Exakt/Regex, Vorherige/Nächste-Navigation, Hervorhebung), damit Sie direkt im Originaltext suchen können.",
        ],
        tips_h2="Verwandte Tipps",
        tips_items=[
            'Verwenden Sie „Minifiziert kopieren" statt „Kopieren", wenn Sie eine kompakte Payload für eine API-Anfrage oder einen Konfigurationswert benötigen — ohne zusätzliche Leerzeichen oder Zeilenumbrüche.',
            "Stellen Sie die Einrückungsgröße auf Tab um, wenn der Stilleitfaden Ihres Projekts Tabs statt Leerzeichen vorschreibt.",
            "Der Regex-Suchmodus kann ein Muster über alle Schlüssel oder Werte gleichzeitig abgleichen — praktisch, um IDs, Daten oder E-Mails in einem großen Dokument zu prüfen.",
            'Klicken Sie bei tief verschachteltem JSON zunächst auf „Alle einklappen", um die Gesamtform zu sehen, und klappen Sie dann nur den Zweig aus, den Sie tatsächlich untersuchen müssen.',
        ],
    ),
}

CONTENT["tool_xml"] = {
    "en": dict(
        title="XML Formatter / Viewer - Validate and Beautify XML Online | Formix",
        description="Online XML formatter. Checks whether your input is valid XML and displays it as a readable, syntax-highlighted tree. Supports collapsing/expanding and tag/attribute/text search; your data is processed only in your browser.",
        keywords="XML formatter, XML viewer, XML validator, XML beautify, XML pretty print, online XML tool",
        og_title="XML Formatter / Viewer | Formix",
        og_description="A free online XML formatter with validation, a readable tree view, search, and collapse/expand.",
        jsonld_name="XML Formatter / Viewer",
        jsonld_description="A free online tool that validates XML strings and displays them as a readable tree. Includes search and collapse/expand.",
        h1="XML Formatter / Viewer",
        lead="Enter an XML string to validate it and see it laid out as an indented, syntax-highlighted tree. Your input is never sent to a server — everything happens in your browser.",
        btn_format="Format", btn_sample="Load sample", btn_clear="Clear",
        indent_label="Indent size", indent2="2-space indent", indent4="4-space indent", indenttab="Tab indent",
        btn_copy="Copy", btn_copy_minify="Copy minified", btn_download="Download .xml",
        tabs_aria="Switch between input and output", tab_input="Input", tab_output="Output",
        status_idle="Enter some XML",
        input_search_mode_label="Search mode", opt_contains="Contains", opt_exact_line="Exact (line)", opt_regex="Regex",
        input_search_placeholder="Search the input text…", prev_title="Previous match", next_title="Next match", clear_title="Clear search",
        input_placeholder="Paste your XML string here.",
        output_label="Output", expand_all="▾ Expand all", collapse_all="▸ Collapse all",
        opt_exact="Exact", output_search_placeholder="Search tags, attributes, or text…",
        hint='Tip. When you stop typing, the input is validated and, if valid, the view switches automatically to the "Output" tab. The dot on the Output tab shows the current validity status. The ▾/▸ buttons for collapsing/expanding elements sit next to the line numbers (left margin) for easy clicking. The search box is focused automatically when the Output tab opens, and you can choose a search mode (Contains/Exact/Regex) to find tag names, attribute names/values, and text content the way you want. Line numbers on the output are renumbered to match only the visible lines, so you can still tell where you are even when parts of the tree are collapsed. The input panel has the same kind of search (Contains/Exact/Regex) so you can locate and highlight text directly in the original input. Press Enter (next) / Shift+Enter (previous) to move between matches.',
        usage_h2="How to use this tool",
        usage_items=[
            "Paste an XML string into the input box on the left and it's validated automatically, with the result rendered right away.",
            "If the XML isn't valid, you'll get an approximate line/column for where the problem is.",
            'Clicking "Format" also reformats the input box\'s content using the selected indent size.',
            'When the output is long, use "Collapse all" to get an overview of the structure first, then expand only the elements you need with the ▾/▸ buttons next to the line numbers.',
            "Everything happens in your browser — the data you enter is never sent to a server.",
            'Once your input is confirmed valid, the view switches automatically to the "Output" tab and focus moves to the search box so you can start typing right away.',
            'Choose a search mode: "Contains" (partial match), "Exact" (exact match), or "Regex" (regular expression).',
            "The input panel has the same search feature (Contains/Exact/Regex, previous/next navigation, highlighting) so you can search directly in the original text.",
            "Elements, attributes, text nodes, comments, and CDATA sections are all recognized and color-coded in the tree view.",
        ],
        tips_h2="Related tips",
        tips_items=[
            "Use Collapse all to get a bird's-eye view of a deeply nested document (like an RSS feed or a SOAP response) before drilling into a specific branch.",
            "The Regex search mode can match attribute values across many elements at once — handy for auditing IDs, dates, or namespaces in a large document.",
            "If your XML starts with an <?xml ...?> declaration, it's kept automatically whenever you use Format, Copy, or Download.",
            'CDATA sections are useful for embedding markup or special characters inside text without escaping them — the formatter preserves them as-is.',
        ],
    ),
    "ko": dict(
        title="XML 포매터 / 뷰어 - 온라인 XML 검증 및 정리 | Formix",
        description="온라인 XML 포매터. 입력한 문자열이 올바른 XML인지 검증하고, 들여쓰기와 문법 강조를 적용해 가독성 좋게 보여줍니다. 트리 접기/펼치기와 태그·속성·텍스트 검색을 지원하며 데이터는 브라우저 안에서만 처리됩니다.",
        keywords="XML 포매터, XML 뷰어, XML validator, XML beautify, XML pretty print, 온라인 XML 도구",
        og_title="XML 포매터 / 뷰어 | Formix",
        og_description="XML 문자열 유효성 검사와 가독성 좋은 트리 뷰, 검색, 접기/펼치기를 지원하는 무료 온라인 XML 포매터.",
        jsonld_name="XML 포매터 / 뷰어",
        jsonld_description="XML 문자열의 유효성을 검사하고 보기 좋은 트리 형태로 정리해주는 무료 온라인 도구. 검색과 접기/펼치기 기능을 제공합니다.",
        h1="XML 포매터 / 뷰어",
        lead="XML 문자열을 입력하면 유효성을 검사하고, 들여쓰기와 문법 강조가 적용된 트리로 정리해 보여줍니다. 입력값은 서버로 전송되지 않고 브라우저 안에서만 처리됩니다.",
        btn_format="정렬(Format)", btn_sample="예시 불러오기", btn_clear="지우기",
        indent_label="들여쓰기 크기", indent2="들여쓰기 2칸", indent4="들여쓰기 4칸", indenttab="들여쓰기 Tab",
        btn_copy="복사", btn_copy_minify="압축 복사", btn_download=".xml 다운로드",
        tabs_aria="입력/결과 전환", tab_input="입력", tab_output="결과",
        status_idle="XML을 입력해주세요",
        input_search_mode_label="검색 방식", opt_contains="포함", opt_exact_line="일치(줄)", opt_regex="정규식",
        input_search_placeholder="입력한 텍스트에서 검색…", prev_title="이전 일치 항목", next_title="다음 일치 항목", clear_title="검색어 지우기",
        input_placeholder="여기에 XML 문자열을 붙여넣으세요.",
        output_label="결과", expand_all="▾ 모두 펼치기", collapse_all="▸ 모두 접기",
        opt_exact="일치", output_search_placeholder="태그·속성·텍스트 검색…",
        hint='Tip. 입력을 멈추면 유효성을 검사해 정상이면 자동으로 "결과" 탭으로 전환합니다. 결과 탭의 점은 현재 유효성 상태를 보여줍니다. 엘리먼트를 접거나 펼치는 ▾/▸ 버튼은 줄 번호 옆(왼쪽 여백)에 있어 클릭하기 편합니다. 검색창은 결과 탭이 열리면 자동으로 포커스되며, 검색 방식(포함/일치/정규식)을 선택해 태그명·속성명/값·텍스트를 원하는 방식으로 찾을 수 있습니다. 결과 화면 왼쪽의 줄 번호는 접기/펼치기 상태에 맞춰 보이는 줄만 다시 매겨져, 구조가 접혀 있어도 위치를 가늠하기 쉽습니다. 입력창에도 동일한 방식의 검색(포함/일치/정규식)이 있어 원본 텍스트에서 바로 위치를 찾고 강조 표시로 확인할 수 있습니다. Enter(다음) / Shift+Enter(이전)로 일치 항목을 이동할 수 있습니다.',
        usage_h2="이 도구는 이렇게 사용하세요",
        usage_items=[
            "왼쪽 입력창에 XML 문자열을 붙여넣으면 자동으로 유효성을 검사하고 결과를 그려줍니다.",
            "유효하지 않은 XML이면 오류가 발생한 대략적인 줄/열 위치를 함께 알려줍니다.",
            '"정렬(Format)" 버튼을 누르면 입력창의 내용도 선택한 들여쓰기 기준으로 정리됩니다.',
            '결과가 길 때는 "모두 접기"로 전체 구조를 먼저 훑어본 뒤, 줄 번호 옆의 ▾/▸ 버튼으로 필요한 엘리먼트만 펼쳐볼 수 있습니다.',
            "모든 처리는 브라우저 안에서만 이뤄지며, 입력한 데이터는 서버로 전송되지 않습니다.",
            '입력을 마치고 결과가 유효함으로 확인되면 자동으로 "결과" 탭으로 전환되고, 검색창에 바로 입력할 수 있도록 포커스가 이동합니다.',
            '검색 방식을 "포함"(부분 일치), "일치"(정확히 같은 값), "정규식"(정규 표현식) 중에서 선택할 수 있습니다.',
            "입력창 상단에도 같은 검색 기능(포함/일치/정규식, 이전·다음 이동, 강조 표시)이 있어 원본 텍스트에서 바로 찾을 수 있습니다.",
            "엘리먼트, 속성, 텍스트 노드, 주석, CDATA 구간을 모두 인식해 트리 뷰에서 색상으로 구분해 보여줍니다.",
        ],
        tips_h2="관련 팁",
        tips_items=[
            "RSS 피드나 SOAP 응답처럼 깊게 중첩된 문서는 먼저 '모두 접기'로 전체 구조를 훑어본 뒤 필요한 분기만 펼쳐보세요.",
            "정규식 검색 모드는 여러 엘리먼트에 걸친 속성 값을 한 번에 찾을 때 유용합니다. (예: 아이디, 날짜, 네임스페이스 점검)",
            "<?xml ...?> 선언으로 시작하는 문서라면 정렬·복사·다운로드 시 선언부가 자동으로 유지됩니다.",
            "CDATA 구간은 마크업이나 특수문자를 이스케이프 없이 텍스트 안에 그대로 담을 때 유용하며, 포매터도 이를 그대로 보존합니다.",
        ],
    ),
    "ja": dict(
        title="XMLフォーマッター / ビューア - オンラインXML検証・整形 | Formix",
        description="オンラインXMLフォーマッター。入力した文字列が正しいXMLかを検証し、インデントとシンタックスハイライトを適用して読みやすく表示します。折りたたみ/展開とタグ・属性・テキスト検索に対応し、データはブラウザ内でのみ処理されます。",
        keywords="XMLフォーマッター, XMLビューア, XML validator, XML beautify, XML pretty print, オンラインXMLツール",
        og_title="XMLフォーマッター / ビューア | Formix",
        og_description="XML文字列の検証と読みやすいツリービュー、検索、折りたたみ/展開に対応した無料オンラインXMLフォーマッター。",
        jsonld_name="XMLフォーマッター / ビューア",
        jsonld_description="XML文字列の妥当性を検証し、読みやすいツリー形式に整理する無料オンラインツール。検索と折りたたみ/展開機能を提供します。",
        h1="XMLフォーマッター / ビューア",
        lead="XML文字列を入力すると妥当性を検証し、インデントとシンタックスハイライトを適用したツリーで表示します。入力値はサーバーに送信されずブラウザ内でのみ処理されます。",
        btn_format="整列(Format)", btn_sample="サンプルを読み込む", btn_clear="クリア",
        indent_label="インデントサイズ", indent2="インデント2桁", indent4="インデント4桁", indenttab="インデントTab",
        btn_copy="コピー", btn_copy_minify="圧縮コピー", btn_download=".xmlをダウンロード",
        tabs_aria="入力/出力の切り替え", tab_input="入力", tab_output="出力",
        status_idle="XMLを入力してください",
        input_search_mode_label="検索方式", opt_contains="部分一致", opt_exact_line="完全一致(行)", opt_regex="正規表現",
        input_search_placeholder="入力テキストを検索…", prev_title="前の一致項目", next_title="次の一致項目", clear_title="検索語をクリア",
        input_placeholder="ここにXML文字列を貼り付けてください。",
        output_label="出力", expand_all="▾ すべて展開", collapse_all="▸ すべて折りたたむ",
        opt_exact="完全一致", output_search_placeholder="タグ・属性・テキストを検索…",
        hint='Tip. 入力を止めると検証が行われ、正常なら自動的に「出力」タブに切り替わります。出力タブのドットは現在の妥当性ステータスを示します。エレメントを折りたたむ/展開する▾/▸ボタンは行番号の隣(左余白)にあり、クリックしやすくなっています。検索ボックスは出力タブが開くと自動的にフォーカスされ、検索方式(部分一致/完全一致/正規表現)を選べばタグ名・属性名/値・テキストを希望の方法で探せます。出力画面左側の行番号は折りたたみ状態に合わせて表示中の行だけに振り直されるため、構造が折りたたまれていても位置を把握しやすくなっています。入力ボックスにも同じ方式の検索があり、元のテキストで直接位置を探してハイライトで確認できます。Enter(次へ) / Shift+Enter(前へ)で一致項目を移動できます。',
        usage_h2="このツールの使い方",
        usage_items=[
            "左側の入力ボックスにXML文字列を貼り付けると、自動的に妥当性を検証し結果を描画します。",
            "無効なXMLの場合は、エラーが発生したおおまかな行/列位置も合わせてお知らせします。",
            "「整列(Format)」ボタンを押すと、入力ボックスの内容も選択したインデント基準で整形されます。",
            "結果が長い場合は「すべて折りたたむ」で全体の構造を先に把握し、行番号隣の▾/▸ボタンで必要なエレメントだけ展開できます。",
            "すべての処理はブラウザ内でのみ行われ、入力したデータがサーバーに送信されることはありません。",
            "入力を終えて結果が有効と確認されると自動的に「出力」タブに切り替わり、検索ボックスにすぐ入力できるようフォーカスが移動します。",
            "検索方式を「部分一致」、「完全一致」、「正規表現」から選べます。",
            "入力ボックス上部にも同じ検索機能があり、元のテキストで直接検索できます。",
            "エレメント、属性、テキストノード、コメント、CDATAセクションをすべて認識し、ツリービューで色分けして表示します。",
        ],
        tips_h2="関連のヒント",
        tips_items=[
            "RSSフィードやSOAPレスポンスのように深くネストした文書は、まず「すべて折りたたむ」で全体構造を把握してから必要な部分だけ展開しましょう。",
            "正規表現の検索モードは、複数のエレメントにまたがる属性値をまとめて探したいとき(ID、日付、名前空間の確認など)に便利です。",
            "<?xml ...?>宣言で始まる文書の場合、整列・コピー・ダウンロード時にこの宣言が自動的に保持されます。",
            "CDATAセクションは、マークアップや特殊文字をエスケープせずにテキスト内へそのまま埋め込みたいときに便利で、フォーマッターもそのまま保持します。",
        ],
    ),
    "zh": dict(
        title="XML 格式化 / 查看器 - 在线 XML 验证与整理 | Formix",
        description="在线 XML 格式化工具。检查输入的字符串是否为有效 XML，并带缩进和语法高亮清晰展示。支持折叠/展开以及标签/属性/文本搜索，数据仅在浏览器中处理。",
        keywords="XML 格式化, XML 查看器, XML validator, XML beautify, XML pretty print, 在线 XML 工具",
        og_title="XML 格式化 / 查看器 | Formix",
        og_description="支持验证、易读树形视图、搜索及折叠/展开的免费在线 XML 格式化工具。",
        jsonld_name="XML 格式化 / 查看器",
        jsonld_description="验证 XML 字符串并以易读树形结构整理展示的免费在线工具。提供搜索与折叠/展开功能。",
        h1="XML 格式化 / 查看器",
        lead="输入 XML 字符串即可验证其有效性，并以带缩进和语法高亮的树形结构展示。输入内容不会发送到服务器，仅在浏览器中处理。",
        btn_format="格式化(Format)", btn_sample="加载示例", btn_clear="清除",
        indent_label="缩进大小", indent2="2 空格缩进", indent4="4 空格缩进", indenttab="Tab 缩进",
        btn_copy="复制", btn_copy_minify="复制压缩版", btn_download="下载 .xml",
        tabs_aria="切换输入/输出", tab_input="输入", tab_output="输出",
        status_idle="请输入 XML",
        input_search_mode_label="搜索方式", opt_contains="包含", opt_exact_line="精确(整行)", opt_regex="正则表达式",
        input_search_placeholder="在输入文本中搜索…", prev_title="上一个匹配项", next_title="下一个匹配项", clear_title="清除搜索词",
        input_placeholder="在此粘贴 XML 字符串。",
        output_label="输出", expand_all="▾ 全部展开", collapse_all="▸ 全部折叠",
        opt_exact="精确", output_search_placeholder="搜索标签、属性或文本…",
        hint='提示：停止输入后会自动验证，若有效则自动切换到"输出"标签页。输出标签上的圆点表示当前的有效性状态。用于折叠/展开元素的 ▾/▸ 按钮位于行号旁边(左侧留白)，方便点击。打开输出标签页时搜索框会自动获得焦点，可选择搜索模式(包含/精确/正则)按需要查找标签名、属性名/值和文本内容。输出区域左侧的行号会根据折叠状态重新编号，只显示当前可见的行，即使结构被折叠也能轻松定位。输入面板也有相同方式的搜索，可直接在原始文本中定位并高亮显示。按 Enter(下一个) / Shift+Enter(上一个) 可在匹配项之间移动。',
        usage_h2="使用方法",
        usage_items=[
            "在左侧输入框中粘贴 XML 字符串，将自动验证并绘制结果。",
            "如果 XML 无效，会告知您大致的错误行/列位置。",
            '点击"格式化(Format)"按钮后，输入框中的内容也会按所选缩进量重新整理。',
            '当结果较长时，可先用"全部折叠"浏览整体结构，再通过行号旁的 ▾/▸ 按钮展开需要的元素。',
            "所有处理都在浏览器中进行，输入的数据不会发送到服务器。",
            '输入完成且结果确认有效后，会自动切换到"输出"标签页，并将焦点移至搜索框以便直接输入。',
            '可在"包含"、"精确"、"正则"中选择搜索模式。',
            "输入框上方也有相同的搜索功能，可直接在原始文本中搜索。",
            "元素、属性、文本节点、注释和 CDATA 区段都会被识别，并在树形视图中以不同颜色区分显示。",
        ],
        tips_h2="相关小技巧",
        tips_items=[
            "对于 RSS 订阅或 SOAP 响应这类层级很深的文档，建议先点击“全部折叠”了解整体结构，再展开需要查看的分支。",
            "正则表达式搜索模式可以一次性匹配多个元素中的属性值，适合用于检查 ID、日期或命名空间。",
            "如果 XML 以 <?xml ...?> 声明开头，在格式化、复制或下载时会自动保留该声明。",
            "CDATA 区段适合在文本中直接嵌入标记或特殊字符而无需转义，格式化工具也会原样保留它们。",
        ],
    ),
    "es": dict(
        title="Formateador / Visor XML - Valida y Embellece XML en Línea | Formix",
        description="Formateador XML en línea. Verifica si tu entrada es XML válido y lo muestra como un árbol legible con resaltado de sintaxis. Soporta colapsar/expandir y búsqueda de etiquetas/atributos/texto, tus datos se procesan solo en tu navegador.",
        keywords="formateador xml, visor xml, validador xml, embellecer xml, xml pretty print, herramienta xml en línea",
        og_title="Formateador / Visor XML | Formix",
        og_description="Un formateador XML en línea gratuito con validación, vista de árbol legible, búsqueda y colapsar/expandir.",
        jsonld_name="Formateador / Visor XML",
        jsonld_description="Una herramienta en línea gratuita que valida cadenas XML y las muestra como un árbol legible. Incluye búsqueda y colapsar/expandir.",
        h1="Formateador / Visor XML",
        lead="Ingresa una cadena XML para validarla y verla organizada como un árbol con sangría y resaltado de sintaxis. Tu entrada nunca se envía a un servidor — todo ocurre en tu navegador.",
        btn_format="Formatear", btn_sample="Cargar ejemplo", btn_clear="Limpiar",
        indent_label="Tamaño de sangría", indent2="Sangría de 2 espacios", indent4="Sangría de 4 espacios", indenttab="Sangría con Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar minificado", btn_download="Descargar .xml",
        tabs_aria="Alternar entre entrada y salida", tab_input="Entrada", tab_output="Salida",
        status_idle="Ingresa un XML",
        input_search_mode_label="Modo de búsqueda", opt_contains="Contiene", opt_exact_line="Exacto (línea)", opt_regex="Regex",
        input_search_placeholder="Buscar en el texto de entrada…", prev_title="Coincidencia anterior", next_title="Siguiente coincidencia", clear_title="Limpiar búsqueda",
        input_placeholder="Pega tu cadena XML aquí.",
        output_label="Salida", expand_all="▾ Expandir todo", collapse_all="▸ Colapsar todo",
        opt_exact="Exacto", output_search_placeholder="Buscar etiquetas, atributos o texto…",
        hint='Consejo. Cuando dejas de escribir, la entrada se valida y, si es válida, la vista cambia automáticamente a la pestaña "Salida". El punto en la pestaña Salida muestra el estado de validez actual. Los botones ▾/▸ para colapsar/expandir elementos están junto a los números de línea (margen izquierdo) para facilitar el clic. El cuadro de búsqueda recibe el foco automáticamente cuando se abre la pestaña Salida, y puedes elegir un modo de búsqueda (Contiene/Exacto/Regex) para encontrar nombres de etiquetas, nombres/valores de atributos y contenido de texto. Los números de línea en la salida se renumeran para coincidir solo con las líneas visibles, así puedes seguir ubicándote aunque partes de la estructura estén colapsadas. El panel de entrada tiene el mismo tipo de búsqueda para localizar y resaltar directamente en el texto original. Presiona Enter (siguiente) / Shift+Enter (anterior) para moverte entre coincidencias.',
        usage_h2="Cómo usar esta herramienta",
        usage_items=[
            "Pega una cadena XML en el cuadro de entrada de la izquierda y se valida automáticamente, mostrando el resultado al instante.",
            "Si el XML no es válido, obtendrás una línea/columna aproximada de dónde está el problema.",
            'Hacer clic en "Formatear" también reformatea el contenido del cuadro de entrada usando el tamaño de sangría seleccionado.',
            'Cuando la salida es larga, usa "Colapsar todo" para obtener una vista general de la estructura primero, luego expande solo los elementos que necesitas con los botones ▾/▸ junto a los números de línea.',
            "Todo ocurre en tu navegador — los datos que ingresas nunca se envían a un servidor.",
            'Una vez que tu entrada se confirma válida, la vista cambia automáticamente a la pestaña "Salida" y el foco se mueve al cuadro de búsqueda para que puedas empezar a escribir de inmediato.',
            'Elige un modo de búsqueda: "Contiene", "Exacto" o "Regex".',
            "El panel de entrada tiene la misma función de búsqueda para buscar directamente en el texto original.",
            "Los elementos, atributos, nodos de texto, comentarios y secciones CDATA se reconocen y se muestran con colores distintos en la vista de árbol.",
        ],
        tips_h2="Consejos relacionados",
        tips_items=[
            'Para documentos profundamente anidados como feeds RSS o respuestas SOAP, haz clic en "Colapsar todo" primero para entender la estructura general, luego expande las ramas que necesitas revisar.',
            "El modo de búsqueda Regex puede coincidir con valores de atributo en varios elementos a la vez — útil para auditar IDs, fechas o espacios de nombres.",
            "Si tu XML comienza con una declaración <?xml ...?>, se conserva automáticamente al formatear, copiar o descargar.",
            "Las secciones CDATA son ideales para incrustar marcado o caracteres especiales directamente en el texto sin escaparlos, y la herramienta las conserva tal cual.",
        ],
    ),
    "vi": dict(
        title="Định dạng / Xem XML - Kiểm tra và Làm đẹp XML Trực tuyến | Formix",
        description="Công cụ định dạng XML trực tuyến. Kiểm tra xem nội dung bạn nhập có phải XML hợp lệ không và hiển thị dưới dạng cây dễ đọc, có tô màu cú pháp. Hỗ trợ thu/mở rộng và tìm kiếm thẻ/thuộc tính/văn bản, dữ liệu của bạn chỉ được xử lý trong trình duyệt.",
        keywords="định dạng xml, xem xml, kiểm tra xml, làm đẹp xml, xml pretty print, công cụ xml trực tuyến",
        og_title="Định dạng / Xem XML | Formix",
        og_description="Công cụ định dạng XML trực tuyến miễn phí với kiểm tra tính hợp lệ, xem dạng cây dễ đọc, tìm kiếm và thu/mở rộng.",
        jsonld_name="Định dạng / Xem XML",
        jsonld_description="Công cụ trực tuyến miễn phí kiểm tra chuỗi XML và hiển thị dưới dạng cây dễ đọc. Bao gồm tìm kiếm và thu/mở rộng.",
        h1="Định dạng / Xem XML",
        lead="Nhập một chuỗi XML để kiểm tra tính hợp lệ và xem nó được trình bày dưới dạng cây có thụt lề, tô màu cú pháp. Nội dung bạn nhập không bao giờ được gửi lên máy chủ — mọi thứ diễn ra trong trình duyệt của bạn.",
        btn_format="Định dạng", btn_sample="Tải ví dụ", btn_clear="Xóa",
        indent_label="Kích thước thụt lề", indent2="Thụt lề 2 khoảng trắng", indent4="Thụt lề 4 khoảng trắng", indenttab="Thụt lề Tab",
        btn_copy="Sao chép", btn_copy_minify="Sao chép rút gọn", btn_download="Tải xuống .xml",
        tabs_aria="Chuyển đổi giữa nhập và kết quả", tab_input="Nhập", tab_output="Kết quả",
        status_idle="Hãy nhập XML",
        input_search_mode_label="Chế độ tìm kiếm", opt_contains="Chứa", opt_exact_line="Chính xác (dòng)", opt_regex="Regex",
        input_search_placeholder="Tìm trong văn bản nhập…", prev_title="Kết quả trước", next_title="Kết quả tiếp theo", clear_title="Xóa tìm kiếm",
        input_placeholder="Dán chuỗi XML của bạn vào đây.",
        output_label="Kết quả", expand_all="▾ Mở rộng tất cả", collapse_all="▸ Thu gọn tất cả",
        opt_exact="Chính xác", output_search_placeholder="Tìm thẻ, thuộc tính hoặc văn bản…",
        hint='Mẹo. Khi bạn dừng gõ, nội dung nhập sẽ được kiểm tra và nếu hợp lệ, màn hình sẽ tự động chuyển sang tab "Kết quả". Dấu chấm trên tab Kết quả cho biết trạng thái hợp lệ hiện tại. Các nút ▾/▸ để thu/mở rộng phần tử nằm cạnh số dòng (lề trái) để dễ nhấp. Hộp tìm kiếm tự động được focus khi tab Kết quả mở, và bạn có thể chọn chế độ tìm kiếm (Chứa/Chính xác/Regex) để tìm tên thẻ, tên/giá trị thuộc tính và nội dung văn bản. Số dòng ở kết quả được đánh số lại chỉ theo các dòng đang hiển thị, nên bạn vẫn biết vị trí ngay cả khi một phần cấu trúc bị thu gọn. Khung nhập cũng có cùng loại tìm kiếm để định vị và tô sáng trực tiếp trong nội dung gốc. Nhấn Enter (tiếp theo) / Shift+Enter (trước đó) để di chuyển giữa các kết quả khớp.',
        usage_h2="Cách sử dụng công cụ này",
        usage_items=[
            "Dán một chuỗi XML vào khung nhập bên trái và nó sẽ được kiểm tra tự động, kết quả hiển thị ngay lập tức.",
            "Nếu XML không hợp lệ, bạn sẽ nhận được dòng/cột gần đúng của vị trí gặp vấn đề.",
            'Nhấp "Định dạng" cũng sẽ định dạng lại nội dung trong khung nhập theo kích thước thụt lề đã chọn.',
            'Khi kết quả dài, dùng "Thu gọn tất cả" để xem tổng quan cấu trúc trước, sau đó chỉ mở rộng các phần tử cần thiết bằng nút ▾/▸ cạnh số dòng.',
            "Mọi thứ diễn ra trong trình duyệt của bạn — dữ liệu bạn nhập không bao giờ được gửi lên máy chủ.",
            'Khi nội dung nhập được xác nhận hợp lệ, màn hình tự động chuyển sang tab "Kết quả" và focus chuyển đến hộp tìm kiếm để bạn có thể gõ ngay.',
            'Chọn chế độ tìm kiếm: "Chứa", "Chính xác", hoặc "Regex".',
            "Khung nhập có cùng tính năng tìm kiếm để bạn tìm trực tiếp trong văn bản gốc.",
            "Phần tử, thuộc tính, nút văn bản, bình luận và các đoạn CDATA đều được nhận diện và hiển thị với màu khác nhau trong chế độ xem dạng cây.",
        ],
        tips_h2="Mẹo liên quan",
        tips_items=[
            'Với các tài liệu lồng nhiều cấp như nguồn cấp RSS hoặc phản hồi SOAP, hãy nhấp "Thu gọn tất cả" trước để hiểu cấu trúc tổng thể, rồi chỉ mở rộng nhánh bạn cần xem.',
            "Chế độ tìm kiếm Regex có thể khớp giá trị thuộc tính trên nhiều phần tử cùng lúc — tiện để kiểm tra ID, ngày tháng hoặc không gian tên.",
            "Nếu XML của bạn bắt đầu bằng khai báo <?xml ...?>, nó sẽ được tự động giữ lại khi định dạng, sao chép hoặc tải xuống.",
            "Các đoạn CDATA rất phù hợp để nhúng trực tiếp đánh dấu hoặc ký tự đặc biệt vào văn bản mà không cần thoát ký tự, và công cụ sẽ giữ nguyên chúng.",
        ],
    ),
    "pt": dict(
        title="Formatador / Visualizador XML - Validar e Formatar XML Online | Formix",
        description="Formatador XML online. Verifica se sua entrada é um XML válido e a exibe como uma árvore legível com destaque de sintaxe. Suporta recolher/expandir e busca de tag/atributo/texto, seus dados são processados apenas no seu navegador.",
        keywords="formatador xml, visualizador xml, validador xml, embelezar xml, xml pretty print, ferramenta xml online",
        og_title="Formatador / Visualizador XML | Formix",
        og_description="Um formatador XML online gratuito com validação, visualização em árvore legível, busca e recolher/expandir.",
        jsonld_name="Formatador / Visualizador XML",
        jsonld_description="Uma ferramenta online gratuita que valida strings XML e as exibe como uma árvore legível. Inclui busca e recolher/expandir.",
        h1="Formatador / Visualizador XML",
        lead="Insira uma string XML para validá-la e vê-la organizada como uma árvore com recuo e destaque de sintaxe. Sua entrada nunca é enviada a um servidor — tudo acontece no seu navegador.",
        btn_format="Formatar", btn_sample="Carregar exemplo", btn_clear="Limpar",
        indent_label="Tamanho do recuo", indent2="Recuo de 2 espaços", indent4="Recuo de 4 espaços", indenttab="Recuo com Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar minificado", btn_download="Baixar .xml",
        tabs_aria="Alternar entre entrada e saída", tab_input="Entrada", tab_output="Saída",
        status_idle="Insira um XML",
        input_search_mode_label="Modo de busca", opt_contains="Contém", opt_exact_line="Exato (linha)", opt_regex="Regex",
        input_search_placeholder="Buscar no texto de entrada…", prev_title="Correspondência anterior", next_title="Próxima correspondência", clear_title="Limpar busca",
        input_placeholder="Cole sua string XML aqui.",
        output_label="Saída", expand_all="▾ Expandir tudo", collapse_all="▸ Recolher tudo",
        opt_exact="Exato", output_search_placeholder="Buscar tags, atributos ou texto…",
        hint='Dica. Quando você para de digitar, a entrada é validada e, se válida, a visualização muda automaticamente para a aba "Saída". O ponto na aba Saída mostra o status de validade atual. Os botões ▾/▸ para recolher/expandir elementos ficam junto aos números de linha (margem esquerda) para facilitar o clique. A caixa de busca recebe foco automaticamente quando a aba Saída abre, e você pode escolher um modo de busca (Contém/Exato/Regex) para encontrar nomes de tags, nomes/valores de atributos e conteúdo de texto. Os números de linha na saída são renumerados para corresponder apenas às linhas visíveis, então você ainda sabe onde está mesmo com partes da estrutura recolhidas. O painel de entrada tem o mesmo tipo de busca para localizar e destacar diretamente no texto original. Pressione Enter (próximo) / Shift+Enter (anterior) para navegar entre as correspondências.',
        usage_h2="Como usar esta ferramenta",
        usage_items=[
            "Cole uma string XML na caixa de entrada à esquerda e ela é validada automaticamente, com o resultado renderizado imediatamente.",
            "Se o XML não for válido, você receberá uma linha/coluna aproximada de onde está o problema.",
            'Clicar em "Formatar" também reformata o conteúdo da caixa de entrada usando o tamanho de recuo selecionado.',
            'Quando a saída for longa, use "Recolher tudo" para ter uma visão geral da estrutura primeiro, depois expanda apenas os elementos necessários com os botões ▾/▸ junto aos números de linha.',
            "Tudo acontece no seu navegador — os dados que você insere nunca são enviados a um servidor.",
            'Depois que sua entrada é confirmada como válida, a visualização muda automaticamente para a aba "Saída" e o foco vai para a caixa de busca para você começar a digitar imediatamente.',
            'Escolha um modo de busca: "Contém", "Exato" ou "Regex".',
            "O painel de entrada tem a mesma função de busca para você buscar diretamente no texto original.",
            "Elementos, atributos, nós de texto, comentários e seções CDATA são reconhecidos e exibidos com cores distintas na visualização em árvore.",
        ],
        tips_h2="Dicas relacionadas",
        tips_items=[
            'Para documentos profundamente aninhados como feeds RSS ou respostas SOAP, clique em "Recolher tudo" primeiro para entender a estrutura geral, depois expanda apenas os ramos que precisa revisar.',
            "O modo de busca Regex pode corresponder a valores de atributo em vários elementos de uma vez — útil para auditar IDs, datas ou namespaces.",
            "Se seu XML começar com uma declaração <?xml ...?>, ela é preservada automaticamente ao formatar, copiar ou baixar.",
            "Seções CDATA são ideais para incorporar marcação ou caracteres especiais diretamente no texto sem escapá-los, e a ferramenta as preserva como estão.",
        ],
    ),
    "id": dict(
        title="Pemformat / Penampil XML - Validasi dan Perindah XML Online | Formix",
        description="Pemformat XML online. Memeriksa apakah input Anda adalah XML yang valid dan menampilkannya sebagai pohon yang mudah dibaca dengan penyorotan sintaks. Mendukung melipat/membuka dan pencarian tag/atribut/teks, data Anda hanya diproses di browser Anda.",
        keywords="pemformat xml, penampil xml, validator xml, xml beautify, xml pretty print, alat xml online",
        og_title="Pemformat / Penampil XML | Formix",
        og_description="Pemformat XML online gratis dengan validasi, tampilan pohon yang mudah dibaca, pencarian, dan lipat/buka.",
        jsonld_name="Pemformat / Penampil XML",
        jsonld_description="Alat online gratis yang memvalidasi string XML dan menampilkannya sebagai pohon yang mudah dibaca. Termasuk pencarian dan lipat/buka.",
        h1="Pemformat / Penampil XML",
        lead="Masukkan string XML untuk memvalidasinya dan melihatnya ditata sebagai pohon dengan indentasi dan penyorotan sintaks. Input Anda tidak pernah dikirim ke server — semuanya terjadi di browser Anda.",
        btn_format="Format", btn_sample="Muat contoh", btn_clear="Hapus",
        indent_label="Ukuran indentasi", indent2="Indentasi 2 spasi", indent4="Indentasi 4 spasi", indenttab="Indentasi Tab",
        btn_copy="Salin", btn_copy_minify="Salin yang diminifikasi", btn_download="Unduh .xml",
        tabs_aria="Beralih antara input dan output", tab_input="Input", tab_output="Output",
        status_idle="Masukkan XML",
        input_search_mode_label="Mode pencarian", opt_contains="Berisi", opt_exact_line="Tepat (baris)", opt_regex="Regex",
        input_search_placeholder="Cari di teks input…", prev_title="Hasil sebelumnya", next_title="Hasil berikutnya", clear_title="Hapus pencarian",
        input_placeholder="Tempel string XML Anda di sini.",
        output_label="Output", expand_all="▾ Buka semua", collapse_all="▸ Lipat semua",
        opt_exact="Tepat", output_search_placeholder="Cari tag, atribut, atau teks…",
        hint='Tips. Saat Anda berhenti mengetik, input akan divalidasi dan, jika valid, tampilan secara otomatis beralih ke tab "Output". Titik pada tab Output menunjukkan status validitas saat ini. Tombol ▾/▸ untuk melipat/membuka elemen berada di sebelah nomor baris (margin kiri) agar mudah diklik. Kotak pencarian otomatis mendapat fokus saat tab Output terbuka, dan Anda dapat memilih mode pencarian (Berisi/Tepat/Regex) untuk menemukan nama tag, nama/nilai atribut, dan konten teks. Nomor baris pada output dinomori ulang agar hanya sesuai dengan baris yang terlihat, sehingga Anda tetap tahu posisi meski sebagian struktur dilipat. Panel input memiliki jenis pencarian yang sama untuk menemukan dan menyorot langsung di teks asli. Tekan Enter (berikutnya) / Shift+Enter (sebelumnya) untuk berpindah antar hasil.',
        usage_h2="Cara menggunakan alat ini",
        usage_items=[
            "Tempel string XML ke kotak input di sebelah kiri dan akan divalidasi secara otomatis, dengan hasil langsung ditampilkan.",
            "Jika XML tidak valid, Anda akan mendapatkan perkiraan baris/kolom tempat masalah berada.",
            'Mengklik "Format" juga memformat ulang konten kotak input menggunakan ukuran indentasi yang dipilih.',
            'Saat output panjang, gunakan "Lipat semua" untuk melihat gambaran struktur terlebih dahulu, lalu buka hanya elemen yang Anda perlukan dengan tombol ▾/▸ di sebelah nomor baris.',
            "Semuanya terjadi di browser Anda — data yang Anda masukkan tidak pernah dikirim ke server.",
            'Setelah input Anda dikonfirmasi valid, tampilan secara otomatis beralih ke tab "Output" dan fokus berpindah ke kotak pencarian agar Anda dapat langsung mengetik.',
            'Pilih mode pencarian: "Berisi", "Tepat", atau "Regex".',
            "Panel input memiliki fitur pencarian yang sama agar Anda bisa mencari langsung di teks asli.",
            "Elemen, atribut, node teks, komentar, dan bagian CDATA semuanya dikenali dan ditampilkan dengan warna berbeda dalam tampilan pohon.",
        ],
        tips_h2="Tips terkait",
        tips_items=[
            'Untuk dokumen yang sangat bertingkat seperti feed RSS atau respons SOAP, klik "Lipat semua" terlebih dahulu untuk memahami struktur keseluruhan, lalu buka hanya cabang yang perlu Anda tinjau.',
            "Mode pencarian Regex dapat mencocokkan nilai atribut di beberapa elemen sekaligus — berguna untuk mengaudit ID, tanggal, atau namespace.",
            "Jika XML Anda dimulai dengan deklarasi <?xml ...?>, deklarasi tersebut akan otomatis dipertahankan saat memformat, menyalin, atau mengunduh.",
            "Bagian CDATA sangat cocok untuk menyematkan markup atau karakter khusus langsung dalam teks tanpa perlu escape, dan alat ini akan mempertahankannya apa adanya.",
        ],
    ),
    "de": dict(
        title="XML-Formatierer / Viewer - XML Online Validieren und Formatieren | Formix",
        description="Online-XML-Formatierer. Prüft, ob Ihre Eingabe gültiges XML ist, und zeigt es als lesbaren, syntaxhervorgehobenen Baum an. Unterstützt Ein-/Ausklappen und Tag-/Attribut-/Text-Suche; Ihre Daten werden nur in Ihrem Browser verarbeitet.",
        keywords="xml formatierer, xml viewer, xml validator, xml beautify, xml pretty print, online xml tool",
        og_title="XML-Formatierer / Viewer | Formix",
        og_description="Ein kostenloser Online-XML-Formatierer mit Validierung, lesbarer Baumansicht, Suche und Ein-/Ausklappen.",
        jsonld_name="XML-Formatierer / Viewer",
        jsonld_description="Ein kostenloses Online-Tool, das XML-Strings validiert und als lesbaren Baum anzeigt. Mit Suche und Ein-/Ausklappen.",
        h1="XML-Formatierer / Viewer",
        lead="Geben Sie einen XML-String ein, um ihn zu validieren und als eingerückten, syntaxhervorgehobenen Baum anzuzeigen. Ihre Eingabe wird nie an einen Server gesendet — alles geschieht in Ihrem Browser.",
        btn_format="Formatieren", btn_sample="Beispiel laden", btn_clear="Leeren",
        indent_label="Einrückungsgröße", indent2="2-Leerzeichen-Einrückung", indent4="4-Leerzeichen-Einrückung", indenttab="Tab-Einrückung",
        btn_copy="Kopieren", btn_copy_minify="Minifiziert kopieren", btn_download=".xml herunterladen",
        tabs_aria="Zwischen Eingabe und Ausgabe wechseln", tab_input="Eingabe", tab_output="Ausgabe",
        status_idle="XML eingeben",
        input_search_mode_label="Suchmodus", opt_contains="Enthält", opt_exact_line="Exakt (Zeile)", opt_regex="Regex",
        input_search_placeholder="Im Eingabetext suchen…", prev_title="Vorherige Übereinstimmung", next_title="Nächste Übereinstimmung", clear_title="Suche leeren",
        input_placeholder="Fügen Sie hier Ihren XML-String ein.",
        output_label="Ausgabe", expand_all="▾ Alle ausklappen", collapse_all="▸ Alle einklappen",
        opt_exact="Exakt", output_search_placeholder="Tags, Attribute oder Text suchen…",
        hint='Tipp. Wenn Sie aufhören zu tippen, wird die Eingabe validiert und, falls gültig, wechselt die Ansicht automatisch zum Tab „Ausgabe". Der Punkt auf dem Ausgabe-Tab zeigt den aktuellen Gültigkeitsstatus. Die Schaltflächen ▾/▸ zum Ein-/Ausklappen von Elementen befinden sich neben den Zeilennummern (linker Rand) für einfaches Klicken. Das Suchfeld erhält automatisch den Fokus, wenn der Ausgabe-Tab geöffnet wird, und Sie können einen Suchmodus (Enthält/Exakt/Regex) wählen, um Tag-Namen, Attributnamen/-werte und Textinhalte zu finden. Die Zeilennummern in der Ausgabe werden neu nummeriert, sodass sie nur zu den sichtbaren Zeilen passen, damit Sie sich auch bei eingeklappten Strukturteilen orientieren können. Das Eingabepanel hat die gleiche Art von Suche, um direkt im Originaltext zu finden und zu markieren. Drücken Sie Enter (nächste) / Shift+Enter (vorherige), um zwischen Treffern zu wechseln.',
        usage_h2="So verwenden Sie dieses Tool",
        usage_items=[
            "Fügen Sie einen XML-String in das Eingabefeld links ein, er wird automatisch validiert und das Ergebnis sofort angezeigt.",
            "Wenn das XML ungültig ist, erhalten Sie eine ungefähre Zeile/Spalte, an der sich das Problem befindet.",
            'Ein Klick auf „Formatieren" formatiert auch den Inhalt des Eingabefelds mit der ausgewählten Einrückungsgröße neu.',
            'Wenn die Ausgabe lang ist, verwenden Sie „Alle einklappen", um zunächst einen Überblick über die Struktur zu erhalten, und klappen Sie dann nur die benötigten Elemente mit den Schaltflächen ▾/▸ neben den Zeilennummern aus.',
            "Alles geschieht in Ihrem Browser — die von Ihnen eingegebenen Daten werden nie an einen Server gesendet.",
            'Sobald Ihre Eingabe als gültig bestätigt ist, wechselt die Ansicht automatisch zum Tab „Ausgabe", und der Fokus springt ins Suchfeld, damit Sie sofort zu tippen beginnen können.',
            'Wählen Sie einen Suchmodus: „Enthält", „Exakt" oder „Regex".',
            "Das Eingabepanel verfügt über die gleiche Suchfunktion, damit Sie direkt im Originaltext suchen können.",
            "Elemente, Attribute, Textknoten, Kommentare und CDATA-Abschnitte werden erkannt und in der Baumansicht mit unterschiedlichen Farben angezeigt.",
        ],
        tips_h2="Verwandte Tipps",
        tips_items=[
            'Klicken Sie bei tief verschachtelten Dokumenten wie RSS-Feeds oder SOAP-Antworten zunächst auf „Alle einklappen", um die Gesamtstruktur zu verstehen, und klappen Sie dann nur die Zweige aus, die Sie überprüfen müssen.',
            "Der Regex-Suchmodus kann Attributwerte über mehrere Elemente gleichzeitig abgleichen — praktisch, um IDs, Daten oder Namespaces zu prüfen.",
            "Wenn Ihr XML mit einer <?xml ...?>-Deklaration beginnt, wird diese beim Formatieren, Kopieren oder Herunterladen automatisch beibehalten.",
            "CDATA-Abschnitte eignen sich gut, um Markup oder Sonderzeichen direkt im Text einzubetten, ohne sie zu maskieren, und das Tool behält sie unverändert bei.",
        ],
    ),
}

CONTENT["tool_converter"] = {
    "en": dict(
        title="JSON to XML / XML to JSON Converter - Free Online Tool | Formix",
        description="Convert JSON to XML or XML to JSON instantly in your browser. Paste either format and Formix detects it automatically, or pick a direction manually. Your data is never sent to a server.",
        keywords="json to xml, xml to json, json xml converter, convert json to xml online, convert xml to json online, json xml converter free",
        og_title="JSON to XML / XML to JSON Converter | Formix",
        og_description="A free online converter between JSON and XML, with automatic format detection. Runs entirely in your browser.",
        jsonld_name="JSON to XML / XML to JSON Converter",
        jsonld_description="A free online tool that converts JSON to XML and XML to JSON, with automatic format detection and configurable indentation.",
        h1="JSON ↔ XML Converter",
        lead="Paste JSON or XML on the left and get the other format on the right. Formix detects which one you pasted automatically — or you can pick a direction yourself. Nothing is sent to a server.",
        btn_format="Convert", btn_sample="Load sample", btn_clear="Clear",
        indent_label="Indent size", indent2="2-space indent", indent4="4-space indent", indenttab="Tab indent",
        btn_copy="Copy", btn_copy_minify="Copy minified", btn_download="Download result",
        tabs_aria="Switch between input and output", tab_input="Input", tab_output="Output",
        status_idle="Paste some JSON or XML",
        input_search_mode_label="Search mode", opt_contains="Contains", opt_exact_line="Exact (line)", opt_regex="Regex",
        input_search_placeholder="Search the input text…", prev_title="Previous match", next_title="Next match", clear_title="Clear search",
        input_placeholder="Paste JSON or XML here — Formix detects the format automatically.",
        output_label="Output", expand_all="▾ Expand all", collapse_all="▸ Collapse all",
        opt_exact="Exact", output_search_placeholder="Search the output text…",
        direction_label="Conversion direction", dir_auto="Auto-detect", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint="Tip. In "
             '"Auto-detect" mode, Formix looks at the first character you pasted (“{”/“[” for JSON, “<” for XML) '
             "to pick a direction automatically; if the format is ambiguous, choose a direction manually from the dropdown. "
             "Because JSON and XML don't model data identically, the conversion follows a fixed, documented convention: a JSON array's "
             "repeated values become repeated XML elements with the same tag name, and XML attributes round-trip through a "
             '“@attributes” object in the JSON. This means a JSON → XML → JSON round trip won’t always reproduce the exact original '
             "shape (for example, top-level arrays get wrapped in a <root><item> element), which is expected for any generic converter.",
        usage_h2="How to use this tool",
        usage_items=[
            "Paste JSON or XML into the input box on the left — the format is detected automatically and the result appears on the right.",
            'If auto-detection picks the wrong format, open the "Conversion direction" dropdown and choose JSON → XML or XML → JSON manually.',
            "If the input isn't valid JSON or XML, you'll get an approximate line/column for where the problem is.",
            'Use the indent-size dropdown to control how the converted output is pretty-printed, then "Copy" or "Download result" to grab it.',
            '"Copy minified" copies the converted output with all unnecessary whitespace removed — handy for pasting into config files or API requests.',
            "Everything happens in your browser — the data you paste is never sent to a server.",
        ],
        tips_h2="Related tips",
        tips_items=[
            "JSON object keys become XML element names — keys with spaces or symbols that aren't valid XML tag names are sanitized automatically.",
            "A JSON array like [\"a\", \"b\"] converts to two sibling elements with the same tag name (not a single element containing a list), since XML has no native array type.",
            "When converting XML that has attributes (e.g. <book id=\"1\">), they appear under an \"@attributes\" key in the resulting JSON so no information is lost.",
            "Need to also validate or pretty-print your JSON or XML on its own? Try the dedicated JSON Formatter or XML Formatter tools linked below.",
        ],
    ),
    "ko": dict(
        title="JSON to XML / XML to JSON 변환기 - 무료 온라인 도구 | Formix",
        description="브라우저에서 바로 JSON을 XML로, XML을 JSON으로 변환하세요. 어떤 형식을 붙여넣든 Formix가 자동으로 감지하며, 방향을 직접 선택할 수도 있습니다. 데이터는 서버로 전송되지 않습니다.",
        keywords="json to xml, xml to json, json xml 변환, json xml 변환기, json을 xml로 변환, xml을 json으로 변환, 온라인 json xml 변환기",
        og_title="JSON to XML / XML to JSON 변환기 | Formix",
        og_description="자동 형식 감지를 지원하는 무료 온라인 JSON ↔ XML 변환기. 모든 처리는 브라우저 안에서 이뤄집니다.",
        jsonld_name="JSON to XML / XML to JSON 변환기",
        jsonld_description="JSON을 XML로, XML을 JSON으로 변환해주는 무료 온라인 도구. 자동 형식 감지와 들여쓰기 설정을 지원합니다.",
        h1="JSON ↔ XML 변환기",
        lead="왼쪽에 JSON 또는 XML을 붙여넣으면 오른쪽에 반대 형식으로 변환된 결과가 표시됩니다. 어떤 형식을 붙여넣었는지는 Formix가 자동으로 감지하며, 방향을 직접 선택할 수도 있습니다. 데이터는 서버로 전송되지 않습니다.",
        btn_format="변환", btn_sample="예시 불러오기", btn_clear="지우기",
        indent_label="들여쓰기 크기", indent2="들여쓰기 2칸", indent4="들여쓰기 4칸", indenttab="들여쓰기 Tab",
        btn_copy="복사", btn_copy_minify="압축 복사", btn_download="결과 다운로드",
        tabs_aria="입력/결과 전환", tab_input="입력", tab_output="결과",
        status_idle="JSON 또는 XML을 붙여넣어주세요",
        input_search_mode_label="검색 방식", opt_contains="포함", opt_exact_line="일치(줄)", opt_regex="정규식",
        input_search_placeholder="입력한 텍스트에서 검색…", prev_title="이전 일치 항목", next_title="다음 일치 항목", clear_title="검색어 지우기",
        input_placeholder="여기에 JSON 또는 XML을 붙여넣으세요. 형식은 자동으로 감지됩니다.",
        output_label="결과", expand_all="▾ 모두 펼치기", collapse_all="▸ 모두 접기",
        opt_exact="일치", output_search_placeholder="결과 텍스트에서 검색…",
        direction_label="변환 방향", dir_auto="자동 감지", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint='Tip. "자동 감지" 모드에서는 붙여넣은 텍스트의 첫 글자({ 또는 [ 는 JSON, < 는 XML)로 방향을 자동으로 판단합니다. '
             "형식이 애매하면 드롭다운에서 방향을 직접 선택해주세요. JSON과 XML은 데이터를 표현하는 방식이 근본적으로 다르기 때문에, "
             "변환은 정해진 규칙을 따릅니다: JSON 배열의 반복되는 값은 같은 태그명을 가진 XML 엘리먼트 여러 개로 변환되고, "
             'XML 속성(attribute)은 JSON에서 "@attributes" 객체로 보존됩니다. 이 때문에 JSON → XML → JSON으로 왕복 변환하면 '
             "원래 모양이 완전히 똑같이 복원되지 않을 수 있습니다(예: 최상위 배열은 <root><item> 구조로 감싸짐). "
             "이는 범용 변환기라면 자연스럽게 발생하는 특성입니다.",
        usage_h2="이 도구는 이렇게 사용하세요",
        usage_items=[
            "왼쪽 입력창에 JSON 또는 XML을 붙여넣으면 형식이 자동으로 감지되어 오른쪽에 변환 결과가 표시됩니다.",
            '자동 감지가 원하는 형식과 다르게 판단했다면 "변환 방향" 드롭다운에서 JSON → XML 또는 XML → JSON을 직접 선택하세요.',
            "입력이 유효한 JSON/XML이 아니면 오류가 발생한 대략적인 줄/열 위치를 알려줍니다.",
            '들여쓰기 크기 드롭다운으로 변환 결과의 정렬 방식을 조절한 뒤, "복사" 또는 "결과 다운로드"로 가져갈 수 있습니다.',
            '"압축 복사"는 불필요한 공백을 모두 제거한 변환 결과를 복사합니다. 설정 파일이나 API 요청에 붙여넣을 때 유용합니다.',
            "모든 처리는 브라우저 안에서만 이뤄지며, 입력한 데이터는 서버로 전송되지 않습니다.",
        ],
        tips_h2="관련 팁",
        tips_items=[
            "JSON 객체의 키는 XML 엘리먼트 이름이 됩니다. 공백이나 기호가 포함되어 XML 태그명으로 쓸 수 없는 키는 자동으로 정리(sanitize)됩니다.",
            'XML에는 배열 타입이 없기 때문에, [\"a\", \"b\"] 같은 JSON 배열은 하나의 엘리먼트가 아니라 같은 태그명을 가진 형제 엘리먼트 두 개로 변환됩니다.',
            '속성이 있는 XML(예: <book id="1">)을 변환하면, 정보 손실 없이 결과 JSON의 "@attributes" 키 아래에 담깁니다.',
            "JSON이나 XML 자체의 유효성 검사·정렬만 필요하다면, 아래 관련 링크의 JSON 포매터 또는 XML 포매터를 사용해보세요.",
        ],
    ),
    "ja": dict(
        title="JSON to XML / XML to JSON 変換ツール - 無料オンラインツール | Formix",
        description="ブラウザ上でJSONをXMLに、XMLをJSONに即座に変換できます。どちらの形式を貼り付けてもFormixが自動判定し、方向を手動で選ぶことも可能です。データはサーバーに送信されません。",
        keywords="json to xml, xml to json, json xml 変換, json xml 変換ツール, json xmlに変換, xml jsonに変換, オンライン json xml 変換",
        og_title="JSON to XML / XML to JSON 変換ツール | Formix",
        og_description="自動フォーマット判定に対応した無料オンラインJSON ↔ XML変換ツール。すべての処理はブラウザ内で行われます。",
        jsonld_name="JSON to XML / XML to JSON 変換ツール",
        jsonld_description="JSONをXMLに、XMLをJSONに変換する無料オンラインツール。自動フォーマット判定とインデント設定に対応しています。",
        h1="JSON ↔ XML 変換ツール",
        lead="左側にJSONまたはXMLを貼り付けると、右側に反対の形式に変換された結果が表示されます。どちらの形式かはFormixが自動判定し、方向を手動で選ぶこともできます。データはサーバーに送信されません。",
        btn_format="変換", btn_sample="サンプルを読み込む", btn_clear="クリア",
        indent_label="インデントサイズ", indent2="インデント2桁", indent4="インデント4桁", indenttab="インデントTab",
        btn_copy="コピー", btn_copy_minify="圧縮コピー", btn_download="結果をダウンロード",
        tabs_aria="入力/出力の切り替え", tab_input="入力", tab_output="出力",
        status_idle="JSONまたはXMLを貼り付けてください",
        input_search_mode_label="検索方式", opt_contains="部分一致", opt_exact_line="完全一致(行)", opt_regex="正規表現",
        input_search_placeholder="入力テキストを検索…", prev_title="前の一致項目", next_title="次の一致項目", clear_title="検索語をクリア",
        input_placeholder="ここにJSONまたはXMLを貼り付けてください。形式は自動的に判定されます。",
        output_label="出力", expand_all="▾ すべて展開", collapse_all="▸ すべて折りたたむ",
        opt_exact="完全一致", output_search_placeholder="出力テキストを検索…",
        direction_label="変換方向", dir_auto="自動判定", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint='Tip. 「自動判定」モードでは、貼り付けたテキストの最初の文字({または[はJSON、<はXML)から方向を自動的に判定します。'
             "判定が曖昧な場合はドロップダウンから方向を手動で選択してください。JSONとXMLはデータの表現方法が根本的に異なるため、"
             "変換は決まった規則に従います: JSON配列の繰り返し値は、同じタグ名を持つ複数のXML要素に変換され、"
             "XML属性(attribute)はJSON側で「@attributes」オブジェクトとして保持されます。このため、JSON → XML → JSONと往復変換しても、"
             "元の形が完全に同じ状態には戻らない場合があります(例: 最上位の配列は<root><item>構造でラップされます)。"
             "これは汎用的な変換ツールであれば自然に生じる特性です。",
        usage_h2="この機能の使い方",
        usage_items=[
            "左側の入力欄にJSONまたはXMLを貼り付けると、形式が自動的に判定され右側に変換結果が表示されます。",
            "自動判定が意図と異なる場合は「変換方向」ドロップダウンからJSON → XMLまたはXML → JSONを手動で選択してください。",
            "入力が有効なJSON/XMLでない場合、エラーが発生したおおよその行・列位置をお知らせします。",
            "インデントサイズのドロップダウンで変換結果の整形方法を調整し、「コピー」または「結果をダウンロード」で取得できます。",
            "「圧縮コピー」は不要な空白をすべて取り除いた変換結果をコピーします。設定ファイルやAPIリクエストへの貼り付けに便利です。",
            "すべての処理はブラウザ内でのみ行われ、入力したデータがサーバーに送信されることはありません。",
        ],
        tips_h2="関連のヒント",
        tips_items=[
            "JSONオブジェクトのキーはXML要素名になります。空白や記号を含みXMLタグ名として使えないキーは自動的に整形(sanitize)されます。",
            "XMLには配列型がないため、[\"a\", \"b\"]のようなJSON配列は1つの要素ではなく、同じタグ名を持つ兄弟要素2つに変換されます。",
            "属性を持つXML(例: <book id=\"1\">)を変換すると、情報を失わずに結果のJSONの「@attributes」キー以下に格納されます。",
            "JSONやXML自体の検証・整形だけが必要な場合は、下の関連リンクからJSONフォーマッターまたはXMLフォーマッターをお試しください。",
        ],
    ),
    "zh": dict(
        title="JSON to XML / XML to JSON 转换工具 - 免费在线工具 | Formix",
        description="在浏览器中即时将 JSON 转换为 XML，或将 XML 转换为 JSON。无论粘贴哪种格式，Formix 都会自动识别，也可以手动选择转换方向。数据不会发送到服务器。",
        keywords="json to xml, xml to json, json xml 转换, json xml 转换工具, json转xml, xml转json, 在线 json xml 转换",
        og_title="JSON to XML / XML to JSON 转换工具 | Formix",
        og_description="支持自动格式识别的免费在线 JSON ↔ XML 转换工具，所有处理都在浏览器内完成。",
        jsonld_name="JSON to XML / XML to JSON 转换工具",
        jsonld_description="将 JSON 转换为 XML、将 XML 转换为 JSON 的免费在线工具，支持自动格式识别和缩进设置。",
        h1="JSON ↔ XML 转换工具",
        lead="在左侧粘贴 JSON 或 XML，右侧会显示转换为另一种格式的结果。Formix 会自动识别粘贴的格式，你也可以手动选择转换方向。数据不会发送到服务器。",
        btn_format="转换", btn_sample="加载示例", btn_clear="清空",
        indent_label="缩进大小", indent2="2 个空格缩进", indent4="4 个空格缩进", indenttab="Tab 缩进",
        btn_copy="复制", btn_copy_minify="复制压缩结果", btn_download="下载结果",
        tabs_aria="切换输入/输出", tab_input="输入", tab_output="输出",
        status_idle="请粘贴 JSON 或 XML",
        input_search_mode_label="搜索方式", opt_contains="包含", opt_exact_line="精确匹配(行)", opt_regex="正则表达式",
        input_search_placeholder="在输入文本中搜索…", prev_title="上一个匹配项", next_title="下一个匹配项", clear_title="清除搜索",
        input_placeholder="在此粘贴 JSON 或 XML，格式将被自动识别。",
        output_label="输出", expand_all="▾ 全部展开", collapse_all="▸ 全部折叠",
        opt_exact="精确匹配", output_search_placeholder="在输出文本中搜索…",
        direction_label="转换方向", dir_auto="自动识别", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint='提示：在"自动识别"模式下，Formix 会根据粘贴文本的第一个字符({或[表示JSON，<表示XML)自动判断转换方向；'
             "如果格式不明确，可以在下拉菜单中手动选择方向。由于 JSON 和 XML 表达数据的方式本质上不同，"
             "转换遵循固定规则：JSON 数组中重复的值会转换为多个同名的 XML 元素，"
             'XML 属性(attribute)会保留在结果 JSON 的 "@attributes" 对象中。因此，经过 JSON → XML → JSON 的往返转换后，'
             "原始结构可能无法完全还原(例如，顶层数组会被包裹在 <root><item> 结构中)。这是任何通用转换工具都会有的正常特性。",
        usage_h2="使用方法",
        usage_items=[
            "在左侧输入框粘贴 JSON 或 XML，格式会被自动识别，转换结果会显示在右侧。",
            '如果自动识别的格式不符合预期，可以在"转换方向"下拉菜单中手动选择 JSON → XML 或 XML → JSON。',
            "如果输入不是有效的 JSON/XML，会提示大致的出错行/列位置。",
            '使用缩进大小下拉菜单调整转换结果的排版方式，然后通过"复制"或"下载结果"获取。',
            '"复制压缩结果"会复制去除所有不必要空白的转换结果，适合粘贴到配置文件或 API 请求中。',
            "所有处理均在浏览器内完成，输入的数据不会发送到服务器。",
        ],
        tips_h2="相关提示",
        tips_items=[
            "JSON 对象的键会成为 XML 元素名称；包含空格或符号、无法作为 XML 标签名的键会被自动清理(sanitize)。",
            '由于 XML 没有原生的数组类型，像 ["a", "b"] 这样的 JSON 数组会转换为两个同名的兄弟元素，而不是一个包含列表的元素。',
            '转换带有属性的 XML(例如 <book id="1">)时，属性会被保留在结果 JSON 的 "@attributes" 键下，不会丢失信息。',
            "如果只需要单独校验或格式化 JSON 或 XML，请尝试下方相关链接中的 JSON 格式化工具或 XML 格式化工具。",
        ],
    ),
    "es": dict(
        title="Convertidor JSON a XML / XML a JSON - Herramienta Gratuita en Línea | Formix",
        description="Convierte JSON a XML o XML a JSON al instante en tu navegador. Sea cual sea el formato que pegues, Formix lo detecta automáticamente, y también puedes elegir la dirección manualmente. Los datos nunca se envían a un servidor.",
        keywords="json to xml, xml to json, convertidor json xml, herramienta json xml, convertir json a xml, convertir xml a json, convertidor json xml en línea",
        og_title="Convertidor JSON a XML / XML a JSON | Formix",
        og_description="Un convertidor JSON ↔ XML en línea gratuito con detección automática de formato; todo el procesamiento ocurre en el navegador.",
        jsonld_name="Convertidor JSON a XML / XML a JSON",
        jsonld_description="Herramienta en línea gratuita para convertir JSON a XML y XML a JSON, con detección automática de formato y configuración de sangría.",
        h1="Convertidor JSON ↔ XML",
        lead="Pega JSON o XML a la izquierda y el resultado convertido al otro formato aparecerá a la derecha. Formix detecta automáticamente el formato pegado, pero también puedes elegir la dirección manualmente. Los datos nunca se envían a un servidor.",
        btn_format="Convertir", btn_sample="Cargar ejemplo", btn_clear="Limpiar",
        indent_label="Tamaño de sangría", indent2="Sangría de 2 espacios", indent4="Sangría de 4 espacios", indenttab="Sangría con Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar resultado minificado", btn_download="Descargar resultado",
        tabs_aria="Alternar entre entrada y salida", tab_input="Entrada", tab_output="Salida",
        status_idle="Pega JSON o XML",
        input_search_mode_label="Modo de búsqueda", opt_contains="Contiene", opt_exact_line="Coincidencia exacta (línea)", opt_regex="Regex",
        input_search_placeholder="Buscar en el texto de entrada…", prev_title="Coincidencia anterior", next_title="Siguiente coincidencia", clear_title="Limpiar búsqueda",
        input_placeholder="Pega JSON o XML aquí; el formato se detectará automáticamente.",
        output_label="Salida", expand_all="▾ Expandir todo", collapse_all="▸ Colapsar todo",
        opt_exact="Coincidencia exacta", output_search_placeholder="Buscar en el texto de salida…",
        direction_label="Dirección de conversión", dir_auto="Detección automática", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint='Consejo. En modo "Detección automática", Formix determina la dirección de conversión según el primer carácter del texto pegado ({ o [ indica JSON, < indica XML); '
             "si el formato no está claro, puedes elegir la dirección manualmente en el menú desplegable. Dado que JSON y XML representan los datos de forma fundamentalmente distinta, "
             "la conversión sigue reglas fijas: los valores repetidos en un arreglo JSON se convierten en varios elementos XML con el mismo nombre, "
             'y los atributos XML se conservan en un objeto "@attributes" en el JSON resultante. Por lo tanto, después de una conversión de ida y vuelta JSON → XML → JSON, '
             "la estructura original puede no restaurarse exactamente (por ejemplo, un arreglo de nivel superior quedará envuelto en una estructura <root><item>). Esta es una característica normal de cualquier herramienta de conversión genérica.",
        usage_h2="Cómo usar esta herramienta",
        usage_items=[
            "Pega JSON o XML en el cuadro de entrada de la izquierda, el formato se detecta automáticamente y el resultado convertido se muestra a la derecha.",
            'Si el formato detectado automáticamente no es el esperado, puedes elegir manualmente JSON → XML o XML → JSON en el menú desplegable "Dirección de conversión".',
            "Si la entrada no es JSON/XML válido, se te indicará una línea/columna aproximada de dónde está el error.",
            'Usa el menú de tamaño de sangría para ajustar el formato del resultado, luego obténlo con "Copiar" o "Descargar resultado".',
            '"Copiar resultado minificado" copia el resultado sin espacios innecesarios, ideal para pegar en archivos de configuración o solicitudes de API.',
            "Todo el procesamiento ocurre en tu navegador — los datos que ingresas nunca se envían a un servidor.",
        ],
        tips_h2="Consejos relacionados",
        tips_items=[
            "Las claves de un objeto JSON se convierten en nombres de elementos XML; las claves con espacios o símbolos que no son válidos como nombres de etiqueta XML se sanean automáticamente.",
            'Como XML no tiene un tipo de arreglo nativo, un arreglo JSON como ["a", "b"] se convierte en dos elementos hermanos con el mismo nombre, en lugar de un elemento que contiene una lista.',
            'Al convertir XML con atributos (por ejemplo, <book id="1">), los atributos se conservan bajo la clave "@attributes" del JSON resultante, sin perder información.',
            "Si solo necesitas validar o formatear JSON o XML por separado, prueba el Formateador JSON o el Formateador XML en los enlaces relacionados debajo.",
        ],
    ),
    "vi": dict(
        title="Chuyển đổi JSON sang XML / XML sang JSON - Công cụ Trực tuyến Miễn phí | Formix",
        description="Chuyển đổi JSON sang XML hoặc XML sang JSON ngay trong trình duyệt của bạn. Dù bạn dán định dạng nào, Formix sẽ tự động nhận diện, và bạn cũng có thể chọn hướng chuyển đổi theo cách thủ công. Dữ liệu không bao giờ được gửi lên máy chủ.",
        keywords="json to xml, xml to json, chuyển đổi json xml, công cụ json xml, chuyển json sang xml, chuyển xml sang json, chuyển đổi json xml trực tuyến",
        og_title="Chuyển đổi JSON sang XML / XML sang JSON | Formix",
        og_description="Công cụ chuyển đổi JSON ↔ XML trực tuyến miễn phí với nhận diện định dạng tự động; mọi xử lý diễn ra trong trình duyệt.",
        jsonld_name="Chuyển đổi JSON sang XML / XML sang JSON",
        jsonld_description="Công cụ trực tuyến miễn phí để chuyển đổi JSON sang XML và XML sang JSON, với nhận diện định dạng tự động và tùy chỉnh thụt lề.",
        h1="Chuyển đổi JSON ↔ XML",
        lead="Dán JSON hoặc XML vào bên trái, kết quả chuyển sang định dạng khác sẽ hiện ở bên phải. Formix tự động nhận diện định dạng được dán, nhưng bạn cũng có thể chọn hướng chuyển đổi theo cách thủ công. Dữ liệu không bao giờ được gửi lên máy chủ.",
        btn_format="Chuyển đổi", btn_sample="Tải ví dụ", btn_clear="Xóa",
        indent_label="Kích thước thụt lề", indent2="Thụt lề 2 khoảng trắng", indent4="Thụt lề 4 khoảng trắng", indenttab="Thụt lề Tab",
        btn_copy="Sao chép", btn_copy_minify="Sao chép kết quả rút gọn", btn_download="Tải kết quả xuống",
        tabs_aria="Chuyển đổi giữa nhập và kết quả", tab_input="Nhập", tab_output="Kết quả",
        status_idle="Hãy dán JSON hoặc XML",
        input_search_mode_label="Chế độ tìm kiếm", opt_contains="Chứa", opt_exact_line="Khớp chính xác (dòng)", opt_regex="Regex",
        input_search_placeholder="Tìm trong văn bản nhập…", prev_title="Kết quả trước", next_title="Kết quả tiếp theo", clear_title="Xóa tìm kiếm",
        input_placeholder="Dán JSON hoặc XML vào đây; định dạng sẽ được nhận diện tự động.",
        output_label="Kết quả", expand_all="▾ Mở rộng tất cả", collapse_all="▸ Thu gọn tất cả",
        opt_exact="Khớp chính xác", output_search_placeholder="Tìm trong văn bản kết quả…",
        direction_label="Hướng chuyển đổi", dir_auto="Tự động nhận diện", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint='Mẹo. Ở chế độ "Tự động nhận diện", Formix xác định hướng chuyển đổi dựa trên ký tự đầu tiên của văn bản dán ({ hoặc [ là JSON, < là XML); '
             "nếu định dạng không rõ ràng, bạn có thể chọn hướng thủ công trong menu thả xuống. Vì JSON và XML biểu diễn dữ liệu theo cách khác nhau về cơ bản, "
             "việc chuyển đổi tuân theo các quy tắc cố định: các giá trị lặp lại trong mảng JSON sẽ chuyển thành nhiều phần tử XML cùng tên, "
             'và các thuộc tính XML sẽ được giữ trong đối tượng "@attributes" của JSON kết quả. Do đó, sau khi chuyển đổi hai chiều JSON → XML → JSON, '
             "cấu trúc gốc có thể không được khôi phục hoàn toàn (ví dụ, một mảng cấp cao nhất sẽ được bọc trong cấu trúc <root><item>). Đây là đặc điểm bình thường của bất kỳ công cụ chuyển đổi tổng quát nào.",
        usage_h2="Cách sử dụng công cụ này",
        usage_items=[
            "Dán JSON hoặc XML vào khung nhập bên trái, định dạng sẽ được nhận diện tự động và kết quả chuyển đổi hiển thị ở bên phải.",
            'Nếu định dạng nhận diện tự động không như mong đợi, bạn có thể chọn thủ công JSON → XML hoặc XML → JSON trong menu thả xuống "Hướng chuyển đổi".',
            "Nếu nội dung nhập không phải JSON/XML hợp lệ, bạn sẽ được thông báo dòng/cột gần đúng của lỗi.",
            'Dùng menu kích thước thụt lề để điều chỉnh cách trình bày kết quả, sau đó lấy kết quả bằng "Sao chép" hoặc "Tải kết quả xuống".',
            '"Sao chép kết quả rút gọn" sẽ sao chép kết quả không có khoảng trắng dư, thích hợp để dán vào tệp cấu hình hoặc yêu cầu API.',
            "Mọi xử lý diễn ra trong trình duyệt của bạn — dữ liệu bạn nhập không bao giờ được gửi lên máy chủ.",
        ],
        tips_h2="Mẹo liên quan",
        tips_items=[
            "Khóa của đối tượng JSON sẽ trở thành tên phần tử XML; các khóa chứa khoảng trắng hoặc ký hiệu không hợp lệ làm tên thẻ XML sẽ được tự động làm sạch.",
            'Vì XML không có kiểu mảng gốc, một mảng JSON như ["a", "b"] sẽ chuyển thành hai phần tử anh em cùng tên, thay vì một phần tử chứa danh sách.',
            'Khi chuyển đổi XML có thuộc tính (ví dụ <book id="1">), các thuộc tính sẽ được giữ trong khóa "@attributes" của JSON kết quả, không bị mất thông tin.',
            "Nếu bạn chỉ cần kiểm tra hoặc định dạng JSON hoặc XML riêng lẻ, hãy thử Công cụ định dạng JSON hoặc Công cụ định dạng XML trong các liên kết liên quan bên dưới.",
        ],
    ),
    "pt": dict(
        title="Conversor JSON para XML / XML para JSON - Ferramenta Gratuita Online | Formix",
        description="Converta JSON para XML ou XML para JSON instantaneamente no seu navegador. Seja qual for o formato que você colar, o Formix detecta automaticamente, e você também pode escolher a direção manualmente. Os dados nunca são enviados a um servidor.",
        keywords="json to xml, xml to json, conversor json xml, ferramenta json xml, converter json para xml, converter xml para json, conversor json xml online",
        og_title="Conversor JSON para XML / XML para JSON | Formix",
        og_description="Um conversor JSON ↔ XML online gratuito com detecção automática de formato; todo o processamento ocorre no navegador.",
        jsonld_name="Conversor JSON para XML / XML para JSON",
        jsonld_description="Ferramenta online gratuita para converter JSON para XML e XML para JSON, com detecção automática de formato e configuração de recuo.",
        h1="Conversor JSON ↔ XML",
        lead="Cole JSON ou XML à esquerda e o resultado convertido para o outro formato aparecerá à direita. O Formix detecta automaticamente o formato colado, mas você também pode escolher a direção manualmente. Os dados nunca são enviados a um servidor.",
        btn_format="Converter", btn_sample="Carregar exemplo", btn_clear="Limpar",
        indent_label="Tamanho do recuo", indent2="Recuo de 2 espaços", indent4="Recuo de 4 espaços", indenttab="Recuo com Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar resultado minificado", btn_download="Baixar resultado",
        tabs_aria="Alternar entre entrada e saída", tab_input="Entrada", tab_output="Saída",
        status_idle="Cole JSON ou XML",
        input_search_mode_label="Modo de busca", opt_contains="Contém", opt_exact_line="Correspondência exata (linha)", opt_regex="Regex",
        input_search_placeholder="Buscar no texto de entrada…", prev_title="Correspondência anterior", next_title="Próxima correspondência", clear_title="Limpar busca",
        input_placeholder="Cole JSON ou XML aqui; o formato será detectado automaticamente.",
        output_label="Saída", expand_all="▾ Expandir tudo", collapse_all="▸ Recolher tudo",
        opt_exact="Correspondência exata", output_search_placeholder="Buscar no texto de saída…",
        direction_label="Direção da conversão", dir_auto="Detecção automática", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint='Dica. No modo "Detecção automática", o Formix determina a direção da conversão com base no primeiro caractere do texto colado ({ ou [ indica JSON, < indica XML); '
             "se o formato não estiver claro, você pode escolher a direção manualmente no menu suspenso. Como JSON e XML representam dados de formas fundamentalmente diferentes, "
             "a conversão segue regras fixas: valores repetidos em um array JSON são convertidos em múltiplos elementos XML com o mesmo nome, "
             'e atributos XML são preservados em um objeto "@attributes" no JSON resultante. Portanto, após uma conversão de ida e volta JSON → XML → JSON, '
             "a estrutura original pode não ser restaurada exatamente (por exemplo, um array de nível superior ficará envolvido em uma estrutura <root><item>). Esta é uma característica normal de qualquer ferramenta de conversão genérica.",
        usage_h2="Como usar esta ferramenta",
        usage_items=[
            "Cole JSON ou XML na caixa de entrada à esquerda, o formato é detectado automaticamente e o resultado convertido é exibido à direita.",
            'Se o formato detectado automaticamente não for o esperado, você pode escolher manualmente JSON → XML ou XML → JSON no menu suspenso "Direção da conversão".',
            "Se a entrada não for JSON/XML válido, você será informado de uma linha/coluna aproximada do erro.",
            'Use o menu de tamanho de recuo para ajustar a formatação do resultado, depois obtenha-o com "Copiar" ou "Baixar resultado".',
            '"Copiar resultado minificado" copia o resultado sem espaços desnecessários, ideal para colar em arquivos de configuração ou requisições de API.',
            "Todo o processamento ocorre no seu navegador — os dados que você insere nunca são enviados a um servidor.",
        ],
        tips_h2="Dicas relacionadas",
        tips_items=[
            "As chaves de um objeto JSON se tornam nomes de elementos XML; chaves com espaços ou símbolos que não são válidos como nomes de tag XML são automaticamente higienizadas.",
            'Como XML não tem um tipo de array nativo, um array JSON como ["a", "b"] é convertido em dois elementos irmãos com o mesmo nome, em vez de um elemento contendo uma lista.',
            'Ao converter XML com atributos (por exemplo, <book id="1">), os atributos são preservados sob a chave "@attributes" do JSON resultante, sem perda de informação.',
            "Se você só precisa validar ou formatar JSON ou XML separadamente, experimente o Formatador JSON ou o Formatador XML nos links relacionados abaixo.",
        ],
    ),
    "id": dict(
        title="Konverter JSON ke XML / XML ke JSON - Alat Online Gratis | Formix",
        description="Konversi JSON ke XML atau XML ke JSON secara instan di browser Anda. Apa pun format yang Anda tempel, Formix akan mendeteksinya secara otomatis, dan Anda juga dapat memilih arah secara manual. Data tidak pernah dikirim ke server.",
        keywords="json to xml, xml to json, konverter json xml, alat json xml, konversi json ke xml, konversi xml ke json, konverter json xml online",
        og_title="Konverter JSON ke XML / XML ke JSON | Formix",
        og_description="Konverter JSON ↔ XML online gratis dengan deteksi format otomatis; semua pemrosesan terjadi di browser.",
        jsonld_name="Konverter JSON ke XML / XML ke JSON",
        jsonld_description="Alat online gratis untuk mengonversi JSON ke XML dan XML ke JSON, dengan deteksi format otomatis dan pengaturan indentasi.",
        h1="Konverter JSON ↔ XML",
        lead="Tempel JSON atau XML di sebelah kiri, dan hasil konversi ke format lain akan muncul di sebelah kanan. Formix secara otomatis mendeteksi format yang ditempel, tetapi Anda juga dapat memilih arah secara manual. Data tidak pernah dikirim ke server.",
        btn_format="Konversi", btn_sample="Muat contoh", btn_clear="Hapus",
        indent_label="Ukuran indentasi", indent2="Indentasi 2 spasi", indent4="Indentasi 4 spasi", indenttab="Indentasi Tab",
        btn_copy="Salin", btn_copy_minify="Salin hasil yang diminifikasi", btn_download="Unduh hasil",
        tabs_aria="Beralih antara input dan output", tab_input="Input", tab_output="Output",
        status_idle="Tempel JSON atau XML",
        input_search_mode_label="Mode pencarian", opt_contains="Berisi", opt_exact_line="Kecocokan tepat (baris)", opt_regex="Regex",
        input_search_placeholder="Cari di teks input…", prev_title="Hasil sebelumnya", next_title="Hasil berikutnya", clear_title="Hapus pencarian",
        input_placeholder="Tempel JSON atau XML di sini; format akan dideteksi secara otomatis.",
        output_label="Output", expand_all="▾ Buka semua", collapse_all="▸ Lipat semua",
        opt_exact="Kecocokan tepat", output_search_placeholder="Cari di teks output…",
        direction_label="Arah konversi", dir_auto="Deteksi otomatis", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint='Tips. Dalam mode "Deteksi otomatis", Formix menentukan arah konversi berdasarkan karakter pertama dari teks yang ditempel ({ atau [ menunjukkan JSON, < menunjukkan XML); '
             "jika formatnya tidak jelas, Anda dapat memilih arah secara manual di menu dropdown. Karena JSON dan XML merepresentasikan data secara fundamental berbeda, "
             "konversi mengikuti aturan tetap: nilai berulang dalam array JSON akan dikonversi menjadi beberapa elemen XML dengan nama yang sama, "
             'dan atribut XML akan dipertahankan dalam objek "@attributes" pada JSON hasil. Oleh karena itu, setelah konversi bolak-balik JSON → XML → JSON, '
             "struktur asli mungkin tidak dapat dipulihkan secara tepat (misalnya, array tingkat atas akan dibungkus dalam struktur <root><item>). Ini adalah karakteristik normal dari alat konversi generik mana pun.",
        usage_h2="Cara menggunakan alat ini",
        usage_items=[
            "Tempel JSON atau XML ke kotak input di sebelah kiri, format akan dideteksi secara otomatis dan hasil konversi ditampilkan di sebelah kanan.",
            'Jika format yang dideteksi otomatis tidak sesuai harapan, Anda dapat memilih JSON → XML atau XML → JSON secara manual di menu dropdown "Arah konversi".',
            "Jika input bukan JSON/XML yang valid, Anda akan diberi tahu perkiraan baris/kolom kesalahan.",
            'Gunakan menu ukuran indentasi untuk menyesuaikan format hasil, lalu dapatkan dengan "Salin" atau "Unduh hasil".',
            '"Salin hasil yang diminifikasi" menyalin hasil tanpa spasi yang tidak perlu, cocok untuk ditempel ke file konfigurasi atau permintaan API.',
            "Semua pemrosesan terjadi di browser Anda — data yang Anda masukkan tidak pernah dikirim ke server.",
        ],
        tips_h2="Tips terkait",
        tips_items=[
            "Kunci objek JSON akan menjadi nama elemen XML; kunci yang mengandung spasi atau simbol yang tidak valid sebagai nama tag XML akan dibersihkan secara otomatis.",
            'Karena XML tidak memiliki tipe array asli, array JSON seperti ["a", "b"] akan dikonversi menjadi dua elemen saudara dengan nama yang sama, bukan satu elemen yang berisi daftar.',
            'Saat mengonversi XML dengan atribut (misalnya, <book id="1">), atribut akan dipertahankan di bawah kunci "@attributes" pada JSON hasil, tanpa kehilangan informasi.',
            "Jika Anda hanya perlu memvalidasi atau memformat JSON atau XML secara terpisah, coba Pemformat JSON atau Pemformat XML di tautan terkait di bawah.",
        ],
    ),
    "de": dict(
        title="JSON-zu-XML / XML-zu-JSON Konverter - Kostenloses Online-Tool | Formix",
        description="Konvertieren Sie JSON zu XML oder XML zu JSON sofort in Ihrem Browser. Welches Format Sie auch einfügen, Formix erkennt es automatisch, und Sie können die Richtung auch manuell wählen. Daten werden nie an einen Server gesendet.",
        keywords="json to xml, xml to json, json xml konverter, json xml tool, json in xml umwandeln, xml in json umwandeln, json xml konverter online",
        og_title="JSON-zu-XML / XML-zu-JSON Konverter | Formix",
        og_description="Ein kostenloser Online-JSON-↔-XML-Konverter mit automatischer Formaterkennung; die gesamte Verarbeitung erfolgt im Browser.",
        jsonld_name="JSON-zu-XML / XML-zu-JSON Konverter",
        jsonld_description="Kostenloses Online-Tool zum Konvertieren von JSON zu XML und XML zu JSON, mit automatischer Formaterkennung und Einrückungseinstellung.",
        h1="JSON ↔ XML Konverter",
        lead="Fügen Sie links JSON oder XML ein, und das in das andere Format konvertierte Ergebnis wird rechts angezeigt. Formix erkennt das eingefügte Format automatisch, Sie können die Richtung aber auch manuell wählen. Daten werden nie an einen Server gesendet.",
        btn_format="Konvertieren", btn_sample="Beispiel laden", btn_clear="Leeren",
        indent_label="Einrückungsgröße", indent2="2-Leerzeichen-Einrückung", indent4="4-Leerzeichen-Einrückung", indenttab="Tab-Einrückung",
        btn_copy="Kopieren", btn_copy_minify="Minifiziertes Ergebnis kopieren", btn_download="Ergebnis herunterladen",
        tabs_aria="Zwischen Eingabe und Ausgabe wechseln", tab_input="Eingabe", tab_output="Ausgabe",
        status_idle="JSON oder XML einfügen",
        input_search_mode_label="Suchmodus", opt_contains="Enthält", opt_exact_line="Exakte Übereinstimmung (Zeile)", opt_regex="Regex",
        input_search_placeholder="Im Eingabetext suchen…", prev_title="Vorherige Übereinstimmung", next_title="Nächste Übereinstimmung", clear_title="Suche leeren",
        input_placeholder="Fügen Sie hier JSON oder XML ein; das Format wird automatisch erkannt.",
        output_label="Ausgabe", expand_all="▾ Alle ausklappen", collapse_all="▸ Alle einklappen",
        opt_exact="Exakte Übereinstimmung", output_search_placeholder="Im Ausgabetext suchen…",
        direction_label="Konvertierungsrichtung", dir_auto="Automatische Erkennung", dir_json2xml="JSON → XML", dir_xml2json="XML → JSON",
        hint='Tipp. Im Modus „Automatische Erkennung" bestimmt Formix die Konvertierungsrichtung anhand des ersten Zeichens des eingefügten Textes ({ oder [ bedeutet JSON, < bedeutet XML); '
             "ist das Format unklar, können Sie die Richtung manuell im Dropdown-Menü wählen. Da JSON und XML Daten grundlegend unterschiedlich darstellen, "
             "folgt die Konvertierung festen Regeln: Wiederholte Werte in einem JSON-Array werden in mehrere XML-Elemente mit demselben Namen umgewandelt, "
             'und XML-Attribute werden in einem „@attributes"-Objekt im resultierenden JSON erhalten. Nach einer Hin-und-Rück-Konvertierung JSON → XML → JSON '
             "kann die ursprüngliche Struktur daher möglicherweise nicht exakt wiederhergestellt werden (z. B. wird ein Array der obersten Ebene in eine <root><item>-Struktur eingeschlossen). Dies ist ein normales Merkmal jedes generischen Konvertierungstools.",
        usage_h2="So verwenden Sie dieses Tool",
        usage_items=[
            "Fügen Sie JSON oder XML in das Eingabefeld links ein, das Format wird automatisch erkannt und das konvertierte Ergebnis rechts angezeigt.",
            'Wenn das automatisch erkannte Format nicht Ihren Erwartungen entspricht, können Sie im Dropdown-Menü „Konvertierungsrichtung" manuell JSON → XML oder XML → JSON wählen.',
            "Wenn die Eingabe kein gültiges JSON/XML ist, erhalten Sie eine ungefähre Zeile/Spalte des Fehlers.",
            'Verwenden Sie das Einrückungsgrößen-Menü, um die Formatierung des Ergebnisses anzupassen, und holen Sie es dann über „Kopieren" oder „Ergebnis herunterladen".',
            '„Minifiziertes Ergebnis kopieren" kopiert das Ergebnis ohne unnötige Leerzeichen — ideal zum Einfügen in Konfigurationsdateien oder API-Anfragen.',
            "Die gesamte Verarbeitung erfolgt in Ihrem Browser — die von Ihnen eingegebenen Daten werden nie an einen Server gesendet.",
        ],
        tips_h2="Verwandte Tipps",
        tips_items=[
            "Schlüssel eines JSON-Objekts werden zu XML-Elementnamen; Schlüssel mit Leerzeichen oder Symbolen, die als XML-Tag-Namen ungültig sind, werden automatisch bereinigt.",
            'Da XML keinen nativen Array-Typ hat, wird ein JSON-Array wie ["a", "b"] in zwei gleichnamige Geschwisterelemente umgewandelt, statt in ein Element, das eine Liste enthält.',
            'Beim Konvertieren von XML mit Attributen (z. B. <book id="1">) werden die Attribute unter dem Schlüssel „@attributes" im resultierenden JSON erhalten, ohne Informationsverlust.',
            "Wenn Sie nur JSON oder XML separat validieren oder formatieren möchten, probieren Sie den JSON-Formatierer oder den XML-Formatierer in den verwandten Links unten.",
        ],
    ),
}

CONTENT["tool_sql"] = {
    "en": dict(
        title="SQL Formatter / Beautifier - Free Online Tool | Formix",
        description="Beautify and indent SQL queries online, free. Supports MySQL, PostgreSQL, SQL Server, Oracle PL/SQL, BigQuery, Snowflake, and more. Runs entirely in your browser — nothing is sent to a server.",
        keywords="sql formatter, sql beautifier, format sql online, sql pretty print, mysql formatter, postgresql formatter, online sql formatter free",
        og_title="SQL Formatter / Beautifier | Formix",
        og_description="A free online SQL formatter that beautifies queries with proper indentation, supporting multiple SQL dialects. Runs entirely in your browser.",
        jsonld_name="SQL Formatter / Beautifier",
        jsonld_description="A free online tool that beautifies SQL queries with indentation and keyword casing, supporting multiple SQL dialects.",
        h1="SQL Formatter",
        lead="Paste a SQL query on the left and get a neatly indented, readable version on the right. Choose the SQL dialect that matches your database for the most accurate result. Nothing is sent to a server.",
        btn_format="Format", btn_sample="Load sample", btn_clear="Clear",
        indent_label="Indent size", indent2="2-space indent", indent4="4-space indent", indenttab="Tab indent",
        btn_copy="Copy", btn_copy_minify="Copy minified", btn_download="Download result",
        tabs_aria="Switch between input and output", tab_input="Input", tab_output="Output",
        status_idle="Paste a SQL query",
        input_search_mode_label="Search mode", opt_contains="Contains", opt_exact_line="Exact (line)", opt_regex="Regex",
        input_search_placeholder="Search the input text…", prev_title="Previous match", next_title="Next match", clear_title="Clear search",
        input_placeholder="Paste a SQL query here, e.g. SELECT * FROM users WHERE id = 1",
        output_label="Output", expand_all="▾ Expand all", collapse_all="▸ Collapse all",
        opt_exact="Exact", output_search_placeholder="Search the output text…",
        dialect_label="SQL dialect",
        dialect_standard="Standard SQL", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint="Tip. This tool beautifies (reformats) SQL — it does not validate whether the query is semantically correct or would run "
             "successfully against a real database. Pick the dialect closest to the database you use for the best formatting result. "
             "If the query can't be parsed at all (for example, unbalanced parentheses or quotes), an approximate error location is shown. "
             "Keywords are uppercased by default, following common SQL style conventions. This tool bundles the open-source "
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> '
             "library (MIT License) locally, so formatting still happens entirely in your browser.",
        usage_h2="How to use this tool",
        usage_items=[
            "Paste your SQL query into the input box on the left.",
            'Pick the "SQL dialect" that matches your database (MySQL, PostgreSQL, SQL Server, and more) for the most accurate formatting.',
            'Click "Format" (or just wait — it also formats automatically as you type) to see the beautified result on the right.',
            "If the query can't be parsed, you'll get an approximate line/column for where the problem is.",
            'Use the indent-size dropdown to control the output indentation, then "Copy" or "Download result" to grab it.',
            "Everything happens in your browser — your SQL is never sent to a server.",
        ],
        tips_h2="Related tips",
        tips_items=[
            "This tool formats/beautifies SQL — it doesn't check whether the query is valid against your actual database schema or would execute successfully.",
            "Different dialects have different keyword sets and syntax quirks (e.g. LIMIT vs TOP, backticks vs double quotes); pick the one matching your database for best results.",
            "Keywords (SELECT, FROM, WHERE, and so on) are uppercased automatically, a common convention for readability.",
            "Need to also work with JSON or XML? Try the dedicated JSON Formatter, XML Formatter, or JSON ↔ XML Converter tools linked below.",
        ],
    ),
    "ko": dict(
        title="SQL 포매터 / 쿼리 정렬기 - 무료 온라인 도구 | Formix",
        description="SQL 쿼리를 무료로 온라인에서 들여쓰기하고 보기 좋게 정리하세요. MySQL, PostgreSQL, SQL Server, Oracle PL/SQL, BigQuery, Snowflake 등을 지원합니다. 모든 처리는 브라우저 안에서만 이뤄지며 서버로 전송되지 않습니다.",
        keywords="sql 포매터, sql 정렬, 온라인 sql 포맷터, sql 예쁘게 만들기, mysql 포매터, postgresql 포매터, 무료 sql 정리 도구",
        og_title="SQL 포매터 / 쿼리 정렬기 | Formix",
        og_description="여러 SQL 방언을 지원하는 무료 온라인 SQL 포매터. 모든 처리는 브라우저 안에서 이뤄집니다.",
        jsonld_name="SQL 포매터 / 쿼리 정렬기",
        jsonld_description="SQL 쿼리를 들여쓰기와 키워드 대소문자로 보기 좋게 정리해주는 무료 온라인 도구. 여러 SQL 방언을 지원합니다.",
        h1="SQL 포매터",
        lead="왼쪽에 SQL 쿼리를 붙여넣으면 오른쪽에 보기 좋게 들여쓰기된 결과가 표시됩니다. 사용 중인 데이터베이스에 맞는 SQL 방언을 선택하면 더 정확한 결과를 얻을 수 있습니다. 데이터는 서버로 전송되지 않습니다.",
        btn_format="정렬", btn_sample="예시 불러오기", btn_clear="지우기",
        indent_label="들여쓰기 크기", indent2="들여쓰기 2칸", indent4="들여쓰기 4칸", indenttab="들여쓰기 Tab",
        btn_copy="복사", btn_copy_minify="압축 복사", btn_download="결과 다운로드",
        tabs_aria="입력/결과 전환", tab_input="입력", tab_output="결과",
        status_idle="SQL 쿼리를 붙여넣어주세요",
        input_search_mode_label="검색 방식", opt_contains="포함", opt_exact_line="일치(줄)", opt_regex="정규식",
        input_search_placeholder="입력한 텍스트에서 검색…", prev_title="이전 일치 항목", next_title="다음 일치 항목", clear_title="검색어 지우기",
        input_placeholder="여기에 SQL 쿼리를 붙여넣으세요. 예: SELECT * FROM users WHERE id = 1",
        output_label="결과", expand_all="▾ 모두 펼치기", collapse_all="▸ 모두 접기",
        opt_exact="일치", output_search_placeholder="결과 텍스트에서 검색…",
        dialect_label="SQL 방언",
        dialect_standard="표준 SQL", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint='Tip. 이 도구는 SQL을 보기 좋게 "정렬(포맷팅)"할 뿐, 쿼리가 실제 데이터베이스에서 의미적으로 올바르게 실행되는지는 '
             "검증하지 않습니다. 사용 중인 데이터베이스에 가장 가까운 방언을 선택하면 더 정확한 결과를 얻을 수 있습니다. "
             "괄호나 따옴표가 맞지 않는 등 구문 자체를 해석할 수 없는 경우 대략적인 오류 위치를 표시합니다. "
             "키워드는 일반적인 SQL 스타일 관례에 따라 기본적으로 대문자로 변환됩니다. 이 도구는 오픈소스 "
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> '
             "라이브러리(MIT 라이선스)를 로컬에 내장하여 사용하므로, 처리는 여전히 브라우저 안에서만 이뤄집니다.",
        usage_h2="이 도구는 이렇게 사용하세요",
        usage_items=[
            "왼쪽 입력창에 SQL 쿼리를 붙여넣으세요.",
            '사용 중인 데이터베이스에 맞는 "SQL 방언"(MySQL, PostgreSQL, SQL Server 등)을 선택하면 더 정확하게 정렬됩니다.',
            '"정렬" 버튼을 클릭하거나(입력하는 동안 자동으로도 정렬됩니다) 오른쪽에서 결과를 확인하세요.',
            "구문을 해석할 수 없으면 오류가 발생한 대략적인 줄/열 위치를 알려줍니다.",
            '들여쓰기 크기 드롭다운으로 결과의 들여쓰기를 조절한 뒤, "복사" 또는 "결과 다운로드"로 가져갈 수 있습니다.',
            "모든 처리는 브라우저 안에서만 이뤄지며, 입력한 SQL은 서버로 전송되지 않습니다.",
        ],
        tips_h2="관련 팁",
        tips_items=[
            "이 도구는 SQL을 정렬/포맷팅할 뿐, 실제 데이터베이스 스키마 기준으로 쿼리가 유효한지나 실행 가능한지는 검사하지 않습니다.",
            "방언마다 키워드와 문법 차이가 있습니다(예: LIMIT vs TOP, 백틱 vs 큰따옴표). 사용 중인 데이터베이스에 맞는 방언을 선택하세요.",
            "SELECT, FROM, WHERE 같은 키워드는 가독성을 위한 일반적인 관례에 따라 자동으로 대문자로 변환됩니다.",
            "JSON이나 XML 작업도 필요하다면, 아래 관련 링크의 JSON 포매터, XML 포매터, JSON ↔ XML 변환기를 사용해보세요.",
        ],
    ),
    "ja": dict(
        title="SQLフォーマッター / 整形ツール - 無料オンラインツール | Formix",
        description="SQLクエリを無料でオンライン整形・インデントできます。MySQL、PostgreSQL、SQL Server、Oracle PL/SQL、BigQuery、Snowflakeなどに対応。すべての処理はブラウザ内で行われ、サーバーには送信されません。",
        keywords="sql フォーマッター, sql 整形, オンライン sql フォーマッター, sql 見やすく, mysql フォーマッター, postgresql フォーマッター, 無料 sql 整形ツール",
        og_title="SQLフォーマッター / 整形ツール | Formix",
        og_description="複数のSQL方言に対応した無料オンラインSQLフォーマッター。すべての処理はブラウザ内で行われます。",
        jsonld_name="SQLフォーマッター / 整形ツール",
        jsonld_description="SQLクエリをインデントとキーワードの大文字化で見やすく整形する無料オンラインツール。複数のSQL方言に対応しています。",
        h1="SQLフォーマッター",
        lead="左側にSQLクエリを貼り付けると、右側に見やすくインデントされた結果が表示されます。お使いのデータベースに合ったSQL方言を選択すると、より正確な結果が得られます。データはサーバーに送信されません。",
        btn_format="整形", btn_sample="例を読み込む", btn_clear="クリア",
        indent_label="インデントサイズ", indent2="インデント2文字", indent4="インデント4文字", indenttab="インデントTab",
        btn_copy="コピー", btn_copy_minify="圧縮コピー", btn_download="結果をダウンロード",
        tabs_aria="入力/結果切り替え", tab_input="入力", tab_output="結果",
        status_idle="SQLクエリを貼り付けてください",
        input_search_mode_label="検索モード", opt_contains="含む", opt_exact_line="完全一致(行)", opt_regex="正規表現",
        input_search_placeholder="入力テキストを検索…", prev_title="前の一致", next_title="次の一致", clear_title="検索をクリア",
        input_placeholder="ここにSQLクエリを貼り付けてください。例: SELECT * FROM users WHERE id = 1",
        output_label="結果", expand_all="▾ すべて展開", collapse_all="▸ すべて折りたたむ",
        opt_exact="完全一致", output_search_placeholder="結果テキストを検索…",
        dialect_label="SQL方言",
        dialect_standard="標準SQL", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint="Tip. このツールはSQLを見やすく「整形」するだけで、クエリが実際のデータベースで意味的に正しく実行できるかどうかは検証しません。"
             "お使いのデータベースに最も近い方言を選択すると、より正確な整形結果が得られます。"
             "括弧や引用符が対応していないなど、構文自体を解析できない場合はおおよそのエラー位置が表示されます。"
             "キーワードは一般的なSQLのスタイル規約に従い、デフォルトで大文字に変換されます。このツールはオープンソースの"
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a>'
             "ライブラリ(MITライセンス)をローカルにバンドルしているため、処理は引き続きブラウザ内で完結します。",
        usage_h2="このツールの使い方",
        usage_items=[
            "左側の入力欄にSQLクエリを貼り付けます。",
            "お使いのデータベースに合った「SQL方言」(MySQL、PostgreSQL、SQL Serverなど)を選択すると、より正確に整形されます。",
            "「整形」ボタンをクリックするか(入力中も自動で整形されます)、右側で結果を確認してください。",
            "構文を解析できない場合は、問題が発生したおおよその行/列位置が表示されます。",
            "インデントサイズのドロップダウンで出力のインデントを調整し、「コピー」または「結果をダウンロード」で取得できます。",
            "すべての処理はブラウザ内で行われ、入力したSQLがサーバーに送信されることはありません。",
        ],
        tips_h2="関連のヒント",
        tips_items=[
            "このツールはSQLの整形のみを行い、実際のデータベーススキーマに対してクエリが有効か、実行可能かは検証しません。",
            "方言によってキーワードや構文が異なります(例: LIMIT と TOP、バッククォートとダブルクォートなど)。お使いのデータベースに合った方言を選択してください。",
            "SELECT、FROM、WHEREなどのキーワードは、可読性のための一般的な慣例に従い自動的に大文字に変換されます。",
            "JSONやXMLの作業も必要な場合は、下記の関連リンクにあるJSONフォーマッター、XMLフォーマッター、JSON ↔ XML 変換ツールもご利用ください。",
        ],
    ),
    "zh": dict(
        title="SQL 格式化工具 / 美化工具 - 免费在线工具 | Formix",
        description="免费在线格式化和缩进 SQL 查询语句。支持 MySQL、PostgreSQL、SQL Server、Oracle PL/SQL、BigQuery、Snowflake 等。所有处理均在浏览器中完成，不会发送到服务器。",
        keywords="sql 格式化, sql 美化, 在线 sql 格式化工具, sql 语句整理, mysql 格式化, postgresql 格式化, 免费 sql 整理工具",
        og_title="SQL 格式化工具 / 美化工具 | Formix",
        og_description="支持多种 SQL 方言的免费在线 SQL 格式化工具，所有处理均在浏览器中完成。",
        jsonld_name="SQL 格式化工具 / 美化工具",
        jsonld_description="通过缩进和关键字大小写格式化，让 SQL 查询更易读的免费在线工具，支持多种 SQL 方言。",
        h1="SQL 格式化工具",
        lead="在左侧粘贴 SQL 查询语句，右侧会显示带有清晰缩进的易读结果。选择与您所用数据库匹配的 SQL 方言可获得更准确的结果。数据不会发送到服务器。",
        btn_format="格式化", btn_sample="加载示例", btn_clear="清空",
        indent_label="缩进大小", indent2="2 格缩进", indent4="4 格缩进", indenttab="Tab 缩进",
        btn_copy="复制", btn_copy_minify="复制压缩结果", btn_download="下载结果",
        tabs_aria="切换输入/结果", tab_input="输入", tab_output="结果",
        status_idle="请粘贴 SQL 查询语句",
        input_search_mode_label="搜索模式", opt_contains="包含", opt_exact_line="精确匹配(整行)", opt_regex="正则表达式",
        input_search_placeholder="在输入文本中搜索…", prev_title="上一个匹配项", next_title="下一个匹配项", clear_title="清除搜索",
        input_placeholder="在此粘贴 SQL 查询语句，例如：SELECT * FROM users WHERE id = 1",
        output_label="结果", expand_all="▾ 全部展开", collapse_all="▸ 全部折叠",
        opt_exact="精确匹配", output_search_placeholder="在结果文本中搜索…",
        dialect_label="SQL 方言",
        dialect_standard="标准 SQL", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint='提示。此工具只对 SQL 进行"格式化(美化)"，并不会验证查询在实际数据库中语义上是否正确或能否成功执行。'
             "选择与您所用数据库最接近的方言可获得更准确的格式化结果。"
             "如果查询完全无法解析(例如括号或引号不匹配)，将显示大致的错误位置。"
             "关键字默认会按照常见的 SQL 风格约定转换为大写。此工具在本地打包(vendor)了开源的 "
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> '
             "库(MIT 许可)，因此格式化处理仍完全在您的浏览器中进行。",
        usage_h2="使用方法",
        usage_items=[
            "将 SQL 查询语句粘贴到左侧的输入框中。",
            '选择与您所用数据库匹配的"SQL 方言"(MySQL、PostgreSQL、SQL Server 等)以获得更准确的格式化结果。',
            '点击"格式化"按钮(输入时也会自动格式化)，即可在右侧查看美化后的结果。',
            "如果查询无法解析，会提示大致的出错行/列位置。",
            '使用缩进大小下拉菜单调整输出的缩进方式，然后通过"复制"或"下载结果"获取。',
            "所有处理均在浏览器内完成，您输入的 SQL 不会发送到服务器。",
        ],
        tips_h2="相关提示",
        tips_items=[
            "此工具仅对 SQL 进行格式化/美化，不会检查查询是否符合您实际的数据库结构或是否能成功执行。",
            "不同方言的关键字和语法存在差异(例如 LIMIT 与 TOP、反引号与双引号等)，请选择与您所用数据库匹配的方言以获得最佳效果。",
            "SELECT、FROM、WHERE 等关键字会按照提升可读性的常见约定自动转换为大写。",
            "如果还需要处理 JSON 或 XML，请尝试下方相关链接中的 JSON 格式化工具、XML 格式化工具或 JSON ↔ XML 转换工具。",
        ],
    ),
    "es": dict(
        title="Formateador SQL / Herramienta de Embellecimiento - Herramienta Gratuita en Línea | Formix",
        description="Formatea e indenta consultas SQL gratis en línea. Compatible con MySQL, PostgreSQL, SQL Server, Oracle PL/SQL, BigQuery, Snowflake y más. Todo el procesamiento ocurre en tu navegador, nunca se envía a un servidor.",
        keywords="formateador sql, embellecer sql, formateador sql en línea, formatear consultas sql, formateador mysql, formateador postgresql, herramienta sql gratis",
        og_title="Formateador SQL / Herramienta de Embellecimiento | Formix",
        og_description="Un formateador SQL en línea gratuito compatible con varios dialectos SQL; todo el procesamiento ocurre en el navegador.",
        jsonld_name="Formateador SQL / Herramienta de Embellecimiento",
        jsonld_description="Herramienta en línea gratuita que hace que las consultas SQL sean más legibles mediante sangría y formato de palabras clave, compatible con varios dialectos SQL.",
        h1="Formateador SQL",
        lead="Pega una consulta SQL a la izquierda y verás un resultado legible con sangría clara a la derecha. Elige el dialecto SQL que coincida con tu base de datos para obtener resultados más precisos. Los datos nunca se envían a un servidor.",
        btn_format="Formatear", btn_sample="Cargar ejemplo", btn_clear="Limpiar",
        indent_label="Tamaño de sangría", indent2="Sangría de 2 espacios", indent4="Sangría de 4 espacios", indenttab="Sangría con Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar resultado minificado", btn_download="Descargar resultado",
        tabs_aria="Alternar entre entrada y resultado", tab_input="Entrada", tab_output="Resultado",
        status_idle="Pega una consulta SQL",
        input_search_mode_label="Modo de búsqueda", opt_contains="Contiene", opt_exact_line="Coincidencia exacta (línea)", opt_regex="Regex",
        input_search_placeholder="Buscar en el texto de entrada…", prev_title="Coincidencia anterior", next_title="Siguiente coincidencia", clear_title="Limpiar búsqueda",
        input_placeholder="Pega tu consulta SQL aquí, por ejemplo: SELECT * FROM users WHERE id = 1",
        output_label="Resultado", expand_all="▾ Expandir todo", collapse_all="▸ Colapsar todo",
        opt_exact="Coincidencia exacta", output_search_placeholder="Buscar en el texto del resultado…",
        dialect_label="Dialecto SQL",
        dialect_standard="SQL estándar", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint='Consejo. Esta herramienta solo "formatea (embellece)" el SQL; no valida si la consulta es semánticamente correcta o ejecutable en una base de datos real. '
             "Elegir el dialecto más cercano a tu base de datos da resultados de formateo más precisos. "
             "Si la consulta no se puede analizar en absoluto (por ejemplo, paréntesis o comillas sin cerrar), se mostrará una posición de error aproximada. "
             "Las palabras clave se convierten a mayúsculas por defecto, siguiendo una convención común de estilo SQL. Esta herramienta incluye localmente la biblioteca de código abierto "
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> '
             "(licencia MIT), por lo que el formateo sigue ocurriendo enteramente en tu navegador.",
        usage_h2="Cómo usar esta herramienta",
        usage_items=[
            "Pega una consulta SQL en el cuadro de entrada de la izquierda.",
            'Elige el "Dialecto SQL" que coincida con tu base de datos (MySQL, PostgreSQL, SQL Server, etc.) para obtener resultados de formateo más precisos.',
            'Haz clic en "Formatear" (también se formatea automáticamente mientras escribes) para ver el resultado embellecido a la derecha.',
            "Si la consulta no se puede analizar, obtendrás una línea/columna aproximada de dónde está el error.",
            'Usa el menú de tamaño de sangría para ajustar la sangría del resultado, luego obtenlo con "Copiar" o "Descargar resultado".',
            "Todo el procesamiento ocurre en tu navegador — el SQL que ingresas nunca se envía a un servidor.",
        ],
        tips_h2="Consejos relacionados",
        tips_items=[
            "Esta herramienta solo formatea/embellece el SQL; no verifica si la consulta coincide con el esquema real de tu base de datos ni si se ejecutará correctamente.",
            "Las palabras clave y la sintaxis varían entre dialectos (por ejemplo, LIMIT vs. TOP, comillas invertidas vs. comillas dobles); elige el dialecto que coincida con tu base de datos para mejores resultados.",
            "Palabras clave como SELECT, FROM y WHERE se convierten automáticamente a mayúsculas siguiendo una convención común que mejora la legibilidad.",
            "Si también necesitas trabajar con JSON o XML, prueba el Formateador JSON, el Formateador XML o el Convertidor JSON ↔ XML en los enlaces relacionados debajo.",
        ],
    ),
    "vi": dict(
        title="Công cụ định dạng SQL / Làm đẹp SQL - Công cụ Trực tuyến Miễn phí | Formix",
        description="Định dạng và thụt lề câu lệnh SQL miễn phí trực tuyến. Hỗ trợ MySQL, PostgreSQL, SQL Server, Oracle PL/SQL, BigQuery, Snowflake và nhiều hơn nữa. Mọi xử lý diễn ra trong trình duyệt, không bao giờ gửi lên máy chủ.",
        keywords="định dạng sql, làm đẹp sql, công cụ định dạng sql trực tuyến, định dạng câu lệnh sql, định dạng mysql, định dạng postgresql, công cụ sql miễn phí",
        og_title="Công cụ định dạng SQL / Làm đẹp SQL | Formix",
        og_description="Công cụ định dạng SQL trực tuyến miễn phí hỗ trợ nhiều phương ngữ SQL; mọi xử lý diễn ra trong trình duyệt.",
        jsonld_name="Công cụ định dạng SQL / Làm đẹp SQL",
        jsonld_description="Công cụ trực tuyến miễn phí giúp câu lệnh SQL dễ đọc hơn bằng cách thụt lề và viết hoa từ khóa, hỗ trợ nhiều phương ngữ SQL.",
        h1="Công cụ định dạng SQL",
        lead="Dán câu lệnh SQL vào bên trái, bạn sẽ thấy kết quả dễ đọc với thụt lề rõ ràng ở bên phải. Chọn phương ngữ SQL khớp với cơ sở dữ liệu của bạn để có kết quả chính xác hơn. Dữ liệu không bao giờ được gửi lên máy chủ.",
        btn_format="Định dạng", btn_sample="Tải ví dụ", btn_clear="Xóa",
        indent_label="Kích thước thụt lề", indent2="Thụt lề 2 khoảng trắng", indent4="Thụt lề 4 khoảng trắng", indenttab="Thụt lề Tab",
        btn_copy="Sao chép", btn_copy_minify="Sao chép kết quả rút gọn", btn_download="Tải kết quả xuống",
        tabs_aria="Chuyển đổi giữa nhập và kết quả", tab_input="Nhập", tab_output="Kết quả",
        status_idle="Hãy dán câu lệnh SQL",
        input_search_mode_label="Chế độ tìm kiếm", opt_contains="Chứa", opt_exact_line="Khớp chính xác (toàn dòng)", opt_regex="Regex",
        input_search_placeholder="Tìm trong văn bản nhập…", prev_title="Kết quả trước", next_title="Kết quả tiếp theo", clear_title="Xóa tìm kiếm",
        input_placeholder="Dán câu lệnh SQL của bạn vào đây, ví dụ: SELECT * FROM users WHERE id = 1",
        output_label="Kết quả", expand_all="▾ Mở rộng tất cả", collapse_all="▸ Thu gọn tất cả",
        opt_exact="Khớp chính xác", output_search_placeholder="Tìm trong văn bản kết quả…",
        dialect_label="Phương ngữ SQL",
        dialect_standard="SQL chuẩn", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint='Mẹo. Công cụ này chỉ "định dạng (làm đẹp)" SQL; nó không kiểm tra liệu câu lệnh có đúng về mặt ngữ nghĩa hoặc có thể thực thi thành công trên cơ sở dữ liệu thực tế hay không. '
             "Chọn phương ngữ gần nhất với cơ sở dữ liệu của bạn sẽ cho kết quả định dạng chính xác hơn. "
             "Nếu câu lệnh hoàn toàn không thể phân tích được (ví dụ dấu ngoặc hoặc dấu ngoặc kép không khớp), vị trí lỗi gần đúng sẽ được hiển thị. "
             "Các từ khóa sẽ tự động chuyển thành chữ hoa theo quy ước phổ biến của SQL. Công cụ này đóng gói cục bộ thư viện mã nguồn mở "
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> '
             "(giấy phép MIT), nên việc định dạng vẫn diễn ra hoàn toàn trong trình duyệt của bạn.",
        usage_h2="Cách sử dụng công cụ này",
        usage_items=[
            "Dán câu lệnh SQL vào khung nhập bên trái.",
            'Chọn "Phương ngữ SQL" khớp với cơ sở dữ liệu của bạn (MySQL, PostgreSQL, SQL Server, v.v.) để có kết quả định dạng chính xác hơn.',
            'Nhấp "Định dạng" (cũng tự động định dạng khi bạn gõ) để xem kết quả đã làm đẹp ở bên phải.',
            "Nếu câu lệnh không thể phân tích được, bạn sẽ nhận được dòng/cột gần đúng của lỗi.",
            'Dùng menu kích thước thụt lề để điều chỉnh thụt lề của kết quả, sau đó lấy kết quả bằng "Sao chép" hoặc "Tải kết quả xuống".',
            "Mọi xử lý diễn ra trong trình duyệt của bạn — SQL bạn nhập không bao giờ được gửi lên máy chủ.",
        ],
        tips_h2="Mẹo liên quan",
        tips_items=[
            "Công cụ này chỉ định dạng/làm đẹp SQL; nó không kiểm tra liệu câu lệnh có khớp với cấu trúc cơ sở dữ liệu thực tế của bạn hay có thực thi thành công hay không.",
            "Từ khóa và cú pháp khác nhau giữa các phương ngữ (ví dụ LIMIT so với TOP, dấu backtick so với dấu ngoặc kép); hãy chọn phương ngữ khớp với cơ sở dữ liệu của bạn để có kết quả tốt nhất.",
            "Các từ khóa như SELECT, FROM, WHERE sẽ tự động chuyển thành chữ hoa theo quy ước phổ biến giúp tăng khả năng đọc.",
            "Nếu bạn cũng cần xử lý JSON hoặc XML, hãy thử Công cụ định dạng JSON, Công cụ định dạng XML hoặc Chuyển đổi JSON ↔ XML trong các liên kết liên quan bên dưới.",
        ],
    ),
    "pt": dict(
        title="Formatador SQL / Ferramenta de Embelezamento - Ferramenta Gratuita Online | Formix",
        description="Formate e indente consultas SQL gratuitamente online. Compatível com MySQL, PostgreSQL, SQL Server, Oracle PL/SQL, BigQuery, Snowflake e mais. Todo o processamento ocorre no seu navegador, nunca é enviado a um servidor.",
        keywords="formatador sql, embelezar sql, formatador sql online, formatar consultas sql, formatador mysql, formatador postgresql, ferramenta sql gratuita",
        og_title="Formatador SQL / Ferramenta de Embelezamento | Formix",
        og_description="Um formatador SQL online gratuito compatível com vários dialetos SQL; todo o processamento ocorre no navegador.",
        jsonld_name="Formatador SQL / Ferramenta de Embelezamento",
        jsonld_description="Ferramenta online gratuita que torna as consultas SQL mais legíveis por meio de recuo e formatação de palavras-chave, compatível com vários dialetos SQL.",
        h1="Formatador SQL",
        lead="Cole uma consulta SQL à esquerda e você verá um resultado legível com recuo claro à direita. Escolha o dialeto SQL que corresponde ao seu banco de dados para resultados mais precisos. Os dados nunca são enviados a um servidor.",
        btn_format="Formatar", btn_sample="Carregar exemplo", btn_clear="Limpar",
        indent_label="Tamanho do recuo", indent2="Recuo de 2 espaços", indent4="Recuo de 4 espaços", indenttab="Recuo com Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar resultado minificado", btn_download="Baixar resultado",
        tabs_aria="Alternar entre entrada e resultado", tab_input="Entrada", tab_output="Resultado",
        status_idle="Cole uma consulta SQL",
        input_search_mode_label="Modo de busca", opt_contains="Contém", opt_exact_line="Correspondência exata (linha)", opt_regex="Regex",
        input_search_placeholder="Buscar no texto de entrada…", prev_title="Correspondência anterior", next_title="Próxima correspondência", clear_title="Limpar busca",
        input_placeholder="Cole sua consulta SQL aqui, por exemplo: SELECT * FROM users WHERE id = 1",
        output_label="Resultado", expand_all="▾ Expandir tudo", collapse_all="▸ Recolher tudo",
        opt_exact="Correspondência exata", output_search_placeholder="Buscar no texto do resultado…",
        dialect_label="Dialeto SQL",
        dialect_standard="SQL padrão", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint='Dica. Esta ferramenta apenas "formata (embeleza)" o SQL; ela não valida se a consulta é semanticamente correta ou executável em um banco de dados real. '
             "Escolher o dialeto mais próximo do seu banco de dados resulta em uma formatação mais precisa. "
             "Se a consulta não puder ser analisada de forma alguma (por exemplo, parênteses ou aspas não correspondentes), uma posição de erro aproximada será exibida. "
             "As palavras-chave são convertidas para maiúsculas por padrão, seguindo uma convenção comum de estilo SQL. Esta ferramenta empacota localmente a biblioteca de código aberto "
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> '
             "(licença MIT), então a formatação continua ocorrendo inteiramente no seu navegador.",
        usage_h2="Como usar esta ferramenta",
        usage_items=[
            "Cole uma consulta SQL na caixa de entrada à esquerda.",
            'Escolha o "Dialeto SQL" que corresponde ao seu banco de dados (MySQL, PostgreSQL, SQL Server, etc.) para resultados de formatação mais precisos.',
            'Clique em "Formatar" (também formata automaticamente enquanto você digita) para ver o resultado embelezado à direita.',
            "Se a consulta não puder ser analisada, você receberá uma linha/coluna aproximada do erro.",
            'Use o menu de tamanho de recuo para ajustar o recuo do resultado, depois obtenha-o com "Copiar" ou "Baixar resultado".',
            "Todo o processamento ocorre no seu navegador — o SQL que você insere nunca é enviado a um servidor.",
        ],
        tips_h2="Dicas relacionadas",
        tips_items=[
            "Esta ferramenta apenas formata/embeleza o SQL; ela não verifica se a consulta corresponde ao esquema real do seu banco de dados ou se será executada com sucesso.",
            "Palavras-chave e sintaxe variam entre dialetos (por exemplo, LIMIT vs. TOP, aspas invertidas vs. aspas duplas); escolha o dialeto que corresponde ao seu banco de dados para melhores resultados.",
            "Palavras-chave como SELECT, FROM e WHERE são automaticamente convertidas para maiúsculas seguindo uma convenção comum que melhora a legibilidade.",
            "Se você também precisar trabalhar com JSON ou XML, experimente o Formatador JSON, o Formatador XML ou o Conversor JSON ↔ XML nos links relacionados abaixo.",
        ],
    ),
    "id": dict(
        title="Pemformat SQL / Alat Perapi - Alat Online Gratis | Formix",
        description="Format dan indentasi kueri SQL gratis secara online. Mendukung MySQL, PostgreSQL, SQL Server, Oracle PL/SQL, BigQuery, Snowflake, dan lainnya. Semua pemrosesan terjadi di browser Anda, tidak pernah dikirim ke server.",
        keywords="pemformat sql, perapi sql, pemformat sql online, format kueri sql, pemformat mysql, pemformat postgresql, alat sql gratis",
        og_title="Pemformat SQL / Alat Perapi | Formix",
        og_description="Pemformat SQL online gratis yang mendukung berbagai dialek SQL; semua pemrosesan terjadi di browser.",
        jsonld_name="Pemformat SQL / Alat Perapi",
        jsonld_description="Alat online gratis yang membuat kueri SQL lebih mudah dibaca melalui indentasi dan pemformatan kata kunci, mendukung berbagai dialek SQL.",
        h1="Pemformat SQL",
        lead="Tempel kueri SQL di sebelah kiri, Anda akan melihat hasil yang mudah dibaca dengan indentasi yang jelas di sebelah kanan. Pilih dialek SQL yang sesuai dengan basis data Anda untuk hasil yang lebih akurat. Data tidak pernah dikirim ke server.",
        btn_format="Format", btn_sample="Muat contoh", btn_clear="Hapus",
        indent_label="Ukuran indentasi", indent2="Indentasi 2 spasi", indent4="Indentasi 4 spasi", indenttab="Indentasi Tab",
        btn_copy="Salin", btn_copy_minify="Salin hasil yang diminifikasi", btn_download="Unduh hasil",
        tabs_aria="Beralih antara input dan hasil", tab_input="Input", tab_output="Hasil",
        status_idle="Tempel kueri SQL",
        input_search_mode_label="Mode pencarian", opt_contains="Berisi", opt_exact_line="Kecocokan tepat (baris)", opt_regex="Regex",
        input_search_placeholder="Cari di teks input…", prev_title="Hasil sebelumnya", next_title="Hasil berikutnya", clear_title="Hapus pencarian",
        input_placeholder="Tempel kueri SQL Anda di sini, misalnya: SELECT * FROM users WHERE id = 1",
        output_label="Hasil", expand_all="▾ Buka semua", collapse_all="▸ Lipat semua",
        opt_exact="Kecocokan tepat", output_search_placeholder="Cari di teks hasil…",
        dialect_label="Dialek SQL",
        dialect_standard="SQL standar", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint='Tips. Alat ini hanya "memformat (merapikan)" SQL; alat ini tidak memvalidasi apakah kueri secara semantik benar atau dapat dieksekusi di basis data sebenarnya. '
             "Memilih dialek yang paling sesuai dengan basis data Anda akan menghasilkan pemformatan yang lebih akurat. "
             "Jika kueri sama sekali tidak dapat diparsing (misalnya tanda kurung atau tanda kutip yang tidak cocok), posisi kesalahan perkiraan akan ditampilkan. "
             "Kata kunci secara default dikonversi menjadi huruf besar, mengikuti konvensi gaya SQL yang umum. Alat ini membundel secara lokal pustaka sumber terbuka "
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> '
             "(Lisensi MIT), sehingga pemformatan tetap berlangsung sepenuhnya di browser Anda.",
        usage_h2="Cara menggunakan alat ini",
        usage_items=[
            "Tempel kueri SQL ke kotak input di sebelah kiri.",
            'Pilih "Dialek SQL" yang sesuai dengan basis data Anda (MySQL, PostgreSQL, SQL Server, dll.) untuk hasil pemformatan yang lebih akurat.',
            'Klik "Format" (juga memformat secara otomatis saat Anda mengetik) untuk melihat hasil yang telah dirapikan di sebelah kanan.',
            "Jika kueri tidak dapat diparsing, Anda akan mendapatkan perkiraan baris/kolom kesalahan.",
            'Gunakan menu ukuran indentasi untuk menyesuaikan indentasi hasil, lalu dapatkan dengan "Salin" atau "Unduh hasil".',
            "Semua pemrosesan terjadi di browser Anda — SQL yang Anda masukkan tidak pernah dikirim ke server.",
        ],
        tips_h2="Tips terkait",
        tips_items=[
            "Alat ini hanya memformat/merapikan SQL; alat ini tidak memeriksa apakah kueri sesuai dengan skema basis data Anda yang sebenarnya atau akan berhasil dieksekusi.",
            "Kata kunci dan sintaks bervariasi antar dialek (misalnya LIMIT vs TOP, backtick vs tanda kutip ganda); pilih dialek yang sesuai dengan basis data Anda untuk hasil terbaik.",
            "Kata kunci seperti SELECT, FROM, WHERE secara otomatis dikonversi menjadi huruf besar mengikuti konvensi umum yang meningkatkan keterbacaan.",
            "Jika Anda juga perlu bekerja dengan JSON atau XML, coba Pemformat JSON, Pemformat XML, atau Konverter JSON ↔ XML di tautan terkait di bawah.",
        ],
    ),
    "de": dict(
        title="SQL-Formatierer / Beautifier - Kostenloses Online-Tool | Formix",
        description="Formatieren und einrücken Sie SQL-Abfragen kostenlos online. Unterstützt MySQL, PostgreSQL, SQL Server, Oracle PL/SQL, BigQuery, Snowflake und mehr. Die gesamte Verarbeitung erfolgt in Ihrem Browser, nie an einen Server gesendet.",
        keywords="sql formatierer, sql beautifier, sql formatierer online, sql abfragen formatieren, mysql formatierer, postgresql formatierer, kostenloses sql tool",
        og_title="SQL-Formatierer / Beautifier | Formix",
        og_description="Ein kostenloser Online-SQL-Formatierer, der mehrere SQL-Dialekte unterstützt; die gesamte Verarbeitung erfolgt im Browser.",
        jsonld_name="SQL-Formatierer / Beautifier",
        jsonld_description="Kostenloses Online-Tool, das SQL-Abfragen durch Einrückung und Schlüsselwort-Formatierung lesbarer macht, unterstützt mehrere SQL-Dialekte.",
        h1="SQL-Formatierer",
        lead="Fügen Sie links eine SQL-Abfrage ein, und rechts sehen Sie ein lesbares Ergebnis mit klarer Einrückung. Wählen Sie den SQL-Dialekt, der zu Ihrer Datenbank passt, für genauere Ergebnisse. Daten werden nie an einen Server gesendet.",
        btn_format="Formatieren", btn_sample="Beispiel laden", btn_clear="Leeren",
        indent_label="Einrückungsgröße", indent2="2-Leerzeichen-Einrückung", indent4="4-Leerzeichen-Einrückung", indenttab="Tab-Einrückung",
        btn_copy="Kopieren", btn_copy_minify="Minifiziertes Ergebnis kopieren", btn_download="Ergebnis herunterladen",
        tabs_aria="Zwischen Eingabe und Ergebnis wechseln", tab_input="Eingabe", tab_output="Ergebnis",
        status_idle="SQL-Abfrage einfügen",
        input_search_mode_label="Suchmodus", opt_contains="Enthält", opt_exact_line="Exakte Übereinstimmung (Zeile)", opt_regex="Regex",
        input_search_placeholder="Im Eingabetext suchen…", prev_title="Vorherige Übereinstimmung", next_title="Nächste Übereinstimmung", clear_title="Suche leeren",
        input_placeholder="Fügen Sie hier Ihre SQL-Abfrage ein, z. B.: SELECT * FROM users WHERE id = 1",
        output_label="Ergebnis", expand_all="▾ Alle ausklappen", collapse_all="▸ Alle einklappen",
        opt_exact="Exakte Übereinstimmung", output_search_placeholder="Im Ergebnistext suchen…",
        dialect_label="SQL-Dialekt",
        dialect_standard="Standard-SQL", dialect_mysql="MySQL / MariaDB", dialect_postgresql="PostgreSQL",
        dialect_tsql="SQL Server (T-SQL)", dialect_plsql="Oracle PL/SQL", dialect_bigquery="Google BigQuery",
        dialect_snowflake="Snowflake", dialect_sqlite="SQLite",
        hint='Tipp. Dieses Tool „formatiert (verschönert)" nur SQL; es validiert nicht, ob die Abfrage semantisch korrekt oder in einer echten Datenbank ausführbar ist. '
             "Die Wahl des Dialekts, der Ihrer Datenbank am nächsten kommt, führt zu genaueren Formatierungsergebnissen. "
             "Wenn die Abfrage überhaupt nicht analysiert werden kann (z. B. nicht übereinstimmende Klammern oder Anführungszeichen), wird eine ungefähre Fehlerposition angezeigt. "
             "Schlüsselwörter werden standardmäßig in Großbuchstaben umgewandelt, gemäß einer gängigen SQL-Stilkonvention. Dieses Tool bündelt lokal die Open-Source-Bibliothek "
             '<a href="https://github.com/sql-formatter-org/sql-formatter" rel="noopener noreferrer" target="_blank">sql-formatter</a> '
             "(MIT-Lizenz), sodass die Formatierung weiterhin vollständig in Ihrem Browser erfolgt.",
        usage_h2="So verwenden Sie dieses Tool",
        usage_items=[
            "Fügen Sie eine SQL-Abfrage in das Eingabefeld links ein.",
            'Wählen Sie den „SQL-Dialekt", der zu Ihrer Datenbank passt (MySQL, PostgreSQL, SQL Server usw.), für genauere Formatierungsergebnisse.',
            'Klicken Sie auf „Formatieren" (formatiert auch automatisch beim Tippen), um das verschönerte Ergebnis rechts zu sehen.',
            "Wenn die Abfrage nicht analysiert werden kann, erhalten Sie eine ungefähre Zeile/Spalte des Fehlers.",
            'Verwenden Sie das Einrückungsgrößen-Menü, um die Einrückung des Ergebnisses anzupassen, und holen Sie es dann über „Kopieren" oder „Ergebnis herunterladen".',
            "Die gesamte Verarbeitung erfolgt in Ihrem Browser — das von Ihnen eingegebene SQL wird nie an einen Server gesendet.",
        ],
        tips_h2="Verwandte Tipps",
        tips_items=[
            "Dieses Tool formatiert/verschönert SQL nur; es prüft nicht, ob die Abfrage zu Ihrem tatsächlichen Datenbankschema passt oder erfolgreich ausgeführt wird.",
            "Schlüsselwörter und Syntax unterscheiden sich zwischen Dialekten (z. B. LIMIT vs. TOP, Backticks vs. doppelte Anführungszeichen); wählen Sie den Dialekt, der zu Ihrer Datenbank passt, für beste Ergebnisse.",
            "Schlüsselwörter wie SELECT, FROM und WHERE werden automatisch in Großbuchstaben umgewandelt, gemäß einer gängigen Konvention, die die Lesbarkeit verbessert.",
            "Wenn Sie auch mit JSON oder XML arbeiten müssen, probieren Sie den JSON-Formatierer, den XML-Formatierer oder den JSON ↔ XML Konverter in den verwandten Links unten.",
        ],
    ),
}

CONTENT["tool_code"] = {
    "en": dict(
        title="Code Viewer / Syntax Highlighter - Free Online Tool | Formix",
        description="Paste source code and view it with syntax highlighting online, free. Supports Java, C#, C, C++, Python, JavaScript, TypeScript, Go, Rust, Kotlin, Swift, PHP, Ruby, HTML/XML, CSS, Bash, JSON, YAML, Markdown, and SQL. Runs entirely in your browser.",
        keywords="code viewer online, syntax highlighter, code syntax highlighting, java syntax highlighter, c# syntax highlighter, python syntax highlighter online, free code highlighter",
        og_title="Code Viewer / Syntax Highlighter | Formix",
        og_description="A free online code viewer with syntax highlighting for 20+ languages. Runs entirely in your browser.",
        jsonld_name="Code Viewer / Syntax Highlighter",
        jsonld_description="A free online tool that displays pasted source code with syntax highlighting, supporting over 20 programming and markup languages.",
        h1="Code Viewer",
        lead="Paste your source code on the left, pick its language, and get a syntax-highlighted, easy-to-read view on the right. Nothing is sent to a server.",
        btn_format="Highlight", btn_sample="Load sample", btn_clear="Clear",
        indent_label="Indent size", indent2="2-space indent", indent4="4-space indent", indenttab="Tab indent",
        btn_copy="Copy", btn_copy_minify="Copy", btn_download="Download result",
        tabs_aria="Switch between input and output", tab_input="Input", tab_output="Output",
        status_idle="Paste some source code",
        input_search_mode_label="Search mode", opt_contains="Contains", opt_exact_line="Exact (line)", opt_regex="Regex",
        input_search_placeholder="Search the input text…", prev_title="Previous match", next_title="Next match", clear_title="Clear search",
        input_placeholder="Paste source code here",
        output_label="Output", expand_all="▾ Expand all", collapse_all="▸ Collapse all",
        opt_exact="Exact", output_search_placeholder="Search the output text…",
        language_label="Language",
        language_plain="Plain text (no highlighting)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint="Tip. This tool only highlights syntax for readability — it does not check whether your code compiles or runs correctly. "
             "Pick the language that matches your code for the most accurate coloring; if you're not sure, \"Plain text\" simply shows the code as-is. "
             "This tool bundles the open-source "
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> '
             "library (MIT License) locally, so highlighting still happens entirely in your browser.",
        usage_h2="How to use this tool",
        usage_items=[
            "Paste your source code into the input box on the left.",
            'Pick the "Language" that matches your code (Java, C#, Python, Go, and more) for accurate highlighting.',
            'Click "Highlight" (or just wait — it also updates automatically as you type) to see the colored result on the right.',
            '"Copy" or "Download result" to grab the highlighted output, or the original text.',
            "Everything happens in your browser — your code is never sent to a server.",
        ],
        tips_h2="Related tips",
        tips_items=[
            "This tool only adds syntax coloring for readability — it doesn't compile, run, lint, or validate your code in any way.",
            "If a language isn't listed or the highlighting looks off, try the closest related language, or use \"Plain text\".",
            "Need to also work with JSON, XML, or SQL specifically? Try the dedicated JSON Formatter, XML Formatter, JSON ↔ XML Converter, or SQL Formatter tools linked below.",
        ],
    ),
    "ko": dict(
        title="코드 뷰어 / 문법 강조 - 무료 온라인 도구 | Formix",
        description="소스 코드를 붙여넣으면 무료로 온라인에서 문법 강조(syntax highlighting)가 적용된 화면으로 볼 수 있습니다. Java, C#, C, C++, Python, JavaScript, TypeScript, Go, Rust, Kotlin, Swift, PHP, Ruby, HTML/XML, CSS, Bash, JSON, YAML, Markdown, SQL을 지원합니다. 모든 처리는 브라우저 안에서만 이뤄집니다.",
        keywords="코드 뷰어, 문법 강조, syntax highlighter, 온라인 코드 하이라이터, java 문법 강조, c# 문법 강조, python 코드 색상, 무료 코드 뷰어",
        og_title="코드 뷰어 / 문법 강조 | Formix",
        og_description="20개 이상 언어를 지원하는 무료 온라인 코드 뷰어. 모든 처리는 브라우저 안에서 이뤄집니다.",
        jsonld_name="코드 뷰어 / 문법 강조",
        jsonld_description="붙여넣은 소스 코드에 문법 강조를 적용해 보여주는 무료 온라인 도구. 20개 이상의 프로그래밍/마크업 언어를 지원합니다.",
        h1="코드 뷰어",
        lead="왼쪽에 소스 코드를 붙여넣고 언어를 선택하면 오른쪽에 문법 강조가 적용된 보기 좋은 결과가 표시됩니다. 데이터는 서버로 전송되지 않습니다.",
        btn_format="강조 적용", btn_sample="예시 불러오기", btn_clear="지우기",
        indent_label="들여쓰기 크기", indent2="들여쓰기 2칸", indent4="들여쓰기 4칸", indenttab="들여쓰기 Tab",
        btn_copy="복사", btn_copy_minify="복사", btn_download="결과 다운로드",
        tabs_aria="입력/결과 전환", tab_input="입력", tab_output="결과",
        status_idle="소스 코드를 붙여넣어주세요",
        input_search_mode_label="검색 방식", opt_contains="포함", opt_exact_line="일치(줄)", opt_regex="정규식",
        input_search_placeholder="입력한 텍스트에서 검색…", prev_title="이전 일치 항목", next_title="다음 일치 항목", clear_title="검색어 지우기",
        input_placeholder="여기에 소스 코드를 붙여넣으세요",
        output_label="결과", expand_all="▾ 모두 펼치기", collapse_all="▸ 모두 접기",
        opt_exact="일치", output_search_placeholder="결과 텍스트에서 검색…",
        language_label="언어",
        language_plain="일반 텍스트(강조 없음)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint='Tip. 이 도구는 가독성을 위해 문법 강조만 적용할 뿐, 코드가 실제로 컴파일되거나 정상 동작하는지는 검사하지 않습니다. '
             '코드에 맞는 언어를 선택해야 가장 정확한 색상이 적용됩니다. 잘 모르겠다면 "일반 텍스트"를 선택하면 원본 그대로 표시됩니다. '
             "이 도구는 오픈소스 "
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> '
             "라이브러리(MIT 라이선스)를 로컬에 내장하여 사용하므로, 처리는 여전히 브라우저 안에서만 이뤄집니다.",
        usage_h2="이 도구는 이렇게 사용하세요",
        usage_items=[
            "왼쪽 입력창에 소스 코드를 붙여넣으세요.",
            '코드에 맞는 "언어"(Java, C#, Python, Go 등)를 선택하면 정확하게 강조됩니다.',
            '"강조 적용" 버튼을 클릭하거나(입력하는 동안 자동으로도 적용됩니다) 오른쪽에서 결과를 확인하세요.',
            '"복사" 또는 "결과 다운로드"로 강조된 결과나 원본 텍스트를 가져갈 수 있습니다.',
            "모든 처리는 브라우저 안에서만 이뤄지며, 입력한 코드는 서버로 전송되지 않습니다.",
        ],
        tips_h2="관련 팁",
        tips_items=[
            "이 도구는 가독성을 위한 문법 색상만 입힐 뿐, 코드를 컴파일하거나 실행하거나 검사하지 않습니다.",
            "목록에 없는 언어이거나 강조가 어색하다면 가장 비슷한 언어를 선택하거나 \"일반 텍스트\"를 사용해보세요.",
            "JSON, XML, SQL을 다뤄야 한다면 아래 관련 링크의 JSON 포매터, XML 포매터, JSON ↔ XML 변환기, SQL 포매터를 사용해보세요.",
        ],
    ),
    "ja": dict(
        title="コードビューア / シンタックスハイライト - 無料オンラインツール | Formix",
        description="ソースコードを貼り付けるだけで無料でシンタックスハイライトが適用された表示を確認できます。Java、C#、C、C++、Python、JavaScript、TypeScript、Go、Rust、Kotlin、Swift、PHP、Ruby、HTML/XML、CSS、Bash、JSON、YAML、Markdown、SQLに対応。すべての処理はブラウザ内で行われます。",
        keywords="コードビューア, シンタックスハイライト, オンライン コードハイライター, java 色分け, c# シンタックスハイライト, python コード表示, 無料 コードビューア",
        og_title="コードビューア / シンタックスハイライト | Formix",
        og_description="20以上の言語に対応した無料オンラインコードビューア。すべての処理はブラウザ内で行われます。",
        jsonld_name="コードビューア / シンタックスハイライト",
        jsonld_description="貼り付けたソースコードにシンタックスハイライトを適用して表示する無料オンラインツール。20以上のプログラミング/マークアップ言語に対応しています。",
        h1="コードビューア",
        lead="左側にソースコードを貼り付けて言語を選択すると、右側にシンタックスハイライト付きの見やすい結果が表示されます。データはサーバーに送信されません。",
        btn_format="ハイライト適用", btn_sample="例を読み込む", btn_clear="クリア",
        indent_label="インデントサイズ", indent2="インデント2文字", indent4="インデント4文字", indenttab="インデントTab",
        btn_copy="コピー", btn_copy_minify="コピー", btn_download="結果をダウンロード",
        tabs_aria="入力/結果切り替え", tab_input="入力", tab_output="結果",
        status_idle="ソースコードを貼り付けてください",
        input_search_mode_label="検索モード", opt_contains="含む", opt_exact_line="完全一致(行)", opt_regex="正規表現",
        input_search_placeholder="入力テキストを検索…", prev_title="前の一致", next_title="次の一致", clear_title="検索をクリア",
        input_placeholder="ここにソースコードを貼り付けてください",
        output_label="結果", expand_all="▾ すべて展開", collapse_all="▸ すべて折りたたむ",
        opt_exact="完全一致", output_search_placeholder="結果テキストを検索…",
        language_label="言語",
        language_plain="プレーンテキスト(ハイライトなし)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint="Tip. このツールは可読性のためにシンタックスハイライトを適用するだけで、コードが実際にコンパイル・実行できるかどうかは検証しません。"
             "コードに合った言語を選択すると、より正確な色付けになります。わからない場合は「プレーンテキスト」を選ぶと原文のまま表示されます。"
             "このツールはオープンソースの"
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a>'
             "ライブラリ(MITライセンス)をローカルにバンドルしているため、処理は引き続きブラウザ内で完結します。",
        usage_h2="このツールの使い方",
        usage_items=[
            "左側の入力欄にソースコードを貼り付けます。",
            "コードに合った「言語」(Java、C#、Python、Goなど)を選択すると、正確にハイライトされます。",
            "「ハイライト適用」ボタンをクリックするか(入力中も自動で適用されます)、右側で結果を確認してください。",
            "「コピー」または「結果をダウンロード」でハイライトされた結果や元のテキストを取得できます。",
            "すべての処理はブラウザ内で行われ、入力したコードがサーバーに送信されることはありません。",
        ],
        tips_h2="関連のヒント",
        tips_items=[
            "このツールは可読性のための色付けのみを行い、コードのコンパイル・実行・検証は一切行いません。",
            "一覧にない言語や、ハイライトが不自然な場合は近い言語を選ぶか、「プレーンテキスト」をお使いください。",
            "JSON、XML、SQLを扱う場合は、下記の関連リンクにあるJSONフォーマッター、XMLフォーマッター、JSON ↔ XML 変換ツール、SQLフォーマッターもご利用ください。",
        ],
    ),
    "zh": dict(
        title="代码查看器 / 语法高亮 - 免费在线工具 | Formix",
        description="粘贴源代码即可免费在线获得语法高亮展示。支持 Java、C#、C、C++、Python、JavaScript、TypeScript、Go、Rust、Kotlin、Swift、PHP、Ruby、HTML/XML、CSS、Bash、JSON、YAML、Markdown、SQL。所有处理均在浏览器中完成。",
        keywords="代码查看器, 语法高亮, 在线代码高亮工具, java 语法高亮, c# 语法高亮, python 代码高亮, 免费代码查看器",
        og_title="代码查看器 / 语法高亮 | Formix",
        og_description="支持 20 多种语言的免费在线代码查看器，所有处理均在浏览器中完成。",
        jsonld_name="代码查看器 / 语法高亮",
        jsonld_description="为粘贴的源代码添加语法高亮展示的免费在线工具，支持 20 多种编程/标记语言。",
        h1="代码查看器",
        lead="在左侧粘贴源代码并选择语言，右侧会显示带语法高亮的易读结果。数据不会发送到服务器。",
        btn_format="应用高亮", btn_sample="加载示例", btn_clear="清空",
        indent_label="缩进大小", indent2="2 格缩进", indent4="4 格缩进", indenttab="Tab 缩进",
        btn_copy="复制", btn_copy_minify="复制", btn_download="下载结果",
        tabs_aria="切换输入/结果", tab_input="输入", tab_output="结果",
        status_idle="请粘贴源代码",
        input_search_mode_label="搜索模式", opt_contains="包含", opt_exact_line="精确匹配(整行)", opt_regex="正则表达式",
        input_search_placeholder="在输入文本中搜索…", prev_title="上一个匹配项", next_title="下一个匹配项", clear_title="清除搜索",
        input_placeholder="在此粘贴源代码",
        output_label="结果", expand_all="▾ 全部展开", collapse_all="▸ 全部折叠",
        opt_exact="精确匹配", output_search_placeholder="在结果文本中搜索…",
        language_label="语言",
        language_plain="纯文本(不高亮)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint='提示。此工具仅为提升可读性而添加语法高亮，并不会检查代码是否能够正确编译或运行。'
             '选择与代码匹配的语言可获得更准确的着色效果；如果不确定，选择"纯文本"即可按原样显示代码。'
             "此工具在本地打包(vendor)了开源的 "
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> '
             "库(MIT 许可)，因此高亮处理仍完全在您的浏览器中进行。",
        usage_h2="使用方法",
        usage_items=[
            "将源代码粘贴到左侧的输入框中。",
            '选择与代码匹配的"语言"(Java、C#、Python、Go 等)以获得准确的高亮效果。',
            '点击"应用高亮"按钮(输入时也会自动应用)，即可在右侧查看高亮后的结果。',
            '通过"复制"或"下载结果"获取高亮结果或原始文本。',
            "所有处理均在浏览器内完成，您输入的代码不会发送到服务器。",
        ],
        tips_h2="相关提示",
        tips_items=[
            "此工具仅添加用于提升可读性的语法着色，不会编译、运行或校验您的代码。",
            "如果列表中没有对应语言，或高亮效果不理想，可尝试选择相近的语言，或使用「纯文本」。",
            "如果还需要处理 JSON、XML 或 SQL，请尝试下方相关链接中的 JSON 格式化工具、XML 格式化工具、JSON ↔ XML 转换工具或 SQL 格式化工具。",
        ],
    ),
    "es": dict(
        title="Visor de Código / Resaltado de Sintaxis - Herramienta Gratuita en Línea | Formix",
        description="Pega código fuente y obtén resaltado de sintaxis gratis en línea. Compatible con Java, C#, C, C++, Python, JavaScript, TypeScript, Go, Rust, Kotlin, Swift, PHP, Ruby, HTML/XML, CSS, Bash, JSON, YAML, Markdown y SQL. Todo el procesamiento ocurre en el navegador.",
        keywords="visor de código, resaltado de sintaxis, herramienta de resaltado de código en línea, resaltado de sintaxis java, resaltado c#, resaltado de código python, visor de código gratis",
        og_title="Visor de Código / Resaltado de Sintaxis | Formix",
        og_description="Un visor de código en línea gratuito compatible con más de 20 lenguajes; todo el procesamiento ocurre en el navegador.",
        jsonld_name="Visor de Código / Resaltado de Sintaxis",
        jsonld_description="Herramienta en línea gratuita que agrega resaltado de sintaxis al código fuente pegado, compatible con más de 20 lenguajes de programación/marcado.",
        h1="Visor de código",
        lead="Pega código fuente a la izquierda y elige un lenguaje; a la derecha verás un resultado legible con resaltado de sintaxis. Los datos nunca se envían a un servidor.",
        btn_format="Aplicar resaltado", btn_sample="Cargar ejemplo", btn_clear="Limpiar",
        indent_label="Tamaño de sangría", indent2="Sangría de 2 espacios", indent4="Sangría de 4 espacios", indenttab="Sangría con Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar", btn_download="Descargar resultado",
        tabs_aria="Alternar entre entrada y resultado", tab_input="Entrada", tab_output="Resultado",
        status_idle="Pega el código fuente",
        input_search_mode_label="Modo de búsqueda", opt_contains="Contiene", opt_exact_line="Coincidencia exacta (línea)", opt_regex="Regex",
        input_search_placeholder="Buscar en el texto de entrada…", prev_title="Coincidencia anterior", next_title="Siguiente coincidencia", clear_title="Limpiar búsqueda",
        input_placeholder="Pega tu código fuente aquí",
        output_label="Resultado", expand_all="▾ Expandir todo", collapse_all="▸ Colapsar todo",
        opt_exact="Coincidencia exacta", output_search_placeholder="Buscar en el texto del resultado…",
        language_label="Lenguaje",
        language_plain="Texto plano (sin resaltado)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint='Consejo. Esta herramienta solo agrega resaltado de sintaxis para mejorar la legibilidad; no verifica si el código compila o se ejecuta correctamente. '
             'Elegir el lenguaje que coincide con tu código da un resultado de coloreado más preciso; si no estás seguro, elige "Texto plano" para mostrar el código tal cual. '
             "Esta herramienta incluye localmente la biblioteca de código abierto "
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> '
             "(licencia MIT), por lo que el resaltado sigue ocurriendo enteramente en tu navegador.",
        usage_h2="Cómo usar esta herramienta",
        usage_items=[
            "Pega el código fuente en el cuadro de entrada de la izquierda.",
            'Elige el "Lenguaje" que coincide con tu código (Java, C#, Python, Go, etc.) para un resaltado preciso.',
            'Haz clic en "Aplicar resaltado" (también se aplica automáticamente mientras escribes) para ver el resultado resaltado a la derecha.',
            'Obtén el resultado resaltado o el texto original con "Copiar" o "Descargar resultado".',
            "Todo el procesamiento ocurre en tu navegador — el código que ingresas nunca se envía a un servidor.",
        ],
        tips_h2="Consejos relacionados",
        tips_items=[
            "Esta herramienta solo agrega coloreado para mejorar la legibilidad; no compila, ejecuta ni valida tu código.",
            'Si tu lenguaje no está en la lista, o el resaltado no se ve bien, intenta elegir un lenguaje similar o usa "Texto plano".',
            "Si también necesitas trabajar con JSON, XML o SQL, prueba el Formateador JSON, el Formateador XML, el Convertidor JSON ↔ XML o el Formateador SQL en los enlaces relacionados debajo.",
        ],
    ),
    "vi": dict(
        title="Xem Mã Nguồn / Tô Màu Cú Pháp - Công cụ Trực tuyến Miễn phí | Formix",
        description="Dán mã nguồn và nhận tô màu cú pháp miễn phí trực tuyến. Hỗ trợ Java, C#, C, C++, Python, JavaScript, TypeScript, Go, Rust, Kotlin, Swift, PHP, Ruby, HTML/XML, CSS, Bash, JSON, YAML, Markdown và SQL. Mọi xử lý diễn ra trong trình duyệt.",
        keywords="xem mã nguồn, tô màu cú pháp, công cụ tô màu mã trực tuyến, tô màu cú pháp java, tô màu c#, tô màu mã python, xem mã nguồn miễn phí",
        og_title="Xem Mã Nguồn / Tô Màu Cú Pháp | Formix",
        og_description="Công cụ xem mã nguồn trực tuyến miễn phí hỗ trợ hơn 20 ngôn ngữ; mọi xử lý diễn ra trong trình duyệt.",
        jsonld_name="Xem Mã Nguồn / Tô Màu Cú Pháp",
        jsonld_description="Công cụ trực tuyến miễn phí thêm tô màu cú pháp cho mã nguồn được dán, hỗ trợ hơn 20 ngôn ngữ lập trình/đánh dấu.",
        h1="Xem mã nguồn",
        lead="Dán mã nguồn vào bên trái và chọn một ngôn ngữ; bên phải sẽ hiển thị kết quả dễ đọc với tô màu cú pháp. Dữ liệu không bao giờ được gửi lên máy chủ.",
        btn_format="Áp dụng tô màu", btn_sample="Tải ví dụ", btn_clear="Xóa",
        indent_label="Kích thước thụt lề", indent2="Thụt lề 2 khoảng trắng", indent4="Thụt lề 4 khoảng trắng", indenttab="Thụt lề Tab",
        btn_copy="Sao chép", btn_copy_minify="Sao chép", btn_download="Tải kết quả xuống",
        tabs_aria="Chuyển đổi giữa nhập và kết quả", tab_input="Nhập", tab_output="Kết quả",
        status_idle="Hãy dán mã nguồn",
        input_search_mode_label="Chế độ tìm kiếm", opt_contains="Chứa", opt_exact_line="Khớp chính xác (toàn dòng)", opt_regex="Regex",
        input_search_placeholder="Tìm trong văn bản nhập…", prev_title="Kết quả trước", next_title="Kết quả tiếp theo", clear_title="Xóa tìm kiếm",
        input_placeholder="Dán mã nguồn của bạn vào đây",
        output_label="Kết quả", expand_all="▾ Mở rộng tất cả", collapse_all="▸ Thu gọn tất cả",
        opt_exact="Khớp chính xác", output_search_placeholder="Tìm trong văn bản kết quả…",
        language_label="Ngôn ngữ",
        language_plain="Văn bản thuần (không tô màu)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint='Mẹo. Công cụ này chỉ thêm tô màu cú pháp để tăng khả năng đọc; nó không kiểm tra liệu mã có thể biên dịch hoặc chạy đúng hay không. '
             'Chọn ngôn ngữ khớp với mã của bạn sẽ cho kết quả tô màu chính xác hơn; nếu không chắc, hãy chọn "Văn bản thuần" để hiển thị mã nguyên bản. '
             "Công cụ này đóng gói cục bộ thư viện mã nguồn mở "
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> '
             "(giấy phép MIT), nên việc tô màu vẫn diễn ra hoàn toàn trong trình duyệt của bạn.",
        usage_h2="Cách sử dụng công cụ này",
        usage_items=[
            "Dán mã nguồn vào khung nhập bên trái.",
            'Chọn "Ngôn ngữ" khớp với mã của bạn (Java, C#, Python, Go, v.v.) để có tô màu chính xác.',
            'Nhấp "Áp dụng tô màu" (cũng tự động áp dụng khi bạn gõ) để xem kết quả tô màu ở bên phải.',
            'Lấy kết quả đã tô màu hoặc văn bản gốc bằng "Sao chép" hoặc "Tải kết quả xuống".',
            "Mọi xử lý diễn ra trong trình duyệt của bạn — mã bạn nhập không bao giờ được gửi lên máy chủ.",
        ],
        tips_h2="Mẹo liên quan",
        tips_items=[
            "Công cụ này chỉ thêm màu để tăng khả năng đọc; nó không biên dịch, chạy hoặc kiểm tra mã của bạn.",
            'Nếu ngôn ngữ của bạn không có trong danh sách, hoặc tô màu không như mong đợi, hãy thử chọn ngôn ngữ tương tự hoặc dùng "Văn bản thuần".',
            "Nếu bạn cũng cần xử lý JSON, XML hoặc SQL, hãy thử Công cụ định dạng JSON, Công cụ định dạng XML, Chuyển đổi JSON ↔ XML hoặc Công cụ định dạng SQL trong các liên kết liên quan bên dưới.",
        ],
    ),
    "pt": dict(
        title="Visualizador de Código / Destaque de Sintaxe - Ferramenta Gratuita Online | Formix",
        description="Cole código-fonte e obtenha destaque de sintaxe gratuitamente online. Compatível com Java, C#, C, C++, Python, JavaScript, TypeScript, Go, Rust, Kotlin, Swift, PHP, Ruby, HTML/XML, CSS, Bash, JSON, YAML, Markdown e SQL. Todo o processamento ocorre no navegador.",
        keywords="visualizador de código, destaque de sintaxe, ferramenta de destaque de código online, destaque de sintaxe java, destaque c#, destaque de código python, visualizador de código gratuito",
        og_title="Visualizador de Código / Destaque de Sintaxe | Formix",
        og_description="Um visualizador de código online gratuito compatível com mais de 20 linguagens; todo o processamento ocorre no navegador.",
        jsonld_name="Visualizador de Código / Destaque de Sintaxe",
        jsonld_description="Ferramenta online gratuita que adiciona destaque de sintaxe ao código-fonte colado, compatível com mais de 20 linguagens de programação/marcação.",
        h1="Visualizador de código",
        lead="Cole o código-fonte à esquerda e escolha uma linguagem; à direita você verá um resultado legível com destaque de sintaxe. Os dados nunca são enviados a um servidor.",
        btn_format="Aplicar destaque", btn_sample="Carregar exemplo", btn_clear="Limpar",
        indent_label="Tamanho do recuo", indent2="Recuo de 2 espaços", indent4="Recuo de 4 espaços", indenttab="Recuo com Tab",
        btn_copy="Copiar", btn_copy_minify="Copiar", btn_download="Baixar resultado",
        tabs_aria="Alternar entre entrada e resultado", tab_input="Entrada", tab_output="Resultado",
        status_idle="Cole o código-fonte",
        input_search_mode_label="Modo de busca", opt_contains="Contém", opt_exact_line="Correspondência exata (linha)", opt_regex="Regex",
        input_search_placeholder="Buscar no texto de entrada…", prev_title="Correspondência anterior", next_title="Próxima correspondência", clear_title="Limpar busca",
        input_placeholder="Cole seu código-fonte aqui",
        output_label="Resultado", expand_all="▾ Expandir tudo", collapse_all="▸ Recolher tudo",
        opt_exact="Correspondência exata", output_search_placeholder="Buscar no texto do resultado…",
        language_label="Linguagem",
        language_plain="Texto simples (sem destaque)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint='Dica. Esta ferramenta apenas adiciona destaque de sintaxe para melhorar a legibilidade; ela não verifica se o código compila ou executa corretamente. '
             'Escolher a linguagem que corresponde ao seu código resulta em uma coloração mais precisa; se não tiver certeza, escolha "Texto simples" para exibir o código como está. '
             "Esta ferramenta empacota localmente a biblioteca de código aberto "
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> '
             "(licença MIT), então o destaque continua ocorrendo inteiramente no seu navegador.",
        usage_h2="Como usar esta ferramenta",
        usage_items=[
            "Cole o código-fonte na caixa de entrada à esquerda.",
            'Escolha a "Linguagem" que corresponde ao seu código (Java, C#, Python, Go, etc.) para um destaque preciso.',
            'Clique em "Aplicar destaque" (também aplica automaticamente enquanto você digita) para ver o resultado destacado à direita.',
            'Obtenha o resultado destacado ou o texto original com "Copiar" ou "Baixar resultado".',
            "Todo o processamento ocorre no seu navegador — o código que você insere nunca é enviado a um servidor.",
        ],
        tips_h2="Dicas relacionadas",
        tips_items=[
            "Esta ferramenta apenas adiciona coloração para melhorar a legibilidade; ela não compila, executa ou valida seu código.",
            'Se sua linguagem não estiver na lista, ou o destaque não ficar bom, tente escolher uma linguagem semelhante ou use "Texto simples".',
            "Se você também precisar trabalhar com JSON, XML ou SQL, experimente o Formatador JSON, o Formatador XML, o Conversor JSON ↔ XML ou o Formatador SQL nos links relacionados abaixo.",
        ],
    ),
    "id": dict(
        title="Penampil Kode / Penyorotan Sintaks - Alat Online Gratis | Formix",
        description="Tempel kode sumber dan dapatkan penyorotan sintaks gratis secara online. Mendukung Java, C#, C, C++, Python, JavaScript, TypeScript, Go, Rust, Kotlin, Swift, PHP, Ruby, HTML/XML, CSS, Bash, JSON, YAML, Markdown, dan SQL. Semua pemrosesan terjadi di browser.",
        keywords="penampil kode, penyorotan sintaks, alat penyorotan kode online, penyorotan sintaks java, penyorotan c#, penyorotan kode python, penampil kode gratis",
        og_title="Penampil Kode / Penyorotan Sintaks | Formix",
        og_description="Penampil kode online gratis yang mendukung lebih dari 20 bahasa; semua pemrosesan terjadi di browser.",
        jsonld_name="Penampil Kode / Penyorotan Sintaks",
        jsonld_description="Alat online gratis yang menambahkan penyorotan sintaks pada kode sumber yang ditempel, mendukung lebih dari 20 bahasa pemrograman/markup.",
        h1="Penampil Kode",
        lead="Tempel kode sumber di sebelah kiri dan pilih bahasa; di sebelah kanan Anda akan melihat hasil yang mudah dibaca dengan penyorotan sintaks. Data tidak pernah dikirim ke server.",
        btn_format="Terapkan penyorotan", btn_sample="Muat contoh", btn_clear="Hapus",
        indent_label="Ukuran indentasi", indent2="Indentasi 2 spasi", indent4="Indentasi 4 spasi", indenttab="Indentasi Tab",
        btn_copy="Salin", btn_copy_minify="Salin", btn_download="Unduh hasil",
        tabs_aria="Beralih antara input dan hasil", tab_input="Input", tab_output="Hasil",
        status_idle="Tempel kode sumber",
        input_search_mode_label="Mode pencarian", opt_contains="Berisi", opt_exact_line="Kecocokan tepat (baris)", opt_regex="Regex",
        input_search_placeholder="Cari di teks input…", prev_title="Hasil sebelumnya", next_title="Hasil berikutnya", clear_title="Hapus pencarian",
        input_placeholder="Tempel kode sumber Anda di sini",
        output_label="Hasil", expand_all="▾ Buka semua", collapse_all="▸ Lipat semua",
        opt_exact="Kecocokan tepat", output_search_placeholder="Cari di teks hasil…",
        language_label="Bahasa",
        language_plain="Teks biasa (tanpa penyorotan)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint='Tips. Alat ini hanya menambahkan penyorotan sintaks untuk meningkatkan keterbacaan; alat ini tidak memeriksa apakah kode dapat dikompilasi atau berjalan dengan benar. '
             'Memilih bahasa yang sesuai dengan kode Anda akan menghasilkan pewarnaan yang lebih akurat; jika tidak yakin, pilih "Teks biasa" untuk menampilkan kode apa adanya. '
             "Alat ini membundel secara lokal pustaka sumber terbuka "
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> '
             "(Lisensi MIT), sehingga penyorotan tetap berlangsung sepenuhnya di browser Anda.",
        usage_h2="Cara menggunakan alat ini",
        usage_items=[
            "Tempel kode sumber ke kotak input di sebelah kiri.",
            'Pilih "Bahasa" yang sesuai dengan kode Anda (Java, C#, Python, Go, dll.) untuk penyorotan yang akurat.',
            'Klik "Terapkan penyorotan" (juga otomatis diterapkan saat Anda mengetik) untuk melihat hasil yang disorot di sebelah kanan.',
            'Dapatkan hasil yang disorot atau teks asli dengan "Salin" atau "Unduh hasil".',
            "Semua pemrosesan terjadi di browser Anda — kode yang Anda masukkan tidak pernah dikirim ke server.",
        ],
        tips_h2="Tips terkait",
        tips_items=[
            "Alat ini hanya menambahkan pewarnaan untuk meningkatkan keterbacaan; alat ini tidak mengompilasi, menjalankan, atau memvalidasi kode Anda.",
            'Jika bahasa Anda tidak ada dalam daftar, atau penyorotan tidak terlihat bagus, coba pilih bahasa yang serupa atau gunakan "Teks biasa".',
            "Jika Anda juga perlu bekerja dengan JSON, XML, atau SQL, coba Pemformat JSON, Pemformat XML, Konverter JSON ↔ XML, atau Pemformat SQL di tautan terkait di bawah.",
        ],
    ),
    "de": dict(
        title="Code-Viewer / Syntaxhervorhebung - Kostenloses Online-Tool | Formix",
        description="Fügen Sie Quellcode ein und erhalten Sie kostenlos Syntaxhervorhebung online. Unterstützt Java, C#, C, C++, Python, JavaScript, TypeScript, Go, Rust, Kotlin, Swift, PHP, Ruby, HTML/XML, CSS, Bash, JSON, YAML, Markdown und SQL. Die gesamte Verarbeitung erfolgt im Browser.",
        keywords="code viewer, syntaxhervorhebung, online code highlighting tool, java syntaxhervorhebung, c# hervorhebung, python code hervorhebung, kostenloser code viewer",
        og_title="Code-Viewer / Syntaxhervorhebung | Formix",
        og_description="Ein kostenloser Online-Code-Viewer, der über 20 Sprachen unterstützt; die gesamte Verarbeitung erfolgt im Browser.",
        jsonld_name="Code-Viewer / Syntaxhervorhebung",
        jsonld_description="Kostenloses Online-Tool, das eingefügtem Quellcode Syntaxhervorhebung hinzufügt, unterstützt über 20 Programmier-/Markup-Sprachen.",
        h1="Code-Viewer",
        lead="Fügen Sie links Quellcode ein und wählen Sie eine Sprache; rechts sehen Sie ein lesbares Ergebnis mit Syntaxhervorhebung. Daten werden nie an einen Server gesendet.",
        btn_format="Hervorhebung anwenden", btn_sample="Beispiel laden", btn_clear="Leeren",
        indent_label="Einrückungsgröße", indent2="2-Leerzeichen-Einrückung", indent4="4-Leerzeichen-Einrückung", indenttab="Tab-Einrückung",
        btn_copy="Kopieren", btn_copy_minify="Kopieren", btn_download="Ergebnis herunterladen",
        tabs_aria="Zwischen Eingabe und Ergebnis wechseln", tab_input="Eingabe", tab_output="Ergebnis",
        status_idle="Quellcode einfügen",
        input_search_mode_label="Suchmodus", opt_contains="Enthält", opt_exact_line="Exakte Übereinstimmung (Zeile)", opt_regex="Regex",
        input_search_placeholder="Im Eingabetext suchen…", prev_title="Vorherige Übereinstimmung", next_title="Nächste Übereinstimmung", clear_title="Suche leeren",
        input_placeholder="Fügen Sie hier Ihren Quellcode ein",
        output_label="Ergebnis", expand_all="▾ Alle ausklappen", collapse_all="▸ Alle einklappen",
        opt_exact="Exakte Übereinstimmung", output_search_placeholder="Im Ergebnistext suchen…",
        language_label="Sprache",
        language_plain="Nur Text (keine Hervorhebung)", language_java="Java", language_csharp="C#", language_c="C", language_cpp="C++",
        language_python="Python", language_javascript="JavaScript", language_typescript="TypeScript", language_go="Go",
        language_rust="Rust", language_kotlin="Kotlin", language_swift="Swift", language_php="PHP", language_ruby="Ruby",
        language_markup="HTML / XML", language_css="CSS", language_bash="Bash / Shell", language_json="JSON",
        language_yaml="YAML", language_markdown="Markdown", language_sql="SQL",
        hint='Tipp. Dieses Tool fügt nur zur besseren Lesbarkeit Syntaxhervorhebung hinzu; es prüft nicht, ob der Code korrekt kompiliert oder ausgeführt wird. '
             'Die Wahl der zu Ihrem Code passenden Sprache führt zu einer genaueren Farbgebung; wenn Sie unsicher sind, wählen Sie „Nur Text", um den Code unverändert anzuzeigen. '
             "Dieses Tool bündelt lokal die Open-Source-Bibliothek "
             '<a href="https://github.com/PrismJS/prism" rel="noopener noreferrer" target="_blank">Prism.js</a> '
             "(MIT-Lizenz), sodass die Hervorhebung weiterhin vollständig in Ihrem Browser erfolgt.",
        usage_h2="So verwenden Sie dieses Tool",
        usage_items=[
            "Fügen Sie den Quellcode in das Eingabefeld links ein.",
            'Wählen Sie die „Sprache", die zu Ihrem Code passt (Java, C#, Python, Go usw.), für eine genaue Hervorhebung.',
            'Klicken Sie auf „Hervorhebung anwenden" (wird auch automatisch beim Tippen angewendet), um das hervorgehobene Ergebnis rechts zu sehen.',
            'Holen Sie sich das hervorgehobene Ergebnis oder den Originaltext über „Kopieren" oder „Ergebnis herunterladen".',
            "Die gesamte Verarbeitung erfolgt in Ihrem Browser — der von Ihnen eingegebene Code wird nie an einen Server gesendet.",
        ],
        tips_h2="Verwandte Tipps",
        tips_items=[
            "Dieses Tool fügt nur Farbgebung zur besseren Lesbarkeit hinzu; es kompiliert, führt oder validiert Ihren Code nicht.",
            'Wenn Ihre Sprache nicht in der Liste ist oder die Hervorhebung nicht gut aussieht, versuchen Sie eine ähnliche Sprache zu wählen oder verwenden Sie „Nur Text".',
            "Wenn Sie auch mit JSON, XML oder SQL arbeiten müssen, probieren Sie den JSON-Formatierer, den XML-Formatierer, den JSON ↔ XML Konverter oder den SQL-Formatierer in den verwandten Links unten.",
        ],
    ),
}

CONTENT["tool_number"] = {
    "en": dict(
        title="Number Reader / Number to Words Converter - Free Online Tool | Formix",
        description="Convert numbers into words online, free. Supports cardinal, ordinal, phone/account digit reading, time, date, and currency, with multiple reading styles (e.g. Sino vs. native Korean, or standard vs. formal). Runs entirely in your browser.",
        keywords="number to words, number reader online, spell out numbers, ordinal number converter, currency to words, number to words converter free",
        og_title="Number Reader / Number to Words Converter | Formix",
        og_description="A free online tool that converts numbers into words, covering cardinal, ordinal, phone numbers, time, date, and currency. Runs entirely in your browser.",
        jsonld_name="Number Reader / Number to Words Converter",
        jsonld_description="A free online tool that converts numbers into words for cardinal, ordinal, phone/account digits, time, date, and currency, with multiple reading styles.",
        h1="Number Reader",
        lead="Enter numbers on the left (one per line), pick a mode and style, and see how they're read out loud on the right. Nothing is sent to a server.",
        btn_format="Convert", btn_sample="Load sample", btn_clear="Clear",
        indent_label="Indent size", indent2="2-space indent", indent4="4-space indent", indenttab="Tab indent",
        btn_copy="Copy", btn_copy_minify="Copy", btn_download="Download result",
        tabs_aria="Switch between input and output", tab_input="Input", tab_output="Output",
        status_idle="Enter a number (one per line)",
        input_search_mode_label="Search mode", opt_contains="Contains", opt_exact_line="Exact (line)", opt_regex="Regex",
        input_search_placeholder="Search the input text…", prev_title="Previous match", next_title="Next match", clear_title="Clear search",
        input_placeholder="Enter a number (one per line)",
        output_label="Output", expand_all="▾ Expand all", collapse_all="▸ Collapse all",
        opt_exact="Exact", output_search_placeholder="Search the output text…",
        mode_label="Mode", style_label="Style",
        mode_cardinal="Number (cardinal)", mode_ordinal="Ordinal", mode_digits="Phone / account number",
        mode_time="Time", mode_date="Date", mode_currency="Currency",
        hint="Tip. Everything runs locally in your browser — nothing you type is ever sent to a server. "
             "Large integers of any length are supported, along with negative numbers and decimals. "
             "For Korean, try the \"All styles\" option to compare the native (고유어) and Sino-Korean (한자어) readings side by side. "
             "Some highly informal or dialectal readings (for example, certain day-of-month readings in Japanese) are simplified for consistency.",
        usage_h2="How to use this tool",
        usage_items=[
            "Enter one number per line in the box on the left — the format depends on the mode (a plain number, a phone number, a time like 14:30, a date like 2026-09-30, etc.).",
            'Pick a "Mode" (cardinal, ordinal, phone/account number, time, date, or currency) and, where available, a "Style" (for example Sino vs. native Korean, or standard vs. formal).',
            'Click "Convert" (or just wait — it also updates automatically as you type) to see the reading on the right, one line per input line.',
            '"Copy" or "Download result" to grab the converted text.',
            "Everything happens in your browser — nothing you enter is sent to a server.",
        ],
        tips_h2="Related tips",
        tips_items=[
            "For Korean, native-style (고유어) numbers only exist for 0–99 — larger native-range requests automatically fall back to the Sino-Korean (한자어) reading.",
            "\"Formal\" / \"大写\" / \"大字\" styles are the anti-fraud number forms traditionally used on checks, invoices, and legal documents in East Asia.",
            "This tool only converts numbers to words for reading purposes — it doesn't perform currency conversion between different currencies.",
        ],
    ),
    "ko": dict(
        title="숫자 읽기 변환기 - 무료 온라인 도구 | Formix",
        description="숫자를 문자로 변환해 무료로 온라인에서 읽는 법을 확인하세요. 일반(기수), 서수, 전화·계좌번호, 시간, 날짜, 화폐를 지원하며, 한자어/고유어/갖은자 등 여러 표기 방식을 제공합니다. 모든 처리는 브라우저 안에서만 이뤄집니다.",
        keywords="숫자 한글로 변환, 숫자 읽기, 금액 한글 표기, 서수 변환, 전화번호 읽기, 숫자 한자어 고유어, 무료 숫자 변환기",
        og_title="숫자 읽기 변환기 | Formix",
        og_description="일반(기수), 서수, 전화번호, 시간, 날짜, 화폐까지 지원하는 무료 온라인 숫자 읽기 변환기. 모든 처리는 브라우저 안에서 이뤄집니다.",
        jsonld_name="숫자 읽기 변환기",
        jsonld_description="숫자를 일반(기수), 서수, 전화·계좌번호, 시간, 날짜, 화폐 등 다양한 방식으로 읽어주는 무료 온라인 도구. 언어별로 여러 표기 방식을 지원합니다.",
        h1="숫자 읽기 변환기",
        lead="왼쪽에 숫자를 입력하고(한 줄에 하나씩) 모드와 표기 방식을 선택하면 오른쪽에 읽는 법이 표시됩니다. 데이터는 서버로 전송되지 않습니다.",
        btn_format="변환", btn_sample="예시 불러오기", btn_clear="지우기",
        indent_label="들여쓰기 크기", indent2="들여쓰기 2칸", indent4="들여쓰기 4칸", indenttab="들여쓰기 Tab",
        btn_copy="복사", btn_copy_minify="복사", btn_download="결과 다운로드",
        tabs_aria="입력/결과 전환", tab_input="입력", tab_output="결과",
        status_idle="숫자를 입력해주세요 (한 줄에 하나씩)",
        input_search_mode_label="검색 방식", opt_contains="포함", opt_exact_line="일치(줄)", opt_regex="정규식",
        input_search_placeholder="입력한 텍스트에서 검색…", prev_title="이전 일치 항목", next_title="다음 일치 항목", clear_title="검색어 지우기",
        input_placeholder="숫자를 입력해주세요 (한 줄에 하나씩)",
        output_label="결과", expand_all="▾ 모두 펼치기", collapse_all="▸ 모두 접기",
        opt_exact="일치", output_search_placeholder="결과 텍스트에서 검색…",
        mode_label="모드", style_label="표기 방식",
        mode_cardinal="일반 숫자(기수)", mode_ordinal="서수", mode_digits="전화·계좌번호",
        mode_time="시간", mode_date="날짜", mode_currency="화폐",
        hint='Tip. 모든 변환은 브라우저 안에서만 이뤄지며, 입력한 내용은 서버로 전송되지 않습니다. '
             '자릿수에 관계없이 아주 큰 정수는 물론 음수·소수점도 지원합니다. '
             '한국어에서는 "전체 비교" 옵션으로 고유어와 한자어 읽기를 한눈에 비교해볼 수 있습니다. '
             '일본어 날짜의 일부 관용적 읽기(1일=ついたち 등)처럼 매우 구어적이거나 방언적인 읽기는 일관성을 위해 단순화되어 있습니다.',
        usage_h2="이 도구는 이렇게 사용하세요",
        usage_items=[
            "왼쪽 입력창에 한 줄에 하나씩 숫자를 입력하세요. 형식은 모드에 따라 다릅니다(일반 숫자, 전화번호, 14:30 같은 시간, 2026-09-30 같은 날짜 등).",
            '"모드"(일반, 서수, 전화·계좌번호, 시간, 날짜, 화폐)를 선택하고, 가능하다면 "표기 방식"(예: 한자어/고유어, 표준/갖은자)도 선택하세요.',
            '"변환" 버튼을 클릭하거나(입력하는 동안 자동으로도 적용됩니다) 오른쪽에서 입력한 줄마다 읽는 법을 확인하세요.',
            '"복사" 또는 "결과 다운로드"로 변환된 텍스트를 가져갈 수 있습니다.',
            "모든 처리는 브라우저 안에서만 이뤄지며, 입력한 내용은 서버로 전송되지 않습니다.",
        ],
        tips_h2="관련 팁",
        tips_items=[
            "한국어 고유어(순우리말) 표기는 0~99까지만 존재합니다. 그 범위를 벗어나면 자동으로 한자어 읽기로 대체됩니다.",
            '"갖은자" 표기는 계약서·수표·영수증 등에서 금액 위변조를 방지하기 위해 전통적으로 사용해온 한자 표기입니다(壹, 貳, 參 등).',
            "이 도구는 숫자를 읽는 법(문자 표기)만 변환할 뿐, 서로 다른 통화 간의 환율 변환은 제공하지 않습니다.",
        ],
    ),
    "ja": dict(
        title="数字の読み方変換 - 無料オンラインツール | Formix",
        description="数字を文字に変換して読み方を無料でオンライン確認できます。基数・序数・電話/口座番号・時刻・日付・通貨に対応し、標準・大字など複数の表記方式を提供します。すべての処理はブラウザ内で行われます。",
        keywords="数字 読み方 変換, 数値 漢数字 変換, 序数 変換, 電話番号 読み方, 大字 変換, 無料 数字変換ツール",
        og_title="数字の読み方変換 | Formix",
        og_description="基数・序数・電話番号・時刻・日付・通貨に対応した無料オンライン数字読み上げ変換ツール。すべての処理はブラウザ内で行われます。",
        jsonld_name="数字の読み方変換",
        jsonld_description="数字を基数・序数・電話/口座番号・時刻・日付・通貨など様々な形式で変換する無料オンラインツール。複数の表記方式に対応しています。",
        h1="数字の読み方変換",
        lead="左側に数字を入力し(1行に1つ)、モードと表記方式を選択すると、右側に読み方が表示されます。データはサーバーに送信されません。",
        btn_format="変換", btn_sample="例を読み込む", btn_clear="クリア",
        indent_label="インデントサイズ", indent2="インデント2文字", indent4="インデント4文字", indenttab="インデントTab",
        btn_copy="コピー", btn_copy_minify="コピー", btn_download="結果をダウンロード",
        tabs_aria="入力/結果切り替え", tab_input="入力", tab_output="結果",
        status_idle="数値を入力してください（1行に1つ）",
        input_search_mode_label="検索モード", opt_contains="含む", opt_exact_line="完全一致(行)", opt_regex="正規表現",
        input_search_placeholder="入力テキストを検索…", prev_title="前の一致", next_title="次の一致", clear_title="検索をクリア",
        input_placeholder="数値を入力してください（1行に1つ）",
        output_label="結果", expand_all="▾ すべて展開", collapse_all="▸ すべて折りたたむ",
        opt_exact="完全一致", output_search_placeholder="結果テキストを検索…",
        mode_label="モード", style_label="表記方式",
        mode_cardinal="数値（基数）", mode_ordinal="序数", mode_digits="電話・口座番号",
        mode_time="時刻", mode_date="日付", mode_currency="通貨",
        hint="Tip. すべての変換はブラウザ内でのみ行われ、入力内容はサーバーに送信されません。"
             "桁数に関わらず非常に大きな整数、負の数、小数にも対応しています。"
             "日付の一部の慣用的な読み方（1日=ついたち 等）のような非常に口語的・方言的な読みは、一貫性のため簡略化しています。",
        usage_h2="このツールの使い方",
        usage_items=[
            "左側の入力欄に1行に1つずつ数値を入力します。形式はモードによって異なります（数値、電話番号、14:30のような時刻、2026-09-30のような日付など）。",
            "「モード」（基数、序数、電話・口座番号、時刻、日付、通貨）を選択し、可能な場合は「表記方式」（標準/大字など）も選択します。",
            "「変換」ボタンをクリックするか（入力中も自動で適用されます）、右側で各行の読み方を確認してください。",
            "「コピー」または「結果をダウンロード」で変換されたテキストを取得できます。",
            "すべての処理はブラウザ内で行われ、入力した内容がサーバーに送信されることはありません。",
        ],
        tips_h2="関連のヒント",
        tips_items=[
            "「大字」表記は、証書・契約書・領収書などで金額の改ざんを防ぐために伝統的に使われてきた漢数字表記です（壱、弐、参 等）。",
            "日付の年は慣例に従い、桁ごとに読む形式（二〇二六年 等）で表示されます。",
            "このツールは数字の読み方（文字表記）を変換するだけで、通貨間の為替換算は行いません。",
        ],
    ),
    "zh": dict(
        title="数字读法转换 - 免费在线工具 | Formix",
        description="将数字转换为文字，免费在线查看读法。支持基数、序数、电话/账号、时间、日期、货币，并提供小写/大写等多种表示方式。所有处理均在浏览器中完成。",
        keywords="数字转中文, 数字大写转换, 序数转换, 电话号码读法, 金额大写, 免费数字转换工具",
        og_title="数字读法转换 | Formix",
        og_description="支持基数、序数、电话号码、时间、日期、货币的免费在线数字读法转换工具，所有处理均在浏览器中完成。",
        jsonld_name="数字读法转换",
        jsonld_description="将数字转换为基数、序数、电话/账号、时间、日期、货币等多种形式的免费在线工具，支持多种表示方式。",
        h1="数字读法转换",
        lead="在左侧输入数字（每行一个），选择模式和表示方式后，右侧会显示读法。数据不会发送到服务器。",
        btn_format="转换", btn_sample="加载示例", btn_clear="清空",
        indent_label="缩进大小", indent2="2 格缩进", indent4="4 格缩进", indenttab="Tab 缩进",
        btn_copy="复制", btn_copy_minify="复制", btn_download="下载结果",
        tabs_aria="切换输入/结果", tab_input="输入", tab_output="结果",
        status_idle="请输入数字（每行一个）",
        input_search_mode_label="搜索模式", opt_contains="包含", opt_exact_line="精确匹配(整行)", opt_regex="正则表达式",
        input_search_placeholder="在输入文本中搜索…", prev_title="上一个匹配项", next_title="下一个匹配项", clear_title="清除搜索",
        input_placeholder="请输入数字（每行一个）",
        output_label="结果", expand_all="▾ 全部展开", collapse_all="▸ 全部折叠",
        opt_exact="精确匹配", output_search_placeholder="在结果文本中搜索…",
        mode_label="模式", style_label="表示方式",
        mode_cardinal="数字（基数）", mode_ordinal="序数", mode_digits="电话·账号",
        mode_time="时间", mode_date="日期", mode_currency="货币",
        hint="提示。所有转换均在浏览器本地完成，您输入的内容不会发送到服务器。"
             "支持任意位数的大整数、负数和小数。"
             "部分非常口语化或方言化的读法（例如日语中某些日期的习惯读法）为保持一致性已做简化处理。",
        usage_h2="使用方法",
        usage_items=[
            "在左侧输入框中每行输入一个数字，格式取决于所选模式（普通数字、电话号码、14:30 这样的时间、2026-09-30 这样的日期等）。",
            "选择「模式」（基数、序数、电话/账号、时间、日期、货币），如可选，也选择「表示方式」（例如小写/大写）。",
            "点击「转换」按钮（输入时也会自动转换），即可在右侧查看每一行的读法。",
            "通过「复制」或「下载结果」获取转换后的文本。",
            "所有处理均在浏览器内完成，您输入的内容不会发送到服务器。",
        ],
        tips_h2="相关提示",
        tips_items=[
            "「大写」表示方式（壹、贰、叁等）是财务票据、合同等场景中传统上用于防止金额篡改的汉字数字写法。",
            "日期中的年份按照惯例逐位读出（例如 二〇二六年）。",
            "此工具仅转换数字的读法（文字表示），不提供不同货币之间的汇率换算。",
        ],
    ),
}

CONTENT["tool_typing"] = {
    "en": dict(
        title="Typing Speed Test (WPM) - Free Online Tool | Formix",
        description="Free online typing speed test. Type the given passage to measure your words per minute (WPM) and accuracy, then copy your result to share. Everything runs locally in your browser.",
        keywords="typing speed test, wpm test, typing test online, free typing test, type racer, keyboard speed test, typing practice",
        og_title="Typing Speed Test (WPM) | Formix",
        og_description="Measure your typing speed and accuracy with a free online test, then share your score.",
        jsonld_name="Typing Speed Test",
        jsonld_description="A free online tool that measures typing speed (WPM) and accuracy from a short practice passage, entirely in the browser.",
        h1="Typing Speed Test",
        lead="Type the passage below as quickly and accurately as you can. The timer starts on your first keystroke and stops when you finish. Nothing you type is ever sent to a server.",
        status_idle="Start typing to begin", status_active="Typing…", status_done="Done!",
        label_time="Time", label_wpm="WPM", label_accuracy="Accuracy", label_best="Best (this browser)",
        best_none="No record yet",
        btn_restart="New passage", btn_copy_result="Copy result",
        copied_msg="Result copied!",
        result_prefix="⌨️ My Formix Typing Test result",
        share_wpm_label="Speed", share_accuracy_label="Accuracy",
        input_aria="Typing input",
        hint="Tip: all scoring happens in your browser — nothing you type is saved or sent anywhere. Your best score for this passage length is kept only in this browser (localStorage) and is cleared if you clear site data.",
        usage_h2="How to use",
        usage_items=[
            "Click into the text box and start typing the passage shown above it.",
            "The timer starts automatically on your first keystroke.",
            "Correctly typed characters are highlighted; mistakes are marked so you can see them as you go.",
            "When you finish the passage, your WPM (words per minute) and accuracy are calculated instantly.",
            "Click “New passage” to try again with a different text and beat your best score.",
        ],
        tips_h2="Related tips",
        tips_items=[
            "WPM is calculated using the standard convention of 5 characters = 1 \"word\", based on correctly typed characters.",
            "Accuracy counts every keystroke, including corrected mistakes, so backspacing to fix an error still affects your score.",
            "Your best score is stored only on this device (browser localStorage) — it is not uploaded or shared with anyone unless you copy and send it yourself.",
        ],
        leaderboard_h2="Leaderboard", leaderboard_lead="See where your score ranks among everyone who has submitted.",
        leaderboard_loading="Loading…", leaderboard_empty="No scores yet — be the first!",
        leaderboard_error="Couldn't load the leaderboard right now.",
        col_rank="#", col_name="Name", col_wpm="WPM", col_accuracy="Accuracy",
        nickname_placeholder="Enter a nickname (optional)", btn_submit_score="Submit to leaderboard",
        submit_success="Submitted! You ranked #{rank}.", submit_error="Couldn't submit your score. Please try again.",
        submit_rate_limited="Please wait a bit before submitting again.", submitting="Submitting…",
        leaderboard_note="Submitting a score sends your nickname, WPM, and accuracy to our server so it can be shown here — see our Privacy Policy for details. Submission is optional.",
    ),
    "ko": dict(
        title="타자 속도 테스트 (WPM) - 무료 온라인 도구 | Formix",
        description="무료 온라인 타자 속도 테스트. 제시된 문장을 입력해 분당 타수(WPM)와 정확도를 측정하고, 결과를 복사해 공유할 수 있습니다. 모든 채점은 브라우저 안에서만 이뤄집니다.",
        keywords="타자 속도 테스트, 타자연습, 타이핑 테스트, 타자속도, WPM 테스트, 온라인 타자 게임, 개발자 타자연습",
        og_title="타자 속도 테스트 (WPM) | Formix",
        og_description="무료 온라인 타자 속도 테스트로 나의 WPM과 정확도를 측정하고 결과를 공유해보세요.",
        jsonld_name="타자 속도 테스트",
        jsonld_description="짧은 연습 문장으로 타자 속도(WPM)와 정확도를 측정하는 무료 온라인 도구. 모든 처리는 브라우저 안에서 이뤄집니다.",
        h1="타자 속도 테스트",
        lead="아래 문장을 최대한 빠르고 정확하게 입력해보세요. 첫 글자를 입력하는 순간 타이머가 시작되고, 문장을 다 입력하면 자동으로 멈춥니다. 입력한 내용은 서버로 전송되지 않습니다.",
        status_idle="입력을 시작하면 타이머가 시작됩니다", status_active="입력 중…", status_done="완료!",
        label_time="경과 시간", label_wpm="WPM", label_accuracy="정확도", label_best="최고 기록 (이 브라우저)",
        best_none="아직 기록이 없습니다",
        btn_restart="새 문장으로 다시", btn_copy_result="결과 복사",
        copied_msg="결과가 복사되었습니다!",
        result_prefix="⌨️ Formix 타자 속도 테스트 결과",
        share_wpm_label="속도", share_accuracy_label="정확도",
        input_aria="타이핑 입력창",
        hint="안내: 모든 채점은 브라우저 안에서만 이뤄지며, 입력한 내용은 저장되거나 어디로도 전송되지 않습니다. 최고 기록은 이 브라우저에만(localStorage) 저장되며, 사이트 데이터를 지우면 함께 사라집니다.",
        usage_h2="사용 방법",
        usage_items=[
            "입력창을 클릭한 뒤 위에 표시된 문장을 그대로 입력하세요.",
            "첫 글자를 입력하는 순간 타이머가 자동으로 시작됩니다.",
            "올바르게 입력한 글자는 강조 표시되고, 틀린 글자는 바로 확인할 수 있도록 표시됩니다.",
            "문장을 다 입력하면 WPM(분당 타수)과 정확도가 즉시 계산됩니다.",
            "“새 문장으로 다시”를 눌러 다른 문장으로 재도전하고 최고 기록을 갱신해보세요.",
        ],
        tips_h2="관련 팁",
        tips_items=[
            "WPM은 일반적인 기준(5글자 = 1단어)에 따라, 올바르게 입력한 글자 수를 기준으로 계산됩니다.",
            "정확도는 수정한 실수를 포함한 전체 입력 횟수를 기준으로 계산되므로, 백스페이스로 고쳐도 점수에 영향을 줍니다.",
            "최고 기록은 이 기기(브라우저 localStorage)에만 저장되며, 직접 복사해 보내지 않는 한 어디로도 전송되지 않습니다.",
        ],
        leaderboard_h2="랭킹", leaderboard_lead="지금까지 제출된 기록 중 내 순위를 확인해보세요.",
        leaderboard_loading="불러오는 중…", leaderboard_empty="아직 등록된 기록이 없습니다 — 첫 번째 주인공이 되어보세요!",
        leaderboard_error="지금은 랭킹을 불러올 수 없습니다.",
        col_rank="순위", col_name="닉네임", col_wpm="WPM", col_accuracy="정확도",
        nickname_placeholder="닉네임 입력 (선택)", btn_submit_score="랭킹에 제출",
        submit_success="제출 완료! {rank}위에 올랐습니다.", submit_error="제출에 실패했습니다. 다시 시도해주세요.",
        submit_rate_limited="잠시 후 다시 제출해주세요.", submitting="제출 중…",
        leaderboard_note="결과를 제출하면 입력한 닉네임, WPM, 정확도가 서버로 전송되어 여기에 공개됩니다 — 자세한 내용은 개인정보처리방침을 참고해주세요. 제출은 선택 사항입니다.",
    ),
    "ja": dict(
        title="タイピング速度テスト (WPM) - 無料オンラインツール | Formix",
        description="無料オンラインのタイピング速度テスト。表示された文章を入力して、1分間あたりのタイプ数(WPM)と正確率を測定し、結果をコピーしてシェアできます。採点はすべてブラウザ内で行われます。",
        keywords="タイピング速度テスト, タイピング練習, タイピングゲーム, WPM テスト, 無料タイピングテスト, キーボード速度テスト",
        og_title="タイピング速度テスト (WPM) | Formix",
        og_description="無料オンラインのタイピング速度テストで自分のWPMと正確率を測定し、結果をシェアしましょう。",
        jsonld_name="タイピング速度テスト",
        jsonld_description="短い練習文でタイピング速度(WPM)と正確率を測定する無料オンラインツール。すべての処理はブラウザ内で行われます。",
        h1="タイピング速度テスト",
        lead="下に表示された文章をできるだけ速く正確に入力してください。最初のキー入力でタイマーが開始し、入力が完了すると自動的に停止します。入力した内容はサーバーに送信されません。",
        status_idle="入力を開始するとタイマーが始まります", status_active="入力中…", status_done="完了!",
        label_time="経過時間", label_wpm="WPM", label_accuracy="正確率", label_best="自己ベスト (このブラウザ)",
        best_none="まだ記録がありません",
        btn_restart="新しい文章で再挑戦", btn_copy_result="結果をコピー",
        copied_msg="結果をコピーしました!",
        result_prefix="⌨️ Formix タイピング速度テストの結果",
        share_wpm_label="速度", share_accuracy_label="正確率",
        input_aria="タイピング入力欄",
        hint="ヒント: 採点はすべてブラウザ内で行われ、入力した内容は保存されたり、どこかに送信されたりすることはありません。自己ベストはこのブラウザのみ(localStorage)に保存され、サイトデータを削除すると消去されます。",
        usage_h2="使い方",
        usage_items=[
            "入力欄をクリックし、上に表示された文章をそのまま入力してください。",
            "最初のキー入力と同時にタイマーが自動的に開始します。",
            "正しく入力できた文字はハイライトされ、間違いはその場で確認できるように表示されます。",
            "文章を入力し終えると、WPM(1分あたりのタイプ数)と正確率が即座に計算されます。",
            "「新しい文章で再挑戦」を押して別の文章に挑戦し、自己ベストを更新しましょう。",
        ],
        tips_h2="関連のヒント",
        tips_items=[
            "WPMは一般的な基準(5文字 = 1単語)に従い、正しく入力できた文字数をもとに計算されます。",
            "正確率は修正した間違いも含めた全入力回数を基準に計算されるため、バックスペースで直しても点数に影響します。",
            "自己ベストはこの端末(ブラウザのlocalStorage)にのみ保存され、自分でコピーして送らない限りどこにも送信されません。",
        ],
        leaderboard_h2="ランキング", leaderboard_lead="これまでに提出された記録の中で自分の順位を確認できます。",
        leaderboard_loading="読み込み中…", leaderboard_empty="まだ記録がありません — 最初の記録を作ってみましょう!",
        leaderboard_error="現在ランキングを読み込めません。",
        col_rank="順位", col_name="ニックネーム", col_wpm="WPM", col_accuracy="正確率",
        nickname_placeholder="ニックネームを入力(任意)", btn_submit_score="ランキングに提出",
        submit_success="提出しました! {rank}位にランクインしました。", submit_error="提出に失敗しました。もう一度お試しください。",
        submit_rate_limited="少し時間を置いてから再度提出してください。", submitting="提出中…",
        leaderboard_note="結果を提出すると、入力したニックネーム・WPM・正確率がサーバーに送信され、ここに公開されます — 詳しくはプライバシーポリシーをご覧ください。提出は任意です。",
    ),
    "zh": dict(
        title="打字速度测试 (WPM) - 免费在线工具 | Formix",
        description="免费在线打字速度测试。输入指定的文章来测量每分钟打字数(WPM)和准确率，并可复制结果进行分享。所有计分均在浏览器中完成。",
        keywords="打字速度测试, 打字练习, 打字游戏, WPM 测试, 免费打字测试, 键盘速度测试",
        og_title="打字速度测试 (WPM) | Formix",
        og_description="通过免费在线打字速度测试测量你的 WPM 和准确率，并分享你的成绩。",
        jsonld_name="打字速度测试",
        jsonld_description="通过简短练习句子测量打字速度(WPM)和准确率的免费在线工具，所有处理均在浏览器中进行。",
        h1="打字速度测试",
        lead="请尽可能快速、准确地输入下方显示的文章。输入第一个字符时计时器自动开始，完成后自动停止。你输入的内容不会发送到服务器。",
        status_idle="开始输入即可启动计时", status_active="输入中…", status_done="完成!",
        label_time="用时", label_wpm="WPM", label_accuracy="准确率", label_best="最佳成绩（本浏览器）",
        best_none="暂无记录",
        btn_restart="换一篇再试", btn_copy_result="复制结果",
        copied_msg="结果已复制!",
        result_prefix="⌨️ 我的 Formix 打字速度测试成绩",
        share_wpm_label="速度", share_accuracy_label="准确率",
        input_aria="打字输入框",
        hint="提示：所有计分均在浏览器本地完成，你输入的内容不会被保存或发送到任何地方。最佳成绩仅保存在本浏览器(localStorage)中，清除网站数据后会一并清除。",
        usage_h2="使用方法",
        usage_items=[
            "点击输入框，然后原样输入上方显示的文章。",
            "输入第一个字符时，计时器会自动开始。",
            "正确输入的字符会高亮显示，错误也会实时标出，方便你查看。",
            "完成文章输入后，系统会立即计算你的 WPM（每分钟打字数）和准确率。",
            "点击“换一篇再试”即可挑战新的文章，刷新你的最佳成绩。",
        ],
        tips_h2="相关提示",
        tips_items=[
            "WPM 按照惯例（5 个字符 = 1 个“单词”）、基于正确输入的字符数计算。",
            "准确率会计入所有按键（包括纠正过的错误），因此用退格键修正也会影响最终得分。",
            "最佳成绩仅保存在本设备（浏览器 localStorage）中，除非你自己复制发送，否则不会上传或分享给任何人。",
        ],
        leaderboard_h2="排行榜", leaderboard_lead="查看你的成绩在所有已提交记录中的排名。",
        leaderboard_loading="加载中…", leaderboard_empty="暂无记录 — 来成为第一名吧！",
        leaderboard_error="暂时无法加载排行榜。",
        col_rank="排名", col_name="昵称", col_wpm="WPM", col_accuracy="准确率",
        nickname_placeholder="输入昵称（可选）", btn_submit_score="提交到排行榜",
        submit_success="提交成功！你排名第 {rank} 位。", submit_error="提交失败，请重试。",
        submit_rate_limited="请稍后再试。", submitting="提交中…",
        leaderboard_note="提交成绩会将你输入的昵称、WPM 和准确率发送到服务器并在此公开展示 — 详情请参阅隐私政策。提交为可选项。",
    ),
    "es": dict(
        title="Prueba de Velocidad de Escritura (PPM) - Herramienta Gratuita en Línea | Formix",
        description="Prueba de velocidad de escritura gratuita en línea. Escribe el pasaje indicado para medir tus palabras por minuto (PPM) y precisión, y copia tu resultado para compartirlo. Todo el cálculo se hace en tu navegador.",
        keywords="prueba de velocidad de escritura, práctica de mecanografía, juego de mecanografía, prueba PPM, prueba de escritura gratis, prueba de velocidad de teclado",
        og_title="Prueba de Velocidad de Escritura (PPM) | Formix",
        og_description="Mide tu PPM y precisión con una prueba de velocidad de escritura en línea gratuita, y comparte tu puntuación.",
        jsonld_name="Prueba de Velocidad de Escritura",
        jsonld_description="Herramienta en línea gratuita que mide la velocidad de escritura (PPM) y la precisión con pasajes cortos de práctica; todo el procesamiento ocurre en el navegador.",
        h1="Prueba de velocidad de escritura",
        lead="Escribe el pasaje que se muestra abajo tan rápido y preciso como puedas. El cronómetro comienza automáticamente con tu primer carácter y se detiene cuando terminas. Lo que escribes nunca se envía a un servidor.",
        status_idle="Empieza a escribir para iniciar el cronómetro", status_active="Escribiendo…", status_done="¡Completado!",
        label_time="Tiempo", label_wpm="PPM", label_accuracy="Precisión", label_best="Mejor marca (este navegador)",
        best_none="Aún no hay registro",
        btn_restart="Probar otro pasaje", btn_copy_result="Copiar resultado",
        copied_msg="¡Resultado copiado!",
        result_prefix="⌨️ Mi resultado en la Prueba de velocidad de escritura de Formix",
        share_wpm_label="Velocidad", share_accuracy_label="Precisión",
        input_aria="Cuadro de entrada de escritura",
        hint="Consejo. Todo el cálculo se hace localmente en tu navegador; lo que escribes nunca se guarda ni se envía a ningún lugar. Tu mejor marca se guarda solo en este navegador (localStorage) y se borrará si limpias los datos del sitio.",
        usage_h2="Cómo usar esta herramienta",
        usage_items=[
            "Haz clic en el cuadro de entrada y escribe el pasaje mostrado arriba exactamente como aparece.",
            "El cronómetro comienza automáticamente con tu primer carácter.",
            "Los caracteres correctos se resaltan y los errores se marcan en tiempo real para que puedas verlos.",
            "Al terminar el pasaje, tu PPM (palabras por minuto) y precisión se calculan al instante.",
            "Haz clic en \"Probar otro pasaje\" para intentarlo con un nuevo texto y mejorar tu mejor marca.",
        ],
        tips_h2="Consejos relacionados",
        tips_items=[
            "El PPM se calcula usando la convención estándar (5 caracteres = 1 \"palabra\"), basado en caracteres correctamente escritos.",
            "La precisión cuenta todas las pulsaciones (incluidas las correcciones), así que corregir con retroceso también afecta tu puntuación final.",
            "Tu mejor marca se guarda solo en este dispositivo (localStorage del navegador) y nunca se sube ni se comparte con nadie a menos que la copies y la envíes tú mismo.",
        ],
        leaderboard_h2="Tabla de clasificación", leaderboard_lead="Mira cómo se compara tu puntuación con todos los resultados enviados.",
        leaderboard_loading="Cargando…", leaderboard_empty="Aún no hay registros — ¡sé el primero!",
        leaderboard_error="No se pudo cargar la tabla de clasificación por ahora.",
        col_rank="Puesto", col_name="Apodo", col_wpm="PPM", col_accuracy="Precisión",
        nickname_placeholder="Ingresa un apodo (opcional)", btn_submit_score="Enviar a la tabla de clasificación",
        submit_success="¡Enviado! Quedaste en el puesto {rank}.", submit_error="Error al enviar, intenta de nuevo.",
        submit_rate_limited="Por favor espera e intenta de nuevo.", submitting="Enviando…",
        leaderboard_note="Enviar tu puntuación envía el apodo que escribiste junto con tu PPM y precisión a nuestro servidor y los muestra públicamente aquí — consulta la Política de privacidad para más detalles. Enviar es opcional.",
    ),
    "vi": dict(
        title="Kiểm Tra Tốc Độ Đánh Máy (WPM) - Công cụ Trực tuyến Miễn phí | Formix",
        description="Kiểm tra tốc độ đánh máy trực tuyến miễn phí. Gõ đoạn văn được chỉ định để đo số từ mỗi phút (WPM) và độ chính xác, và sao chép kết quả để chia sẻ. Mọi phép tính diễn ra trong trình duyệt của bạn.",
        keywords="kiểm tra tốc độ đánh máy, luyện đánh máy, trò chơi đánh máy, kiểm tra WPM, kiểm tra đánh máy miễn phí, kiểm tra tốc độ bàn phím",
        og_title="Kiểm Tra Tốc Độ Đánh Máy (WPM) | Formix",
        og_description="Đo WPM và độ chính xác của bạn bằng bài kiểm tra tốc độ đánh máy trực tuyến miễn phí, và chia sẻ điểm số của bạn.",
        jsonld_name="Kiểm Tra Tốc Độ Đánh Máy",
        jsonld_description="Công cụ trực tuyến miễn phí đo tốc độ đánh máy (WPM) và độ chính xác qua các đoạn luyện tập ngắn; mọi xử lý diễn ra trong trình duyệt.",
        h1="Kiểm tra tốc độ đánh máy",
        lead="Hãy gõ đoạn văn hiển thị dưới đây nhanh và chính xác nhất có thể. Bộ đếm giờ tự động bắt đầu khi bạn gõ ký tự đầu tiên và tự động dừng khi hoàn thành. Nội dung bạn gõ không bao giờ được gửi lên máy chủ.",
        status_idle="Bắt đầu gõ để khởi động bộ đếm giờ", status_active="Đang gõ…", status_done="Hoàn thành!",
        label_time="Thời gian", label_wpm="WPM", label_accuracy="Độ chính xác", label_best="Kỷ lục tốt nhất (trình duyệt này)",
        best_none="Chưa có kỷ lục",
        btn_restart="Thử đoạn văn khác", btn_copy_result="Sao chép kết quả",
        copied_msg="Đã sao chép kết quả!",
        result_prefix="⌨️ Kết quả Kiểm tra tốc độ đánh máy của tôi trên Formix",
        share_wpm_label="Tốc độ", share_accuracy_label="Độ chính xác",
        input_aria="Khung nhập đánh máy",
        hint="Mẹo. Mọi phép tính được thực hiện cục bộ trong trình duyệt của bạn; nội dung bạn gõ không bao giờ được lưu lại hoặc gửi đi bất cứ đâu. Kỷ lục tốt nhất của bạn chỉ được lưu trong trình duyệt này (localStorage) và sẽ bị xóa nếu bạn xóa dữ liệu trang web.",
        usage_h2="Cách sử dụng công cụ này",
        usage_items=[
            "Nhấp vào khung nhập, sau đó gõ chính xác đoạn văn hiển thị ở trên.",
            "Bộ đếm giờ tự động bắt đầu khi bạn gõ ký tự đầu tiên.",
            "Các ký tự gõ đúng sẽ được tô sáng và lỗi được đánh dấu theo thời gian thực để bạn dễ theo dõi.",
            "Khi hoàn thành đoạn văn, WPM (số từ mỗi phút) và độ chính xác của bạn được tính ngay lập tức.",
            "Nhấp \"Thử đoạn văn khác\" để thử với một đoạn văn mới và cải thiện kỷ lục tốt nhất của bạn.",
        ],
        tips_h2="Mẹo liên quan",
        tips_items=[
            "WPM được tính theo quy ước chuẩn (5 ký tự = 1 \"từ\"), dựa trên số ký tự gõ đúng.",
            "Độ chính xác tính tất cả các lần nhấn phím (bao gồm cả các lần sửa lỗi), vì vậy việc sửa bằng phím backspace cũng ảnh hưởng đến điểm số cuối cùng.",
            "Kỷ lục tốt nhất của bạn chỉ được lưu trên thiết bị này (localStorage của trình duyệt) và không bao giờ được tải lên hay chia sẻ với ai trừ khi bạn tự sao chép và gửi nó.",
        ],
        leaderboard_h2="Bảng xếp hạng", leaderboard_lead="Xem điểm số của bạn so với tất cả các kết quả đã gửi.",
        leaderboard_loading="Đang tải…", leaderboard_empty="Chưa có kỷ lục nào — hãy là người đầu tiên!",
        leaderboard_error="Hiện không thể tải bảng xếp hạng.",
        col_rank="Hạng", col_name="Biệt danh", col_wpm="WPM", col_accuracy="Độ chính xác",
        nickname_placeholder="Nhập biệt danh (không bắt buộc)", btn_submit_score="Gửi lên bảng xếp hạng",
        submit_success="Đã gửi! Bạn đứng ở hạng {rank}.", submit_error="Gửi thất bại, vui lòng thử lại.",
        submit_rate_limited="Vui lòng chờ và thử lại sau.", submitting="Đang gửi…",
        leaderboard_note="Gửi điểm số sẽ gửi biệt danh bạn nhập cùng với WPM và độ chính xác của bạn đến máy chủ của chúng tôi và hiển thị công khai ở đây — xem Chính sách bảo mật để biết chi tiết. Việc gửi là tùy chọn.",
    ),
    "pt": dict(
        title="Teste de Velocidade de Digitação (PPM) - Ferramenta Gratuita Online | Formix",
        description="Teste de velocidade de digitação gratuito online. Digite o trecho indicado para medir suas palavras por minuto (PPM) e precisão, e copie seu resultado para compartilhar. Todo o cálculo é feito no seu navegador.",
        keywords="teste de velocidade de digitação, prática de digitação, jogo de digitação, teste de PPM, teste de digitação gratuito, teste de velocidade de teclado",
        og_title="Teste de Velocidade de Digitação (PPM) | Formix",
        og_description="Meça seu PPM e precisão com um teste de velocidade de digitação online gratuito, e compartilhe sua pontuação.",
        jsonld_name="Teste de Velocidade de Digitação",
        jsonld_description="Ferramenta online gratuita que mede a velocidade de digitação (PPM) e a precisão com trechos curtos de prática; todo o processamento ocorre no navegador.",
        h1="Teste de velocidade de digitação",
        lead="Digite o trecho exibido abaixo o mais rápido e preciso possível. O cronômetro começa automaticamente no seu primeiro caractere e para quando você termina. O que você digita nunca é enviado a um servidor.",
        status_idle="Comece a digitar para iniciar o cronômetro", status_active="Digitando…", status_done="Concluído!",
        label_time="Tempo", label_wpm="PPM", label_accuracy="Precisão", label_best="Melhor marca (este navegador)",
        best_none="Ainda sem registro",
        btn_restart="Tentar outro trecho", btn_copy_result="Copiar resultado",
        copied_msg="Resultado copiado!",
        result_prefix="⌨️ Meu resultado no Teste de velocidade de digitação do Formix",
        share_wpm_label="Velocidade", share_accuracy_label="Precisão",
        input_aria="Caixa de entrada de digitação",
        hint="Dica. Todo o cálculo é feito localmente no seu navegador; o que você digita nunca é salvo ou enviado a lugar algum. Sua melhor marca é salva apenas neste navegador (localStorage) e será apagada se você limpar os dados do site.",
        usage_h2="Como usar esta ferramenta",
        usage_items=[
            "Clique na caixa de entrada e digite o trecho mostrado acima exatamente como aparece.",
            "O cronômetro começa automaticamente com seu primeiro caractere.",
            "Caracteres digitados corretamente são destacados e os erros são marcados em tempo real para você acompanhar.",
            "Ao terminar o trecho, seu PPM (palavras por minuto) e precisão são calculados instantaneamente.",
            "Clique em \"Tentar outro trecho\" para tentar com um novo texto e melhorar sua melhor marca.",
        ],
        tips_h2="Dicas relacionadas",
        tips_items=[
            "O PPM é calculado usando a convenção padrão (5 caracteres = 1 \"palavra\"), com base em caracteres digitados corretamente.",
            "A precisão conta todas as teclas pressionadas (incluindo correções), então corrigir com backspace também afeta sua pontuação final.",
            "Sua melhor marca é salva apenas neste dispositivo (localStorage do navegador) e nunca é enviada ou compartilhada com ninguém, a menos que você mesmo a copie e envie.",
        ],
        leaderboard_h2="Ranking", leaderboard_lead="Veja como sua pontuação se compara a todos os resultados enviados.",
        leaderboard_loading="Carregando…", leaderboard_empty="Ainda sem registros — seja o primeiro!",
        leaderboard_error="Não foi possível carregar o ranking no momento.",
        col_rank="Posição", col_name="Apelido", col_wpm="PPM", col_accuracy="Precisão",
        nickname_placeholder="Digite um apelido (opcional)", btn_submit_score="Enviar para o ranking",
        submit_success="Enviado! Você ficou na posição {rank}.", submit_error="Falha ao enviar, tente novamente.",
        submit_rate_limited="Aguarde e tente novamente.", submitting="Enviando…",
        leaderboard_note="Enviar sua pontuação envia o apelido que você digitou junto com seu PPM e precisão ao nosso servidor e os exibe publicamente aqui — veja a Política de privacidade para detalhes. O envio é opcional.",
    ),
    "id": dict(
        title="Tes Kecepatan Mengetik (WPM) - Alat Online Gratis | Formix",
        description="Tes kecepatan mengetik online gratis. Ketik paragraf yang ditentukan untuk mengukur kata per menit (WPM) dan akurasi Anda, lalu salin hasil Anda untuk dibagikan. Semua penilaian dilakukan di browser Anda.",
        keywords="tes kecepatan mengetik, latihan mengetik, permainan mengetik, tes WPM, tes mengetik gratis, tes kecepatan keyboard",
        og_title="Tes Kecepatan Mengetik (WPM) | Formix",
        og_description="Ukur WPM dan akurasi Anda dengan tes kecepatan mengetik online gratis, dan bagikan skor Anda.",
        jsonld_name="Tes Kecepatan Mengetik",
        jsonld_description="Alat online gratis yang mengukur kecepatan mengetik (WPM) dan akurasi dengan paragraf latihan singkat; semua pemrosesan terjadi di browser.",
        h1="Tes kecepatan mengetik",
        lead="Ketik paragraf yang ditampilkan di bawah secepat dan seakurat mungkin. Timer otomatis dimulai saat karakter pertama Anda dan berhenti saat Anda selesai. Apa yang Anda ketik tidak pernah dikirim ke server.",
        status_idle="Mulai mengetik untuk memulai timer", status_active="Sedang mengetik…", status_done="Selesai!",
        label_time="Waktu", label_wpm="WPM", label_accuracy="Akurasi", label_best="Rekor terbaik (browser ini)",
        best_none="Belum ada rekor",
        btn_restart="Coba paragraf lain", btn_copy_result="Salin hasil",
        copied_msg="Hasil disalin!",
        result_prefix="⌨️ Hasil Tes Kecepatan Mengetik saya di Formix",
        share_wpm_label="Kecepatan", share_accuracy_label="Akurasi",
        input_aria="Kotak input mengetik",
        hint="Tips. Semua penilaian dilakukan secara lokal di browser Anda; apa yang Anda ketik tidak pernah disimpan atau dikirim ke mana pun. Rekor terbaik Anda hanya disimpan di browser ini (localStorage) dan akan terhapus jika Anda menghapus data situs.",
        usage_h2="Cara menggunakan alat ini",
        usage_items=[
            "Klik kotak input, lalu ketik paragraf yang ditampilkan di atas sesuai aslinya.",
            "Timer otomatis dimulai saat karakter pertama Anda.",
            "Karakter yang diketik dengan benar akan disorot dan kesalahan ditandai secara real-time agar Anda dapat melihatnya.",
            "Setelah menyelesaikan paragraf, WPM (kata per menit) dan akurasi Anda langsung dihitung.",
            "Klik \"Coba paragraf lain\" untuk mencoba teks baru dan meningkatkan rekor terbaik Anda.",
        ],
        tips_h2="Tips terkait",
        tips_items=[
            "WPM dihitung menggunakan konvensi standar (5 karakter = 1 \"kata\"), berdasarkan karakter yang diketik dengan benar.",
            "Akurasi menghitung semua ketukan tombol (termasuk koreksi), jadi memperbaiki dengan backspace juga memengaruhi skor akhir Anda.",
            "Rekor terbaik Anda hanya disimpan di perangkat ini (localStorage browser) dan tidak pernah diunggah atau dibagikan kepada siapa pun kecuali Anda sendiri yang menyalin dan mengirimkannya.",
        ],
        leaderboard_h2="Papan peringkat", leaderboard_lead="Lihat bagaimana skor Anda dibandingkan dengan semua hasil yang telah dikirim.",
        leaderboard_loading="Memuat…", leaderboard_empty="Belum ada rekor — jadilah yang pertama!",
        leaderboard_error="Tidak dapat memuat papan peringkat saat ini.",
        col_rank="Peringkat", col_name="Nama panggilan", col_wpm="WPM", col_accuracy="Akurasi",
        nickname_placeholder="Masukkan nama panggilan (opsional)", btn_submit_score="Kirim ke papan peringkat",
        submit_success="Terkirim! Anda berada di peringkat {rank}.", submit_error="Gagal mengirim, silakan coba lagi.",
        submit_rate_limited="Harap tunggu dan coba lagi.", submitting="Mengirim…",
        leaderboard_note="Mengirim skor Anda akan mengirimkan nama panggilan yang Anda ketik beserta WPM dan akurasi Anda ke server kami dan menampilkannya secara publik di sini — lihat Kebijakan Privasi untuk detailnya. Pengiriman bersifat opsional.",
    ),
    "de": dict(
        title="Schreibgeschwindigkeitstest (WPM) - Kostenloses Online-Tool | Formix",
        description="Kostenloser Online-Schreibgeschwindigkeitstest. Tippen Sie den vorgegebenen Text, um Ihre Wörter pro Minute (WPM) und Genauigkeit zu messen, und kopieren Sie Ihr Ergebnis zum Teilen. Die gesamte Auswertung erfolgt in Ihrem Browser.",
        keywords="schreibgeschwindigkeitstest, tippübung, tippspiel, wpm test, kostenloser tipptest, tastatur geschwindigkeitstest",
        og_title="Schreibgeschwindigkeitstest (WPM) | Formix",
        og_description="Messen Sie Ihren WPM-Wert und Ihre Genauigkeit mit einem kostenlosen Online-Schreibgeschwindigkeitstest und teilen Sie Ihr Ergebnis.",
        jsonld_name="Schreibgeschwindigkeitstest",
        jsonld_description="Kostenloses Online-Tool, das die Schreibgeschwindigkeit (WPM) und Genauigkeit mit kurzen Übungstexten misst; die gesamte Verarbeitung erfolgt im Browser.",
        h1="Schreibgeschwindigkeitstest",
        lead="Tippen Sie den unten angezeigten Text so schnell und genau wie möglich. Der Timer startet automatisch mit Ihrem ersten Zeichen und stoppt, wenn Sie fertig sind. Was Sie tippen, wird nie an einen Server gesendet.",
        status_idle="Beginnen Sie zu tippen, um den Timer zu starten", status_active="Tippen…", status_done="Fertig!",
        label_time="Zeit", label_wpm="WPM", label_accuracy="Genauigkeit", label_best="Bestleistung (dieser Browser)",
        best_none="Noch kein Eintrag",
        btn_restart="Anderen Text versuchen", btn_copy_result="Ergebnis kopieren",
        copied_msg="Ergebnis kopiert!",
        result_prefix="⌨️ Mein Ergebnis im Formix-Schreibgeschwindigkeitstest",
        share_wpm_label="Geschwindigkeit", share_accuracy_label="Genauigkeit",
        input_aria="Tipp-Eingabefeld",
        hint="Tipp. Die gesamte Auswertung erfolgt lokal in Ihrem Browser; was Sie tippen, wird nie gespeichert oder irgendwohin gesendet. Ihre Bestleistung wird nur in diesem Browser (localStorage) gespeichert und gelöscht, wenn Sie die Website-Daten löschen.",
        usage_h2="So verwenden Sie dieses Tool",
        usage_items=[
            "Klicken Sie auf das Eingabefeld und tippen Sie den oben angezeigten Text genau ab.",
            "Der Timer startet automatisch mit Ihrem ersten Zeichen.",
            "Richtig getippte Zeichen werden hervorgehoben, und Fehler werden in Echtzeit markiert, damit Sie sie sehen können.",
            "Nach Abschluss des Textes werden Ihr WPM-Wert (Wörter pro Minute) und Ihre Genauigkeit sofort berechnet.",
            'Klicken Sie auf „Anderen Text versuchen", um es mit einem neuen Text zu versuchen und Ihre Bestleistung zu verbessern.',
        ],
        tips_h2="Verwandte Tipps",
        tips_items=[
            'Der WPM-Wert wird nach der Standardkonvention berechnet (5 Zeichen = 1 „Wort"), basierend auf korrekt getippten Zeichen.',
            "Die Genauigkeit zählt alle Tastenanschläge (einschließlich Korrekturen), sodass das Korrigieren mit der Rücktaste ebenfalls Ihr Endergebnis beeinflusst.",
            "Ihre Bestleistung wird nur auf diesem Gerät (Browser-localStorage) gespeichert und niemals hochgeladen oder mit jemandem geteilt, außer Sie kopieren und senden sie selbst.",
        ],
        leaderboard_h2="Rangliste", leaderboard_lead="Sehen Sie, wie sich Ihr Ergebnis mit allen eingereichten Ergebnissen vergleicht.",
        leaderboard_loading="Lädt…", leaderboard_empty="Noch keine Einträge — seien Sie der Erste!",
        leaderboard_error="Die Rangliste kann derzeit nicht geladen werden.",
        col_rank="Rang", col_name="Spitzname", col_wpm="WPM", col_accuracy="Genauigkeit",
        nickname_placeholder="Spitzname eingeben (optional)", btn_submit_score="An Rangliste senden",
        submit_success="Gesendet! Sie belegen Rang {rank}.", submit_error="Senden fehlgeschlagen, bitte erneut versuchen.",
        submit_rate_limited="Bitte warten Sie und versuchen Sie es erneut.", submitting="Wird gesendet…",
        leaderboard_note="Beim Senden Ihres Ergebnisses werden der von Ihnen eingegebene Spitzname zusammen mit Ihrem WPM-Wert und Ihrer Genauigkeit an unseren Server gesendet und hier öffentlich angezeigt — Details finden Sie in der Datenschutzerklärung. Das Senden ist optional.",
    ),
}

CONTENT["game_syntax"] = {
    "en": dict(
        title="Programming Language Syntax Quiz - Free Online Game | Formix",
        description="Free multiple-choice syntax quiz covering JavaScript, Python, Java, and C. Test your knowledge of basic syntax for each language, right in your browser — no sign-up required.",
        keywords="syntax quiz, programming quiz, javascript quiz, python quiz, java quiz, c programming quiz, coding quiz game, learn programming syntax",
        og_title="Programming Language Syntax Quiz | Formix",
        og_description="A free multiple-choice quiz testing basic syntax knowledge across JavaScript, Python, Java, and C.",
        jsonld_name="Programming Language Syntax Quiz",
        jsonld_description="A free online multiple-choice quiz game that tests basic syntax knowledge for JavaScript, Python, Java, and C, entirely in the browser.",
        h1="Coding Syntax Quiz",
        lead="Pick a programming language and answer short multiple-choice questions about its basic syntax. Great for a quick warm-up or for testing what you remember.",
        lang_select_label="Choose a language",
        btn_start="Start quiz",
        question_progress="Question {current} of {total}",
        score_label="Score",
        correct_label="Correct!",
        incorrect_label="Not quite.",
        explain_label="Explanation",
        btn_next="Next question",
        btn_change_lang="Choose a different language",
        finish_title="Quiz complete!",
        finish_summary="You got {score} out of {total} correct.",
        btn_retry="Try again",
        usage_h2="How to use",
        usage_items=[
            "Pick one of the programming languages below.",
            "Answer each multiple-choice question — you'll see immediately whether you were right, along with a short explanation.",
            "After the last question, you'll see your final score and can try again or pick a different language.",
        ],
        tips_h2="Related tips",
        tips_items=[
            "Questions and their order are shuffled each time you start a quiz, so retrying stays fresh.",
            "This quiz focuses on basic syntax, not advanced language features or best practices.",
            "Everything runs locally in your browser — your answers are never sent to a server.",
        ],
    ),
    "ko": dict(
        title="프로그래밍 언어 문법 퀴즈 - 무료 온라인 게임 | Formix",
        description="JavaScript, Python, Java, C의 기본 문법을 다루는 무료 객관식 퀴즈. 각 언어의 기본 문법 지식을 브라우저에서 바로 테스트해보세요. 회원가입이 필요 없습니다.",
        keywords="문법 퀴즈, 프로그래밍 퀴즈, 자바스크립트 퀴즈, 파이썬 퀴즈, 자바 퀴즈, C언어 퀴즈, 코딩 퀴즈 게임, 개발자 퀴즈",
        og_title="프로그래밍 언어 문법 퀴즈 | Formix",
        og_description="JavaScript, Python, Java, C의 기본 문법 지식을 테스트하는 무료 객관식 퀴즈입니다.",
        jsonld_name="프로그래밍 언어 문법 퀴즈",
        jsonld_description="JavaScript, Python, Java, C의 기본 문법 지식을 테스트하는 무료 온라인 객관식 퀴즈 게임. 모든 처리는 브라우저 안에서 이뤄집니다.",
        h1="코딩 문법 퀴즈",
        lead="프로그래밍 언어를 선택하고 기본 문법에 관한 짧은 객관식 문제를 풀어보세요. 가볍게 실력을 점검하거나 워밍업하기에 좋습니다.",
        lang_select_label="언어를 선택하세요",
        btn_start="퀴즈 시작",
        question_progress="{current} / {total} 문제",
        score_label="점수",
        correct_label="정답입니다!",
        incorrect_label="오답입니다.",
        explain_label="설명",
        btn_next="다음 문제",
        btn_change_lang="다른 언어 선택",
        finish_title="퀴즈 완료!",
        finish_summary="{total}문제 중 {score}문제를 맞췄습니다.",
        btn_retry="다시 풀기",
        usage_h2="사용 방법",
        usage_items=[
            "아래에서 프로그래밍 언어 하나를 선택하세요.",
            "객관식 문제를 풀면 정답 여부와 짧은 설명을 바로 확인할 수 있습니다.",
            "마지막 문제를 풀면 최종 점수가 표시되며, 다시 풀거나 다른 언어를 선택할 수 있습니다.",
        ],
        tips_h2="관련 팁",
        tips_items=[
            "퀴즈를 시작할 때마다 문제와 순서가 무작위로 섞여 다시 풀어도 새롭게 느껴집니다.",
            "이 퀴즈는 고급 기능이나 모범 사례보다는 기본 문법에 초점을 맞춥니다.",
            "모든 처리는 브라우저 안에서만 이뤄지며, 답변은 서버로 전송되지 않습니다.",
        ],
    ),
    "ja": dict(
        title="プログラミング言語 文法クイズ - 無料オンラインゲーム | Formix",
        description="JavaScript、Python、Java、Cの基本文法を扱う無料の選択式クイズ。各言語の基本文法の知識をブラウザ上でそのままテストできます。登録不要です。",
        keywords="文法クイズ, プログラミングクイズ, JavaScriptクイズ, Pythonクイズ, Javaクイズ, C言語クイズ, コーディングクイズゲーム, 開発者クイズ",
        og_title="プログラミング言語 文法クイズ | Formix",
        og_description="JavaScript、Python、Java、Cの基本文法の知識をテストする無料の選択式クイズです。",
        jsonld_name="プログラミング言語 文法クイズ",
        jsonld_description="JavaScript、Python、Java、Cの基本文法の知識をテストする無料オンライン選択式クイズゲーム。すべての処理はブラウザ内で行われます。",
        h1="コーディング文法クイズ",
        lead="プログラミング言語を選んで、基本文法に関する短い選択式の問題に挑戦しましょう。軽いウォーミングアップや知識の確認にぴったりです。",
        lang_select_label="言語を選択してください",
        btn_start="クイズを始める",
        question_progress="問題 {current} / {total}",
        score_label="得点",
        correct_label="正解です!",
        incorrect_label="不正解です。",
        explain_label="解説",
        btn_next="次の問題",
        btn_change_lang="別の言語を選ぶ",
        finish_title="クイズ終了!",
        finish_summary="{total}問中{score}問正解しました。",
        btn_retry="もう一度挑戦",
        usage_h2="使い方",
        usage_items=[
            "下から好きなプログラミング言語を選んでください。",
            "選択式の問題に答えると、正解かどうかと簡単な解説がすぐに表示されます。",
            "最後の問題が終わると最終得点が表示され、もう一度挑戦するか別の言語を選べます。",
        ],
        tips_h2="関連のヒント",
        tips_items=[
            "クイズを始めるたびに問題と順番がシャッフルされるので、何度でも新鮮に楽しめます。",
            "このクイズは高度な機能やベストプラクティスより、基本文法に焦点を当てています。",
            "すべての処理はブラウザ内で行われ、回答はサーバーに送信されません。",
        ],
    ),
    "zh": dict(
        title="编程语言语法测验 - 免费在线游戏 | Formix",
        description="涵盖 JavaScript、Python、Java 和 C 的免费选择题语法测验。直接在浏览器中测试你对各语言基础语法的掌握程度，无需注册。",
        keywords="语法测验, 编程测验, JavaScript 测验, Python 测验, Java 测验, C语言测验, 编程小游戏, 开发者测验",
        og_title="编程语言语法测验 | Formix",
        og_description="一个免费的选择题测验，测试你对 JavaScript、Python、Java 和 C 基础语法的掌握程度。",
        jsonld_name="编程语言语法测验",
        jsonld_description="测试 JavaScript、Python、Java 和 C 基础语法知识的免费在线选择题游戏，所有处理均在浏览器中进行。",
        h1="编程语法测验",
        lead="选择一种编程语言，回答关于其基础语法的简短选择题。适合用来热身或检验自己还记得多少。",
        lang_select_label="请选择一种语言",
        btn_start="开始测验",
        question_progress="第 {current} / {total} 题",
        score_label="得分",
        correct_label="回答正确！",
        incorrect_label="回答错误。",
        explain_label="解析",
        btn_next="下一题",
        btn_change_lang="选择其他语言",
        finish_title="测验完成！",
        finish_summary="你答对了 {total} 题中的 {score} 题。",
        btn_retry="再测一次",
        usage_h2="使用方法",
        usage_items=[
            "从下面选择一种编程语言。",
            "回答每道选择题后，会立即显示对错以及简短解析。",
            "答完最后一题后会显示最终得分，你可以重新测验或选择其他语言。",
        ],
        tips_h2="相关提示",
        tips_items=[
            "每次开始测验时，题目和顺序都会被随机打乱，重新测验也不会感到重复。",
            "本测验侧重基础语法，而非高级特性或最佳实践。",
            "所有处理均在浏览器本地完成，你的答案不会发送到服务器。",
        ],
    ),
    "es": dict(
        title="Quiz de Sintaxis de Programación - Juego Gratuito en Línea | Formix",
        description="Un quiz de opción múltiple gratuito sobre JavaScript, Python, Java y C. Pon a prueba tus conocimientos de sintaxis básica en cada lenguaje directamente en tu navegador, sin registro.",
        keywords="quiz de sintaxis, quiz de programación, quiz de javascript, quiz de python, quiz de java, quiz de c, mini juego de programación, quiz para desarrolladores",
        og_title="Quiz de Sintaxis de Programación | Formix",
        og_description="Un quiz de opción múltiple gratuito que pone a prueba tu conocimiento de la sintaxis básica de JavaScript, Python, Java y C.",
        jsonld_name="Quiz de Sintaxis de Programación",
        jsonld_description="Un juego de opción múltiple en línea gratuito que pone a prueba el conocimiento de sintaxis básica de JavaScript, Python, Java y C; todo el procesamiento ocurre en el navegador.",
        h1="Quiz de sintaxis de código",
        lead="Elige un lenguaje de programación y responde preguntas cortas de opción múltiple sobre su sintaxis básica. Ideal para calentar o comprobar cuánto recuerdas.",
        lang_select_label="Elige un lenguaje",
        btn_start="Comenzar quiz",
        question_progress="Pregunta {current} de {total}",
        score_label="Puntuación",
        correct_label="¡Correcto!",
        incorrect_label="Incorrecto.",
        explain_label="Explicación",
        btn_next="Siguiente pregunta",
        btn_change_lang="Elegir otro lenguaje",
        finish_title="¡Quiz completado!",
        finish_summary="Respondiste correctamente {score} de {total} preguntas.",
        btn_retry="Intentar de nuevo",
        usage_h2="Cómo usar esta herramienta",
        usage_items=[
            "Elige un lenguaje de programación abajo.",
            "Después de responder cada pregunta de opción múltiple, verás inmediatamente si es correcta o no, junto con una breve explicación.",
            "Después de la última pregunta, se muestra tu puntuación final y puedes volver a intentarlo o elegir otro lenguaje.",
        ],
        tips_h2="Consejos relacionados",
        tips_items=[
            "Las preguntas y su orden se mezclan cada vez que empiezas el quiz, así que repetirlo no se sentirá repetitivo.",
            "Este quiz se enfoca en sintaxis básica, no en características avanzadas ni mejores prácticas.",
            "Todo el procesamiento ocurre localmente en tu navegador — tus respuestas nunca se envían a un servidor.",
        ],
    ),
    "vi": dict(
        title="Đố Vui Cú Pháp Lập Trình - Trò Chơi Trực Tuyến Miễn Phí | Formix",
        description="Một bài trắc nghiệm miễn phí về JavaScript, Python, Java và C. Kiểm tra kiến thức cú pháp cơ bản của bạn trong từng ngôn ngữ ngay trong trình duyệt, không cần đăng ký.",
        keywords="đố vui cú pháp, đố vui lập trình, đố vui javascript, đố vui python, đố vui java, đố vui c, trò chơi nhỏ lập trình, đố vui cho developer",
        og_title="Đố Vui Cú Pháp Lập Trình | Formix",
        og_description="Một bài trắc nghiệm miễn phí kiểm tra kiến thức của bạn về cú pháp cơ bản của JavaScript, Python, Java và C.",
        jsonld_name="Đố Vui Cú Pháp Lập Trình",
        jsonld_description="Trò chơi trắc nghiệm trực tuyến miễn phí kiểm tra kiến thức cú pháp cơ bản của JavaScript, Python, Java và C; mọi xử lý diễn ra trong trình duyệt.",
        h1="Đố vui cú pháp lập trình",
        lead="Chọn một ngôn ngữ lập trình và trả lời các câu hỏi trắc nghiệm ngắn về cú pháp cơ bản của nó. Thích hợp để làm nóng hoặc kiểm tra xem bạn còn nhớ được bao nhiêu.",
        lang_select_label="Hãy chọn một ngôn ngữ",
        btn_start="Bắt đầu đố vui",
        question_progress="Câu {current} / {total}",
        score_label="Điểm",
        correct_label="Chính xác!",
        incorrect_label="Chưa đúng.",
        explain_label="Giải thích",
        btn_next="Câu tiếp theo",
        btn_change_lang="Chọn ngôn ngữ khác",
        finish_title="Hoàn thành đố vui!",
        finish_summary="Bạn đã trả lời đúng {score} trong tổng số {total} câu.",
        btn_retry="Thử lại",
        usage_h2="Cách sử dụng công cụ này",
        usage_items=[
            "Chọn một ngôn ngữ lập trình bên dưới.",
            "Sau khi trả lời mỗi câu hỏi trắc nghiệm, bạn sẽ ngay lập tức thấy đúng hay sai, cùng với một giải thích ngắn.",
            "Sau câu hỏi cuối cùng, điểm số cuối cùng của bạn sẽ hiện ra và bạn có thể làm lại hoặc chọn ngôn ngữ khác.",
        ],
        tips_h2="Mẹo liên quan",
        tips_items=[
            "Các câu hỏi và thứ tự của chúng được xáo trộn mỗi khi bạn bắt đầu đố vui, nên làm lại sẽ không cảm thấy lặp lại.",
            "Bài đố vui này tập trung vào cú pháp cơ bản, không phải các tính năng nâng cao hay thực hành tốt nhất.",
            "Mọi xử lý diễn ra cục bộ trong trình duyệt của bạn — câu trả lời của bạn không bao giờ được gửi lên máy chủ.",
        ],
    ),
    "pt": dict(
        title="Quiz de Sintaxe de Programação - Jogo Gratuito Online | Formix",
        description="Um quiz de múltipla escolha gratuito sobre JavaScript, Python, Java e C. Teste seu conhecimento de sintaxe básica em cada linguagem diretamente no seu navegador, sem cadastro.",
        keywords="quiz de sintaxe, quiz de programação, quiz de javascript, quiz de python, quiz de java, quiz de c, minijogo de programação, quiz para desenvolvedores",
        og_title="Quiz de Sintaxe de Programação | Formix",
        og_description="Um quiz de múltipla escolha gratuito que testa seu conhecimento da sintaxe básica de JavaScript, Python, Java e C.",
        jsonld_name="Quiz de Sintaxe de Programação",
        jsonld_description="Um jogo de múltipla escolha online gratuito que testa o conhecimento de sintaxe básica de JavaScript, Python, Java e C; todo o processamento ocorre no navegador.",
        h1="Quiz de sintaxe de código",
        lead="Escolha uma linguagem de programação e responda perguntas curtas de múltipla escolha sobre sua sintaxe básica. Ótimo para aquecer ou verificar o quanto você ainda lembra.",
        lang_select_label="Escolha uma linguagem",
        btn_start="Começar quiz",
        question_progress="Pergunta {current} de {total}",
        score_label="Pontuação",
        correct_label="Correto!",
        incorrect_label="Incorreto.",
        explain_label="Explicação",
        btn_next="Próxima pergunta",
        btn_change_lang="Escolher outra linguagem",
        finish_title="Quiz concluído!",
        finish_summary="Você respondeu corretamente {score} de {total} perguntas.",
        btn_retry="Tentar novamente",
        usage_h2="Como usar esta ferramenta",
        usage_items=[
            "Escolha uma linguagem de programação abaixo.",
            "Depois de responder cada pergunta de múltipla escolha, você verá imediatamente se está certo ou errado, junto com uma breve explicação.",
            "Após a última pergunta, sua pontuação final é exibida e você pode tentar de novo ou escolher outra linguagem.",
        ],
        tips_h2="Dicas relacionadas",
        tips_items=[
            "As perguntas e sua ordem são embaralhadas cada vez que você inicia o quiz, então refazer não vai parecer repetitivo.",
            "Este quiz foca na sintaxe básica, não em recursos avançados ou melhores práticas.",
            "Todo o processamento ocorre localmente no seu navegador — suas respostas nunca são enviadas a um servidor.",
        ],
    ),
    "id": dict(
        title="Kuis Sintaks Koding - Permainan Online Gratis | Formix",
        description="Kuis pilihan ganda gratis tentang JavaScript, Python, Java, dan C. Uji pengetahuan sintaks dasar Anda di setiap bahasa langsung di browser, tanpa pendaftaran.",
        keywords="kuis sintaks, kuis koding, kuis javascript, kuis python, kuis java, kuis c, permainan kecil koding, kuis untuk developer",
        og_title="Kuis Sintaks Koding | Formix",
        og_description="Kuis pilihan ganda gratis yang menguji pengetahuan Anda tentang sintaks dasar JavaScript, Python, Java, dan C.",
        jsonld_name="Kuis Sintaks Koding",
        jsonld_description="Permainan pilihan ganda online gratis yang menguji pengetahuan sintaks dasar JavaScript, Python, Java, dan C; semua pemrosesan terjadi di browser.",
        h1="Kuis Sintaks Koding",
        lead="Pilih bahasa pemrograman dan jawab pertanyaan pilihan ganda singkat tentang sintaks dasarnya. Cocok untuk pemanasan atau menguji seberapa banyak yang masih Anda ingat.",
        lang_select_label="Silakan pilih bahasa",
        btn_start="Mulai kuis",
        question_progress="Pertanyaan {current} dari {total}",
        score_label="Skor",
        correct_label="Benar!",
        incorrect_label="Kurang tepat.",
        explain_label="Penjelasan",
        btn_next="Pertanyaan berikutnya",
        btn_change_lang="Pilih bahasa lain",
        finish_title="Kuis selesai!",
        finish_summary="Anda menjawab benar {score} dari {total} pertanyaan.",
        btn_retry="Coba lagi",
        usage_h2="Cara menggunakan alat ini",
        usage_items=[
            "Pilih bahasa pemrograman di bawah ini.",
            "Setelah menjawab setiap pertanyaan pilihan ganda, Anda akan langsung melihat apakah benar atau salah, beserta penjelasan singkat.",
            "Setelah pertanyaan terakhir, skor akhir Anda ditampilkan dan Anda dapat mencoba lagi atau memilih bahasa lain.",
        ],
        tips_h2="Tips terkait",
        tips_items=[
            "Pertanyaan dan urutannya diacak setiap kali Anda memulai kuis, sehingga mengulanginya tidak akan terasa membosankan.",
            "Kuis ini berfokus pada sintaks dasar, bukan fitur lanjutan atau praktik terbaik.",
            "Semua pemrosesan terjadi secara lokal di browser Anda — jawaban Anda tidak pernah dikirim ke server.",
        ],
    ),
    "de": dict(
        title="Coding-Syntax-Quiz - Kostenloses Online-Spiel | Formix",
        description="Ein kostenloses Multiple-Choice-Quiz zu JavaScript, Python, Java und C. Testen Sie Ihr Wissen über die Grundsyntax jeder Sprache direkt in Ihrem Browser, ohne Registrierung.",
        keywords="syntax quiz, coding quiz, javascript quiz, python quiz, java quiz, c quiz, coding minispiel, entwickler quiz",
        og_title="Coding-Syntax-Quiz | Formix",
        og_description="Ein kostenloses Multiple-Choice-Quiz, das Ihr Wissen über die Grundsyntax von JavaScript, Python, Java und C testet.",
        jsonld_name="Coding-Syntax-Quiz",
        jsonld_description="Ein kostenloses Online-Multiple-Choice-Spiel, das Grundsyntax-Wissen zu JavaScript, Python, Java und C testet; die gesamte Verarbeitung erfolgt im Browser.",
        h1="Coding-Syntax-Quiz",
        lead="Wählen Sie eine Programmiersprache und beantworten Sie kurze Multiple-Choice-Fragen zu ihrer Grundsyntax. Gut zum Aufwärmen oder um zu prüfen, wie viel Sie noch wissen.",
        lang_select_label="Bitte wählen Sie eine Sprache",
        btn_start="Quiz starten",
        question_progress="Frage {current} von {total}",
        score_label="Punktzahl",
        correct_label="Richtig!",
        incorrect_label="Nicht ganz.",
        explain_label="Erklärung",
        btn_next="Nächste Frage",
        btn_change_lang="Andere Sprache wählen",
        finish_title="Quiz abgeschlossen!",
        finish_summary="Sie haben {score} von {total} Fragen richtig beantwortet.",
        btn_retry="Erneut versuchen",
        usage_h2="So verwenden Sie dieses Tool",
        usage_items=[
            "Wählen Sie unten eine Programmiersprache.",
            "Nachdem Sie jede Multiple-Choice-Frage beantwortet haben, sehen Sie sofort, ob sie richtig oder falsch war, zusammen mit einer kurzen Erklärung.",
            "Nach der letzten Frage wird Ihre Endpunktzahl angezeigt, und Sie können es erneut versuchen oder eine andere Sprache wählen.",
        ],
        tips_h2="Verwandte Tipps",
        tips_items=[
            "Fragen und ihre Reihenfolge werden jedes Mal, wenn Sie das Quiz starten, neu gemischt, sodass es sich beim Wiederholen nicht repetitiv anfühlt.",
            "Dieses Quiz konzentriert sich auf die Grundsyntax, nicht auf fortgeschrittene Funktionen oder Best Practices.",
            "Die gesamte Verarbeitung erfolgt lokal in Ihrem Browser — Ihre Antworten werden nie an einen Server gesendet.",
        ],
    ),
}

# ---------------------------------------------------------------------------
# 프로그래밍 언어별 문법 퀴즈 문제 은행.
# choices는 대부분 코드/고유 구문이라 언어(사이트 locale)에 무관하게 공유하지만,
# 설명식 선택지가 필요한 문항은 choices 항목 자체를 {en,ko,ja,zh} dict로 대신 넣을 수 있다
# (build_quiz_payload()가 문자열/딕셔너리 어느 쪽이든 처리한다).
# ---------------------------------------------------------------------------
QUIZ_LANGS = [("javascript", "JavaScript"), ("python", "Python"), ("java", "Java"), ("c", "C")]

QUIZ_BANK = {
    "javascript": [
        {
            "stem": {"en": "Which keyword declares a constant (a variable that cannot be reassigned) in JavaScript?",
                     "ko": "JavaScript에서 재할당할 수 없는 상수를 선언할 때 쓰는 키워드는?",
                     "ja": "JavaScriptで再代入できない定数を宣言するキーワードは?",
                     "zh": "在 JavaScript 中，用于声明不可重新赋值的常量的关键字是什么？",
                     "es": "¿Qué palabra clave declara una constante (una variable que no se puede reasignar) en JavaScript?",
                     "vi": "Từ khóa nào dùng để khai báo một hằng số (biến không thể gán lại) trong JavaScript?",
                     "pt": "Qual palavra-chave declara uma constante (uma variável que não pode ser reatribuída) em JavaScript?",
                     "id": "Kata kunci mana yang mendeklarasikan konstanta (variabel yang tidak dapat diberi nilai ulang) di JavaScript?",
                     "de": "Welches Schlüsselwort deklariert eine Konstante (eine Variable, die nicht neu zugewiesen werden kann) in JavaScript?"},
            "choices": ["var", "let", "const", "static"], "correct": 2,
            "explain": {"en": "\"const\" creates a binding that cannot be reassigned after it is set.",
                        "ko": "\"const\"로 선언한 변수는 한 번 값이 정해지면 다시 할당할 수 없습니다.",
                        "ja": "\"const\"で宣言した変数は、値を設定した後に再代入できません。",
                        "zh": "用 \"const\" 声明的变量一旦赋值后就不能再重新赋值。",
                        "es": "\"const\" crea un enlace que no se puede reasignar después de establecerse.",
                        "vi": "\"const\" tạo ra một ràng buộc không thể gán lại sau khi đã được thiết lập.",
                        "pt": "\"const\" cria uma vinculação que não pode ser reatribuída depois de definida.",
                        "id": "\"const\" membuat binding yang tidak dapat diberi nilai ulang setelah ditetapkan.",
                        "de": "\"const\" erzeugt eine Bindung, die nach der Zuweisung nicht mehr neu zugewiesen werden kann."},
        },
        {
            "stem": {"en": "Which symbol is used to start a multi-line comment in JavaScript?",
                     "ko": "JavaScript에서 여러 줄 주석을 시작할 때 사용하는 기호는?",
                     "ja": "JavaScriptで複数行コメントを開始する記号は?",
                     "zh": "在 JavaScript 中，用于开始多行注释的符号是什么？",
                     "es": "¿Qué símbolo se usa para iniciar un comentario de varias líneas en JavaScript?",
                     "vi": "Ký hiệu nào dùng để bắt đầu một chú thích nhiều dòng trong JavaScript?",
                     "pt": "Qual símbolo é usado para iniciar um comentário de várias linhas em JavaScript?",
                     "id": "Simbol mana yang digunakan untuk memulai komentar multi-baris di JavaScript?",
                     "de": "Welches Symbol wird verwendet, um einen mehrzeiligen Kommentar in JavaScript zu beginnen?"},
            "choices": ["//", "/*", "#", "<!--"], "correct": 1,
            "explain": {"en": "Multi-line comments start with /* and end with */. // is for single-line comments.",
                        "ko": "여러 줄 주석은 /*로 시작해 */로 끝납니다. //는 한 줄 주석에 사용합니다.",
                        "ja": "複数行コメントは/*で始まり*/で終わります。//は単一行コメント用です。",
                        "zh": "多行注释以 /* 开始，以 */ 结束。// 用于单行注释。",
                        "es": "Los comentarios de varias líneas comienzan con /* y terminan con */. // se usa para comentarios de una sola línea.",
                        "vi": "Chú thích nhiều dòng bắt đầu bằng /* và kết thúc bằng */. // dùng cho chú thích một dòng.",
                        "pt": "Comentários de várias linhas começam com /* e terminam com */. // é usado para comentários de uma linha.",
                        "id": "Komentar multi-baris dimulai dengan /* dan diakhiri dengan */. // digunakan untuk komentar satu baris.",
                        "de": "Mehrzeilige Kommentare beginnen mit /* und enden mit */. // steht für einzeilige Kommentare."},
        },
        {
            "stem": {"en": "Which operator checks both value and type equality in JavaScript?",
                     "ko": "JavaScript에서 값과 타입을 모두 비교하는 연산자는?",
                     "ja": "JavaScriptで値と型の両方を比較する演算子は?",
                     "zh": "在 JavaScript 中，同时比较值和类型的运算符是什么？",
                     "es": "¿Qué operador comprueba tanto la igualdad de valor como de tipo en JavaScript?",
                     "vi": "Toán tử nào kiểm tra cả giá trị và kiểu dữ liệu bằng nhau trong JavaScript?",
                     "pt": "Qual operador verifica tanto a igualdade de valor quanto de tipo em JavaScript?",
                     "id": "Operator mana yang memeriksa kesetaraan nilai dan tipe sekaligus di JavaScript?",
                     "de": "Welcher Operator prüft sowohl Wert- als auch Typgleichheit in JavaScript?"},
            "choices": ["=", "==", "===", "!=="], "correct": 2,
            "explain": {"en": "\"===\" (strict equality) compares value and type without type coercion, unlike \"==\".",
                        "ko": "\"===\"(일치 연산자)는 \"==\"와 달리 타입 변환 없이 값과 타입을 모두 비교합니다.",
                        "ja": "\"===\"(厳密等価)は\"==\"と異なり、型変換なしで値と型を両方比較します。",
                        "zh": "\"===\"（严格相等）与 \"==\" 不同，不进行类型转换，同时比较值和类型。",
                        "es": "\"===\" (igualdad estricta) compara valor y tipo sin conversión de tipo, a diferencia de \"==\".",
                        "vi": "\"===\" (so sánh nghiêm ngặt) so sánh cả giá trị và kiểu mà không ép kiểu, khác với \"==\".",
                        "pt": "\"===\" (igualdade estrita) compara valor e tipo sem conversão de tipo, diferente de \"==\".",
                        "id": "\"===\" (kesetaraan ketat) membandingkan nilai dan tipe tanpa konversi tipe, berbeda dengan \"==\".",
                        "de": "\"===\" (strikte Gleichheit) vergleicht Wert und Typ ohne Typumwandlung, anders als \"==\"."},
        },
        {
            "stem": {"en": "Which built-in function converts the string \"42\" into the number 42?",
                     "ko": "문자열 \"42\"를 숫자 42로 변환하는 내장 함수는?",
                     "ja": "文字列\"42\"を数値42に変換する組み込み関数は?",
                     "zh": "将字符串 \"42\" 转换为数字 42 的内置函数是什么？",
                     "es": "¿Qué función incorporada convierte la cadena \"42\" en el número 42?",
                     "vi": "Hàm có sẵn nào chuyển chuỗi \"42\" thành số 42?",
                     "pt": "Qual função embutida converte a string \"42\" no número 42?",
                     "id": "Fungsi bawaan mana yang mengubah string \"42\" menjadi angka 42?",
                     "de": "Welche eingebaute Funktion wandelt die Zeichenkette \"42\" in die Zahl 42 um?"},
            "choices": ["parseInt(str)", "Integer.parse(str)", "str.toInt()", "int(str)"], "correct": 0,
            "explain": {"en": "parseInt() parses a string and returns an integer; the other forms don't exist in JavaScript.",
                        "ko": "parseInt()는 문자열을 분석해 정수를 반환합니다. 나머지는 JavaScript에 존재하지 않는 형태입니다.",
                        "ja": "parseInt()は文字列を解析して整数を返します。他の形式はJavaScriptには存在しません。",
                        "zh": "parseInt() 会解析字符串并返回整数，其他写法在 JavaScript 中并不存在。",
                        "es": "parseInt() analiza una cadena y devuelve un entero; las otras formas no existen en JavaScript.",
                        "vi": "parseInt() phân tích một chuỗi và trả về một số nguyên; các dạng khác không tồn tại trong JavaScript.",
                        "pt": "parseInt() analisa uma string e retorna um inteiro; as outras formas não existem em JavaScript.",
                        "id": "parseInt() mem-parsing string dan mengembalikan bilangan bulat; bentuk lainnya tidak ada di JavaScript.",
                        "de": "parseInt() wertet eine Zeichenkette aus und gibt eine Ganzzahl zurück; die anderen Formen existieren in JavaScript nicht."},
        },
        {
            "stem": {"en": "Which syntax correctly embeds a variable named \"name\" inside a string using a template literal?",
                     "ko": "템플릿 리터럴을 이용해 변수 name을 문자열에 올바르게 삽입하는 문법은?",
                     "ja": "テンプレートリテラルを使って変数nameを文字列に正しく埋め込む構文は?",
                     "zh": "使用模板字符串正确地将变量 name 插入字符串中的写法是什么？",
                     "es": "¿Qué sintaxis incorpora correctamente una variable llamada \"name\" dentro de una cadena usando un literal de plantilla?",
                     "vi": "Cú pháp nào nhúng đúng biến có tên \"name\" vào trong một chuỗi bằng template literal?",
                     "pt": "Qual sintaxe insere corretamente uma variável chamada \"name\" dentro de uma string usando um literal de template?",
                     "id": "Sintaks mana yang dengan benar menyisipkan variabel bernama \"name\" ke dalam string menggunakan template literal?",
                     "de": "Welche Syntax bettet eine Variable namens \"name\" korrekt mit einem Template-Literal in eine Zeichenkette ein?"},
            "choices": ["`Hello, ${name}`", "'Hello, ${name}'", "\"Hello, \" + ${name}", "`Hello, {name}`"], "correct": 0,
            "explain": {"en": "Template literals use backticks with ${expression} to embed values; regular quotes don't interpolate.",
                        "ko": "템플릿 리터럴은 백틱(`)과 ${표현식}을 사용해 값을 삽입합니다. 일반 따옴표는 보간되지 않습니다.",
                        "ja": "テンプレートリテラルはバックティックと${式}を使って値を埋め込みます。通常の引用符では補間されません。",
                        "zh": "模板字符串使用反引号和 ${表达式} 来插入值，普通引号不会进行插值。",
                        "es": "Los literales de plantilla usan comillas invertidas con ${expresión} para incorporar valores; las comillas normales no interpolan.",
                        "vi": "Template literal dùng dấu backtick với ${biểu thức} để nhúng giá trị; dấu nháy thông thường không nội suy.",
                        "pt": "Literais de template usam crases com ${expressão} para incorporar valores; aspas normais não fazem interpolação.",
                        "id": "Template literal menggunakan tanda backtick dengan ${ekspresi} untuk menyisipkan nilai; tanda kutip biasa tidak melakukan interpolasi.",
                        "de": "Template-Literale verwenden Backticks mit ${Ausdruck}, um Werte einzubetten; normale Anführungszeichen interpolieren nicht."},
        },
        {
            "stem": {"en": "Which array method adds a new element to the end of an array?",
                     "ko": "배열의 맨 뒤에 새 요소를 추가하는 배열 메서드는?",
                     "ja": "配列の末尾に新しい要素を追加する配列メソッドは?",
                     "zh": "在数组末尾添加新元素的数组方法是什么？",
                     "es": "¿Qué método de array agrega un nuevo elemento al final de un array?",
                     "vi": "Phương thức mảng nào thêm một phần tử mới vào cuối mảng?",
                     "pt": "Qual método de array adiciona um novo elemento ao final de um array?",
                     "id": "Metode array mana yang menambahkan elemen baru ke akhir array?",
                     "de": "Welche Array-Methode fügt ein neues Element am Ende eines Arrays hinzu?"},
            "choices": ["push()", "pop()", "shift()", "unshift()"], "correct": 0,
            "explain": {"en": "push() appends one or more elements to the end of an array and returns the new length.",
                        "ko": "push()는 배열 끝에 요소를 추가하고 새로운 배열의 길이를 반환합니다.",
                        "ja": "push()は配列の末尾に要素を追加し、新しい配列の長さを返します。",
                        "zh": "push() 会在数组末尾添加元素，并返回新数组的长度。",
                        "es": "push() agrega uno o más elementos al final de un array y devuelve la nueva longitud.",
                        "vi": "push() thêm một hoặc nhiều phần tử vào cuối mảng và trả về độ dài mới.",
                        "pt": "push() adiciona um ou mais elementos ao final de um array e retorna o novo tamanho.",
                        "id": "push() menambahkan satu atau lebih elemen ke akhir array dan mengembalikan panjang baru.",
                        "de": "push() fügt ein oder mehrere Elemente am Ende eines Arrays hinzu und gibt die neue Länge zurück."},
        },
    ],
    "python": [
        {
            "stem": {"en": "Which symbol starts a single-line comment in Python?",
                     "ko": "Python에서 한 줄 주석을 시작하는 기호는?",
                     "ja": "Pythonで単一行コメントを開始する記号は?",
                     "zh": "在 Python 中，用于开始单行注释的符号是什么？",
                     "es": "¿Qué símbolo inicia un comentario de una sola línea en Python?",
                     "vi": "Ký hiệu nào bắt đầu một chú thích một dòng trong Python?",
                     "pt": "Qual símbolo inicia um comentário de uma linha em Python?",
                     "id": "Simbol mana yang memulai komentar satu baris di Python?",
                     "de": "Welches Symbol beginnt einen einzeiligen Kommentar in Python?"},
            "choices": ["#", "//", "/* */", "--"], "correct": 0,
            "explain": {"en": "Python uses # for single-line comments; it has no dedicated multi-line comment syntax.",
                        "ko": "Python은 한 줄 주석에 #을 사용하며, 전용 여러 줄 주석 문법은 따로 없습니다.",
                        "ja": "Pythonは単一行コメントに#を使い、専用の複数行コメント構文はありません。",
                        "zh": "Python 使用 # 表示单行注释，没有专门的多行注释语法。",
                        "es": "Python usa # para comentarios de una sola línea; no tiene una sintaxis dedicada para comentarios de varias líneas.",
                        "vi": "Python dùng # cho chú thích một dòng; nó không có cú pháp riêng cho chú thích nhiều dòng.",
                        "pt": "Python usa # para comentários de uma linha; não possui uma sintaxe dedicada para comentários de várias linhas.",
                        "id": "Python menggunakan # untuk komentar satu baris; tidak ada sintaks khusus untuk komentar multi-baris.",
                        "de": "Python verwendet # für einzeilige Kommentare; es gibt keine eigene Syntax für mehrzeilige Kommentare."},
        },
        {
            "stem": {"en": "Which keyword is used to define a function in Python?",
                     "ko": "Python에서 함수를 정의할 때 사용하는 키워드는?",
                     "ja": "Pythonで関数を定義するときに使うキーワードは?",
                     "zh": "在 Python 中，用于定义函数的关键字是什么？",
                     "es": "¿Qué palabra clave se usa para definir una función en Python?",
                     "vi": "Từ khóa nào dùng để định nghĩa một hàm trong Python?",
                     "pt": "Qual palavra-chave é usada para definir uma função em Python?",
                     "id": "Kata kunci mana yang digunakan untuk mendefinisikan fungsi di Python?",
                     "de": "Welches Schlüsselwort wird verwendet, um eine Funktion in Python zu definieren?"},
            "choices": ["function", "def", "func", "void"], "correct": 1,
            "explain": {"en": "Functions are defined with \"def name():\" followed by an indented block.",
                        "ko": "함수는 \"def 이름():\" 뒤에 들여쓰기된 블록으로 정의합니다.",
                        "ja": "関数は\"def 名前():\"の後にインデントされたブロックで定義します。",
                        "zh": "函数使用 \"def 名称():\" 加缩进代码块来定义。",
                        "es": "Las funciones se definen con \"def nombre():\" seguido de un bloque con sangría.",
                        "vi": "Hàm được định nghĩa bằng \"def tên():\" theo sau là một khối lệnh thụt lề.",
                        "pt": "Funções são definidas com \"def nome():\" seguido de um bloco indentado.",
                        "id": "Fungsi didefinisikan dengan \"def nama():\" diikuti oleh blok yang diindentasi.",
                        "de": "Funktionen werden mit \"def Name():\" gefolgt von einem eingerückten Block definiert."},
        },
        {
            "stem": {"en": "Which keyword is used for an \"else if\" branch in Python?",
                     "ko": "Python에서 \"else if\"에 해당하는 키워드는?",
                     "ja": "Pythonで\"else if\"に相当するキーワードは?",
                     "zh": "在 Python 中，相当于 \"else if\" 的关键字是什么？",
                     "es": "¿Qué palabra clave se usa para una rama \"else if\" en Python?",
                     "vi": "Từ khóa nào dùng cho nhánh \"else if\" trong Python?",
                     "pt": "Qual palavra-chave é usada para um ramo \"else if\" em Python?",
                     "id": "Kata kunci mana yang digunakan untuk cabang \"else if\" di Python?",
                     "de": "Welches Schlüsselwort wird für einen \"else if\"-Zweig in Python verwendet?"},
            "choices": ["elseif", "elif", "else if", "elsif"], "correct": 1,
            "explain": {"en": "Python uses \"elif\", a contraction of \"else if\", not \"elseif\" or \"else if\".",
                        "ko": "Python은 \"else if\"의 축약형인 \"elif\"를 사용합니다. \"elseif\"나 \"else if\"는 쓰지 않습니다.",
                        "ja": "Pythonは\"else if\"の短縮形である\"elif\"を使います。\"elseif\"や\"else if\"は使いません。",
                        "zh": "Python 使用 \"else if\" 的缩写 \"elif\"，而不是 \"elseif\" 或 \"else if\"。",
                        "es": "Python usa \"elif\", una contracción de \"else if\", no \"elseif\" ni \"else if\".",
                        "vi": "Python dùng \"elif\", dạng rút gọn của \"else if\", không dùng \"elseif\" hay \"else if\".",
                        "pt": "Python usa \"elif\", uma contração de \"else if\", não \"elseif\" ou \"else if\".",
                        "id": "Python menggunakan \"elif\", kontraksi dari \"else if\", bukan \"elseif\" atau \"else if\".",
                        "de": "Python verwendet \"elif\", eine Kurzform von \"else if\", nicht \"elseif\" oder \"else if\"."},
        },
        {
            "stem": {"en": "Which expression creates a list of the squares of 0 through 9?",
                     "ko": "0부터 9까지의 제곱으로 이루어진 리스트를 만드는 표현식은?",
                     "ja": "0から9までの2乗からなるリストを作る式は?",
                     "zh": "创建一个包含 0 到 9 的平方的列表的表达式是什么？",
                     "es": "¿Qué expresión crea una lista con los cuadrados de 0 a 9?",
                     "vi": "Biểu thức nào tạo ra một danh sách các bình phương từ 0 đến 9?",
                     "pt": "Qual expressão cria uma lista com os quadrados de 0 a 9?",
                     "id": "Ekspresi mana yang membuat daftar kuadrat dari 0 hingga 9?",
                     "de": "Welcher Ausdruck erzeugt eine Liste der Quadrate von 0 bis 9?"},
            "choices": ["[x**2 for x in range(10)]", "(x**2 for x in range(10))", "{x**2 for x in range(10)}", "x**2 for x in range(10)"], "correct": 0,
            "explain": {"en": "Square brackets make a list comprehension; parentheses make a generator, and braces make a set.",
                        "ko": "대괄호는 리스트 컴프리헨션을, 소괄호는 제너레이터를, 중괄호는 집합(set)을 만듭니다.",
                        "ja": "角括弧はリスト内包表記、丸括弧はジェネレータ、波括弧は集合(set)を作ります。",
                        "zh": "方括号用于创建列表推导式，圆括号创建生成器，花括号创建集合（set）。",
                        "es": "Los corchetes crean una comprensión de lista; los paréntesis crean un generador y las llaves crean un conjunto.",
                        "vi": "Dấu ngoặc vuông tạo list comprehension; dấu ngoặc tròn tạo generator, và dấu ngoặc nhọn tạo set.",
                        "pt": "Colchetes criam uma list comprehension; parênteses criam um gerador e chaves criam um conjunto (set).",
                        "id": "Tanda kurung siku membuat list comprehension; tanda kurung membuat generator, dan kurung kurawal membuat set.",
                        "de": "Eckige Klammern erzeugen eine List Comprehension; runde Klammern einen Generator und geschweifte Klammern ein Set."},
        },
        {
            "stem": {"en": "Which built-in function returns the number of items in a list?",
                     "ko": "리스트의 항목 개수를 반환하는 내장 함수는?",
                     "ja": "リストの要素数を返す組み込み関数は?",
                     "zh": "返回列表中元素个数的内置函数是什么？",
                     "es": "¿Qué función incorporada devuelve el número de elementos de una lista?",
                     "vi": "Hàm có sẵn nào trả về số lượng phần tử trong một danh sách?",
                     "pt": "Qual função embutida retorna o número de itens de uma lista?",
                     "id": "Fungsi bawaan mana yang mengembalikan jumlah item dalam sebuah list?",
                     "de": "Welche eingebaute Funktion gibt die Anzahl der Elemente einer Liste zurück?"},
            "choices": ["len(list)", "size(list)", "list.length()", "count(list)"], "correct": 0,
            "explain": {"en": "len() works on lists, strings, tuples, and other sequences to return their length.",
                        "ko": "len()은 리스트, 문자열, 튜플 등 시퀀스의 길이를 반환합니다.",
                        "ja": "len()はリスト、文字列、タプルなどのシーケンスの長さを返します。",
                        "zh": "len() 可用于列表、字符串、元组等序列，返回其长度。",
                        "es": "len() funciona con listas, cadenas, tuplas y otras secuencias para devolver su longitud.",
                        "vi": "len() hoạt động trên danh sách, chuỗi, tuple và các kiểu dữ liệu dãy khác để trả về độ dài của chúng.",
                        "pt": "len() funciona com listas, strings, tuplas e outras sequências para retornar seu tamanho.",
                        "id": "len() bekerja pada list, string, tuple, dan sequence lainnya untuk mengembalikan panjangnya.",
                        "de": "len() funktioniert mit Listen, Zeichenketten, Tupeln und anderen Sequenzen und gibt deren Länge zurück."},
        },
        {
            "stem": {"en": "Which statement correctly imports the \"math\" module in Python?",
                     "ko": "Python에서 math 모듈을 올바르게 불러오는 문장은?",
                     "ja": "Pythonでmathモジュールを正しく読み込む文は?",
                     "zh": "在 Python 中正确导入 math 模块的语句是什么？",
                     "es": "¿Qué instrucción importa correctamente el módulo \"math\" en Python?",
                     "vi": "Câu lệnh nào nhập đúng module \"math\" trong Python?",
                     "pt": "Qual instrução importa corretamente o módulo \"math\" em Python?",
                     "id": "Pernyataan mana yang dengan benar mengimpor modul \"math\" di Python?",
                     "de": "Welche Anweisung importiert das Modul \"math\" in Python korrekt?"},
            "choices": ["import math", "#include <math>", "using math;", "require('math')"], "correct": 0,
            "explain": {"en": "Python modules are loaded with \"import module_name\"; the other forms belong to other languages.",
                        "ko": "Python 모듈은 \"import 모듈이름\"으로 불러옵니다. 나머지는 다른 언어의 문법입니다.",
                        "ja": "Pythonのモジュールは\"import モジュール名\"で読み込みます。他の形式は他言語の構文です。",
                        "zh": "Python 模块使用 \"import 模块名\" 导入，其他写法属于别的语言。",
                        "es": "Los módulos de Python se cargan con \"import nombre_modulo\"; las otras formas pertenecen a otros lenguajes.",
                        "vi": "Module trong Python được nạp bằng \"import tên_module\"; các dạng khác thuộc về các ngôn ngữ khác.",
                        "pt": "Os módulos do Python são carregados com \"import nome_do_modulo\"; as outras formas pertencem a outras linguagens.",
                        "id": "Modul Python dimuat dengan \"import nama_modul\"; bentuk lainnya milik bahasa lain.",
                        "de": "Python-Module werden mit \"import modulname\" geladen; die anderen Formen gehören zu anderen Sprachen."},
        },
    ],
    "java": [
        {
            "stem": {"en": "Which keyword declares a constant in Java?",
                     "ko": "Java에서 상수를 선언할 때 사용하는 키워드는?",
                     "ja": "Javaで定数を宣言するキーワードは?",
                     "zh": "在 Java 中，用于声明常量的关键字是什么？",
                     "es": "¿Qué palabra clave declara una constante en Java?",
                     "vi": "Từ khóa nào dùng để khai báo một hằng số trong Java?",
                     "pt": "Qual palavra-chave declara uma constante em Java?",
                     "id": "Kata kunci mana yang mendeklarasikan konstanta di Java?",
                     "de": "Welches Schlüsselwort deklariert eine Konstante in Java?"},
            "choices": ["const", "final", "static", "readonly"], "correct": 1,
            "explain": {"en": "\"final\" prevents a variable from being reassigned; \"const\" is reserved but unused in Java.",
                        "ko": "\"final\"은 변수를 재할당할 수 없게 만듭니다. \"const\"는 예약어이지만 Java에서 실제로 쓰이지 않습니다.",
                        "ja": "\"final\"は変数の再代入を防ぎます。\"const\"は予約語ですがJavaでは実際には使われません。",
                        "zh": "\"final\" 可以防止变量被重新赋值；\"const\" 是保留字但在 Java 中并未实际使用。",
                        "es": "\"final\" evita que una variable sea reasignada; \"const\" está reservada pero no se usa en Java.",
                        "vi": "\"final\" ngăn một biến bị gán lại; \"const\" là từ dành riêng nhưng không được dùng trong Java.",
                        "pt": "\"final\" impede que uma variável seja reatribuída; \"const\" é reservada mas não é usada em Java.",
                        "id": "\"final\" mencegah variabel diberi nilai ulang; \"const\" adalah kata cadangan tetapi tidak digunakan di Java.",
                        "de": "\"final\" verhindert, dass eine Variable neu zugewiesen wird; \"const\" ist reserviert, wird in Java aber nicht verwendet."},
        },
        {
            "stem": {"en": "What is the correct signature for the main method that starts a Java program?",
                     "ko": "Java 프로그램의 시작점이 되는 main 메서드의 올바른 선언은?",
                     "ja": "Javaプログラムの開始点となるmainメソッドの正しい宣言は?",
                     "zh": "作为 Java 程序入口的 main 方法的正确签名是什么？",
                     "es": "¿Cuál es la firma correcta del método main que inicia un programa Java?",
                     "vi": "Chữ ký đúng của phương thức main khởi động một chương trình Java là gì?",
                     "pt": "Qual é a assinatura correta do método main que inicia um programa Java?",
                     "id": "Apa tanda tangan (signature) yang benar untuk metode main yang memulai program Java?",
                     "de": "Wie lautet die korrekte Signatur der main-Methode, die ein Java-Programm startet?"},
            "choices": ["public static void main(String[] args)", "public void main(String[] args)",
                        "static void Main(String[] args)", "public static main(String[] args)"], "correct": 0,
            "explain": {"en": "The JVM looks for exactly \"public static void main(String[] args)\" as the entry point.",
                        "ko": "JVM은 정확히 \"public static void main(String[] args)\" 형태를 진입점으로 찾습니다.",
                        "ja": "JVMは正確に\"public static void main(String[] args)\"をエントリーポイントとして探します。",
                        "zh": "JVM 会寻找完全匹配 \"public static void main(String[] args)\" 的方法作为入口。",
                        "es": "La JVM busca exactamente \"public static void main(String[] args)\" como punto de entrada.",
                        "vi": "JVM tìm chính xác \"public static void main(String[] args)\" làm điểm bắt đầu.",
                        "pt": "A JVM procura exatamente por \"public static void main(String[] args)\" como ponto de entrada.",
                        "id": "JVM mencari persis \"public static void main(String[] args)\" sebagai titik masuk.",
                        "de": "Die JVM sucht genau nach \"public static void main(String[] args)\" als Einstiegspunkt."},
        },
        {
            "stem": {"en": "Which symbol is used for single-line comments in Java?",
                     "ko": "Java에서 한 줄 주석에 사용하는 기호는?",
                     "ja": "Javaで単一行コメントに使う記号は?",
                     "zh": "在 Java 中，用于单行注释的符号是什么？",
                     "es": "¿Qué símbolo se usa para comentarios de una sola línea en Java?",
                     "vi": "Ký hiệu nào dùng cho chú thích một dòng trong Java?",
                     "pt": "Qual símbolo é usado para comentários de uma linha em Java?",
                     "id": "Simbol mana yang digunakan untuk komentar satu baris di Java?",
                     "de": "Welches Symbol wird für einzeilige Kommentare in Java verwendet?"},
            "choices": ["//", "#", "<!-- -->", "'"], "correct": 0,
            "explain": {"en": "Java uses // for single-line comments and /* */ for multi-line comments, like C and JavaScript.",
                        "ko": "Java는 C, JavaScript와 마찬가지로 한 줄 주석에 //, 여러 줄 주석에 /* */를 사용합니다.",
                        "ja": "JavaはCやJavaScriptと同様、単一行コメントに//、複数行コメントに/* */を使います。",
                        "zh": "Java 与 C、JavaScript 一样，使用 // 表示单行注释，/* */ 表示多行注释。",
                        "es": "Java usa // para comentarios de una sola línea y /* */ para comentarios de varias líneas, igual que C y JavaScript.",
                        "vi": "Java dùng // cho chú thích một dòng và /* */ cho chú thích nhiều dòng, giống C và JavaScript.",
                        "pt": "Java usa // para comentários de uma linha e /* */ para comentários de várias linhas, como C e JavaScript.",
                        "id": "Java menggunakan // untuk komentar satu baris dan /* */ untuk komentar multi-baris, seperti C dan JavaScript.",
                        "de": "Java verwendet // für einzeilige Kommentare und /* */ für mehrzeilige Kommentare, wie C und JavaScript."},
        },
        {
            "stem": {"en": "Which statement correctly declares an integer array of size 5 in Java?",
                     "ko": "Java에서 크기가 5인 정수 배열을 올바르게 선언하는 문장은?",
                     "ja": "Javaでサイズ5の整数配列を正しく宣言する文は?",
                     "zh": "在 Java 中正确声明一个大小为 5 的整数数组的语句是什么？",
                     "es": "¿Qué instrucción declara correctamente un array de enteros de tamaño 5 en Java?",
                     "vi": "Câu lệnh nào khai báo đúng một mảng số nguyên có kích thước 5 trong Java?",
                     "pt": "Qual instrução declara corretamente um array de inteiros de tamanho 5 em Java?",
                     "id": "Pernyataan mana yang dengan benar mendeklarasikan array integer berukuran 5 di Java?",
                     "de": "Welche Anweisung deklariert korrekt ein Integer-Array der Größe 5 in Java?"},
            "choices": ["int[] arr = new int[5];", "int arr[5];", "array<int> arr(5);", "int arr = new int(5);"], "correct": 0,
            "explain": {"en": "Java arrays are declared with a type, brackets, and \"new type[size]\", unlike C or C++ syntax.",
                        "ko": "Java 배열은 타입, 대괄호, \"new 타입[크기]\" 형태로 선언합니다. C/C++ 문법과는 다릅니다.",
                        "ja": "Java配列は型、角括弧、\"new 型[サイズ]\"の形で宣言します。C/C++の構文とは異なります。",
                        "zh": "Java 数组使用类型、方括号和 \"new 类型[大小]\" 的形式声明，与 C/C++ 的写法不同。",
                        "es": "Los arrays en Java se declaran con un tipo, corchetes y \"new tipo[tamaño]\", a diferencia de la sintaxis de C o C++.",
                        "vi": "Mảng trong Java được khai báo với một kiểu, dấu ngoặc vuông và \"new kiểu[kích thước]\", khác với cú pháp C hoặc C++.",
                        "pt": "Arrays em Java são declarados com um tipo, colchetes e \"new tipo[tamanho]\", diferente da sintaxe de C ou C++.",
                        "id": "Array Java dideklarasikan dengan tipe, tanda kurung siku, dan \"new tipe[ukuran]\", berbeda dari sintaks C atau C++.",
                        "de": "Java-Arrays werden mit einem Typ, Klammern und \"new Typ[Größe]\" deklariert, anders als in C oder C++."},
        },
        {
            "stem": {"en": "Which keyword is used for a class to inherit from another class in Java?",
                     "ko": "Java에서 클래스가 다른 클래스를 상속받을 때 사용하는 키워드는?",
                     "ja": "Javaでクラスが別のクラスを継承するときに使うキーワードは?",
                     "zh": "在 Java 中，用于类继承另一个类的关键字是什么？",
                     "es": "¿Qué palabra clave se usa para que una clase herede de otra clase en Java?",
                     "vi": "Từ khóa nào dùng để một lớp kế thừa từ một lớp khác trong Java?",
                     "pt": "Qual palavra-chave é usada para uma classe herdar de outra classe em Java?",
                     "id": "Kata kunci mana yang digunakan agar suatu class mewarisi dari class lain di Java?",
                     "de": "Welches Schlüsselwort wird verwendet, damit eine Klasse von einer anderen Klasse erbt in Java?"},
            "choices": ["extends", "implements", "inherits", "super"], "correct": 0,
            "explain": {"en": "\"extends\" is used for class inheritance; \"implements\" is used for interfaces instead.",
                        "ko": "클래스 상속에는 \"extends\"를 사용하며, \"implements\"는 인터페이스 구현에 사용합니다.",
                        "ja": "クラスの継承には\"extends\"を使い、\"implements\"はインターフェースの実装に使います。",
                        "zh": "类的继承使用 \"extends\"，而 \"implements\" 用于实现接口。",
                        "es": "\"extends\" se usa para la herencia de clases; \"implements\" se usa en cambio para interfaces.",
                        "vi": "\"extends\" dùng cho kế thừa lớp; \"implements\" được dùng cho interface.",
                        "pt": "\"extends\" é usado para herança de classes; \"implements\" é usado para interfaces.",
                        "id": "\"extends\" digunakan untuk pewarisan class; \"implements\" digunakan untuk interface.",
                        "de": "\"extends\" wird für die Klassenvererbung verwendet; \"implements\" wird stattdessen für Interfaces verwendet."},
        },
        {
            "stem": {"en": "Which statement correctly prints text to the console in Java?",
                     "ko": "Java에서 콘솔에 텍스트를 출력하는 올바른 문장은?",
                     "ja": "Javaでコンソールにテキストを出力する正しい文は?",
                     "zh": "在 Java 中正确地将文本打印到控制台的语句是什么？",
                     "es": "¿Qué instrucción imprime correctamente texto en la consola en Java?",
                     "vi": "Câu lệnh nào in đúng văn bản ra console trong Java?",
                     "pt": "Qual instrução imprime corretamente texto no console em Java?",
                     "id": "Pernyataan mana yang dengan benar mencetak teks ke konsol di Java?",
                     "de": "Welche Anweisung gibt Text korrekt in der Konsole in Java aus?"},
            "choices": ["System.out.println(\"text\");", "print(\"text\");", "console.log(\"text\");", "printf(\"text\");"], "correct": 0,
            "explain": {"en": "System.out.println() writes to standard output followed by a newline in Java.",
                        "ko": "System.out.println()은 Java에서 표준 출력에 줄바꿈과 함께 텍스트를 출력합니다.",
                        "ja": "System.out.println()はJavaで標準出力に改行付きでテキストを出力します。",
                        "zh": "System.out.println() 会在 Java 中向标准输出打印文本并换行。",
                        "es": "System.out.println() escribe en la salida estándar seguido de un salto de línea en Java.",
                        "vi": "System.out.println() ghi ra luồng xuất chuẩn kèm theo một dòng mới trong Java.",
                        "pt": "System.out.println() escreve na saída padrão seguido de uma nova linha em Java.",
                        "id": "System.out.println() menulis ke output standar diikuti oleh baris baru di Java.",
                        "de": "System.out.println() schreibt in Java auf die Standardausgabe, gefolgt von einem Zeilenumbruch."},
        },
    ],
    "c": [
        {
            "stem": {"en": "Which header must be included to use printf() in C?",
                     "ko": "C언어에서 printf()를 사용하려면 포함해야 하는 헤더는?",
                     "ja": "C言語でprintf()を使うためにインクルードが必要なヘッダーは?",
                     "zh": "在 C 语言中使用 printf() 需要包含哪个头文件？",
                     "es": "¿Qué cabecera debe incluirse para usar printf() en C?",
                     "vi": "Phải bao gồm header nào để sử dụng printf() trong C?",
                     "pt": "Qual cabeçalho deve ser incluído para usar printf() em C?",
                     "id": "Header mana yang harus disertakan untuk menggunakan printf() di C?",
                     "de": "Welcher Header muss eingebunden werden, um printf() in C zu verwenden?"},
            "choices": ["#include <stdio.h>", "#include <iostream>", "#include <string.h>", "#include <stdlib.h>"], "correct": 0,
            "explain": {"en": "stdio.h declares the standard input/output functions, including printf() and scanf().",
                        "ko": "stdio.h는 printf(), scanf()를 비롯한 표준 입출력 함수를 선언합니다.",
                        "ja": "stdio.hはprintf()やscanf()を含む標準入出力関数を宣言します。",
                        "zh": "stdio.h 声明了标准输入输出函数，包括 printf() 和 scanf()。",
                        "es": "stdio.h declara las funciones de entrada/salida estándar, incluyendo printf() y scanf().",
                        "vi": "stdio.h khai báo các hàm nhập/xuất chuẩn, bao gồm printf() và scanf().",
                        "pt": "stdio.h declara as funções de entrada/saída padrão, incluindo printf() e scanf().",
                        "id": "stdio.h mendeklarasikan fungsi input/output standar, termasuk printf() dan scanf().",
                        "de": "stdio.h deklariert die Standard-Ein-/Ausgabefunktionen, einschließlich printf() und scanf()."},
        },
        {
            "stem": {"en": "Which symbol marks the end of a statement in C?",
                     "ko": "C언어에서 하나의 문장이 끝났음을 나타내는 기호는?",
                     "ja": "C言語で文の終わりを示す記号は?",
                     "zh": "在 C 语言中，用于标记语句结束的符号是什么？",
                     "es": "¿Qué símbolo marca el final de una instrucción en C?",
                     "vi": "Ký hiệu nào đánh dấu kết thúc một câu lệnh trong C?",
                     "pt": "Qual símbolo marca o final de uma instrução em C?",
                     "id": "Simbol mana yang menandai akhir sebuah pernyataan di C?",
                     "de": "Welches Symbol markiert das Ende einer Anweisung in C?"},
            "choices": [";", ":", ".", ","], "correct": 0,
            "explain": {"en": "Every C statement ends with a semicolon; forgetting it is one of the most common syntax errors.",
                        "ko": "C언어의 모든 문장은 세미콜론으로 끝나며, 이를 빠뜨리는 것이 가장 흔한 문법 오류 중 하나입니다.",
                        "ja": "C言語のすべての文はセミコロンで終わり、これを忘れるのは最も一般的な構文エラーの一つです。",
                        "zh": "C 语言的每条语句都以分号结尾，遗漏分号是最常见的语法错误之一。",
                        "es": "Toda instrucción en C termina con un punto y coma; olvidarlo es uno de los errores de sintaxis más comunes.",
                        "vi": "Mọi câu lệnh trong C đều kết thúc bằng dấu chấm phẩy; quên nó là một trong những lỗi cú pháp phổ biến nhất.",
                        "pt": "Toda instrução em C termina com um ponto e vírgula; esquecê-lo é um dos erros de sintaxe mais comuns.",
                        "id": "Setiap pernyataan dalam C diakhiri dengan titik koma; melupakannya adalah salah satu kesalahan sintaks paling umum.",
                        "de": "Jede C-Anweisung endet mit einem Semikolon; es zu vergessen ist einer der häufigsten Syntaxfehler."},
        },
        {
            "stem": {"en": "Which declaration correctly creates a pointer to an integer in C?",
                     "ko": "C언어에서 정수를 가리키는 포인터를 올바르게 선언한 것은?",
                     "ja": "C言語で整数を指すポインタを正しく宣言したものは?",
                     "zh": "在 C 语言中正确声明一个指向整数的指针的写法是什么？",
                     "es": "¿Qué declaración crea correctamente un puntero a un entero en C?",
                     "vi": "Khai báo nào tạo đúng một con trỏ trỏ tới một số nguyên trong C?",
                     "pt": "Qual declaração cria corretamente um ponteiro para um inteiro em C?",
                     "id": "Deklarasi mana yang dengan benar membuat pointer ke integer di C?",
                     "de": "Welche Deklaration erzeugt korrekt einen Zeiger auf eine Ganzzahl in C?"},
            "choices": ["int *p;", "int p*;", "pointer int p;", "int &p;"], "correct": 0,
            "explain": {"en": "The asterisk before the variable name declares it as a pointer: \"int *p;\" means p holds an address.",
                        "ko": "변수 이름 앞의 별표(*)는 포인터를 선언합니다. \"int *p;\"는 p가 주소를 저장한다는 뜻입니다.",
                        "ja": "変数名の前のアスタリスク(*)はポインタを宣言します。\"int *p;\"はpがアドレスを保持することを意味します。",
                        "zh": "变量名前的星号（*）表示声明一个指针：\"int *p;\" 表示 p 保存的是地址。",
                        "es": "El asterisco antes del nombre de la variable la declara como puntero: \"int *p;\" significa que p contiene una dirección.",
                        "vi": "Dấu hoa thị trước tên biến khai báo nó là một con trỏ: \"int *p;\" có nghĩa là p chứa một địa chỉ.",
                        "pt": "O asterisco antes do nome da variável a declara como ponteiro: \"int *p;\" significa que p contém um endereço.",
                        "id": "Tanda bintang sebelum nama variabel mendeklarasikannya sebagai pointer: \"int *p;\" berarti p menyimpan sebuah alamat.",
                        "de": "Das Sternchen vor dem Variablennamen deklariert sie als Zeiger: \"int *p;\" bedeutet, dass p eine Adresse enthält."},
        },
        {
            "stem": {"en": "Which format specifier prints an integer with printf() in C?",
                     "ko": "C언어에서 printf()로 정수를 출력할 때 사용하는 서식 지정자는?",
                     "ja": "C言語でprintf()を使って整数を出力する際の書式指定子は?",
                     "zh": "在 C 语言中使用 printf() 打印整数时所用的格式说明符是什么？",
                     "es": "¿Qué especificador de formato imprime un entero con printf() en C?",
                     "vi": "Trình chỉ định định dạng nào in một số nguyên bằng printf() trong C?",
                     "pt": "Qual especificador de formato imprime um inteiro com printf() em C?",
                     "id": "Specifier format mana yang mencetak integer dengan printf() di C?",
                     "de": "Welcher Formatbezeichner gibt eine Ganzzahl mit printf() in C aus?"},
            "choices": ["%d", "%s", "%f", "%c"], "correct": 0,
            "explain": {"en": "%d (or %i) formats an integer; %s is for strings, %f for floats, and %c for a single character.",
                        "ko": "%d(또는 %i)는 정수를, %s는 문자열을, %f는 실수를, %c는 문자 하나를 출력할 때 사용합니다.",
                        "ja": "%d(または%i)は整数、%sは文字列、%fは浮動小数点数、%cは1文字を出力する際に使います。",
                        "zh": "%d（或 %i）用于格式化整数，%s 用于字符串，%f 用于浮点数，%c 用于单个字符。",
                        "es": "%d (o %i) formatea un entero; %s es para cadenas, %f para flotantes y %c para un solo carácter.",
                        "vi": "%d (hoặc %i) định dạng một số nguyên; %s dùng cho chuỗi, %f cho số thực, và %c cho một ký tự.",
                        "pt": "%d (ou %i) formata um inteiro; %s é para strings, %f para floats e %c para um único caractere.",
                        "id": "%d (atau %i) memformat integer; %s untuk string, %f untuk float, dan %c untuk satu karakter.",
                        "de": "%d (oder %i) formatiert eine Ganzzahl; %s steht für Zeichenketten, %f für Gleitkommazahlen und %c für ein einzelnes Zeichen."},
        },
        {
            "stem": {"en": "What does the \"sizeof\" operator return in C?",
                     "ko": "C언어에서 \"sizeof\" 연산자가 반환하는 값은?",
                     "ja": "C言語で\"sizeof\"演算子が返す値は?",
                     "zh": "在 C 语言中，\"sizeof\" 运算符返回的是什么？",
                     "es": "¿Qué devuelve el operador \"sizeof\" en C?",
                     "vi": "Toán tử \"sizeof\" trả về điều gì trong C?",
                     "pt": "O que o operador \"sizeof\" retorna em C?",
                     "id": "Apa yang dikembalikan oleh operator \"sizeof\" di C?",
                     "de": "Was gibt der Operator \"sizeof\" in C zurück?"},
            "choices": [
                {"en": "The size in bytes of a type or variable", "ko": "타입이나 변수의 크기(바이트 단위)",
                 "ja": "型や変数のサイズ(バイト単位)", "zh": "类型或变量的大小（以字节为单位）",
                 "es": "El tamaño en bytes de un tipo o variable", "vi": "Kích thước tính bằng byte của một kiểu hoặc biến",
                 "pt": "O tamanho em bytes de um tipo ou variável", "id": "Ukuran dalam byte dari suatu tipe atau variabel",
                 "de": "Die Größe in Bytes eines Typs oder einer Variablen"},
                {"en": "The number of elements in an array only", "ko": "배열의 요소 개수만",
                 "ja": "配列の要素数のみ", "zh": "仅数组的元素个数",
                 "es": "Solo el número de elementos de un array", "vi": "Chỉ số lượng phần tử trong một mảng",
                 "pt": "Apenas o número de elementos de um array", "id": "Hanya jumlah elemen dalam sebuah array",
                 "de": "Nur die Anzahl der Elemente in einem Array"},
                {"en": "The memory address of a variable", "ko": "변수의 메모리 주소",
                 "ja": "変数のメモリアドレス", "zh": "变量的内存地址",
                 "es": "La dirección de memoria de una variable", "vi": "Địa chỉ bộ nhớ của một biến",
                 "pt": "O endereço de memória de uma variável", "id": "Alamat memori dari sebuah variabel",
                 "de": "Die Speicheradresse einer Variablen"},
                {"en": "The current value stored in a variable", "ko": "변수에 저장된 현재 값",
                 "ja": "変数に格納されている現在の値", "zh": "变量当前存储的值",
                 "es": "El valor actual almacenado en una variable", "vi": "Giá trị hiện tại được lưu trong một biến",
                 "pt": "O valor atual armazenado em uma variável", "id": "Nilai saat ini yang tersimpan dalam sebuah variabel",
                 "de": "Der aktuell in einer Variablen gespeicherte Wert"},
            ], "correct": 0,
            "explain": {"en": "sizeof returns the size in bytes of any type or variable, which is also how it's commonly used to compute array lengths.",
                        "ko": "sizeof는 모든 타입이나 변수의 크기(바이트)를 반환하며, 이를 이용해 배열의 길이를 계산하는 경우가 많습니다.",
                        "ja": "sizeofは任意の型や変数のサイズ(バイト)を返し、これを利用して配列の長さを計算することが多いです。",
                        "zh": "sizeof 返回任意类型或变量的大小（字节数），常被用来计算数组的长度。",
                        "es": "sizeof devuelve el tamaño en bytes de cualquier tipo o variable, lo cual también se usa comúnmente para calcular la longitud de arrays.",
                        "vi": "sizeof trả về kích thước tính bằng byte của bất kỳ kiểu hoặc biến nào, và đó cũng là cách nó thường được dùng để tính độ dài mảng.",
                        "pt": "sizeof retorna o tamanho em bytes de qualquer tipo ou variável, o que também é usado comumente para calcular o tamanho de arrays.",
                        "id": "sizeof mengembalikan ukuran dalam byte dari tipe atau variabel apa pun, yang juga umum digunakan untuk menghitung panjang array.",
                        "de": "sizeof gibt die Größe in Bytes eines beliebigen Typs oder einer Variablen zurück, was auch häufig zur Berechnung von Array-Längen verwendet wird."},
        },
        {
            "stem": {"en": "Which loop structure checks its condition after running the loop body at least once?",
                     "ko": "루프 본문을 최소 한 번 실행한 뒤에 조건을 검사하는 반복문 구조는?",
                     "ja": "ループ本体を最低1回実行した後に条件を確認するループ構造は?",
                     "zh": "先执行一次循环体之后再检查条件的循环结构是什么？",
                     "es": "¿Qué estructura de bucle comprueba su condición después de ejecutar el cuerpo del bucle al menos una vez?",
                     "vi": "Cấu trúc vòng lặp nào kiểm tra điều kiện sau khi đã chạy phần thân vòng lặp ít nhất một lần?",
                     "pt": "Qual estrutura de loop verifica sua condição depois de executar o corpo do loop pelo menos uma vez?",
                     "id": "Struktur loop mana yang memeriksa kondisinya setelah menjalankan isi loop setidaknya sekali?",
                     "de": "Welche Schleifenstruktur prüft ihre Bedingung erst, nachdem der Schleifenkörper mindestens einmal ausgeführt wurde?"},
            "choices": ["do-while", "while", "for", "if"], "correct": 0,
            "explain": {"en": "A do-while loop runs the body first and checks the condition afterward, guaranteeing at least one execution.",
                        "ko": "do-while 루프는 본문을 먼저 실행한 뒤 조건을 검사하므로 최소 한 번은 실행됩니다.",
                        "ja": "do-whileループは本体を先に実行し、その後で条件を確認するため、最低1回は実行されます。",
                        "zh": "do-while 循环会先执行一次循环体，然后再检查条件，因此至少会执行一次。",
                        "es": "Un bucle do-while ejecuta primero el cuerpo y comprueba la condición después, garantizando al menos una ejecución.",
                        "vi": "Vòng lặp do-while chạy phần thân trước và kiểm tra điều kiện sau đó, đảm bảo thực hiện ít nhất một lần.",
                        "pt": "Um loop do-while executa o corpo primeiro e verifica a condição depois, garantindo pelo menos uma execução.",
                        "id": "Loop do-while menjalankan isi terlebih dahulu dan memeriksa kondisi setelahnya, menjamin setidaknya satu eksekusi.",
                        "de": "Eine do-while-Schleife führt zuerst den Rumpf aus und prüft die Bedingung danach, wodurch mindestens eine Ausführung garantiert ist."},
        },
    ],
}


def build_quiz_payload(lang):
    """현재 사이트 언어(lang)에 맞춰 QUIZ_BANK을 JSON 직렬화 가능한 구조로 변환한다.
    choices 항목은 보통 코드/고유 구문이라 언어 공통으로 공유하지만, 설명 문구가 선택지인
    경우(예: C의 sizeof 문항)는 choices 항목 자체가 {en,ko,ja,zh} dict일 수 있으므로
    그 경우에만 lang 값으로 치환한다."""
    def resolve_choice(choice):
        return choice[lang] if isinstance(choice, dict) else choice

    payload = {}
    for prog_key, _label in QUIZ_LANGS:
        questions = []
        for q in QUIZ_BANK[prog_key]:
            questions.append({
                "stem": q["stem"][lang],
                "choices": [resolve_choice(c) for c in q["choices"]],
                "correct": q["correct"],
                "explain": q["explain"][lang],
            })
        payload[prog_key] = questions
    return payload

# ---------------------------------------------------------------------------
# 렌더링 헬퍼
# ---------------------------------------------------------------------------

def esc(s):
    return s.format_map(FormatUrls()) if "{" in s else s


class FormatUrls(dict):
    """format_map에 쓰이는 헬퍼: 아래에서 실제 urls dict로 교체해서 사용."""
    def __missing__(self, key):
        return "{" + key + "}"


def fmt(s, urls):
    return s.format(home=urls["home"], about=urls["about"], privacy=urls["privacy"], tool=urls["tool"],
                     tool_xml=urls["tool_xml"], tool_converter=urls["tool_converter"], tool_sql=urls["tool_sql"],
                     tool_code=urls["tool_code"], tool_number=urls["tool_number"], tool_typing=urls["tool_typing"],
                     game_syntax=urls["game_syntax"],
                     faq=urls["faq"], contact=urls["contact"], terms=urls["terms"], updates=urls["updates"])


def theme_fouc_script():
    return '''<script>
  (function () {
    try {
      var t = localStorage.getItem("formix-theme");
      if (!t) t = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", t);
    } catch (e) {}
  })();
</script>'''


def lang_detect_script(lang):
    """루트(en) 페이지에서만 최초 방문 시 브라우저 언어를 감지해 리다이렉트.
    다른 언어 페이지는 방문 시 선호 언어를 현재 언어로 동기화만 한다."""
    if lang == DEFAULT_LANG:
        return '''<script>
  (function () {
    try {
      var SUPPORTED = ''' + repr([l for l in LANGS if l != DEFAULT_LANG]) + '''.slice();
      var stored = localStorage.getItem("formix-lang");
      if (stored) {
        if (stored !== "en" && SUPPORTED.indexOf(stored) !== -1) {
          location.replace("/" + stored + location.pathname + location.search);
        }
        return;
      }
      var langs = navigator.languages || [navigator.language || "en"];
      var match = null;
      for (var i = 0; i < langs.length; i++) {
        var code = String(langs[i]).slice(0, 2).toLowerCase();
        if (SUPPORTED.indexOf(code) !== -1) { match = code; break; }
      }
      if (match) {
        localStorage.setItem("formix-lang", match);
        location.replace("/" + match + location.pathname + location.search);
      } else {
        localStorage.setItem("formix-lang", "en");
      }
    } catch (e) {}
  })();
</script>'''
    else:
        return '''<script>
  try { localStorage.setItem("formix-lang", "''' + lang + '''"); } catch (e) {}
</script>'''


def hreflang_links(page_key):
    links = []
    for l in langs_for_page(page_key):
        u = urls_for(l)[page_key]
        links.append('<link rel="alternate" hreflang="%s" href="%s%s" />' % (LANG_META[l]["html_lang"], SITE_DOMAIN, u))
    default_u = urls_for(DEFAULT_LANG)[page_key]
    links.append('<link rel="alternate" hreflang="x-default" href="%s%s" />' % (SITE_DOMAIN, default_u))
    return "\n".join(links)


def breadcrumb_jsonld(lang, page_key, page_title):
    urls = urls_for(lang)
    items = [
        {"@type": "ListItem", "position": 1, "name": SITE_NAME[lang], "item": SITE_DOMAIN + urls["home"]},
        {"@type": "ListItem", "position": 2, "name": page_title, "item": SITE_DOMAIN + urls[page_key]},
    ]
    import json as _json
    data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}
    return '<script type="application/ld+json">\n%s\n</script>' % _json.dumps(data, ensure_ascii=False, indent=2)


OG_LOCALE = {"en": "en_US", "ko": "ko_KR", "ja": "ja_JP", "zh": "zh_CN",
             "es": "es_ES", "vi": "vi_VN", "pt": "pt_BR", "id": "id_ID", "de": "de_DE"}

THEME_COLOR_LIGHT = "#ffffff"
THEME_COLOR_DARK = "#14161a"


def search_verification_tags():
    tags = []
    if SEARCH_ENGINE_VERIFICATION.get("google"):
        tags.append('<meta name="google-site-verification" content="%s" />' % SEARCH_ENGINE_VERIFICATION["google"])
    if SEARCH_ENGINE_VERIFICATION.get("bing"):
        tags.append('<meta name="msvalidate.01" content="%s" />' % SEARCH_ENGINE_VERIFICATION["bing"])
    return "\n".join(tags)


def head_block(lang, page_key, title, description, keywords=None, og_title=None, og_description=None,
               robots="index, follow", extra=""):
    urls = urls_for(lang)
    canonical = SITE_DOMAIN + urls[page_key]
    kw = ('<meta name="keywords" content="%s" />\n' % keywords) if keywords else ""
    og_img = "%s/assets/img/og-%s.png" % (SITE_DOMAIN, lang)
    alt_locales = "\n".join(
        '<meta property="og:locale:alternate" content="%s" />' % OG_LOCALE[l] for l in langs_for_page(page_key) if l != lang
    )
    final_og_title = og_title or title
    final_og_desc = og_description or description
    return '''<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>%s</title>
<meta name="description" content="%s" />
%s<link rel="canonical" href="%s" />
<meta name="robots" content="%s" />
<meta name="theme-color" content="%s" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="%s" media="(prefers-color-scheme: dark)" />
%s
<meta property="og:type" content="website" />
<meta property="og:site_name" content="%s" />
<meta property="og:title" content="%s" />
<meta property="og:description" content="%s" />
<meta property="og:url" content="%s" />
<meta property="og:image" content="%s" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="%s" />
%s
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="%s" />
<meta name="twitter:description" content="%s" />
<meta name="twitter:image" content="%s" />

%s

<link rel="icon" href="%s" />
<link rel="stylesheet" href="/assets/css/style.css" />
%s
%s
%s''' % (title, description, kw, canonical, robots, THEME_COLOR_LIGHT, THEME_COLOR_DARK,
         search_verification_tags(),
         SITE_NAME[lang], final_og_title, final_og_desc, canonical, og_img,
         OG_LOCALE[lang], alt_locales, final_og_title, final_og_desc, og_img,
         hreflang_links(page_key), ICON_DATA_URI,
         theme_fouc_script(), lang_detect_script(lang), extra)


def flag_img_html(l, cls="flag-icon"):
    """국기 이모지 대신 쓰는 실제 SVG 국기 아이콘 <img> 태그.
    Windows(특히 Chrome)는 유니코드 국기 이모지 글꼴을 지원하지 않아 빈 사각형/텍스트로만
    보이는 경우가 많아, /assets/img/flags/{cc}.svg 파일을 직접 로드한다."""
    meta = LANG_META[l]
    return '<img class="%s" src="/assets/img/flags/%s.svg" alt="" loading="lazy" width="20" height="15">' % (cls, meta["flag_cc"])


def lang_switcher(lang, current_page_key):
    page_langs = langs_for_page(current_page_key)
    urls_by_lang = {l: urls_for(l)[current_page_key] for l in page_langs}
    items = []
    for l in page_langs:
        cur = ' aria-current="true"' if l == lang else ""
        items.append(
            '<li><a href="%s" data-lang-option="%s"%s>%s <span>%s</span></a></li>'
            % (urls_by_lang[l], l, cur, flag_img_html(l), LANG_META[l]["label"])
        )
    return '''<div class="lang-switch" data-lang-switch>
        <button class="lang-switch-toggle" type="button" data-lang-toggle aria-haspopup="true" aria-expanded="false" aria-label="%s">%s</button>
        <ul class="lang-switch-menu" data-lang-menu hidden>
          %s
        </ul>
      </div>''' % (NAV[lang]["lang"], flag_img_html(lang, "flag-icon flag-icon-toggle"), "\n          ".join(items))


TOOL_PAGE_KEYS = set(url_key for url_key, _ in TOOL_NAV_ITEMS)
GAME_PAGE_KEYS = set(url_key for url_key, _ in GAME_NAV_ITEMS)


def breadcrumb_html(lang, active_key):
    """모든 페이지 상단에 표시되는 현재 위치(홈 > [도구/게임 >] 현재 페이지) 표시줄.
    홈/404 페이지에는 표시하지 않는다."""
    if active_key in ("home", "notfound"):
        return ""
    urls = urls_for(lang)
    n = NAV[lang]
    items = ['<li><a href="%s">%s</a></li>' % (urls["home"], n["home"])]
    if active_key in TOOL_PAGE_KEYS:
        items.append('<li><span class="breadcrumb-group">%s</span></li>' % n["tools_group"])
    elif active_key in GAME_PAGE_KEYS:
        items.append('<li><span class="breadcrumb-group">%s</span></li>' % n["games_group"])
    items.append('<li aria-current="page"><span>%s</span></li>' % n[active_key])
    return '''<nav class="breadcrumb" aria-label="%s">
  <ol class="breadcrumb-list container">
    %s
  </ol>
</nav>''' % (n["breadcrumb_aria"], "\n    ".join(items))


def nav_dropdown_html(label, active_cls, links_html):
    """도구/게임 드롭다운 공통 마크업. data-nav-dropdown* 속성은 두 드롭다운 모두 동일하게
    써서 assets/js/main.js의 initNavDropdowns()가 하나의 로직으로 둘 다 처리하게 한다."""
    return '''<li class="nav-dropdown" data-nav-dropdown>
        <button class="nav-dropdown-toggle%s" type="button" data-nav-dropdown-toggle aria-haspopup="true" aria-expanded="false">
          %s <span class="nav-caret" aria-hidden="true">▾</span>
        </button>
        <ul class="nav-dropdown-menu" data-nav-dropdown-menu hidden>
          %s
        </ul>
      </li>''' % (active_cls, label, links_html)


def header_nav(lang, active_key, asset_home="/"):
    urls = urls_for(lang)
    n = NAV[lang]
    def cur(key):
        return ' aria-current="page"' if key == active_key else ""
    tool_links = "\n          ".join(
        '<li><a href="%s"%s>%s</a></li>' % (urls[url_key], cur(url_key), n[nav_key])
        for url_key, nav_key in TOOL_NAV_ITEMS
    )
    game_links = "\n          ".join(
        '<li><a href="%s"%s>%s</a></li>' % (urls[url_key], cur(url_key), n[nav_key])
        for url_key, nav_key in GAME_NAV_ITEMS
    )
    tools_active_cls = " is-active" if active_key in TOOL_PAGE_KEYS else ""
    games_active_cls = " is-active" if active_key in GAME_PAGE_KEYS else ""
    tools_dropdown = nav_dropdown_html(n["tools_group"], tools_active_cls, tool_links)
    games_dropdown = nav_dropdown_html(n["games_group"], games_active_cls, game_links)
    return '''<a class="skip-link" href="#main-content">%s</a>

<header class="site-header">
  <div class="container nav">
    <a class="nav-brand" href="%s">
      <span class="nav-brand-mark">F</span>
      %s
    </a>
    <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-nav" aria-label="%s">☰</button>
    <ul class="nav-links" id="primary-nav" data-nav-links>
      <li><a href="%s"%s>%s</a></li>
      %s
      %s
      <li><a href="%s"%s>%s</a></li>
      <li><a href="%s"%s>%s</a></li>
    </ul>
    <div class="nav-right">
      %s
      <button class="theme-toggle" type="button" data-theme-toggle aria-pressed="false" aria-label="%s">\U0001F319</button>
    </div>
  </div>
</header>
%s''' % (n["skip"], urls["home"], SITE_NAME[lang], n["menu"],
         urls["home"], cur("home"), n["home"],
         tools_dropdown,
         games_dropdown,
         urls["about"], cur("about"), n["about"],
         urls["privacy"], cur("privacy"), n["privacy"],
         lang_switcher(lang, active_key), n["dark"],
         breadcrumb_html(lang, active_key))


def footer_block(lang):
    urls = urls_for(lang)
    n = NAV[lang]
    tool_links = "\n      ".join(
        '<a href="%s">%s</a>' % (urls[url_key], n[nav_key]) for url_key, nav_key in TOOL_NAV_ITEMS
    )
    game_links = "\n      ".join(
        '<a href="%s">%s</a>' % (urls[url_key], n[nav_key]) for url_key, nav_key in GAME_NAV_ITEMS
    )
    page_links = "\n      ".join(
        '<a href="%s">%s</a>' % (urls[url_key], n[nav_key]) for url_key, nav_key in FOOTER_NAV_ITEMS
    )
    return '''<footer class="site-footer">
  <div class="container footer-inner">
    <span>&copy; <span id="footer-year">2026</span> %s. All rights reserved.</span>
    <nav class="footer-links">
      %s
      %s
      %s
      <button type="button" class="footer-settings-btn" data-cookie-settings>%s</button>
    </nav>
  </div>
</footer>

<script src="/assets/js/main.js"></script>
<script src="/assets/js/i18n.js"></script>
<script src="/assets/js/consent.js"></script>
<script>document.getElementById("footer-year").textContent = new Date().getFullYear();</script>''' % (
        SITE_NAME[lang], page_links, tool_links, game_links, n["cookie_settings"])


def page_wrap(lang, head, body):
    return '''<!DOCTYPE html>
<html lang="%s">
<head>
%s
</head>
<body>
%s
</body>
</html>
''' % (LANG_META[lang]["html_lang"], head, body)


def write_file(rel_path, content):
    full = os.path.join(ROOT, rel_path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return full


# ---------------------------------------------------------------------------
# 페이지 렌더러
# ---------------------------------------------------------------------------

def render_index(lang):
    c = CONTENT["index"][lang]
    urls = urls_for(lang)
    jsonld = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "%s",
  "url": "%s",
  "description": "%s",
  "inLanguage": "%s"
}
</script>''' % (SITE_NAME[lang], SITE_DOMAIN + urls["home"], c["hero_p"][:120], LANG_META[lang]["html_lang"])
    head = head_block(lang, "home", c["title"], c["description"], c["keywords"], c["og_title"], c["og_description"], extra=jsonld)
    cards = '''<a class="tool-card" href="%s">
        <div class="tool-card-icon">\U0001F9E9</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </a>

      <a class="tool-card" href="%s">
        <div class="tool-card-icon">\U0001F4C4</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </a>

      <a class="tool-card" href="%s">
        <div class="tool-card-icon">\U0001F504</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </a>

      <a class="tool-card" href="%s">
        <div class="tool-card-icon">\U0001F5C4️</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </a>

      <a class="tool-card" href="%s">
        <div class="tool-card-icon">\U0001F3A8</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </a>

      <a class="tool-card" href="%s">
        <div class="tool-card-icon">\U0001F522</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </a>''' % (urls["tool"], c["card1_title"], c["card1_desc"], c["card1_tag"],
                        urls["tool_xml"], c["card2_title"], c["card2_desc"], c["card2_tag"],
                        urls["tool_converter"], c["card3_title"], c["card3_desc"], c["card3_tag"],
                        urls["tool_sql"], c["card4_title"], c["card4_desc"], c["card4_tag"],
                        urls["tool_code"], c["card5_title"], c["card5_desc"], c["card5_tag"],
                        urls["tool_number"], c["card6_title"], c["card6_desc"], c["card6_tag"])
    game_cards = '''<a class="tool-card" href="%s">
        <div class="tool-card-icon">\U00002328\U0000FE0F</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </a>

      <a class="tool-card" href="%s">
        <div class="tool-card-icon">\U0001F9E0</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </a>''' % (urls["tool_typing"], c["card7_title"], c["card7_desc"], c["card7_tag"],
                        urls["game_syntax"], c["card8_title"], c["card8_desc"], c["card8_tag"])
    why_items = "\n      ".join(
        '<li><strong>%s</strong> — %s</li>' % (t, d) for t, d in c["why_items"]
    )
    body = header_nav(lang, "home") + '''

<main id="main-content">
  <section class="hero container">
    <span class="eyebrow">%s</span>
    <h1>%s</h1>
    <p>%s</p>
  </section>

  <section class="section container">
    <h2 style="margin-bottom: 4px;">%s</h2>
    <p style="color: var(--color-text-muted); margin-top: 0 0 20px;">%s</p>
    <div class="card-grid" style="margin-top: 20px;">
      %s
    </div>
  </section>

  <section class="section container">
    <h2 style="margin-bottom: 4px;">%s</h2>
    <p style="color: var(--color-text-muted); margin-top: 0 0 20px;">%s</p>
    <div class="card-grid" style="margin-top: 20px;">
      %s
    </div>
  </section>

  <section class="section-tight container prose">
    <h2>%s</h2>
    <ul>
      %s
    </ul>
  </section>
</main>

''' % (c["eyebrow"], c["h1"], c["hero_p"], c["features_h2"], c["features_p"], cards,
       c["games_h2"], c["games_p"], game_cards, c["why_h2"], why_items) + footer_block(lang)
    return page_wrap(lang, head, body)


def render_about(lang):
    c = CONTENT["about"][lang]
    urls = urls_for(lang)
    head = head_block(lang, "about", c["title"], c["description"], og_title=c["og_title"], og_description=c["og_description"],
                       extra=breadcrumb_jsonld(lang, "about", c["h1"]))
    s2_items = "\n        ".join(
        '<li><strong>%s</strong> — %s</li>' % (t, fmt(d, urls)) for t, d in c["s2_items"]
    )
    body = header_nav(lang, "about") + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%s</h1>
    <p>%s</p>
  </div>

  <div class="container prose section-tight" style="max-width: 760px;">
    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <ul>
        %s
      </ul>
    </section>

    <section>
      <h2>%s</h2>
      <ul>
        <li>%s</li>
        <li>%s</li>
        <li>%s</li>
        <li>%s</li>
        <li>%s</li>
        <li>%s</li>
        <li>%s</li>
        <li>%s</li>
      </ul>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
      <p><a href="mailto:%s">%s</a></p>
    </section>
  </div>
</main>

''' % (c["h1"], c["lead"], c["s1_h2"], fmt(c["s1_p"], urls), c["s2_h2"], s2_items,
       c["s3_h2"], fmt(c["s3_item"], urls), fmt(c["s3_item2"], urls), fmt(c["s3_item3"], urls), fmt(c["s3_item4"], urls), fmt(c["s3_item5"], urls), fmt(c["s3_item6"], urls), fmt(c["s3_item7"], urls), fmt(c["s3_item8"], urls), fmt(c["s3_p"], urls), c["s4_h2"], fmt(c["s4_p"], urls),
       c["s5_h2"], c["s5_p"], CONTACT_EMAIL, CONTACT_EMAIL) + footer_block(lang)
    return page_wrap(lang, head, body)


def render_privacy(lang):
    c = CONTENT["privacy"][lang]
    head = head_block(lang, "privacy", c["title"], c["description"], og_title=c["og_title"], og_description=c["og_description"],
                       extra=breadcrumb_jsonld(lang, "privacy", c["h1"]))
    body = header_nav(lang, "privacy") + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%s</h1>
    <p>%s</p>
  </div>

  <div class="container prose section-tight" style="max-width: 760px;">
    <p>%s</p>

    <section>
      <h2>%s</h2>
      <p>%s</p>
      <p>%s</p>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
      <ul>
        <li>%s</li>
        <li>%s</li>
        <li>%s</li>
      </ul>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
      <p><a href="mailto:%s">%s</a></p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>
  </div>
</main>

''' % (c["h1"], c["effective"], c["intro"],
       c["s1_h2"], c["s1_p1"], c["s1_p2"], c["s1_p3"],
       c["s2_h2"], c["s2_p1"], c["s2_p2"],
       c["s3_h2"], c["s3_p1"], c["s3_li1"], c["s3_li2"], c["s3_li3"], c["s3_p2"],
       c["s4_h2"], c["s4_p1"],
       c["s5_h2"], c["s5_p1"],
       c["s6_h2"], c["s6_p1"], CONTACT_EMAIL, CONTACT_EMAIL,
       c["s7_h2"], c["s7_p1"]) + footer_block(lang)
    return page_wrap(lang, head, body)


def faq_jsonld(lang, items):
    import json as _json
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": re.sub("<[^>]+>", "", q),
                "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)},
            }
            for q, a in items
        ],
    }
    return '<script type="application/ld+json">\n%s\n</script>' % _json.dumps(data, ensure_ascii=False, indent=2)


def render_faq(lang):
    c = CONTENT["faq"][lang]
    urls = urls_for(lang)
    items = [(q, fmt(a, urls)) for q, a in c["items"]]
    head = head_block(lang, "faq", c["title"], c["description"], og_title=c["og_title"], og_description=c["og_description"],
                       extra=faq_jsonld(lang, items) + "\n" + breadcrumb_jsonld(lang, "faq", c["h1"]))
    faq_items = "\n      ".join(
        '<details class="faq-item"><summary>%s</summary><div class="faq-answer"><p>%s</p></div></details>' % (q, a)
        for q, a in items
    )
    body = header_nav(lang, "faq") + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%s</h1>
    <p>%s</p>
  </div>

  <div class="container prose section-tight" style="max-width: 760px;">
    <div class="faq-list">
      %s
    </div>
  </div>
</main>

''' % (c["h1"], c["lead"], faq_items) + footer_block(lang)
    return page_wrap(lang, head, body)


def render_contact(lang):
    c = CONTENT["contact"][lang]
    urls = urls_for(lang)
    head = head_block(lang, "contact", c["title"], c["description"], og_title=c["og_title"], og_description=c["og_description"],
                       extra=breadcrumb_jsonld(lang, "contact", c["h1"]))
    s2_items = "\n        ".join("<li>%s</li>" % item for item in c["s2_items"])
    body = header_nav(lang, "contact") + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%s</h1>
    <p>%s</p>
  </div>

  <div class="container prose section-tight" style="max-width: 760px;">
    <section>
      <h2>%s</h2>
      <p>%s</p>
      <p><a href="mailto:%s">%s</a></p>
    </section>

    <section>
      <h2>%s</h2>
      <ul>
        %s
      </ul>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>
  </div>
</main>

''' % (c["h1"], c["lead"], c["s1_h2"], c["s1_p"], CONTACT_EMAIL, CONTACT_EMAIL,
       c["s2_h2"], s2_items, c["s3_h2"], fmt(c["s3_p"], urls)) + footer_block(lang)
    return page_wrap(lang, head, body)


def render_terms(lang):
    c = CONTENT["terms"][lang]
    urls = urls_for(lang)
    head = head_block(lang, "terms", c["title"], c["description"], og_title=c["og_title"], og_description=c["og_description"],
                       extra=breadcrumb_jsonld(lang, "terms", c["h1"]))
    body = header_nav(lang, "terms") + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%s</h1>
    <p>%s</p>
  </div>

  <div class="container prose section-tight" style="max-width: 760px;">
    <p>%s</p>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
      <ul>
        <li>%s</li>
        <li>%s</li>
        <li>%s</li>
      </ul>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
    </section>

    <section>
      <h2>%s</h2>
      <p>%s</p>
      <p><a href="mailto:%s">%s</a></p>
    </section>
  </div>
</main>

''' % (c["h1"], c["effective"], c["intro"],
       c["s1_h2"], c["s1_p1"],
       c["s2_h2"], fmt(c["s2_p1"], urls),
       c["s3_h2"], c["s3_p1"], c["s3_li1"], c["s3_li2"], c["s3_li3"],
       c["s4_h2"], c["s4_p1"],
       c["s5_h2"], c["s5_p1"],
       c["s6_h2"], c["s6_p1"],
       c["s7_h2"], c["s7_p1"],
       c["s8_h2"], fmt(c["s8_p1"], urls),
       c["s9_h2"], fmt(c["s9_p1"], urls), CONTACT_EMAIL, CONTACT_EMAIL) + footer_block(lang)
    return page_wrap(lang, head, body)


def render_updates(lang):
    c = CONTENT["updates"][lang]
    urls = urls_for(lang)
    head = head_block(lang, "updates", c["title"], c["description"], og_title=c["og_title"], og_description=c["og_description"],
                       extra=breadcrumb_jsonld(lang, "updates", c["h1"]))
    entries_html = "\n    ".join(
        '''<article class="update-entry">
      <p class="update-date">%s</p>
      <h2>%s</h2>
      <ul>
        %s
      </ul>
    </article>''' % (date, title, "\n        ".join("<li>%s</li>" % b for b in bullets))
        for date, title, bullets in c["entries"]
    )
    body = header_nav(lang, "updates") + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%s</h1>
    <p>%s</p>
  </div>

  <div class="container prose section-tight update-list" style="max-width: 760px;">
    %s

    <p>%s</p>
  </div>
</main>

''' % (c["h1"], c["lead"], entries_html, fmt(c["outro"], urls)) + footer_block(lang)
    return page_wrap(lang, head, body)


def render_notfound(lang):
    c = CONTENT["notfound"][lang]
    urls = urls_for(lang)
    head = '''<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>%s</title>
<meta name="robots" content="noindex, follow" />
<link rel="stylesheet" href="/assets/css/style.css" />
%s''' % (c["title"], theme_fouc_script())
    body = '''<header class="site-header">
  <div class="container nav">
    <a class="nav-brand" href="%s">
      <span class="nav-brand-mark">F</span>
      %s
    </a>
  </div>
</header>
<main>
  <div class="container hero">
    <span class="eyebrow">%s</span>
    <h1>%s</h1>
    <p>%s</p>
    <p style="margin-top: 24px;"><a class="btn btn-primary" href="%s">%s</a></p>
  </div>
</main>
<script src="/assets/js/main.js"></script>
<script src="/assets/js/i18n.js"></script>''' % (urls["home"], SITE_NAME[lang], c["eyebrow"], c["h1"], c["p"], urls["home"], c["back"])
    return page_wrap(lang, head, body)


def render_tool_page(lang, content_key, page_key, id_prefix, css_href, js_src, extra_toolbar=""):
    """도구 페이지 공통 렌더러. json-formatter/xml-formatter 모두 이 함수 하나로 생성한다.
    새 도구를 추가할 때는 CONTENT[content_key]에 콘텐츠를 채우고 이 함수를 얇게 감싸는
    wrapper 함수(및 urls_for/NAV/TOOL_NAV_ITEMS 항목)만 추가하면 된다."""
    c = CONTENT[content_key][lang]
    urls = urls_for(lang)
    n = NAV[lang]
    jsonld = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "%s",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Any (Web Browser)",
  "url": "%s",
  "description": "%s",
  "inLanguage": "%s",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
}
</script>''' % (c["jsonld_name"], SITE_DOMAIN + urls[page_key], c["jsonld_description"], LANG_META[lang]["html_lang"])
    head = head_block(lang, page_key, c["title"], c["description"], c["keywords"], c["og_title"], c["og_description"],
                       extra=jsonld + "\n" + breadcrumb_jsonld(lang, page_key, c["h1"]))
    head = head.replace('href="/assets/css/style.css" />', 'href="/assets/css/style.css" />\n<link rel="stylesheet" href="%s" />' % css_href)

    usage_lis = "\n      ".join("<li>%s</li>" % item for item in c["usage_items"])
    tips_lis = "\n      ".join("<li>%s</li>" % item for item in c["tips_items"])

    body = header_nav(lang, page_key) + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%(h1)s</h1>
    <p>%(lead)s</p>
  </div>

  <div class="container section-tight">
    <div class="jf-toolbar">
      <button class="btn btn-primary" id="btn-format" type="button">%(btn_format)s</button>
      <button class="btn" id="btn-sample" type="button">%(btn_sample)s</button>
      <button class="btn" id="btn-clear" type="button">%(btn_clear)s</button>
      <span class="spacer"></span>
      <label for="indent-select" class="visually-hidden">%(indent_label)s</label>
      <select class="jf-select" id="indent-select">
        <option value="2" selected>%(indent2)s</option>
        <option value="4">%(indent4)s</option>
        <option value="tab">%(indenttab)s</option>
      </select>
      %(extra_toolbar)s
      <button class="btn btn-sm" id="btn-copy" type="button">%(btn_copy)s</button>
      <button class="btn btn-sm" id="btn-copy-minify" type="button">%(btn_copy_minify)s</button>
      <button class="btn btn-sm" id="btn-download" type="button">%(btn_download)s</button>
    </div>

    <div class="jf-tabs" role="tablist" aria-label="%(tabs_aria)s">
      <button class="jf-tab is-active" id="tab-input" type="button" role="tab" aria-selected="true" aria-controls="panel-input" data-tab="input">
        %(tab_input)s
      </button>
      <button class="jf-tab" id="tab-output" type="button" role="tab" aria-selected="false" aria-controls="panel-output" data-tab="output">
        %(tab_output)s
        <span id="tab-output-badge" class="jf-tab-badge is-idle" aria-hidden="true"></span>
      </button>
    </div>

    <div class="jf-tabpanels">
      <section class="jf-panel" id="panel-input" role="tabpanel" aria-labelledby="tab-input" aria-label="%(tab_input)s">
        <div class="jf-panel-head jf-panel-head-status">
          <span id="json-status-top" class="status-pill is-idle">%(status_idle)s</span>
          <span id="json-error-detail-top" class="jf-error-detail"></span>
        </div>
        <div class="jf-search">
          <label for="json-input-search-mode" class="visually-hidden">%(input_search_mode_label)s</label>
          <select class="jf-select jf-search-mode" id="json-input-search-mode">
            <option value="contains" selected>%(opt_contains)s</option>
            <option value="exact">%(opt_exact_line)s</option>
            <option value="regex">%(opt_regex)s</option>
          </select>
          <label for="json-input-search" class="visually-hidden">%(input_search_mode_label)s</label>
          <input type="text" id="json-input-search" placeholder="%(input_search_placeholder)s" />
          <span class="jf-search-count" id="json-input-search-count">0 / 0</span>
          <button class="jf-icon-btn" id="btn-input-search-prev" type="button" title="%(prev_title)s" disabled>↑</button>
          <button class="jf-icon-btn" id="btn-input-search-next" type="button" title="%(next_title)s" disabled>↓</button>
          <button class="jf-icon-btn" id="btn-input-search-clear" type="button" title="%(clear_title)s" disabled>✕</button>
        </div>
        <div class="jf-editor">
          <div class="jf-gutter" id="json-gutter" aria-hidden="true">
            <div class="jf-gutter-inner" id="json-gutter-inner"></div>
          </div>
          <div class="jf-input-wrap">
            <div class="jf-input-highlight" id="json-input-highlight" aria-hidden="true"></div>
            <textarea
              id="json-input"
              spellcheck="false"
              autocapitalize="off"
              autocorrect="off"
              wrap="off"
              placeholder="%(input_placeholder)s"
            ></textarea>
          </div>
        </div>
        <div class="jf-status-bar">
          <span id="json-status" class="status-pill is-idle">%(status_idle)s</span>
          <span id="json-error-detail" class="jf-error-detail"></span>
        </div>
      </section>

      <section class="jf-panel" id="panel-output" role="tabpanel" aria-labelledby="tab-output" aria-label="%(tab_output)s" hidden>
        <div class="jf-panel-head">
          <span>%(output_label)s</span>
          <div class="jf-output-tools">
            <button class="btn btn-sm" id="btn-expand-all" type="button">%(expand_all)s</button>
            <button class="btn btn-sm" id="btn-collapse-all" type="button">%(collapse_all)s</button>
          </div>
        </div>
        <div class="jf-search">
          <label for="json-search-mode" class="visually-hidden">%(input_search_mode_label)s</label>
          <select class="jf-select jf-search-mode" id="json-search-mode" disabled>
            <option value="contains" selected>%(opt_contains)s</option>
            <option value="exact">%(opt_exact)s</option>
            <option value="regex">%(opt_regex)s</option>
          </select>
          <label for="json-search" class="visually-hidden">%(output_search_placeholder)s</label>
          <input type="text" id="json-search" placeholder="%(output_search_placeholder)s" disabled />
          <span class="jf-search-count" id="jf-search-count">0 / 0</span>
          <button class="jf-icon-btn" id="btn-search-prev" type="button" title="%(prev_title)s" disabled>↑</button>
          <button class="jf-icon-btn" id="btn-search-next" type="button" title="%(next_title)s" disabled>↓</button>
          <button class="jf-icon-btn" id="btn-search-clear" type="button" title="%(clear_title)s" disabled>✕</button>
        </div>
        <div class="jf-output-body">
          <div class="jf-gutter jf-gutter-with-toggle" id="json-output-gutter" aria-hidden="true">
            <div class="jf-gutter-inner" id="json-output-gutter-inner"></div>
          </div>
          <div id="json-output" role="log" aria-live="polite"></div>
        </div>
      </section>
    </div>

    <p class="jf-hint">%(hint)s</p>
  </div>

  <div class="container prose section-tight" style="max-width: 760px;">
    <h2>%(usage_h2)s</h2>
    <ul>
      %(usage_lis)s
    </ul>

    <h2>%(tips_h2)s</h2>
    <ul>
      %(tips_lis)s
    </ul>

    <h2>%(related_h2)s</h2>
    <ul>
      %(related_lis)s
      <li><a href="%(faq_url)s">%(faq_link_text)s</a></li>
    </ul>
  </div>
</main>

''' % dict(**c, usage_lis=usage_lis, tips_lis=tips_lis, related_h2=n["related_h2"],
       related_lis="\n      ".join(
           '<li><a href="%s">%s</a></li>' % (urls[other_key], n[nav_key])
           for other_key, nav_key in TOOL_NAV_ITEMS if other_key != page_key
       ),
       faq_url=urls["faq"], faq_link_text=n["faq"], extra_toolbar=extra_toolbar) + footer_block(lang)
    if id_prefix != "json":
        body = body.replace('"json-', '"' + id_prefix + '-')
    body = body.replace('<script src="/assets/js/main.js"></script>\n<script src="/assets/js/i18n.js"></script>',
                         '<script src="/assets/js/main.js"></script>\n<script src="%s"></script>\n<script src="/assets/js/i18n.js"></script>' % js_src)
    return page_wrap(lang, head, body)


def render_tool(lang):
    return render_tool_page(lang, "tool", "tool", "json", "/tools/json-formatter.css", "/tools/json-formatter.js")


def render_tool_xml(lang):
    return render_tool_page(lang, "tool_xml", "tool_xml", "xml", "/tools/xml-formatter.css", "/tools/xml-formatter.js")


def render_tool_converter(lang):
    c = CONTENT["tool_converter"][lang]
    direction_select = '''      <label for="json-direction-select" class="visually-hidden">%s</label>
      <select class="jf-select conv-direction-select" id="json-direction-select">
        <option value="auto" selected>%s</option>
        <option value="json2xml">%s</option>
        <option value="xml2json">%s</option>
      </select>''' % (c["direction_label"], c["dir_auto"], c["dir_json2xml"], c["dir_xml2json"])
    return render_tool_page(lang, "tool_converter", "tool_converter", "conv",
                             "/tools/json-xml-converter.css", "/tools/json-xml-converter.js",
                             extra_toolbar=direction_select)


def render_tool_sql(lang):
    c = CONTENT["tool_sql"][lang]
    dialect_select = '''      <label for="json-dialect-select" class="visually-hidden">%s</label>
      <select class="jf-select sql-dialect-select" id="json-dialect-select">
        <option value="sql" selected>%s</option>
        <option value="mysql">%s</option>
        <option value="postgresql">%s</option>
        <option value="tsql">%s</option>
        <option value="plsql">%s</option>
        <option value="bigquery">%s</option>
        <option value="snowflake">%s</option>
        <option value="sqlite">%s</option>
      </select>''' % (c["dialect_label"], c["dialect_standard"], c["dialect_mysql"], c["dialect_postgresql"],
                       c["dialect_tsql"], c["dialect_plsql"], c["dialect_bigquery"], c["dialect_snowflake"],
                       c["dialect_sqlite"])
    body = render_tool_page(lang, "tool_sql", "tool_sql", "sql",
                             "/tools/sql-formatter.css", "/tools/sql-formatter.js",
                             extra_toolbar=dialect_select)
    # sql-formatter(오픈소스, MIT) 라이브러리를 이 페이지에서만 로드한다.
    body = body.replace('<script src="/tools/sql-formatter.js"></script>',
                         '<script src="/tools/vendor/sql-formatter.min.js"></script>\n<script src="/tools/sql-formatter.js"></script>')
    return body


def render_tool_code(lang):
    c = CONTENT["tool_code"][lang]
    lang_options = [
        ("plain", "language_plain"), ("java", "language_java"), ("csharp", "language_csharp"),
        ("c", "language_c"), ("cpp", "language_cpp"), ("python", "language_python"),
        ("javascript", "language_javascript"), ("typescript", "language_typescript"), ("go", "language_go"),
        ("rust", "language_rust"), ("kotlin", "language_kotlin"), ("swift", "language_swift"),
        ("php", "language_php"), ("ruby", "language_ruby"), ("markup", "language_markup"),
        ("css", "language_css"), ("bash", "language_bash"), ("json", "language_json"),
        ("yaml", "language_yaml"), ("markdown", "language_markdown"), ("sql", "language_sql"),
    ]
    options_html = "\n        ".join(
        '<option value="%s"%s>%s</option>' % (val, ' selected' if val == "plain" else "", c[key])
        for val, key in lang_options
    )
    language_select = '''      <label for="json-language-select" class="visually-hidden">%s</label>
      <select class="jf-select code-language-select" id="json-language-select">
        %s
      </select>''' % (c["language_label"], options_html)
    body = render_tool_page(lang, "tool_code", "tool_code", "code",
                             "/tools/code-viewer.css", "/tools/code-viewer.js",
                             extra_toolbar=language_select)
    # Prism.js(오픈소스, MIT) 라이브러리를 이 페이지에서만 로드한다.
    body = body.replace('<script src="/tools/code-viewer.js"></script>',
                         '<script src="/tools/vendor/prism-bundle.min.js"></script>\n<script src="/tools/code-viewer.js"></script>')
    return body


def render_tool_number(lang):
    c = CONTENT["tool_number"][lang]
    extra_toolbar = '''      <label for="json-mode-select" class="visually-hidden">%s</label>
      <select class="jf-select num-mode-select" id="json-mode-select">
        <option value="cardinal" selected>%s</option>
        <option value="ordinal">%s</option>
        <option value="digits">%s</option>
        <option value="time">%s</option>
        <option value="date">%s</option>
        <option value="currency">%s</option>
      </select>
      <span id="json-style-label-wrap">
        <label for="json-style-select" class="visually-hidden">%s</label>
        <select class="jf-select num-style-select" id="json-style-select"></select>
      </span>''' % (c["mode_label"], c["mode_cardinal"], c["mode_ordinal"], c["mode_digits"],
                     c["mode_time"], c["mode_date"], c["mode_currency"], c["style_label"])
    body = render_tool_page(lang, "tool_number", "tool_number", "num",
                             "/tools/number-reader.css", "/tools/number-reader.js",
                             extra_toolbar=extra_toolbar)
    return body


def render_tool_typing(lang):
    """타자 속도 테스트 전용 렌더러. 입력/출력 2패널(jf-toolbar) 구조를 쓰는 다른 도구들과
    달리 샘플 문장 표시 + 타이핑 입력 + 통계(WPM/정확도/시간) UI라서 render_tool_page를
    재사용하지 않고 전용 마크업을 쓴다. usage/tips/related 섹션 패턴은 그대로 따른다."""
    c = CONTENT["tool_typing"][lang]
    urls = urls_for(lang)
    n = NAV[lang]
    page_key = "tool_typing"
    jsonld = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "%s",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Any (Web Browser)",
  "url": "%s",
  "description": "%s",
  "inLanguage": "%s",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
}
</script>''' % (c["jsonld_name"], SITE_DOMAIN + urls[page_key], c["jsonld_description"], LANG_META[lang]["html_lang"])
    head = head_block(lang, page_key, c["title"], c["description"], c["keywords"], c["og_title"], c["og_description"],
                       extra=jsonld + "\n" + breadcrumb_jsonld(lang, page_key, c["h1"]))
    head = head.replace('href="/assets/css/style.css" />', 'href="/assets/css/style.css" />\n<link rel="stylesheet" href="/tools/typing-test.css" />')

    usage_lis = "\n      ".join("<li>%s</li>" % item for item in c["usage_items"])
    tips_lis = "\n      ".join("<li>%s</li>" % item for item in c["tips_items"])
    related_lis = "\n      ".join(
        '<li><a href="%s">%s</a></li>' % (urls[other_key], n[nav_key])
        for other_key, nav_key in GAME_NAV_ITEMS if other_key != page_key
    )
    share_url = SITE_DOMAIN + urls[page_key]

    body = header_nav(lang, page_key) + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%(h1)s</h1>
    <p>%(lead)s</p>
  </div>

  <div class="container section-tight tt-layout">
    <div class="tt-main">
      <div class="tt-stats" id="tt-stats">
        <div class="tt-stat"><span class="tt-stat-label">%(label_time)s</span><span class="tt-stat-value" id="tt-time">0.0s</span></div>
        <div class="tt-stat"><span class="tt-stat-label">%(label_wpm)s</span><span class="tt-stat-value" id="tt-wpm">0</span></div>
        <div class="tt-stat"><span class="tt-stat-label">%(label_accuracy)s</span><span class="tt-stat-value" id="tt-accuracy">100%%</span></div>
        <div class="tt-stat"><span class="tt-stat-label">%(label_best)s</span><span class="tt-stat-value" id="tt-best">%(best_none)s</span></div>
      </div>

      <div class="tt-panel" id="tt-panel" data-result-prefix="%(result_prefix)s" data-wpm-label="%(share_wpm_label)s" data-accuracy-label="%(share_accuracy_label)s" data-share-url="%(share_url)s" data-status-idle="%(status_idle)s" data-status-active="%(status_active)s" data-status-done="%(status_done)s" data-best-none="%(best_none)s">
        <div class="tt-panel-head">
          <span id="tt-status" class="status-pill is-idle">%(status_idle)s</span>
        </div>
        <div class="tt-passage" id="tt-passage" aria-hidden="true"></div>
        <label for="tt-input" class="visually-hidden">%(input_aria)s</label>
        <textarea id="tt-input" class="tt-input" spellcheck="false" autocapitalize="off" autocorrect="off" wrap="off" rows="3"></textarea>
      </div>

      <div class="tt-toolbar">
        <button class="btn btn-primary" id="tt-btn-restart" type="button">%(btn_restart)s</button>
        <button class="btn" id="tt-btn-copy" type="button" disabled>%(btn_copy_result)s</button>
        <span class="tt-copied" id="tt-copied" hidden>%(copied_msg)s</span>
      </div>

      <div class="tt-submit" id="tt-submit" hidden>
        <label for="tt-nickname" class="visually-hidden">%(nickname_placeholder)s</label>
        <input type="text" id="tt-nickname" class="tt-nickname-input" placeholder="%(nickname_placeholder)s" maxlength="20" />
        <button class="btn btn-primary" id="tt-btn-submit" type="button">%(btn_submit_score)s</button>
        <span class="tt-submit-status" id="tt-submit-status" aria-live="polite"></span>
      </div>

      <p class="jf-hint">%(hint)s</p>
    </div>

    <div class="tt-side" id="tt-leaderboard-wrap" data-lang="%(lb_lang)s"
         data-lb-loading="%(leaderboard_loading)s" data-lb-empty="%(leaderboard_empty)s" data-lb-error="%(leaderboard_error)s"
         data-lb-submitting="%(submitting)s" data-lb-success="%(submit_success)s" data-lb-error-submit="%(submit_error)s"
         data-lb-rate-limited="%(submit_rate_limited)s">
      <h2>%(leaderboard_h2)s</h2>
      <p class="tt-leaderboard-lead">%(leaderboard_lead)s</p>
      <div class="tt-leaderboard-table-wrap">
        <table class="tt-leaderboard-table">
          <thead>
            <tr><th>%(col_rank)s</th><th>%(col_name)s</th><th>%(col_wpm)s</th><th>%(col_accuracy)s</th></tr>
          </thead>
          <tbody id="tt-leaderboard-body">
            <tr><td colspan="4" class="tt-leaderboard-status">%(leaderboard_loading)s</td></tr>
          </tbody>
        </table>
      </div>
      <p class="jf-hint">%(leaderboard_note)s</p>
    </div>
  </div>

  <div class="container prose section-tight" style="max-width: 760px;">
    <h2>%(usage_h2)s</h2>
    <ul>
      %(usage_lis)s
    </ul>

    <h2>%(tips_h2)s</h2>
    <ul>
      %(tips_lis)s
    </ul>

    <h2>%(related_h2)s</h2>
    <ul>
      %(related_lis)s
      <li><a href="%(faq_url)s">%(faq_link_text)s</a></li>
    </ul>
  </div>
</main>

''' % dict(**c, usage_lis=usage_lis, tips_lis=tips_lis, related_h2=n["related_h2"], related_lis=related_lis,
       faq_url=urls["faq"], faq_link_text=n["faq"], share_url=share_url, lb_lang=lang) + footer_block(lang)
    body = body.replace('<script src="/assets/js/main.js"></script>\n<script src="/assets/js/i18n.js"></script>',
                         '<script src="/assets/js/main.js"></script>\n<script src="/tools/typing-test.js"></script>\n<script src="/assets/js/i18n.js"></script>')
    return page_wrap(lang, head, body)


def render_game_syntax(lang):
    """프로그래밍 언어별 문법 객관식 퀴즈 게임. 타자 속도 테스트와 마찬가지로 입력/출력
    2패널 구조가 아니므로 render_tool_page를 재사용하지 않고 전용 마크업을 쓴다.
    문제 데이터(QUIZ_BANK)는 현재 사이트 언어에 맞춰 build_quiz_payload()로 JSON 직렬화해
    <script type="application/json"> 태그에 그대로 심어두고, game-syntax-quiz.js가
    그 JSON만 읽어 UI를 그린다(사이트 언어별 번역은 빌드 타임에 이미 끝난 상태)."""
    import json
    c = CONTENT["game_syntax"][lang]
    urls = urls_for(lang)
    n = NAV[lang]
    page_key = "game_syntax"
    jsonld = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "%s",
  "applicationCategory": "GameApplication",
  "operatingSystem": "Any (Web Browser)",
  "url": "%s",
  "description": "%s",
  "inLanguage": "%s",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
}
</script>''' % (c["jsonld_name"], SITE_DOMAIN + urls[page_key], c["jsonld_description"], LANG_META[lang]["html_lang"])
    head = head_block(lang, page_key, c["title"], c["description"], c["keywords"], c["og_title"], c["og_description"],
                       extra=jsonld + "\n" + breadcrumb_jsonld(lang, page_key, c["h1"]))
    head = head.replace('href="/assets/css/style.css" />', 'href="/assets/css/style.css" />\n<link rel="stylesheet" href="/games/syntax-quiz.css" />')

    usage_lis = "\n      ".join("<li>%s</li>" % item for item in c["usage_items"])
    tips_lis = "\n      ".join("<li>%s</li>" % item for item in c["tips_items"])
    related_lis = "\n      ".join(
        '<li><a href="%s">%s</a></li>' % (urls[other_key], n[nav_key])
        for other_key, nav_key in GAME_NAV_ITEMS if other_key != page_key
    )
    lang_buttons = "\n        ".join(
        '<button class="gq-lang-btn" type="button" data-quiz-lang="%s"><span class="gq-lang-name">%s</span><span class="gq-lang-start">%s</span></button>'
        % (prog_key, label, c["btn_start"])
        for prog_key, label in QUIZ_LANGS
    )
    quiz_data_json = json.dumps(build_quiz_payload(lang), ensure_ascii=False)

    body = header_nav(lang, page_key) + '''

<main id="main-content">
  <div class="page-header container">
    <h1>%(h1)s</h1>
    <p>%(lead)s</p>
  </div>

  <div class="container section-tight">
    <div class="gq-panel" id="gq-panel"
         data-progress-template="%(question_progress)s" data-score-label="%(score_label)s"
         data-correct-label="%(correct_label)s" data-incorrect-label="%(incorrect_label)s"
         data-explain-label="%(explain_label)s" data-btn-next="%(btn_next)s"
         data-btn-change-lang="%(btn_change_lang)s" data-finish-title="%(finish_title)s"
         data-finish-summary="%(finish_summary)s" data-btn-retry="%(btn_retry)s">

      <div id="gq-select" class="gq-select">
        <h2>%(lang_select_label)s</h2>
        <div class="gq-lang-grid">
        %(lang_buttons)s
        </div>
      </div>

      <div id="gq-quiz" class="gq-quiz" hidden>
        <div class="gq-quiz-head">
          <span id="gq-progress" class="gq-progress"></span>
          <span id="gq-score" class="gq-score"></span>
        </div>
        <p id="gq-stem" class="gq-stem"></p>
        <div id="gq-choices" class="gq-choices"></div>
        <div id="gq-feedback" class="gq-feedback" hidden>
          <p id="gq-feedback-label" class="gq-feedback-label"></p>
          <p id="gq-explain" class="gq-explain"></p>
          <button class="btn btn-primary" id="gq-btn-next" type="button"></button>
        </div>
      </div>

      <div id="gq-finish" class="gq-finish" hidden>
        <h2 id="gq-finish-title"></h2>
        <p id="gq-finish-summary" class="gq-finish-summary"></p>
        <div class="gq-finish-actions">
          <button class="btn btn-primary" id="gq-btn-retry" type="button"></button>
          <button class="btn" id="gq-btn-change-lang" type="button"></button>
        </div>
      </div>
    </div>
  </div>

  <div class="container prose section-tight" style="max-width: 760px;">
    <h2>%(usage_h2)s</h2>
    <ul>
      %(usage_lis)s
    </ul>

    <h2>%(tips_h2)s</h2>
    <ul>
      %(tips_lis)s
    </ul>

    <h2>%(related_h2)s</h2>
    <ul>
      %(related_lis)s
      <li><a href="%(faq_url)s">%(faq_link_text)s</a></li>
    </ul>
  </div>
</main>

<script type="application/json" id="gq-data">%(quiz_data_json)s</script>

''' % dict(**c, usage_lis=usage_lis, tips_lis=tips_lis, related_h2=n["related_h2"], related_lis=related_lis,
       faq_url=urls["faq"], faq_link_text=n["faq"], lang_buttons=lang_buttons,
       quiz_data_json=quiz_data_json) + footer_block(lang)
    body = body.replace('<script src="/assets/js/main.js"></script>\n<script src="/assets/js/i18n.js"></script>',
                         '<script src="/assets/js/main.js"></script>\n<script src="/games/syntax-quiz.js"></script>\n<script src="/assets/js/i18n.js"></script>')
    return page_wrap(lang, head, body)


# ---------------------------------------------------------------------------
# 실행부: 각 언어 x 각 페이지 조합으로 정적 파일 생성 + sitemap
# ---------------------------------------------------------------------------

def build():
    written = []
    for lang in LANGS:
        prefix = lang_prefix(lang)
        written.append(write_file(prefix + "/index.html", render_index(lang)))
        written.append(write_file(prefix + "/about.html", render_about(lang)))
        written.append(write_file(prefix + "/privacy.html", render_privacy(lang)))
        written.append(write_file(prefix + "/faq.html", render_faq(lang)))
        written.append(write_file(prefix + "/contact.html", render_contact(lang)))
        written.append(write_file(prefix + "/terms.html", render_terms(lang)))
        written.append(write_file(prefix + "/updates.html", render_updates(lang)))
        written.append(write_file(prefix + "/404.html", render_notfound(lang)))
        written.append(write_file(prefix + "/tools/json-formatter.html", render_tool(lang)))
        written.append(write_file(prefix + "/tools/xml-formatter.html", render_tool_xml(lang)))
        written.append(write_file(prefix + "/tools/json-xml-converter.html", render_tool_converter(lang)))
        written.append(write_file(prefix + "/tools/sql-formatter.html", render_tool_sql(lang)))
        written.append(write_file(prefix + "/tools/code-viewer.html", render_tool_code(lang)))
        if lang in NUMBER_READER_LANGS:
            written.append(write_file(prefix + "/tools/number-reader.html", render_tool_number(lang)))
        written.append(write_file(prefix + "/games/typing-test.html", render_tool_typing(lang)))
        written.append(write_file(prefix + "/games/syntax-quiz.html", render_game_syntax(lang)))

    # sitemap.xml (404는 noindex이므로 제외)
    import datetime
    today = datetime.date.today().isoformat()
    priority_map = {"home": "1.0", "about": "0.6", "privacy": "0.3", "faq": "0.5", "contact": "0.4",
                     "terms": "0.3", "updates": "0.5", "tool": "0.9", "tool_xml": "0.9", "tool_converter": "0.9",
                     "tool_sql": "0.9", "tool_code": "0.9", "tool_number": "0.9", "tool_typing": "0.9",
                     "game_syntax": "0.9"}
    changefreq_map = {"home": "weekly", "about": "monthly", "privacy": "yearly", "faq": "monthly", "contact": "yearly",
                       "terms": "yearly", "updates": "weekly", "tool": "weekly", "tool_xml": "weekly", "tool_converter": "weekly",
                       "tool_sql": "weekly", "tool_code": "weekly", "tool_number": "weekly", "tool_typing": "weekly",
                       "game_syntax": "weekly"}
    url_entries = []
    for page_key in ["home", "about", "privacy", "faq", "contact", "terms", "updates", "tool", "tool_xml", "tool_converter", "tool_sql", "tool_code", "tool_number", "tool_typing", "game_syntax"]:
        page_langs = langs_for_page(page_key)
        for lang in page_langs:
            loc = SITE_DOMAIN + urls_for(lang)[page_key]
            alt_links = "\n".join(
                '    <xhtml:link rel="alternate" hreflang="%s" href="%s%s" />' % (
                    LANG_META[l]["html_lang"], SITE_DOMAIN, urls_for(l)[page_key])
                for l in page_langs
            )
            alt_links += '\n    <xhtml:link rel="alternate" hreflang="x-default" href="%s%s" />' % (
                SITE_DOMAIN, urls_for(DEFAULT_LANG)[page_key])
            url_entries.append(
                '  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>%s</changefreq>\n    <priority>%s</priority>\n%s\n  </url>'
                % (loc, today, changefreq_map[page_key], priority_map[page_key], alt_links)
            )
    sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
%s
</urlset>
''' % "\n".join(url_entries)
    written.append(write_file("sitemap.xml", sitemap))

    robots = '''User-agent: *
Allow: /

Sitemap: %s/sitemap.xml
''' % SITE_DOMAIN
    written.append(write_file("robots.txt", robots))

    ads_txt = "google.com, pub-4388558717852090, DIRECT, f08c47fec0942fa0\n"
    written.append(write_file("ads.txt", ads_txt))

    print("Wrote %d files" % len(written))
    for w in written:
        print(" -", os.path.relpath(w, ROOT))


if __name__ == "__main__":
    build()
