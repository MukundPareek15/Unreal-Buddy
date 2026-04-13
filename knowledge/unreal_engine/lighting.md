# Unreal Engine 5 — Lighting

## Light Types

| Light Type | Description |
|------------|-------------|
| **Directional Light** | Simulates the sun. Infinite distance, parallel rays. One per scene typically. |
| **Point Light** | Omnidirectional. Like a light bulb. Has attenuation radius. |
| **Spot Light** | Cone-shaped. Has inner/outer cone angles and attenuation radius. |
| **Rect Light** | Rectangular area light. Good for TVs, windows, monitors. |
| **Sky Light** | Captures the sky and applies it as ambient lighting. Essential for outdoor scenes. |

All lights have: **Intensity** (lux for directional, candelas for others), **Light Color**, **Temperature** (Kelvin, when Use Temperature is enabled), **Cast Shadows** toggle.

## Lumen (Dynamic Global Illumination)

Lumen is UE5's default real-time GI system. Enabled via Project Settings > Rendering > Dynamic Global Illumination Method = Lumen.

- Handles indirect lighting, reflections, and sky lighting automatically.
- Works best with **Movable** lights. Static/Stationary lights can still contribute.
- **Lumen Scene**: Lumen builds a simplified scene representation (Lumen Scene) — visible via `r.Lumen.Visualize.Scene 1` in console.
- **Hardware Ray Tracing**: Enable in Project Settings for higher quality Lumen. Requires DX12 and RTX GPU.
- **Lumen Reflection Quality**: Adjust via Post Process Volume > Lumen Reflections > Quality.

## Sky Atmosphere and Sky Light

For outdoor scenes, use this combination:

1. **SkyAtmosphere** actor: Physically-based sky color, atmosphere scattering.
2. **Directional Light** with **Atmosphere Sun Light** enabled: Drives sky color based on light angle.
3. **Sky Light** with **Real Time Capture** enabled: Captures the atmosphere and uses it for ambient/reflection.
4. **Exponential Height Fog**: Adds ground fog and aerial perspective.
5. **Volumetric Clouds** (optional): Adds 3D cloud layer.

For these to work together, the Directional Light must have **Atmosphere Sun Light** checked in its Details.

## Post Process Volume

Controls final image appearance. Place one in the level and check **Infinite Extent** to apply globally, or leave it bounded for zone-based effects.

Key settings:

- **Exposure**: Min/Max EV100 to control auto-exposure range. Set Min = Max to lock exposure.
- **Bloom**: Intensity and threshold for light bleed on bright areas.
- **Depth of Field**: Camera lens blur. Cinematic Camera actor sets this automatically.
- **Color Grading**: Shadows/Midtones/Highlights color wheels. Saturation, Contrast, Gamma.
- **Film**: Toe, Slope, Shoulder — filmic tone mapping curve controls.
- **Ambient Occlusion**: Screen-space AO (SSAO). Intensity and radius.
- **Motion Blur**: Amount and max distortion. Set to 0 for game-feel clarity.
- **Lumen GI / Reflections**: Per-volume overrides for Lumen quality.

## Baked Lighting (Lightmass)

For Static and Stationary lights, build lighting to bake to lightmaps: **Build > Build Lighting Only**.

- Actors must have **Cast Shadow** enabled.
- Static meshes need a **Lightmap UV** (channel 1). Most imported meshes have this auto-generated.
- Lightmap Resolution: Set per mesh in the Static Mesh Editor, or override per-actor in Details > Lighting > Overridden Light Map Res.
- **World Settings > Lightmass**: Controls bounce count, quality (Preview/Medium/High/Production).

## Shadow Types

| Shadow Type | When Used |
|-------------|-----------|
| Static shadows | Baked into lightmaps. Zero runtime cost. Static lights only. |
| Stationary shadows | Baked for static objects, dynamic for movable objects. |
| Dynamic shadows | Fully real-time. Most expensive. Movable lights. |
| Distance Field Shadows | Efficient dynamic soft shadows. Enable in Project Settings. |
| Ray Traced Shadows | Highest quality, expensive. Requires hardware ray tracing. |

## Common Lighting Issues

**Dark seams on meshes**: Missing or overlapping lightmap UVs. Fix in Static Mesh Editor > Build Settings > Generate Lightmap UVs.

**Light bleeding through walls**: Increase mesh lightmap resolution or make geometry thicker.

**Lumen indirect light looks noisy**: Increase `r.Lumen.ScreenProbeGather.DownsampleFactor` or add more Lumen Scene Detail in Project Settings.

**Scene too dark/bright indoors**: Add a Post Process Volume, set Exposure Min = Max to override auto-exposure.

**Shadows not casting**: Check: light has Cast Shadows enabled, mesh has Cast Shadow enabled in Details, and mesh mobility allows it.

## Performance Tips

- Keep Directional Light as **Stationary** and bake lighting for static geometry — dramatic performance gain.
- Use **Distance Field Ambient Occlusion** instead of SSAO for better performance at high resolutions.
- Limit number of shadow-casting lights in view — each adds draw call cost.
- Use **Light Channels** to control which lights affect which actors (Details > Lighting > Light Channels).
- **IES profiles**: Import real-world light distribution profiles (.ies files) into UE and assign to Point/Spot lights for physically accurate falloff shapes.

## Documentation

Official UE5 lighting documentation — cite these when relevant:

- Lighting overview: https://dev.epicgames.com/documentation/en-us/unreal-engine/lighting-the-environment-in-unreal-engine
- Lumen GI and reflections: https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine
- Lumen technical details: https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine
- Sky Atmosphere: https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine
- Post Process effects: https://dev.epicgames.com/documentation/en-us/unreal-engine/post-process-effects-in-unreal-engine
- Lightmass baked lighting: https://dev.epicgames.com/documentation/en-us/unreal-engine/global-illumination-in-unreal-engine
- Shadows: https://dev.epicgames.com/documentation/en-us/unreal-engine/shadowing-in-unreal-engine
- Light types reference: https://dev.epicgames.com/documentation/en-us/unreal-engine/light-types-and-their-mobility-in-unreal-engine
