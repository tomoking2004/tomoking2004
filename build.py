"""Build the images for the profile README: assets/{hero,skills}-{dark,light}.svg and assets/fox.gif.

Usage: python build.py [path to claude-plugins/plugins/fox]

Without the path, the fox plugin is read from the claude-plugins checkout
next to this repository.

Every image the README shows is kept in this repository. The hero inlines
the sprites of the fox plugin, and fox.gif is a copy of the plugin's preview.
The skills row sets the names in SKILLS under the logos in logos/ (Simple
Icons, CC0). No image is fetched from another repository or service when the
profile is viewed, so the images keep rendering whatever happens there. Rerun
this script after the fox plugin exports its art again.
"""
import json
import re
import shutil
import sys
from collections.abc import Iterable
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "assets"
FOX = HERE.parent / "claude-plugins" / "plugins" / "fox"
LOGOS = HERE / "logos"

NAME = "Tomoharu Nakano"

THEMES = {
    "dark": dict(
        sky=("#10121b", "#1c2030"), star="#f8ddb8", title="#f8ddb8", shadow="#8c4a28",
        floor="#3a2a22", plank="#2b1f19", edge="#5c463c",
    ),
    "light": dict(
        sky=("#fdf9f2", "#f4eadb"), star="#d9781e", title="#3a2010", shadow="#ebc9a0",
        floor="#d9b48a", plank="#c49a6c", edge="#ebd3b0",
    ),
}

SKILLS = {"python": "Python", "pytorch": "PyTorch", "c": "C", "git": "Git", "github": "GitHub",
          "claudecode": "Claude Code"}  # stem of a logo file in logos/: the skill's name, shown under its logo
LOGO = 24  # side of a logo, in its own units
# The system fonts of GitHub's text font stack
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"

# Pixel font, only for the characters of NAME in upper case.
# Each glyph is GLYPH_W x GLYPH_H dots, row by row ('#' is a dot).
GLYPH_W, GLYPH_H = 5, 7
GLYPH_PITCH = GLYPH_W + 1  # a glyph and the gap after it
GLYPHS = {
    "A": ".###.#...##...#######...##...##...#", "H": "#...##...##...#######...##...##...#",
    "K": "#...##..#.#.#..##...#.#..#..#.#...#", "M": "#...###.###.#.##...##...##...##...#",
    "N": "#...##...###..##.#.##..###...##...#", "O": ".###.#...##...##...##...##...#.###.",
    "R": "####.#...##...#####.#.#..#..#.#...#", "T": "#####..#....#....#....#....#....#..",
    "U": "#...##...##...##...##...##...#.###.", " ": "." * (GLYPH_W * GLYPH_H),
}

SPRITE = 64  # side of a fox sprite, in its own dots
TICKS_PER_SECOND = 10  # the sprites' animations step in ticks


def pixel_text(text: str, x: int, y: int, dot: int, cls: str) -> str:
    """Return `text` in the pixel font as one path, drawing each dot of a glyph as a square of side `dot`."""
    d = []
    for i, ch in enumerate(text):
        glyph = GLYPHS[ch]
        for row in range(GLYPH_H):
            for col in range(GLYPH_W):
                if glyph[row * GLYPH_W + col] == "#":
                    d.append(f"M{x + (i * GLYPH_PITCH + col) * dot} {y + row * dot}h{dot}v{dot}h-{dot}z")
    return f'<path class="{cls}" d="{"".join(d)}"/>'


def text_width(text: str, dot: int) -> int:
    """Return the width of `text` as `pixel_text` draws it."""
    return (GLYPH_PITCH * len(text) - 1) * dot


def sprite(path: Path, prefix: str, x: int, y: int, scale: int, delay: int,
           recolor: Iterable[tuple[str, str]] = ()) -> tuple[str, str]:
    """Return the CSS and the element of a fox sprite, ready to inline.

    Class and keyframe names are prefixed with `prefix`, so that several
    sprites share one SVG without their names clashing. The animation starts
    `delay` ticks in. `recolor` lists (old, new) pairs of colors.
    """
    svg = path.read_text(encoding="utf-8")
    svg = svg.replace("animation-delay:0s", f"animation-delay:-{delay / TICKS_PER_SECOND}s")
    for old, new in recolor:
        svg = svg.replace(old, new)
    style = re.search(r"<style>(.*?)</style>", svg, re.S)
    css = style.group(1)
    body = svg[style.end():svg.rindex("</svg>")]
    css = re.sub(r"\.([A-Za-z]+)(?=[{,])", lambda m: f".{prefix}{m.group(1)}", css)
    css = re.sub(r"@keyframes k(\d+)", rf"@keyframes {prefix}k\1", css)
    body = re.sub(r'class="([^"]+)"',
                  lambda m: 'class="' + " ".join(prefix + c for c in m.group(1).split()) + '"', body)
    body = re.sub(r"animation-name:k(\d+)", rf"animation-name:{prefix}k\1", body)
    size = SPRITE * scale
    return css, (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 {SPRITE} {SPRITE}" '
                 f'shape-rendering="crispEdges">{body}</svg>')


