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

LANGS = ["en", "ko", "ja", "zh"]
DEFAULT_LANG = "en"

LANG_META = {
    "en": {"label": "English", "flag": "\U0001F1FA\U0001F1F8", "html_lang": "en"},
    "ko": {"label": "한국어", "flag": "\U0001F1F0\U0001F1F7", "html_lang": "ko"},
    "ja": {"label": "日本語", "flag": "\U0001F1EF\U0001F1F5", "html_lang": "ja"},
    "zh": {"label": "中文", "flag": "\U0001F1E8\U0001F1F3", "html_lang": "zh-CN"},
}

SITE_NAME = {"en": "Formix", "ko": "Formix", "ja": "Formix", "zh": "Formix"}

CONTACT_EMAIL = "hongsh119@gmail.com"

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
        "notfound": p + "/404.html",
    }


# 헤더 내비게이션에 노출할 도구 목록. 새 도구를 추가할 때 이 리스트에 (urls_for 키, NAV 라벨 키)만
# 추가하면 헤더/푸터/언어 스위처가 모두 자동으로 반영된다.
TOOL_NAV_ITEMS = [("tool", "tool"), ("tool_xml", "tool_xml")]

# 푸터에 노출할 일반 페이지(도구가 아닌 페이지) 목록. 새 페이지를 추가할 때 이 리스트에
# (urls_for 키, NAV 라벨 키)만 추가하면 푸터/사이트맵이 자동으로 반영된다.
FOOTER_NAV_ITEMS = [("about", "about"), ("faq", "faq"), ("updates", "updates"), ("contact", "contact"),
                     ("terms", "terms"), ("privacy", "privacy")]

NAV = {
    "en": {"home": "Home", "tool": "JSON Formatter", "tool_xml": "XML Formatter", "about": "About",
           "privacy": "Privacy Policy", "faq": "FAQ", "contact": "Contact", "related_h2": "Related",
           "cookie_settings": "Cookie preferences", "terms": "Terms of Service", "updates": "What's New",
           "menu": "Open menu", "dark": "Switch to dark mode", "light": "Switch to light mode",
           "lang": "Select language", "skip": "Skip to content"},
    "ko": {"home": "홈", "tool": "JSON 포매터", "tool_xml": "XML 포매터", "about": "사이트 소개",
           "privacy": "개인정보처리방침", "faq": "자주 묻는 질문", "contact": "문의하기", "related_h2": "관련 링크",
           "cookie_settings": "쿠키 설정", "terms": "이용약관", "updates": "업데이트 소식",
           "menu": "메뉴 열기", "dark": "다크 모드로 전환", "light": "라이트 모드로 전환",
           "lang": "언어 선택", "skip": "본문으로 건너뛰기"},
    "ja": {"home": "ホーム", "tool": "JSONフォーマッター", "tool_xml": "XMLフォーマッター", "about": "サイト紹介",
           "privacy": "プライバシーポリシー", "faq": "よくある質問", "contact": "お問い合わせ", "related_h2": "関連リンク",
           "cookie_settings": "Cookie設定", "terms": "利用規約", "updates": "更新情報",
           "menu": "メニューを開く", "dark": "ダークモードに切り替え", "light": "ライトモードに切り替え",
           "lang": "言語選択", "skip": "本文へスキップ"},
    "zh": {"home": "首页", "tool": "JSON 格式化", "tool_xml": "XML 格式化", "about": "关于本站",
           "privacy": "隐私政策", "faq": "常见问题", "contact": "联系我们", "related_h2": "相关链接",
           "cookie_settings": "Cookie 设置", "terms": "使用条款", "updates": "更新日志",
           "menu": "打开菜单", "dark": "切换到深色模式", "light": "切换到浅色模式",
           "lang": "选择语言", "skip": "跳转到正文"},
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
        card3_title="More tools coming soon",
        card3_desc="Text/encoding conversion, case conversion, and more tools will be added over time.",
        card3_tag="Coming soon",
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
        card3_title="다음 도구 준비 중",
        card3_desc="텍스트/인코딩 변환, 대소문자 변환 등 새로운 도구를 순차적으로 추가할 예정입니다.",
        card3_tag="Coming soon",
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
        card3_title="次のツールを準備中",
        card3_desc="テキスト/エンコード変換、大文字小文字変換など、新しいツールを順次追加していく予定です。",
        card3_tag="Coming soon",
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
        card3_title="更多工具即将上线",
        card3_desc="文本/编码转换、大小写转换等新工具将陆续添加。",
        card3_tag="Coming soon",
        why_h2="为什么选择Formix?",
        why_items=[
            ("无需安装、无需注册", "打开链接即可立即使用。"),
            ("浏览器端处理", "输入的数据完全在客户端处理，不会发送到服务器。"),
            ("支持深色模式", "随时通过右上角的按钮切换浅色/深色主题。"),
            ("持续更新功能", "我们会持续添加在开发和工作中常用的实用工具。"),
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
        s3_p="Suggestions for new features or improvements are always welcome.",
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
        s3_p="새로운 기능 제안이나 개선 의견은 언제든 환영합니다.",
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
        s3_p="新機能のご提案や改善のご意見はいつでも歓迎します。",
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
        s3_p="欢迎随时提出新功能建议或改进意见。",
        s4_h2="关于广告与服务运营",
        s4_p='为了维持服务运营，Formix未来可能会引入 Google AdSense 等广告服务。如果引入广告，相关数据的处理方式将在<a href="{privacy}">隐私政策</a>页面中透明说明，工具的核心功能(如 JSON 处理)将始终免费提供，不受广告影响。',
        s5_h2="联系方式", s5_p="如有错误反馈、功能建议或其他咨询，请通过以下邮箱联系我们。",
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
            ("Will more tools be added?", 'Yes. Formix started with a JSON Formatter and now also offers an <a href="{tool_xml}">XML Formatter</a>. We plan to keep adding small, genuinely useful browser-based tools over time — see our <a href="{about}">About</a> page for our guiding principles.'),
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
            ("앞으로 도구가 더 추가되나요?", '네. Formix는 JSON 포매터로 시작해 현재는 <a href="{tool_xml}">XML 포매터</a>도 제공하고 있습니다. 앞으로도 실무에 유용한 브라우저 기반 도구를 계속 추가할 예정입니다. 운영 철학은 <a href="{about}">사이트 소개</a> 페이지를 참고해주세요.'),
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
            ("今後もツールは追加されますか?", 'はい。FormixはJSONフォーマッターから始まり、現在は<a href="{tool_xml}">XMLフォーマッター</a>も提供しています。今後も実務に役立つブラウザ完結型のツールを継続的に追加していく予定です。運営方針は<a href="{about}">サイト紹介</a>ページをご覧ください。'),
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
            ("以后会添加更多工具吗?", '会的。Formix从 JSON 格式化工具起步，目前也提供 <a href="{tool_xml}">XML 格式化工具</a>。我们会持续添加对实际工作有帮助的浏览器端工具，运营理念请参阅<a href="{about}">关于本站</a>页面。'),
            ("如何反馈错误或提出功能建议?", '请通过<a href="{contact}">联系我们</a>页面与我们联系，我们会查看每一条反馈。'),
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
}

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
                     tool_xml=urls["tool_xml"], faq=urls["faq"], contact=urls["contact"],
                     terms=urls["terms"], updates=urls["updates"])


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
    for l in LANGS:
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


