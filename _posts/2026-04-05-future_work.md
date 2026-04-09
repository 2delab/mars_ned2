---
layout: single
title: " Future Work"
date: 2026-04-05
classes: wide
author_profile: false
---

MARS solves a specific problem: coordinated dual-arm manipulation on namespace-isolated ROS2 hardware, with planning-time collision safety and three selectable coordination modes. It does not solve the general multi-arm coordination problem. This post maps the open problems and the directions where the architecture extends naturally versus where new work is needed.

---

## The Immediately Solvable

### Driver-Level Synchronisation

The largest gap between simulation and hardware for synchronised mode is the 20–50 ms inter-arm start offset caused by sequential trajectory dispatch. A synchronisation shim at the driver level — a barrier that releases both hardware controllers simultaneously via a shared signal — would eliminate this offset without changes to the MoveIt2 planning pipeline.

This is well-scoped: implement a `SynchronisedActionClient` that sends both trajectory goals and then releases a start signal to both arms simultaneously. The Niryo hardware likely supports this via its internal ROS1 infrastructure; whether the ROSBridge exposes it is the open question.

### Tighter Safety Margins

The 5 cm per-link padding produces a 14% planning rejection rate for boundary configurations. Calibrating the padding to measured hardware error (positional repeatability + velocity-scaled latency) rather than estimated values would reduce unnecessary rejections. This is one measurement session with a calibration target and a timing analysis of the ROSBridge latency distribution.

### Pre-Dispatch Collision Validation

Adding a final collision check to the `TrajectoryProxy` — verifying the current robot state against the planned trajectory start state before dispatch — would harden the system against the edge case where the robot moves between planning and execution. This is a 20-line addition to the proxy based on the Stoop et al. (2023) pattern.

---

## The Architecturally Natural Extensions

### Three or More Arms

The `JointStateManager` and `TrajectoryProxy` are parameterised by arm count, not hardcoded for two. Adding a third arm requires:
- Extending the composite URDF with a third arm's kinematic chain
- Adding the third arm's namespace to the JointStateManager configuration
- Adding a third planning group and cross-arm collision pairs to the SRDF

The computational challenge is 18-DOF planning for the combined group and the exponentially larger collision check set (all cross-arm link pairs). Whether RRTConnect remains tractable at 18-DOF is an empirical question. Shome et al.'s dRRT* (2019) is the natural alternative for higher-DOF multi-robot problems.

### Dynamic Obstacle Integration

The planning scene monitor supports occupancy map integration via the `PointCloudOctomapUpdater` plugin. Connecting a depth camera to the planning scene would extend MARS to handle unmodelled objects in the workspace. The architecture already supports this — the `collision_avoidance.md` post documents the octomap configuration. The missing piece is commissioning a depth camera with calibrated transform to the robot base frame.

### Online Replanning

MoveIt2 supports replanning on execution preemption — the planner can regenerate the remainder of a trajectory from the current state if execution is interrupted. Integrating this with the `TrajectoryProxy` (detect abort, replan from current state, redispatch) would handle the ROSBridge connection drop failure mode gracefully instead of requiring a manual restart.

---

## The Harder Problems

### Adaptive Safety Margins

Fixed padding is conservative and uniform. A more principled approach would compute safety margins dynamically based on:
- Current velocity (higher velocity → larger margin needed)
- Distance to the other arm (closer → tighter margin, more careful checking)
- Task type (free motion → standard margin; approach to shared workspace → larger margin)

He (2026) demonstrates risk-aware adaptive margins for MPC systems in dynamic environments. Applying this concept to the MoveIt2 planning scene — dynamically updating link padding based on arm proximity and velocity — would produce a system that is less conservative in free space and more conservative near collision boundaries.

This requires changes to the `PlanningSceneMonitor` update cycle, which is currently read-only with respect to padding parameters.

### Task-Adaptive Mode Selection

Currently, the coordination mode is a user-specified parameter. Automating mode selection — switching to async when arms are in separated zones, hybrid when they approach shared space, sync when precise relative positioning is required — would reduce the configuration burden and prevent the zone-crossing failure mode.

The inputs to this decision are available at runtime: both arms' current joint configurations (from the JointStateManager), the planned target poses, and the workspace geometry. Building an automaton that maps these inputs to coordination mode selection is a bounded engineering problem with a clear interface.

### Generalisation Beyond Pick-and-Place

The MARS validation uses pick-and-place as the primary benchmark. This is appropriate for the coordination architecture question but leaves unexplored whether the system performs correctly on tasks requiring continuous path following (welding, painting, deburring) rather than point-to-point motion. Continuous path tasks impose tighter timing requirements on synchronised mode and tighter spatial requirements on asynchronous workspace partitioning.

---

## The Case for Adaptive Safety Margins

Of all the future work directions, adaptive safety margins have the highest ratio of impact to engineering cost. The current fixed padding produces correct results at the cost of a 14% planning rejection rate at workspace boundaries. Variable padding — larger near the shared boundary, tighter in free space — would reduce false negatives without compromising safety.

The implementation path is clear: a `PaddingManager` node that monitors arm proximity via the planning scene and updates link padding in the SRDF parameters at runtime. The MoveIt2 planning scene supports parameter updates; the challenge is determining the correct padding schedule as a function of arm configuration and task type.

This is the extension that would most directly improve the system's practical utility for real coordination tasks.
