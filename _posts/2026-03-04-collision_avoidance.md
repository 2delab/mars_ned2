---
layout: single
title: "Collision avoidance"
header:
  teaser: /assets/images/posts/collision_avoidance.png
date: 2026-03-04
classes: 
  - wide
author_profile: false
---

# Collision aviodance in Practice

Collision avoidance in MoveIt 2 operates at planning time only. The planner produces a trajectory that was collision-free against a snapshot of the world at the moment planning ran. What happens during execution is a separate concern. Understanding this distinction is important when tracing how collision checking actually works, from the geometry library at the bottom to the trajectory executor at the top.


## FCL: The Collision Engine

MoveIt 2 delegates all geometry-versus-geometry queries to the **Flexible Collision Library (FCL)**. Every collision check in the planning pipeline, whether checking a sampled joint configuration against the world or checking two robot links against each other, eventually becomes an FCL query.

FCL operates in two phases:

**Broadphase** uses a dynamic AABB (Axis-Aligned Bounding Box) tree to rapidly eliminate object pairs that cannot possibly be in contact. Each object's bounding box is maintained in a persistent spatial data structure. When a query arrives, only pairs whose bounding boxes overlap advance to the next phase. For world objects, `CollisionEnvFCL` maintains a persistent `fcl::BroadPhaseCollisionManagerd` that is updated incrementally as objects are added or removed. For self-collision, a new manager is created per query from pre-computed per-link geometries; the link geometries are computed once at startup and stored, and only their global transforms are recomputed per query, making repeated self-collision checks cheap.

**Narrowphase** handles the pairs that survived broadphase. Depending on geometry type, FCL runs GJK/EPA (for convex shapes) or mesh-mesh intersection tests to determine whether contact exists and, if requested, where.

The result contains `collision` (bool), `distance` (closest separation between any two bodies), `contact_count`, and a contact map keyed by body-pair identifiers. Most planning queries use the default configuration  binary collision only which is the fastest path through FCL. Distance computation requires a full narrowphase pass on all surviving broadphase pairs even after a collision is found; it is not used during planning.

Two check types exist at the `CollisionEnvFCL` level:

- `checkSelfCollision(req, res, state, acm)`: robot links vs. other robot links, filtered by the Allowed Collision Matrix
- `checkRobotCollision(req, res, state, acm)`: robot links vs. world objects only; self-collision is not performed here

There is also a **continuous** variant of `checkRobotCollision` that accepts two states and checks the swept volume between them. OMPL does not call this variant by default; it uses only the discrete checker per sampled state. The implications of this are discussed in the planning section below.

---

## The Planning Scene as FCL's Input

The `PlanningScene` object owns the collision world and is the interface planners query. It wraps `CollisionEnvFCL` and combines the robot model, current joint state, world collision objects, and the Allowed Collision Matrix into a single queryable structure.

Key methods available at the Python binding level (from `planning_scene.pyi` and `planning_scene.cpp`):

| Method | What it checks |
|---|---|
| `check_collision(req, res)` | Self-collision + world, padded geometry, current state |
| `check_collision(req, res, state, acm)` | Same with an explicit state and custom ACM |
| `check_self_collision(req, res)` | Robot links vs. robot links only |
| `is_state_valid(state, group)` | Collision + kinematic constraints combined |
| `is_path_valid(trajectory, group)` | Every waypoint in a trajectory; returns indices of invalid states |

In MARS, a single `move_group` node manages the full dual-arm URDF (launched in `mars_ned2.launch.py`). Both `arm_1` and `arm_2` exist in the same planning scene and therefore the same FCL environment. There is no cross-process scene synchronisation problem; the inter-arm collision check is a native FCL query within the single scene. The static world geometry loaded at startup is a 3×3 m workspace platform box (`workspace_scene.yaml`):

```yaml
collision_objects:
  - id: "workspace_platform"
    header:
      frame_id: "world"
    primitives:
      - type: 1  # BOX primitive
        dimensions: [3.0, 3.0, 0.01]
    primitive_poses:
      - position: {x: 0.0, y: 0.0, z: -0.015}
        orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    operation: 0  # ADD
```

No sensor-driven octomap is active. All collision objects are static geometric primitives placed explicitly.

The `PlanningSceneMonitor` maintains the live scene and provides thread-safe access via `read_only` / `read_write` context managers. It receives joint states via `/joint_states`, published by `JointStateManager` at 15 Hz (`publish_frequency: 15.0` in `mars_ned2.launch.py`). This rate sets the temporal resolution of the planner's world model: at any given moment the robot configuration known to the planning scene may be up to 67 ms stale.

---

## Link Padding: Inflating Geometry Before Any FCL Query

