#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹툴박스 다국어 정적 사이트 생성기.

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
SITE_DOMAIN = "https://example.com"  # 실제 배포 도메인이 정해지면 이 값만 바꾸면 됩니다.

LANGS = ["en", "ko", "ja", "zh"]
DEFAULT_LANG = "en"

LANG_META = {
    "en": {"label": "English", "flag": "\U0001F1FA\U0001F1F8", "html_lang": "en"},
    "ko": {"label": "한국어", "flag": "\U0001F1F0\U0001F1F7", "html_lang": "ko"},
    "ja": {"label": "日本語", "flag": "\U0001F1EF\U0001F1F5", "html_lang": "ja"},
    "zh": {"label": "中文", "flag": "\U0001F1E8\U0001F1F3", "html_lang": "zh-CN"},
}

SITE_NAME = {"en": "WebToolBox", "ko": "웹툴박스", "ja": "ウェブツールボックス", "zh": "网页工具箱"}

CONTACT_EMAIL = "hongsh119@gmail.com"

ICON_DATA_URI = (
    'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22>'
    '<rect width=%22100%22 height=%22100%22 rx=%2222%22 fill=%22%232f6feb%22/>'
    '<text x=%2250%22 y=%2266%22 font-size=%2258%22 font-family=%22sans-serif%22 font-weight=%22800%22 '
    'text-anchor=%22middle%22 fill=%22white%22>W</text></svg>'
)


def lang_prefix(lang):
    return "" if lang == DEFAULT_LANG else "/" + lang


def urls_for(lang):
    p = lang_prefix(lang)
    return {
        "home": p + "/",
        "about": p + "/about.html",
        "privacy": p + "/privacy.html",
        "tool": p + "/tools/json-formatter.html",
        "notfound": p + "/404.html",
    }


NAV = {
    "en": {"home": "Home", "tool": "JSON Formatter", "about": "About", "privacy": "Privacy Policy",
           "menu": "Open menu", "dark": "Switch to dark mode", "light": "Switch to light mode",
           "lang": "Select language", "skip": "Skip to content"},
    "ko": {"home": "홈", "tool": "JSON 포매터", "about": "사이트 소개", "privacy": "개인정보처리방침",
           "menu": "메뉴 열기", "dark": "다크 모드로 전환", "light": "라이트 모드로 전환",
           "lang": "언어 선택", "skip": "본문으로 건너뛰기"},
    "ja": {"home": "ホーム", "tool": "JSONフォーマッター", "about": "サイト紹介", "privacy": "プライバシーポリシー",
           "menu": "メニューを開く", "dark": "ダークモードに切り替え", "light": "ライトモードに切り替え",
           "lang": "言語選択", "skip": "本文へスキップ"},
    "zh": {"home": "首页", "tool": "JSON 格式化", "about": "关于本站", "privacy": "隐私政策",
           "menu": "打开菜单", "dark": "切换到深色模式", "light": "切换到浅色模式",
           "lang": "选择语言", "skip": "跳转到正文"},
}

# ---------------------------------------------------------------------------
# 페이지별 콘텐츠. {placeholder} 는 urls_for(lang) 값으로 치환됩니다.
# ---------------------------------------------------------------------------
CONTENT = {}