def hero(sprites: Path, theme: str) -> str:
    """Return the hero SVG in `theme`: NAME over three foxes from `sprites`."""
    t = THEMES[theme]
    w, h, floor_y = 1200, 430, 370
    radius, edge_h, scale = 12, 6, 3
    variants = json.loads((sprites / "index.json").read_text(encoding="utf-8"))["variants"]
    foxes = [  # (file name, x, delay in ticks, index of the color variant; 0 keeps the sprite's own)
        ("sub-research.svg", 250, 17, 1),
        ("main-watch-0.svg", 504, 0, 0),
        ("sub-run.svg", 758, 31, 0),
    ]
    css_parts, elements = [], []
    for i, (name, x, delay, variant) in enumerate(foxes):
        recolor = zip(variants[0], variants[variant], strict=True)
        css, element = sprite(sprites / name, f"f{i}", x, floor_y - SPRITE * scale, scale, delay, recolor)
        css_parts.append(css)
        elements.append(element)

    stars = [  # (x, y, delay in seconds)
        (84, 60, 0), (160, 150, 1.3), (1010, 52, 0.6), (1120, 140, 1.9), (930, 150, 2.8),
        (60, 250, 3.3), (1150, 260, 0.9), (464, 196, 2.4), (724, 176, 1.6), (1040, 290, 2.1),
    ]
    star_rects = "".join(
        f'<rect class="star" x="{x}" y="{y}" width="6" height="6" style="animation-delay:-{delay}s"/>'
        for x, y, delay in stars)

    title = NAME.upper()
    dot = 8
    tx, ty = (w - text_width(title, dot)) // 2, 60
    planks = "".join(
        f'<rect x="{x}" y="{floor_y + edge_h}" width="6" height="{h - floor_y - edge_h}" fill="{t["plank"]}"/>'
        for x in range(0, w, 150))

    stylesheet = (
        f".star{{fill:{t['star']};animation:tw 3.6s steps(1) infinite}}"
        "@keyframes tw{0%{opacity:.9}40%{opacity:.25}70%{opacity:.6}}"
        f".title{{fill:{t['title']}}}.shadow{{fill:{t['shadow']}}}"
        + "".join(css_parts)
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{NAME}: three pixel-art foxes at work">'
        f"<style>{stylesheet}</style>"
        f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{t["sky"][0]}"/><stop offset="1" stop-color="{t["sky"][1]}"/>'
        f"</linearGradient></defs>"
        f'<rect width="{w}" height="{h}" rx="{radius}" fill="url(#sky)"/>'
        f"{star_rects}"
        f'{pixel_text(title, tx + dot, ty + dot, dot, "shadow")}{pixel_text(title, tx, ty, dot, "title")}'
        f'<path d="M0 {floor_y}H{w}V{h - radius}a{radius} {radius} 0 0 1-{radius} {radius}'
        f'H{radius}a{radius} {radius} 0 0 1-{radius}-{radius}z" fill="{t["floor"]}"/>'
        f'<rect y="{floor_y}" width="{w}" height="{edge_h}" fill="{t["edge"]}"/>{planks}'
        f"{''.join(elements)}</svg>"
    )


def skills(theme: str) -> str:
    """Return the skills SVG in `theme`: the logos of SKILLS in one row, each over its name.

    Everything is in the color of the hero's title. The names are text in
    SANS, so they render in whichever of its fonts the viewer has.
    """
    scale, cell = 2, 104  # a logo's scale, and the width each logo and its name take up
    size = LOGO * scale
    baseline = size + 26  # y of the names' baseline, 26 units below the bottom of the logos
    height = size + 32  # of the whole row, leaving room under the baseline for descenders
    items = []
    for i, (stem, name) in enumerate(SKILLS.items()):
        d = re.search(r' d="([^"]+)"', (LOGOS / f"{stem}.svg").read_text(encoding="utf-8")).group(1)
        items.append(f'<path transform="translate({i * cell + (cell - size) // 2}) scale({scale})" d="{d}"/>'
                     f'<text x="{i * cell + cell // 2}" y="{baseline}">{name}</text>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cell * len(SKILLS)} {height}" role="img" '
        f'aria-label="{", ".join(SKILLS.values())}" fill="{THEMES[theme]["title"]}" font-size="16" '
        f'font-family="{SANS}" text-anchor="middle">{"".join(items)}</svg>'
    )


def main() -> None:
    """Write the images to assets/, reading the fox plugin from argv[1] or its default location."""
    fox = Path(sys.argv[1]) if len(sys.argv) > 1 else FOX
    OUT.mkdir(exist_ok=True)
    for theme in THEMES:
        (OUT / f"hero-{theme}.svg").write_text(hero(fox / "sprites", theme), encoding="utf-8", newline="\n")
        (OUT / f"skills-{theme}.svg").write_text(skills(theme), encoding="utf-8", newline="\n")
    shutil.copyfile(fox / "preview.gif", OUT / "fox.gif")


if __name__ == "__main__":
    main()
