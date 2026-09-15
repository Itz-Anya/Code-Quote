import datetime
import json
import mimetypes
import os
import random
import re
from xml.sax.saxutils import escape as xml_escape

from flask import Flask, Response, render_template, request, send_from_directory

mimetypes.add_type("application/manifest+json", ".webmanifest")

app = Flask(__name__)

CANONICAL_URL = "https://codequote.vercel.app"
GITHUB_URL = "https://github.com/Itz-Anya/Code-Quote"

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "public")

QUOTES_PATH = os.path.join(os.path.dirname(__file__), "quotes.json")

with open(QUOTES_PATH, "r", encoding="utf-8") as f:
    QUOTES = json.load(f)

FONT_STACKS = {
    "sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
    "serif": "Georgia, 'Times New Roman', serif",
    "mono": "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace",
}

PALETTES = {
    "dark": dict(
        bg_from="#0d1117", bg_to="#161b22", card_stroke="#30363d",
        title="#8b949e", quote="#e6edf3", author="#7ee787",
        accent_from="#7ee787", accent_to="#58a6ff",
    ),
    "light": dict(
        bg_from="#ffffff", bg_to="#f6f8fa", card_stroke="#d0d7de",
        title="#57606a", quote="#1f2328", author="#0969da",
        accent_from="#0969da", accent_to="#8250df",
    ),
    "github": dict(
        bg_from="#0d1117", bg_to="#161b22", card_stroke="#30363d",
        title="#8b949e", quote="#e6edf3", author="#7ee787",
        accent_from="#7ee787", accent_to="#58a6ff",
    ),
    "dracula": dict(
        bg_from="#282a36", bg_to="#21222c", card_stroke="#44475a",
        title="#6272a4", quote="#f8f8f2", author="#ff79c6",
        accent_from="#50fa7b", accent_to="#bd93f9",
    ),
    "nord": dict(
        bg_from="#2e3440", bg_to="#3b4252", card_stroke="#4c566a",
        title="#81a1c1", quote="#eceff4", author="#b48ead",
        accent_from="#a3be8c", accent_to="#88c0d0",
    ),
    "monokai": dict(
        bg_from="#272822", bg_to="#2d2e27", card_stroke="#49483e",
        title="#75715e", quote="#f8f8f2", author="#fd971f",
        accent_from="#a6e22e", accent_to="#66d9ef",
    ),
    "solarized": dict(
        bg_from="#002b36", bg_to="#073642", card_stroke="#586e75",
        title="#93a1a1", quote="#eee8d5", author="#b58900",
        accent_from="#859900", accent_to="#268bd2",
    ),
    "gruvbox": dict(
        bg_from="#282828", bg_to="#32302f", card_stroke="#504945",
        title="#a89984", quote="#ebdbb2", author="#fabd2f",
        accent_from="#b8bb26", accent_to="#83a598",
    ),
    "onedark": dict(
        bg_from="#282c34", bg_to="#21252b", card_stroke="#3e4451",
        title="#5c6370", quote="#abb2bf", author="#c678dd",
        accent_from="#98c379", accent_to="#61afef",
    ),
    "tokyonight": dict(
        bg_from="#1a1b26", bg_to="#16161e", card_stroke="#414868",
        title="#565f89", quote="#c0caf5", author="#bb9af7",
        accent_from="#9ece6a", accent_to="#7aa2f7",
    ),
    "catppuccin": dict(
        bg_from="#1e1e2e", bg_to="#181825", card_stroke="#313244",
        title="#a6adc8", quote="#cdd6f4", author="#f5c2e7",
        accent_from="#a6e3a1", accent_to="#89b4fa",
    ),
    "synthwave": dict(
        bg_from="#262335", bg_to="#241b2f", card_stroke="#495495",
        title="#848bbd", quote="#f4eee4", author="#ff7edb",
        accent_from="#72f1b8", accent_to="#fe4450",
    ),
    "ayu": dict(
        bg_from="#0f1419", bg_to="#131721", card_stroke="#232834",
        title="#5c6773", quote="#e6e1cf", author="#ffb454",
        accent_from="#b8cc52", accent_to="#59c2ff",
    ),
    "rosepine": dict(
        bg_from="#191724", bg_to="#1f1d2e", card_stroke="#403d52",
        title="#908caa", quote="#e0def4", author="#eb6f92",
        accent_from="#9ccfd8", accent_to="#c4a7e7",
    ),
}
DOT_COLORS = ("#ff5f56", "#ffbd2e", "#27c93f")

THEMES = set(PALETTES.keys())


def pick_quote(author_filter=None):
    pool = QUOTES
    if author_filter:
        needle = author_filter.strip().lower()
        filtered = [q for q in QUOTES if needle in q["author"].lower()]
        if filtered:
            pool = filtered
    return random.choice(pool)


def wrap_text(text, max_chars):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def clamp(value, low, high):
    return max(low, min(high, value))


