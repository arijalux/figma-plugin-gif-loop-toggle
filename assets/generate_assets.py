import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BLUE_LIGHT = (24, 160, 251)     # #18A0FB
BLUE_DARK = (13, 142, 224)      # #0D8EE0
NAVY_DEEP = (11, 24, 45)        # #0B182D
WHITE = (255, 255, 255)

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def diagonal_gradient(size, c1, c2):
    w, h = size
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    t = (xx + yy) / 2.0
    t = np.clip(t, 0, 1)
    c1 = np.array(c1, dtype=np.float32)
    c2 = np.array(c2, dtype=np.float32)
    img = c1[None, None, :] + (c2 - c1)[None, None, :] * t[:, :, None]
    img = img.astype(np.uint8)
    return Image.fromarray(img, mode="RGB")


def draw_icon_glyph(draw, cx, cy, r, stroke_w, color=WHITE, badge_color=NAVY_DEEP):
    # Closed loop ring (signifies looping/repeat) around a play triangle.
    bbox = [cx - r, cy - r, cx + r, cy + r]
    draw.ellipse(bbox, outline=color, width=stroke_w)

    # Play triangle, centered with slight optical right offset
    tri_h = r * 1.05
    tri_w = tri_h * 0.92
    offset_x = tri_w * 0.08
    p1 = (cx - tri_w * 0.42 + offset_x, cy - tri_h * 0.55)
    p2 = (cx - tri_w * 0.42 + offset_x, cy + tri_h * 0.55)
    p3 = (cx + tri_w * 0.58 + offset_x, cy)
    draw.polygon([p1, p2, p3], fill=color)

    # Toggle-switch badge, bottom-right of the ring, signifies "on/off control"
    badge_w = r * 1.05
    badge_h = badge_w * 0.52
    bx = cx + r * 0.62
    by = cy + r * 0.62
    bbox_badge = [bx - badge_w / 2, by - badge_h / 2, bx + badge_w / 2, by + badge_h / 2]
    draw.rounded_rectangle(bbox_badge, radius=badge_h / 2, fill=color)
    knob_r = badge_h * 0.36
    knob_x = bx + badge_w / 2 - badge_h / 2
    knob_y = by
    draw.ellipse([knob_x - knob_r, knob_y - knob_r, knob_x + knob_r, knob_y + knob_r], fill=badge_color)


def make_icon(path, size=128, ss=4):
    S = size * ss
    canvas = diagonal_gradient((S, S), BLUE_LIGHT, BLUE_DARK).convert("RGBA")

    mask = Image.new("L", (S, S), 0)
    mdraw = ImageDraw.Draw(mask)
    radius = int(S * 0.225)
    mdraw.rounded_rectangle([0, 0, S - 1, S - 1], radius=radius, fill=255)

    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), mask)

    draw = ImageDraw.Draw(out)
    cx, cy = S / 2, S / 2 + S * 0.01
    r = S * 0.30
    stroke_w = max(2, int(S * 0.045))
    draw_icon_glyph(draw, cx, cy, r, stroke_w)

    out = out.resize((size, size), Image.LANCZOS)
    out.save(path)
    print("saved", path, out.size)


def rounded_rect_shadow(base, box, radius, blur=40, opacity=110):
    x0, y0, x1, y1 = box
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle(box, radius=radius, fill=(0, 0, 0, opacity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(shadow)


def scatter_pattern(base, count=46, seed=7):
    rng = np.random.default_rng(seed)
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for _ in range(count):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        r = rng.uniform(10, 26)
        alpha = int(rng.uniform(10, 26))
        tri_w = r * 1.0
        tri_h = r * 1.15
        p1 = (x, y - tri_h / 2)
        p2 = (x, y + tri_h / 2)
        p3 = (x + tri_w, y)
        odraw.polygon([p1, p2, p3], fill=(255, 255, 255, alpha))
    base.alpha_composite(overlay)


def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def make_cover(path, size=(1920, 1080)):
    W, H = size
    ss = 2
    S = (W * ss, H * ss)

    bg = diagonal_gradient(S, NAVY_DEEP, BLUE_DARK).convert("RGBA")
    scatter_pattern(bg, count=70, seed=3)

    # Icon card
    card_size = int(S[1] * 0.62)
    card_x = int(S[0] * 0.085)
    card_y = (S[1] - card_size) // 2
    radius = int(card_size * 0.225)

    rounded_rect_shadow(
        bg,
        [card_x + 10 * ss, card_y + 22 * ss, card_x + card_size + 10 * ss, card_y + card_size + 22 * ss],
        radius,
        blur=36 * ss,
        opacity=130,
    )

    card_grad = diagonal_gradient((card_size, card_size), BLUE_LIGHT, BLUE_DARK).convert("RGBA")
    card_mask = Image.new("L", (card_size, card_size), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle([0, 0, card_size - 1, card_size - 1], radius=radius, fill=255)
    card = Image.new("RGBA", (card_size, card_size), (0, 0, 0, 0))
    card.paste(card_grad, (0, 0), card_mask)

    cdraw = ImageDraw.Draw(card)
    cx, cy = card_size / 2, card_size / 2 + card_size * 0.01
    r = card_size * 0.30
    stroke_w = max(2, int(card_size * 0.045))
    draw_icon_glyph(cdraw, cx, cy, r, stroke_w)

    bg.paste(card, (card_x, card_y), card)

    # Text block
    draw = ImageDraw.Draw(bg)
    text_x = card_x + card_size + int(S[0] * 0.05)
    center_y = S[1] / 2

    eyebrow_font = ImageFont.truetype(FONT_BOLD, int(30 * ss))
    tagline_font = ImageFont.truetype(FONT_REG, int(46 * ss))

    eyebrow = "FIGMA PLUGIN"
    spaced = "  ".join(list(eyebrow))
    _, eh = text_width(draw, spaced, eyebrow_font)

    title = "GIF Loop Toggle"
    max_title_w = S[0] - text_x - int(70 * ss)
    title_size = 112 * ss
    title_font = ImageFont.truetype(FONT_BLACK, int(title_size))
    tw, th = text_width(draw, title, title_font)
    while tw > max_title_w and title_size > 40 * ss:
        title_size -= 2 * ss
        title_font = ImageFont.truetype(FONT_BLACK, int(title_size))
        tw, th = text_width(draw, title, title_font)

    tagline = "Turn GIF looping on or off."
    _, tgh = text_width(draw, tagline, tagline_font)

    gap1, gap2 = int(28 * ss), int(30 * ss)
    total_h = eh + gap1 + th + gap2 + tgh
    y = center_y - total_h / 2

    draw.text((text_x, y), spaced, font=eyebrow_font, fill=(255, 255, 255, 170))
    y += eh + gap1
    draw.text((text_x, y), title, font=title_font, fill=WHITE)
    y += th + gap2
    draw.text((text_x, y), tagline, font=tagline_font, fill=(255, 255, 255, 200))

    bg = bg.resize(size, Image.LANCZOS).convert("RGB")
    bg.save(path, quality=95)
    print("saved", path, bg.size)


if __name__ == "__main__":
    make_icon("/Users/arijal/Desktop/ClaudeDesign/figma-plugin-gif-play-once/assets/icon-128.png")
    make_cover("/Users/arijal/Desktop/ClaudeDesign/figma-plugin-gif-play-once/assets/cover-1920x1080.png")