OG_LOCALE = {"en": "en_US", "ko": "ko_KR", "ja": "ja_JP", "zh": "zh_CN"}

THEME_COLOR_LIGHT = "#ffffff"
THEME_COLOR_DARK = "#14161a"


def head_block(lang, page_key, title, description, keywords=None, og_title=None, og_description=None,
               robots="index, follow", extra=""):
    urls = urls_for(lang)
    canonical = SITE_DOMAIN + urls[page_key]
    kw = ('<meta name="keywords" content="%s" />\n' % keywords) if keywords else ""
    og_img = "%s/assets/img/og-%s.png" % (SITE_DOMAIN, lang)
    alt_locales = "\n".join(
        '<meta property="og:locale:alternate" content="%s" />' % OG_LOCALE[l] for l in LANGS if l != lang
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
         SITE_NAME[lang], final_og_title, final_og_desc, canonical, og_img,
         OG_LOCALE[lang], alt_locales, final_og_title, final_og_desc, og_img,
         hreflang_links(page_key), ICON_DATA_URI,
         theme_fouc_script(), lang_detect_script(lang), extra)


def lang_switcher(lang, current_page_key):
    urls_by_lang = {l: urls_for(l)[current_page_key] for l in LANGS}
    items = []
    for l in LANGS:
        cur = ' aria-current="true"' if l == lang else ""
        items.append(
            '<li><a href="%s" data-lang-option="%s"%s>%s <span>%s</span></a></li>'
            % (urls_by_lang[l], l, cur, LANG_META[l]["flag"], LANG_META[l]["label"])
        )
    return '''<div class="lang-switch" data-lang-switch>
        <button class="lang-switch-toggle" type="button" data-lang-toggle aria-haspopup="true" aria-expanded="false" aria-label="%s">%s</button>
        <ul class="lang-switch-menu" data-lang-menu hidden>
          %s
        </ul>
      </div>''' % (NAV[lang]["lang"], LANG_META[lang]["flag"], "\n          ".join(items))


def header_nav(lang, active_key, asset_home="/"):
    urls = urls_for(lang)
    n = NAV[lang]
    def cur(key):
        return ' aria-current="page"' if key == active_key else ""
    tool_links = "\n      ".join(
        '<li><a href="%s"%s>%s</a></li>' % (urls[url_key], cur(url_key), n[nav_key])
        for url_key, nav_key in TOOL_NAV_ITEMS
    )
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
      <li><a href="%s"%s>%s</a></li>
      <li><a href="%s"%s>%s</a></li>
    </ul>
    <div class="nav-right">
      %s
      <button class="theme-toggle" type="button" data-theme-toggle aria-pressed="false" aria-label="%s">\U0001F319</button>
    </div>
  </div>
