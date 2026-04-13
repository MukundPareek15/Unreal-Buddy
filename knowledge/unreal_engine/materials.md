# Unreal Engine 5 — Materials

## Material Editor Layout

Double-click any .uasset material to open it. Main areas:

- **Graph canvas**: Connect nodes to the Material Result Node (large node on the right).
- **Details panel** (left): Properties of the selected node, or the material itself when nothing is selected.
- **Palette**: Searchable list of all nodes. Drag onto canvas or right-click canvas to search.
- **Preview viewport** (top-left): Live preview of the material. Right-click to change the preview shape.

## Material Result Node Inputs

The most important inputs on the main result node:

| Input | Description |
|-------|-------------|
| Base Color | Diffuse color (RGB). No lighting information. |
| Metallic | 0 = dielectric, 1 = metal. Usually binary (0 or 1), not in-between. |
| Roughness | 0 = mirror, 1 = fully rough. Most surfaces are 0.3–0.8. |
| Normal | Tangent-space normal map. Plug in a normal texture → Tangent Space Normal node. |
| Emissive Color | Makes the surface glow. Multiply by a scalar to control intensity. |
| Opacity | Requires Blend Mode = Translucent or Masked. |
| Opacity Mask | For Masked blend mode. 0 = fully clipped. Threshold set by Opacity Mask Clip Value. |
| World Position Offset | Moves vertices in world space. Used for wind, cloth, foliage sway. |
| Ambient Occlusion | Pre-baked AO texture to darken crevices. |

## Blend Modes

Set in the Details panel with nothing selected (material properties):

- **Opaque**: Default. No transparency. Cheapest.
- **Masked**: Binary transparency via Opacity Mask. Good for foliage, fences.
- **Translucent**: Full transparency. Expensive. Doesn't receive shadow by default.
- **Additive**: Adds color to whatever is behind. Good for particles, fire, electricity.

## Shading Models

Set in material properties:

- **Default Lit**: Standard PBR. Affected by all lights.
- **Unlit**: Ignores lighting entirely. Just shows Emissive Color. Good for UI, VFX.
- **Subsurface**: For skin, wax — light scatters through the surface.
- **Two Sided Foliage**: Two-sided with subsurface scattering. For leaves.

## Texture Nodes

- **Texture Sample**: Samples a texture at UV coordinates. Outputs RGBA channels.
- **TextureCoordinate (TexCoord)**: Provides UV channel. Set U/V Tiling to repeat.
- **Panner**: Scrolls UVs over time. Plug into Texture Sample's UV input for animated textures.
- **Rotator**: Rotates UVs. Also animated.

## Common Math Nodes

| Node | Use |
|------|-----|
| Multiply | Scale a value or tint a color |
| Add | Offset a value |
| Lerp (LinearInterpolate) | Blend between A and B by alpha |
| Clamp | Keep value within Min/Max |
| Power | Sharpen/soften gradients (roughness curves) |
| Fresnel | Edge glow based on view angle |
| Dot Product | Angle between two vectors |
| Append | Combine R+G into RG, etc |
| Component Mask | Extract R, G, B, or A from a vector |

## Material Parameters

To make values tweakable in Material Instances, use parameter nodes instead of constant nodes:

- **Scalar Parameter**: Single float. Right-click a Constant node > Convert to Parameter.
- **Vector Parameter**: RGBA color.
- **Texture Parameter**: Swappable texture slot.
- **Static Switch Parameter**: Compile-time branch (zero cost at runtime).

Give each parameter a descriptive **Parameter Name** and a **Group** to organize them in the instance editor.

## Material Instances

Material Instances are children of a parent material. They let you override exposed parameters without recompiling the shader. Much cheaper than separate materials.

Right-click a material in Content Browser > Create Material Instance. Open the instance — check the checkbox next to a parameter to override it.

**Material Instance Dynamic (MID)**: Created at runtime in Blueprint. Lets you change parameter values on a live material (e.g., changing a character's color during gameplay). Use `Create Dynamic Material Instance` node, then `Set Scalar Parameter Value` / `Set Vector Parameter Value`.

## Material Functions

Reusable node subgraphs. Create via Content Browser > Material > Material Function. Inside, use **Function Input** and **Function Output** nodes. Call them in any material with a **MaterialFunctionCall** node.

Good for: triplanar projection, detail normal blending, wetness effects.

## Nanite and Materials

Materials used on Nanite meshes cannot use:
- World Position Offset (WPO) — disabled by default on Nanite; enable per-material with `Nanite > Enable WPO`
- Vertex interpolators
- Tessellation (deprecated in UE5)

Masked materials on Nanite meshes have a performance cost — prefer opaque where possible.

## Lumen and Emissive

Lumen picks up emissive materials as area lights. Multiply your emissive color by a high scalar (50–500) to get visible global illumination contribution. Too low and Lumen ignores it.

## Documentation

Official UE5 materials documentation — cite these when relevant:

- Material overview: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-materials
- Material editor reference: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-material-editor-user-guide
- PBR physically based rendering: https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine
- Material instances: https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-materials-in-unreal-engine
- Material functions: https://dev.epicgames.com/documentation/en-us/unreal-engine/material-functions-in-unreal-engine
- Material expressions reference: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-material-expressions-reference
- Nanite materials: https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine
- Lumen with emissive: https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine
