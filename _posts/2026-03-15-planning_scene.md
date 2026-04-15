---
layout: single
title: "The Planning Scene"
header:
  teaser: /assets/images/posts/planning_scene.png
date: 2026-03-15
classes: wide
author_profile: false
---

## The Planning Scene simplified

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

## Planning Scene Queries During Motion Planning

When MoveIt2's motion planner (RRTConnect or other sampling-based planner) generates a trajectory, it continuously queries the planning scene. The planning loop operates like this:

1. **Sample** a configuration (random point in joint space or biased toward goal)
2. **Query** the planning scene: "Is this configuration collision-free?"
3. **Receive** a binary response: collision detected or not
4. **Accept or reject** the sample based on the response
5. **Repeat** thousands of times until a path to the goal is found

Each query asks the planning scene's collision checker: "Given the current robot geometry (from joint states) and current world state (obstacles, other robots), does this configuration cause contact between any checked link pairs?"

The critical point: **the planning scene is a snapshot of the world taken at the moment planning begins**. If the world changes during planning (an obstacle moves, the other robot shifts position), the planner is unaware. This is acceptable because:

- Planning typically completes in milliseconds (100–500 ms for complex trajectories)
- Execution also happens on a millisecond timescale
- The time window between planning and execution is small relative to robot dynamics
- MARS validation shows zero unplanned collisions across 86 executed trajectories, evidence that the snapshot model is conservative enough in practice

---

## Dual-Arm Planning Scene (MARS Architecture)

The key for MARS lies in how dual-arm collision checking emerges naturally from a single architectural choice: **one URDF containing both arms, managed by one move_group node, sharing one planning scene.**

### How It Works

**The URDF unifies the geometry:**
- The composite URDF file defines arm_1's complete kinematic chain (base → joint_1 → link_1 → joint_2 → ... → end_effector)
- The same URDF defines arm_2's complete kinematic chain starting from its own base
- All 22 links (11 per arm) exist in a single kinematic model

**The move_group loads the composite model:**
- A single `move_group` node launches with the composite URDF as its robot model
- It creates one `PlanningScene` object
- This scene contains the geometry of all 22 links from both arms

**The planning scene contains one FCL world:**
- When the planner queries the planning scene, it's querying a single Flexible Collision Library (FCL) collision world
- This world contains collision geometry for all links from both arms
- All link pairs (arm_1 links against arm_2 links, arm_1 links against themselves, arm_2 links against themselves) are checked in the same FCL database

**Inter-arm collisions are automatic:**
- There is no special logic or messaging to check "does arm_1 collide with arm_2?"
- The Allowed Collision Matrix (ACM) already contains entries for every link pair across the two arms
- When planning the `dual` group (12-DOF composite group), a sampled configuration includes all 12 joint angles from both arms
- That configuration is collision-checked against the shared FCL world; if arm_1_link_3 collides with arm_2_link_2 in the current geometry, the check returns true (collision detected)

<video width="100%" controls autoplay muted loop>
  <source src="/mars_ned2/assets/videos/planning_scene.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>


### Why choose this approach?

The alternative, maintaining separate planning scenes for each robot and synchronising collision checks across a network boundary, would require:
- Two independent `move_group` nodes, one per arm
- Custom message passing to communicate inter-arm collision queries
- Eventual consistency problems (which robot's model of the other's position is authoritative?)

MARS sidesteps all of this. Both arms are unified at the URDF level, so both are inherently visible to a single collision checker. The planning scene is one unified data structure; no cross-process synchronization is needed.

---

## Visualising and Debugging the Planning Scene

Understanding why the planner accepts or rejects a configuration requires seeing the planning scene in action.

### RViz2 Visualization

Launch RViz2 with the MARS configuration and enable these visualization layers:

**Scene Geometry:**
- Shows the static world objects (workspace boundaries, tables, fixtures)
- Checkbox: `MarkerArray → Scene Geometry`

**Scene Collision Objects:**
- Shows any dynamically added collision objects in the planning scene
- Checkbox: `MarkerArray → Scene Collision Objects`

