"""
FIBO Agent Core - Handles FIBO model integration and generation calls
"""

import json
import torch
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from diffusers import StableDiffusionPipeline
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

logger = logging.getLogger(__name__)

class FIBOAgent:
    """Core agent for FIBO model interactions"""
    
    def __init__(self, model_path: str = "runwayml/stable-diffusion-v1-5", device: str = "auto"):
        """Initialize FIBO agent with model loading"""
        self.device = self._get_device(device)
        self.model_path = model_path
        self.pipeline = None
        self._load_model()
        
    def _get_device(self, device: str) -> str:
        """Determine the best device for inference"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device
    
    def _load_model(self):
        """Load the Stable Diffusion model pipeline"""
        try:
            logger.info(f"Loading Stable Diffusion model from {self.model_path}")
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            self.pipeline = self.pipeline.to(self.device)
            
            # Enable memory efficient settings
            if self.device != "cpu":
                self.pipeline.enable_attention_slicing()
                
            logger.info("Stable Diffusion model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate_hdri(self, config: Dict[str, Any]) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        Generate 360° HDRI from configuration
        
        Args:
            config: FIBO configuration dictionary
            
        Returns:
            Tuple of (generated_image, metadata)
        """
        # Prepare HDRI-specific parameters
        hdri_config = self._prepare_hdri_config(config)
        
        # Generate the HDRI
        prompt = hdri_config["prompt"]
        
        # Add HDRI-specific prompt modifications
        hdri_prompt = f"{prompt}, 360 degree panoramic view, equirectangular projection, high dynamic range, professional lighting, environment map, spherical panorama"
        
        logger.info(f"Generating HDRI with prompt: {hdri_prompt}")
        
        # Generate base image
        result = self.pipeline(
            prompt=hdri_prompt,
            negative_prompt=hdri_config.get("negative_prompt", "low quality, blurry, distorted, people, faces"),
            width=1024,  # Start with square, then resize
            height=512,   # 2:1 aspect ratio
            num_inference_steps=hdri_config.get("steps", 30),
            guidance_scale=hdri_config.get("guidance_scale", 7.5),
            generator=torch.Generator(device=self.device).manual_seed(hdri_config.get("seed", 42))
        )
        
        # Post-process for HDRI characteristics
        hdri_image = self._enhance_for_hdri(result.images[0], hdri_config)
        
        metadata = {
            "type": "hdri",
            "config": hdri_config,
            "format": "equirectangular",
            "bit_depth": 16
        }
        
        return hdri_image, metadata
    
    def generate_pbr_texture(self, config: Dict[str, Any], texture_type: str = "albedo") -> Tuple[Image.Image, Dict[str, Any]]:
        """
        Generate PBR texture map from configuration
        
        Args:
            config: FIBO configuration dictionary
            texture_type: Type of PBR map (albedo, normal, roughness, ao)
            
        Returns:
            Tuple of (generated_image, metadata)
        """
        # Prepare PBR-specific parameters
        pbr_config = self._prepare_pbr_config(config, texture_type)
        
        prompt = pbr_config["prompt"]
        
        # Add texture-specific prompt modifications
        texture_prompts = {
            "albedo": f"{prompt}, seamless tileable texture, diffuse color map, no lighting, flat lighting",
            "normal": f"{prompt}, normal map, purple and blue tones, surface detail, seamless tileable",
            "roughness": f"{prompt}, roughness map, grayscale, surface roughness detail, seamless tileable",
            "ao": f"{prompt}, ambient occlusion map, grayscale, shadow detail, seamless tileable"
        }
        
        texture_prompt = texture_prompts.get(texture_type, texture_prompts["albedo"])
        
        logger.info(f"Generating {texture_type} texture with prompt: {texture_prompt}")
        
        result = self.pipeline(
            prompt=texture_prompt,
            negative_prompt=pbr_config.get("negative_prompt", "seams, visible edges, lighting, shadows, people, faces"),
            width=512,  # Smaller for faster generation
            height=512,
            num_inference_steps=pbr_config.get("steps", 25),
            guidance_scale=pbr_config.get("guidance_scale", 7.5),
            generator=torch.Generator(device=self.device).manual_seed(pbr_config.get("seed", 42))
        )
        
        # Make texture tileable
        texture_image = self._make_tileable(result.images[0])
        
        metadata = {
            "type": f"pbr_{texture_type}",
            "config": pbr_config,
            "tileable": True,
            "bit_depth": 16
        }
        
        return texture_image, metadata
    
    def _prepare_hdri_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare configuration specific for HDRI generation"""
        hdri_config = config.copy()
        
        # HDRI-specific modifications
        hdri_config.update({
            "width": 2048,
            "height": 1024,
            "format": "equirectangular",
            "hdr": True
        })
        
        return hdri_config
    
    def _prepare_pbr_config(self, config: Dict[str, Any], texture_type: str) -> Dict[str, Any]:
        """Prepare configuration specific for PBR texture generation"""
        pbr_config = config.copy()
        
        # PBR-specific modifications
        pbr_config.update({
            "width": 1024,
            "height": 1024,
            "tileable": True,
            "texture_type": texture_type
        })
        
        return pbr_config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate FIBO configuration against schema"""
        required_fields = ["prompt", "ev_value", "azimuth"]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate ranges
        if not (8.0 <= config["ev_value"] <= 15.0):
            logger.error(f"EV value {config['ev_value']} out of range (8.0-15.0)")
            return False
            
        if not (0 <= config["azimuth"] <= 360):
            logger.error(f"Azimuth {config['azimuth']} out of range (0-360)")
            return False
        
        return True
    
    def _enhance_for_hdri(self, image: Image.Image, config: Dict[str, Any]) -> Image.Image:
        """Enhance image for HDRI characteristics"""
        # Resize to proper HDRI aspect ratio (2:1)
        hdri_image = image.resize((1024, 512), Image.Resampling.LANCZOS)
        
        # Apply EV-based brightness adjustment
        ev_value = config.get("ev_value", 12.0)
        brightness_factor = self._ev_to_brightness_factor(ev_value)
        
        enhancer = ImageEnhance.Brightness(hdri_image)
        hdri_image = enhancer.enhance(brightness_factor)
        
        # Apply contrast enhancement for HDR look
        contrast_enhancer = ImageEnhance.Contrast(hdri_image)
        hdri_image = contrast_enhancer.enhance(1.2)
        
        return hdri_image
    
    def _ev_to_brightness_factor(self, ev_value: float) -> float:
        """Convert EV value to brightness enhancement factor"""
        # EV 8.0 = dark (0.6x), EV 12.0 = normal (1.0x), EV 15.0 = bright (1.8x)
        # Linear interpolation between these points
        if ev_value <= 8.0:
            return 0.6
        elif ev_value >= 15.0:
            return 1.8
        else:
            # Linear interpolation
            return 0.6 + (ev_value - 8.0) * (1.8 - 0.6) / (15.0 - 8.0)
    
    def _make_tileable(self, image: Image.Image) -> Image.Image:
        """Make texture tileable using edge blending"""
        width, height = image.size
        
        # Create a copy to work with
        tileable = image.copy()
        
        # Simple edge blending - blend left/right edges
        blend_width = width // 8
        
        # Get edge strips
        left_strip = image.crop((0, 0, blend_width, height))
        right_strip = image.crop((width - blend_width, 0, width, height))
        
        # Blend the edges
        for x in range(blend_width):
            alpha = x / blend_width
            for y in range(height):
                left_pixel = left_strip.getpixel((x, y))
                right_pixel = right_strip.getpixel((blend_width - 1 - x, y))
                
                # Blend pixels
                if isinstance(left_pixel, tuple):
                    blended = tuple(int(left_pixel[i] * (1 - alpha) + right_pixel[i] * alpha) 
                                  for i in range(len(left_pixel)))
                else:
                    blended = int(left_pixel * (1 - alpha) + right_pixel * alpha)
                
                tileable.putpixel((x, y), blended)
                tileable.putpixel((width - 1 - x, y), blended)
        
        return tileable