---
layout: single
title: "Camera Calibration"
header:
  teaser: /assets/images/posts/camera_calibration.png
date: 2026-02-10
classes: wide
author_profile: false
---


## The need for camera intrinsics and extrinsics 

Your brain doesn't need a manual to understand that parallel lines meet at the horizon, or that a distant car is smaller than it appears. computer vision? Not so lucky.
When a camera captures the 3D world onto a 2D sensor, information gets lost. Lenses bend light in unpredictable ways. Pixels don't map cleanly to real-world coordinates. Without knowing _how_ your camera distorts reality, any attempt to estimate position or reconstruct 3D scenes is built on shaky ground.

That's where camera calibration comes in and why intrinsic parameters are needed for pose estimation.

![Niryo_camera](/mars_ned2/assets/images/camera.png){: .align-center}

## The Two Faces of Camera Parameters
Camera calibration splits into two distinct problems:
**Intrinsic parameters** describe the cameras internal geometry. Think focal length, sensor dimensions, optical center, and lens distortion. These stay constant unless you swap lenses or change zoom.
**Extrinsic parameters** describe where the camera sits in the world, specifically its position and orientation relative to the scene. These change every time the camera moves.
The projection from 3D world point to 2D pixel combines both:
```
s · p = K [R|t] P_w
```
Where:
- `K` = intrinsic matrix (what we're about to dissect)
- `[R|t]` = rotation and translation (extrinsics/pose)
- `P_w` = 3D point in world coordinates
- `p` = resulting 2D pixel
Without `K`, you can't solve for `[R|t]`. They're mathematically inseparable.
## Inside the Intrinsic Matrix
The intrinsic matrix `K` captures four critical properties:
```
K = [f_x    0    c_x]
    [0    f_y    c_y]
    [0      0      1]
```
**Focal lengths** `f_x`, `f_y`): How strongly the lens bends light, measured in pixels. For industrial cameras, you can approximate this from specs:
```
f_x = f_mm / pixel_size_mm
```
Or derive from field of view.
**Principal point** `c_x`, `c_y`): Where the optical axis pierces the image plane. Ideally the image center, but manufacturing tolerances mean it rarely is.
**Skew coefficient** (typically zero): Accounts for non-rectangular pixels. Modern cameras have square pixels, so this vanishes.
**Distortion coefficients**: Radial and tangential distortion parameters that describe how lenses warp straight lines into curves. Critical for wide-angle lenses.
## Why Pose Estimation Breaks Without Intrinsics
Pose estimation determines where your camera is relative to known 3D points. Algorithms like `solvePnP` need both:
- Observed 2D pixel coordinates
- Corresponding 3D world coordinates
- The intrinsic matrix `K`
Here's why `K` is mandatory:
**The projection equation must invert**. Given pixel `(u, v)` and world point `(X, Y, Z)`, you're solving for rotation `R` and translation `t`. But the equation mixes intrinsics and extrinsics. Without knowing `f_x`, `f_y`, `c_x`, and `c_y`, there are infinite solutions.
**Distortion scrambles correspondences**. Radial distortion bends straight lines. If you measure pixel coordinates without undistorting them first, your 3D-to-2D correspondences are wrong. The pose solver will fail or return garbage.
**Scale ambiguity explodes**. Focal length directly determines depth scale. A close object and a distant object can project to the same image size. Without `f_x` and `f_y`, depth becomes meaningless.


## Calibration
Use a checkerboard or calibration target with known geometry. OpenCV's `calibrateCamera` solves for intrinsics by:

![camera calibration](/mars_ned2/assets/images/camera_calibration.png)

1. Detecting corners in multiple images
2. Computing homographies (planar transformations)
3. Running nonlinear optimization to minimise reprojection error

You get back `K` and distortion coefficients. Save these as YAML or NPZ files, as they are reusable until hardware changes.

the values can then be used to

### 1: Undistort Images
Apply distortion correction using the coefficients from calibration.

### 2: Estimate Pose
Feed undistorted image points, known 3D coordinates, and `K` into `solvePnP`. It returns rotation `R` and translation `t`, representing your camera's pose.

### 3: Validate 
Project the 3D points back to 2D using your estimated pose and `K`. Measure reprojection error. Low error means your calibration and pose are solid.


## When to come back to this and recaalibrate your camera
Poor calibration manifests as:
- **Jittery pose estimates** that jump frame-to-frame
- **Warped 3D reconstructions** where parallel lines diverge
- **Depth errors** that compound over distance




