---
layout: single
title: "Project Retrospective"
header:
  teaser: /assets/images/posts/retrospective.png
date: 2026-04-06
classes: wide
author_profile: false
---

## What Was Planned and What Was Built

MARS began with a simple 12-week plan. However, there was some deviations as a result of encountering real problems that the plan did not anticipate.


## The Original 12-Week Plan

| Phase | Weeks | Planned deliverables |
|---|---|---|
| **Foundation** | 1–2 | ROS2 environment, physical hardware, Gazebo simulation |
| **Perception & Planning** | 3–4 | AprilTag vision system, 3D pose estimation, MoveIt2 dual-arm setup |
| **Single-Arm Baseline** | 5–6 | Autonomous single-arm block stacking, baseline metrics (cycle time, success rate) |
| **Coordination Framework** | 7–8 | ROS2 communication channels, task representation, conflict prevention rules |
| **Task Allocation & Execution** | 9–10 | Bidding system (distance/cost), conflict resolution, collision-free execution |
| **Evaluation & Documentation** | 11–12 | Multi-arm vs single-arm comparison, stress tests, final report |

The plan assumed a linear build: perception feeds the planner, the planner feeds the execution layer, and the coordination layer sits on top. This is the correct conceptual architecture. The problem was the build order.

---

## Planned vs Actual: Gantt Charts

### Original Plan

![Original 12-week plan](/mars_ned2/assets/images/gantt_planned.png)

### Actual Execution

![Actual execution timeline](/mars_ned2/assets/images/gantt_actual.png)

The most visible feature of the actual chart is the purple block in weeks 5–7: `JointStateManager` and `TrajectoryProxy` are the two components that do not appear anywhere in the original plan. These were architectural prerequisites without which nothing else could run on real hardware. Their emergence, and the reasons for the other two major deviations, are explained below.

---

## Deviation 1: The Middleware Layer That Was Not in the Plan

The original plan assumed MoveIt2 could talk directly to the Niryo NED2 hardware drivers. It cannot, for a structural reason that was not apparent until hardware bring-up.

The Niryo drivers publish joint states under namespace-relative topics (`/arm_1/joint_states`, `/arm_2/joint_states`) using **unprefixed** joint names (`joint_1`, `joint_2`, …). MoveIt2's planning scene requires a single `/joint_states` topic carrying all joints with **prefixed** names (`arm_1_joint_1`, `arm_2_joint_1`, …). Equally, MoveIt2 dispatches `FollowJointTrajectory` goals with prefixed names; the hardware controllers reject these because they expect unprefixed names.

There is no configuration option that resolves this. It requires purpose-built translation nodes.

Two nodes were built:

**`JointStateManager`** subscribes to both arms' hardware state streams, aggregates them with namespace prefixes, injects two MORS mounting joints absent from the hardware driver, and publishes a single combined `/joint_states` at 15 Hz. Without this, the Robot State Publisher cannot resolve the TF tree, and MoveIt2 has no knowledge of the robot's current configuration.

**`TrajectoryProxy`** sits between MoveIt2's controller manager and the hardware. It accepts prefixed trajectory goals from MoveIt2, strips the prefix from joint names, and forwards the translated goal to the hardware action server. It also handles execution monitoring, cancellation, and timeout — passing hardware error codes back to MoveIt2 correctly so the planning pipeline can distinguish between successful execution and hardware failure.

Together these two nodes consumed three weeks — weeks 5, 6, and 7 — and produced Contribution 3 of the final project: a documented, reusable architecture for integrating namespace-isolated ROS2 hardware with unified multi-arm planning. This was not in the plan because the problem was invisible until the hardware was running.

**What this taught**: build in data flow order. The correct sequence is:

```
JointStateManager  →  Robot State Publisher  →  MoveIt2  →  TrajectoryProxy  →  Hardware
```

Each component is testable against the one before it. Building the MoveIt2 configuration before the state aggregation layer meant having a complete planner with nothing to feed it — and nothing to execute against — for two weeks.

---

## Deviation 2: Perception Descoped from the Validation Pipeline

The vision system was built. Camera calibration, ArUco marker detection, and hand-eye calibration are all implemented and functional. It was excluded from the validation pipeline deliberately, for a methodological reason.

MARS is investigating a coordination architecture question: does synchronised dual-arm execution work under real hardware latency? Are collision margins sufficient? Does the state aggregation layer maintain consistency under concurrent load? These questions require **repeatable, fixed experimental conditions** so that variance in results can be attributed to the coordination mechanism, not to perception noise.

Adding a vision pipeline introduces an independent source of variance. If the arm misses a target, the cause could be an 8 mm pose estimation error from marker detection noise, lighting variation, or residual camera distortion — or it could be a coordination failure. These cannot be cleanly separated in results. For validation of timing metrics (cross-trial CV < 1%, planning overhead < 0.2% of task time), programmatic target poses are not a simplification — they are the correct experimental design.

The ROSBridge latency budget reinforces this. The ROS1→ROS2 bridge introduces 20–50 ms per command. The vision pipeline (capture → detection → transformation → planning request) adds another 100–300 ms. For coordination experiments where arm timing is measured to ±100 ms precision, this overhead is not acceptable.

The vision system is available in the repository (`vision` branch). It is the natural integration point for a future extension of MARS that includes dynamic object placement. The architecture supports it: MoveIt2 accepts Cartesian pose goals in any TF frame, and the hand-eye calibration provides the transform from camera frame to robot base frame.

---

## Deviation 3: Task Allocation Dropped

