# FIBO HDRI Studio - Usage Guide

## Overview

FIBO HDRI Studio generates professional-quality HDRI environments and PBR texture sets from text descriptions. The tool ensures lighting consistency between HDRI and textures, making it ideal for VFX and 3D workflows.

## Key Concepts

### Deterministic Generation
- Same prompt + parameters = identical results
- Controlled via EV values and lighting parameters
- JSON configurations ensure repeatability

### Professional Formats
- **HDRI**: 16-bit EXR format for maximum dynamic range
- **Textures**: 16-bit PNG/TIFF for professional workflows
- **Metadata**: Complete generation parameters saved with each asset

### Lighting Consistency
- HDRI and PBR maps share lighting characteristics
- EV values control overall exposure and mood
- Azimuth controls directional lighting

## Web Interface Usage

### 1. Basic Generation

1. **Enter Scene Description**
   ```
   Example: "rough roman cobblestone street"
   ```

2. **Adjust Lighting Parameters**
   - **EV Value (8.0-15.0)**: Controls brightness and mood
     - 8.0-10.0: Dark, moody lighting
     - 10.0-13.0: Balanced, natural lighting  
     - 13.0-15.0: Bright, high-key lighting
   
   - **Azimuth (0°-360°)**: Controls light direction
     - 0°: North (front lighting)
     - 90°: East (side lighting)
     - 180°: South (back lighting)
     - 270°: West (side lighting)

3. **Select Generation Options**
   - ✅ 360° HDRI Environment
   - ✅ PBR Texture Maps
     - Albedo (Base Color)
     - Normal Map
     - Roughness Map
     - Ambient Occlusion

4. **Click Generate Assets**

### 2. Using Presets

Quick presets for common lighting scenarios:

- **☀️ Sunny Day**: EV 14.0, Azimuth 135°
- **🌅 Golden Hour**: EV 11.0, Azimuth 270°
- **☁️ Overcast**: EV 10.0, Azimuth 180°
- **🎭 Dramatic**: EV 8.5, Azimuth 225°

### 3. Downloading Results

- **Individual Files**: Download HDRI or specific texture maps
- **Complete Package**: ZIP file with all assets and configurations

## CLI Usage

### Basic Generation
```bash
python generate.py \
  --prompt "weathered brick wall" \
  --ev-value 12.0 \
  --azimuth 180 \
  --color-profile sRGB
```

### Advanced Options
```bash
python generate.py \
  --prompt "wooden planks" \
  --ev-value 10.5 \
  --azimuth 225 \
  --color-profile ACEScg \
  --texture-types albedo normal roughness ao \
  --format-hdri exr \
  --format-texture tiff \
  --output-dir ./my_assets \
  --seed 42 \
  --verbose
```

### Regenerate from Configuration
```bash
python generate.py regenerate --config config_12345.json
```

## Parameter Guide

### EV Value Effects

| EV Range | Lighting Character | Use Cases |
|----------|-------------------|-----------|
| 8.0-9.0  | Very dark, dramatic | Night scenes, horror, dramatic portraits |
| 9.0-10.0 | Dark, moody | Sunset, indoor scenes, film noir |
| 10.0-11.0 | Balanced, natural | Overcast day, soft lighting |
| 11.0-12.0 | Bright, clear | Daylight, outdoor scenes |
| 12.0-13.0 | Very bright | Sunny day, high-key lighting |
| 13.0-15.0 | Extremely bright | Desert, snow, studio lighting |

### Azimuth Direction Guide

```
        0° (North)
           |
270° ------+------ 90°
  (West)   |    (East)
           |
       180° (South)
```

### Color Profile Selection

- **sRGB**: Standard web/gaming (most common)
- **ACEScg**: VFX and film production
- **Rec.2020**: HDR displays and broadcasting
- **DCI-P3**: Digital cinema projection

## Workflow Examples

### 1. Game Asset Creation

**Objective**: Create tileable stone texture for game environment

