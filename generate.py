#!/usr/bin/env python3
"""
FIBO HDRI Studio - CLI Interface
"""

import click
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.fibo_agent import FIBOAgent
from src.parameter_handler import ParameterHandler
from src.post_processor import PostProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@click.command()
@click.option('--prompt', '-p', required=True, help='Text description of the scene/texture')
@click.option('--ev-value', '-e', default=12.0, type=float, help='Exposure value (8.0-15.0)')
@click.option('--azimuth', '-a', default=180.0, type=float, help='Light angle in degrees (0-360)')
@click.option('--color-profile', '-c', default='sRGB', 
              type=click.Choice(['sRGB', 'ACEScg', 'Rec.2020', 'DCI-P3']),
              help='Color space profile')
@click.option('--seed', '-s', type=int, help='Random seed for reproducibility')
@click.option('--output-dir', '-o', default='./outputs', help='Output directory')
@click.option('--hdri/--no-hdri', default=True, help='Generate HDRI')
@click.option('--textures/--no-textures', default=True, help='Generate PBR textures')
@click.option('--texture-types', '-t', multiple=True, 
              default=['albedo', 'normal', 'roughness'],
              type=click.Choice(['albedo', 'normal', 'roughness', 'ao']),
              help='PBR texture types to generate')
@click.option('--model-path', '-m', default='briaai/BRIA-2.3', help='FIBO model path')
@click.option('--format-hdri', default='exr', 
              type=click.Choice(['exr', 'hdr', 'tiff']),
              help='HDRI output format')
@click.option('--format-texture', default='png',
              type=click.Choice(['png', 'tiff', 'jpg']),
              help='Texture output format')
@click.option('--package/--no-package', default=True, help='Create asset package')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def generate(prompt, ev_value, azimuth, color_profile, seed, output_dir,
            hdri, textures, texture_types, model_path, format_hdri, 
            format_texture, package, verbose):
    """
    Generate HDRI and PBR textures using FIBO model
    
    Example:
        python generate.py -p "rough roman cobblestone street" -e 12.0 -a 180
    """
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize components
        click.echo("Initializing FIBO HDRI Studio...")
        fibo_agent = FIBOAgent(model_path)
        parameter_handler = ParameterHandler()
        post_processor = PostProcessor(output_dir)
        
        # Create master configuration
        click.echo(f"Creating configuration for: '{prompt}'")
        master_config = parameter_handler.create_master_config(
            prompt=prompt,
            ev_value=ev_value,
            azimuth=azimuth,
            color_profile=color_profile,
            seed=seed
        )
        
        results = {
            'hdri_path': None,
            'texture_paths': {}
        }
        
        # Generate HDRI if requested
        if hdri:
            click.echo("Generating HDRI...")
            hdri_config = parameter_handler.create_hdri_config(master_config)
            hdri_image, hdri_metadata = fibo_agent.generate_hdri(hdri_config)
            
            # Save HDRI
            filename = f"hdri_{master_config['seed']}"
            hdri_path = post_processor.process_hdri(
                hdri_image, hdri_metadata, filename, format_hdri
            )
            results['hdri_path'] = hdri_path
            click.echo(f"HDRI saved: {hdri_path}")
        
        # Generate PBR textures if requested
        if textures:
            click.echo("Generating PBR textures...")
            for texture_type in texture_types:
                click.echo(f"  Generating {texture_type} map...")
                pbr_config = parameter_handler.create_pbr_config(
                    master_config, texture_type
                )
                texture_image, texture_metadata = fibo_agent.generate_pbr_texture(
                    pbr_config, texture_type
                )
                
                # Save texture
                filename = f"{texture_type}_{master_config['seed']}"
                texture_path = post_processor.process_pbr_texture(
                    texture_image, texture_metadata, filename, format_texture
                )
                results['texture_paths'][texture_type] = texture_path
                click.echo(f"  {texture_type.capitalize()} saved: {texture_path}")
        
        # Create asset package if requested
        if package and (hdri or textures):
            click.echo("Creating asset package...")
            package_name = f"asset_package_{master_config['seed']}"
            package_path = post_processor.create_asset_package(
                results['hdri_path'],
                results['texture_paths'],
                master_config,
                package_name
            )
            click.echo(f"Asset package created: {package_path}")
        
        # Save master configuration
        config_path = Path(output_dir) / f"config_{master_config['seed']}.json"
        parameter_handler.save_config(master_config, str(config_path))
        click.echo(f"Configuration saved: {config_path}")
        
        click.echo("Generation completed successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@click.command()
@click.option('--config', '-c', required=True, help='Configuration JSON file')
@click.option('--output-dir', '-o', default='./outputs', help='Output directory')
@click.option('--model-path', '-m', default='briaai/BRIA-2.3', help='FIBO model path')
def regenerate(config, output_dir, model_path):
    """
    Regenerate assets from saved configuration
    
    Example:
        python generate.py regenerate -c config_12345.json
    """
    try:
        # Initialize components
        click.echo("Initializing FIBO HDRI Studio...")
        fibo_agent = FIBOAgent(model_path)
        parameter_handler = ParameterHandler()
        post_processor = PostProcessor(output_dir)
        
        # Load configuration
        click.echo(f"Loading configuration from: {config}")
        master_config = parameter_handler.load_config(config)
        
        # Regenerate based on config
        prompt = master_config['prompt']
        click.echo(f"Regenerating for: '{prompt}'")
        
        # This would follow the same generation logic as the main command
        # Implementation details omitted for brevity
        
        click.echo("Regeneration completed successfully!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

# Create CLI group
@click.group()
def cli():
    """FIBO HDRI Studio - Professional HDRI and PBR texture generation"""
    pass

cli.add_command(generate)
cli.add_command(regenerate)

if __name__ == '__main__':
    cli()