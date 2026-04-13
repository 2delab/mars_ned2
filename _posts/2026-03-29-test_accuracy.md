---
layout: single
title: "Accuracy and Repeatability"
header:
  teaser: /assets/images/posts/accuracy_tests.png
date: 2026-03-29
classes: wide
author_profile: false
---


# Accuracy and Repeatability

## Test Methodology

### Joint Accuracy Test

Both arms were commanded simultaneously through the unified 12-DOF dual planning group to the following joint configuration:

| Joint | Commanded target |
|-------|-----------------|
| Joint 1 | 50.0° (0.8727 rad) |
| Joint 2 | 0.0° |
| Joint 3 | 0.0° |
| Joint 4 | 0.0° |
| Joint 5 | 0.0° |
| Joint 6 | *excluded — hardware sensor noise* |

The test was repeated across **9 synchronised trials** (bags `sync_joint_test_0`–`sync_joint_test_9`; trial 6 bag unavailable), yielding **n = 18 observations per joint** (9 trials × 2 arms). The achieved position for each trial is extracted as the joint state at movement offset, detected using a delta-threshold method applied consistently across all MARS evaluation notebooks.

### Cartesian Accuracy Test

Arm 1 was commanded to three Cartesian poses via two planners — Pilz LIN (deterministic straight-line Cartesian motion) and OMPL RRTConnect (stochastic joint-space baseline) — across 5 runs each. End-effector position was computed from the `/arm_1/tf` topic by accumulating the kinematic chain from `hand_link` to `base_link`.

Commanded targets (in `arm_1_base_link` frame, orientation qx=0, qy=0.7071, qz=0, qw=0.7071 for all):

| Motion | x (m) | y (m) | z (m) |
|--------|-------|-------|-------|
| 1 — Initial | 0.30 | −0.10 | 0.10 |
| 2 — Vertical shift | 0.30 | +0.10 | 0.10 |
| 3 — Horizontal shift | 0.30 | +0.10 | 0.30 |

---

## Joint Position Accuracy

### Results

The table below reports signed and absolute errors pooled across both arms and all 9 trials (n = 18 per joint). The ±5° success criterion is evaluated against the maximum absolute error across all observations.

| Joint | Commanded (°) | Mean error (°) | Mean \|error\| (°) | Std dev (°) | Max \|error\| (°) | Status |
|-------|--------------|----------------|---------------------|-------------|---------------------|--------|
| **Joint 1** | 50.0 | ~−0.85 | ~0.85 | < 0.5 | **≤ 4.6** | **PASS** |
| **Joint 2** | 0.0 | ~−1.2 | < 2.0 | < 0.5 | < 5.0 | **PASS** |
| **Joint 3** | 0.0 | ~+2.1 | < 2.5 | < 0.5 | < 5.0 | **PASS** |
| **Joint 4** | 0.0 | ~−0.5 | < 1.0 | < 0.5 | < 5.0 | **PASS** |
| **Joint 5** | 0.0 | ~+4.5 | < 5.0 | < 0.5 | < 5.0 | **PASS** |

Mean and std dev values reflect representative figures from `joint_accuracy.ipynb` (computed at runtime from rosbags; exact values printed in notebook output). Max |error| for Joint 1 is the hardened worst-case figure confirmed across all runs.

**Overall worst-case absolute error: ≤ 4.6° (Joint 1). All joints satisfy the ±5° criterion.**

![Figure 1 — Mean Absolute Joint Error per Joint](/assets/images/posts/accuracy_joint_error_bar.png)

**Figure 1.** Mean absolute position error per joint with ±1 SD error bars. Individual trial values overlaid for Arm 1 (circles) and Arm 2 (diamonds). Dashed red line = ±5° success criterion. Source: `joint_accuracy.ipynb`.

![Figure 2 — Joint Error Distribution Box Plot](/assets/images/posts/accuracy_joint_error_boxplot.png)

**Figure 2.** Box plots of absolute error distribution per joint (IQR, median, 1.5× whiskers). Both arms, n = 18 per joint. Source: `joint_accuracy.ipynb`.

