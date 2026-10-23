"""Preview the exact vector/text subset emitted by EletroProjeto PDFs via Cairo.
Not a general PDF reader. Parses emitted page streams/ToUnicode independently.
"""

import ctypes as c
import re
import sys
from pathlib import Path

pdf = Path(sys.argv[1]).read_bytes()
output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp")
output.mkdir(parents=True, exist_ok=True)
cm = re.search(rb"begincmap(.*?)endcmap", pdf, re.S).group(1)
mapping = {}
for block in re.findall(rb"beginbfchar(.*?)endbfchar", cm, re.S):
    for code, unicode in re.findall(rb"<([A-Fa-f0-9]+)>\s+<([A-Fa-f0-9]+)>", block):
        mapping[int(code, 16)] = bytes.fromhex(unicode.decode()).decode("utf-16-be")
lib = c.CDLL("libcairo.so.2")


def fn(name, args, restype=None):
    f = getattr(lib, name)
    f.argtypes = args
    f.restype = restype
    return f


ptr, dbl = c.c_void_p, c.c_double
surface = fn("cairo_image_surface_create", [c.c_int, c.c_int, c.c_int], ptr)
create = fn("cairo_create", [ptr], ptr)
scale = fn("cairo_scale", [ptr, dbl, dbl])
color = fn("cairo_set_source_rgb", [ptr, dbl, dbl, dbl])
paint = fn("cairo_paint", [ptr])
rect = fn("cairo_rectangle", [ptr, dbl, dbl, dbl, dbl])
fill = fn("cairo_fill", [ptr])
face = fn("cairo_select_font_face", [ptr, c.c_char_p, c.c_int, c.c_int])
size = fn("cairo_set_font_size", [ptr, dbl])
move = fn("cairo_move_to", [ptr, dbl, dbl])
show = fn("cairo_show_text", [ptr, c.c_char_p])
write = fn("cairo_surface_write_to_png", [ptr, c.c_char_p], c.c_int)
destroy = fn("cairo_destroy", [ptr])
finish = fn("cairo_surface_destroy", [ptr])
page = 0
for stream in re.findall(rb"stream\n(.*?)\nendstream", pdf, re.S):
    if b"BT /F1" not in stream:
        continue
    page += 1
    surf = surface(0, 1191, 1684)
    ctx = create(surf)
    scale(ctx, 2, 2)
    color(ctx, 1, 1, 1)
    paint(ctx)
    for command in stream.decode("ascii").splitlines():
        box = re.fullmatch(r"q ([\d.]+) g ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) re f Q", command)
        if box:
            shade, x, y, w, h = map(float, box.groups())
            color(ctx, shade, shade, shade)
            rect(ctx, x, 841.89 - y - h, w, h)
            fill(ctx)
        text = re.fullmatch(r"BT /F1 (\d+) Tf 1 0 0 1 (\d+) (\d+) Tm <([A-F0-9]*)> Tj ET", command)
        if text:
            pts, x, y, encoded = text.groups()
            value = "".join(mapping[int(encoded[i : i + 4], 16)] for i in range(0, len(encoded), 4))
            color(ctx, 0.12, 0.12, 0.12)
            face(ctx, b"DejaVu Sans Mono", 0, 0)
            size(ctx, float(pts))
            move(ctx, float(x), 841.89 - float(y))
            show(ctx, value.encode())
    target = str(output / f"eletroprojeto-pdf-page-{page}.png")
    assert write(surf, target.encode()) == 0
    destroy(ctx)
    finish(surf)
print(f"{page} páginas renderizadas a partir dos streams PDF")