**Link Collision Geometry:**
- Shows the actual collision geometry of every robot link, **with padding applied**
- This is critical for understanding rejections: the padded volumes are what FCL actually checks, not the visual meshes
- Checkbox: `RobotModel → Link Collision Geometry`

When enabled together, RViz2 displays the exact geometry the planner sees: the two arms' collision-padded volumes in their current configuration, plus all world obstacles. If two padded volumes overlap visually in RViz2, the planner will detect a collision at that configuration.

### Inspecting Planning Scene State via ROS2 CLI

The planning scene is managed by a set of ROS2 services and topics. You can query its state directly from the command line:

**List planning scene services:**
```bash
ros2 service list | grep planning_scene
```

This returns services like `/get_planning_scene`, `/apply_planning_scene`, etc.

**Dump the current planning scene:**
```bash
ros2 service call /get_planning_scene moveit_msgs/srv/GetPlanningScene {}
```

This returns the complete planning scene state: all link geometries, all collision objects, the ACM, padding values, and everything else the planner sees.

**Check if a specific configuration is valid:**
Most MoveIt2 setups expose a `/check_state_validity` service or similar. Consult the deployed move_group node's service list for the exact name.

### Understanding Planning Scene Rejections

When the planner rejects a configuration (collision detected), the cause is visible in RViz2:

1. Enable "Link Collision Geometry" in RViz2
2. Manually command the robot (via interactive markers or joint sliders) to the rejected configuration
3. Observe: do any padded link volumes overlap? If yes, that's why the planner rejected it
4. If no overlap is visible, the rejection might be due to self-collision constraints or other non-collision checks

This visual feedback is the primary debugging tool for understanding planner behavior.

---

## What the Planning Scene Is Not

### It Is Not Real-Time

The planning scene is updated at 15 Hz. Between updates, the planner's model of the world is stale. A fast-moving object can enter the workspace between planning scene updates and not be visible to the planner. This is acceptable when the environment is approximately static (fixed obstacles, slow-moving robots) and not acceptable for highly dynamic environments with fast-moving objects or humans.

### It Is Not the World

Every obstacle in the planning scene is explicitly placed there by software. If you forget to add a table, the planner will plan trajectories through the table. If your hand-eye calibration is off by 20 mm, the planner will place obstacles 20 mm from where they actually are. The planning scene is only as accurate as the data you feed it.

### It Is Not Conservative by Default

A common misconception is that MoveIt 2 is "safe by default." It is not. By default, the planner checks for collisions between robot links and planning scene objects, but only at the resolution specified by the collision checking configuration. The default collision detection checks discrete waypoints along the trajectory. An interpolated path between two collision-free waypoints can pass through a collision state if the interpolation step is too coarse.


---

## The ACM and Padding

The Allowed Collision Matrix and link padding are the two primary levers for tuning what the planning scene treats as a collision. The ACM scopes which link pairs FCL checks at all; padding inflates every link's geometry before any check is performed. Both are configured statically in the SRDF and are consumed directly by the underlying collision engine.

Their mechanics, including how the ACM is consulted by `CollisionEnvFCL::checkSelfCollisionHelper`, how padding is applied via `updatedPaddingOrScaling()`, and the specific values used in MARS, are covered in the Collision Avoidance post.

![Padding](/mars_ned2/assets/images/padding.png){: .align-center}
---

## The Planning Scene Is a Model

The core insight: the planning scene is a model. All models are wrong; some are useful. The utility of the MARS planning scene model is that it provides a conservative, reproducible, computationally tractable basis for collision-free trajectory generation. Its accuracy is bounded by the quality of the robot's URDF, the precision of obstacle placement, and the frequency of state updates.

In practice, the 5–7 cm link padding applied in MARS produces false negatives: 14 out of 100 test configurations were rejected by the planner because padded geometries overlapped, even though the physical links would not have touched. Zero unplanned physical collisions occurred across those 100 tests. The margin appears appropriate; whether it is more conservative than necessary is a calibration question for future work.

Treating the planning scene as ground truth, assuming that collision-free in the model means collision-free in the world, is the error. The padding exists precisely because that assumption is not made.