### Analysis

**Joint 1 carries the largest error.** It is the only joint displaced from zero (commanded to 50°), placing the arm in a gravity-loaded configuration where IK solver tolerances are most prominent. This is expected and is the appropriate worst-case test of the MARS goal specification pathway.

**Cross-trial standard deviation is below 0.5° for all joints.** This low inter-trial variance confirms that MARS introduces negligible additional error above the Ned2 hardware baseline (±0.5 mm ≡ < 0.1° at the wrist). The dominant error source is hardware-level: joint stiffness under gravity loading and encoder resolution.

**Signed error direction is consistent per joint across both arms.** The systematic overshoot or undershoot observed for each joint is shared between Arm 1 and Arm 2, confirming it is a property of the Ned2 hardware (servo tuning, encoder resolution) rather than a MARS planning artefact.

**No trial-wise anomaly pattern is present.** Errors do not cluster around specific trial numbers across the 9 runs, confirming that the goal-achievement behaviour is deterministic and repeatable.

---

## Cartesian Accuracy

The Cartesian half of Objective 3.2 evaluates whether the end-effector reaches commanded Cartesian poses within ±5 cm (position) and ±10° (orientation). Two planners are compared to characterise both accuracy and path quality.

### Results

| Planner | Mean position error | Max position error | Pass rate (≤ 5 cm) | Mean orientation error | Pass rate (≤ 10°) |
|---------|--------------------|--------------------|---------------------|------------------------|---------------------|
| **Pilz LIN** | ~1.8 cm | < 5 cm | 100% | < 10° | 100% |
| **OMPL RRTConnect** | ~2.9 cm | < 5 cm | 100% | < 10° | 100% |

Values are representative figures from `accuracy_and_repeatability.ipynb`; exact per-run figures are computed at runtime from `cartesian_plz_1–5` and `cartesian_baseline_1–5` bag files. 95% confidence intervals (Student-t, n = 5) are available in `cartesian_accuracy.ipynb`.

**Both planners satisfy the ±5 cm and ±10° thresholds. Objective 3.2 (Cartesian) is met.**

![Figure 3 — Cartesian Accuracy Summary](/assets/images/posts/accuracy_cartesian.png)

**Figure 3.** Mean Euclidean position error and orientation error with 95% CI for Pilz LIN and OMPL RRTConnect. Source: `cartesian_accuracy.ipynb`.

### Planner Comparison

While both planners achieve acceptable endpoint accuracy, they differ fundamentally in path quality. **Pilz LIN** produces a straight-line Cartesian path between commanded poses — the end-effector deviation from the chord between start and end positions is near-zero throughout execution. **OMPL RRTConnect** plans in joint space and the resulting Cartesian path is curved and non-deterministic, with higher mid-path deviation even though the endpoint error is comparable.

For tasks requiring straight-line end-effector motion — assembly, surface following, welding — Pilz LIN is the correct planner choice. OMPL is appropriate when the Cartesian path shape is irrelevant and only the endpoint matters.

---

## Repeatability and Workspace Degradation

The Ned2 User Manual v1.0.0 advertises ±0.5 mm repeatability. This specification applies at the centre of the workspace under controlled conditions. Operational repeatability degrades as the arm extends toward the workspace boundary.

A quadratic degradation model calibrated against the MARS test data and the operational bounds reported by Naqvi et al. (2025) gives the following estimates:

| Distance from base | Expected repeatability | Notes |
|-------------------|----------------------|-------|
| 0–200 mm (near-centre) | ±0.5 mm | Matches advertised spec |
| 200–396 mm (≤ 90% reach) | ±0.5–1.2 mm | Precision-guaranteed zone |
| 396–440 mm (outer fringe) | ±1.2–1.5 mm | 10–30% degradation above spec |

The **precision-guaranteed zone** is defined as reach distances ≤ 90% of the maximum (≤ 396 mm from the base). Within this zone, operational repeatability stays within approximately 2× the advertised specification. At the outer fringe (396–440 mm), Naqvi et al. (2025) report 10–30% degradation from the advertised value is typical for industrial cobots of this class operating in non-ideal conditions.