def generate_svg(quote_text, author, theme="dark", width=600, font="sans"):
    theme = theme if theme in THEMES else "dark"
    font_family = FONT_STACKS.get(font, FONT_STACKS["sans"])
    width = clamp(width, 380, 900)

    padding_x = 40
    quote_font_size = 21
    line_height = 30
    avg_char_width = quote_font_size * 0.56
    max_chars = max(10, int((width - 2 * padding_x) / avg_char_width))

    safe_quote = xml_escape(quote_text)
    safe_author = xml_escape(author)

    lines = wrap_text(safe_quote, max_chars)

    header_h = 56
    quote_block_h = len(lines) * line_height
    author_h = 40
    footer_h = 18
    padding_y = 28

    height = header_h + quote_block_h + author_h + footer_h + padding_y

    p = PALETTES[theme]
    dot1, dot2, dot3 = DOT_COLORS

    light_override = ""
    if theme == "github":
        lp = PALETTES["light"]
        light_override = f"""
        @media (prefers-color-scheme: light) {{
            .cq-bg-from {{ stop-color: {lp['bg_from']}; }}
            .cq-bg-to {{ stop-color: {lp['bg_to']}; }}
            .cq-card-stroke {{ stroke: {lp['card_stroke']}; }}
            .cq-title {{ fill: {lp['title']}; }}
            .cq-quote {{ fill: {lp['quote']}; }}
            .cq-author {{ fill: {lp['author']}; }}

        }}"""

    quote_start_y = header_h + padding_y / 2 + quote_font_size
    tspans = "".join(
        f'<tspan x="{padding_x}" dy="{0 if i == 0 else line_height}">{line}</tspan>'
        for i, line in enumerate(lines)
    )

    author_y = quote_start_y + quote_block_h - line_height + author_h

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Coding quote card">
  <title>CodeQuote</title>
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop class="cq-bg-from" offset="0%" stop-color="{p['bg_from']}" />
      <stop class="cq-bg-to" offset="100%" stop-color="{p['bg_to']}" />
    </linearGradient>
    <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p['accent_from']}" stop-opacity="0.9" />
      <stop offset="100%" stop-color="{p['accent_to']}" stop-opacity="0.9" />
    </linearGradient>
    <linearGradient id="accentText" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{p['accent_from']}" />
      <stop offset="100%" stop-color="{p['accent_to']}" />
    </linearGradient>
    <style>
      .cq-title {{ fill: {p['title']}; }}
      .cq-quote {{ fill: {p['quote']}; }}
      .cq-author {{ fill: {p['author']}; }}
      .cq-card-stroke {{ stroke: {p['card_stroke']}; }}
      text {{ font-family: {font_family}; }}
      {light_override}
    </style>
  </defs>

  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14"
        fill="url(#bgGrad)" stroke="url(#borderGrad)" stroke-width="1.4" />
  <rect x="3" y="3" width="{width - 6}" height="{height - 6}" rx="12"
        fill="none" class="cq-card-stroke" stroke-width="1" />

  <circle cx="{padding_x - 12}" cy="26" r="5" fill="{dot1}" opacity="0.9" />
  <circle cx="{padding_x + 4}" cy="26" r="5" fill="{dot2}" opacity="0.9" />
  <circle cx="{padding_x + 20}" cy="26" r="5" fill="{dot3}" opacity="0.9" />

  <text x="{width - padding_x}" y="31" text-anchor="end" font-size="15" font-weight="700" fill="url(#accentText)">&lt;/&gt; CodeQuote</text>

  <text x="{width - 26}" y="{height - 18}" font-size="46" class="cq-title" opacity="0.06" font-weight="700">{{}}</text>

  <line x1="{padding_x}" y1="46" x2="{width - padding_x}" y2="46" class="cq-card-stroke" stroke-width="1" opacity="0.6" />

  <text x="{padding_x}" y="{quote_start_y}" font-size="{quote_font_size}" font-weight="600" class="cq-quote">{tspans}</text>

  <text x="{width - padding_x}" y="{author_y}" text-anchor="end" font-size="15" font-style="italic" class="cq-author">{safe_author}</text>
</svg>'''
    return svg


@app.route("/api/quote.svg")
def quote_svg():
    theme = request.args.get("theme", "dark")
    if theme not in THEMES:
        theme = "dark"

    font = request.args.get("font", "sans")
    if font not in FONT_STACKS:
        font = "sans"

    width_raw = request.args.get("width", "600")
    try:
        width = int(re.sub(r"[^0-9-]", "", width_raw) or 600)
    except ValueError:
        width = 600

    author_filter = request.args.get("author")

    q = pick_quote(author_filter)
    svg = generate_svg(q["quote"], q["author"], theme=theme, width=width, font=font)

    response = Response(svg, mimetype="image/svg+xml")

    # GitHub doesn't fetch your image directly when it's embedded in a README -
    # it routes it through its own image proxy ("Camo"), which caches whatever
    # it fetches and serves that cached copy to everyone afterwards. A soft
    # "no-cache" isn't enough to stop that, since Camo (and Fastly in front of
    # it) treats it as "revalidate if you can" rather than "don't store" - and
    # with no ETag/Last-Modified there's nothing to revalidate against, so it
    # just keeps serving the first quote it ever fetched.
    # These headers explicitly tell every layer (browser, Camo, any CDN in
    # between) to never store a copy, so each README render triggers a fresh
    # request to this endpoint and gets a new random quote.
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    # Belt-and-suspenders: strip any validators Flask/Werkzeug might attach,
    # since a stray ETag/Last-Modified is exactly the kind of thing a cache
    # will use to justify reusing the old copy.
    response.headers.pop("ETag", None)
    response.headers.pop("Last-Modified", None)

    return response


@app.route("/")
def home():
    return render_template(
        "index.html",
        canonical_url=CANONICAL_URL,
        github_url=GITHUB_URL,
        current_year=datetime.datetime.utcnow().year,
    )


@app.route("/<path:filename>")
def public_asset(filename):
    return send_from_directory(PUBLIC_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
