---
layout: single
title: "Robot Description"
date: 2026-02-02
classes: wide
author_profile: false
---


## How to decribe a robot: The Unified Robot Description Format

When you command Ned2 to pick an object detected by its wrist camera, how does the computer know where to move the gripper? How do you know whether a planned motion causes self-collision? 

We'll exlore the two critical systems: **URDF** which defines Ned2's structure (links, joints, and geometry) and  **TF/TF2**  which tracks where each joint actually is in space over time.

## URDF — Unified Robot Description Format

URDF is the XML format ROS uses to describe robots. It is a blueprint that captures physical details: links, joints, visuals, collision shapes, inertial properties, sensors, and how everything connects.

At its core URDF models a robot as links connected by joints:

- Links — rigid bodies (wheel, link, sensor mount)
- Joints — connections that define relative motion between links

### Links (building blocks)

Each link may include:

- Visual properties (meshes, basic shapes, colors)
- Collision geometry (simplified shapes for physics)
- Inertial properties (mass, center of mass, inertia matrix)

Example (URDF):

```xml
<link name="base_link">
  <visual>
    <geometry>
      <box size="0.6 0.4 0.2"/>
    </geometry>
    <material name="blue"/>
  </visual>
  <collision>
    <geometry>
      <box size="0.6 0.4 0.2"/>
    </geometry>
  </collision>
</link>
```

#### Using mesh files

URDF supports common 3D formats:

- STL — simple, widely supported (no color/texture)
- COLLADA/DAE — supports materials and textures
- OBJ — good balance of features and compatibility

Example referencing package resources:

```xml
<link name="gripper_link">
  <visual>
    <geometry>
      <mesh filename="package://my_robot_description/meshes/gripper.dae" scale="0.001 0.001 0.001"/>
    </geometry>
  </visual>
  <collision>
    <geometry>
      <mesh filename="package://my_robot_description/meshes/gripper_collision.stl"/>
    </geometry>
  </collision>
</link>
```

Use the `package://` URI to keep your robot description portable instead of hardcoded absolute paths.

### Joints (connections)

Joints specify how links move relative to each other. Common joint types:

- `fixed` — no movement
- `revolute` — rotation with limits (hinge)
- `continuous` — unlimited rotation (wheel)
- `prismatic` — linear sliding
- `planar` — motion within a plane
- `floating` — unconstrained 6‑DOF

Example (URDF):

```xml
<joint name="base_to_arm" type="revolute">
  <parent link="base_link"/>
  <child link="arm_link"/>
  <origin xyz="0 0 0.1" rpy="0 0 0"/>
  <axis xyz="0 0 1"/>
  <limit lower="-1.57" upper="1.57" effort="10" velocity="1"/>
</joint>
```

URDF is a tree: one root link, all other links connect via a single parent joint (no loops). Use SRDF or semantic descriptions for additional groupings.

### Units

URDF uses SI units:

- Distance — meters
- Angles — radians
- Mass — kilograms
- Time — seconds

## Beyond geometry

A complete robot description  includes:

1. **Kinematics** — parent/child relationships and joint axes define how Ned2 moves.
2. **Dynamics** — mass, inertia, damping, friction enable realistic simulation and constrain trajectory planning. When MoveIt2 plans for Ned2's 300g payload capacity, it consults inertial properties to determine feasible accelerations and speeds. Gazebo uses these values to simulate physics accurately; without them, simulated behavior diverges from hardware.
3. **Sensors** — camera, LiDAR, IMU mounts and orientations specify where sensors are attached. Ned2's wrist camera is mounted on `tool_link`; URDF declares its pose. TF then transforms sensor data (camera detections, point clouds) into planning coordinates automatically.
4. **Actuators** — transmissions and motor parameters (via plugins) convert joint commands into motor control. Ned2's actuator specs determine speed profiles and effort limits; these are consulted by the controller when executing planned trajectories.

### Xacro — URDF on steroids

Xacro is an XML macro language that makes URDF maintainable: variables, macros, math, and conditional logic reduce duplication.

