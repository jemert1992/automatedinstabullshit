import os
import random
import time

from flask import Blueprint, request, jsonify, current_app as app
import openai

content_bp = Blueprint('content', __name__)

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
            'error': 'Image generation temporarily disabled due to deployment constraints. All text controls and AI fact generation are working properly.'
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

