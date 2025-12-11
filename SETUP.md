# FIBO HDRI Studio - Setup Guide

## Prerequisites

### System Requirements
- Python 3.8 or higher
- 8GB+ RAM (16GB recommended)
- NVIDIA GPU with 6GB+ VRAM (for optimal performance)
- 10GB+ free disk space

### Required Software
- Git
- Python pip
- CUDA toolkit (for GPU acceleration)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd fibo-hdri-studio
```

### 2. Create Virtual Environment
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n fibo-hdri python=3.9
conda activate fibo-hdri
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install OpenEXR (Optional but Recommended)
For full HDR support, install OpenEXR:

**Ubuntu/Debian:**
```bash
sudo apt-get install libopenexr-dev
pip install OpenEXR
```

**macOS:**
```bash
brew install openexr
pip install OpenEXR
```

**Windows:**
```bash
# Download pre-compiled wheels from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#openexr
pip install OpenEXR-1.3.2-cp39-cp39-win_amd64.whl
```

### 5. Download FIBO Model
The FIBO model will be automatically downloaded on first use. To pre-download:

```python
from transformers import StableDiffusionPipeline
pipeline = StableDiffusionPipeline.from_pretrained("briaai/BRIA-2.3")
```

## Configuration

### Environment Variables (Optional)
Create a `.env` file in the project root:

```bash
# Model configuration
FIBO_MODEL_PATH=briaai/BRIA-2.3
FIBO_DEVICE=auto  # auto, cuda, cpu, mps

# Output configuration
DEFAULT_OUTPUT_DIR=./outputs
DEFAULT_HDRI_FORMAT=exr
DEFAULT_TEXTURE_FORMAT=png

# Web interface
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false

# Hugging Face token (if using private models)
HF_TOKEN=your_token_here
```

### GPU Memory Optimization
For systems with limited VRAM, add these optimizations:

```python
# In src/fibo_agent.py, modify the pipeline loading:
self.pipeline.enable_attention_slicing()
self.pipeline.enable_sequential_cpu_offload()
```

## Verification

### Test CLI Interface
```bash
python generate.py --prompt "test cobblestone" --ev-value 12.0 --azimuth 180 --no-textures
```

### Test Web Interface
```bash
python app.py
```
Then open http://localhost:5000 in your browser.

### Test Model Loading
```bash
python -c "from src.fibo_agent import FIBOAgent; agent = FIBOAgent(); print('Model loaded successfully')"
```

## Troubleshooting

### Common Issues

**1. CUDA Out of Memory**
- Reduce batch size or image resolution
- Enable memory optimization flags
- Use CPU inference as fallback

**2. OpenEXR Import Error**
- Install system OpenEXR libraries
- Use TIFF format as fallback for HDR

**3. Model Download Fails**
- Check internet connection
- Verify Hugging Face access
- Use local model path if available

**4. Slow Generation**
- Ensure GPU is being used
- Check CUDA installation
- Reduce inference steps

### Performance Tips

1. **GPU Acceleration**: Ensure CUDA is properly installed
2. **Memory Management**: Use attention slicing for large images
3. **Batch Processing**: Generate multiple textures in sequence
4. **Model Caching**: Keep model loaded between generations

## Development Setup

### Additional Dependencies for Development
```bash
pip install pytest black flake8 mypy
```

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

## Docker Setup (Alternative)

### Build Docker Image
```bash
docker build -t fibo-hdri-studio .
```

### Run Container
```bash
docker run -p 5000:5000 -v $(pwd)/outputs:/app/outputs fibo-hdri-studio
```

## Next Steps

1. Review the [Usage Guide](USAGE.md)
2. Check out [Example Workflows](examples/)
3. Read the [API Documentation](API.md)
4. Join our [Community Discord](https://discord.gg/fibo-hdri)