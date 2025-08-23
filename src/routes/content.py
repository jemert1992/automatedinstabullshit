import os
import io
import base64
from flask import Blueprint, jsonify, request
from PIL import Image, ImageDraw, ImageFont

# Create the blueprint for content routes
content_bp = Blueprint('content', __name__)

# Global error handler for all exceptions
@content_bp.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions and return proper JSON error response"""
    return jsonify({
        'success': False,
        'error': str(e),
        'message': 'An unexpected error occurred'
    }), 500

def wrap_text(text, font, draw, max_width):
    """Wrap text to fit within specified width"""
    words = text.split()
    lines = []
    while words:
        line = ''
        i = 0
        while i < len(words):
            test_line = (line + ' ' + words[i]).strip() if line else words[i]
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w > max_width and line:
                break
            else:
                line = test_line
                i += 1
        lines.append(line)
        words = words[i:]
    return lines

def create_insta_post_img(
    background_path, fact, brand_name, text_size=84, text_x=50, text_y=10, brand_size=36):
    """Create Instagram post image with given parameters"""
    try:
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
        line_height = bbox_A[3] - bbox_A[1]
        band_height = line_height * len(fact_lines) + 48
        band_y0 = 24
        band_y1 = band_y0 + band_height
        draw.rectangle([(0, band_y0), (1080, band_y1)], fill=(0, 0, 0, 190))
        
        # VIRAL tag centering
        viral_bbox = draw.textbbox((0, 0), viral_tag, font=viral_font)
        viral_w = viral_bbox[2] - viral_bbox[0]
        draw.text(((1080 - viral_w) // 2, 8), viral_tag, font=viral_font, fill="red")
        
        # Draw each line of headline centered, with shadow for readability
        top = band_y0 + 24
        for line in fact_lines:
            bbox = draw.textbbox((0, 0), line, font=fact_font)
            w = bbox[2] - bbox[0]
            draw.text(((1080 - w) // 2 + 2, top + 2), line, font=fact_font, fill="black")
            draw.text(((1080 - w) // 2, top), line, font=fact_font, fill="white")
            top += line_height
        
        # Brand mark at bottom center
        brand_bbox = draw.textbbox((0, 0), brand_name, font=brand_font)
        brand_w = brand_bbox[2] - brand_bbox[0]
        brand_h = brand_bbox[3] - brand_bbox[1]
        bx = (1080 - brand_w) // 2
        by = 1080 - brand_h - 40
        draw.text((bx + 2, by + 2), brand_name, font=brand_font, fill="black")
        draw.text((bx, by), brand_name, font=brand_font, fill="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        raise Exception(f"Failed to create Instagram post image: {str(e)}")

@content_bp.route('/generate', methods=['POST'])
def generate_content():
    """Generate Instagram post content"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate required fields
        required_fields = ['fact', 'brand_name', 'background_path']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'message': 'Please provide all required fields'
            }), 400
        
        # Generate the image
        image_data = create_insta_post_img(
            data['background_path'],
            data['fact'],
            data['brand_name'],
            data.get('text_size', 84),
            data.get('text_x', 50),
            data.get('text_y', 10),
            data.get('brand_size', 36)
        )
        
        return jsonify({
            'success': True,
            'message': 'Content generated successfully',
            'data': {
                'image_data': image_data,
                'fact': data['fact'],
                'brand_name': data['brand_name']
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate content'
        }), 500

@content_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Content service is healthy',
        'status': 'ok'
    }), 200

@content_bp.route('/validate', methods=['POST'])
def validate_content():
    """Validate content parameters"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Check for required fields
        required_fields = ['fact', 'brand_name', 'background_path']
        validation_results = {}
        
        for field in required_fields:
            if field not in data:
                validation_results[field] = {'valid': False, 'error': 'Field is required'}
            elif not data[field] or not str(data[field]).strip():
                validation_results[field] = {'valid': False, 'error': 'Field cannot be empty'}
            else:
                validation_results[field] = {'valid': True, 'error': None}
        
        # Check if background path exists (if provided)
        if 'background_path' in data and data['background_path']:
            if not os.path.exists(data['background_path']):
                validation_results['background_path'] = {
                    'valid': False, 
                    'error': 'Background image file does not exist'
                }
        
        all_valid = all(result['valid'] for result in validation_results.values())
        
        return jsonify({
            'success': True,
            'message': 'Validation completed',
            'data': {
                'valid': all_valid,
                'validation_results': validation_results
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to validate content'
        }), 500
