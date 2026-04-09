---
layout: single
title: " Trajectory Execution with MoveIt2"
date: 2026-03-12
classes: 
  - wide
author_profile: false
---

# Synchronous and Asynchronous Execution with MoveIt2

MoveIt2 does not commit to a single execution paradigm. The dual-arm moveit config supports both tightly-coupled synchronous motion and fully independent asynchronous motion, selected purely by which planning group you target. The choice is made at the point of planning. No runtime reconfiguration is required.


---

## The Two Coordination Modes

The SRDF (Semantic Robot Description Format) defines three planning groups for this system:

- `arm_1` — a 6-DOF kinematic chain for the first arm alone
- `arm_2` — a 6-DOF kinematic chain for the second arm alone
- `dual` — a 12-DOF composite group that includes both `arm_1` and `arm_2` as subgroups

Which group you plan against determines everything downstream: the dimensionality of the search space, the structure of the resulting trajectory, and how `TrajectoryExecutionManager` dispatches it to hardware. This single decision is what separates synchronous from asynchronous execution.

---

## Synchronous Execution: The Dual Planning Group

When planning against the `dual` group, MoveIt2 treats both arms as a single composite system.

### Planning in a shared joint space

The `PlanningComponent` for the `dual` group searches a 12-DOF configuration space — all six joints of `arm_1` and all six joints of `arm_2` are optimised simultaneously in a single planning call. OMPL's RRTConnect constructs bidirectional trees in this combined space, finding a path from the current 12-DOF configuration to the 12-DOF goal.

The resulting `RobotTrajectory` contains waypoints for all 12 joints with **identical timestamps**. Time parameterisation is not negotiated separately per arm — it is produced once by the planner and shared across both arms. Both arms receive the same number of waypoints, spaced at the same intervals.

### Controller dispatch

`TrajectoryExecutionManager` maps the plan to a controller group defined in `moveit_controllers.yaml`. The `dual` controller group lists both `arm_1_controller` and `arm_2_controller`. The trajectory manager dispatches the single 12-DOF trajectory to both controllers simultaneously — there is no sequential handoff.

### Inter-arm collision safety

Because the planner searches the full 12-DOF space, inter-arm collision geometry is checked continuously during planning, not at dispatch time. FCL (Flexible Collision Library) performs AABB broad-phase filtering followed by GJK narrow-phase testing at every 0.5% increment of normalised path length. A trajectory only reaches execution if it is collision-free throughout — for both arms, with respect to each other and the environment.



## Asynchronous Execution: Independent Planning Groups

When planning against `arm_1` and `arm_2` separately, MoveIt2 treats each arm as a fully independent system.

### Planning in independent joint spaces

Two `PlanningComponent` instances are created — one for `arm_1`, one for `arm_2`. Each plans in its own 6-DOF joint space. The two planning calls have no shared state: each produces its own `RobotTrajectory` with its own time parameterisation. There is no shared clock, no synchronisation point, and no dependency between the two plans.

The shared planning scene still contains both arms' geometry, so each arm plans with awareness of the other arm's position at planning time. Collision safety is preserved even in asynchronous mode. What is absent is the temporal coupling — each arm's trajectory duration is determined independently by the planner based on its own goal and path length.

### Controller dispatch

`TrajectoryExecutionManager` dispatches each trajectory to its respective controller entry in `moveit_controllers.yaml` — `arm_1_controller` for `arm_1`, `arm_2_controller` for `arm_2`. These are independent dispatch calls with no synchronisation between them.

### Concurrent execution at the ROS layer

`MoveItPy`'s internal ROS node runs on a detached background thread with a `SingleThreadedExecutor`. The `execute()` call releases the Python GIL during trajectory execution, meaning the calling thread is not blocked. Two `execute()` calls can be issued in immediate succession from the client side — both reach their respective controllers and run concurrently at the hardware level.

On the client node, a `MultiThreadedExecutor` with 8 threads allows action server callbacks for both arms to run simultaneously. There is no mutual blocking at the ROS callback layer.


---

## How MoveIt2 Enables Both

The mode switch requires no code changes to MoveIt2 itself. The following components interact to make both patterns possible:

| Component | Role in synchronous | Role in asynchronous |
|---|---|---|
| SRDF planning groups | `dual` defines a shared 12-DOF joint space | `arm_1`/`arm_2` define independent 6-DOF spaces |
| `moveit_controllers.yaml` | `dual` controller group lists both arm controllers | Single-arm controller groups each list one controller |
| `TrajectoryExecutionManager` | Dispatches one 12-DOF trajectory to both controllers | Dispatches two independent trajectories to one controller each |
| `PlanningComponent` | One instance, plans both arms together | Two instances, each plans one arm independently |
| `MoveItPy` detached executor | Executes the combined trajectory; GIL released during dispatch | Both `execute()` calls return without blocking; arms run concurrently |
| `MultiThreadedExecutor` (client) | Single action callback for the combined goal | Concurrent action callbacks for both arm goals |
| FCL collision checking | Checks inter-arm geometry during the shared 12-DOF search | Checks each arm's path against the shared scene independently |

The planning group is the only decision point. Everything downstream — trajectory structure, controller routing, execution concurrency — follows from that single choice.

---

## When to Use Each

| | Synchronous (`dual` group) | Asynchronous (`arm_1`/`arm_2` groups) |
|---|---|---|
| Best for | Coordinated assembly, tasks requiring temporal alignment between arms | Independent parallel tasks, maximising throughput |
| Inter-arm collision safety | Guaranteed at planning time within the shared 12-DOF search | Guaranteed at planning time; each arm plans against the shared scene |
| Timing coupling | Identical time parameterisation from a single planner call | Independent; each arm's duration determined by its own path |
| Throughput | One plan covers both arms; execution is coordinated | Both arms execute simultaneously; no serialisation overhead |
| Planning group | `dual` (12-DOF composite) | `arm_1` and `arm_2` (6-DOF each) |
