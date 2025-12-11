#!/usr/bin/env python3
"""
FIBO HDRI Studio - Demonstration Script

This script demonstrates the key features of FIBO HDRI Studio by generating
a series of assets that showcase deterministic control and professional output.
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.fibo_agent import FIBOAgent
from src.parameter_handler import ParameterHandler
from src.post_processor import PostProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FIBODemo:
    """Demonstration class for FIBO HDRI Studio"""
    
    def __init__(self):
        self.demo_dir = Path("./demo_outputs")
        self.demo_dir.mkdir(exist_ok=True)
        
        print("🎬 FIBO HDRI Studio Demonstration")
        print("=" * 50)
        
    def run_full_demo(self):
        """Run the complete demonstration"""
        try:
            # Initialize components
            print("\n📦 Initializing FIBO HDRI Studio...")
            self.fibo_agent = FIBOAgent()
            self.parameter_handler = ParameterHandler()
            self.post_processor = PostProcessor(str(self.demo_dir))
            
            # Run demonstrations
            self.demo_deterministic_control()
            self.demo_lighting_variations()
            self.demo_professional_workflow()
            
            print("\n🎉 Demonstration completed successfully!")
            print(f"📁 All outputs saved to: {self.demo_dir}")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            return False
        
        return True
    
    def demo_deterministic_control(self):
        """Demonstrate deterministic generation control"""
        print("\n🎯 Demo 1: Deterministic Control")
        print("-" * 30)
        
        base_prompt = "rough roman cobblestone street"
        
        # Generate with different EV values but same seed
        ev_values = [8.0, 12.0, 15.0]
        seed = 42
        
        for i, ev in enumerate(ev_values):
            print(f"  Generating EV {ev} variation...")
            
            config = self.parameter_handler.create_master_config(
                prompt=base_prompt,
                ev_value=ev,
                azimuth=180.0,
                seed=seed
            )
            
            # Generate HDRI only for speed
            hdri_config = self.parameter_handler.create_hdri_config(config)
            hdri_image, hdri_metadata = self.fibo_agent.generate_hdri(hdri_config)
            
            # Save with descriptive name
            filename = f"demo1_deterministic_ev{ev}_seed{seed}"
            hdri_path = self.post_processor.process_hdri(
                hdri_image, hdri_metadata, filename
            )
            
            print(f"    ✅ Saved: {Path(hdri_path).name}")
        
        print("  📊 Result: Same prompt + seed, different EV = predictable lighting variations")
    
    def demo_lighting_variations(self):
        """Demonstrate lighting direction control"""
        print("\n🌅 Demo 2: Lighting Direction Control")
        print("-" * 35)
        
        prompt = "weathered brick wall"
        
        # Test different azimuth angles
        azimuths = [0, 90, 180, 270]  # North, East, South, West
        directions = ["North", "East", "South", "West"]
        
        for azimuth, direction in zip(azimuths, directions):
            print(f"  Generating {direction} lighting ({azimuth}°)...")
            
            config = self.parameter_handler.create_master_config(
                prompt=prompt,
                ev_value=11.0,
                azimuth=float(azimuth),
                seed=1337
            )
            
            # Generate both HDRI and albedo texture
            hdri_config = self.parameter_handler.create_hdri_config(config)
            hdri_image, hdri_metadata = self.fibo_agent.generate_hdri(hdri_config)
            
            pbr_config = self.parameter_handler.create_pbr_config(config, "albedo")
            texture_image, texture_metadata = self.fibo_agent.generate_pbr_texture(
                pbr_config, "albedo"
            )
            
            # Save both
            hdri_filename = f"demo2_hdri_{direction.lower()}_lighting"
            texture_filename = f"demo2_albedo_{direction.lower()}_lighting"
            
            hdri_path = self.post_processor.process_hdri(
                hdri_image, hdri_metadata, hdri_filename
            )
            texture_path = self.post_processor.process_pbr_texture(
                texture_image, texture_metadata, texture_filename
            )
            
            print(f"    ✅ HDRI: {Path(hdri_path).name}")
            print(f"    ✅ Texture: {Path(texture_path).name}")
        
        print("  📊 Result: Consistent material with directional lighting variations")
    
    def demo_professional_workflow(self):
        """Demonstrate complete professional asset generation"""
        print("\n🏭 Demo 3: Professional Asset Package")
        print("-" * 35)
        
        prompt = "polished marble surface"
        
        print("  Generating complete PBR asset set...")
        
        config = self.parameter_handler.create_master_config(
            prompt=prompt,
            ev_value=12.5,
            azimuth=135.0,
            color_profile="ACEScg",  # Professional color space
            seed=2024
        )
        
        # Generate HDRI
        print("    🌐 Generating HDRI environment...")
        hdri_config = self.parameter_handler.create_hdri_config(config)
        hdri_image, hdri_metadata = self.fibo_agent.generate_hdri(hdri_config)
        
        hdri_path = self.post_processor.process_hdri(
            hdri_image, hdri_metadata, "demo3_marble_hdri", "exr"
        )
        
        # Generate complete PBR set
        texture_types = ["albedo", "normal", "roughness"]
        texture_paths = {}
        
        for tex_type in texture_types:
            print(f"    🎨 Generating {tex_type} map...")
            pbr_config = self.parameter_handler.create_pbr_config(config, tex_type)
            texture_image, texture_metadata = self.fibo_agent.generate_pbr_texture(
                pbr_config, tex_type
            )
            
            texture_path = self.post_processor.process_pbr_texture(
                texture_image, texture_metadata, f"demo3_marble_{tex_type}", "tiff"
            )
            texture_paths[tex_type] = texture_path
        
        # Create professional asset package
        print("    📦 Creating asset package...")
        package_path = self.post_processor.create_asset_package(
            hdri_path,
            texture_paths,
            config,
            "demo3_marble_professional_package"
        )
        
        print(f"    ✅ Complete package: {Path(package_path).name}")
        print("  📊 Result: Production-ready HDRI + PBR asset package")
    
    def generate_demo_video_script(self):
        """Generate a script for creating the demonstration video"""
        script_path = self.demo_dir / "video_script.md"
        
        script_content = """
