---
layout: single
title: "Fudutial Markers"
date: 2026-02-18
classes:
  - wide
author_profile: false
---


# Choosing ArUco Tags insead of Classical Pose Estimation 


## The Core Problem

A collaborative setup requires both robots to pick items from a shared table. Both need to know _where_ things are, and need to agree on those positions. Hardcoding won't work on dynamic environments. 

The naive approach: run individual pose estimation on every pick. Classical vision pipelines introduce operational costs that compound in a two-robot system:

- **Per-frame inconsistency**: PnP solvers on RGB images yield different pose estimates frame-to-frame due to noise, especially under varying lighting
- **Synchronization complexity**: When robot A estimates an item's pose and robot B disagrees by 2cm, who's right? Suddenly there's a consensus problem
- **Real-time constraints**: Object detection + feature extraction + PnP solving + filtering = latency that stacks with simultaneous queries
- **Camera calibration sensitivity**: Intrinsic parameters drift, extrinsic parameters shift with camera mounting vibrations

The requirement: a baseline that's _reliable, agreed-upon across both robot control nodes, and fast enough to run at 10Hz+_.

## Why Classical Methods Failed in Practice

### PnP and Feature Matching

The textbook approach: detect the object (via color segmentation), extract SIFT/SURF features, match them to a reference model, then use EPnP or DLT to solve for 6-DOF pose.

**Early prototype:**

```python
# Prototype using cv2.solvePnP
detector = cv2.SIFT_create()
kp_ref, des_ref = detector.detectAndCompute(reference_image, None)

def estimate_pose(frame):
    kp, des = detector.detectAndCompute(frame, None)
    matches = flann.knnMatch(des_ref, des, k=2)
    # Lowe's ratio test
    good = [m for m,n in matches if m.distance < 0.7*n.distance]
    if len(good) < 4:
        return None
    src_pts = np.float32([kp_ref[m.queryIdx].pt for m in good])
    dst_pts = np.float32([kp[m.trainIdx].pt for m in good])
    _, rvec, tvec, inliers = cv2.solvePnPRansac(
        objectPoints=model_3d_points,
        imagePoints=dst_pts,
        cameraMatrix=K,
        distCoeffs=dist_coeffs,
        iterationsCount=100,
        reprojectionError=8.0,
        confidence=0.99
    )
    return rvec, tvec
```

**Discovered issues:**

1. **Feature starvation on simple objects**: Items with uniform colors or smooth surfaces yielded 3-5 features per frame. Below ~8 inliers, RANSAC becomes unreliable
2. **Lighting sensitivity**: Arm shadows across the table tanked feature matching. Light repositioning required recalibrating feature parameters
3. **Drift under occlusion**: Partial occlusion by one robot caused pose estimates from the full-view robot to jump as features disappeared and reappeared. No temporal filtering could smooth this without introducing lag
4. **Reference model maintenance**: Every object type needed reference images from canonical viewpoints. Items rotated or tilted at different angles required 6+ references per object type with expensive template matching

### Template Matching (2D approach)

Straight template matching on the workspace—detect bounding box, estimate pose from 2D projection.

**Core issue**: Under-constrained problem. A 2D projection of a 3D object yields multiple valid 3D interpretations. Adding constraints (flat on table, known dimensions) requires building object-specific models anyway.

A week spent here solving sub-problems (semantic segmentation, depth estimation) eliminated the simplicity being pursued.

## Why ArUco Markers Changed Everything

The realization: the task doesn't require recognizing _arbitrary_ objects—objects are known beforehand. They're itemr with specific dimensions. They can be marked.

ArUco (Augmented Reality University of Córdoba) markers provide:

- **Binary patterns**: No features to extract, no lighting sensitivity, no reference images
- **Deterministic**: Same marker on the same physical cube decodes to identical ID and corner positions frame-to-frame
- **Fast**: Marker detection is fast.


**Implementation:**

```python
import cv2

# Single initialization
arucoDict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(arucoDict, parameters)

def estimate_item_pose(frame, camera_matrix, dist_coeffs, marker_length=0.05):
    """
    Detect ArUco markers and estimate pose.
    marker_length: physical size of printed marker in meters
    Returns: (marker_id, tvec, rvec) or None
    """
    corners, ids, rejected = detector.detectMarkers(frame)
    if ids is None:
        return None
    poses = []
    for i, marker_id in enumerate(ids.flatten()):
        rvec, tvec, _ = aruco.estimatePoseSingleMarkers(
            corners[i], marker_length, camera_matrix, dist_coeffs
        )
        poses.append((marker_id, rvec.flatten(), tvec.flatten()))
    return poses
```

**Critical advantages for two-robot systems:**

1. **No per-object calibration**: Every ArUco marker of the same size has identical corner geometry
2. **Cheap redundancy**: 2-3 markers per cube. If one is occluded, others compensate:

```python
def fuse_marker_poses(poses, marker_to_object_map, history_buffer=5):
    """
    Fuse multiple marker detections into object-level poses.
    Uses median filtering to reject noise.
    """
    object_poses = {}
    for marker_id, rvec, tvec in poses:
        obj_id = marker_to_object_map.get(marker_id)
        if obj_id not in object_poses:
            object_poses[obj_id] = []
        object_poses[obj_id].append((rvec, tvec))
    
    fused = {}
    for obj_id, pose_list in object_poses.items():
        if len(pose_list) > 1:
            rvecs = np.array([p[0] for p in pose_list])
            tvecs = np.array([p[1] for p in pose_list])
            fused[obj_id] = (np.median(rvecs, axis=0), np.median(tvecs, axis=0))
        else:
            fused[obj_id] = pose_list[0]
    return fused
```

3. **Temporal consistency**: Deterministic markers enable confident Kalman filtering with minimal frame-to-frame noise:

```python
from filterpy.kalman import KalmanFilter

class ItemPoseTracker:
    def __init__(self, process_variance=1e-5, measurement_variance=1e-4):
        self.kf = KalmanFilter(dim_x=6, dim_z=6)  # 3 translation + 3 rotation
        self.kf.x = np.zeros(6)
        self.kf.F = np.eye(6)  # Identity transition
        self.kf.H = np.eye(6)
        self.kf.P *= 1000
        self.kf.R = measurement_variance
        self.kf.Q = process_variance
    
    def update(self, rvec, tvec):
        z = np.hstack([tvec, rvec])
        self.kf.predict()
        self.kf.update(z)
        return self.kf.x
```

## Accepted Trade-offs

Trading _generality_ for _reliability in this specific context_:

- **Marker visibility**: Complete marker obscuration loses that data point (could be resolved with multiple markers)
- **Rotation ambiguity**: Single markers create 180° rotation ambiguity around the marker's normal (solved by assuming items placed flat)
- **Not suitable for arbitrary objects**: Changing to unmarked items requires a new approach(nex wooould be to train an AI model which is computetionally expensive)


## In summary

For multi-robot systems with known objects, ArUco markers provide a starting point that eliminates an entire class of fragility. Classical methods have their place but for well-defined industrial tasks with controlled items, fiducial markers deliver determinism and speed. That's worth an afternoon of printing markers.