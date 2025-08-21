import os
import random
import textwrap
import time

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

@content_bp.route('/create-post', methods=['POST'])
def create_post():
    """Create an Instagram post with text overlay"""
    try:
        data = request.get_json()
        topic = data.get('topic', 'general')
        fact = data.get('fact', '')
        brand_name = data.get('brand', 'FACTS')
        text_size = data.get('textSize', 64)
        text_x = data.get('textX', 50)
        text_y = data.get('textY', 75)
        brand_size = data.get('brandSize', 24)
        
        if not fact:
            return jsonify({
                'success': False,
                'error': 'No fact provided'
            }), 400
        
        # Select a random template based on topic
        templates = TEMPLATES.get(topic, TEMPLATES['general'])
        template_filename = random.choice(templates)
        template_path = os.path.join(app.static_folder, template_filename)
        
        # Create output filename
        timestamp = int(time.time())
        output_filename = f'instagram_post_{timestamp}.png'
        output_path = os.path.join(app.static_folder, output_filename)
        
        # Create the Instagram post
        create_instagram_post(template_path, fact, brand_name, output_path, text_size, text_x, text_y, brand_size)
        
        # Return the URL to the generated image
        image_url = f'/{output_filename}'
        
        return jsonify({
            'success': True,
            'image_path': image_url,
            'image_url': image_url
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_instagram_post(background_path, fact_text, brand_name, output_path, text_size=64, text_x=50, text_y=75, brand_size=24):
    """Create an Instagram post with text overlay on background image"""
    
    # Open the background image
    img = Image.open(background_path)
    img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # Create a drawing context
    draw = ImageDraw.Draw(img)
    
    # Try to load bold fonts, fallback to default if not available
    try:
        # Use dynamic font sizes based on parameters
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", text_size)
        brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", brand_size)
        viral_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
        viral_font = ImageFont.load_default()
    
    # Text styling
    text_color = (255, 255, 255)  # White text
    shadow_color = (0, 0, 0, 200)  # Strong black shadow
    
    # Convert text to uppercase for impact
    fact_text = fact_text.upper()
    brand_name = brand_name.upper()
    
    # Calculate text positioning
    img_width, img_height = img.size
    
    # Add "VIRAL" tag at top left corner
    viral_text = "VIRAL"
    viral_x = 40
    viral_y = 40
    
    # Draw VIRAL tag with shadow
    draw.text((viral_x+2, viral_y+2), viral_text, font=viral_font, fill=shadow_color)
    draw.text((viral_x, viral_y), viral_text, font=viral_font, fill=text_color)
    
    # Add brand name at top right corner
    brand_bbox = draw.textbbox((0, 0), brand_name, font=brand_font)
    brand_width = brand_bbox[2] - brand_bbox[0]
    brand_x = img_width - brand_width - 40
    brand_y = 40
    
    # Draw brand name with shadow
    draw.text((brand_x+2, brand_y+2), brand_name, font=brand_font, fill=shadow_color)
    draw.text((brand_x, brand_y), brand_name, font=brand_font, fill=text_color)
    
    # Wrap the main text more compactly
    wrapped_text = textwrap.fill(fact_text, width=16)  # Shorter lines for bottom placement
    
    # Position the main fact text based on user parameters
    lines = wrapped_text.split('\n')
    line_height = text_size + 10  # Dynamic line height based on font size
    total_text_height = len(lines) * line_height
    
    # Calculate position based on percentage parameters
    start_x = (img_width * text_x) // 100
    start_y = (img_height * text_y) // 100 - (total_text_height // 2)
    
    # Draw each line of the fact with stronger shadow
    for i, line in enumerate(lines):
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = start_x - (text_width // 2)  # Center horizontally around the X position
        y = start_y + (i * line_height)
        
        # Add stronger text shadow for better readability
        shadow_offset = 4
        draw.text((x+shadow_offset, y+shadow_offset), line, font=title_font, fill=shadow_color)
        draw.text((x, y), line, font=title_font, fill=text_color)
    
    # Save the final image
    img.save(output_path, 'PNG', quality=95)

@content_bp.route('/topics', methods=['GET'])
def get_topics():
    """Get available topic categories"""
    return jsonify({
        'success': True,
        'topics': list(TEMPLATES.keys())
    })