CONTENT["index"] = {
    "en": dict(
        title="WebToolBox | Free Online Developer Tools You Can Use Instantly",
        description="Free online tools you can use right in your browser — no sign-up required. Validate and beautify JSON with the JSON Formatter. Your data is processed locally and never sent to a server.",
        keywords="online tools, JSON formatter, JSON viewer, JSON validator, web utilities, free developer tools",
        og_title="WebToolBox | Free Online Developer Tools",
        og_description="Free online tools including a JSON Formatter, usable right in your browser. Your data is never stored on our servers.",
        eyebrow="FREE ONLINE TOOLS",
        h1="Browser-based online tools.<br />No install, no sign-up.",
        hero_p="WebToolBox is a free collection of online utilities for the small, everyday tasks that come up during development and work. Everything you enter is processed only on your own computer (in your browser) and is never sent to a server.",
        features_h2="Available tools",
        features_p="Try the tool below right away — more tools are on the way.",
        card1_title="JSON Formatter / Viewer",
        card1_desc="Checks whether your input is valid JSON and displays it as a readable, syntax-highlighted tree. Includes collapsible nodes and key/value search.",
        card1_tag="JSON · Formatter · Validator",
        card2_title="More tools coming soon",
        card2_desc="Text/encoding conversion, case conversion, and more tools will be added over time.",
        card2_tag="Coming soon",
        why_h2="Why WebToolBox?",
        why_items=[
            ("No install or sign-up", "Just open the link and start using it right away."),
            ("Processed in your browser", "Your input is handled entirely on the client side and is never sent to a server."),
            ("Dark mode support", "Switch between light and dark themes anytime using the toggle in the top right."),
            ("Continuously expanding", "We plan to keep adding tools that are useful for everyday development and work."),
        ],
    ),
    "ko": dict(
        title="웹툴박스 | 브라우저에서 바로 쓰는 무료 온라인 개발자 도구 모음",
        description="회원가입 없이 브라우저에서 바로 사용하는 무료 온라인 도구 모음. JSON 포매터로 JSON 문자열을 검증하고 보기 좋게 정리하세요. 데이터는 서버로 전송되지 않고 내 브라우저 안에서만 처리됩니다.",
        keywords="온라인 도구, JSON 포매터, JSON 뷰어, JSON validator, 웹 유틸리티, 무료 개발자 도구",
        og_title="웹툴박스 | 무료 온라인 개발자 도구 모음",
        og_description="JSON 포매터를 비롯해 브라우저에서 바로 쓰는 무료 온라인 도구를 제공합니다. 데이터는 서버에 저장되지 않습니다.",
        eyebrow="FREE ONLINE TOOLS",
        h1="설치도, 가입도 필요 없는<br />브라우저 기반 온라인 도구 모음",
        hero_p="웹툴박스는 개발과 업무 중 자주 필요한 자잔한 작업들을 브라우저에서 바로 끝낼 수 있게 만든 무료 온라인 유틸리티 모음입니다. 입력한 데이터는 서버로 전송되지 않고 내 컴퓨터(브라우저) 안에서만 처리되어 안전하게 사용할 수 있습니다.",
        features_h2="제공 기능",
        features_p="아래 기능을 바로 사용해보세요. 새로운 도구는 계속 추가될 예정입니다.",
        card1_title="JSON 포매터 / 뷰어",
        card1_desc="입력한 문자열이 올바른 JSON인지 검사하고, 들여쓰기와 문법 강조를 적용해 가독성 좋게 보여줍니다. 트리 접기/펼치기와 키·값 검색 기능을 제공합니다.",
        card1_tag="JSON · Formatter · Validator",
        card2_title="다음 도구 준비 중",
        card2_desc="텍스트/인코딩 변환, 대소문자 변환 등 새로운 도구를 순차적으로 추가할 예정입니다.",
        card2_tag="Coming soon",
        why_h2="왜 웹툴박스인가요?",
        why_items=[
            ("설치·가입 불필요", "링크만 열면 바로 사용할 수 있습니다."),
            ("브라우저 내 처리", "입력한 데이터를 서버로 전송하지 않고 클라이언트에서만 처리합니다."),
            ("다크 모드 지원", "화면 우측 상단 토글로 언제든 라이트/다크 테마를 전환할 수 있습니다."),
            ("지속적인 기능 추가", "자주 쓰는 개발/업무 도구를 계속 확장해 나갈 예정입니다."),
        ],
    ),
    "ja": dict(
        title="ウェブツールボックス | インストール不要の無料オンライン開発者ツール集",
        description="会員登録不要でブラウザ上ですぐ使える無料のオンラインツール集。JSONフォーマッターでJSON文字列を検証し、読みやすく整形して表示します。データはサーバーに送信されず、ブラウザ内でのみ処理されます。",
        keywords="オンラインツール, JSONフォーマッター, JSONビューア, JSON validator, ウェブユーティリティ, 無料開発者ツール",
        og_title="ウェブツールボックス | 無料オンライン開発者ツール集",
        og_description="JSONフォーマッターをはじめ、ブラウザですぐ使える無料オンラインツールを提供します。データはサーバーに保存されません。",
        eyebrow="FREE ONLINE TOOLS",
        h1="インストールも登録も不要な<br />ブラウザ完結型オンラインツール集",
        hero_p="ウェブツールボックスは、開発や業務中によく必要になる細かな作業をブラウザ上ですぐに済ませられるようにした無料のオンラインユーティリティ集です。入力したデータはサーバーに送信されず、お使いのコンピューター（ブラウザ）内でのみ処理されるため、安心してご利用いただけます。",
        features_h2="提供機能",
        features_p="下記の機能をすぐにお試しください。新しいツールも順次追加していく予定です。",
        card1_title="JSONフォーマッター / ビューア",
        card1_desc="入力した文字列が正しいJSONかどうかを検証し、インデントとシンタックスハイライトを適用して読みやすく表示します。ツリーの折りたたみ/展開とキー・値の検索機能を提供します。",
        card1_tag="JSON · Formatter · Validator",
        card2_title="次のツールを準備中",
        card2_desc="テキスト/エンコード変換、大文字小文字変換など、新しいツールを順次追加していく予定です。",
        card2_tag="Coming soon",
        why_h2="なぜウェブツールボックスなのか?",
        why_items=[
            ("インストール・登録不要", "リンクを開くだけですぐに利用できます。"),
            ("ブラウザ内処理", "入力したデータをサーバーに送信せず、クライアント側だけで処理します。"),
            ("ダークモード対応", "画面右上のトグルでライト/ダークテーマをいつでも切り替えられます。"),
            ("継続的な機能追加", "よく使う開発・業務ツールを今後も追加していく予定です。"),
        ],
    ),
    "zh": dict(
        title="网页工具箱 | 无需安装即可使用的免费在线开发者工具",
        description="无需注册，直接在浏览器中使用的免费在线工具集。使用 JSON 格式化工具验证 JSON 字符串并以易读的方式展示。数据不会发送到服务器，仅在您的浏览器中处理。",
        keywords="在线工具, JSON 格式化, JSON 查看器, JSON validator, 网页工具, 免费开发者工具",
        og_title="网页工具箱 | 免费在线开发者工具",
        og_description="提供 JSON 格式化等可在浏览器中直接使用的免费在线工具，数据不会保存在服务器上。",
        eyebrow="FREE ONLINE TOOLS",
        h1="无需安装、无需注册的<br />浏览器端在线工具集",
        hero_p="网页工具箱是一套免费的在线实用工具集合，帮助你在开发和工作中快速完成各种琐碎任务。你输入的数据不会发送到服务器，只会在你自己的电脑（浏览器）中处理，可以放心使用。",
        features_h2="提供的功能",
        features_p="立即体验下面的功能，我们会持续添加新的工具。",
        card1_title="JSON 格式化 / 查看器",
        card1_desc="检查输入的字符串是否为有效的 JSON，并以带缩进和语法高亮的树形结构清晰展示。支持节点折叠/展开以及键值搜索功能。",
        card1_tag="JSON · Formatter · Validator",
        card2_title="更多工具即将上线",
        card2_desc="文本/编码转换、大小写转换等新工具将陆续添加。",
        card2_tag="Coming soon",
        why_h2="为什么选择网页工具箱?",
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
        title="About | WebToolBox",
        description="WebToolBox is a free collection of online developer tools you can use right in your browser, no sign-up required. Learn about the service, its principles, and available features.",
        og_title="About | WebToolBox",
        og_description="An introduction to WebToolBox and the principles behind it.",
        h1="About", lead="An introduction to what WebToolBox is and the principles it's run by.",
        s1_h2="What is WebToolBox?",
        s1_p='WebToolBox is a free collection of online utilities that lets you handle small but tedious tasks you often run into during development or work, directly in your web browser — no separate program to install, no sign-up required. The first tool we offer is the <a href="{tool}">JSON Formatter</a>, and we plan to keep adding tools that are genuinely useful in everyday work.',
        s2_h2="Our principles",
        s2_items=[
            ("Use it instantly, no sign-up", "Anyone can start using it immediately — no account or login required."),
            ("Client-side processing", 'Most tools process your input entirely in the browser (JavaScript) and never send it to a server. See our <a href="{privacy}">Privacy Policy</a> for details.'),
            ("Light and fast", "We aim for a simple screen that cuts unnecessary elements and focuses on the features you actually need."),
            ("Dark mode built in", "Choose between light and dark themes, either automatically from your system settings or manually with the toggle."),
        ],
        s3_h2="Available features",
        s3_item='<a href="{tool}">JSON Formatter / Viewer</a> — Validates JSON strings and displays them as an indented, syntax-highlighted tree. Supports collapsing/expanding nodes and searching keys and values.',
        s3_p="Suggestions for new features or improvements are always welcome.",
        s4_h2="About advertising and running this service",
        s4_p='WebToolBox may introduce advertising services such as Google AdSense in the future to help support running the site. If we do, how related data is handled will be explained transparently on the <a href="{privacy}">Privacy Policy</a> page, and the core functionality of our tools (e.g. JSON processing) will remain free regardless of whether ads are shown.',
        s5_h2="Contact",
        s5_p="For bug reports, feature requests, or any other inquiries, please reach out at the email below.",
    ),
    "ko": dict(
        title="사이트 소개 | 웹툴박스",
        description="웹툴박스는 회원가입 없이 브라우저에서 바로 쓰는 무료 온라인 개발자 도구 모음입니다. 서비스 소개와 운영 철학, 제공 중인 기능을 안내합니다.",
        og_title="사이트 소개 | 웹툴박스",
        og_description="웹툴박스 서비스 소개와 운영 철학을 안내합니다.",
        h1="사이트 소개", lead="웹툴박스가 어떤 서비스인지, 어떤 원칙으로 운영되는지 소개합니다.",
        s1_h2="웹툴박스란?",
        s1_p='웹툴박스(WebToolBox)는 개발이나 업무 중 자주 마주하지만 번거로운 작업을 별도 프로그램 설치나 회원가입 없이, 웹 브라우저에서 바로 처리할 수 있도록 만든 무료 온라인 유틸리티 모음입니다. 첫 번째로 제공하는 기능은 <a href="{tool}">JSON 포매터</a>이며, 앞으로도 실무에 도움이 되는 도구를 지속적으로 추가할 예정입니다.',
        s2_h2="운영 원칙",
        s2_items=[
            ("가입 없이 바로 사용", "별도의 계정이나 로그인 없이 누구나 즉시 이용할 수 있습니다."),
            ("클라이언트 사이드 처리", '대부분의 도구는 입력값을 서버로 전송하지 않고 브라우저(자바스크립트) 안에서만 처리합니다. 자세한 내용은 <a href="{privacy}">개인정보처리방침</a>을 참고해주세요.'),
            ("가벼고 빠른 화면", "불필요한 요소를 줄이고 필요한 기능에 집중한 단순한 화면을 지향합니다."),
            ("다크 모드 기본 지원", "시스템 설정 또는 수동 전환으로 라이트/다크 테마를 선택할 수 있습니다."),
        ],
        s3_h2="제공 중인 기능",
        s3_item='<a href="{tool}">JSON 포매터 / 뷰어</a> — JSON 문자열의 유효성을 검사하고, 들여쓰기·문법 강조가 적용된 트리 형태로 보여줍니다. 노드 접기/펼치기와 키·값 검색을 지원합니다.',
        s3_p="새로운 기능 제안이나 개선 의견은 언제든 환영합니다.",
        s4_h2="광고 및 서비스 운영에 대해",
        s4_p='웹툴박스는 서비스 운영을 위해 향후 Google AdSense 등 광고 서비스를 도입할 수 있습니다. 광고 도입 시 관련 데이터 처리 방식은 <a href="{privacy}">개인정보처리방침</a> 페이지를 통해 투명하게 안내하며, 도구의 핵심 기능(예: JSON 처리)은 광고 여부와 무관하게 계속 무료로 제공됩니다.',
        s5_h2="문의", s5_p="버그 제보, 기능 제안, 기타 문의는 아래 이메일로 연락해 주세요.",
    ),
    "ja": dict(
        title="サイト紹介 | ウェブツールボックス",
        description="ウェブツールボックスは会員登録不要でブラウザ上ですぐ使える無料のオンライン開発者ツール集です。サービス紹介、運営方針、提供機能をご案内します。",
        og_title="サイト紹介 | ウェブツールボックス",
        og_description="ウェブツールボックスのサービス紹介と運営方針をご案内します。",
        h1="サイト紹介", lead="ウェブツールボックスがどのようなサービスか、どのような方針で運営されているかをご紹介します。",
        s1_h2="ウェブツールボックスとは?",
        s1_p='ウェブツールボックス(WebToolBox)は、開発や業務でよく発生する細かくて面倒な作業を、別途プログラムのインストールや会員登録なしに、ウェブブラウザ上ですぐに処理できるようにした無料のオンラインユーティリティ集です。最初に提供する機能は<a href="{tool}">JSONフォーマッター</a>で、今後も実務に役立つツールを継続的に追加していく予定です。',
        s2_h2="運営方針",
        s2_items=[
            ("登録不要ですぐ使える", "アカウントやログインなしで誰でもすぐに利用できます。"),
            ("クライアントサイド処理", 'ほとんどのツールは入力値をサーバーに送信せず、ブラウザ(JavaScript)内でのみ処理します。詳しくは<a href="{privacy}">プライバシーポリシー</a>をご覚ください。'),
            ("軸くて速い画面", "不要な要素を減らし、必要な機能に集中したシンプルな画面を目指しています。"),
            ("ダークモード標準対応", "システム設定または手動切り替えでライト/ダークテーマを選択できます。"),
        ],
        s3_h2="提供中の機能",
        s3_item='<a href="{tool}">JSONフォーマッター / ビューア</a> — JSON文字列の妥当性を検証し、インデントとシンタックスハイライトを適用したツリー形式で表示します。ノードの折りたたみ/展開、キー・値の検索に対応しています。',
        s3_p="新機能のご提案や改善のご意見はいつでも歓迎します。",
        s4_h2="広告およびサービス運営について",
        s4_p='ウェブツールボックスはサービス運営のため、今後 Google AdSense などの広告サービスを導入する場合があります。導入時の関連データの取り扱いは<a href="{privacy}">プライバシーポリシー</a>ページで透明性を持ってご案内し、ツールの中核機能(JSON処理など)は広告の有無にかかわらず引き続き無料で提供します。',
        s5_h2="お問い合わせ", s5_p="不具合報告、機能提案、その他のお問い合わせは下記メールアドレスまでご連絡ください。",
    ),
    "zh": dict(
        title="关于本站 | 网页工具箱",
        description="网页工具箱是无需注册即可在浏览器中直接使用的免费在线开发者工具集。介绍服务内容、运营理念和已提供的功能。",
        og_title="关于本站 | 网页工具箱",
        og_description="介绍网页工具箱的服务内容与运营理念。",
        h1="关于本站", lead="介绍网页工具箱是一项怎样的服务，以及它的运营理念。",
        s1_h2="什么是网页工具箱?",
        s1_p='网页工具箱(WebToolBox)是一套免费的在线实用工具集，让你无需安装额外程序、无需注册账号，就能在网页浏览器中直接处理开发或工作中常见的琐碎任务。首个提供的功能是<a href="{tool}">JSON 格式化工具</a>，未来还会持续添加对实际工作有帮助的工具。',
        s2_h2="运营理念",
        s2_items=[
            ("无需注册，立即使用", "任何人无需账号或登录即可立即使用。"),
            ("客户端处理", '大多数工具不会将输入内容发送到服务器，仅在浏览器(JavaScript)中处理。详情请参阅<a href="{privacy}">隐私政策</a>。'),
            ("轻量快速的界面", "减少不必要的元素，专注于真正需要的功能，力求界面简洁。"),
            ("默认支持深色模式", "可根据系统设置自动切换，或手动在浅色/深色主题之间切换。"),
        ],
        s3_h2="已提供的功能",
        s3_item='<a href="{tool}">JSON 格式化 / 查看器</a> — 验证 JSON 字符串的有效性，并以带缩进和语法高亮的树形结构展示。支持节点折叠/展开以及键值搜索。',
        s3_p="欢迎随时提出新功能建议或改进意见。",
        s4_h2="关于广告与服务运营",
        s4_p='为了维持服务运营，网页工具箱未来可能会引入 Google AdSense 等广告服务。如果引入广告，相关数据的处理方式将在<a href="{privacy}">隐私政策</a>页面中透明说明，工具的核心功能(如 JSON 处理)将始终免费提供，不受广告影响。',
        s5_h2="联系方式", s5_p="如有错误反馈、功能建议或其他咨询，请通过以下邮箱联系我们。",
    ),
}