The original plan included a bidding system: each arm calculates a cost (distance, time, or configuration effort) for each available task, bids on the cheapest task, and the system assigns tasks to the winning arm. This is a commonly described approach in multi-robot literature.

Distance-based task allocation for two robots with a fixed task set and known positions is a tractable special case of the multi-robot task allocation (MRTA) problem. The two-robot implementation requires the integration of: collision between allocation and coordination, replanning when a task fails mid-execution, and deadlock prevention when both arms bid on adjacent tasks.

This is not a small component to add as a side quest. It is a research project in itself.

More importantly, the project's contribution is in **coordination architecture** i.e. how two arms share a planning scene, execute trajectories safely in parallel, and maintain deterministic timing. Task allocation is the layer above that. Implementing a well-validated coordination layer with a simple deterministic task assignment (spatial zone partitioning: arm 1 operates left of centre, arm 2 operates right of centre) is a cleaner scope than implementing a partial allocation system whose correctness cannot be formally validated within the project's time constraints.

The zone partitioning approach was explored as a convention rather than enforced in the API which i've added as a known limitation (the system accepts any target pose and plans without checking assignment). A runtime enforcement layer is listed as a specific future work item.

---

## What the Scope Changes Produced

The final project is focused and more internally consistent than the original plan would have produced.

The perception descoping produced cleaner validation data. The timing results (CV < 1%, Phase 3 CV = 0%) are credible because the only variable in the experiment is the coordination mechanism. With vision in the loop, those results would be confounded.

Dropping task allocation produced a tighter research question. The four contributions of the final project are all in the coordination and planning architecture:

1. Multi-mode coordination framework (synchronous, asynchronous, hybrid) with dynamic mode selection
2. Integrated planning-time collision avoidance validated on real hardware (0 collisions across 86 trajectories)
3. Namespace-aggregated state management architecture — a documented, reusable pattern for ROS2 multi-arm systems
4. End-to-end hardware validation on Niryo NED2 with quantitative throughput and repeatability results

The middleware layer (Contribution 3) emerged from a real problem and is arguably the most practically useful contribution. Every team integrating a namespace-isolated dual-arm system into MoveIt2 will encounter exactly the same namespace translation requirement. 

---

## The Timeline in Summary

| Period | What actually happened |
|---|---|
| **Weeks 1–2** | ROS2 environment, URDF, hardware connections established |
| **Week 3** | Hardware bring-up issues: ROSBridge connection drops under load; Gazebo simulation to validate URDF only |
| **Weeks 3–5** | MoveIt2 configuration extended; vision system built and tested |
| **Weeks 5–7** | JointStateManager and TrajectoryProxy built |
| **Week 6** | Vision descoped from validation pipeline; decision documented |
| **Weeks 7–9** | Single-arm baseline completed; multi-arm coordination framework built |
| **Week 7** | Task allocation bidding system scoped and dropped |
| **Weeks 9–10** | Synchronous and asynchronous execution modes implemented and tested |
| **Weeks 10–11** | Collision avoidance validation: 100 test configurations, 0 hardware collisions |
| **Weeks 11–12** | Pick-and-place throughput validation: 28.6% cycle time reduction vs single-arm baseline |

The original plan compressed hardware integration and architecture into two weeks. In practice, hardware integration — specifically the namespace translation problem — took three weeks and produced the middleware layer. Everything downstream of that was delayed by one to two weeks but ultimately delivered.

---

## What Would Not Change

The architectural decisions that held:

- **MoveItPy over C++**: Python bindings provided faster iteration for the coordination logic without sacrificing planning performance.
- **Unified URDF over separate planners**: A single composite robot model gives MoveIt2 full visibility of both arms in one planning scene, enabling planning-time inter-arm collision checking. Separate planners cannot guarantee this.
- **Planning-time safety over runtime detection**: Planning-time collision guarantees are formal; runtime detection is reactive. For a shared-workspace system, the cost of a false negative at planning time (one fewer valid pose) is acceptable; the cost of a false positive at execution time (hardware collision) is not.
- **Hardware-first validation over simulation-only claims**: The ROSBridge latency issues, the namespace translation problem, and the joint_5 accuracy variance on arm_1 are all invisible in simulation. The results are credible because they were obtained on the hardware they describe.

---

## What Would Change

These are the decisions that, with hindsight, would be made differently.

**Build the JointStateManager first.** It is the foundation of the data flow. The current build order put two weeks of MoveIt2 configuration before the state aggregation layer existed, which meant the planner had nothing to consume for two weeks.

**Calibrate the collision padding from measurement, not estimation.** The 5 cm per-link padding was set conservatively at the start and never revisited. The 14 planning failures in the collision tests are configurations that are probably physically safe but inside the safety margin. A measurement session (positional error at maximum velocity × ROSBridge latency distribution → Cartesian deviation estimate) would have produced a tighter, defensible number. A 3 cm padding would likely reduce false negatives without compromising safety, given the NED2's ±0.5 mm repeatability.

**Enforce zone assignments in the API.** The workspace zone convention for asynchronous mode (arm 1: left of joint_1 = 0°, arm 2: right) is documented but not validated at the API boundary. The system plans any target pose regardless of zone. A zone check at the task level — raise a warning when a target is outside the arm's assigned zone — would surface configuration errors before they reach the planner.

**More trials for the synchronisation tests.** 10 repeated runs is sufficient for the reported metrics, but the confidence intervals are wide. 30 runs (approximately 2 additional hours of hardware time) would have produced cleaner statistical claims on the cross-trial timing CV.
