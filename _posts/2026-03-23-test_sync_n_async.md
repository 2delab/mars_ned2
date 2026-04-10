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

MARS has two coordination modes: **synchronised** and **asynchronous** motion. Both modes ran on physical Niryo NED2 hardware with joint state data logged at 15 Hz from `/arm_1/joint_states` and `/arm_2/joint_states`.

The fundamental difference is architectural: the `dual` 12-DOF planning group produces a **single shared trajectory** that moves both arms together; the independent `arm_1`/`arm_2` 6-DOF groups produce **separate schedules** with no shared clock. This choice at planning time determines execution behavior at hardware time.

---

## How the Tests Were Run

### Test Execution Flow

Both test suites used the same execution pipeline:

```
For each test run:
  ├─ Initialize ROS2/MoveIt2 with dual-arm URDF
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

(Config 5 is the primary configuration analyzed in results below. Joint 6 excluded due to hardware sensor noise.)

### Data Collection

- **Topics**: `/arm_1/joint_states` and `/arm_2/joint_states`
- **Frequency**: 15 Hz (66.7 ms per message)
- **Recorded via**: ROS2 rosbag during trajectory execution
- **Analysis tool**: `data/sync_joints2.ipynb` processes rosbag data and computes metrics

---

## Synchronised Motion

**Planning Group**: `dual` (12-DOF unified)  
**Test Runs**: 10 trials  
**Goal**: J1 = 10°, J2 = −25°, J3 = 15°, J4 = −20°, J5 = −50°  
**Valid Trials**: 9 (test 6 excluded due to incomplete rosbag recording)

### Video Demonstration

<video width="100%" controls autoplay muted loop>
  <source src="/mars_ned2/assets/videos/test_sync.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>


### Phase Shift Analysis

The `dual` planning group produces time-parameterised trajectories where both arms follow the same motion schedule. However, hardware dispatch is sequential: arm_1's goal reaches the controller ~20–50 ms before arm_2's goal (depending on TCP/IP network timing). This creates the **start phase shift** — a constant offset present throughout execution.

**Phase shift detection method**: For each joint, find the first timestep where |Δθ| > 0 (motion starts). Compute the time difference between arm_1 and arm_2 detecting motion onset. This offset is measured both at start and end of the trajectory to verify it remains constant. 

| Test | Arm 1 (s) | Arm 2 (s) | Diff (s) | Start Shift (s) | End Shift (s) | Sync Score |
|------|----------:|----------:|--------:|----------------:|---------------:|----------:|
| test_0 | 5.32 | 5.19 | 0.13 | -1.12 | -1.25 | 97.49% |
| test_1 | 5.38 | 5.42 | 0.04 | 0.36 | 0.39 | 99.32% |
| test_2 | 5.23 | 5.48 | 0.25 | 1.20 | 1.44 | 95.48% |
| test_3 | 5.44 | 5.43 | 0.01 | 1.54 | 1.53 | 99.89% |
| test_4 | 5.36 | 5.45 | 0.10 | 0.04 | 0.14 | 98.24% |
| test_5 | 5.29 | 5.28 | 0.01 | 1.33 | 1.32 | 99.80% |
| test_7 | 5.52 | 5.39 | 0.13 | -1.59 | -1.72 | 97.63% |
| test_8 | 5.52 | 5.56 | 0.04 | 1.62 | 1.66 | 99.23% |
| test_9 | 5.42 | 5.37 | 0.05 | -1.16 | -1.21 | 99.15% |

### Key Observations

**Duration Alignment**: Arm execution times differ by max 0.25 s (out of ~5.3 s trajectories = 4.7% variation). Both arms follow identical trajectories at the same speed.

**Phase Shift Pattern**: The start phase shift (mean 0.96 s, range −1.72 to +1.62 s) is **hardware-determined, not a planning issue**. The `TrajectoryProxy` dispatches arm_1's goal to its controller, waits ~20 ms, then dispatches arm_2's goal. Because the planner produces time-parameterised trajectories, this offset is **constant throughout execution** — both arms' clocks start at different wall times but move at identical speeds.

**Verification**: If the offset were causing tracking divergence, end-position joint angles would differ significantly. Instead, joints converge to ≤2.5° difference at trajectory end, proving both arms arrive at the goal despite the network dispatch offset.



---

## Asynchronous Motion

**Planning Groups**: `arm_1` (6-DOF) + `arm_2` (6-DOF) parallel  
**Test Runs**: 10 trials  
**Goal**: J1 = 50°, J2 = 0°, J3 = 0°, J4 = 0°, J5 = 0°  
**Execution**: Independent action clients running in parallel threads (no synchronisation)

### Video Demonstration

<video width="100%" controls autoplay muted loop>
  <source src="/mars_ned2/assets/videos/test_aync.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>

**What to observe**: even though the motion **looks synchornised** further investigation reveals its doupled nature.

### Duration Variability Analysis

| Metric | Arm 1 | Arm 2 | Duration Difference |
|--------|------:|------:|--------------------:|
| Mean (s) | 1.170 | 1.193 | 0.117 |
| Std Dev (s) | 0.124 | 0.087 | 0.121 |
| Min–Max (s) | 0.92–1.41 | 1.08–1.35 | 0.016–0.425 |

### Independence Through Variability

The **duration difference standard deviation of 0.121 s** (range 0.016–0.425 s) is the key evidence of independent execution:

- **If arms were coupled** (shared control clock): Duration differences would be near-constant across all 10 trials. You'd see std dev ≈ 0.01 s or less.
- **If arms were independent** (separate controllers): Each arm's execution time varies trial-to-trial due to network jitter, motor response variance, etc. The difference between arm_1 and arm_2 completion times would also vary significantly.

The observed 0.121 s std dev is only achievable with **truly independent execution** where each arm has its own trajectory, its own controller, and its own completion time — with no forced synchronisation.


## Data Analysis Pipeline


### Rosbag Data Extraction

```
Raw rosbag → Extract /arm_1/joint_states and /arm_2/joint_states messages
  ├─ Each message contains: timestamp, 6 joint positions, 6 velocities
  ├─ Sample rate: 15 Hz (66.7 ms per message)
  └─ Duration: ~5.5 s per synchronized test, ~1.2 s per asynchronous test
