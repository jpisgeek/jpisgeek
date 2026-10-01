#!/usr/bin/env python3
"""Generate assets/header.svg: a terminal window that "types" the profile banner.

Zero dependencies. Edit the constants below, then run:  python3 assets/gen_header.py

BANNER is `figlet -f "ANSI Shadow" jpisgeek`. Each █ becomes a filled cell and the
box-drawing shadow becomes double strokes, so the banner renders identically no matter
which fonts the viewer has. Animations are plain CSS and switch off under
prefers-reduced-motion, leaving the finished frame.
"""
from html import escape
from pathlib import Path

BANNER = """\
     ██╗██████╗ ██╗███████╗ ██████╗ ███████╗███████╗██╗  ██╗
     ██║██╔══██╗██║██╔════╝██╔════╝ ██╔════╝██╔════╝██║ ██╔╝
     ██║██████╔╝██║███████╗██║  ███╗█████╗  █████╗  █████╔╝
██   ██║██╔═══╝ ██║╚════██║██║   ██║██╔══╝  ██╔══╝  ██╔═██╗
╚█████╔╝██║     ██║███████║╚██████╔╝███████╗███████╗██║  ██╗
 ╚════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝""".splitlines()

USER, HOST = "jason", "jpisgeek"
CMD1 = 'figlet -f "ANSI Shadow" jpisgeek'
CMD2 = "cat /etc/motd"
MOTD = "senior systems engineer // datacenter · homelab · privacy-first"

# Palette (GitHub dark)
BG, BAR_BG, BORDER = "#0d1117", "#161b22", "#30363d"
FG, MUTED, GREEN, BLUE = "#e6edf3", "#8b949e", "#7ee787", "#79c0ff"
GRADIENT = [("0", "#58a6ff"), (".45", "#56d4dd"), ("1", "#7ee787")]

# Geometry (px)
W = 820
PAD = 28            # left padding inside the window
BAR = 36            # title bar height
FS, CHW = 15, 9     # font size and forced monospace advance
CW, CH = 11, 22     # banner cell size, terminal-ish 1:2
D = 2.5             # half-gap between double strokes

PROMPT = f"{USER}@{HOST}:~$"
CMD_X = PAD + (len(PROMPT) + 1) * CHW

Y1 = BAR + 34                          # first prompt baseline
BANNER_Y = Y1 + 16
Y2 = BANNER_Y + len(BANNER) * CH + 34  # second prompt
Y3 = Y2 + 26                           # motd output
Y4 = Y3 + 30                           # idle prompt
H = Y4 + 30

# Timeline (s)
T_CMD1, CPS1 = 0.4, 0.045
T_BANNER = T_CMD1 + len(CMD1) * CPS1 + 0.2
T_LINE2 = T_BANNER + len(BANNER) * 0.07 + 0.4
T_CMD2, CPS2 = T_LINE2 + 0.3, 0.05
T_MOTD = T_CMD2 + len(CMD2) * CPS2 + 0.2
T_IDLE = T_MOTD + 0.2


def n(v):
    return f"{v:g}"


def strokes(ch, x, y):
    """Double-line segments for a box-drawing char occupying cell (x, y)."""
    l, r, t, b = x, x + CW, y, y + CH
    cx, cy = x + CW / 2, y + CH / 2
    return {
        "═": [[(l, cy - D), (r, cy - D)], [(l, cy + D), (r, cy + D)]],
        "║": [[(cx - D, t), (cx - D, b)], [(cx + D, t), (cx + D, b)]],
        "╗": [[(l, cy - D), (cx + D, cy - D), (cx + D, b)], [(l, cy + D), (cx - D, cy + D), (cx - D, b)]],
        "╔": [[(r, cy - D), (cx - D, cy - D), (cx - D, b)], [(r, cy + D), (cx + D, cy + D), (cx + D, b)]],
        "╝": [[(l, cy + D), (cx + D, cy + D), (cx + D, t)], [(l, cy - D), (cx - D, cy - D), (cx - D, t)]],
        "╚": [[(r, cy + D), (cx - D, cy + D), (cx - D, t)], [(r, cy - D), (cx + D, cy - D), (cx + D, t)]],
    }.get(ch, [])


def text(x, y, s, fill, extra=""):
    return (f'<text x="{x}" y="{y}" fill="{fill}" textLength="{len(s) * CHW}" '
            f'lengthAdjust="spacingAndGlyphs"{extra}>{escape(s, quote=False)}</text>')


def prompt(y):
    return (f'<text x="{PAD}" y="{y}" textLength="{len(PROMPT) * CHW}" lengthAdjust="spacingAndGlyphs">'
            f'<tspan fill="{GREEN}">{USER}@{HOST}</tspan><tspan fill="{FG}">:</tspan>'
            f'<tspan fill="{BLUE}">~</tspan><tspan fill="{FG}">$</tspan></text>')


