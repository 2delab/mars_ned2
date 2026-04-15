---
layout: single
title: "Sync and Async Tests"
header:
  teaser: /assets/images/posts/sync_async_tests.png
date: 2026-03-23
classes: wide
author_profile: false
---

# Testing Coordination

MARS implements two coordination modes, **synchronised** and **asynchronous**, for dual-arm motion execution on physical Niryo NED2 hardware. Joint state data were logged at 15 Hz from `/arm_1/joint_states` and `/arm_2/joint_states` via ROS2 rosbag.

The architectural distinction between the two modes is fundamental: the `dual` 12-DOF planning group produces a **single shared time-parameterised trajectory** in which both arms are planned jointly and share a common motion schedule; the independent `arm_1`/`arm_2` 6-DOF groups produce **separate trajectories** with no shared clock or synchronisation constraint. This planning-time decision determines all observable execution-time behaviour.

---

## Methodology

### Test Execution Flow

Both test suites used the same execution pipeline:

```
For each test run:
  ├─ Initialise ROS2/MoveIt2 with dual-arm URDF
  ├─ Load collision objects from workspace_scene.yaml
  ├─ Set up planning component (dual or independent groups)
  ├─ For each joint configuration:
  │   ├─ Set goal state for arm_1 and arm_2 (identical goals)
  │   ├─ Request plan with appropriate planning group
  │   ├─ If planning succeeds:
  │   │   ├─ Execute trajectory via FollowJointTrajectory action
  │   │   ├─ Record joint states via rosbag at 15 Hz
  │   │   └─ Log start/end timestamps for phase analysis
  │   └─ Repeat for next configuration
  └─ End run
```

### Test Configurations

Three joint-space configurations were tested sequentially:

| Config | Joint 1 | Joint 2 | Joint 3 | Joint 4 | Joint 5 | Purpose |
|--------|---------|---------|---------|---------|---------|---------|
| Config 1 | 50° | 0° | 0° | 0° | 0° | Single-joint motion |
| Config 3 | 45° | -30° | 20° | 0° | 0° | Multi-joint motion |
| Config 5 | 10° | -25° | 15° | -20° | -50° | Full 5-joint engagement |

_**NOTE:**_
- The arm moves between these configurations for each test.
- Joint 6 excluded due to hardware sensor noise.

### Data Collection

- **Topics**: `/arm_1/joint_states` and `/arm_2/joint_states`
- **Frequency**: 15 Hz (66.7 ms per message)
- **Recorded via**: ROS2 rosbag during trajectory execution
- **Analysis tool**: `data/sync_joints2.ipynb` processes rosbag data and computes metrics

### Phase Shift Detection

For each trial, motion onset and offset are detected per arm independently:

```
For each joint (1–5):
  1. Extract arm_1 and arm_2 joint position time series
  2. Zero-reference each arm's timestamps to its own first message
  3. Find first index where |arm[t] − arm[t-1]| > 0  → motion onset
  4. Find last  index where |arm[t] − arm[t-1]| > 0  → motion offset
  5. Compute start phase shift: arm_2_onset  − arm_1_onset
  6. Compute end   phase shift: arm_2_offset − arm_1_offset
  7. Average across joints (1–5) to obtain per-trial phase shifts
```

The **start phase shift** is the signed time difference between arm_1 and arm_2 motion onset. A positive value indicates arm_2 begins later; negative indicates arm_2 begins first. The **end phase shift** applies the same logic at trajectory offset. A constant offset between the two indicates both arms execute at identical speeds; divergence indicates independent rate progression.

### Synchronisation Score

The **synchronisation score** provides a scalar measure of temporal coupling, defined as:

```
sync_score = 100 × (1 − |duration_diff| / max(arm1_duration, arm2_duration))
```

where `duration_diff` is the absolute difference in execution duration between the two arms, normalised by the longer duration. A score of 100% indicates identical execution durations; lower scores reflect increasing temporal divergence.

**Interpretation thresholds:**
- **≥ 95%**: High synchronisation, consistent with shared time-parameterised trajectory execution
- **85–95%**: Moderate divergence, with detectable but bounded timing differences
- **< 85%**: Significant divergence, consistent with independent execution under separate controllers

---

## Synchronised Motion

**Planning Group**: `dual` (12-DOF unified)  
**Test Runs**: 10 trials  
**Goal**: J1 = 10°, J2 = −25°, J3 = 15°, J4 = −20°, J5 = −50°  
**Valid Trials**: 9 (test_6 excluded due to incomplete rosbag recording)

### Video Demonstration

<video width="100%" controls autoplay muted loop>
  <source src="/mars_ned2/assets/videos/test_sync.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>

