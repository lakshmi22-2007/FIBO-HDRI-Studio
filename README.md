# 🎬 FIBO HDRI Studio Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)

A professional deterministic HDRI and PBR texture generation tool for VFX and 3D workflows. Generate matched 360° HDRI environments and tileable PBR texture sets with precise lighting control.

## Overview

This agent generates matched HDRI environments and PBR texture sets from a single prompt, providing:
- 360° equirectangular HDRI maps (16-bit EXR format)
- Tileable PBR texture maps (Albedo, Normal, Roughness, AO)
- Deterministic control via EV values and lighting parameters
- JSON-based repeatability for production workflows

## ✨ Key Features

- 🎯 **Deterministic Generation**: Same prompt + parameters = identical results
- 🎨 **Professional Formats**: 16-bit EXR for HDRI, 16-bit PNG/TIFF for textures  
- 💡 **Lighting Consistency**: HDRI and PBR maps share the same lighting characteristics
- 🔧 **Production Ready**: Direct integration with Blender, Unity, and other 3D tools
- 🌐 **Web Interface**: Professional UI with real-time parameter control
- ⚡ **CLI Support**: Batch processing and automation capabilities
- 📦 **Asset Packaging**: Organized output with complete metadata

## 🚀 Quick Start

### Web Interface (Recommended)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the web server
python app.py

# 3. Open browser to http://localhost:5000
```

### CLI Interface
```bash
# Generate complete asset package
python generate.py \
  --prompt "rough roman cobblestone street" \
  --ev-value 12.0 \
  --azimuth 180 \
  --texture-types albedo normal roughness \
  --package
```

### Demo Mode
```bash
# Run interactive demonstration
python demo.py
```

## Project Structure

```
fibo-hdri-studio/
├── src/
│   ├── fibo_agent.py      # Core FIBO API integration
│   ├── parameter_handler.py # Input processing and JSON generation
│   ├── post_processor.py   # Output formatting and saving
│   └── web_ui.py          # Flask web interface
├── examples/
│   ├── outputs/           # Sample generated assets
│   └── configs/           # Example JSON configurations
├── app.py                 # Main web application
├── generate.py            # CLI interface
└── requirements.txt
```

## Usage

### Web Interface
Access the web UI at `http://localhost:5000` to:
- Enter text prompts
- Adjust EV values (8.0-15.0)
- Set azimuth angles (0°-360°)
- Select color profiles
- Generate matched HDRI and PBR sets

### CLI Interface
```bash
python generate.py \
  --prompt "weathered brick wall" \
  --ev 10.5 \
  --azimuth 225 \
  --color-profile sRGB \
  --output-dir ./outputs
```

## Technical Details

The agent uses a dual-call approach:
1. **HDRI Generation**: 360° equirectangular projection with HDR color space
2. **PBR Generation**: Tileable texture maps using consistent lighting parameters

Each generation saves the exact FIBO JSON configuration for repeatability.

## Requirements

- Python 3.8+
- FIBO model access (Hugging Face)
- 8GB+ VRAM recommended
- Storage space for 16-bit assets

## License

MIT License - See LICENSE file for details