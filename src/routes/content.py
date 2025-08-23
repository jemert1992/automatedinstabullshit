import os
import random
import time
import base64
import io
from flask import Blueprint, request, jsonify, current_app as app
from PIL import Image, ImageDraw, ImageFont
import openai

content_bp = Blueprint('content', __name__)

# Template categories with their corresponding background images
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
    """Generate a fact based on the provided topic"""
    try:
        data = request.get_json()
        topic = data.get('topic', 'general')

        # Create topic-specific prompts
        prompts = {
            'real_estate': f"Generate a short, impactful headline about real estate or property that would grab attention on social media. Make it bold, surprising, and under 15 words. Format it like a news headline or viral fact. Examples: 'WORLD'S MOST EXPENSIVE HOME COSTS MORE THAN SOME COUNTRIES' GDP' or 'TOKYO APARTMENTS SELL FOR LESS THAN A CAR'",
            'yachts': f"Generate a short, impactful headline about yachts, boats, or maritime luxury that would grab attention on social media. Make it bold, surprising, and under 15 words. Format it like a news headline or viral fact. Examples: 'WORLD'S LARGEST YACHT HAS ITS OWN SUBMARINE GARAGE' or 'BILLIONAIRE'S YACHT COSTS $1 MILLION PER WEEK TO MAINTAIN'",
            'general': f"Generate a short, impactful headline about science, history, or amazing facts that would grab attention on social media. Make it bold, surprising, and under 15 words. Format it like a news headline or viral fact. Examples: 'OCTOPUSES HAVE THREE HEARTS AND BLUE BLOOD' or 'HONEY NEVER EXPIRES - 3000 YEAR OLD HONEY IS STILL EDIBLE'"
        }

        prompt = prompts.get(topic, prompts['general'])

        # Generate content using OpenAI
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_insta_post_img(background_path, fact, brand_name, text_size=84, text_x=50, text_y=10, brand_size=36):
    img = Image.open(background_path).convert("RGBA").resize((1080, 1080))
    draw = ImageDraw.Draw(img)

    # Font paths (ensure these exist; fallback to default if not)
    font_path = os.path.join("src", "static", "Arial-Bold.ttf")
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # fallback for common servers

    fact_font = ImageFont.truetype(font_path, text_size)
    brand_font = ImageFont.truetype(font_path, brand_size)

    fact = fact.upper()
    brand_name = brand_name.upper()

    # Main fact centered horizontally, near the top by text_y (%)
    fact_w, fact_h = draw.textsize(fact, font=fact_font)
    fx = int((1080 - fact_w) / 2) if isinstance(text_x, (int, float)) else int(text_x)
    fy = int(1080 * (text_y/100)) if isinstance(text_y, (int, float)) and text_y <= 1 else int(text_y) if text_y > 1 else int(1080 * text_y)
    # Shadow
    draw.text((fx+3, fy+3), fact, font=fact_font, fill="black")
    # Main text
    draw.text((fx, fy), fact, font=fact_font, fill="white")

    # Brand name bottom right
    brand_w, brand_h = draw.textsize(brand_name, font=brand_font)
    bx = 1080 - brand_w - 40
    by = 1080 - brand_h - 40
    draw.text((bx+2, by+2), brand_name, font=brand_font, fill="black")
    draw.text((bx, by), brand_name, font=brand_font, fill="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@content_bp.route('/create-post', methods=['POST'])
def create_post():
    """Create an Instagram post with background image and return base64-encoded PNG"""
    try:
        data = request.get_json()
        topic = data.get('topic', 'general')
        fact = data.get('fact', '')
        brand_name = data.get('brand', 'FACTS')
        text_size = int(data.get('textSize', 84))
        text_x = int(data.get('textX', 50))
        text_y = int(data.get('textY', 10))
        brand_size = int(data.get('brandSize', 36))

        if not fact:
            return jsonify({
                'success': False,
                'error': 'No fact provided'
            }), 400

        # Select a random template based on topic
        templates = TEMPLATES.get(topic, TEMPLATES['general'])
        template_filename = random.choice(templates)
        template_path = os.path.join(app.static_folder, template_filename)

        # Create the post image with overlays baked in
        base64_image = create_insta_post_img(
            template_path, fact, brand_name, text_size, text_x, text_y, brand_size
        )

        return jsonify({
            'success': True,
            'background_image_base64': base64_image,
            'image_dimensions': {'width': 1080, 'height': 1080}
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_bp.route('/topics', methods=['GET'])
def get_topics():
    """Get available topic categories"""
    return jsonify({
        'success': True,
        'topics': list(TEMPLATES.keys())
    })
