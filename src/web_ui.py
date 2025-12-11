"""
Web UI - Flask-based web interface for FIBO HDRI Studio
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Import components (will be mocked for demo)
try:
    from .fibo_agent import FIBOAgent
    from .parameter_handler import ParameterHandler
    from .post_processor import PostProcessor
    FULL_FUNCTIONALITY = True
except ImportError:
    # Mock classes for demo mode
    FULL_FUNCTIONALITY = False

logger = logging.getLogger(__name__)

class WebUI:
    """Flask web interface for FIBO HDRI Studio"""
    
    def __init__(self, model_path: str = "briaai/BRIA-2.3"):
        self.app = Flask(__name__, 
                        template_folder='../templates',
                        static_folder='../static')
        CORS(self.app)
        
        # Initialize components (demo mode if dependencies not available)
        if FULL_FUNCTIONALITY:
            self.fibo_agent = FIBOAgent(model_path)
            self.parameter_handler = ParameterHandler()
            self.post_processor = PostProcessor()
        else:
            logger.warning("Running in demo mode - ML dependencies not available")
            self.fibo_agent = None
            self.parameter_handler = None
            self.post_processor = None
        
        # Setup routes
        self._setup_routes()
        
        # Store generation results
        self.generation_results = {}
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main interface page"""
            return render_template('index.html')
        
        @self.app.route('/api/generate', methods=['POST'])
        def generate():
            """Generate HDRI and PBR textures"""
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
                
                if not FULL_FUNCTIONALITY:
                    # Demo mode - return mock results
                    import time
                    import random
                    
                    # Simulate processing time
                    time.sleep(2)
                    
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
                        results['files']['hdri'] = f"demo_hdri_{seed}.exr"
                    
                    if generate_textures:
                        results['files']['textures'] = {
                            tex_type: f"demo_{tex_type}_{seed}.png" 
                            for tex_type in texture_types
                        }
                    
                    results['result_id'] = str(seed)
                    self.generation_results[str(seed)] = results
                    
                    return jsonify(results)
                
                # Full functionality mode
                master_config = self.parameter_handler.create_master_config(
                    prompt=prompt,
                    ev_value=ev_value,
                    azimuth=azimuth,
                    color_profile=color_profile
                )
                
                results = {
                    'success': True,
                    'config': master_config,
                    'files': {}
                }
                
                # Generate HDRI if requested
                if generate_hdri:
                    hdri_config = self.parameter_handler.create_hdri_config(master_config)
                    hdri_image, hdri_metadata = self.fibo_agent.generate_hdri(hdri_config)
                    
                    # Save HDRI
                    filename = f"hdri_{master_config['seed']}"
                    hdri_path = self.post_processor.process_hdri(
                        hdri_image, hdri_metadata, filename
                    )
                    results['files']['hdri'] = hdri_path
                
                # Generate PBR textures if requested
                if generate_textures:
                    texture_paths = {}
                    for texture_type in texture_types:
                        pbr_config = self.parameter_handler.create_pbr_config(
                            master_config, texture_type
                        )
                        texture_image, texture_metadata = self.fibo_agent.generate_pbr_texture(
                            pbr_config, texture_type
                        )
                        
                        # Save texture
                        filename = f"{texture_type}_{master_config['seed']}"
                        texture_path = self.post_processor.process_pbr_texture(
                            texture_image, texture_metadata, filename
                        )
                        texture_paths[texture_type] = texture_path
                    
                    results['files']['textures'] = texture_paths
                
                # Create asset package if both HDRI and textures were generated
                if generate_hdri and generate_textures:
                    package_name = f"asset_package_{master_config['seed']}"
                    package_path = self.post_processor.create_asset_package(
                        results['files'].get('hdri'),
                        results['files'].get('textures', {}),
                        master_config,
                        package_name
                    )
                    results['files']['package'] = package_path
                
                # Store results for download
                result_id = str(master_config['seed'])
                self.generation_results[result_id] = results
                results['result_id'] = result_id
                
                return jsonify(results)
                
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/download/<result_id>/<file_type>')
        def download_file(result_id, file_type):
            """Download generated files"""
            try:
                if result_id not in self.generation_results:
                    return jsonify({'error': 'Result not found'}), 404
                
                results = self.generation_results[result_id]
                files = results.get('files', {})
                
                if file_type == 'hdri' and 'hdri' in files:
                    return send_file(files['hdri'], as_attachment=True)
                elif file_type in files.get('textures', {}):
                    return send_file(files['textures'][file_type], as_attachment=True)
                elif file_type == 'package' and 'package' in files:
                    # Create zip of package directory
                    import zipfile
                    import tempfile
                    
                    package_dir = Path(files['package'])
                    zip_path = tempfile.mktemp(suffix='.zip')
                    
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_path in package_dir.rglob('*'):
                            if file_path.is_file():
                                arcname = file_path.relative_to(package_dir)
                                zipf.write(file_path, arcname)
                    
                    return send_file(zip_path, as_attachment=True, 
                                   download_name=f"{package_dir.name}.zip")
                else:
                    return jsonify({'error': 'File not found'}), 404
                    
            except Exception as e:
                logger.error(f"Download failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/presets')
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
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status"""
            if not FULL_FUNCTIONALITY:
                return jsonify({
                    'status': 'demo_mode',
                    'model_loaded': False,
                    'device': 'cpu',
                    'demo_mode': True,
                    'supported_formats': {
                        'hdri': ['exr', 'hdr', 'tiff'],
                        'textures': ['png', 'tiff', 'jpg']
                    }
                })
            
            return jsonify({
                'status': 'ready',
                'model_loaded': self.fibo_agent.pipeline is not None,
                'device': self.fibo_agent.device,
                'supported_formats': {
                    'hdri': self.post_processor.hdri_formats,
                    'textures': self.post_processor.texture_formats
                }
            })
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application"""
        logger.info(f"Starting FIBO HDRI Studio web interface on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)