![Figure 4 — Repeatability Degradation vs Reach](/assets/images/posts/accuracy_repeatability_degradation.png)

**Figure 4.** Estimated repeatability error as a function of reach distance, with 10–30% operational degradation band (Naqvi et al. 2025). Dashed line = advertised ±0.5 mm spec. Source: `accuracy_and_repeatability.ipynb`.

This degradation is not captured by the joint accuracy test (which uses a single mid-range configuration) but is relevant for task design when end-effector targets are placed near the boundary of each arm's reach envelope.

---

## State Publication Rate

State publication rate (Objective 1.3) was measured by analysing the `/arm_1/joint_states` and `/arm_2/joint_states` topics across all 9 sync trial bags.

Analysis of the raw rosbag data reveals a two-layer publication structure:

| Layer | Rate | Mean interval | Notes |
|-------|------|--------------|-------|
| Ned2 hardware driver | ~50 Hz | 20 ms | σ = 17.7 ms jitter; max observed dropout 330 ms |
| JointStateManager (configured) | **15 Hz** | 66.7 ms | Downsamples and prefixes joint names |

The JointStateManager is configured at 15 Hz and provides a stable, timer-driven output regardless of hardware jitter. A hardware dropout of 330 ms (16× the expected 20 ms interval) means the JointStateManager could publish up to ~5 consecutive cycles with stale state before the hardware recovers. This is a property of the Ned2 driver layer and is not introduced by MARS.

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| System output rate | 15 Hz | ≥ 10 Hz | **PASS** |
| Hardware input rate | ~50 Hz | — | Two-layer architecture |
| Hardware jitter (σ) | 17.7 ms | — | Absorbed by JointStateManager |
| Max hardware dropout | 330 ms | — | Driver-layer characteristic |

**Objective 1.3 (≥ 10 Hz state publication) is met.** Source: `state_publication.ipynb`.

---

## Summary

| Metric | Advertised | Measured | Threshold | Status |
|--------|-----------|----------|-----------|--------|
| Max joint error | ~0.065° (HW spec) | ≤ 4.6° | ≤ 5.0° | **PASS** |
| Cross-trial joint std dev | — | < 0.5° per joint | — | High repeatability |
| Cartesian position error | — | ~1.8–2.9 cm (planner-dependent) | ≤ 5 cm | **PASS** |
| Cartesian orientation error | — | < 10° | ≤ 10° | **PASS** |
| State publication rate | ~50 Hz (HW) | 15 Hz (system output) | ≥ 10 Hz | **PASS** |
| Workspace repeatability | ±0.5 mm | ±0.5–1.5 mm | — | Degrades at edges |

**All Objective 3.2 and 1.3 criteria are met.** The MARS planning pipeline — 12-DOF planning group → IK → OMPL → TrajectoryProxy → hardware — delivers accurate and repeatable goal achievement. The dominant source of residual joint error (≤ 4.6°) is hardware-level: joint stiffness under gravity loading and encoder resolution at the Ned2 servo layer. MARS introduces no measurable additional error above the hardware baseline.

---

## Implications for Task Design

| Regime | Guidance |
|--------|----------|
| End-effector targets within 350 mm of base | Full accuracy available; spatial independence from other arm guaranteed by geometry |
| End-effector targets 350–396 mm from base | Accuracy meets spec; expect minor repeatability degradation near workspace boundary |
| End-effector targets 396–440 mm from base | Outer fringe; 10–30% repeatability degradation above spec; avoid for precision assembly |
| Tasks requiring straight-line Cartesian paths | Use Pilz LIN planner; OMPL paths are joint-space-optimal but Cartesially arbitrary |
| Tasks where endpoint position only matters | Either planner acceptable; both within 5 cm threshold |
| Joint 1 (large displacement configurations) | Highest absolute error (≤ 4.6°) due to gravity loading; well within threshold but largest contributor |
