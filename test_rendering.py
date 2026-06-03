#!/usr/bin/env python3
import os
import unicodedata
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
import cairo
from PIL import Image

def split_graphemes(text):
    graphemes = []
    current = ""
    for char in text:
        is_mark = unicodedata.category(char).startswith('M')
        is_zwj = char == '\u200d'
        is_vs = '\ufe00' <= char <= '\ufe0f'
        was_zwj = current.endswith('\u200d') if current else False
        
        if current and (is_mark or is_zwj or is_vs or was_zwj):
            current += char
        else:
            if current:
                graphemes.append(current)
            current = char
    if current:
        graphemes.append(current)
    return graphemes

def render_ascii_art(text, is_dark_mode=True):
    lines = text.splitlines()
    grid = []
    max_cols = 0
    for line in lines:
        row = split_graphemes(line)
        grid.append(row)
        if len(row) > max_cols:
            max_cols = len(row)
            
    rows = len(grid)
    if rows == 0 or max_cols == 0:
        return cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)

    dummy_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    dummy_ctx = cairo.Context(dummy_surface)
    dummy_layout = PangoCairo.create_layout(dummy_ctx)
    
    # Font fallback list
    font_desc_str = "monospace, Noto Sans, Noto Sans Tamil, Noto Sans Devanagari, Noto Color Emoji 12"
    font_desc = Pango.FontDescription.from_string(font_desc_str)
    dummy_layout.set_font_description(font_desc)
    
    # Measure reference character
    dummy_layout.set_text("M", -1)
    cell_w, cell_h = dummy_layout.get_pixel_size()
    
    if cell_w == 0: cell_w = 10
    if cell_h == 0: cell_h = 20

    img_width = max_cols * cell_w
    img_height = rows * cell_h

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, img_width, img_height)
    ctx = cairo.Context(surface)
    
    # Background
    if is_dark_mode:
        ctx.set_source_rgb(0.07, 0.07, 0.07)
    else:
        ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.paint()

    # Text color
    if is_dark_mode:
        ctx.set_source_rgb(1.0, 1.0, 1.0)
    else:
        ctx.set_source_rgb(0.0, 0.0, 0.0)

    layout = PangoCairo.create_layout(ctx)
    layout.set_font_description(font_desc)
    
    for r in range(rows):
        row = grid[r]
        for c in range(len(row)):
            grapheme = row[c]
            if not grapheme or grapheme.isspace():
                continue
                
            layout.set_text(grapheme, -1)
            lw, lh = layout.get_pixel_size()
            
            if lw == 0 or lh == 0:
                continue
                
            # Scale down if it exceeds the cell dimensions, preserve aspect ratio
            scale_x = cell_w / lw
            scale_y = cell_h / lh
            scale = min(scale_x, scale_y)
            
            ctx.save()
            ctx.translate(c * cell_w + cell_w / 2.0, r * cell_h + cell_h / 2.0)
            ctx.scale(scale, scale)
            ctx.translate(-lw / 2.0, -lh / 2.0)
            PangoCairo.show_layout(ctx, layout)
            ctx.restore()

    return surface

def main():
    os.makedirs("test_output", exist_ok=True)
    
    test_cases = {
        "tamil": "வணக்கம் உலகம்",
        "hindi": "नमस्ते दुनिया",
        "emoji": "😀🚀🔥",
        "mixed": "Hello வணக்கம் 😀",
        "malayalam": "ഹലോ ലോകം",
        "telugu": "నమస్కారం ప్రపంచం",
        "kannada": "ನಮಸ್ಕಾರ ಪ್ರಪಂಚ",
        "bengali": "হ্যালো বিশ্ব",
        "arabic": "مرحبا بالعالم",
        "mixed_multiline": "Hello வணக்கம் 😀\nनमस्ते दुनिया\n😀🚀🔥\nمرحبا بالعالم"
    }

    for name, text in test_cases.items():
        # Render dark mode version
        surface_dark = render_ascii_art(text, is_dark_mode=True)
        surface_dark.write_to_png(f"test_output/{name}_dark.png")
        
        # Render light mode version
        surface_light = render_ascii_art(text, is_dark_mode=False)
        surface_light.write_to_png(f"test_output/{name}_light.png")
        
        print(f"Rendered test case '{name}' successfully.")

if __name__ == "__main__":
    main()
