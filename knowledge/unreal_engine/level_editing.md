# Unreal Engine 5 — Level Editing

## Placing Actors

Three ways to add actors to a level:

1. **Drag from Content Browser**: Drag any asset (mesh, Blueprint, sound) directly into the viewport.
2. **Place Actors Panel**: Window > Place Actors (or Shift+1). Browse by category — Basic shapes, Lights, Volumes, etc. Drag into viewport.
3. **Right-click in viewport**: Place Actor menu for common types.

## Selecting and Transforming

- **Click**: Select. **Ctrl+click**: Add to selection.
- **W / E / R**: Switch between Translate / Rotate / Scale gizmos.
- **X axis = red, Y = green, Z = blue** everywhere in Unreal.
- Hold **Shift** while dragging a gizmo axis to move the camera with the object.
- **Alt + drag**: Duplicate and move simultaneously.
- **End key**: Snap the selected actor to the floor (traces downward).
- **Snap settings**: Bottom of the viewport — grid snap, rotation snap, scale snap increments.

## Actor Details Panel

When an actor is selected, the Details panel shows:

- **Transform**: Location, Rotation, Scale. Click the lock icon to lock proportional scale.
- **Components**: Expand to see all components. Click a component to see its properties.
- **Tags**: Add gameplay tags for quick Blueprint identification.
- **Actor Hidden In Game**: Hides at runtime, visible in editor.
- **Mobility**: Static / Stationary / Movable. Affects lighting and performance significantly.

## Actor Mobility

| Mobility | Description |
|----------|-------------|
| Static | Never moves. Baked into lightmaps. Cheapest. |
| Stationary | Doesn't move but can change light color/intensity. Partial baking. |
| Movable | Can move at runtime. Fully dynamic lighting. Most expensive for lights. |

Changing a mesh from Static to Movable means it can no longer contribute to or receive baked lighting.

## World Outliner

- **Search bar**: Filter actors by name.
- **Folders**: Right-click > New Folder. Drag actors in. Folders don't exist in the game world — editor-only organization.
- **Visibility toggle** (eye icon): Hides in editor only, not in game.
- **Lock icon**: Prevents selection in viewport.
- **Type column**: Shows actor class.

Selecting in the outliner highlights in the viewport and vice versa.

## Snapping and Alignment

- **Surface snapping**: Hold **Alt+End** or enable Surface Snapping in toolbar — actors snap to surfaces when moved.
- **Align to floor**: Select actors > right-click viewport > Snap/Align > Align Bottom to Floor.
- **Align actors**: Select multiple > right-click > Snap/Align > options to align by axes.
- **Grid snap**: Toggle with the magnet icon at viewport bottom. Change increment with the number next to it.

## Working with Static Mesh Actors

- Double-click a placed Static Mesh Actor to open the Static Mesh Editor.
- **Collision**: Set in Static Mesh Editor under Collision menu. Auto-generate box/sphere/convex. Or use UCX_ prefixed meshes exported from DCC tools.
- **LODs**: Static Mesh Editor > LOD Settings. Auto-generate or import per-LOD meshes.
- **Nanite**: Static Mesh Editor > Enable Nanite (checkbox in Details). Works best on high-poly hero assets.

## Volumes

Volumes are box/sphere/custom brush actors that define regions:

- **Trigger Volume**: Generates overlap events for Blueprints.
- **Post Process Volume**: Applies post-process settings (bloom, exposure, color grading) within the volume. Check **Infinite Extent** to apply globally.
- **Blocking Volume**: Invisible collision wall.
- **Nav Mesh Bounds Volume**: Defines where the AI navigation mesh is generated. Required for any AI movement.
- **Kill Z Volume**: Destroys actors that enter it. For out-of-bounds regions.
- **Audio Volume**: Controls ambient sound reverb and attenuation within a region.

## Landscape

Create via Place Actors > Landscape or the Landscape mode toolbar button.

- **Sculpt tools**: Raise/Lower, Smooth, Flatten, Ramp, Erosion.
- **Paint tools**: Paint material layers onto terrain (requires a Landscape Material with Landscape Layer Blend nodes).
- **Manage tab**: Resize, add components, import/export heightmap (.r16 or .png).
- Landscape uses its own material system — regular materials must use **Landscape Layer Blend** node for multi-layer painting.

## Level Blueprint

Every level has a **Level Blueprint** — access via toolbar > Blueprints > Open Level Blueprint. Use it for level-specific events (cinematic triggers, one-off logic). Avoid putting reusable logic here; use Actor Blueprints instead.

## Saving and Levels

- **Ctrl+S**: Save current level.
- **Ctrl+Shift+S**: Save all modified assets.
- Unsaved assets show a **\*** in the Content Browser and World Outliner.
- **File > New Level**: Choose from templates (Basic, Open World, VR Basic, Empty).
- Sub-levels: Use Window > Levels panel to manage persistent + streaming sub-levels.

## Documentation

Official UE5 level editing documentation — cite these when relevant:

- Placing actors: https://dev.epicgames.com/documentation/en-us/unreal-engine/placing-actors-in-unreal-engine
- Selecting and transforming actors: https://dev.epicgames.com/documentation/en-us/unreal-engine/transforming-actors-in-unreal-engine
- World Outliner: https://dev.epicgames.com/documentation/en-us/unreal-engine/world-outliner-in-unreal-engine
- Volumes: https://dev.epicgames.com/documentation/en-us/unreal-engine/volumes-in-unreal-engine
- Landscape overview: https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-outdoor-terrain-in-unreal-engine
- Landscape sculpt tools: https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-sculpt-mode-in-unreal-engine
- Level Blueprint: https://dev.epicgames.com/documentation/en-us/unreal-engine/level-blueprint-in-unreal-engine
- Actor mobility: https://dev.epicgames.com/documentation/en-us/unreal-engine/actor-mobility-in-unreal-engine