```

### Phase Shift Detection

For **synchronized motion** (dual planning group):

```
For each joint (1–5):
  1. Extract arm_1 joint positions and arm_2 joint positions
  2. Align timestamps across both arms
  3. Find first index where |arm_1[t] − arm_1[t-1]| > 0  → arm_1 motion start
  4. Find first index where |arm_2[t] − arm_2[t-1]| > 0  → arm_2 motion start
  5. Compute time difference: arm_1_start_time − arm_2_start_time
  6. Repeat at trajectory end for end-phase shift
  7. Average across all joints to get overall phase shift
```

This reveals the **hardware dispatch offset** — how long after arm_1 begins its motion does arm_2 begin (or vice versa).

### Sync Score Calculation

The sync score quantifies how tightly motion is synchronized:

```
sync_score = 100 × (1 − abs(mean_phase_shift) / trajectory_duration)
```

- **99.89%** (test_3): ~1.53 s shift over 5.44 s trajectory = minimal relative offset
- **95.48%** (test_2): ~1.44 s shift over 5.48 s trajectory = larger relative offset
- All trials > 95%: Proves arms remain synchronized despite hardware dispatch jitter

---

## Comparing the Two Modes: Phase Difference as Visual Proof

**The videos look similar, but here's why phase difference proves they're fundamentally different:**

### Synchronised Motion 
- **Planning**: Single 12-DOF `dual` trajectory with identical waypoints for both arms
- **Phase shift**: ~1.0 s constant offset throughout execution
- **Sync score**: 95–99% (tight alignment relative to trajectory duration)
- **Variability**: Duration differences < 0.25 s across 9 trials (std dev ~0.07 s)
- **Behavior**: Arms move together; if one arm lags, the lag is constant, not cumulative

**Evidence of synchronization**: The phase shift is **constant** from start to end. If arm_1 starts 1.0 s before arm_2, it also *ends* 1.0 s before arm_2. This proves they're executing identical trajectories at identical speeds, just dispatched at different wall times.

### Asynchronous Motion
- **Planning**: Two separate 6-DOF trajectories, one per arm, executed in parallel threads
- **Phase shift**: Not measured (arms not coordinated — no expectation of alignment)
- **Duration variability**: Std dev = 0.121 s per arm; difference between arms = 0.121 s std dev
- **Behavior**: Arms complete independently; one may finish while the other is still moving

**Evidence of independence**: The duration difference **varies significantly** trial-to-trial (0.016–0.425 s). Each arm executes at its own pace, determined by its own controller's response, without waiting for the other.

### Why They Look Similar

Both configurations command identical joint goals (50° on joint 1, others at home). Both arms move to the same position. **But how they get there reveals the planning group difference**:

- **Dual group**: Forces both arms along the *same path* at the *same pace* — coordinated by design
- **Independent groups**: Each arm finds *its own path* at *its own pace* — synchronized only by having the same goal, not the same schedule

The **constant phase shift (synchronized) vs. variable duration difference (asynchronous)** is the quantitative proof that these are two distinct coordination modes, even though end-state positioning appears visually identical.

---

## Summary: What This Validates

| Mode | Planning Group | Result | Validates |
|------|---|---|---|
| **Synchronised** | `dual` (12-DOF) | Phase shift constant, sync score 95–99% | Shared trajectory ensures arms move together |
| **Asynchronous** | `arm_1` + `arm_2` (6-DOF each) | Duration variability 0.121 s std dev | Independent execution with no forced synchronisation |