Before FCL evaluates any pair, MoveIt inflates every link's collision geometry by its configured padding value. This is applied in `CollisionEnvFCL::updatedPaddingOrScaling()`, which reconstructs the FCL geometry objects with enlarged dimensions. Padding is not a runtime offset; it physically changes the shape handed to FCL. A padded box becomes a larger box; a padded mesh has its surface extruded outward.

The effect on collision queries: two links whose physical surfaces are 8 cm apart will report a collision if each carries 5 cm padding, because the padded shapes are 10 cm thick. The query result is "in collision" even though no physical contact would occur.

In MARS, `niryo_ned2_dual_arm.srdf` defines padding for all 22 links across both arms:

```xml
<!-- Standard arm links: 5 cm -->
<link_padding link="arm_1_base_link"     padding="0.05"/>
<link_padding link="arm_1_shoulder_link" padding="0.05"/>
<link_padding link="arm_1_arm_link"      padding="0.05"/>
<link_padding link="arm_1_elbow_link"    padding="0.05"/>
<link_padding link="arm_1_forearm_link"  padding="0.05"/>
<link_padding link="arm_1_wrist_link"    padding="0.05"/>
<link_padding link="arm_1_hand_link"     padding="0.05"/>
<!-- End-effector components: 7 cm -->
<link_padding link="arm_1_base_gripper_1" padding="0.07"/>
<link_padding link="arm_1_mors_1"         padding="0.07"/>
<link_padding link="arm_1_mors_2"         padding="0.07"/>
<link_padding link="arm_1_camera_link"    padding="0.07"/>
<!-- arm_2 carries identical values -->
```

This establishes a minimum guaranteed physical clearance between any two cross-arm links in a collision-free plan of **10 cm** (5 cm per arm). For gripper-to-gripper proximity the margin is **14 cm** (7 cm per side). The asymmetry at the end-effector reflects the higher consequence of a contact at the gripper during manipulation: a wrist contact is recoverable, whereas a gripper contact during a pick operation likely destroys the task.

The cost is false negatives: configurations where the physical links would not touch but the padded geometries overlap are rejected by the planner.  these are the intended as a conservative behaviour of a model that does not trust its own accuracy.

---

## The Allowed Collision Matrix 

Left unconstrained, FCL would check every possible link pair, including adjacent links that are permanently in contact by design and links on opposite ends of the kinematic chain that could never physically reach each other. The Allowed Collision Matrix (ACM) filters these to prevent false positives that would make planning impossible.

The ACM is a sparse symmetric matrix of (link_name, link_name) → allowed/not-allowed entries. `CollisionEnvFCL::checkSelfCollisionHelper` consults the ACM before dispatching any pair to the narrowphase. Pairs with an `ALWAYS` entry are skipped entirely.

The SRDF populates the ACM at startup. MoveIt's Setup Assistant generates `reason="Adjacent"` entries for kinematically connected links and `reason="Never"` entries for pairs it determines to be geometrically unreachable via its self-collision sampling pass. In MARS, `niryo_ned2_dual_arm.srdf` disables the following categories:

**Within each arm** (adjacent links, physically connected, always in contact):
```xml
<disable_collisions link1="arm_1_arm_link"      link2="arm_1_shoulder_link" reason="Adjacent"/>
<disable_collisions link1="arm_1_arm_link"      link2="arm_1_elbow_link"    reason="Adjacent"/>
<disable_collisions link1="arm_1_forearm_link"  link2="arm_1_wrist_link"    reason="Adjacent"/>
<!-- and so on for all adjacent pairs -->
```

**Within each arm** (geometrically unreachable pairs):
```xml
<disable_collisions link1="arm_1_arm_link" link2="arm_1_base_link" reason="Never"/>
<disable_collisions link1="arm_1_arm_link" link2="arm_1_hand_link" reason="Never"/>
```

**Between arms** (the shared mounting base):
```xml
<disable_collisions link1="arm_1_base_link" link2="arm_2_base_link" reason="Adjacent"/>
```

This last entry is the only cross-arm disabled pair. Every other combination of an `arm_1` link with an `arm_2` link remains active in the ACM. This means every inter-arm link pair is handed to FCL's narrowphase on every self-collision check during planning. With 10 arm links per side (excluding the shared base), that is 100 potential cross-arm pairs queried at every sampled state in the planning graph.

The ACM can be modified at runtime via `planning_scene.allowed_collision_matrix.set_entry(name1, name2, allowed)`. This is not used in MARS; the static SRDF configuration is treated as fixed.

---

## How OMPL Calls FCL During Planning

OMPL is not aware of FCL directly. It interacts with MoveIt through a `StateValidityChecker` interface: for every state it samples or expands toward, it asks whether that state is valid. The checker calls `PlanningScene::isStateValid()`, which calls `checkCollision()`, which dispatches to `CollisionEnvFCL`. One OMPL planning call may invoke this chain thousands of times.

