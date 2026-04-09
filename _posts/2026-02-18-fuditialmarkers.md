---
layout: single
title: "Fiducial Markers"
date: 2026-02-18
classes:
  - wide
author_profile: false
---

# Choosing ArUco Tags Instead of Classical Pose Estimation

A dual-arm system requires consensus on object locations. This post documents why classical pose estimation failed in practice and how ArUco fiducial markers solved the problem for MARS. 

![Aruco](/mars_ned2/assets/images/aruco.png){: .align-center}

## The Core Problem

A collaborative setup requires both robots to pick items from a shared table. Both need to know _where_ things are, and need to agree on those positions. Hardcoding won't work on dynamic environments. 

The first approach: run individual pose estimation on every pick. Classical vision pipelines like pose detection using pnp or AI introduce costs that compound in a two-robot system:

- **Per-frame inconsistency**: PnP solvers on RGB images yield different pose estimates frame-to-frame due to noise, especially under varying lighting
- **Synchronization complexity**: When robot A estimates an item's pose and robot B disagrees by 2cm, who's right? Suddenly there's a consensus problem
- **Real-time constraints**: Object detection + feature extraction + PnP solving + filtering = latency that stacks with simultaneous queries
- **Camera calibration sensitivity**: Intrinsic parameters drift, extrinsic parameters shift with camera mounting vibrations


## Why Classical Methods Failed in Practice

### PnP and Feature Matching

Approach: detect the object (via color segmentation), extract SIFT/SURF features, match them to a reference model, then use EPnP or DLT to solve for 6-DOF pose.

<video width="100%" controls autoplay muted loop>>
  <source src="/mars_ned2/assets/videos/PnP_detection.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>
**Discovered issues:**

1. **Feature starvation on simple objects**: Items with uniform colors or smooth surfaces yielded 3-5 features per frame. Below ~8 inliers, RANSAC becomes unreliable
2. **Lighting sensitivity**: Arm shadows across the table tanked feature matching. Light repositioning required recalibrating feature parameters
3. **Drift under occlusion**: Partial occlusion by one robot caused pose estimates from the full-view robot to jump as features disappeared and reappeared. No temporal filtering could smooth this without introducing lag
4. **Reference model maintenance**: Every object type needed reference images from canonical viewpoints. Items rotated or tilted at different angles required 6+ references per object type with expensive template matching


## Why ArUco Markers 

The new approach: the task doesn't require recognising _arbitrary_ objects—objects are known beforehand. They're items with specific dimensions. They can be marked.

ArUco (Augmented Reality University of Córdoba) markers provide:

- **Binary patterns**: No features to extract, no lighting sensitivity, no reference images
- **Deterministic**: Same marker on the same physical cube decodes to identical ID and corner positions frame-to-frame
- **Fast**: Marker detection is fast.


**Why ArUco Over Classical Methods**:
- **No feature extraction**: Binary patterns are deterministic—same marker = same pattern every frame
- **No reference images**: Don't need 6+ views of each object type
- **Lighting robust**: Shadows and uneven lighting don't break binary patterns
- **Fast**: 5-10 ms per camera (camera sensor limited, not algorithm limited)
- **Scalable**: One marker dictionary supports 250 unique markers. Classical PnP requires individual model per object


**For two-robot systems**:

1. **Robust independent detection**: Each camera gets consistent, deterministic detections (no disagreement from jitter/noise)
2. **Redundancy through multiple markers**: Place 2-3 markers per object. If one is occluded by a gripper, others still detect
3. **Planning handles disagreement**: Since cameras are on moving arms, planning reads both estimates + current joint states to reconcile position

![Aruco](/mars_ned2/assets/images/aruco_detection.png){: .align-center}

## Production Implementation: Detection in Dual-Robot Setup

### The Camera Disagreement Problem

The MARS system has two cameras—one mounted on `arm_1_wrist_link` (monocular) and one on `arm_2_wrist_link` (monocular). Both arms move independently.

**The reality**: These cameras **will NOT agree** on where a marker is:
- Camera 1 detects marker at (0.3, 0.2, 0.1) *in its own frame* (moving with arm_1)
- Camera 2 detects the same marker at (0.3, 0.2, 0.1) *in its own frame* (moving with arm_2)
- These are **different coordinate systems**. Camera 1's "0.3m to the right" is literally different space than Camera 2's "0.3m to the right"

The cameras cannot agree on absolute position because they're mounted on moving joints. This is **not a bug—it's how the real world works**. The planning layer handles the disagreement by accounting for where each arm is when it reads the pose estimates.

<video width="100%" controls autoplay muted loop>>
  <source src="/mars_ned2/assets/videos/aruco_mismatch.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>

### Detection Pipeline: How Each Camera Works

Despite disagreement on absolute position, **each camera independently detects markers reliably**. That's where ArUco excels.

