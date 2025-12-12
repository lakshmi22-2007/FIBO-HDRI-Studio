#!/usr/bin/env python3
"""
FIBO HDRI Studio - Main Web Application
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.web_ui import WebUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main application entry point"""
    try:
        # Initialize web UI with Stable Diffusion model
        web_ui = WebUI("runwayml/stable-diffusion-v1-5")
        
        # Run the application
        web_ui.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\nShutting down FIBO HDRI Studio...")
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()