</header>''' % (n["skip"], urls["home"], SITE_NAME[lang], n["menu"],
                 urls["home"], cur("home"), n["home"],
                 tool_links,
                 urls["about"], cur("about"), n["about"],
                 urls["privacy"], cur("privacy"), n["privacy"],
                 lang_switcher(lang, active_key), n["dark"])


def footer_block(lang):
    urls = urls_for(lang)
    n = NAV[lang]
    tool_links = "\n      ".join(
        '<a href="%s">%s</a>' % (urls[url_key], n[nav_key]) for url_key, nav_key in TOOL_NAV_ITEMS
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
      <button type="button" class="footer-settings-btn" data-cookie-settings>%s</button>
    </nav>
  </div>
</footer>

<script src="/assets/js/main.js"></script>
<script src="/assets/js/i18n.js"></script>
<script src="/assets/js/consent.js"></script>
<script>document.getElementById("footer-year").textContent = new Date().getFullYear();</script>''' % (
        SITE_NAME[lang], page_links, tool_links, n["cookie_settings"])


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
    cards = '''<article class="tool-card">
        <div class="tool-card-icon">\U0001F9E9</div>
        <h3><a href="%s">%s</a></h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </article>

      <article class="tool-card">
        <div class="tool-card-icon">\U0001F4C4</div>
        <h3><a href="%s">%s</a></h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </article>

      <article class="tool-card is-soon" aria-disabled="true">
        <div class="tool-card-icon">\U0001F6E0️</div>
        <h3>%s</h3>
        <p>%s</p>
        <span class="tag">%s</span>
      </article>''' % (urls["tool"], c["card1_title"], c["card1_desc"], c["card1_tag"],
                        urls["tool_xml"], c["card2_title"], c["card2_desc"], c["card2_tag"],
                        c["card3_title"], c["card3_desc"], c["card3_tag"])
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

  <section class="section-tight container prose">
    <h2>%s</h2>
    <ul>
      %s
    </ul>
  </section>
</main>

''' % (c["eyebrow"], c["h1"], c["hero_p"], c["features_h2"], c["features_p"], cards, c["why_h2"], why_items) + footer_block(lang)
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
       c["s3_h2"], fmt(c["s3_item"], urls), fmt(c["s3_item2"], urls), c["s3_p"], c["s4_h2"], fmt(c["s4_p"], urls),
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
       c["s1_h2"], c["s1_p1"], c["s1_p2"],
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


def render_tool_page(lang, content_key, page_key, id_prefix, css_href, js_src):
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
      <li><a href="%(related_url)s">%(related_link_text)s</a></li>
      <li><a href="%(faq_url)s">%(faq_link_text)s</a></li>
    </ul>
  </div>
</main>

''' % dict(**c, usage_lis=usage_lis, tips_lis=tips_lis, related_h2=n["related_h2"],
       related_url=(urls["tool_xml"] if page_key == "tool" else urls["tool"]),
       related_link_text=(n["tool_xml"] if page_key == "tool" else n["tool"]),
       faq_url=urls["faq"], faq_link_text=n["faq"]) + footer_block(lang)
    if id_prefix != "json":
        body = body.replace('"json-', '"' + id_prefix + '-')
    body = body.replace('<script src="/assets/js/main.js"></script>\n<script src="/assets/js/i18n.js"></script>',
                         '<script src="/assets/js/main.js"></script>\n<script src="%s"></script>\n<script src="/assets/js/i18n.js"></script>' % js_src)
    return page_wrap(lang, head, body)


def render_tool(lang):
    return render_tool_page(lang, "tool", "tool", "json", "/tools/json-formatter.css", "/tools/json-formatter.js")


def render_tool_xml(lang):
    return render_tool_page(lang, "tool_xml", "tool_xml", "xml", "/tools/xml-formatter.css", "/tools/xml-formatter.js")


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

    # sitemap.xml (404는 noindex이므로 제외)
    import datetime
    today = datetime.date.today().isoformat()
    priority_map = {"home": "1.0", "about": "0.6", "privacy": "0.3", "faq": "0.5", "contact": "0.4",
                     "terms": "0.3", "updates": "0.5", "tool": "0.9", "tool_xml": "0.9"}
    changefreq_map = {"home": "weekly", "about": "monthly", "privacy": "yearly", "faq": "monthly", "contact": "yearly",
                       "terms": "yearly", "updates": "weekly", "tool": "weekly", "tool_xml": "weekly"}
    url_entries = []
    for page_key in ["home", "about", "privacy", "faq", "contact", "terms", "updates", "tool", "tool_xml"]:
        for lang in LANGS:
            loc = SITE_DOMAIN + urls_for(lang)[page_key]
            alt_links = "\n".join(
                '    <xhtml:link rel="alternate" hreflang="%s" href="%s%s" />' % (
                    LANG_META[l]["html_lang"], SITE_DOMAIN, urls_for(l)[page_key])
                for l in LANGS
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