# FIBO HDRI Studio - Video Demonstration Script

## Intro (30 seconds)
- Show problem: Inconsistent HDRI and texture generation
- Introduce FIBO HDRI Studio as solution
- Highlight key benefits: Deterministic, Professional, Consistent

## Controllability Demo (1 minute)
1. Open web interface
2. Enter prompt: "rough roman cobblestone street"
3. Show EV slider at 8.0 - generate (dark, moody result)
4. Change EV to 14.0 - generate (bright, sunny result)
5. Highlight: Same prompt, different EV = predictable control

## Professional Workflow Demo (1.5 minutes)
1. Generate complete asset set for "polished marble"
2. Show HDRI generation (EXR format)
3. Show PBR texture generation (Albedo, Normal, Roughness)
4. Open Blender/Unity
5. Import HDRI - show environment lighting
6. Apply PBR textures to 3D object
7. Show realistic material rendering
8. Highlight: Professional formats, seamless integration

## Conclusion (30 seconds)
- Recap key features
- Show output directory with organized assets
- Mention JSON repeatability
- Call to action

## Technical Notes
- Use screen recording software (OBS Studio)
- Record at 1080p 60fps
- Use clear, professional narration
- Show mouse movements clearly
- Include smooth transitions between sections
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        print(f"📝 Video script saved to: {script_path}")

def main():
    """Main demonstration function"""
    demo = FIBODemo()
    
    print("Choose demonstration mode:")
    print("1. Full Demo (generates all examples)")
    print("2. Quick Demo (HDRI only)")
    print("3. Generate Video Script")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting full demonstration...")
        success = demo.run_full_demo()
        if success:
            demo.generate_demo_video_script()
    elif choice == "2":
        print("\n⚡ Starting quick demonstration...")
        demo.demo_deterministic_control()
    elif choice == "3":
        demo.generate_demo_video_script()
    elif choice == "4":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()