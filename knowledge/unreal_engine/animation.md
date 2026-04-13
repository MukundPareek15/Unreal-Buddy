# Unreal Engine 5 — Animation

## Animation Asset Types

| Asset | Description |
|-------|-------------|
| **Skeleton** | Bone hierarchy shared by all meshes/animations for a character. |
| **Skeletal Mesh** | A mesh bound to a Skeleton. The visible character. |
| **Animation Sequence** | A single animation clip (walk, idle, jump). |
| **Blend Space** | Blends multiple animations by 1D or 2D parameters (e.g., speed + direction). |
| **Animation Montage** | Composable clip for gameplay-triggered animations (attacks, reactions). |
| **Animation Blueprint** | The logic graph that drives which animations play and how they blend. |
| **Control Rig** | Procedural rig for runtime IK, FK, and pose correction. |
| **Pose Asset** | Stores named poses for facial animation or additive blending. |

## Animation Blueprint

The Animation Blueprint (AnimBP) runs every frame to determine the final pose.

Two main graphs:
- **Event Graph**: Standard Blueprint logic. Update variables here (speed, is_falling, etc) each frame using **Event Blueprint Update Animation**.
- **Anim Graph**: Pose-computation graph. Starts from **Output Pose** node on the right. Feeds through state machines, blend nodes, and sequence players.

### Anim Graph Key Nodes

| Node | Description |
|------|-------------|
| State Machine | Manages animation states (Idle, Walk, Run, Jump) with transitions. |
| Blend Poses by Bool | Plays A or B based on a boolean. |
| Layered Blend per Bone | Blends upper/lower body separately. |
| Apply Additive | Adds an additive animation on top of a base pose. |
| Two Bone IK | IK for arms/legs to reach targets. |
| Look At | Rotates a bone to face a target. |
| Sequence Player | Plays a single AnimSequence. |
| Blend Space Player | Drives a Blend Space with parameters. |

## State Machine

Inside an Anim Graph State Machine:
- Each **State** contains its own mini anim graph (plays a sequence or blend space).
- **Transitions** connect states. Click the transition arrow to set its rule (a Boolean expression).
- **Automatic Rule**: Check "Automatic Rule Based on Sequence Player" to auto-transition when the clip ends.
- **Transition blend time**: Set in the transition properties. Crossfade duration in seconds.

## Blend Spaces

Blend Spaces blend animations based on input parameters.

- **1D Blend Space**: One axis (e.g., Speed → walk to run).
- **Blend Space (2D)**: Two axes (e.g., Speed + Direction → 8-directional movement).

Editing: Drag animation samples onto the grid. UE interpolates between them. Set **Axis Settings** for the min/max range and name of each axis.

In AnimBP, use a **Blend Space Player** node and connect your Speed/Direction variables to the input pins.

## Animation Montage

Montages let you trigger animations from gameplay code/Blueprints and control sections.

- Divide a montage into **Sections** (e.g., Start, Loop, End) via the Sections panel.
- Add **Anim Notify** events at specific frames (trigger sounds, particles, gameplay events).
- Play in Blueprint with `Play Anim Montage` node on a Character.
- Stop with `Stop Anim Montage`. Check completion with `On Montage Ended` delegate.
- Montages play on a **Slot** — add a `Slot` node in the Anim Graph at the position where montages should override the base pose (typically above the State Machine output).

## Notify Events

**Anim Notifies** fire events at specific frames in a sequence or montage:

- **Anim Notify**: Single-frame event. Handle in AnimBP via `AnimNotify_[Name]` function or in the owning actor.
- **Anim Notify State**: Has Begin/Tick/End. Good for "weapon is active" windows.
- **Sound Notify**: Plays a sound at a frame.
- **Particle Effect Notify**: Spawns particles.
- **Footstep Notify**: Common pattern — trigger a footstep sound/decal at the foot-strike frame.

## Inverse Kinematics (IK)

- **Two Bone IK**: Classic IK for arms/legs. Set Root, Joint (elbow/knee), Effector bone. Connect an Effector Location (world-space target).
- **FABRIK**: Multi-bone chain IK. More flexible for spine/tail.
- **Full Body IK (FBIK)**: UE5 Control Rig-based. Solves whole body simultaneously.

Common use: foot IK to conform feet to uneven terrain. Trace the floor, feed the hit location as the effector target.

## Root Motion

Root motion moves the character's capsule using the animation's root bone movement rather than the Character Movement Component.

Enable in: Animation Sequence > Asset Details > Root Motion > Enable Root Motion.

In Character Blueprint: Character Movement > Root Motion From Everywhere (or From Montages Only).

Use root motion for: precise melee attacks, climbing, rolls where animation must drive exact displacement.

## Retargeting

Retargeting applies animations from one Skeleton to another (e.g., Mixamo to UE5 Mannequin).

UE5 uses **IK Retargeter** and **IK Rig** assets:
1. Create IK Rig for source and target skeletons.
2. Create IK Retargeter referencing both IK Rigs.
3. In the Retargeter, map chains and alignment poses.
4. Export retargeted animations or use the Retargeter at runtime.

## Animation Optimization

- Set **Update Rate Optimization** on Skeletal Mesh components for background characters — reduces update frequency based on distance/visibility.
- Use **LODs** on Skeletal Meshes — lower LODs can disable cloth, physics, and use simpler AnimBPs.
- **Fast Path**: Keep Anim Graph nodes on Fast Path (lightning bolt icon). Avoid calling Blueprint functions from pure Anim Graph nodes.
- **URO (Update Rate Optimization)**: Enables in the Skeletal Mesh Component settings. Characters far away update animations less frequently.

## Documentation

Official UE5 animation documentation — cite these when relevant:

- Animation overview: https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-animation-system-in-unreal-engine
- Animation Blueprint: https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprints-in-unreal-engine
- State machines: https://dev.epicgames.com/documentation/en-us/unreal-engine/state-machines-in-unreal-engine
- Blend spaces: https://dev.epicgames.com/documentation/en-us/unreal-engine/blend-spaces-in-unreal-engine
- Animation Montage: https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-montage-in-unreal-engine
- Anim Notifies: https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-notifies-in-unreal-engine
- IK Rig and retargeting: https://dev.epicgames.com/documentation/en-us/unreal-engine/ik-rig-in-unreal-engine
- Root motion: https://dev.epicgames.com/documentation/en-us/unreal-engine/root-motion-in-unreal-engine
- Control Rig: https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-in-unreal-engine
