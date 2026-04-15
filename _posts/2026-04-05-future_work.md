---
layout: single
title: "Future Work"
header:
  teaser: /assets/images/posts/future_work.png
date: 2026-04-05
classes: wide
author_profile: false
---

## Key opprtunities for improvement 


### Three or More Arms

The `JointStateManager` uses a list of arm namespaces that drives the subscription and prefix logic:

```python
ARM_NAMESPACES = ['arm_1', 'arm_2']  # extend to add arm_3, arm_4, ...
```

Adding a third arm to the manager is a configuration change: add `'arm_3'` to the list, and the aggregation, prefixing, and startup guard generalise automatically.

The `TrajectoryProxy` is not equally flexible. It has two named action clients (`arm_1_client`, `arm_2_client`) that are hardcoded. A third arm requires adding a third client and updating the dispatch logic; this is a code change, not a configuration change. Refactoring the proxy to take an arm namespace list at construction and build clients dynamically is the right direction but was not done for two arms because the added abstraction cost wasn't justified.

Beyond the software changes, adding a third arm requires:

- Extending the composite URDF with a third arm's kinematic chain and a new fixed joint to `world`
- Adding the third arm's namespace to the `JointStateManager` configuration
- Adding a third planning group and all cross-arm collision pairs to the SRDF
- Commissioning the physical arm at the right position and yaw relative to the shared workspace

The computational challenge is 18-DOF planning for the combined group. RRTConnect's performance at 18-DOF is an open question; it scales poorly with dimensionality in cluttered spaces. Whether the planning time remains acceptable depends on the geometry of the workspace and the required trajectory complexity. This is an empirical question that requires testing.

---

### Dynamic Obstacle Integration

The `PlanningSceneMonitor` supports occupancy map integration via the `PointCloudOctomapUpdater` plugin. Connecting a depth camera to the planning scene would allow the planner to treat unmodelled objects, such as a component placed on the workspace surface or a person's hand entering the workspace, as collision objects. The architecture supports this today; the missing pieces are:

1. A depth camera with a calibrated transform to `world` (the hand-eye calibration infrastructure already exists for the wrist camera; a fixed overhead camera would be simpler)
2. The `PointCloudOctomapUpdater` configuration in the MoveIt2 launch file pointing at the camera's point cloud topic
3. An octomap resolution choice: finer resolution (1–2 cm voxels) gives more precise obstacle representation at higher memory and update cost; coarser resolution (5 cm voxels) is faster but may over-approximate obstacle extents

The planner would then refuse trajectories that pass through occupied voxels, not just through the arm's own collision geometry. This is the path to reactive behaviour in unstructured environments.

---

### Online Replanning

MoveIt2 supports replanning from the current state when execution is interrupted. The `TrajectoryProxy` currently handles an interrupted trajectory (a `PREEMPTED` result from the hardware action server) by logging an error and returning. The replanning extension would change this to:

1. Catch `PREEMPTED` result code from `goal_handle.get_result_async()`
2. Read current joint state from `/joint_states`
3. Call `set_start_state_to_current_state()` on the relevant `PlanningComponent`
4. Call `plan()` from current state to the original goal
5. Redispatch the new trajectory via `send_goal_async()`

The latency constraint matters here. OMPL planning takes 100–500 ms for a typical MARS trajectory. A `PREEMPTED` event means the arm has stopped mid-motion. Two cases:

**Connection drop**: the arm is stationary. Replanning from current state is safe at any time. The 100–500 ms replanning window is acceptable because the arm is not moving.

**Hardware fault or collision event**: the arm has stopped because something is wrong. Replanning and redispatching immediately is the wrong response; it sends the arm back into the situation that caused the fault. The correct response is to abort, alert, and require human confirmation before resuming. These two cases require different handling in the proxy, which is why the simple "catch and replan" pattern is not sufficient.

---


### Adaptive Safety Margins

Fixed 5 cm padding is conservative and uniform across all links and all configurations. A more principled approach would compute margins dynamically:

- Higher velocity → larger margin (more Cartesian uncertainty at execution time)
- Arms close together → tighter checking at boundary links, standard checking elsewhere
- Free-space motion → standard margin; approach to shared workspace centre → larger margin

The technical barrier is MoveIt2's architecture. Link padding parameters are set at construction time when `PlanningSceneMonitor` initialises from the SRDF. They are stored in the `CollisionRobot` object which has no setter after construction; `getAllowedCollisionMatrix()` is readable but the padding values are write-once at init. Changing them at runtime has two implementation paths:

**Full rebuild**: destroy and reconstruct the `PlanningSceneMonitor` with new padding values before each planning call. This re-parses the URDF and regenerates the ACM, approximately 50–200 ms per rebuild. Acceptable for low-frequency adaptation (one rebuild per task phase) but not per-trajectory.

**Parallel proximity model**: maintain a lightweight parallel collision model alongside the standard planning scene. The parallel model uses dynamic margins computed from current arm proximity and velocity. It is used only for proximity queries near the shared zone boundary; the standard planning scene handles the full trajectory check. This avoids the rebuild cost but requires custom integration into the MoveIt2 planning pipeline, specifically a custom `PlanningSceneMonitor` subclass that routes proximity queries to the dynamic model.

Neither is a small addition. Both require MoveIt2 internals changes beyond what the current Python API exposes.

---

### Task-Adaptive Mode Selection

Currently, the coordination mode (`sync`, `async`, `hybrid`) is a user-specified parameter at task invocation. The user must know in advance whether the task requires synchronised timing or just collision safety. Getting this wrong, for example using `async` for a task where the arms approach the same workspace zone, does not produce a planning failure; it produces a physically unsafe execution because `async` mode performs no cross-arm collision checking.

Automating mode selection removes this burden and prevents the zone-crossing failure mode. The automaton would work as follows:

**Inputs** (all available at planning time without additional sensing):
- Both arms' current joint configurations from `/joint_states`
- The target joint configurations for each arm (the planning goal)
- The workspace zone boundary: the Cartesian projection of `joint_1 = 0°` for each arm, which defines the boundary between each arm's nominal zone and the shared centre region

**Decision rule**:
- Both arms' planned trajectories remain entirely within their respective home zones throughout all waypoints → `async`
- Either arm's trajectory crosses into the shared centre zone, but not simultaneously → `hybrid` (plan with `dual` group for collision awareness, execute independently)
- Both arms' trajectories enter the shared centre zone within the same time window → `sync` (plan and execute as a coordinated 12-DOF trajectory)

**Why this is bounded**: all inputs are available at planning time from the joint state topic and the URDF geometry. No additional sensing is required. The zone boundary is a static geometric constraint.

**What it doesn't solve**: the decision rule above is a spatial heuristic. It detects whether trajectories overlap geometrically, but not whether the task semantics require simultaneous arrival. Two arms approaching the shared zone at different times for independent picks do not need `sync` mode even if their trajectories geometrically overlap. Distinguishing geometric overlap from task-level synchronisation requirement needs a higher-level task representation; the arms need to know not just where they are going but why, and whether their goals are temporally coupled. That is a task planning problem, not a motion planning problem.