```bash
python generate.py \
  --prompt "medieval stone blocks" \
  --ev-value 12.0 \
  --azimuth 135 \
  --texture-types albedo normal roughness \
  --format-texture png \
  --no-hdri
```

**Result**: Seamlessly tileable PBR texture set ready for game engines

### 2. VFX Environment Setup

**Objective**: Create HDRI for 3D scene lighting

```bash
python generate.py \
  --prompt "industrial warehouse interior" \
  --ev-value 10.0 \
  --azimuth 180 \
  --color-profile ACEScg \
  --format-hdri exr \
  --no-textures
```

**Result**: Professional HDRI for realistic scene lighting

### 3. Complete Asset Package

**Objective**: Generate matched HDRI and textures for architectural visualization

```bash
python generate.py \
  --prompt "modern concrete surface" \
  --ev-value 11.5 \
  --azimuth 225 \
  --texture-types albedo normal roughness ao \
  --package
```

**Result**: Complete asset package with HDRI and PBR textures

## Integration with 3D Software

### Blender Integration

1. **Import HDRI**:
   - World Properties → Surface → Environment Texture
   - Load generated EXR file
   - Set Color Space to "Linear"

2. **Apply PBR Textures**:
   - Create Principled BSDF material
   - Connect Albedo → Base Color
   - Connect Normal → Normal (via Normal Map node)
   - Connect Roughness → Roughness

### Unity Integration

1. **HDRI Setup**:
   - Window → Rendering → Lighting
   - Environment → Skybox Material
   - Create new Skybox/Panoramic material
   - Assign generated HDRI

2. **Material Setup**:
   - Create new Material
   - Set Rendering Mode to "Standard"
   - Assign texture maps to appropriate slots

### Unreal Engine Integration

1. **HDRI Import**:
   - Import EXR as Texture Cube
   - Create Sky Light actor
   - Set Source Type to "SLS Specified Cubemap"

2. **Material Creation**:
   - Create new Material
   - Connect texture maps to Material inputs
   - Set Material Domain to "Surface"

## Best Practices

### Prompt Writing

**Good Prompts**:
- "weathered red brick wall"
- "polished marble surface"
- "rusty metal panels"
- "wooden oak planks"

**Avoid**:
- Overly complex descriptions
- Multiple materials in one prompt
- Lighting descriptions (use EV/azimuth instead)

### Parameter Selection

1. **Start with presets** for common scenarios
2. **Adjust EV first** to set overall mood
3. **Fine-tune azimuth** for directional lighting
4. **Use consistent seeds** for variations

### File Management

1. **Use descriptive names** for output directories
2. **Save configurations** for important assets
3. **Organize by project** or material type
4. **Keep metadata files** for repeatability

## Troubleshooting

### Common Issues

**Textures not tileable**:
- Ensure "tileable" option is enabled
- Check edge blending in post-processor
- Verify seamless generation parameters

**HDRI too dark/bright**:
- Adjust EV value
- Check color profile settings
- Verify HDR display capabilities

**Inconsistent lighting**:
- Use same seed for HDRI and textures
- Verify azimuth settings
- Check color profile consistency

### Performance Optimization

**Slow generation**:
- Use GPU acceleration
- Reduce image resolution for testing
- Enable memory optimization flags

**Memory issues**:
- Enable attention slicing
- Use sequential CPU offload
- Reduce batch size

## Advanced Features

### Custom Model Integration

Replace the default FIBO model:

```python
# In src/fibo_agent.py
agent = FIBOAgent(model_path="path/to/custom/model")
```

### Batch Processing

Generate multiple variations:

```bash
for seed in {1..10}; do
  python generate.py \
    --prompt "stone texture" \
    --seed $seed \
    --output-dir "./batch_$seed"
done
```

### API Integration

Use the web API programmatically:

```python
import requests

response = requests.post('http://localhost:5000/api/generate', json={
    'prompt': 'brick wall',
    'ev_value': 12.0,
    'azimuth': 180.0
})

result = response.json()
```