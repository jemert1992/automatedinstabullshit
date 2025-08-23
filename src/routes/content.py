def wrap_text(text, font, draw, max_width):
    words = text.split()
    lines = []
    while words:
        line = ''
        i = 0
        while i < len(words):
            test_line = (line + ' ' + words[i]).strip() if line else words[i]
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox
            if w > max_width and line:
                break
            else:
                line = test_line
                i += 1
        lines.append(line)
        words = words[i:]
    return lines

def create_insta_post_img(
    background_path, fact, brand_name, text_size=84, text_x=50, text_y=10, brand_size=36
):
    img = Image.open(background_path).convert("RGBA").resize((1080, 1080))
    draw = ImageDraw.Draw(img, "RGBA")

    font_path = os.path.join("src", "static", "Arial-Bold.ttf")
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    fact_font = ImageFont.truetype(font_path, text_size)
    brand_font = ImageFont.truetype(font_path, brand_size)
    viral_font = ImageFont.truetype(font_path, int(text_size // 2))

    fact = str(fact).upper()
    brand_name = str(brand_name).upper()
    viral_tag = "VIRAL"

    # Wrap headline and calculate sizes
    max_text_width = int(1080 * 0.92)
    fact_lines = wrap_text(fact, fact_font, draw, max_text_width)
    bbox_A = fact_font.getbbox("A")
    line_height = bbox_A[3] - bbox_A[3]
    band_height = line_height * len(fact_lines) + 48
    band_y0 = 24
    band_y1 = band_y0 + band_height
    draw.rectangle([(0, band_y0), (1080, band_y1)], fill=(0, 0, 0, 190))

    # VIRAL tag centering
    viral_bbox = draw.textbbox((0, 0), viral_tag, font=viral_font)
    viral_w = viral_bbox[2] - viral_bbox
    draw.text(((1080 - viral_w) // 2, 8), viral_tag, font=viral_font, fill="red")

    # Draw each line of headline centered, with shadow for readability
    top = band_y0 + 24
    for line in fact_lines:
        bbox = draw.textbbox((0, 0), line, font=fact_font)
        w = bbox[2] - bbox
        draw.text(((1080 - w) // 2 + 2, top + 2), line, font=fact_font, fill="black")
        draw.text(((1080 - w) // 2, top), line, font=fact_font, fill="white")
        top += line_height

    # Brand mark at bottom center
    brand_bbox = draw.textbbox((0, 0), brand_name, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox
    brand_h = brand_bbox - brand_bbox[3]
    bx = (1080 - brand_w) // 2
    by = 1080 - brand_h - 40
    draw.text((bx + 2, by + 2), brand_name, font=brand_font, fill="black")
    draw.text((bx, by), brand_name, font=brand_font, fill="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"
