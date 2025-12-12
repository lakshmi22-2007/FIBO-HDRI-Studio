"""
Simple Image Generator - Creates procedural HDRI and texture images
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import random
import math
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class SimpleGenerator:
    """Simple procedural image generator for demo purposes"""
    
    def __init__(self):
        self.seed_value = None
    
    def generate_hdri(self, config: Dict[str, Any]) -> Tuple[Image.Image, Dict[str, Any]]:
        """Generate a procedural HDRI-style image"""
        seed = config.get("seed", 42)
        random.seed(seed)
        np.random.seed(seed)
        
        prompt = config.get("prompt", "")
        ev_value = config.get("ev_value", 12.0)
        azimuth = config.get("azimuth", 180.0)
        
        # Create base HDRI image (2:1 aspect ratio)
        width, height = 1024, 512
        
        # Generate sky gradient based on EV value
        hdri_image = self._create_sky_gradient(width, height, ev_value, azimuth)
        
        # Add environment elements based on prompt
        hdri_image = self._add_environment_elements(hdri_image, prompt, ev_value)
        
        # Apply HDR-like processing
        hdri_image = self._apply_hdr_processing(hdri_image, ev_value)
        
        metadata = {
            "type": "hdri",
            "config": config,
            "format": "equirectangular",
            "bit_depth": 16,
            "generator": "SimpleGenerator"
        }
        
        logger.info(f"Generated HDRI for prompt: '{prompt}' with EV: {ev_value}")
        return hdri_image, metadata
    
    def generate_pbr_texture(self, config: Dict[str, Any], texture_type: str) -> Tuple[Image.Image, Dict[str, Any]]:
        """Generate a procedural PBR texture"""
        seed = config.get("seed", 42)
        random.seed(seed)
        np.random.seed(seed)
        
        prompt = config.get("prompt", "")
        
        # Create base texture (square for tiling)
        size = 512
        
        if texture_type == "albedo":
            texture_image = self._create_albedo_texture(size, prompt)
        elif texture_type == "normal":
            texture_image = self._create_normal_texture(size, prompt)
        elif texture_type == "roughness":
            texture_image = self._create_roughness_texture(size, prompt)
        elif texture_type == "ao":
            texture_image = self._create_ao_texture(size, prompt)
        else:
            texture_image = self._create_albedo_texture(size, prompt)
        
        # Make tileable
        texture_image = self._make_tileable(texture_image)
        
        metadata = {
            "type": f"pbr_{texture_type}",
            "config": config,
            "tileable": True,
            "bit_depth": 16,
            "generator": "SimpleGenerator"
        }
        
        logger.info(f"Generated {texture_type} texture for prompt: '{prompt}'")
        return texture_image, metadata
    
    def _create_sky_gradient(self, width: int, height: int, ev_value: float, azimuth: float) -> Image.Image:
        """Create a sky gradient based on EV value"""
        # Create gradient from top to bottom
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Determine colors based on EV value
        if ev_value < 9.0:
            # Dark/night sky
            top_color = (20, 25, 40)
            bottom_color = (60, 70, 100)
        elif ev_value < 11.0:
            # Overcast/moody
            top_color = (120, 130, 140)
            bottom_color = (180, 190, 200)
        elif ev_value < 13.0:
            # Normal daylight
            top_color = (135, 206, 235)  # Sky blue
            bottom_color = (255, 255, 240)  # Light yellow
        else:
            # Bright/sunny
            top_color = (100, 149, 237)  # Bright blue
            bottom_color = (255, 255, 200)  # Bright yellow
        
        # Create vertical gradient
        for y in range(height):
            ratio = y / height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add sun/light source based on azimuth
        sun_x = int((azimuth / 360.0) * width)
        sun_y = int(height * 0.3)  # Upper third of image
        
        # Draw sun glow
        sun_size = 40 if ev_value > 12.0 else 20
        sun_color = (255, 255, 200) if ev_value > 11.0 else (200, 200, 150)
        
        # Create radial gradient for sun
        for radius in range(sun_size, 0, -2):
            alpha = 1.0 - (radius / sun_size)
            color = tuple(int(c * alpha + 255 * (1 - alpha)) for c in sun_color)
            draw.ellipse([sun_x - radius, sun_y - radius, 
                         sun_x + radius, sun_y + radius], 
                        fill=color)
        
        return image
    
    def _add_environment_elements(self, image: Image.Image, prompt: str, ev_value: float) -> Image.Image:
        """Add environment elements based on prompt"""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Simple keyword-based environment generation
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['street', 'cobblestone', 'road']):
            # Add ground/street at bottom
            ground_height = height // 4
            ground_color = (100, 80, 60) if ev_value < 11.0 else (150, 130, 110)
            draw.rectangle([0, height - ground_height, width, height], fill=ground_color)
            
        elif any(word in prompt_lower for word in ['brick', 'wall']):
            # Add brick pattern
            self._add_brick_pattern(draw, width, height, ev_value)
            
        elif any(word in prompt_lower for word in ['wood', 'plank']):
            # Add wood grain pattern
            self._add_wood_pattern(draw, width, height, ev_value)
        
        return image
    
    def _add_brick_pattern(self, draw: ImageDraw.Draw, width: int, height: int, ev_value: float):
        """Add simple brick pattern"""
        brick_color = (120, 80, 60) if ev_value < 11.0 else (180, 140, 120)
        mortar_color = (80, 80, 80) if ev_value < 11.0 else (200, 200, 200)
        
        brick_width = 60
        brick_height = 30
        
        for y in range(0, height, brick_height):
            offset = (brick_width // 2) if (y // brick_height) % 2 else 0
            for x in range(-offset, width + brick_width, brick_width):
                # Draw brick
                draw.rectangle([x, y, x + brick_width - 2, y + brick_height - 2], 
                              fill=brick_color)
                # Draw mortar lines
                draw.rectangle([x + brick_width - 2, y, x + brick_width, y + brick_height], 
                              fill=mortar_color)
                draw.rectangle([x, y + brick_height - 2, x + brick_width, y + brick_height], 
                              fill=mortar_color)
    
    def _add_wood_pattern(self, draw: ImageDraw.Draw, width: int, height: int, ev_value: float):
        """Add simple wood grain pattern"""
        wood_color = (139, 69, 19) if ev_value < 11.0 else (205, 133, 63)
        
        plank_height = 40
        for y in range(0, height, plank_height):
            # Vary wood color slightly for each plank
            variation = random.randint(-20, 20)
            plank_color = tuple(max(0, min(255, c + variation)) for c in wood_color)
            draw.rectangle([0, y, width, y + plank_height - 2], fill=plank_color)
            
            # Add wood grain lines
            for i in range(3):
                grain_y = y + random.randint(5, plank_height - 5)
                grain_color = tuple(max(0, c - 30) for c in plank_color)
                draw.line([0, grain_y, width, grain_y], fill=grain_color, width=1)
    
    def _apply_hdr_processing(self, image: Image.Image, ev_value: float) -> Image.Image:
        """Apply HDR-like processing"""
        # Adjust brightness based on EV
        brightness_factor = self._ev_to_brightness_factor(ev_value)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness_factor)
        
        # Increase contrast for HDR look
        contrast_enhancer = ImageEnhance.Contrast(image)
        image = contrast_enhancer.enhance(1.3)
        
        # Slight saturation boost
        color_enhancer = ImageEnhance.Color(image)
        image = color_enhancer.enhance(1.2)
        
        return image
    
    def _ev_to_brightness_factor(self, ev_value: float) -> float:
        """Convert EV value to brightness factor"""
        if ev_value <= 8.0:
            return 0.5
        elif ev_value >= 15.0:
            return 2.0
        else:
            return 0.5 + (ev_value - 8.0) * (2.0 - 0.5) / (15.0 - 8.0)
    
    def _create_albedo_texture(self, size: int, prompt: str) -> Image.Image:
        """Create albedo (base color) texture"""
        prompt_lower = prompt.lower()
        
        if 'brick' in prompt_lower:
            base_color = (150, 100, 80)
        elif 'wood' in prompt_lower:
            base_color = (139, 69, 19)
        elif 'stone' in prompt_lower or 'cobblestone' in prompt_lower:
            base_color = (120, 120, 100)
        elif 'metal' in prompt_lower:
            base_color = (100, 100, 120)
        else:
            base_color = (128, 128, 128)
        
        # Create base texture with noise
        image = Image.new('RGB', (size, size), base_color)
        
        # Add noise for texture variation
        pixels = np.array(image)
        noise = np.random.randint(-30, 30, pixels.shape)
        pixels = np.clip(pixels + noise, 0, 255)
        
        return Image.fromarray(pixels.astype(np.uint8))
    
    def _create_normal_texture(self, size: int, prompt: str) -> Image.Image:
        """Create normal map texture (purple/blue tones)"""
        # Normal maps are typically purple/blue
        base_color = (128, 128, 255)  # Neutral normal
        
        image = Image.new('RGB', (size, size), base_color)
        
        # Add surface detail variation
        pixels = np.array(image)
        
        # Create height variation for normal calculation
        height_map = np.random.random((size, size)) * 50
        
        # Simple normal map generation (simplified)
        for y in range(1, size - 1):
            for x in range(1, size - 1):
                # Calculate gradients
                dx = height_map[y, x + 1] - height_map[y, x - 1]
                dy = height_map[y + 1, x] - height_map[y - 1, x]
                
                # Convert to normal map colors
                nx = int(128 + dx * 2)
                ny = int(128 + dy * 2)
                nz = 255
                
                pixels[y, x] = [np.clip(nx, 0, 255), np.clip(ny, 0, 255), nz]
        
        return Image.fromarray(pixels.astype(np.uint8))
    
    def _create_roughness_texture(self, size: int, prompt: str) -> Image.Image:
        """Create roughness map (grayscale)"""
        prompt_lower = prompt.lower()
        
        if 'smooth' in prompt_lower or 'polished' in prompt_lower:
            base_roughness = 50  # Smooth
        elif 'rough' in prompt_lower or 'weathered' in prompt_lower:
            base_roughness = 200  # Rough
        else:
            base_roughness = 128  # Medium
        
        # Create grayscale roughness map
        image = Image.new('L', (size, size), base_roughness)
        
        # Add variation
        pixels = np.array(image)
        noise = np.random.randint(-40, 40, pixels.shape)
        pixels = np.clip(pixels + noise, 0, 255)
        
        # Convert back to RGB (grayscale)
        rgb_pixels = np.stack([pixels, pixels, pixels], axis=-1)
        
        return Image.fromarray(rgb_pixels.astype(np.uint8))
    
    def _create_ao_texture(self, size: int, prompt: str) -> Image.Image:
        """Create ambient occlusion map (grayscale)"""
        # AO is typically lighter with darker areas in crevices
        base_ao = 200  # Light base
        
        image = Image.new('L', (size, size), base_ao)
        
        # Add darker areas for crevices/details
        pixels = np.array(image)
        
        # Create some darker regions
        for _ in range(size // 20):
            x = random.randint(0, size - 1)
            y = random.randint(0, size - 1)
            radius = random.randint(5, 15)
            
            for dy in range(-radius, radius):
                for dx in range(-radius, radius):
                    if 0 <= x + dx < size and 0 <= y + dy < size:
                        distance = math.sqrt(dx*dx + dy*dy)
                        if distance < radius:
                            factor = 1.0 - (distance / radius)
                            pixels[y + dy, x + dx] = max(50, 
                                int(pixels[y + dy, x + dx] * (1 - factor * 0.5)))
        
        # Convert to RGB
        rgb_pixels = np.stack([pixels, pixels, pixels], axis=-1)
        
        return Image.fromarray(rgb_pixels.astype(np.uint8))
    
    def _make_tileable(self, image: Image.Image) -> Image.Image:
        """Make texture seamlessly tileable"""
        width, height = image.size
        
        # Simple edge blending
        blend_size = min(width, height) // 8
        
        # Create a copy
        tileable = image.copy()
        pixels = np.array(tileable)
        
        # Blend horizontal edges
        for x in range(blend_size):
            alpha = x / blend_size
            for y in range(height):
                # Blend left edge with right edge
                left_pixel = pixels[y, x]
                right_pixel = pixels[y, width - blend_size + x]
                
                blended = left_pixel * (1 - alpha) + right_pixel * alpha
                pixels[y, x] = blended.astype(np.uint8)
                pixels[y, width - blend_size + x] = blended.astype(np.uint8)
        
        # Blend vertical edges
        for y in range(blend_size):
            alpha = y / blend_size
            for x in range(width):
                # Blend top edge with bottom edge
                top_pixel = pixels[y, x]
                bottom_pixel = pixels[height - blend_size + y, x]
                
                blended = top_pixel * (1 - alpha) + bottom_pixel * alpha
                pixels[y, x] = blended.astype(np.uint8)
                pixels[height - blend_size + y, x] = blended.astype(np.uint8)
        
        return Image.fromarray(pixels)