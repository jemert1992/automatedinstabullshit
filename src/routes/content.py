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

def create_insta_post_img(background_path, fact, brand_name, text_size=84, text_x=50, text_y=10, brand_size=36):
    img = Image.open(background_path).convert("RGBA").resize((1080, 1080))
    draw = ImageDraw.Draw(img)

    font_path = os.path.join("src", "static", "Arial-Bold.ttf")
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    fact_font = ImageFont.truetype(font_path, text_size)
    brand_font = ImageFont.truetype(font_path, brand_size)

    fact = str(fact).upper()
    brand_name = str(brand_name).upper()

    # Compute size for FACT text
    fact_bbox = draw.textbbox((0, 0), fact, font=fact_font)  # (left, upper, right, lower)
    fact_w = fact_bbox[2] - fact_bbox
    fact_h = fact_bbox[2] - fact_bbox[3]
    fx = int((1080 - fact_w) / 2)

    if isinstance(text_y, (float, int)):
        if isinstance(text_y, float) and text_y <= 1:
            fy = int(1080 * text_y)
        elif isinstance(text_y, int) and text_y < 100:
            fy = int(1080 * (text_y / 100))
        else:
            fy = int(text_y)
    else:
        fy = 10

    # Draw shadow and text
    draw.text((fx + 3, fy + 3), fact, font=fact_font, fill="black")
    draw.text((fx, fy), fact, font=fact_font, fill="white")

    # Compute size for BRAND text
    brand_bbox = draw.textbbox((0, 0), brand_name, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox
    brand_h = brand_bbox[2] - brand_bbox[3]
    bx = 1080 - brand_w - 40
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
