import os
import random
import base64
import io
from flask import Blueprint, request, jsonify, current_app as app
from PIL import Image, ImageDraw, ImageFont
import openai

content_bp = Blueprint('content', __name__)

TEMPLATES = {
    'real_estate': [
        'real_estate_template_1.png',
        'real_estate_template_2.png',
        'real_estate_template_3.png'
    ],
    'yachts': [
        'yacht_template_1.png',
        'yacht_template_2.png'
    ],
    'general': [
        'general_template_1.png',
        'general_template_2.png'
    ]
}

@content_bp.route('/generate-fact', methods=['POST'])
def generate_fact():
    try:
        data = request.get_json()
        topic = data.get('topic', 'general')
        prompts = {
            'real_estate': "Generate a short, impactful headline about real estate or property that would grab attention on social media. Make it bold, surprising, and under 15 words. Format it like a news headline or viral fact. Examples: 'WORLD'S MOST EXPENSIVE HOME COSTS MORE THAN SOME COUNTRIES' GDP' or 'TOKYO APARTMENTS SELL FOR LESS THAN A CAR'",
            'yachts': "Generate a short, impactful headline about yachts, boats, or maritime luxury that would grab attention on social media. Make it bold, surprising, and under 15 words. Format it like a news headline or viral fact. Examples: 'WORLD'S LARGEST YACHT HAS ITS OWN SUBMARINE GARAGE' or 'BILLIONAIRE'S YACHT COSTS $1 MILLION PER WEEK TO MAINTAIN'",
            'general': "Generate a short, impactful headline about science, history, or amazing facts that would grab attention on social media. Make it bold, surprising, and under 15 words. Format it like a news headline or viral fact. Examples: 'OCTOPUSES HAVE THREE HEARTS AND BLUE BLOOD' or 'HONEY NEVER EXPIRES - 3000 YEAR OLD HONEY IS STILL EDIBLE'"
        }
        prompt = prompts.get(topic, prompts['general'])
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a fact generator that creates engaging, surprising, and accurate facts. Always provide just the fact without any additional text or formatting."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.8
        )
        fact = response.choices[0].message.content.strip()
        return jsonify({
            'success': True,
            'fact': fact,
            'topic': topic
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def wrap_text(text, font, draw, max_width):
    """Wrap text so lines never exceed max_width in pixels."""
    words = text.split()
    lines = []
    while words:
        line = ''
        while words:
            test_line = f"{line} {words[0]}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox
            if w > max_width and line:
                break
            else:
                line = test_line
                words.pop(0)
        lines.append(line)
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
    line_height = fact_font.getbbox("A")[3] - fact_font.getbbox("A")[3]
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
        draw.text(
            ((1080 - w) // 2 + 2, top + 2), line, font=fact_font, fill="black"
        )
        draw.text(
            ((1080 - w) // 2, top), line, font=fact_font, fill="white"
        )
        top += line_height

    # Brand mark at bottom center
    brand_bbox = draw.textbbox((0, 0), brand_name, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox
    brand_h = brand_bbox[4] - brand_bbox[3]
    bx = (1080 - brand_w) // 2
    by = 1080 - brand_h - 40
    draw.text((bx + 2, by + 2), brand_name, font=brand_font, fill="black")
    draw.text((bx, by), brand_name, font=brand_font, fill="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@content_bp.route('/create-post', methods=['POST'])
def create_post():
    try:
        data = request.get_json()
        topic = data.get('topic', 'general')
        fact = data.get('fact', '')
        brand_name = data.get('brand', 'FACTS')
        text_size = int(data.get('textSize', 84))
        text_x = data.get('textX', 50)
        text_y = data.get('textY', 10)
        if isinstance(text_x, str):
            text_x = float(text_x) if '.' in text_x else int(text_x)
        if isinstance(text_y, str):
            text_y = float(text_y) if '.' in text_y else int(text_y)
        brand_size = int(data.get('brandSize', 36))

        if not fact:
            return jsonify({'success': False, 'error': 'No fact provided'}), 400

        templates = TEMPLATES.get(topic, TEMPLATES['general'])
        template_filename = random.choice(templates)
        template_path = os.path.join(app.static_folder, template_filename)
        base64_image = create_insta_post_img(
            template_path, fact, brand_name, text_size, text_x, text_y, brand_size
        )

        return jsonify({
            'success': True,
            'background_image_base64': base64_image,
            'image_dimensions': {'width': 1080, 'height': 1080}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@content_bp.route('/topics', methods=['GET'])
def get_topics():
    return jsonify({'success': True, 'topics': list(TEMPLATES.keys())})
