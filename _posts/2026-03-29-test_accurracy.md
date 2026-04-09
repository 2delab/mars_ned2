---
layout: single
title: "Repeatability test"
date: 2026-03-29
classes: wide
author_profile: false
---

The most important result from the pick-and-place validation is not the 28.6% throughput gain. It is the 0.5% coefficient of variation across repeated dual-arm tasks. This is the result that determines whether the system is deployable. its not how fast it is, but how consistently it behaves.

---

## Why Repeatability Is the Primary Metric

A system that achieves 28.6% throughput improvement in one trial but shows 40% variance across trials is not reliable. You cannot reason about its behaviour, set realistic expectations, or integrate it into a larger system with defined timing constraints.

A system that achieves 28.6% improvement consistently — with 0.5% CV — can be treated as deterministic for practical purposes. You know what it will do before it does it.

For MARS, repeatability is especially important because the coordination architecture involves two independent hardware controllers receiving sequential trajectory commands over TCP/IP. If communication jitter were accumulating — if each task introduced additional timing error — the CV would increase across the test set. It does not.

---

## The Data

Three repeated dual-arm pick-and-place tasks, each consisting of three phases (approach/lower/retract for pick, approach/lower/retract for place, approach/lower/retract for return):

| Task | Total Time (s) | Phase 1 (s) | Phase 2 (s) | Phase 3 (s) |
|------|---------------|-------------|-------------|-------------|
| 1 | 23.43 | 8.37 | 8.00 | 7.07 |
| 2 | 23.27 | 8.27 | 7.93 | 7.07 |
| 3 | 23.47 | 8.33 | 8.07 | 7.07 |
| **Mean** | **23.39** | **8.32** | **8.00** | **7.07** |
| **Std Dev** | **0.11** | **0.05** | **0.07** | **0.00** |
| **CV** | **0.5%** | **0.6%** | **0.9%** | **< 0.1%** |

Phase 3 shows essentially zero variance (< 0.1% CV). This phase always involves the arm returning to the same retract position from the same placement pose — the path length is constant and the hardware executes it identically every time.

Phase 1 and 2 show slightly higher variance (0.6–0.9%) due to varying approach distances as the arm moves between pick and place positions at different spatial extents. The variance is bounded and consistent.

The single-arm baseline shows similar characteristics:

| Single-arm | Times (s) | Mean (s) | Std Dev (s) |
|-----------|-----------|---------|-------------|
| Task 1 | 14.44 | — | — |
| Tasks 2–6 | 16.73, 16.80, 16.73, 16.87, 16.73 | 16.77 | 0.06 |

Task 1 is an outlier (14.44 s) — the startup overhead of the first planning call after system initialisation. Excluding it, the variance is 0.06 s (0.4% CV). The dual-arm system shows comparable variance (0.11 s) despite the additional complexity of coordinating two arms.

---

## What Produces the Variance

The residual variance (~0.1 s) comes from two sources:

**Communication jitter**: the ROSBridge round-trip time varies between 20–50 ms depending on network load. Across a task with 6 movements and 2 arms, this accumulates to approximately ±60–180 ms.

**Hardware motion profile**: the Niryo's internal motion profile generator produces slightly different velocity profiles depending on the joint configuration at the start of each movement. This is mechanical, not software-induced.

Neither source accumulates across tasks. There is no drift — task 3 has the same variance as task 1. The `TrajectoryProxy` dispatch introduces no cumulative timing error.

---

## The Planning Overhead Is Negligible

Across all pick-and-place movements:

| Metric | Value |
|--------|-------|
| Mean planning time | 26.7 ms |
| Maximum planning time | 33.0 ms |
| Planning as % of total task time | < 0.2% |

The motion planner is not the bottleneck. Hardware execution (400–6000 ms per movement) dominates. This has an important implication: optimising the planner (faster algorithm, lower timeout) would not meaningfully improve total task time. Improving hardware communication latency (native ROS2 driver instead of ROSBridge) would.

---

## The Baseline Comparison

The single-arm baseline executes all 6 tasks sequentially: 98.31 s total. The dual-arm system executes 6 equivalent arm-tasks in parallel: 70.17 s total. The difference (28.14 s, 28.6%) is stable across the three-trial set.

The throughput gain is real. More importantly, it is **reproducible** — which means it can be relied upon, not just observed once.
