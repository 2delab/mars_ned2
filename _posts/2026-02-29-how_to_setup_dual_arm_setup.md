---
layout: single
title: "Multiple Robots in MoveIt2"
header:
  teaser: /assets/images/posts/multiple_robots_moveit2.png
date: 2026-02-29
classes: wide
author_profile: false
---

## How to configure Multiple robots for MoveIt2

There is not just a single way to solve the dual arm problem in MoveIt2. here we'll discuss three distinct architectural approaches, each with different tradeoffs for collision awareness, scalability, and implementation complexity. This post documents each approach, when to use it, and the specific constraints that led MARS decision making.


## Approach 1: Unified URDF with Multiple Move Groups

### Description

A single URDF file contains all robots with unique prefixes for each robot's links and joints. A single MoveIt2 instance manages the full system through multiple planning groups. one per arm, plus an optional combined group spanning all arms.

### Structure

```
# Unified URDF link naming
arm_1_base_link → arm_1_shoulder_link → ... → arm_1_tool_link
arm_2_base_link → arm_2_shoulder_link → ... → arm_2_tool_link
world (fixed base connecting both arm bases)

# SRDF planning groups
group: arm_1  (joints: arm_1_joint_1 ... arm_1_joint_6)
group: arm_2  (joints: arm_2_joint_1 ... arm_2_joint_6)
group: dual   (joints: arm_1_joint_1...6 + arm_2_joint_1...6)
```

### Advantages

- **Single shared planning scene**: both robots exist in the same collision world which means inter-arm collision checking is automatic
- **Unified TF tree**: one Robot State Publisher publishes all transforms 
- **Multi-group planning**: the `dual` group enables 12-DOF joint planning for synchronised motion; individual groups enable independent 6-DOF planning
- **Single node manages all robots**: one `move_group` process, one planning scene monitor, one action server endpoint

### Disadvantages

- All robots must be defined statically at launch; dynamic addition is not supported
- Computational overhead scales with total DOF for planning scene updates

### Best For

Tightly coordinated dual-arm systems operating in a shared workspace where arms must avoid each other or execute synchronised bimanual tasks.


## Approach 2: Separate URDFs with Independent Planning Scenes

### Description

Each robot has its own URDF, MoveIt2 configuration, and `move_group` node running in isolated ROS2 namespaces. No shared state exists between planning scenes.

### Structure

```
# Namespace isolation
/arm_1/move_group  → planning scene contains only arm_1 geometry
/arm_2/move_group  → planning scene contains only arm_2 geometry

# No cross-arm collision checking
# arm_1 plans freely through arm_2's physical space
# arm_2 plans freely through arm_1's physical space
```

### Advantages

- Fully modular: each robot can be modified, upgraded, or replaced independently
- Reduced per-arm planning complexity (6-DOF instead of 12-DOF)
- Easy to test each arm in isolation
- Scalable: adding a third arm is adding a third namespace

### Disadvantages

- **No automatic inter-robot collision checking** — two planners can independently generate trajectories that collide physically
- Coordinated motion requires external arbitration logic
- Cannot plan bimanual tasks requiring cross-arm constraint satisfaction

### Best For

Loosely coupled systems where arms operate in spatially separate zones and rarely interact. Safety enforced by workspace partitioning rather than planning-time collision checking.


## Approach 3: Separate URDFs with Shared Planning Scene Topic

### Description

Each robot has its own URDF and `move_group`, but all nodes subscribe to and publish on a shared `/planning_scene` topic, allowing each planner to be aware of the other's collision objects.

### Structure

```
# Shared planning scene
arm_1/move_group  ─┬─ publishes arm_1 geometry to /planning_scene
arm_2/move_group  ─┘─ subscribes to /planning_scene (sees arm_2 too)
                  └─ publishes arm_2 geometry to /planning_scene
                     arm_1/move_group subscribes (sees arm_1 too)
```

### Why It Fails in Practice

This approach appears scalable on paper but breaks due to race conditions and namespace conflicts. Both `move_group` instances attempt to own the planning scene monitor, producing inconsistent state, duplicate collision object IDs, and unpredictable planner behaviour.

The MoveIt2 architecture assumes one authoritative planning scene per `move_group` instance. Sharing a single topic between two independent instances violates this assumption. Stoop et al. (2023) document this failure mode in their work on multi-robot asynchronous trajectory execution in MoveIt2, ultimately recommending against this pattern for safety-critical coordination.

### Best For

Not recommended where inter-robot collision avoidance is required. Usable for loosely coupled systems if the shared scene is read-only for one planner, but requires custom middleware.

---

## Why MARS Uses Approach 1

Collision-aware coordinated motion in a shared workspace imposes four specific requirements:

1. **Inter-arm collision checking at planning time** → requires both arms in the same planning scene
2. **12-DOF joint planning for synchronised mode** → requires a combined `dual` planning group
3. **Independent 6-DOF planning for asynchronous mode** → requires per-arm groups within the same SRDF
4. **Unified state representation** → requires a single Robot State Publisher consuming a merged joint state topic

Only Approach 1 satisfies all four. The added URDF complexity is a one-time engineering cost. The payoff is structural collision safety across all three coordination modes by construction.
