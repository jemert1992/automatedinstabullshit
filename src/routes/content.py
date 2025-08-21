import os
import random
import time
from flask import Blueprint, request, jsonify, current_app as app, send_file
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

# Ensure /tmp directory exists for Render.com compatibility
TMP_DIR = '/tmp'
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

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
    """Create an Instagram post with background image and return text overlay data"""
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
        
        # Create output filename for the background image - save to /tmp for Render.com
        timestamp = int(time.time())
        output_filename = f'instagram_bg_{timestamp}.png'
        output_path = os.path.join(TMP_DIR, output_filename)
        
        # Create the background image without text
        create_background_image(template_path, output_path)
        
        # Return the dynamic image URL for the new route
        background_url = f'/api/get-image/{output_filename}'
        
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
            'background_image': background_url,
            'text_overlays': text_overlays,
            'image_dimensions': {'width': 1080, 'height': 1080}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@content_bp.route('/api/get-image/<filename>', methods=['GET'])
def get_image(filename):
    """Serve images from /tmp directory for Render.com compatibility"""
    try:
        # Validate filename to prevent directory traversal
        if not filename or '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
            
        file_path = os.path.join(TMP_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        # Serve the file
        return send_file(file_path, mimetype='image/png')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_background_image(background_path, output_path):
    """Create a background image without text overlay"""
    
    # Open and resize the background image
    img = Image.open(background_path)
    img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # Save the background image without any text to /tmp directory
    img.save(output_path, 'PNG', quality=95)

@content_bp.route('/topics', methods=['GET'])
def get_topics():
    """Get available topic categories"""
    return jsonify({
        'success': True,
        'topics': list(TEMPLATES.keys())
    })
