---
layout: single
title: "The Planning Scene"
date: 2026-03-15
classes: wide
author_profile: false
---

The MoveIt 2 planning scene is a simplified, static, approximate model of reality that the motion planner uses to check for collisions.

## What the Planning Scene Contains

The planning scene is a data structure maintained by the `PlanningSceneMonitor` node. It contains:

- **Robot geometry**: the collision meshes for every link of every robot in the URDF, in their current configuration as computed from the joint state
- **World collision objects**: geometric primitives (boxes, spheres, cylinders), meshes, or occupancy maps representing obstacles
- **The Allowed Collision Matrix (ACM)**: a table specifying which link pairs are permitted to be in contact without triggering a collision

At any moment, the planning scene represents the planner's *belief* about the world. It is updated from:
- Joint states → robot pose (continuous, ~15 Hz)
- Explicitly published collision objects → static/dynamic obstacles (on-demand)
- Sensor data → occupancy map (if configured)

---

## What the Planning Scene Is Not

### It Is Not Real-Time

The planning scene is updated at 15 Hz. Between updates, the planner's model of the world is stale. A fast-moving object can enter the workspace between planning scene updates and not be visible to the planner. This is acceptable when the environment is approximately static (fixed obstacles, slow-moving robots) and not acceptable for highly dynamic environments with fast-moving objects or humans.

### It Is Not the World

Every obstacle in the planning scene is explicitly placed there by software. If you forget to add a table, the planner will plan trajectories through the table. If your hand-eye calibration is off by 20 mm, the planner will place obstacles 20 mm from where they actually are. The planning scene is only as accurate as the data you feed it.

### It Is Not Conservative by Default

A common misconception is that MoveIt 2 is "safe by default." It is not. By default, the planner checks for collisions between robot links and planning scene objects — but only at the resolution specified by the collision checking configuration. The default collision detection checks discrete waypoints along the trajectory. An interpolated path between two collision-free waypoints can pass through a collision state if the interpolation step is too coarse.


---

## The ACM and Padding

The Allowed Collision Matrix and link padding are the two primary levers for tuning what the planning scene treats as a collision. The ACM scopes which link pairs FCL checks at all; padding inflates every link's geometry before any check is performed. Both are configured statically in the SRDF and are consumed directly by the underlying collision engine.

Their mechanics — how the ACM is consulted by `CollisionEnvFCL::checkSelfCollisionHelper`, how padding is applied via `updatedPaddingOrScaling()`, and the specific values used in MARS — are covered in the [Collision Avoidance]({% post_url 2026-03-04-collision_avoidance %}) post.

---

## The Planning Scene Is a Model

The core insight: the planning scene is a model. All models are wrong; some are useful. The utility of the MARS planning scene model is that it provides a conservative, reproducible, computationally tractable basis for collision-free trajectory generation. Its accuracy is bounded by the quality of the robot's URDF, the precision of obstacle placement, and the frequency of state updates.

In practice, the 5–7 cm link padding applied in MARS produces false negatives: 14 out of 100 test configurations were rejected by the planner because padded geometries overlapped, even though the physical links would not have touched. Zero unplanned physical collisions occurred across those 100 tests. The margin appears appropriate; whether it is more conservative than necessary is a calibration question for future work.

Treating the planning scene as ground truth — assuming that collision-free in the model means collision-free in the world — is the error. The padding exists precisely because that assumption is not made.
