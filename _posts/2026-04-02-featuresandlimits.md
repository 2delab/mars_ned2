---
layout: single
title: "What MARS Can Do and What It Cannot: A Practical Summary"
date: 2026-04-02
classes: wide
author_profile: false
---

## What It Does

### Three Coordination Modes

MARS provides three selectable modes at runtime, each with different guarantees:

**Asynchronous mode** — both arms plan and execute independently, 6-DOF each. No cross-arm collision checking. This is the mode that delivers the headline result: 28.6% cycle time reduction in parallel pick-and-place compared to sequential single-arm execution. Use this when the task naturally partitions into separate left and right work zones.

**Hybrid mode** — both arms plan together as a 12-DOF group with full collision awareness, then execute on separate per-arm controllers. This is the sweet spot for tasks that need collision checking but do not require lockstep timing. The planning is slower (12-DOF instead of 6+6), but the collision safety is guaranteed at the planning stage, not guessed at execution time.

**Synchronous mode** — both arms plan and execute together, 12-DOF lockstep. This is validated in simulation only; physical execution has a ~20–50 ms sequential start offset. Use this for tasks requiring precise inter-arm positioning, such as coordinated grasp handoff or simultaneous assembly.

Each mode maps cleanly to a task class. Choose the mode based on whether your task requires collision awareness and whether the arms must arrive at waypoints simultaneously.

### Planning-Time Collision Safety

Across 86 executed trajectories, zero unplanned collisions occurred. 14 trajectories were correctly rejected by the planner as unsafe. This is not a lucky streak — it is a guarantee. MARS enforces collision safety at the planning stage through FCL distance computation with per-link padding, not through runtime contact detection.

The planning rejection rate is not uniform: it is zero for most configurations and 100% for a specific geometric region — when one arm's joint_1 is at ±50° and the other's is at 0°, which places their padded volumes at the shared workspace boundary. This is exactly what you want from a safety system: configurations far from the collision boundary plan without difficulty; configurations at the edge are rejected consistently.

### Namespace Bridging Without Overhead

The `JointStateManager` transparently aggregates two separate NED2 hardware namespaces into a unified state stream at 15 Hz. The aggregation is bidirectional: joint names are prefixed on the state path (so each arm's joint_1 is renamed to arm_1_joint_1), and prefixes are stripped before dispatch to hardware (so the planner sees a unified 12-DOF state but the vendor drivers see only their own prefixed joints).

This overhead is invisible to MoveIt2, the Robot State Publisher, and RViz2. No downstream consumer needs to know that the state came from two separate namespaces. The separation is an implementation detail, not an API constraint.

### Validated Pick-and-Place on Physical Hardware

All results are from real NED2 robots on a physical test stand, not simulation. Simulation is useful for validating the URDF and TF tree, but it hides the things that matter: ROSBridge latency, driver behaviour, joint state gaps. MARS was developed hardware-first. The simulation validation is a bonus, not the source of truth.

---

## What It Does Not Do
### Dual Cartesian Goals Require Manual IK Composition

MoveItPy's `PlanningComponent.setGoal()` API enforces a constraint: each call accepts either a single Cartesian target (PoseStamped + link) or a full robot state, but not multiple Cartesian targets. Setting two simultaneous Cartesian goals for the dual group requires manual per-arm inverse kinematics composition:

```python
robot_state.set_from_ik("arm_1", arm1_pose, "arm_1_tool_link")
robot_state.set_from_ik("arm_2", arm2_pose, "arm_2_tool_link")
dual_group.set_goal_state(robot_state=robot_state)
dual_group.plan()
```

This workaround has a failure mode: if the two independently solved IK poses compose into a self-collision (even though each pose individually avoids obstacles), or if either IK solve fails, the error surfaces only as an opaque planning failure, not an early diagnostic signal.

**The implication**: if your task uses Cartesian targets (e.g., "move the left gripper to pose X and the right gripper to pose Y simultaneously"), be prepared to handle IK failures and composition self-collisions at the planning error level. The limitation is fundamental to MoveItPy's API design; alternative implementations using raw ROS2 action clients do not escape it.

### Pilz Linear/Circular Planners Do Not Work with the Dual Group

The Pilz LIN and CIRC planners generate deterministic straight-line or circular Cartesian paths. Both require a unique end-effector (tip frame) to define the direction of motion. The dual planning group has two tip frames: `arm_1_tool_link` and `arm_2_tool_link`.

Requesting Pilz planning for the dual group returns immediate planning failure. Deterministic straight-line Cartesian planning is only available per-arm via the `arm_1` and `arm_2` groups.

**The implication**: if your task requires guaranteed Cartesian paths (e.g., precision hole insertion, deburring), you cannot use dual-group planning. You must plan single-arm synchronous sequences: move arm_1 to pose A while arm_2 waits, then move arm_2 to pose B. This is slower and less elegant than true bimanual Cartesian planning, but it is the only way to get deterministic paths on the NED2.


### No Payload Testing

All MARS validation was conducted on unloaded arms. The NED2's nominal 300 g payload capacity effectively becomes ~200–230 g after gripper weight is accounted for. The effect of inertial loading on joint accuracy, repeatability, and trajectory timing was not characterised.

Real-world deployment of NED2 systems shows 10–30% degradation from advertised specifications (Naqvi et al., 2025). Payload effects are not measured here.

**The implication**: if you plan to deploy MARS with payloads, you need to characterise the loaded system yourself. The validation results apply to unloaded manipulation only.

### NED2 Speed Ceiling Limits Reactive Use

The Niryo NED2 has three interrelated constraints:

- **Maximum TCP speed**: 468 mm/s. This is not fast for manipulation.
- **ROSBridge latency floor**: ~10 ms minimum round-trip to the hardware.
- **No holding brakes**: The arm descends under gravity on power loss, with no error recovery.

Together, these mean the system cannot support reactive replanning cycles faster than ~50 ms (network latency plus conservative compute margin). For comparison, a human grasp reaction time is ~200 ms, so this is not a blocker for collaborative tasks, but it is a blocker for dynamic responsive tasks.

**The implication**: MARS is well-suited to structured, pre-planned manipulation with defined workspaces. It is not appropriate for ad-hoc reactive tasks or high-speed continuous path applications (welding, painting, deburring).

---

## Practically

MARS delivers what it sets out to do: namespace-isolated dual-arm coordination on the NED2 with three modes and planning-time safety. The system is well-validated, the limitations are clearly mapped, and the architecture extends naturally to richer problems (three arms, dynamic obstacles, adaptive safety margins).