def typed(name, y, cmd, start, cps):
    """Command text revealed one char at a time by a sliding cover, with a moving cursor."""
    steps, dur, dist = len(cmd), len(cmd) * cps, len(cmd) * CHW
    anim = f"{name} {n(dur)}s steps({steps}) {n(start)}s both"
    keyframes = f"@keyframes {name}{{from{{transform:translateX(0)}}to{{transform:translateX({dist}px)}}}}"
    svg = (
        text(CMD_X, y, cmd, FG)
        + f'<rect x="{CMD_X}" y="{n(y - FS)}" width="{dist + CHW}" height="{n(FS * 1.4)}" fill="{BG}" '
          f'style="transform:translateX({dist}px);animation:{anim}"/>'
        + f'<rect x="{CMD_X}" y="{n(y - FS * 0.9)}" width="{CHW}" height="{n(FS * 1.15)}" fill="{FG}" '
          f'style="opacity:0;transform:translateX({dist}px);animation:{anim},on {n(dur)}s linear {n(start)}s backwards"/>'
    )
    return svg, keyframes


def appear(t):
    return f'style="animation:appear .01s linear {n(t)}s both"'


def banner():
    rows = []
    for r, line in enumerate(BANNER):
        rects, segs, c = [], [], 0
        while c < len(line):
            if line[c] == "█":
                start = c
                while c < len(line) and line[c] == "█":
                    c += 1
                rects.append(f'<rect x="{start * CW}" y="{r * CH}" width="{(c - start) * CW}" height="{CH}"/>')
                continue
            for seg in strokes(line[c], c * CW, r * CH):
                segs.append("M" + "L".join(f"{n(x)} {n(y)}" for x, y in seg))
            c += 1
        delay = T_BANNER + r * 0.07
        rows.append(
            f'<g style="animation:rise .35s ease-out {n(delay)}s both">'
            f'<path d="{"".join(segs)}"/><g class="blk">{"".join(rects)}</g></g>'
        )
    return "".join(rows)


def main():
    banner_w = max(len(l) for l in BANNER) * CW
    cmd1, kf1 = typed("t1", Y1, CMD1, T_CMD1, CPS1)
    cmd2, kf2 = typed("t2", Y2, CMD2, T_CMD2, CPS2)
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GRADIENT)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title">
<title id="title">{escape(f"{USER}@{HOST}: {MOTD}", quote=False)}</title>
<defs>
<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{banner_w}" y2="0">{stops}</linearGradient>
<filter id="glow" x="-5%" y="-20%" width="110%" height="140%">
<feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur"/>
<feComponentTransfer in="blur" result="soft"><feFuncA type="linear" slope=".5"/></feComponentTransfer>
<feMerge><feMergeNode in="soft"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<clipPath id="win"><rect width="{W}" height="{H}" rx="10"/></clipPath>
</defs>
<style>
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS}px}}
.title{{font-size:13px}}
.banner path{{fill:none;stroke:url(#g);stroke-opacity:.5;stroke-width:1.5}}
.banner .blk{{fill:url(#g)}}
@keyframes appear{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
@keyframes on{{from,to{{opacity:1}}}}
@keyframes blink{{50%{{opacity:0}}}}
{kf1}
{kf2}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<g clip-path="url(#win)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<rect width="{W}" height="{BAR}" fill="{BAR_BG}"/>
<rect y="{BAR}" width="{W}" height="1" fill="{BORDER}"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{BORDER}"/>
<circle cx="20" cy="18" r="6" fill="#ff5f56"/><circle cx="40" cy="18" r="6" fill="#ffbd2e"/><circle cx="60" cy="18" r="6" fill="#27c93f"/>
{text(W // 2, 23, f"{USER}@{HOST}: ~", MUTED, ' class="title" text-anchor="middle"')}
<g>{prompt(Y1)}{cmd1}</g>
<g class="banner" filter="url(#glow)" transform="translate({PAD} {BANNER_Y})">{banner()}</g>
<g {appear(T_LINE2)}>{prompt(Y2)}{cmd2}</g>
<g {appear(T_MOTD)}>{text(PAD, Y3, MOTD, MUTED)}</g>
<g {appear(T_IDLE)}>{prompt(Y4)}<rect x="{CMD_X}" y="{n(Y4 - FS * 0.9)}" width="{CHW}" height="{n(FS * 1.15)}" fill="{FG}" style="animation:blink 1.1s step-end {n(T_IDLE)}s infinite"/></g>
</svg>
"""
    out = Path(__file__).with_name("header.svg")
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({W}x{H})")


if __name__ == "__main__":
    main()
