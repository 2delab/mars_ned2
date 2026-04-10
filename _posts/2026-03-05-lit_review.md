---
layout: single
title: "Literature Review: Multi-Arm Coordination in Robotics"
header:
  teaser: /assets/images/posts/lit_review.png
date: 2026-03-05
classes: wide
author_profile: false
---

# The Market and Research approoaches to MARS

## Industrial Baselines: Proprietary Control

### ABB YuMi (IRB 14000)

ABB's dual-arm collaborative robot, introduced in 2015, is an exellent standard for bimanual coordination in production and assembly. It features two 7-DOF arms mounted on a shared torso with a 559 mm reach per arm. It is explicitly designed for human coexistence — no safety fencing required.

**Coordination approach:** Both arms are managed by a single IRC5 controller. The controller maintains a unified joint state across all 14 DOF in real time. Trajectory planning, collision checking, and execution all happen within the same hardware unit. Neither arm is aware of the other independently, the controller is the only point of coordination.

**The benefits:** From a coordination perspective, YuMi solves the problem at the hardware level. Collision checking is native and runs on-chip with microsecond latency. Trajectory time-parameterisation across both arms is built in. Synchronised and asynchronous execution modes are both supported out of the box, with no software integration required.

**The cost:** YuMi's coordination architecture is not programmable via standard ROS interfaces. You cannot inspect the joint state fusion logic, modify the collision model, or extend the planner. The entire coordination stack is proprietary. If you need a third arm, a different hardware brand, or custom planning behaviour, you are outside what the system supports.

![ABB YuMi](/mars_ned2/assets/images/ABB_YuMi.png){: .align-center}


### Yaskawa Motoman SDA Series
The Motoman SDA (Slim Dual-Arm) series (SDA5, SDA10, SDA20) covers a 5–20 kg payload range per arm across three variants. Each model pairs two 7-DOF arms on a shared base and torso, with the SDA10 being the most commonly deployed. with a reach of approximately 910 mm on the SDA10. Unlike YuMi, these are industrial arms, not collaborative — they operate at higher speed and payload behind safety fencing.

**Coordination approach:** A single DX200 or YRC1000 controller manages both arms. The controller runs Yaskawa's proprietary INFORM motion language internally, handling trajectory planning, execution timing, and inter-arm collision avoidance as a unified process. Both arms share the same clock, enabling precise temporal synchronisation across the 14-DOF configuration space.

**The benefits:** The SDA series handles industrial tasks like welding, machine tending, and heavy assembly with both arms moving simultaneously with a central timing control. The shared controller eliminates the latency and jitter that would arise from two independent controllers trying to synchronise over a network. Planning is fast because the controller has direct hardware access to both arms' states.

**The cost:** Same as YuMi but more acute. The system is fully closed: proprietary controller, proprietary software, no ROS interface. For research purposes, the SDA series is effectively a black box. You can send high-level task commands via Yaskawa's API, but the coordination logic beneath is inaccessible. It also does not translate as patterns learned from the SDA cannot be applied to non-Yaskawa hardware.

![SDA](/mars_ned2/assets/images/SDA.png){: .align-center}


**The industrial pattern:** coordination works when both arms are managed by the same hardware controller. This provides:
- Microsecond-level synchronisation
- Native collision checking with no communication overhead
- Joint-space planning that is globally aware of both arms
- Reliable execution without latency-induced drift
**The cost:** this architecture does not scale to heterogeneous hardware. You cannot add a third arm from a different brand. You cannot run your own planning algorithm. You cannot inspect or modify the coordination logic. And you cannot reproduce it on a commodity arm in a research lab.



## Open-Source and Research Approaches

Recent systems attempt to solve multi-arm coordination in open software. None solves it completely.


### Fabrica (Tian et al., MIT CSAIL / Autodesk, CoRL 2025)

**What it is:** An integrated planning + learning framework for dual-arm assembly of multi-part objects. Won the best paper award at CoRL 2025.

**Coordination approach:** Fabrica uses a unified world model and dual-arm task decomposition. Assembly tasks are decomposed into primitive operations (grasping, insertion, hand-off), and a learning module predicts which arm should execute which sub-task. The planner then solves for both arms jointly.

