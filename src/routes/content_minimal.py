import os
import random
import time

from flask import Blueprint, request, jsonify, current_app as app

content_bp = Blueprint('content', __name__)

# Sample facts for each category
SAMPLE_FACTS = {
    'real_estate': [
        "WORLD'S MOST EXPENSIVE HOME COSTS MORE THAN SOME COUNTRIES' GDP",
        "TOKYO APARTMENTS SELL FOR LESS THAN A CAR",
        "MONACO HAS THE HIGHEST PROPERTY PRICES PER SQUARE METER GLOBALLY",
        "NEW YORK'S CENTRAL PARK IS WORTH MORE THAN ENTIRE COUNTRIES",
        "DUBAI BUILDS A NEW SKYSCRAPER EVERY 3 DAYS ON AVERAGE"
    ],
    'yachts': [
        "WORLD'S LARGEST YACHT HAS ITS OWN SUBMARINE GARAGE",
        "BILLIONAIRE'S YACHT COSTS $1 MILLION PER WEEK TO MAINTAIN",
        "SOME LUXURY YACHTS HAVE THEIR OWN HELICOPTER LANDING PADS",
        "THE MOST EXPENSIVE YACHT EVER SOLD COST $4.8 BILLION",
        "MEGA YACHTS CONSUME MORE FUEL THAN SMALL TOWNS"
    ],
    'general': [
        "OCTOPUSES HAVE THREE HEARTS AND BLUE BLOOD",
        "HONEY NEVER EXPIRES - 3000 YEAR OLD HONEY IS STILL EDIBLE",
        "BANANAS ARE BERRIES BUT STRAWBERRIES AREN'T",
        "A GROUP OF FLAMINGOS IS CALLED A 'FLAMBOYANCE'",
        "SHARKS HAVE BEEN AROUND LONGER THAN TREES"
    ]
}

@content_bp.route('/generate-fact', methods=['POST'])
def generate_fact():
    """Generate a fact based on the provided topic"""
    try:
        data = request.get_json()
        topic = data.get('topic', 'general')
        
        # Get a random fact from the sample facts
        facts = SAMPLE_FACTS.get(topic, SAMPLE_FACTS['general'])
        fact = random.choice(facts)
        
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
    """Create an Instagram post (simplified version without image processing)"""
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
        
        # For now, return success without creating actual image
        # This allows the UI controls to work properly
        return jsonify({
            'success': False,
            'error': 'Image generation temporarily disabled due to deployment constraints. All text controls and fact generation are working properly. Settings: Text Size: {}, Position: {}%, {}%, Brand Size: {}'.format(text_size, text_x, text_y, brand_size)
        }), 500
        
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
        'topics': ['general', 'real_estate', 'yachts']
    })