The density of collision checks along path segments is controlled by `longest_valid_segment_fraction` in `ompl_planning_pipeline.yaml`:

```yaml
longest_valid_segment_fraction: 0.005
```

This parameter defines the maximum edge length, expressed as a fraction of the total joint state space diameter, that OMPL will accept without explicitly validating intermediate sub-states. A value of 0.005 means that for any edge longer than 0.5% of the state space, OMPL subdivides the edge and checks each sub-state individually. For the NED2's 6-DOF joint space, this produces approximately one collision check per 1–2 degrees of joint motion along any edge, depending on which joints are moving.

Setting this value too high means collision checks are sparse along edges: a narrow obstacle could be missed if both endpoints of an edge are collision-free but the interpolated path passes through the obstacle. Setting it too low means FCL is called far more frequently per planning attempt, increasing planning time proportionally.

At 0.005, planning time for typical MARS trajectories (home to pick pose, approximately 60–90 degrees of motion across multiple joints) involves several thousand FCL queries per planning attempt. Given FCL's broadphase culling, most of these resolve without narrowphase computation.

**What OMPL does not do**: OMPL uses only the discrete state checker, never FCL's continuous `checkRobotCollision(state1, state2)` swept-volume variant. The distinction matters: discrete checking confirms that the two endpoints and a finite set of interpolated sub-states are collision-free. It does not confirm that the continuous motion between those sub-states is collision-free. The `longest_valid_segment_fraction` parameter trades off the probability of missing a collision in the interpolated segment against planning speed. At 0.5%, combined with 5–7 cm link padding, the probability of a physical collision being missed during planning is low but not zero.



## What MoveIt Plans but Does Not Execute Safely

Once `PlanningComponent::plan()` returns a trajectory, the trajectory passes to MoveIt's execution layer. In MARS this is the `TrajectoryProxy` node (`trajectory_proxy.py`), which accepts a `FollowJointTrajectory` action goal from MoveIt and forwards it to the Niryo hardware controller:

```python
hw_goal = FollowJointTrajectory.Goal(trajectory=unprefixed_trajectory)
send_future = hw_client.send_goal_async(hw_goal, feedback_callback=feedback_callback)
```

Once the goal is accepted by the hardware controller, the trajectory executes as a **time-parameterised joint interpolation**. The Niryo controller tracks waypoints using its internal PID; MoveIt is not in the control loop. During execution, `TrajectoryProxy` checks only two things: whether a cancellation has been requested from the action client, and whether the configurable wall-clock timeout has been exceeded (`trajectory_timeout_sec: 120.0`).

```python
if goal_handle.is_cancel_requested:
    hw_goal_handle.cancel_goal_async()
    ...

elapsed = (self.get_clock().now() - start_time).nanoseconds / 1e9
if elapsed > self.traj_timeout:
    hw_goal_handle.cancel_goal_async()
    goal_handle.abort()
```

Neither check involves the planning scene or FCL. An obstacle added to the scene after the planning call completes will not cause the execution to stop. A joint state drift that puts the robot on a collision course mid-trajectory will not be detected. The planning scene continues updating at 15 Hz during execution, but nothing reads it for the purpose of execution safety.

This is a known, documented limitation of MoveIt's architecture. GitHub issue moveit/moveit#2631 identifies the root cause: the `ExecuteTrajectory` action capability bypasses `PlanExecution` and goes directly to `TrajectoryExecutionManager`, which does not include collision monitoring. Only the `move()` method on `MoveGroupInterface`, which plans and executes in a single monitored call, provides trajectory monitoring, and even this is only available via the C++ `MoveGroupInterface`, not through the `PlanningComponent` API used in MARS.

The consequence is architectural: the guarantee MoveIt provides is that **the planned trajectory was collision-free in the planning scene at planning time**. It provides no guarantee about what the physical robot encounters during execution.

---

## Summary

| Stage | Collision-free? | Mechanism |
|---|---|---|
| Sampled states during OMPL planning | Yes | FCL via `isStateValid` at every sub-state along each edge |
| Interpolated path between checked sub-states | Approximately | 0.5% segment fraction + 5–7 cm padding reduce but do not eliminate the gap |
| Trajectory during execution | No | Open-loop `FollowJointTrajectory`; planning scene not consulted |
| New obstacles after planning completes | Not handled | `TrajectoryProxy` has no scene awareness; execution continues regardless |

MoveIt 2's collision avoidance is a planning-time guarantee, not an execution-time guarantee. The FCL broadphase/narrowphase pipeline, the ACM, link padding, and `longest_valid_segment_fraction` together determine how thoroughly the planner searches for collision-free paths. None of these mechanisms are active once the trajectory leaves the planner.
