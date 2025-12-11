"""
Parameter Handler - Processes user input and generates FIBO JSON configurations
"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class FIBOParameters:
    """Data class for FIBO generation parameters"""
    prompt: str
    ev_value: float = 12.0
    azimuth: float = 180.0
    color_profile: str = "sRGB"
    seed: int = 42
    steps: int = 50
    guidance_scale: float = 7.5
    negative_prompt: str = "low quality, blurry, distorted"
    width: int = 1024
    height: int = 1024

class ParameterHandler:
    """Handles parameter processing and JSON generation for FIBO"""
    
    def __init__(self):
        self.color_profiles = ["sRGB", "ACEScg", "Rec.2020", "DCI-P3"]
        self.ev_range = (8.0, 15.0)
        self.azimuth_range = (0.0, 360.0)
    
    def create_master_config(self, 
                           prompt: str,
                           ev_value: float = 12.0,
                           azimuth: float = 180.0,
                           color_profile: str = "sRGB",
                           seed: Optional[int] = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Create master FIBO configuration from user parameters
        
        Args:
            prompt: Text description of the scene/texture
            ev_value: Exposure value (8.0-15.0)
            azimuth: Light angle in degrees (0-360)
            color_profile: Color space profile
            seed: Random seed for reproducibility
            **kwargs: Additional parameters
            
        Returns:
            Master configuration dictionary
        """
        # Validate inputs
        self._validate_parameters(prompt, ev_value, azimuth, color_profile)
        
        # Generate seed if not provided
        if seed is None:
            seed = self._generate_seed_from_prompt(prompt)
        
        # Create base parameters
        params = FIBOParameters(
            prompt=prompt,
            ev_value=ev_value,
            azimuth=azimuth,
            color_profile=color_profile,
            seed=seed,
            **kwargs
        )
        
        # Convert to dictionary and add metadata
        config = asdict(params)
        config.update({
            "metadata": {
                "version": "1.0",
                "generator": "FIBO-HDRI-Studio",
                "lighting": {
                    "ev_value": ev_value,
                    "azimuth": azimuth,
                    "elevation": kwargs.get("elevation", 45.0)
                },
                "color": {
                    "profile": color_profile,
                    "bit_depth": 16,
                    "gamma": kwargs.get("gamma", 2.2)
                }
            }
        })
        
        logger.info(f"Created master config for prompt: '{prompt[:50]}...'")
        return config
    
    def create_hdri_config(self, master_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create HDRI-specific configuration from master config
        
        Args:
            master_config: Master FIBO configuration
            
        Returns:
            HDRI-specific configuration
        """
        hdri_config = master_config.copy()
        
        # HDRI-specific modifications
        hdri_config.update({
            "output_type": "hdri",
            "format": "equirectangular",
            "projection": "360_panoramic",
            "width": 2048,
            "height": 1024,
            "hdr_encoding": True,
            "bit_depth": 16,
            "file_format": "exr"
        })
        
        # Enhance prompt for HDRI generation
        original_prompt = hdri_config["prompt"]
        hdri_config["prompt"] = self._enhance_hdri_prompt(original_prompt, hdri_config)
        
        logger.info("Created HDRI configuration")
        return hdri_config
    
    def create_pbr_config(self, master_config: Dict[str, Any], texture_type: str) -> Dict[str, Any]:
        """
        Create PBR texture-specific configuration from master config
        
        Args:
            master_config: Master FIBO configuration
            texture_type: Type of PBR map (albedo, normal, roughness, ao)
            
        Returns:
            PBR texture-specific configuration
        """
        pbr_config = master_config.copy()
        
        # PBR-specific modifications
        pbr_config.update({
            "output_type": f"pbr_{texture_type}",
            "texture_type": texture_type,
            "tileable": True,
            "seamless": True,
            "width": 1024,
            "height": 1024,
            "bit_depth": 16,
            "file_format": "png"
        })
        
        # Enhance prompt for PBR generation
        original_prompt = pbr_config["prompt"]
        pbr_config["prompt"] = self._enhance_pbr_prompt(original_prompt, texture_type, pbr_config)
        
        # Adjust negative prompt for textures
        pbr_config["negative_prompt"] = "seams, visible edges, lighting baked in, shadows, highlights, non-tileable"
        
        logger.info(f"Created PBR {texture_type} configuration")
        return pbr_config
    
    def _validate_parameters(self, prompt: str, ev_value: float, azimuth: float, color_profile: str):
        """Validate input parameters"""
        if not prompt or len(prompt.strip()) == 0:
            raise ValueError("Prompt cannot be empty")
        
        if not (self.ev_range[0] <= ev_value <= self.ev_range[1]):
            raise ValueError(f"EV value must be between {self.ev_range[0]} and {self.ev_range[1]}")
        
        if not (self.azimuth_range[0] <= azimuth <= self.azimuth_range[1]):
            raise ValueError(f"Azimuth must be between {self.azimuth_range[0]} and {self.azimuth_range[1]}")
        
        if color_profile not in self.color_profiles:
            raise ValueError(f"Color profile must be one of: {', '.join(self.color_profiles)}")
    
    def _generate_seed_from_prompt(self, prompt: str) -> int:
        """Generate a deterministic seed from prompt"""
        return hash(prompt) % (2**31)
    
    def _enhance_hdri_prompt(self, prompt: str, config: Dict[str, Any]) -> str:
        """Enhance prompt for HDRI generation"""
        ev_value = config["ev_value"]
        azimuth = config["azimuth"]
        
        # Add lighting descriptors based on EV value
        if ev_value < 10.0:
            lighting_desc = "moody, dramatic lighting, low key"
        elif ev_value > 13.0:
            lighting_desc = "bright, high key lighting, well lit"
        else:
            lighting_desc = "balanced lighting, natural exposure"
        
        # Add directional lighting based on azimuth
        if 45 <= azimuth <= 135:
            direction_desc = "side lighting"
        elif 135 <= azimuth <= 225:
            direction_desc = "back lighting"
        elif 225 <= azimuth <= 315:
            direction_desc = "side lighting"
        else:
            direction_desc = "front lighting"
        
        enhanced_prompt = f"{prompt}, {lighting_desc}, {direction_desc}, 360 degree panoramic view, equirectangular projection, high dynamic range, professional HDRI"
        
        return enhanced_prompt
    
    def _enhance_pbr_prompt(self, prompt: str, texture_type: str, config: Dict[str, Any]) -> str:
        """Enhance prompt for PBR texture generation"""
        texture_descriptors = {
            "albedo": "diffuse color map, base color, no lighting, flat shading, material color",
            "normal": "normal map, surface detail, bump detail, purple and blue tones",
            "roughness": "roughness map, surface roughness, grayscale, material roughness",
            "ao": "ambient occlusion map, shadow detail, grayscale, cavity detail"
        }
        
        descriptor = texture_descriptors.get(texture_type, texture_descriptors["albedo"])
        enhanced_prompt = f"{prompt}, {descriptor}, seamless tileable texture, high resolution, material texture"
        
        return enhanced_prompt
    
    def save_config(self, config: Dict[str, Any], filepath: str):
        """Save configuration to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def load_config(self, filepath: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {filepath}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise