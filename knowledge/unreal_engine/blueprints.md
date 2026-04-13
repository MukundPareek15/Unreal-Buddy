# Unreal Engine 5 — Blueprints

## Blueprint Classes

A Blueprint is a visual script that lives as a .uasset. Main types:

- **Actor Blueprint**: Placeable in the world. Right-click Content Browser > Blueprint Class > Actor.
- **Character Blueprint**: Actor with movement component + mesh. Base for player/NPCs.
- **GameMode Blueprint**: Rules of the game — which pawn to spawn, win conditions.
- **Widget Blueprint**: UI (HUD, menus). Created under User Interface > Widget Blueprint.
- **Blueprint Function Library**: Static utility functions callable from any Blueprint.
- **Blueprint Interface**: Defines a contract of functions; multiple Blueprint types can implement it without inheritance.

## Blueprint Editor Layout

- **Event Graph**: Main script canvas. Right-click to add nodes.
- **Components Panel** (top-left): Add/remove components (mesh, collision, lights, etc).
- **My Blueprint** (left): Variables, functions, macros, event dispatchers, interfaces.
- **Details Panel** (right): Properties of the selected node or component.
- **Viewport tab**: 3D preview of components.

## Event Graph Basics

Execution flows along white wires (exec pins). Data flows along colored wires (typed pins). Nodes without exec pins are pure functions — they evaluate on demand.

Common starting events:
- **Event BeginPlay**: Fires once when the actor spawns/level starts.
- **Event Tick**: Fires every frame. Has Delta Seconds output. Avoid heavy logic here.
- **Event ActorBeginOverlap / EndOverlap**: Triggered by collision overlap.
- **Event Hit**: Triggered by blocking collision.
- **Custom Event**: Create your own callable event. Right-click > Add Custom Event.

## Variables

Add variables in My Blueprint panel > Variables > + button. Types:
- Boolean, Integer, Integer64, Float, String, Name, Text
- Vector, Rotator, Transform
- Object Reference (reference to another actor/component)
- Array, Map, Set (container types)

Set **Instance Editable** (eye icon) to expose the variable in the Details panel when the actor is placed in a level. Set **Expose on Spawn** to pass values in when spawning.

**Get vs Set nodes**: Drag a variable onto the graph — choose Get or Set. Set nodes have exec pins; Get nodes are pure.

## Functions and Macros

- **Functions**: Compiled, can have local variables, can be overridden in child Blueprints. Cannot contain latent (timeline/delay) nodes.
- **Macros**: Inline expansion, can contain latent nodes, not overridable. Useful for repeating patterns.
- **Collapse to Function**: Select nodes > right-click > Collapse to Function.

## Blueprint Communication Patterns

**Direct Reference**: Get a reference to another actor (via overlap, cast, or exposed variable) then call functions on it directly.

**Cast To**: Drag off an Actor reference > Cast To [YourBlueprintClass]. Gives typed access to that Blueprint's variables/functions. Fails gracefully via the Cast Failed pin.

**Event Dispatcher**: Defined on the source actor. Other actors bind to it. Source calls it; all bound actors respond. Loose coupling — source doesn't know who's listening.

**Blueprint Interface**: Call interface functions on any actor without knowing its type. Implement the interface on the receiver. Useful for interaction systems.

**Get All Actors Of Class**: Finds all instances of a class in the world. Expensive — avoid every tick.

## Common Useful Nodes

| Node | Description |
|------|-------------|
| Print String | Debug text on screen and in Output Log |
| Delay | Wait N seconds (latent — yellow clock icon) |
| Set Timer by Function Name | Repeat or delay a function call |
| Spawn Actor from Class | Instantiate a Blueprint at runtime |
| Destroy Actor | Remove actor from world |
| Get Player Character / Get Player Controller | Access the player |
| Line Trace by Channel | Raycast from point A to B |
| Branch | If/else |
| Sequence | Execute multiple outputs in order |
| For Each Loop | Iterate an array |
| Do Once | Execute only the first time |
| Flip Flop | Toggle between two outputs |
| Gate | Open/close an execution path |

## Blueprint Debugging

- **Compile button**: Top-left of Blueprint editor. Must compile before changes take effect.
- **Breakpoints**: Right-click a node > Add Breakpoint. PIE pauses on that node.
- **Watch Values**: Right-click a wire or variable > Watch This Value. Shows live value in PIE.
- **Print String**: Easiest debug tool. Shows in viewport and Output Log.
- **Blueprint Debugger**: Window > Blueprint Debugger. Shows call stack and variable values.

## Expose Variable to Details Panel

1. Select variable in My Blueprint panel.
2. In Details: check **Instance Editable**.
3. Optionally check **Expose on Spawn** for spawn-time setting.
4. Optionally set **Category** to group it in the Details panel.
5. Re-compile. The variable now appears in the Details panel when the actor is placed.

## Blueprint vs C++

Blueprints are good for: game logic, rapid iteration, designer-owned systems, one-off actors.
C++ is better for: performance-critical code, reusable engine extensions, complex data structures.
Common pattern: implement base logic in C++, expose it to Blueprint for designers to extend.

## Documentation

Official UE5 Blueprint documentation — cite these when relevant:

- Blueprint overview: https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprints-visual-scripting-in-unreal-engine
- Blueprint class types: https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-class-assets-in-unreal-engine
- Variables: https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-variables-in-unreal-engine
- Functions: https://dev.epicgames.com/documentation/en-us/unreal-engine/functions-in-unreal-engine-blueprints
- Event Dispatchers: https://dev.epicgames.com/documentation/en-us/unreal-engine/event-dispatchers-in-unreal-engine
- Blueprint communication: https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-communication-usage-in-unreal-engine
- Blueprint debugger: https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-debugger-in-unreal-engine
- Blueprint best practices: https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-best-practices-in-unreal-engine
- Expose variable to Details: https://dev.epicgames.com/documentation/en-us/unreal-engine/exposing-variables-in-unreal-engine-blueprints