**Strengths:**
- Novel learning + planning integration
- Solves real-world multi-part assembly (demonstrated on Franka Emika arms)
- Open source on GitHub (yunshengtian/Fabrica)

**Limitations:**
- **Planning speed:** 15–45 seconds per plan. Too slow for reactive tasks.
- **Hardware scope:** Demonstrated only on Franka Emika arms. Not hardware-agnostic.
- **Asynchronous execution:** Not supported. The system assumes synchronised dual-arm operation.
- **Scalability:** Single unified URDF with 12 DOF. Spatial reasoning is limited by the planner's ability to handle high-dimensional spaces.

**Position in the landscape:** Fabrica solves the *learning to coordinate* problem but does not solve the *coordination infrastructure* problem. It is a demonstration system, not a reusable framework.

### Stoop et al. (2023): Asynchronous Trajectory Execution in MoveIt2

**What it is:** A method presented at the IROS 2023 workshop (Planning and Robotics) by Pascal Stoop and colleagues at OST Rapperswil and ZHAW Winterthur, Switzerland.

**Coordination approach:** Stoop et al. directly address the asynchronous execution problem in MoveIt2. They propose:
1. Planning two arms independently using separate 6-DOF planning groups
2. A pre-dispatch collision check that verifies each trajectory against the current robot state before sending it to hardware
3. Separate action server calls for each arm, allowing independent motion

**Strengths:**
- Directly solves async execution in MoveIt2
- Pre-dispatch collision check (critical safety mechanism)
- Hardware-agnostic (works with any arm that has a FollowJointTrajectory action server)

**Limitations:**
- **No synchronisation mode:** The paper focuses on asynchronous execution only
- **Limited planning scope:** No inter-arm collision checking during planning (asynchronous assumes spatial independence)
- **Scope:** Presented as an extended abstract, not a full system implementation

**Position in the landscape:** Stoop et al. is complementary to MARS — it solves async execution cleanly but does not address synchronisation or state aggregation.


## The ROS2 Coordination Gap

The community is aware of the gap. Evidence:

**GitHub Issues:**
- MoveIt2 #2744 (March 2024): "Controlling two Robots simultaneously via MoveIt" — closed as `not_planned`
- MoveIt2 #3037 (October 2024): "Move multiple arms simultaneously" — no standard solution offered, closed with recommendation to "explore custom solutions"

**ROS Answers:**
- Multiple unanswered threads (2022–2023) asking how to structure TF trees and namespaces for multi-arm systems
- A canonical question on multi-robot namespace design has no accepted answer

**Why no standard?** MoveIt2 is designed for single-robot planning. The core data structures (RobotState, PlanningScene) assume one arm. Multi-arm coordination requires:
1. Aggregating joint states from independent sources
2. Building a unified RobotState
3. Solving jointly for all DOF
4. Dispatching trajectories back to independent controllers

Each of these steps has design choices, and no single choice is optimal for all use cases.

---

## Motion Planning for Multi-Arm Systems

MoveIt2 uses OMPL (Open Motion Planning Library) for trajectory generation. OMPL is a sampling-based planner — it works by randomly sampling the configuration space and building a roadmap of collision-free paths.

**For a single 6-DOF arm:**
- Configuration space: 6 dimensions
- Typical planning time: 0.5–5 seconds
- Collision checks: ~1000–5000 samples

**For two 6-DOF arms (12-DOF unified space):**
- Configuration space: 12 dimensions
- Typical planning time: 5–30 seconds (longer due to higher dimensionality)
- Collision checks: ~10,000–50,000 samples (exponentially more due to link-pair explosion)

The computation is not just 2× slower. The curse of dimensionality means planning time scales super-linearly with DOF.

**Collision checking:** MoveIt2 uses FCL (Flexible Collision Library) for distance computation. For inter-arm collision checking:
- Single arm: ~20 link-pair checks per configuration sample
- Dual arm: ~200 link-pair checks per configuration sample (12 DOF, 2 arms, 6 links each)

