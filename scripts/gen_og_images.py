#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
og:image용 소셜 공유 배너(1200x630)를 언어별로 생성.
브랜드 컬러(#2f6feb) 그라디언트 배경 + 로고 마크 + 사이트명 + 짧은 태그라인.
실행: python3 scripts/gen_og_images.py
출력: assets/img/og-<lang>.png (en/ko/ja/zh)
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "img")
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 1200, 630
COLOR_TOP = (47, 111, 235)     # #2f6feb
COLOR_BOTTOM = (24, 58, 130)   # darker blue

FONT_CJK_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_LATIN_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_LATIN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SITE_NAME = {"en": "WebToolBox", "ko": "웹툴박스", "ja": "ウェブツールボックス", "zh": "网页工具箱"}
TAGLINE = {
    "en": "Free Online Developer Tools",
    "ko": "브라우저에서 바로 쓰는 무료 개발자 도구",
    "ja": "ブラウザですぐ使える無料開発者ツール",
    "zh": "免费在线开发者工具",
}


def font_for(lang, size, bold=True):
    path = FONT_CJK_BOLD if lang in ("ko", "ja", "zh") else (FONT_LATIN_BOLD if bold else FONT_LATIN)
    return ImageFont.truetype(path, size)


def make_gradient(w, h, top, bottom):
    base = Image.new("RGB", (w, h), top)
    top_arr = top
    bottom_arr = bottom
    draw = ImageDraw.Draw(base)
    for y in range(h):
        t = y / (h - 1)
        r = int(top_arr[0] + (bottom_arr[0] - top_arr[0]) * t)
        g = int(top_arr[1] + (bottom_arr[1] - top_arr[1]) * t)
        b = int(top_arr[2] + (bottom_arr[2] - top_arr[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return base


def rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def build(lang):
    img = make_gradient(W, H, COLOR_TOP, COLOR_BOTTOM)
    draw = ImageDraw.Draw(img)

    # subtle decorative circles
    draw.ellipse([W - 260, -140, W + 220, 320], fill=(255, 255, 255, 0))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse([W - 260, -160, W + 260, 300], fill=(255, 255, 255, 18))
    odraw.ellipse([-200, H - 260, 220, H + 200], fill=(255, 255, 255, 14))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # logo mark (rounded square with "W")
    mark_size = 132
    mark_x, mark_y = 100, 165
    rounded_rect(draw, [mark_x, mark_y, mark_x + mark_size, mark_y + mark_size], 30, (255, 255, 255))
    wf = font_for("en", 84, bold=True)
    bbox = draw.textbbox((0, 0), "W", font=wf)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((mark_x + (mark_size - tw) / 2 - bbox[0], mark_y + (mark_size - th) / 2 - bbox[1]), "W",
               font=wf, fill=COLOR_TOP)

    # site name
    name_font = font_for(lang, 74, bold=True)
    name_x = mark_x + mark_size + 40
    name_y = 180
    draw.text((name_x, name_y), SITE_NAME[lang], font=name_font, fill=(255, 255, 255))

    # tagline
    tag_font = font_for(lang, 34, bold=False)
    draw.text((100, 372), TAGLINE[lang], font=tag_font, fill=(230, 236, 250))

    # bottom thin accent line + small dev-tool motif dots
    for idx, cx in enumerate([100, 140, 180]):
        draw.ellipse([cx, 470, cx + 16, 486], fill=(255, 255, 255, 200))

    out_path = os.path.join(OUT_DIR, "og-%s.png" % lang)
    img.save(out_path, "PNG", optimize=True)
    print("wrote", out_path)


if __name__ == "__main__":
    for l in ["en", "ko", "ja", "zh"]:
        build(l)
