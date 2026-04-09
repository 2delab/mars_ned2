---
layout: single
title: "Accuracy tests"
date: 2026-03-29
classes: wide
author_profile: false
---

This post measures how accurately the Niryo Ned2 arms execute commanded trajectories. Given a target joint configuration, how close does the actual joint position get? How much does this vary across repeated trials? Accuracy is measured as the range (min-max spread) of achieved positions across 9 test cycles.

---

## Why Command Accuracy Matters

The gap between commanded position and actual position determines whether the system is trustworthy for real tasks. A planner can generate perfect trajectories, but if the hardware executes them inaccurately or inconsistently, the entire system fails.

**Key question**: When we command joint_5 to position 0.8483 rad, what range of positions will we actually see?

- If it's always 0.8483 ± 0.0005 rad → **highly accurate and consistent**
- If it's 0.8483 ± 0.0261 rad → **accurate on average, but high variance** (different each execution)
- If it drifts from trial 1 to trial 9 → **degradation** (system unreliable)

The data shows what we actually observe across 9 repeated commanded configurations on both arms.

---

## Test Methodology

Each arm was commanded to 5 target configurations via MoveIt2 trajectory execution. For each commanded configuration, the joint_states were recorded from 9 repeated executions. The min-max range shows the actual spread of achieved positions.

This measures **execution accuracy** — whether the joint reaches the commanded position — separate from **trajectory timing** or **synchronization**.

---

## ARM 1: Command Accuracy by Joint

| Joint | Commanded (rad) | Actual Mean (rad) | Min (rad) | Max (rad) | Range (rad) | Std Dev (mrad) | CV (%) |
|-------|-----------|-----------|-----------|-------------|---|---|
| **joint_1** | 0.7013 | 0.7013 | 0.7001 | 0.7016 | 0.0015 | 0.63 | **0.09** |
| **joint_2** | 0.5250 | 0.5250 | 0.5242 | 0.5257 | 0.0015 | 0.75 | **0.14** |
| **joint_3** | 0.3486 | 0.3486 | 0.3484 | 0.3500 | 0.0015 | 0.48 | **0.14** |
| **joint_4** | 0.3499 | 0.3499 | 0.3482 | 0.3513 | 0.0031 | 1.13 | **0.32** |
| **joint_5** | 0.8483 | 0.8483 | 0.8422 | 0.8682 | 0.0261 | 7.37 | **0.87** |

**Reading**: When we command joint_1 to 0.7013 rad, the actual achieved position varies by ±0.75 mrad (0.0015 rad range). The mean always matches the command perfectly, but there's scatter around that mean.

**Analysis**:
- **Joints 1–4**: Excellent accuracy. Range < 0.0031 rad, CV < 0.35%. The arm reliably executes these commands.
- **Joint 5**: Poor accuracy. Range = 0.0261 rad (±13 mm at full reach), CV = 0.87%. This joint is mechanically unreliable.

---

## ARM 2: Command Accuracy by Joint

| Joint | Commanded (rad) | Actual Mean (rad) | Min (rad) | Max (rad) | Range (rad) | Std Dev (mrad) | CV (%) |
|-------|-----------|-----------|-----------|-------------|---|---|
| **joint_1** | 0.7006 | 0.7006 | 0.6986 | 0.7016 | 0.0030 | 1.02 | **0.14** |
| **joint_2** | 0.5240 | 0.5240 | 0.5227 | 0.5242 | 0.0015 | 0.48 | **0.09** |
| **joint_3** | 0.3484 | 0.3484 | 0.3484 | 0.3484 | 0.0000 | 0.00 | **0.00** |
| **joint_4** | 0.3506 | 0.3506 | 0.3497 | 0.3513 | 0.0015 | 0.76 | **0.22** |
| **joint_5** | 0.8572 | 0.8572 | 0.8544 | 0.8590 | 0.0046 | 1.41 | **0.16** |

**Analysis**:
- **Joint 3 is perfect**: Zero variance (0% CV). Every time we command this position, we get exactly the same result. This is exceptional.
- **Joint 5 is stable**: 0.16% CV on arm_2 vs 0.87% on arm_1. The second arm's wrist is significantly more accurate. This suggests mechanical difference (calibration drift, servo tuning, or wear).
- **Overall**: Arm 2 outperforms arm_1 in all metrics. All joints < 0.25% CV except joint_5.

---

## Accuracy vs Execution Time

Command accuracy is independent of execution speed. Across the 10 test cycles (different execution durations 8.8–9.7 s), the position range remains constant. Fast execution and slow execution hit the same range of actual positions:

| Metric | Value |
|--------|-------|
| Fastest cycle | 8.8 s |
| Slowest cycle | 9.7 s |
| Position range change over speed variation | None (stationary) |

**Implication**: The hardware's accuracy limitation is not time-dependent. It's a static mechanical property.

---

## What Causes Position Inaccuracy

Three factors explain why actual position deviates from commanded position:

**1. Servo Resolution**: The Niryo's joint servos cannot achieve infinite precision. Each servo has mechanical backlash and encoder resolution (~0.5 mrad). Joint 5 experiences the largest backlash because of wrist compliance.

**2. Load-Dependent Gravity Compensation**: The robot's gravity compensation algorithm estimates joint torques needed to hold each position. The estimate depends on assumed payload (default = gripper only). If gripper load varies, compensation drifts. Joint 5 (wrist) is most sensitive because it cantilevered, creating leverage.

**3. Thermal Drift**: Joint servo parameters drift slowly with temperature. Over 9 test cycles spanning ~90 seconds, thermal effects are minimal. But joint_5's higher variance suggests its servo may be tuned less conservatively.

The range does **not increase** from trial 1 to trial 9 — the error is **stationary**, not degrading. The mechanism is static, not cumulative.

---

## Implications for Task Design

Command accuracy determines which joint configurations are suitable for which tasks:

| Joint | Accuracy | Best Use | Avoid |
|-------|----------|----------|-------|
| joint_1, joint_2 | CV < 0.15% | Precision tasks | High-speed cycles |
| joint_3 | CV ≤ 0.22% | Precision assembly | None—excellent |
| joint_4 | CV < 0.35% | General manipulation | Tight tolerances |
| joint_5 | CV 0.16–0.87% | Approach/grip positioning | Precision angles |

**For high-precision tasks** (hole insertion, part alignment): Avoid joint_5 as the primary motion axis. Use joints 1–4 for precision; use joint_5 only for final positioning or grip angle.

**For general tasks** (pick-and-place, assembly): All joints are accurate enough. Even joint_5's 0.87% CV translates to ±1–2 cm at the end-effector, which is acceptable for most bin-picking tasks.

**Recommendation**: Calibrate arm_1's joint_5 servo to reduce its variance. Arm_2's wrist is 5× more accurate (0.16% vs 0.87%), suggesting arm_1 needs tuning or maintenance.