This is why industrial systems use proprietary planners — they can apply domain knowledge to prune the search space. OMPL, being general-purpose, does not have that luxury.

**Related work:** Zhang et al. (2023) in *Sensors* propose real-time kinematically synchronous planning using self-organizing competitive neural networks to avoid high-dimensional search. This is an alternative approach, not yet integrated into ROS2 frameworks.

---

## Temporal Synchronisation

When two arms must move in tandem — for example, holding opposite ends of an object — they must stay synchronised. **Synchronisation is a temporal problem, not just a spatial one.**

### Pearson Correlation as a Metric

The MARS project (and the academic literature on bimanual coordination) uses the Pearson product-moment correlation coefficient *r* as a synchronisation metric:

$$r = \frac{\sum_{t} (\theta_1(t) - \bar{\theta}_1)(\theta_2(t) - \bar{\theta}_2)}{\sqrt{\sum_{t} (\theta_1(t) - \bar{\theta}_1)^2} \sqrt{\sum_{t} (\theta_2(t) - \bar{\theta}_2)^2}}$$

Where $\theta_1$ and $\theta_2$ are the joint trajectories of arm 1 and arm 2.

- *r* = 1.0: perfect synchronisation (arms move identically)
- *r* > 0.8: strong synchronisation (acceptable for most tasks)
- *r* < 0.3: weak synchronisation (arms are independent)

**Why Pearson r?** It is invariant to scaling (joint speed differences) and offset (different absolute positions). It captures whether the *pattern* of motion is similar, which is what matters for coordination.

### Trajectory Time-Parameterisation

A critical requirement for synchronisation is **time-parameterisation:** both trajectories must have the same duration and follow a shared time schedule.

In MoveIt2, this is handled by `robot_trajectory::RobotTrajectory`, which stores:
- Joint positions for each waypoint
- Time duration for each segment
- Interpolated velocity and acceleration

For dual-arm synchronisation:
1. Generate independent 6-DOF trajectories for each arm
2. Compute the maximum duration across both
3. Time-scale both trajectories to match that duration
4. Dispatch with aligned timing to both controllers

The latency introduced by network communication (20–50 ms over TCP/IP for Ned2) can cause drift unless both controllers receive their commands with low jitter.

---

## Hardware Limitations and Architecture Implications

A critical but often overlooked factor: **hardware limitations determine architectural choices.**

### Naqvi et al. (2025) — Advertised vs Operational Performance

Recent research in *Nature Scientific Reports* (Naqvi et al., 2025) quantifies the gap between advertised and real-world performance in robotic systems, including the Niryo Ned2:

