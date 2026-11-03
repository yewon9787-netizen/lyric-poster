"""Editable title/artist overlay for Lyric2Poster Studio 2.0.

Usage: edit_poster(base_png, title, artist, position='bottom',
                   alignment='center', text_color='#FFFFFF', title_scale=6)
"""
from __future__ import annotations

import io
import re
from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [
    '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'DejaVuSans-Bold.ttf',
]


def _font(size: int):
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _fit(draw, text, max_width, start_size):
    size = start_size
    while size > 12:
        font = _font(size)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
        size -= 2
    return _font(12)


def edit_poster(
    base_png: bytes,
    title: str,
    artist: str,
    *,
    position: str = 'bottom',
    alignment: str = 'center',
    text_color: str = '#FFFFFF',
    title_scale: int = 6,
) -> bytes:
    """Draw editable typography on an unlettered poster image; return PNG bytes."""
    if position not in {'top', 'center', 'bottom'}:
        raise ValueError('Invalid position')
    if alignment not in {'left', 'center', 'right'}:
        raise ValueError('Invalid alignment')
    if not re.fullmatch(r'#[0-9A-Fa-f]{6}', text_color):
        raise ValueError('text_color must be a #RRGGBB color')
    if not 3 <= title_scale <= 12:
        raise ValueError('title_scale must be between 3 and 12')

    with Image.open(io.BytesIO(base_png)) as source:
        image = source.convert('RGBA')
    w, h = image.size
    margin = max(8, int(w * .08))
    max_width = w - 2 * margin

    # Transparent dark band helps keep type readable over busy artwork.
    band_h = max(100, int(h * .27))
    y_band = {'top': 0, 'center': (h - band_h)//2, 'bottom': h-band_h}[position]
    band = Image.new('RGBA', (w, band_h), (0, 0, 0, 125))
    image.alpha_composite(band, (0, y_band))

    draw = ImageDraw.Draw(image)
    title = title.strip()[:120]
    artist = artist.strip()[:120]
    title_font = _fit(draw, title, max_width, max(14, int(h * title_scale / 100)))
    artist_font = _fit(draw, artist, max_width, max(12, int(h * .028)))
    title_box = draw.textbbox((0, 0), title, font=title_font)
    artist_box = draw.textbbox((0, 0), artist, font=artist_font)
    title_h = title_box[3] - title_box[1]
    artist_h = artist_box[3] - artist_box[1]
    space = max(8, int(h * .018))
    y = y_band + max(5, (band_h - title_h - artist_h - space)//2)

    def x_for(text, font):
        width = draw.textbbox((0, 0), text, font=font)[2]
        return {'left': margin, 'center': (w-width)//2, 'right': w-margin-width}[alignment]

    rgb = tuple(int(text_color[i:i+2], 16) for i in (1, 3, 5))
    draw.text((x_for(title, title_font), y-title_box[1]), title, font=title_font, fill=rgb)
    draw.text((x_for(artist, artist_font), y+title_h+space-artist_box[1]), artist,
              font=artist_font, fill=rgb)

    buffer = io.BytesIO()
    image.convert('RGB').save(buffer, format='PNG')
    return buffer.getvalue()