### Results

The `dual` planning group produces a single time-parameterised trajectory in which both arms share an identical motion schedule. At execution time, the `TrajectoryProxy` dispatches each arm's goal sequentially to its respective hardware controller. The measured phase shifts reflect this dispatch sequencing combined with network-level timing variability.

![sync](/mars_ned2/assets/images/sync_phase.png){: .align-center}

| Test | Arm 1 (s) | Arm 2 (s) | Diff (s) | Start Shift (s) | End Shift (s) | Sync Score (%) |
|------|----------:|----------:|--------:|----------------:|---------------:|---------------:|
| test_0 | 5.32 | 5.19 | 0.13 | -1.12 | -1.25 | 97.49 |
| test_1 | 5.38 | 5.42 | 0.04 | +0.36 | +0.39 | 99.32 |
| test_2 | 5.23 | 5.48 | 0.25 | +1.20 | +1.44 | 95.48 |
| test_3 | 5.44 | 5.43 | 0.01 | +1.54 | +1.53 | 99.89 |
| test_4 | 5.36 | 5.45 | 0.10 | +0.04 | +0.14 | 98.24 |
| test_5 | 5.29 | 5.28 | 0.01 | +1.33 | +1.32 | 99.80 |
| test_7 | 5.52 | 5.39 | 0.13 | -1.59 | -1.72 | 97.63 |
| test_8 | 5.52 | 5.56 | 0.04 | +1.62 | +1.66 | 99.23 |
| test_9 | 5.42 | 5.37 | 0.05 | -1.16 | -1.21 | 99.15 |

**Duration**: Arm execution times differ by a maximum of 0.25 s (mean duration ~5.39 s; max relative deviation 4.7%), a direct consequence of shared time parameterisation, as both arms receive the same velocity profile from the `dual` planner.

**Phase shift**: The mean start phase shift is +0.24 s (std dev 1.27 s; range −1.59 s to +1.62 s). The sign and magnitude vary across trials, reflecting non-deterministic network dispatch timing. Critically, within any given trial the shift is **constant**: start and end phase shifts agree closely (e.g., test_3: +1.54 s / +1.53 s; test_7: −1.59 s / −1.72 s), confirming both arms execute at identical speeds once motion begins. The offset is set at dispatch time and does not accumulate.

**Sync score**: All 9 trials score ≥ 95.48% (mean 98.47% ± 1.42%), consistent with the ≥ 95% threshold for shared trajectory execution. The low standard deviation (1.42%) reflects the high consistency of the shared planner across trials.

---

## Asynchronous Motion

**Planning Groups**: `arm_1` (6-DOF) + `arm_2` (6-DOF) parallel  
**Test Runs**: 10 trials  
**Goal**: J1 = 50°, J2 = 0°, J3 = 0°, J4 = 0°, J5 = 0°  
**Valid Trials**: 9 (test_6 excluded)  
**Execution**: Independent action clients running in parallel threads (no synchronisation)

### Video Demonstration

<video width="100%" controls autoplay muted loop>
  <source src="/mars_ned2/assets/videos/test_aync.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>

**Observe**: even though the motion **looks synchronised**, further quantitative investigation reveals its decoupled nature.

### Results

Under asynchronous execution, each arm's trajectory is independently time-parameterised and dispatched through a separate 6-DOF planning group and action client. Phase shifts and duration differences therefore reflect **independent controller response times and network dispatch variability** rather than a constant trajectory offset.

![async](/mars_ned2/assets/images/async_phase.png){: .align-center}


| Test | Arm 1 (s) | Arm 2 (s) | Diff (s) | Start Shift (s) | End Shift (s) | Sync Score (%) |
|------|----------:|----------:|--------:|----------------:|---------------:|---------------:|
| test_0 | 3.24 | 2.02 | 1.22 | +1.78 | +0.56 | 62.29 |
| test_1 | 1.60 | 2.50 | 0.90 | +2.12 | +3.02 | 63.89 |
| test_2 | 1.69 | 1.53 | 0.15 | -0.81 | -0.96 | 90.85 |
| test_3 | 1.94 | 1.55 | 0.39 | -1.26 | -1.65 | 80.01 |
| test_4 | 2.16 | 1.48 | 0.68 | -0.98 | -1.66 | 68.61 |
| test_5 | 1.92 | 1.58 | 0.34 | +2.15 | +1.81 | 82.27 |
| test_7 | 1.52 | 1.56 | 0.04 | +1.65 | +1.68 | 97.58 |
| test_8 | 1.70 | 2.02 | 0.32 | +0.79 | +1.11 | 84.23 |
| test_9 | 1.85 | 2.18 | 0.33 | +1.18 | +1.51 | 84.84 |

