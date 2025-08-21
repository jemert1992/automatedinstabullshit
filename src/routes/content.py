import os
import random
import time
import base64
import io
from flask import Blueprint, request, jsonify, current_app as app
from PIL import Image
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
    """Create an Instagram post with background image and return base64-encoded PNG"""
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
        
        # Create the background image and return as base64
        base64_image = create_background_image_base64(template_path)
        
        # Prepare text overlay data for HTML rendering
        text_overlays = {
            'viral_tag': {
                'text': 'VIRAL',
                'position': {'x': 40, 'y': 40},
                'style': {
                    'fontSize': '20px',
                    'fontWeight': 'bold',
                    'color': 'white',
                    'textShadow': '2px 2px 4px rgba(0,0,0,0.8)',
                    'position': 'absolute',
                    'zIndex': 10
                }
            },
            'brand_name': {
                'text': brand_name.upper(),
                'position': {'x': f'calc(100% - {len(brand_name) * brand_size/2 + 40}px)', 'y': 40},
                'style': {
                    'fontSize': f'{brand_size}px',
                    'fontWeight': 'bold', 
                    'color': 'white',
                    'textShadow': '2px 2px 4px rgba(0,0,0,0.8)',
                    'position': 'absolute',
                    'right': '40px',
                    'zIndex': 10
                }
            },
            'main_fact': {
                'text': fact.upper(),
                'position': {'x': f'{text_x}%', 'y': f'{text_y}%'},
                'style': {
                    'fontSize': f'{text_size}px',
                    'fontWeight': 'bold',
                    'color': 'white',
                    'textShadow': '4px 4px 8px rgba(0,0,0,0.8)',
                    'position': 'absolute',
                    'left': f'{text_x}%',
                    'top': f'{text_y}%',
                    'transform': 'translate(-50%, -50%)',
                    'textAlign': 'center',
                    'maxWidth': '80%',
                    'lineHeight': '1.2',
                    'zIndex': 10,
                    'wordWrap': 'break-word'
                }
            }
        }
        
        return jsonify({
            'success': True,
            'background_image_base64': base64_image,
            'text_overlays': text_overlays,
            'image_dimensions': {'width': 1080, 'height': 1080}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_background_image_base64(background_path):
    """Create a background image and return it as base64-encoded string"""
    
    # Open and resize the background image
    img = Image.open(background_path)
    img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # Convert image to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG", quality=95)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

@content_bp.route('/topics', methods=['GET'])
def get_topics():
    """Get available topic categories"""
    return jsonify({
        'success': True,
        'topics': list(TEMPLATES.keys())
    })
