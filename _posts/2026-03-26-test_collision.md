---
layout: single
title: "The TrajectoryProxy Pattern"
date: 2026-03-26
classes: wide
author_profile: false
---


The collision safety validation is the most straightforward result in MARS: 100 hardware tests across two scenarios, zero unplanned collisions. 

---

## Test Setup

Two collision test scenarios were executed:


**Dynamic tests** (50 configurations): arm_2 moves between two configurations while arm_1 is free to move from its position. 

**Static tests** (50 configurations):  arm_2 moves between two configurations while arm_1 is fixed at its position. 

totaling to 100 run times (10 JSON result files per scenario), with 5 configuration pairs per run.


---

## Results

| Scenario | Tests | Planning Success | Execution Success | Collisions |
|----------|-------|-----------------|-------------------|-----------|
| Dynamic | 50 | 43 / 50 (86%) | 43 / 43 (100%) | **0** |
| Static | 50 | 43 / 50 (86%) | 43 / 43 (100%) | **0** |
| **Total** | **100** | **86 / 100 (86%)** | **86 / 86 (100%)** | **0** |

Planning timing:

| Metric | Dynamic | Static | Overall |
|--------|---------|--------|---------|
| Mean (ms) | 26.7 | 21.4 | 24.1 |
| Std dev (ms) | 12.4 | 10.0 | 11.5 |
| Max (ms) | 85.0 | 50.4 | 85.0 |
| 95% CI (ms) | [23.6, 30.4] | [18.7, 24.2] | [21.9, 26.4] |

---

## What the 86% Means

The 14 planning failures are not system errors. They are the planner correctly refusing to generate trajectories for unsafe goal configurations.

All 14 failures share the same property: the goal configuration places arm_2's `joint_1` at ±50° while arm_1 holds `joint_1` at 0° — configurations where the arms approach the shared workspace boundary and the 5 cm per-link padding causes the padded volumes to overlap.

In these cases:
- Physical link separation > 0 (the arms would not physically touch)
- Padded link separation < 0 (the safety volumes overlap)
- Planner result: **rejected**

This is the intended behaviour. The planner is conservative: it treats the padded geometry as the real geometry. Configurations that are physically safe but within the safety margin are rejected. The 14 rejections are false negatives — conservatively rejected safe states — not false positives.

The 0% collision rate across all 86 executed trajectories confirms that every configuration passed by the planner was genuinely safe. The system produces no false positives.

---

## Planning Time Distribution

The planning time distribution for dynamic tests is non-normal, with occasional outliers up to 85 ms. These correspond to configurations where RRTConnect requires additional sampling iterations near the collision boundary.

The 95th percentile planning time is below 60 ms. All planning times are well within the 5-second timeout. For the pick-and-place validation, planning overhead averaged 26.7 ms per movement — less than 0.2% of total task execution time.

---

## What This Proves

The collision safety result validates two properties simultaneously:

**Objective 1.2 (Planning scene management)**: the unified planning scene contains correct geometry for both arms. If the planning scene were incorrect — wrong link positions, missing geometry, incorrect TF frames — the planner would either accept configurations that are physically unsafe (false positives) or reject all configurations (planning failures unrelated to safety). Neither occurred.

**Objective 3.1 (Collision-free planning)**: every trajectory dispatched to hardware is free of inter-arm collisions. The 100% execution success rate and 0 collision events confirm this.

---

## The Unverified Assumption

One important caveat: collision detection in MoveIt2 is passive — it detects whether the planning scene says two objects are in contact, but it does not independently verify this on hardware using contact sensing or torque monitoring.

The 0 collision result is validated by:
- No mechanical contact events observed during testing
- No trajectory abort events triggered by hardware error
- No visible arm interference in recorded test sessions

It is not validated by direct contact sensing. For higher-assurance applications, independent runtime monitoring (torque-based collision detection) would complement the planning-time safety guarantee.