CONTENT["privacy"] = {
    "en": dict(
        title="Privacy Policy | WebToolBox",
        description="WebToolBox's privacy policy. Explains what information we collect, our use of cookies/local storage, and how data is handled in relation to advertising (Google AdSense).",
        og_title="Privacy Policy | WebToolBox",
        og_description="Information on WebToolBox's collection and use of personal data and our use of cookies.",
        h1="Privacy Policy", effective="Effective date: September 20, 2026",
        intro='WebToolBox (the "Site") values its users\' privacy and strives to comply with applicable data protection laws. This policy explains what information the Site collects and how it is used.',
        s1_h2="1. Information processed and how",
        s1_p1="Tools provided on the Site, such as the JSON Formatter, process the text you enter entirely within your browser (JavaScript) and never send it to a server. In other words, the JSON data or text you input is never transmitted to or stored by the Site operator.",
        s1_p2="Simple preference settings, such as your theme choice (light/dark mode), are stored only in your browser's local storage (localStorage) and are never transmitted externally.",
        s2_h2="2. Use of cookies and similar technologies",
        s2_p1="The Site may use cookies for service analytics and advertising purposes. A cookie is a small piece of information a website stores in your browser; you can refuse or delete cookies through your browser settings. Note that refusing cookies may limit some features.",
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
        title="개인정보처리방침 | 웹툴박스",
        description="웹툴박스의 개인정보처리방침입니다. 수집하는 정보, 쿠키·로컬스토리지 사용, 광고(Google AdSense) 관련 데이터 처리 방식을 안내합니다.",
        og_title="개인정보처리방침 | 웹툴박스",
        og_description="웹툴박스의 개인정보 수집·이용 및 쿠키 사용에 대한 안내입니다.",
        h1="개인정보처리방침", effective="시행일자: 2026년 9월 20일",
        intro='웹툴박스(이하 "사이트")는 이용자의 개인정보를 소중히 여기며, 개인정보 보호법 등 관련 법령을 준수하기 위해 노력합니다. 본 방침은 사이트가 어떤 정보를 어떻게 수집·이용하는지 설명합니다.',
        s1_h2="1. 처리하는 정보 및 처리 방식",
        s1_p1="사이트에서 제공하는 JSON 포매터 등 도구는 입력하신 텍스트를 서버로 전송하지 않고 이용자의 브라우저(자바스크립트) 내에서만 처리합니다. 즉, 입력한 JSON 데이터나 텍스트는 사이트 운영자에게 전달되거나 저장되지 않습니다.",
        s1_p2="다만 화면 테마 설정(라이트/다크 모드)과 같은 단순 환경설정 값은 이용자의 브라우저 로컬 스토리지(localStorage)에만 저장되며, 이 정보는 외부로 전송되지 않습니다.",
        s2_h2="2. 쿠키(Cookie) 및 유사 기술의 사용",
        s2_p1="사이트는 서비스 이용 분석 및 광고 제공을 위해 쿠키를 사용할 수 있습니다. 쿠키는 웹사이트가 이용자의 브라우저에 저장하는 소량의 정보로, 이용자는 브라우저 설정을 통해 쿠키 저장을 거부하거나 삭제할 수 있습니다. 다만 쿠키 저장을 거부할 경우 일부 기능 이용에 어려움이 있을 수 있습니다.",
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
        title="プライバシーポリシー | ウェブツールボックス",
        description="ウェブツールボックスのプライバシーポリシーです。収集する情報、Cookie・ローカルストレージの利用、広告(Google AdSense)に関するデータの取り扱いについてご案内します。",
        og_title="プライバシーポリシー | ウェブツールボックス",
        og_description="ウェブツールボックスの個人情報の収集・利用およびCookieの使用に関するご案内です。",
        h1="プライバシーポリシー", effective="施行日: 2026年9月20日",
        intro='ウェブツールボックス(以下「本サイト」)は、利用者のプライバシーを重視し、関連法令の遵守に努めます。本ポリシーでは、本サイトがどのような情報をどのように収集・利用するかを説明します。',
        s1_h2="1. 処理する情報と処理方法",
        s1_p1="本サイトが提供するJSONフォーマッターなどのツールは、入力されたテキストをサーバーに送信せず、利用者のブラウザ(JavaScript)内でのみ処理します。つまり、入力されたJSONデータやテキストがサイト運営者に送信・保存されることはありません。",
        s1_p2="画面テーマ設定(ライト/ダークモード)などの単純な環境設定値のみ、利用者のブラウザのローカルストレージ(localStorage)に保存され、この情報が外部に送信されることはありません。",
        s2_h2="2. Cookie(クッキー)および類似技術の使用",
        s2_p1="本サイトはサービス利用分析および広告配信のためにCookieを使用する場合があります。Cookieとはウェブサイトが利用者のブラウザに保存する少量の情報で、利用者はブラウザの設定でCookieの保存を拒否または削除できます。ただし、Cookieの保存を拒否した場合、一部機能のご利用に支障が生じる可能性があります。",
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
        title="隐私政策 | 网页工具箱",
        description="网页工具箱的隐私政策，说明我们收集的信息、Cookie 与本地存储的使用方式，以及与广告服务(Google AdSense)相关的数据处理方式。",
        og_title="隐私政策 | 网页工具箱",
        og_description="关于网页工具箱收集与使用个人信息及使用 Cookie 的说明。",
        h1="隐私政策", effective="生效日期：2026年9月20日",
        intro='网页工具箱(以下简称"本网站")重视用户隐私，并致力于遵守相关法律法规。本政策说明本网站收集哪些信息以及如何使用这些信息。',
        s1_h2="1. 处理的信息及处理方式",
        s1_p1="本网站提供的 JSON 格式化等工具，会将您输入的文本完全在您的浏览器(JavaScript)中处理，不会发送到服务器。也就是说，您输入的 JSON 数据或文本不会被传送给网站运营者或被保存。",
        s1_p2="仅主题设置(浅色/深色模式)等简单的偏好设置值会保存在您浏览器的本地存储(localStorage)中，该信息不会对外传输。",
        s2_h2="2. Cookie 及类似技术的使用",
        s2_p1="本网站可能会为服务分析和广告投放使用 Cookie。Cookie 是网站保存在您浏览器中的少量信息，您可以通过浏览器设置拒绝或删除 Cookie。但拒绝 Cookie 可能会影响部分功能的使用。",
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

CONTENT["notfound"] = {
    "en": dict(title="Page Not Found | WebToolBox", eyebrow="404", h1="Page Not Found",
                p="The page you requested may have been removed or its address may have changed.", back="Back to Home"),
    "ko": dict(title="페이지를 찾을 수 없습니다 | 웹툴박스", eyebrow="404", h1="페이지를 찾을 수 없습니다",
                p="요청하신 페이지가 삭제되었거나 주소가 변경되었을 수 있습니다.", back="홈으로 돌아가기"),
    "ja": dict(title="ページが見つかりません | ウェブツールボックス", eyebrow="404", h1="ページが見つかりません",
                p="お探しのページは削除されたか、URLが変更された可能性があります。", back="ホームに戻る"),
    "zh": dict(title="页面未找到 | 网页工具箱", eyebrow="404", h1="页面未找到",
                p="您访问的页面可能已被删除或地址已更改。", back="返回首页"),
}

CONTENT["tool"] = {
    "en": dict(
        title="JSON Formatter / Viewer - Validate and Beautify JSON Online | WebToolBox",
        description="Online JSON formatter. Checks whether your input is valid JSON and displays it as a readable, syntax-highlighted tree. Supports collapsing/expanding and key/value search; your data is processed only in your browser.",
        keywords="JSON formatter, JSON viewer, JSON validator, JSON beautify, JSON pretty print, online JSON tool",
        og_title="JSON Formatter / Viewer | WebToolBox",
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
    ),
    "ko": dict(
        title="JSON 포매터 / 뷰어 - 온라인 JSON 검증 및 정리 | 웹툴박스",
        description="온라인 JSON 포매터. 입력한 문자열이 올바른 JSON인지 검증하고, 들여쓰기와 문법 강조를 적용해 가독성 좋게 보여줍니다. 트리 접기/펼치기와 키·값 검색을 지원하며 데이터는 브라우저 안에서만 처리됩니다.",
        keywords="JSON 포매터, JSON 뷰어, JSON validator, JSON beautify, JSON pretty print, 온라인 JSON 도구",
        og_title="JSON 포매터 / 뷰어 | 웹툴박스",
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
    ),
    "ja": dict(
        title="JSONフォーマッター / ビューア - オンラインJSON検証・整形 | ウェブツールボックス",
        description="オンラインJSONフォーマッター。入力した文字列が正しいJSONかを検証し、インデントとシンタックスハイライトを適用して読みやすく表示します。折りたたみ/展開とキー・値検索に対応し、データはブラウザ内でのみ処理されます。",
        keywords="JSONフォーマッター, JSONビューア, JSON validator, JSON beautify, JSON pretty print, オンラインJSONツール",
        og_title="JSONフォーマッター / ビューア | ウェブツールボックス",
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
    ),
    "zh": dict(
        title="JSON 格式化 / 查看器 - 在线 JSON 验证与整理 | 网页工具箱",
        description="在线 JSON 格式化工具。检查输入的字符串是否为有效 JSON，并带缩进和语法高亮清晰展示。支持折叠/展开以及键值搜索，数据仅在浏览器中处理。",
        keywords="JSON 格式化, JSON 查看器, JSON validator, JSON beautify, JSON pretty print, 在线 JSON 工具",
        og_title="JSON 格式化 / 查看器 | 网页工具箱",
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
    return s.format(home=urls["home"], about=urls["about"], privacy=urls["privacy"], tool=urls["tool"])


def theme_fouc_script():
    return '''<script>
  (function () {
    try {
      var t = localStorage.getItem("wtb-theme");
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
      var stored = localStorage.getItem("wtb-lang");
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
        localStorage.setItem("wtb-lang", match);
        location.replace("/" + match + location.pathname + location.search);
      } else {
        localStorage.setItem("wtb-lang", "en");
      }
    } catch (e) {}
  })();
</script>'''
    else:
        return '''<script>
  try { localStorage.setItem("wtb-lang", "''' + lang + '''"); } catch (e) {}
</script>'''


def hreflang_links(page_key):
    links = []
    for l in LANGS:
        u = urls_for(l)[page_key]
        links.append('<link rel="alternate" hreflang="%s" href="%s%s" />' % (LANG_META[l]["html_lang"], SITE_DOMAIN, u))
    default_u = urls_for(DEFAULT_LANG)[page_key]
    links.append('<link rel="alternate" hreflang="x-default" href="%s%s" />' % (SITE_DOMAIN, default_u))
    return "\n".join(links)


def head_block(lang, page_key, title, description, keywords=None, og_title=None, og_description=None,
               robots="index, follow", extra=""):
    urls = urls_for(lang)
    canonical = SITE_DOMAIN + urls[page_key]
    kw = ('<meta name="keywords" content="%s" />\n' % keywords) if keywords else ""
    return '''<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>%s</title>
<meta name="description" content="%s" />
%s<link rel="canonical" href="%s" />
<meta name="robots" content="%s" />

<meta property="og:type" content="website" />
<meta property="og:site_name" content="%s" />
<meta property="og:title" content="%s" />
<meta property="og:description" content="%s" />
<meta property="og:url" content="%s" />
<meta name="twitter:card" content="summary" />

%s

<link rel="icon" href="%s" />
<link rel="stylesheet" href="/assets/css/style.css" />
%s
%s
%s''' % (title, description, kw, canonical, robots, SITE_NAME[lang], og_title or title,
         og_description or description, canonical, hreflang_links(page_key), ICON_DATA_URI,
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
    return '''<a class="skip-link" href="#main-content">%s</a>

<header class="site-header">
  <div class="container nav">
    <a class="nav-brand" href="%s">
      <span class="nav-brand-mark">W</span>
      %s
    </a>
    <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-nav" aria-label="%s">☰</button>
    <ul class="nav-links" id="primary-nav" data-nav-links>
      <li><a href="%s"%s>%s</a></li>
      <li><a href="%s"%s>%s</a></li>
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
                 urls["tool"], cur("tool"), n["tool"],
                 urls["about"], cur("about"), n["about"],
                 urls["privacy"], cur("privacy"), n["privacy"],
                 lang_switcher(lang, active_key), n["dark"])


def footer_block(lang):
    urls = urls_for(lang)
    n = NAV[lang]
    return '''<footer class="site-footer">
  <div class="container footer-inner">
    <span>&copy; <span id="footer-year">2026</span> %s. All rights reserved.</span>
    <nav class="footer-links">
      <a href="%s">%s</a>
      <a href="%s">%s</a>
      <a href="%s">%s</a>
    </nav>
  </div>
</footer>

<script src="/assets/js/main.js"></script>
<script src="/assets/js/i18n.js"></script>
<script>document.getElementById("footer-year").textContent = new Date().getFullYear();</script>''' % (
        SITE_NAME[lang], urls["about"], n["about"], urls["privacy"], n["privacy"], urls["tool"], n["tool"])


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
  "description": "%s"
}
</script>''' % (SITE_NAME[lang], SITE_DOMAIN + urls["home"], c["hero_p"][:120])
    head = head_block(lang, "home", c["title"], c["description"], c["keywords"], c["og_title"], c["og_description"], extra=jsonld)
    cards = '''<article class="tool-card">
        <div class="tool-card-icon">\U0001F9E9</div>
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
                        c["card2_title"], c["card2_desc"], c["card2_tag"])
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
    head = head_block(lang, "about", c["title"], c["description"], og_title=c["og_title"], og_description=c["og_description"])
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
       c["s3_h2"], fmt(c["s3_item"], urls), c["s3_p"], c["s4_h2"], fmt(c["s4_p"], urls),
       c["s5_h2"], c["s5_p"], CONTACT_EMAIL, CONTACT_EMAIL) + footer_block(lang)
    return page_wrap(lang, head, body)


def render_privacy(lang):
    c = CONTENT["privacy"][lang]
    head = head_block(lang, "privacy", c["title"], c["description"], og_title=c["og_title"], og_description=c["og_description"])
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
       c["s2_h2"], c["s2_p1"],
       c["s3_h2"], c["s3_p1"], c["s3_li1"], c["s3_li2"], c["s3_li3"], c["s3_p2"],
       c["s4_h2"], c["s4_p1"],
       c["s5_h2"], c["s5_p1"],
       c["s6_h2"], c["s6_p1"], CONTACT_EMAIL, CONTACT_EMAIL,
       c["s7_h2"], c["s7_p1"]) + footer_block(lang)
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
      <span class="nav-brand-mark">W</span>
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


def render_tool(lang):
    c = CONTENT["tool"][lang]
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
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
}
</script>''' % (c["jsonld_name"], SITE_DOMAIN + urls["tool"], c["jsonld_description"])
    head = head_block(lang, "tool", c["title"], c["description"], c["keywords"], c["og_title"], c["og_description"], extra=jsonld)
    head = head.replace('href="/assets/css/style.css" />', 'href="/assets/css/style.css" />\n<link rel="stylesheet" href="/tools/json-formatter.css" />')

    usage_lis = "\n      ".join("<li>%s</li>" % item for item in c["usage_items"])

    body = header_nav(lang, "tool") + '''

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
  </div>
</main>

''' % dict(**c, usage_lis=usage_lis) + footer_block(lang)
    body = body.replace('<script src="/assets/js/main.js"></script>\n<script src="/assets/js/i18n.js"></script>',
                         '<script src="/assets/js/main.js"></script>\n<script src="/tools/json-formatter.js"></script>\n<script src="/assets/js/i18n.js"></script>')
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
        written.append(write_file(prefix + "/404.html", render_notfound(lang)))
        written.append(write_file(prefix + "/tools/json-formatter.html", render_tool(lang)))

    # sitemap.xml (404는 noindex이므로 제외)
    url_entries = []
    for page_key in ["home", "about", "privacy", "tool"]:
        for lang in LANGS:
            loc = SITE_DOMAIN + urls_for(lang)[page_key]
            alt_links = "\n".join(
                '    <xhtml:link rel="alternate" hreflang="%s" href="%s%s" />' % (
                    LANG_META[l]["html_lang"], SITE_DOMAIN, urls_for(l)[page_key])
                for l in LANGS
            )
            alt_links += '\n    <xhtml:link rel="alternate" hreflang="x-default" href="%s%s" />' % (
                SITE_DOMAIN, urls_for(DEFAULT_LANG)[page_key])
            url_entries.append('  <url>\n    <loc>%s</loc>\n%s\n  </url>' % (loc, alt_links))
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

    print("Wrote %d files" % len(written))
    for w in written:
        print(" -", os.path.relpath(w, ROOT))


if __name__ == "__main__":
    build()