```xml
<xacro:property name="wheel_radius" value="0.1"/>
<xacro:property name="wheel_width" value="0.05"/>

<xacro:macro name="wheel" params="prefix">
  <link name="${prefix}_wheel">
    <visual>
      <geometry>
        <cylinder radius="${wheel_radius}" length="${wheel_width}"/>
      </geometry>
    </visual>
  </link>
</xacro:macro>
```

Validate and visualize before deployment:

```bash
check_urdf my_robot.urdf
xacro my_robot.xacro
urdf_to_graphiz my_robot.urdf
```

### Format Comparison

| Format | Purpose | Use Case | Complexity |
|--------|---------|----------|-----------|
| **URDF** | Kinematic tree structure (links, joints, meshes) | Simulation, visualization, kinematics | Raw XML; verbose |
| **Xacro** | Parameterized URDF (variables, macros, math) | Robots with repeated structures; maintainability | XML + macro language |

**When to use what**: Write Ned2's main structure in Xacro to reduce duplication (6 joints, multiple sensors). Compile Xacro to URDF for use with simulators and visualization. 

## TF / TF2 — the transform system

If URDF describes the robot's structure, TF (TF2) tracks where each frame is in space over time. TF manages a tree of coordinate frames and broadcasts transforms so you can convert poses and sensor data between frames easily.

For Ned2, standard frames include `base_link` (the arm base), `tool_link` (the gripper), `camera_frame` (wrist camera), `odom` (odometry reference), and `map` (global reference). Each frame has a fixed relationship defined in the URDF; TF broadcasts these relationships continuously, accounting for joint motion.

### Why TF matters

Sensor readings, commands, and detections are expressed in different frames. Ned2's wrist camera publishes detected objects in `camera_frame`. Your motion planner needs to know: where is that object relative to `tool_link`? TF answers this by composing transforms: `camera_frame` → `tool_link` (from URDF) → `base_link` (from joint states). This transformation chain is the backbone of perception-to-manipulation pipelines.

TF also returns transforms from past timestamps—critical for hand-eye calibration and sensor fusion. You can ask: "Where was Ned2's wrist when this camera frame arrived?" This temporal query is what makes multi-sensor systems coherent.

### Transform types

- Static transforms — constant relations (published once):

```bash
ros2 run tf2_ros static_transform_publisher 0 0 0.5 0 0 0 base_link camera_link
```

- Dynamic transforms — continuously changing (joint states, wheel rotations) and published at runtime.

## Practical Limitations & Pitfalls

Understanding what URDF *can't* do prevents debugging nightmares.

**Missing collision geometry**: If you forget `<collision>` tags, your robot has no collision shape. Gazebo won't detect self-collisions; the planner won't warn when joints hit each other. Always define collision geometry, even if simplified relative to visual meshes.

**Incorrect joint limits**: Ned2's joint limits are fixed by design. Document them precisely. Wrong limits break planning: limits that are too tight prevent valid motions; limits that are too loose allow impossible configurations. Always validate limits against the robot's mechanical specification.

**Mesh scale errors**: Ned2's meshes must align with kinematic dimensions exactly. A mesh scaled 0.1 units off creates a divergence between what MoveIt2 sees and what actually moves. Use `urdf_to_graphviz` to visualize the tree and spot scaling issues early.

**Hardcoded paths**: Never use absolute paths like `/home/user/my_robot/meshes/`. Use `package://` URIs: `package://ned2_description/meshes/gripper.dae`. This keeps the URDF portable across machines and workspaces.

**Mismatched visual and collision geometries**: It's tempting to use high-poly meshes for visuals and rough boxes for collision. that's fine but when they diverge significantly, planning behaves unexpectedly. Ned2's gripper collision may allow clearances the visual suggests aren't there.

## Bringing it together

The `robot_state_publisher` node reads your URDF, subscribes to `/joint_states`, computes forward kinematics, and publishes TF transforms for every link in real time. Here's the data flow:

1. URDF file (or Xacro compiled to URDF) → `robot_state_publisher` loads kinematic tree
2. Hardware/controller publishes `/joint_states` (Ned2's joint angles)
3. `robot_state_publisher` computes forward kinematics for each joint
4. TF broadcasts transforms: `base_link` → `shoulder_link` → `arm_link` → ... → `tool_link`
5. Any node needing spatial information (MoveIt2, perception, control) queries TF

the static URDF description becomes a living model synchronized with hardware.