**Camera 1 (arm_1_wrist_link)**:
```python
# Frame: continuously moving with arm_1 joint states
capture_frame_from_camera(camera_id=0)
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# Detect markers (binary pattern matching—deterministic)
corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict)

# Estimate 6-DOF pose relative to camera frame
rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
    corners, marker_size=0.03, cameraMatrix=K, distCoeffs=d
)

# Publish: "In my frame, marker 10 is at position X relative to me"
# Planning layer will handle: "Where is arm_1 right now? Transform accordingly"
publish_pose(marker_id=12, tvec=tvec, camera_frame="camera_1")
```

**Camera 2 (arm_2_wrist_link)**:
```python
# Frame: continuously moving with arm_2 joint states
# Same detection pipeline
# Different frame, different position estimates, no consensus expected
publish_pose(marker_id=12, tvec=tvec, camera_frame="camera_2")
```



**Result**: Both cameras see marker 12, publish its position in their own frames. Planning reads both, knows where each arm is, reconciles the disagreement by transforming both into world frame using joint states.

### Why ArUco Detection Is Robust Here

Even though cameras disagree on absolute position, **detection itself is rock-solid**:
- **Binary pattern matching**: Marker 10 is always marker 10 (no ambiguity)
- **Deterministic**: Same marker → same corners every frame (no frame-to-frame jitter)
- **Fast**: 5-10 ms per camera (camera-limited, not algorithm-limited)
- **Lighting invariant**: Binary patterns don't care about shadows or ambient light
- **No calibration objects needed**: Every marker of same size has identical geometry

Classical PnP would produce wildly different estimates from each camera due to feature extraction noise. ArUco produces consistent detections that planning can work with, even if they disagree on absolute position.

### Calibration: Critical for Accuracy Within Each Frame

Camera intrinsics (K, distortion) matter for pose estimation accuracy **within each camera's frame**. Without calibration: position estimates are systematically wrong (error grows with distance). With calibration: accurate to ±1-2 cm at 30cm distance.

---

## Real-World Limitations

- **Marker visibility**: Gripper occlusion of one marker loses that data point. **Solution**: 2-3 markers per object for redundancy
- **Rotation ambiguity**: Single flat marker can't distinguish 180° rotation around vertical. **Solution**: not needed—pick operations only care about XY position, not Z-rotation
- **Cameras disagree on position**: Because mounted on moving arms, camera estimates are in different coordinate frames. **Solution**: planning layer transforms both into world frame using joint states before deciding pick strategy
- **Not generalist**: Can't detect unmarked objects. For unknown items, classical vision or ML-based detection needed
- **Compute cost**: 5-10 ms per camera × 2 cameras at 30 FPS = significant load. Acceptable because detection is camera-limited (not algorithm-limited)

---

## Practical Deployment

**Marker generation** (DICT_6X6_250):
```python
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
marker_img = cv2.aruco.drawMarker(aruco_dict, marker_id, 200)
```

**Printing & mounting**: 3 cm × 3 cm, white paper, flat mount on objects. Even lighting, no shadows.

**Multi-marker strategy**: Place 2-3 markers per object (e.g., IDs 10, 11, 12). If gripper occludes one, others still detect.

---

## Performance Comparison

| Aspect | PnP | Template Match | ArUco |
|--------|---|---|---|
| Per-frame jitter | ±2-3 cm | ±1-5 cm | ±0.5 cm |
| Feature dependency | High | High | None |
| Lighting robustness | Low | Low | Very High |
| Speed | 20-50 ms | 30-100 ms | 5-10 ms |
| Generality | Any object | Any object | Marked only |

### MARS Hardware Metrics

**Detection accuracy**: ±1-2 cm at 30 cm · ±2-3 cm at 50 cm

**Compute cost**: 5-10 ms per camera · Dual cameras at 30 FPS = ~85-90% CPU on single-core ARM (camera-limited, not algorithm-limited)

---

## Why This Approach Wins for Multi-Robot Systems

| Aspect | Classical PnP | Template Matching | ArUco Markers |
|--------|---|---|---|
| **Per-frame consistency** | ±2-3 cm variation | ±1-5 cm variation | ±0.5 cm variation |
| **Feature dependency** | High (needs distinctive features) | High (template matching) | None (binary patterns) |
| **Lighting sensitivity** | High (shadows break features) | High | Very Low |
| **Compute cost** | 20-50 ms | 30-100 ms | 5-10 ms |
| **Two-robot consensus** | Hard (different views = disagreement) | Hard | Trivial (same reference frame) |
| **Generality** | Yes (any object) | Yes (any object) | No (marked objects only) |

ArUco trades away generality for determinism—exactly what you need in a controlled, multi-robot environment.

---

## Summary

For dual-arm systems with known objects, ArUco markers provide **robust, deterministic detection** from each camera independently. The cameras will disagree on absolute position (they're on moving arms)—that's expected. Planning handles the disagreement by reading both camera poses and transforming them using current joint states.

The win: deterministic detections (no jitter) + speed (5-10 ms) + robustness to lighting. Classical PnP fails because feature extraction is noisy and sensitive to shadows. ArUco's binary patterns are immune to these problems. On compute-limited hardware, 5-10 ms per camera is acceptable because the algorithm is camera-limited, not CPU-limited.

Worth an afternoon of printing markers.