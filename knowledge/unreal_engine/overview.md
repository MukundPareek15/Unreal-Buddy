# Unreal Engine 5 — Editor Overview

## Editor Layout

The UE5 editor has five main areas:

- **Viewport** (center): 3D scene view. WASD + right-click to fly. F focuses the selected actor. G toggles game view (hides editor chrome). Hold Alt + LMB/RMB/MMB to orbit/dolly/pan.
- **World Outliner** (top-right): Tree of every actor in the level. Drag to reparent. Folder icon creates folders. Lock icon prevents selection.
- **Details Panel** (bottom-right): Properties of the selected actor/component. Pin the panel to lock it to a specific actor.
- **Content Browser** (bottom): Project assets. Ctrl+Space opens it if closed. Right-click to import or create assets. Filter bar on the left. Sources panel shows folder tree.
- **Toolbar** (top): Play, Simulate, Build Lighting, Source Control. The three dots (...) on the right opens extra toolbar options.

## Main Editor Modes

Switch via the toolbar mode selector (top-left of viewport):

- **Select Mode**: Default. Click actors to select. Ctrl+click to multi-select.
- **Landscape Mode**: Paint and sculpt terrain.
- **Foliage Mode**: Paint foliage instances onto surfaces.
- **Mesh Paint Mode**: Vertex-paint meshes.
- **Modeling Mode**: Polygon modeling tools (UE5+).

## Common Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Move gizmo | W |
| Rotate gizmo | E |
| Scale gizmo | R |
| Focus selected | F |
| Duplicate | Alt + drag |
| Snap to floor | End |
| Frame all | A (in viewport) |
| Play in editor | Alt+P |
| Eject (PIE) | F8 |
| Open Content Browser | Ctrl+Space |
| Save current level | Ctrl+S |
| Save all | Ctrl+Shift+S |
| Open asset | double-click in Content Browser |
| Find actor in scene | Ctrl+F |

## Project Structure

- **Content/**: All in-editor assets (.uasset, .umap). Never move these outside the editor.
- **Source/**: C++ source files. Build via Visual Studio or Rider.
- **Config/**: .ini files for project settings (DefaultEngine.ini, DefaultGame.ini, etc).
- **Saved/**: Logs, screenshots, autosaves. Safe to delete.
- **Intermediate/**: Build artifacts. Safe to delete.

## World Partition vs Persistent Level

UE5 projects can use **World Partition** (open world streaming) or the classic **Persistent Level + Sub-levels** setup. In World Partition, actors stream in/out based on distance. Check Edit > World Settings > Enable World Partition to see which mode the project uses.

## Output Log

Window > Output Log. Essential for debugging. Filter by category (LogBlueprint, LogTemp, etc). PrintString and UE_LOG output appears here during PIE.

## Project Settings vs Editor Preferences

- **Edit > Project Settings**: Affects the shipped game (input mappings, rendering features, plugins).
- **Edit > Editor Preferences**: Affects only your local editor experience.

## Documentation

Official UE5 documentation — cite these when relevant:

- Editor interface overview: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-editor-interface
- Keyboard shortcuts: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-editor-keyboard-shortcuts
- Project structure and directories: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-directory-structure
- World Partition: https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine
- Level Streaming: https://dev.epicgames.com/documentation/en-us/unreal-engine/level-streaming-in-unreal-engine
- Output Log and debugging: https://dev.epicgames.com/documentation/en-us/unreal-engine/logging-in-unreal-engine
