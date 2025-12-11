"""
Post Processor - Handles output formatting, HDR conversion, and file saving
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple
import logging
import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)

# Try to import OpenEXR for HDR support
try:
    import OpenEXR
    import Imath
    HAS_OPENEXR = True
except ImportError:
    logger.warning("OpenEXR not available. HDR output will be limited to 16-bit TIFF.")
    HAS_OPENEXR = False

class PostProcessor:
    """Handles post-processing and output formatting for generated assets"""
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Supported formats
        self.hdri_formats = ["exr", "hdr", "tiff"] if HAS_OPENEXR else ["tiff"]
        self.texture_formats = ["png", "tiff", "jpg"]
    
    def process_hdri(self, 
                     image: Image.Image, 
                     metadata: Dict[str, Any], 
                     filename: str,
                     format: str = "exr") -> str:
        """
        Process and save HDRI image in professional format
        
        Args:
            image: Generated PIL Image
            metadata: Generation metadata
            filename: Output filename (without extension)
            format: Output format (exr, hdr, tiff)
            
        Returns:
            Path to saved file
        """
        if format not in self.hdri_formats:
            logger.warning(f"Format {format} not supported. Using TIFF instead.")
            format = "tiff"
        
        # Convert to HDR format
        hdr_image = self._convert_to_hdr(image)
        
        # Generate output path
        output_path = self.output_dir / f"{filename}.{format}"
        
        if format == "exr" and HAS_OPENEXR:
            self._save_exr(hdr_image, output_path, metadata)
        elif format == "hdr":
            self._save_hdr(hdr_image, output_path)
        else:  # TIFF fallback
            self._save_16bit_tiff(hdr_image, output_path)
        
        # Save metadata
        self._save_metadata(metadata, output_path.with_suffix('.json'))
        
        logger.info(f"HDRI saved to {output_path}")
        return str(output_path)
    
    def process_pbr_texture(self, 
                           image: Image.Image, 
                           metadata: Dict[str, Any], 
                           filename: str,
                           format: str = "png") -> str:
        """
        Process and save PBR texture in professional format
        
        Args:
            image: Generated PIL Image
            metadata: Generation metadata
            filename: Output filename (without extension)
            format: Output format (png, tiff, jpg)
            
        Returns:
            Path to saved file
        """
        if format not in self.texture_formats:
            logger.warning(f"Format {format} not supported. Using PNG instead.")
            format = "png"
        
        # Ensure tileable if specified
        if metadata.get("tileable", False):
            image = self._make_tileable(image)
        
        # Convert to 16-bit if supported by format
        if format in ["png", "tiff"]:
            processed_image = self._convert_to_16bit(image)
        else:
            processed_image = image
        
        # Generate output path
        output_path = self.output_dir / f"{filename}.{format}"
        
        # Save with appropriate settings
        if format == "png":
            processed_image.save(output_path, "PNG", optimize=False, compress_level=0)
        elif format == "tiff":
            processed_image.save(output_path, "TIFF", compression=None)
        else:  # JPG
            processed_image.save(output_path, "JPEG", quality=95)
        
        # Save metadata
        self._save_metadata(metadata, output_path.with_suffix('.json'))
        
        logger.info(f"PBR texture saved to {output_path}")
        return str(output_path)
    
    def create_asset_package(self, 
                           hdri_path: str, 
                           texture_paths: Dict[str, str], 
                           master_config: Dict[str, Any],
                           package_name: str) -> str:
        """
        Create a complete asset package with HDRI and PBR textures
        
        Args:
            hdri_path: Path to HDRI file
            texture_paths: Dictionary of texture type -> file path
            master_config: Master configuration used for generation
            package_name: Name for the asset package
            
        Returns:
            Path to package directory
        """
        package_dir = self.output_dir / package_name
        package_dir.mkdir(exist_ok=True)
        
        # Create package structure
        (package_dir / "hdri").mkdir(exist_ok=True)
        (package_dir / "textures").mkdir(exist_ok=True)
        (package_dir / "configs").mkdir(exist_ok=True)
        
        # Copy HDRI
        if hdri_path:
            hdri_dest = package_dir / "hdri" / Path(hdri_path).name
            self._copy_file(hdri_path, hdri_dest)
        
        # Copy textures
        for tex_type, tex_path in texture_paths.items():
            if tex_path:
                tex_dest = package_dir / "textures" / f"{tex_type}_{Path(tex_path).name}"
                self._copy_file(tex_path, tex_dest)
        
        # Save master configuration
        master_config_path = package_dir / "configs" / "master_config.json"
        with open(master_config_path, 'w') as f:
            json.dump(master_config, f, indent=2)
        
        # Create package info
        package_info = {
            "name": package_name,
            "version": "1.0",
            "generator": "FIBO-HDRI-Studio",
            "contents": {
                "hdri": Path(hdri_path).name if hdri_path else None,
                "textures": {k: f"{k}_{Path(v).name}" for k, v in texture_paths.items() if v}
            },
            "config": "master_config.json"
        }
        
        package_info_path = package_dir / "package.json"
        with open(package_info_path, 'w') as f:
            json.dump(package_info, f, indent=2)
        
        logger.info(f"Asset package created at {package_dir}")
        return str(package_dir)
    
    def _convert_to_hdr(self, image: Image.Image) -> np.ndarray:
        """Convert PIL Image to HDR numpy array"""
        # Convert to numpy array
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # Apply gamma correction for HDR
        gamma = 2.2
        img_array = np.power(img_array, gamma)
        
        # Expand dynamic range
        img_array = img_array * 2.0  # Simple HDR expansion
        
        return img_array
    
    def _convert_to_16bit(self, image: Image.Image) -> Image.Image:
        """Convert PIL Image to 16-bit"""
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to 16-bit
        img_array = np.array(image, dtype=np.uint16)
        img_array = (img_array * 257).astype(np.uint16)  # Scale 8-bit to 16-bit
        
        # Create 16-bit PIL image
        img_16bit = Image.fromarray(img_array, mode='RGB')
        
        return img_16bit
    
    def _make_tileable(self, image: Image.Image) -> Image.Image:
        """Make image seamlessly tileable using edge blending"""
        img_array = np.array(image)
        h, w = img_array.shape[:2]
        
        # Create blend masks
        blend_size = min(h, w) // 8  # 12.5% blend zone
        
        # Horizontal tiling
        left_edge = img_array[:, :blend_size]
        right_edge = img_array[:, -blend_size:]
        
        # Create horizontal blend
        for i in range(blend_size):
            alpha = i / blend_size
            img_array[:, i] = (1 - alpha) * right_edge[:, -(blend_size-i)] + alpha * left_edge[:, i]
            img_array[:, -(i+1)] = (1 - alpha) * left_edge[:, i] + alpha * right_edge[:, -(i+1)]
        
        # Vertical tiling
        top_edge = img_array[:blend_size, :]
        bottom_edge = img_array[-blend_size:, :]
        
        # Create vertical blend
        for i in range(blend_size):
            alpha = i / blend_size
            img_array[i, :] = (1 - alpha) * bottom_edge[-(blend_size-i), :] + alpha * top_edge[i, :]
            img_array[-(i+1), :] = (1 - alpha) * top_edge[i, :] + alpha * bottom_edge[-(i+1), :]
        
        return Image.fromarray(img_array.astype(np.uint8))
    
    def _save_exr(self, hdr_image: np.ndarray, output_path: Path, metadata: Dict[str, Any]):
        """Save HDR image as OpenEXR"""
        if not HAS_OPENEXR:
            raise RuntimeError("OpenEXR not available")
        
        h, w, c = hdr_image.shape
        
        # Convert to OpenEXR format
        header = OpenEXR.Header(w, h)
        header['channels'] = {
            'R': Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT)),
            'G': Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT)),
            'B': Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT))
        }
        
        # Add metadata to header
        if metadata:
            header['generator'] = metadata.get('generator', 'FIBO-HDRI-Studio')
        
        # Create EXR file
        exr_file = OpenEXR.OutputFile(str(output_path), header)
        
        # Write channels
        r_channel = hdr_image[:, :, 0].astype(np.float32).tobytes()
        g_channel = hdr_image[:, :, 1].astype(np.float32).tobytes()
        b_channel = hdr_image[:, :, 2].astype(np.float32).tobytes()
        
        exr_file.writePixels({
            'R': r_channel,
            'G': g_channel,
            'B': b_channel
        })
        
        exr_file.close()
    
    def _save_hdr(self, hdr_image: np.ndarray, output_path: Path):
        """Save HDR image as Radiance HDR"""
        # Convert to OpenCV format and save
        hdr_bgr = cv2.cvtColor(hdr_image.astype(np.float32), cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output_path), hdr_bgr)
    
    def _save_16bit_tiff(self, hdr_image: np.ndarray, output_path: Path):
        """Save as 16-bit TIFF (fallback for HDR)"""
        # Tone map HDR to 16-bit range
        tone_mapped = np.clip(hdr_image * 32767, 0, 65535).astype(np.uint16)
        
        # Save as TIFF
        img_pil = Image.fromarray(tone_mapped, mode='RGB')
        img_pil.save(output_path, "TIFF", compression=None)
    
    def _save_metadata(self, metadata: Dict[str, Any], output_path: Path):
        """Save metadata as JSON"""
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _copy_file(self, src: str, dest: Path):
        """Copy file from source to destination"""
        import shutil
        shutil.copy2(src, dest)