**Duration**: Execution durations are substantially shorter than synchronised mode (Arm 1 mean 1.96 s ± 0.52 s; Arm 2 mean 1.82 s ± 0.37 s), reflecting the simpler single-joint goal (J1 = 50° only). Duration differences range from 0.04 s to 1.22 s (std dev 0.36 s), a 4.5× increase over synchronised mode (std dev 0.08 s), and vary substantially across trials.

**Phase shift**: Start and end phase shifts **diverge within individual trials**, indicating the two arms do not progress at the same rate. For example, test_1 shows +2.12 s at start and +3.02 s at end; test_0 shows +1.78 s at start and +0.56 s at end. This intra-trial divergence is structurally absent in synchronised mode and constitutes the clearest per-trial signature of independent execution. Mean start shift is +0.74 s (std dev 1.39 s); mean end shift is +0.60 s (std dev 1.67 s).

**Sync score**: Scores range from 62.29% to 97.58% (mean 79.40% ± 12.11%). Six of nine trials fall below the 85% threshold for significant divergence. The 12.11% standard deviation, compared to 1.42% for synchronised mode, reflects the high trial-to-trial variability inherent to independent execution: each arm's controller responds to its own trajectory without reference to the other.

---

## Comparison

Both test configurations command identical joint-space goals for each arm; both arms arrive at the same final configuration. Visual similarity is therefore expected, since **goal equivalence does not imply execution coupling**. The distinction lies in how each arm gets there.

| Metric | Synchronised | Asynchronous |
|--------|:------------:|:------------:|
| Planning group | `dual` (12-DOF) | `arm_1` + `arm_2` (6-DOF each) |
| Mean execution duration | ~5.39 s | ~1.9 s |
| Duration diff std dev | 0.08 s | 0.36 s |
| Mean start shift | +0.24 s | +0.74 s |
| Mean end shift | +0.26 s | +0.60 s |
| Intra-trial shift consistency | constant | diverges |
| Mean sync score | 98.47% ± 1.42% | 79.40% ± 12.11% |

In synchronised mode, the shared trajectory enforces a common execution rate. Any dispatch-time offset is preserved unchanged through to trajectory end, so start and end shifts agree and sync scores cluster tightly above 95%. In asynchronous mode, each arm computes its own time parameterisation and executes without reference to the other. Start and end shifts diverge within trials, duration differences vary substantially across trials, and sync scores distribute widely below 85%. These are the quantitative signatures of two distinct coordination architectures.


![async](/mars_ned2/assets/images/sync_task.png){: .align-center}
![async](/mars_ned2/assets/images/async_task.png){: .align-center}

---

## Practical Discussion

The primary utility of synchronised mode is **collision-safe coordinated execution in shared workspace**. Because the `dual` 12-DOF planner plans both arms jointly, it is aware of each arm's position at every timestep of the trajectory. This guarantees that the computed path is collision-free not only for each arm individually but for the pair operating simultaneously. The constant intra-trial phase shift observed in the data, with start and end shifts agreeing to within fractions of a second across all 9 trials, confirms that once dispatched, both arms remain locked to the same trajectory clock regardless of network timing. This property is a prerequisite for tasks involving shared objects, bimanual grasping, coordinated assembly, or any scenario where the arms operate in proximity: if one arm arrived early under independent execution, the other would still be moving through potentially conflicting workspace.

Asynchronous mode is appropriate when the arms operate on **spatially independent subtasks** with no shared object or workspace overlap. In these cases, the 0.04–1.22 s duration variability observed across trials is operationally irrelevant; each arm simply needs to reach its goal, and the order or timing of completion carries no consequence. The lower computational and communication overhead of independent 6-DOF planning also makes asynchronous mode preferable where task structure permits it. These tests validate that MARS exposes both coordination architectures through a consistent planning interface, allowing mode selection to be driven by task geometry rather than system capability.

Two hardware-level constraints are worth noting. First, even in synchronised mode the mean start phase shift of +0.24 s indicates a non-trivial dispatch offset attributable to sequential TCP/IP goal dispatch and controller scheduling latency. Although this offset is constant within trials and therefore does not compromise trajectory tracking, it represents a lower bound on temporal precision achievable at the hardware layer and should be accounted for in time-critical task design. Second, the synchronised sync score ceiling of 95.48–99.89%, while high, confirms that perfect temporal alignment is not achieved in practice. For applications requiring sub-100 ms arm synchronisation, additional hardware-level timestamping or a hardware synchronisation signal would be necessary beyond what the current ROS2/MoveIt2 software stack provides.
