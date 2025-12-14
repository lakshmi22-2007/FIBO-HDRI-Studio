#!/usr/bin/env python3
"""
FIBO HDRI Studio - Demo Mode Web Server
Runs without ML dependencies
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
import time
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# Store generation results
generation_results = {}

@app.route('/')
def index():
    """Main interface page"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate HDRI and PBR textures in demo mode"""
    try:
        data = request.get_json()
        
        # Extract parameters
        prompt = data.get('prompt', '')
        ev_value = float(data.get('ev_value', 12.0))
        azimuth = float(data.get('azimuth', 180.0))
        color_profile = data.get('color_profile', 'sRGB')
        generate_hdri = data.get('generate_hdri', True)
        generate_textures = data.get('generate_textures', True)
        texture_types = data.get('texture_types', ['albedo'])
        
        logger.info(f"Demo generation request: {prompt}")
        
        # Simulate processing time
        time.sleep(1)
        seed = random.randint(1000, 9999)
        
        results = {
            'success': True,
            'config': {
                'prompt': prompt,
                'ev_value': ev_value,
                'azimuth': azimuth,
                'color_profile': color_profile,
                'seed': seed
            },
            'files': {},
            'demo_mode': True
        }
        
        if generate_hdri:
            results['files']['hdri'] = f"demo_hdri_{seed}.png"
            logger.info(f"Generated HDRI: {results['files']['hdri']}")
        
        if generate_textures:
            results['files']['textures'] = {
                tex_type: f"demo_{tex_type}_{seed}.png" 
                for tex_type in texture_types
            }
            logger.info(f"Generated textures: {list(results['files']['textures'].keys())}")
        
        results['result_id'] = str(seed)
        generation_results[str(seed)] = results
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/presets')
def get_presets():
    """Get predefined parameter presets"""
    presets = {
        'sunny_day': {
            'name': 'Sunny Day',
            'ev_value': 14.0,
            'azimuth': 135.0,
            'color_profile': 'sRGB'
        },
        'golden_hour': {
            'name': 'Golden Hour',
            'ev_value': 11.0,
            'azimuth': 270.0,
            'color_profile': 'sRGB'
        },
        'overcast': {
            'name': 'Overcast',
            'ev_value': 10.0,
            'azimuth': 180.0,
            'color_profile': 'sRGB'
        },
        'dramatic': {
            'name': 'Dramatic',
            'ev_value': 8.5,
            'azimuth': 225.0,
            'color_profile': 'ACEScg'
        }
    }
    return jsonify(presets)

@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'demo_mode',
        'model_loaded': False,
        'device': 'cpu',
        'mode': 'demo',
        'message': 'Running in demo mode - ML dependencies not required',
        'supported_formats': {
            'hdri': ['png', 'tiff'],
            'textures': ['png', 'tiff']
        }
    })

@app.route('/api/download/<result_id>/<file_type>')
def download_file(result_id, file_type):
    """Download generated files (demo mode - returns mock data)"""
    return jsonify({'error': 'Download not available in demo mode'}), 404

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎬 FIBO HDRI Studio - Demo Mode")
    print("="*60)
    print("\n✅ Running in DEMO MODE - No ML dependencies required")
    print("📍 Server starting at: http://localhost:5000")
    print("\n💡 This demonstrates the UI and workflow")
    print("   For full generation, install ML dependencies\n")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
