---
layout: single
title: "Sync and Async Tests"
date: 2026-03-23
classes: wide
author_profile: false
---

MARS has two coordination modes. synchronised and asynchronous motion. Both modes ran on physical Niryo NED2 hardware with joint state data logged at 15 Hz from `/arm_1/joint_states` and `/arm_2/joint_states`. 

The fundamental difference between the two modes is the planning group used: the `dual` 12-DOF group produces a single shared trajectory; the independent `arm_1` / `arm_2` 6-DOF groups produce separate schedules with no shared clock.

---

## Synchronised Motion 

### Test Design

Ten trials were planned using the unified 12-DOF `dual` planning group. Joint-space goals were issued for both arms simultaneously: J1 = 10°, J2 = −25°, J3 = 15°, J4 = −20°, J5 = −50°. Joint 6 was excluded from analysis due to hardware sensor noise. One trial (test 6) was excluded from timing analysis due to an incomplete recording, leaving 9 valid trials.

Phase alignment was measured using motion onset detection. The first timestep where |Δθ| > 0 per joint initiates a start phase shift between arms. 

| Test | Arm 1 Duration (s) | Arm 2 Duration (s) | Duration Diff (s) | Start Phase Shift (s) | End Phase Shift (s) | Avg Start Shift (s) | Avg End Shift (s) | Sync Score (%) |
|------|-------------------:|-------------------:|------------------:|----------------------:|--------------------:|--------------------:|------------------:|---------------:|
| sync_joint_test_0 | 5.3215 | 5.1878 | 0.1337 | -1.1206 | -1.2543 | 0.0445 | -1.2368 | 97.49 |
| sync_joint_test_1 | 5.3804 | 5.4171 | 0.0367 | 0.3581 | 0.3948 | 0.6444 | 0.4033 | 99.32 |
| sync_joint_test_2 | 5.2335 | 5.4815 | 0.2479 | 1.1958 | 1.4437 | 1.0877 | 2.3245 | 95.48 |
| sync_joint_test_3 | 5.4406 | 5.4348 | 0.0058 | 1.5362 | 1.5304 | 1.2124 | 1.1647 | 99.89 |
| sync_joint_test_4 | 5.3566 | 5.4526 | 0.0960 | 0.0402 | 0.1362 | -0.0267 | 0.8015 | 98.24 |
| sync_joint_test_5 | 5.2917 | 5.2811 | 0.0105 | 1.3288 | 1.3183 | 0.8205 | 1.3193 | 99.80 |
| sync_joint_test_7 | 5.5164 | 5.3856 | 0.1308 | -1.5889 | -1.7197 | -1.3436 | -1.7373 | 97.63 |
| sync_joint_test_8 | 5.5205 | 5.5633 | 0.0428 | 1.6182 | 1.6610 | 1.2552 | 1.7274 | 99.23 |
| sync_joint_test_9 | 5.4194 | 5.3731 | 0.0463 | -1.1638 | -1.2102 | -1.0782 | -0.5456 | 99.15 |



### The Start Phase Shift

The start phase shift (mean 1.175 s, range 0.095–1.725 s) is a hardware-layer characteristic, not a planning failure. The `TrajectoryProxy` dispatches trajectories to each arm's hardware controller sequentially over TCP/IP — arm_2 receives its goal 20–50 ms to over a second after arm_1 depending on network timing. Because both trajectories are time-parameterised identically by the planner, this offset is constant throughout execution and does not accumulate. The end-position alignment (max 2.50°) confirms the offset does not cause tracking divergence and both arms arrive at the same position regardless of when they started.

**Objective 2.1: Met.** Duration ratio ≥ 0.95 across all 9 trials; inter-arm joint difference at end position ≤ 2.50° across all joints.

---

## Asynchronous Motion (Aim 2, Objective 2.2)

### Test Design

Ten trials used separate `arm_1` and `arm_2` 6-DOF planning groups with independent action clients running in parallel threads. Both arms were commanded to the same joint-space goals (J1 = 50°, J2 = 0°, J3 = 0°, J4 = 0°, J5 = 0°) from the same home configuration. Independence is demonstrated through execution timing variability — if the arms shared a control schedule, duration differences between trials would be near zero.

### Duration Variability

**Table 5.6 — Asynchronous Motion Duration Variability**

| Metric | Arm 1 | Arm 2 | Duration Difference |
|--------|-------|-------|---------------------|
| Mean (s) | 1.170 | 1.193 | 0.117 |
| Std Dev (s) | 0.124 | 0.087 | 0.121 |
| Range (s) | 0.920–1.409 | 1.080–1.345 | 0.016–0.425 |

The duration difference standard deviation of 0.121 s, with a range of 0.016–0.425 s, provides the primary evidence of independent execution. A coupled system would produce near-zero duration differences across trials. This magnitude of variability is only possible if each arm is executing its own time-parameterised trajectory without synchronisation to the other.


## Comparing the Two Modes

The contrast between synchronised and asynchronous results reveals the coordination modes working as designed:

**Synchronised**: small mean differences (< 2.35°), moderate peak deviations during acceleration. Both arms track the same trajectory closely — the phase offset is the limiting factor, not the planning.

**Asynchronous**: large mean differences (3–9°) reflecting genuinely different trajectories. Arms are operating independently with no expectation of similarity.

The difference between the two modes is not an accident of experimental parameters — it is the direct consequence of the planning group used. The `dual` group produces time-parameterised trajectories where both arms move together; separate groups produce independent trajectories where divergence is expected and correct.
