---
layout: single
title: " Future Work"
header:
  teaser: /assets/images/posts/future_work.png
date: 2026-04-05
classes: wide
author_profile: false
---

## Key improvement areas

### Driver-Level Synchronisation

The largest gap between simulation and hardware for synchronised mode is the 20–50 ms inter-arm start offset caused by sequential trajectory dispatch. A synchronisation interface at the driver level would eliminate this offset as hardware controllers would have no network delay and execute simultaneously via a shared signal without changes to the MoveIt2 planning pipeline.


### Tighter Safety Margins

The 5 cm per-link padding produces a 14% planning rejection rate for boundary configurations. Calibrating the padding to measured hardware error (positional repeatability + velocity-scaled latency) rather than estimated values would reduce unnecessary rejections. This is one measurement session with a calibration target and a timing analysis of the ROSBridge latency distribution.


### Pre-Dispatch Collision Validation

Adding a final collision check to the `TrajectoryProxy` and verifying the current robot state against the planned trajectory start state before dispatch would harden the system against the edge case where the robot moves between planning and execution.

---

## The Architecturally Natural Extensions

### Three or More Arms

The `JointStateManager` and `TrajectoryProxy` are parameterised by arm count, not hardcoded for two. Adding a third arm requires:

- Extending the composite URDF with a third arm's kinematic chain
- Adding the third arm's namespace to the JointStateManager configuration
- Adding a third planning group and cross-arm collision pairs to the SRDF

The computational challenge is 18-DOF planning for the combined group and the exponentially larger collision check set (all cross-arm link pairs). Whether RRTConnect remains tractable at 18-DOF is an empirical question. 

### Dynamic Obstacle Integration

The planning scene monitor supports occupancy map integration via the `PointCloudOctomapUpdater` plugin. Connecting a depth camera to the planning scene would extend MARS to handle unmodelled objects in the workspace. The architecture already supports this. The missing piece is commissioning a depth camera with calibrated transform to the robot base frame.

### Online Replanning

MoveIt2 supports replanning on execution preemption — the planner can regenerate the remainder of a trajectory from the current state if execution is interrupted. Integrating this with the `TrajectoryProxy` (detect abort, replan from current state, redispatch) would handle the connection drop failures mode gracefully.

---

## The Harder Problems

### Adaptive Safety Margins

Fixed padding is conservative and uniform. A more principled approach would compute safety margins dynamically based on:

- Current velocity (higher velocity → larger margin needed)
- Distance to the other arm (closer → tighter margin, more careful checking)
- Task type (free motion → standard margin; approach to shared workspace → larger margin)

Dynamically updating link padding based on arm proximity and velocity would produce a system that is less conservative in free space and more conservative near collision boundaries.

This requires changes to the `PlanningSceneMonitor` update cycle, which is currently read-only with respect to padding parameters.

### Task-Adaptive Mode Selection

Currently, the coordination mode is a user-specified parameter. Automating mode selection to switch to async when arms are in separated zones and sync when precise relative positioning is required would reduce the configuration burden and prevent the zone-crossing failure mode.

The inputs to this decision are available at runtime: both arms' current joint configurations (from the JointStateManager), the planned target poses, and the workspace geometry. Building an automaton that maps these inputs to coordination mode selection is a bounded engineering problem with a clear interface.

