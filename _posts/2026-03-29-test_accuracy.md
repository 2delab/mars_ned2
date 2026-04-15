---
layout: single
title: "Accuracy and Repeatability"
header:
  teaser: /assets/images/posts/accuracy_tests.png
date: 2026-03-29
classes: wide
author_profile: false
---

## Trajectory Repeatability and Accuracy 

The goal of this study is to verify that the MARS dual-arm system executes the same motion consistently across repeated runs. By commanding each arm through an identical joint-space trajectory multiple times, we can quantify how closely each repetition matches the others ensuring the system behaves predictably and that any single trial is representative of general operation.

### Methodology

Position range (max − min) is computed per joint per trial for each arm. This metric is independent of timing differences between trials: it captures how consistently each joint sweeps the same motion amplitude across repeated executions. The coefficient of variation (CV = std / mean × 100%) summarises cross-trial consistency.

### Results

**Arm 1 — position range across 9 trials:**

| Joint | Mean range (rad) | Std (rad) | CV (%) | Min (rad) | Max (rad) |
|-------|-----------------|-----------|--------|-----------|-----------|
| Joint 1 | 0.701270 | 0.000633 | 0.09 | 0.700086 | 0.701608 |
| Joint 2 | 0.525013 | 0.000753 | 0.14 | 0.524171 | 0.525686 |
| Joint 3 | 0.348606 | 0.000476 | 0.14 | 0.348438 | 0.349952 |
| Joint 4 | 0.349918 | 0.001131 | 0.32 | 0.348214 | 0.351282 |
| Joint 5 | 0.848291 | 0.007374 | 0.87 | 0.842155 | 0.868233 |
| **Average** | | | **0.31** | | |

**Arm 2 — position range across 9 trials:** 

| Joint | Mean range (rad) | Std (rad) | CV (%) | Min (rad) | Max (rad) |
|-------|-----------------|-----------|--------|-----------|-----------|
| Joint 1 | 0.700594 | 0.001015 | 0.14 | 0.698565 | 0.701608 |
| Joint 2 | 0.524003 | 0.000476 | 0.09 | 0.522656 | 0.524171 |
| Joint 3 | 0.348438 | 0.000000 | 0.00 | 0.348438 | 0.348438 |
| Joint 4 | 0.350600 | 0.000762 | 0.22 | 0.349748 | 0.351282 |
| Joint 5 | 0.857154 | 0.001406 | 0.16 | 0.854427 | 0.859029 |
| **Average** | | | **0.12** | | |



Arm 1 avg CV = 0.31% and  Arm 2 avg CV = 0.12% shows clear consistency as position range (max − min) of each joint varies by only 0.31% (Arm 1) and 0.12% (Arm 2) on average. i.e. the motion amplitude is almost identical every single run.

Each joint sweeps a nearly identical motion amplitude across all 9 trials. Joint 5 shows the highest variance (CV 0.87% for Arm 1) but remains well within the excellent threshold. Arm 2 is marginally more consistent than Arm 1 overall. The dual-arm system delivers reproducible motion independently of small timing variations between trials.

---

## Time parameterisation

The `dual` 12-DOF MoveGroup planner produces a single time-parameterised trajectory shared by both arms.


### Methodology

1. **Execution duration similarity** — ratio `min(d1, d2) / max(d1, d2)` per trial. A ratio close to 1.0 confirms both arms executed from one shared time plan. Motion onset/offset detected with a 0.5°/sample velocity threshold on joint 1.
2. **Joint goal agreement** — `|Arm1 − Arm2|` final position at each arm's movement offset. Both arms are commanded to the same target; sub-degree agreement confirms independent goal achievement.


### Execution Duration Similarity

| Trial | Arm 1 (s) | Arm 2 (s) | Ratio | Onset shift (s) | 
|-------|-----------|-----------|-------|-----------------|
| T0 | 5.099 | 5.110 | 0.9980 | −1.229 | 
| T1 | 5.340 | 5.154 | 0.9652 | +0.581 |  
| T2 | 5.213 | 5.162 | 0.9902 | +1.476 | 
| T3 | 5.279 | 5.164 | 0.9782 | +1.511 | 
| T4 | 5.075 | 5.328 | 0.9524 | −0.095 |
| T5 | 5.136 | 5.114 | 0.9957 | +1.340 |
| T7 | 5.221 | 5.303 | 0.9844 | −1.725 |
| T8 | 5.323 | 5.464 | 0.9741 | +1.520 |
| T9 | 5.338 | 5.249 | 0.9833 | −1.104 |
| **Mean** | | | **0.9802** | **1.175 s** | |
| **Std**| | | **0.0138** | | |
| **Range** || **0.9524–0.9980** |

All 9 trials PASS (criterion: mean ratio > 0.95).

### Joint Goal Agreement

| Joint | Mean \|Δ\| (°) | Std (°) | Min \|Δ\| (°) | Max \|Δ\| (°) | 
|-------|----------------|---------|----------------|----------------|
| Joint 1 | 0.659 | 0.792 | 0.087 | 2.703 | 
| Joint 2 | 0.029 | 0.041 | 0.000 | 0.087 | 
| Joint 3 | 0.048 | 0.059 | 0.000 | 0.174 |
| Joint 4 | 0.127 | 0.212 | 0.000 | 0.703 |
| Joint 5 | 0.498 | 0.442 | 0.088 | 1.494 | 
| **Overall mean** | **0.272°** | | | | |

All joints PASS (criterion: mean \|Δ\| < 1.0°). Overall mean 0.272°

Joint 1 shows the highest inter-arm difference (mean 0.659°, max 2.703°) due to its large commanded displacement and gravity loading. Joints 2–4 show near-perfect agreement (mean < 0.13°). All values are well within the 5° threshold of Aim 2, Objective 1.



---

## Summary

| Metric | Result | Criterion | Status |
|--------|--------|-----------|--------|
| Arm 1 avg position range CV | 0.31% | < 2% |  PASS |
| Arm 2 avg position range CV | 0.12% | < 2% |  PASS|
| Duration ratio (mean) | 0.9802 | > 0.95 | PASS |
| Duration ratio (min) | 0.9524 | > 0.95 |  PASS|
| Joint goal agreement (mean) | 0.272° | < 1.0° |  PASS |
| Joint goal agreement (max joint mean) | 0.659° (J1) | < 1.0° |  PASS|

MARS delivers trajectory repeatability with CV below 1% for all joints on both arms, and synchronised coordination with duration ratios above 0.95 and inter-arm goal agreement below 0.66° across all 9 trials. 