- **Advertised specs** (manufacturer's controlled testing): ±0.5 mm repeatability
- **Operational specs** (real-world deployment): 10–30% degradation typical
- **Environmental factors** add 5–15% additional variance
- **Cumulative wear** further degrades accuracy over time

**Why this matters for coordination:** If the actual positioning error is 0.5–1.5 mm (not the advertised ±0.5 mm), your collision padding must reflect real-world performance, not published specs. A 5 cm safety margin per link becomes necessary.

### Latency and Control Architecture

Ned2's ROS2 driver communicates via ROS Bridge (WebSocket), introducing 20–50 ms latency per command.

**At this latency:**
- Real-time reactive control is not feasible (50 ms is too slow for feedback control)
- Planning-time safety guarantees are mandatory (you cannot rely on runtime collision detection)
- Both arms must receive their trajectory waypoints at nearly the same moment to avoid temporal drift

This is why MARS uses **planning-time collision checking** (not runtime detection) and **trajectory proxying** (synchronized dispatch). Hardware latency drove the architecture.

---

## Comparative Summary: Systems and Capabilities

| System | Planning Speed | Sync Exec | Async Exec | Openness | HW Flexibility | Notes |
|--------|---|---|---|---|---|---|
| **ABB YuMi** | < 1 s | ✓ Full | ✓ Full | Closed | YuMi only | Industrial baseline; proprietary controller |
| **Fabrica** | 15–45 s | Limited | ✗ | Partial | Franka only | CoRL 2025; learning + planning; demo system |
| **MoveIt Pro** | ~5 s | ✓ Full | ✗ | Partial | Generic | Commercial; single-arm focus |
| **Stoop et al.** | — | ✗ | ✓ Full | Open | Any MoveIt2 | Academic; async only; pre-dispatch safety |


---

## What the Gap Actually Is

No prior system provides **all five** of these simultaneously:

1. **Both sync and async modes** — Most systems commit to one or the other. Fabrica is sync-only. Stoop et al. is async-only. Industrial systems support both but are proprietary.

2. **Hardware-agnostic coordination** — Works with any arm that publishes JointState and has FollowJointTrajectory. Not Franka-specific, not YuMi-specific.

3. **Open-source architecture** — Full source available, extensible, reproducible in academic settings.

4. **Joint-space planning with inter-arm collision checking** — Unified URDF, multi-group planning in MoveIt2, FCL collision checking across all link pairs.

5. **Production-ready execution** — Not a research demo. Real hardware validation. Measurable performance metrics (0 collisions, timing consistency, synchronisation quality).


MARS targets exactly this gap: the hardware-agnostic, both-modes-supported, open-source coordination layer that the community has documented as missing.


---

## References

**Primary Literature:**

1. Naqvi, M. R., Sarkar, A., Ameri, F., Elmhadhbi, L., Louge, T., & Karray, M. H. (2025). "Ontology-driven integration of advertised and operational capabilities in robots." *Nature Scientific Reports*, 15, 34326. doi: 10.1038/s41598-025-16649-3

2. Stoop, P., Ratnayake, T., & Toffetti, G. (2023). "A Method for Multi-Robot Asynchronous Trajectory Execution in MoveIt2." *IROS 2023 Workshop on Planning and Robotics*. arXiv:2310.08597

3. Tian, Y., Jacob, J., Huang, Y., Zhao, J., Gu, E., Ma, P., Zhang, A., Javid, F., Romero, B., Chitta, S., Sueda, S., & Li, H. (2025). "Fabrica: Dual-Arm Assembly of General Multi-Part Objects via Integrated Planning and Learning." *Conference on Robot Learning (CoRL) 2025*. arXiv:2506.05168

4. Zhang, H., Jin, H., Ge, M., & Zhao, J. (2023). "Real-Time Kinematically Synchronous Planning for Cooperative Manipulation of Multi-Arms Robot Using the Self-Organizing Competitive Neural Network." *Sensors*, 23(11), 5120. doi: 10.3390/s23115120

**Community Documentation:**

5. MoveIt2 GitHub Issue #2744 (March 2024): "Controlling two Robots simultaneously via MoveIt" — https://github.com/moveit/moveit2/issues/2744

6. MoveIt2 GitHub Issue #3037 (October 2024): "Move multiple arms simultaneously" — https://github.com/moveit/moveit2/issues/3037

7. ROS Answers (2022–2023): Various threads on multi-robot namespace coordination — https://answers.ros.org/

**Industry References:**

8. ABB Robotics. (2015). YuMi IRB 14000 Technical Specifications. Retrieved from ABB corporate documentation.

9. Yaskawa Motoman. (2024). SDA Series Dual-Arm Robot Specifications. Retrieved from Yaskawa corporate documentation.

10. Kawasaki Heavy Industries. (2024). duAro Collaborative Dual-Arm Robot. Retrieved from Kawasaki corporate documentation.

---

## What Comes Next

With the landscape mapped, the next posts document MARS itself: its architecture (how state aggregation solves the namespace problem), its execution model (how TrajectoryProxy enables mode switching), and its validation (how real hardware testing confirms the design).

The field is moving. Fabrica shows that learned task allocation can drive coordination. Stoop et al. shows that asynchronous execution in MoveIt2 is achievable. multipanda_ros2 shows real-time coordination at the hardware level. MARS synthesises these insights into a single, reusable, hardware-agnostic framework.

The gap is not closed — the community still lacks a standard, packaged, one-size-fits-most solution. But the building blocks now exist. The task ahead is integration.
