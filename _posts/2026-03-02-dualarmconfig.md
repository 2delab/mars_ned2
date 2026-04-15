---
layout: single
title: "Dual Arm MoveIt Config"
header:
  teaser: /assets/images/posts/dual_arm_config.png
date: 2026-03-02
classes: 
  - wide
author_profile: false
---

# Building a Dual-Arm MoveIt2 Configuration

The goal of this step was a single MoveIt2 configuration package (`niryo_ned2_dual_arm_moveit_config`) that treats both Niryo NED2 arms as one robot with three planning groups: `arm_1`, `arm_2`, and `dual`. Everything downstream depends on this package: the planning scene, the collision matrix, the controller mappings, the kinematics solvers. Getting the naming and structure right here determines whether any of the later coordination work is possible.

---

## The URDF: One World, Two Arms

The first decision was how to represent two robots in a single URDF file.

**Option A: Two separate base links with independent chains.** Each arm gets its own root link with no spatial relationship between them. MoveIt2 can plan for each arm independently but treats them as geometrically unrelated objects. There is no shared planning scene, no inter-arm collision checking, and no way to express the physical relationship between the two bases. Rejected.

**Option B: One `world` fixed frame, two independently-actuated subtrees.** Both arms attach to a common `world` link via fixed joints. MoveIt2 builds one kinematic model from the single URDF root, placing both arms in the same coordinate frame. Inter-arm collision geometry is computed from their known spatial relationship. This is the approach that makes a shared planning scene possible.

The `world` link is a coordinate reference. Its sole purpose is to give MoveIt2 a common root from which it can compute the transform chain to every link of both arms simultaneously. Without it, the planner has no basis for determining whether `arm_1_wrist_link` and `arm_2_elbow_link` are about to intersect.

---

## Constructing the URDF with Xacro Macros

Rather than defining the full 22-link kinematic chain twice (once per arm), the URDF uses a Xacro macro. The NED2 description package provides the single-arm definition; a `ned2_robot` macro wraps it with parameterised prefix and position:

```xml
<!-- niryo_ned2_dual_arm.urdf.xacro -->
<?xml version="1.0"?>
<robot name="niryo_ned2_dual_arm" xmlns:xacro="http://www.ros.org/wiki/xacro">

  <xacro:include filename="$(find niryo_ned_description)/urdf/ned2/niryo_ned2_param.urdf.xacro"/>
  <xacro:include filename="$(find niryo_ned_description)/urdf/tools/niryo_gripper1.urdf.xacro"/>

  <!-- Macro: instantiate a single NED2 arm at a given position and orientation -->
  <xacro:macro name="ned2_robot" params="prefix base_x base_y base_z base_yaw">

    <link name="${prefix}base_link"> ... </link>
    <!-- 6 revolute joints: ${prefix}joint_1 through ${prefix}joint_6 -->
    <!-- shoulder_link, arm_link, elbow_link, forearm_link, wrist_link, hand_link -->
    <!-- tool_link, camera_link, led_ring_link -->
    <xacro:gripper_1 prefix="${prefix}"/>

    <joint name="${prefix}base_mount" type="fixed">
      <parent link="world"/>
      <child  link="${prefix}base_link"/>
      <origin xyz="${base_x} ${base_y} ${base_z}" rpy="0 0 ${base_yaw}"/>
    </joint>

  </xacro:macro>

  <!-- Common root -->
  <link name="world"/>

  <!-- Instantiate both arms -->
  <xacro:ned2_robot prefix="arm_1_" base_x="-0.40" base_y="0" base_z="0" base_yaw="0"/>
  <xacro:ned2_robot prefix="arm_2_" base_x="0.40"  base_y="0" base_z="0" base_yaw="${PI}"/>

</robot>
```

### Parameters

**`prefix`** namespaces every link and joint name produced by the macro. `arm_1_` produces `arm_1_base_link`, `arm_1_joint_1`, `arm_1_wrist_link`, and so on. `arm_2_` produces the equivalent set. This is the naming convention that propagates through the entire stack: the SRDF planning groups, the `JointStateManager` prefix translation, and the `TrajectoryProxy` prefix stripping all depend on this exact convention.

**`base_yaw="${PI}"` on arm_2** rotates the second arm 180° around the vertical axis. Both arms face inward toward the shared workspace centre. Without this, both arms would face the same direction, their reach envelopes would not overlap in a useful working plane, and coordinated tasks requiring both arms to approach the same object from opposite sides would be geometrically impossible.

**`base_x="-0.40"` / `base_x="0.40"`** places the arm bases 800 mm apart (400 mm each side of the world origin). This matches the physical lab setup. The value is not arbitrary: at 800 mm separation the reach envelopes overlap by approximately 180 mm at the workspace centre, providing enough shared volume for handoff and cooperative manipulation tasks while keeping the arms clear of each other at their home positions.

**Xacro macros over copy-paste**: the full NED2 kinematic chain is 22 links, 12 revolute joints, 4 passive gripper joints, mesh references, inertial properties, and joint limits. Defining it once in a macro and instantiating it twice means a mesh path change, joint limit correction, or collision geometry update only needs making in one place. 

### Validation

```bash
# Check the URDF parses correctly
xacro niryo_ned2_dual_arm.urdf.xacro > /tmp/dual_arm_check.urdf
check_urdf /tmp/dual_arm_check.urdf

# Visualise the kinematic tree
urdf_to_graphviz /tmp/dual_arm_check.urdf

# Render in RViz with joint sliders
ros2 launch urdf_tutorial display.launch.py model:=/tmp/dual_arm_check.urdf
```

Both arms rendered correctly in RViz: 800 mm apart, facing each other, all 22 links visible, joint sliders actuating each arm independently. The TF tree showed a single root (`world`) branching to `arm_1_base_link` and `arm_2_base_link`, confirming the shared coordinate frame.

---

## MoveIt Setup Assistant

With a valid dual-arm URDF, the Setup Assistant generates the semantic configuration: planning groups, collision matrix, kinematics solvers, and controller mappings. This is where the URDF's structural choices get translated into MoveIt2 behaviour.

```bash
ros2 launch moveit_setup_assistant setup_assistant.launch.py
```

Load `niryo_ned2_dual_arm.urdf.xacro`. The assistant parses the file and extracts all 44 links (22 per arm) and all 24 joints (12 per arm).

### Step 1: Self-Collision Matrix

The assistant runs a sampling pass: it generates thousands of random joint configurations for the full 44-link model and tests which link pairs are ever in contact. Link pairs that are always in contact (adjacent links, physically connected) or geometrically impossible to bring into contact (distant links on the same chain) are candidates for disabling. Disabling a pair means FCL will never run a narrowphase check on it, reducing the per-query cost.

For the MARS SRDF, the pass produced three categories of disabled pairs:

**Adjacent links within each arm** (physically connected and always in contact by design):
```xml
<disable_collisions link1="arm_1_arm_link"     link2="arm_1_shoulder_link" reason="Adjacent"/>
<disable_collisions link1="arm_1_arm_link"     link2="arm_1_elbow_link"    reason="Adjacent"/>
<disable_collisions link1="arm_1_forearm_link" link2="arm_1_wrist_link"    reason="Adjacent"/>
<!-- and so on for all kinematically connected pairs -->
```

**Geometrically unreachable pairs within each arm** (links so far apart in the kinematic chain that no joint configuration can bring them into contact):
```xml
<disable_collisions link1="arm_1_arm_link" link2="arm_1_base_link" reason="Never"/>
<disable_collisions link1="arm_1_arm_link" link2="arm_1_hand_link" reason="Never"/>
```

**The shared mounting base (the only cross-arm disabled pair):**
```xml
<disable_collisions link1="arm_1_base_link" link2="arm_2_base_link" reason="Adjacent"/>
```

This last entry is the key result of the sampling pass for a dual-arm system. Both arms are bolted to the same physical platform; their base links are always in contact. Leaving this pair enabled would cause the planner to detect a permanent collision at the bases and reject every configuration. Disabling it removes the false positive.

Every other combination of an `arm_1` link with an `arm_2` link, all 100 cross-arm pairs excluding the bases, remains active in the collision matrix. This is what makes inter-arm collision checking automatic: there is no special logic for "check arm_1 against arm_2"; the ACM simply does not have `ALWAYS_ALLOW` entries for those pairs, so FCL queries them at every sampled state.

### Step 2: Planning Groups

Five groups were defined. The names were chosen to match the `arm_1_` / `arm_2_` prefix convention from the URDF, which propagates to the `JointStateManager` and `TrajectoryProxy`:

| Group | Type | Joints | Purpose |
|---|---|---|---|
| `arm_1` | Joint chain | `arm_1_joint_1` … `arm_1_joint_6` | Single-arm planning, async mode, Cartesian goals |
| `arm_2` | Joint chain | `arm_2_joint_1` … `arm_2_joint_6` | Single-arm planning, async mode, Cartesian goals |
| `dual` | Subgroup composite | `arm_1` + `arm_2` | 12-DOF joint planning, sync mode |
| `arm_1_gripper` | Joint chain | `arm_1_joint_base_to_mors_1`, `arm_1_joint_base_to_mors_2` | Gripper open/close |
| `arm_2_gripper` | Joint chain | `arm_2_joint_base_to_mors_1`, `arm_2_joint_base_to_mors_2` | Gripper open/close |

The `dual` group is not a joint chain; it is a composite of two subgroups. MoveIt2 assembles a 12-DOF joint space from the union of `arm_1` and `arm_2`'s joints. Planning against `dual` searches this combined space, which is what enables planning-time inter-arm collision checking during synchronised motion.


### Step 3: Kinematics Solvers

KDL (Kinematic and Dynamics Library) is configured independently for each single-arm group:

```yaml
# kinematics.yaml
arm_1:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.005
arm_2:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.005
```

No IK solver is configured for the `dual` group. This is intentional: the `dual` group plans in joint space, where goals are expressed as a `RobotState` with explicit joint positions for both arms. IK is only needed when converting a Cartesian pose to joint angles, which happens at the single-arm level. There is no single IK formulation that can simultaneously satisfy two independent Cartesian goals in a 12-DOF system without additional constraints.

### Step 4: Controllers

`moveit_controllers.yaml` maps MoveIt2's trajectory dispatcher to the hardware action servers. Each arm gets its own entry:

```yaml
controller_names:
  - arm_1_controller
  - arm_2_controller

arm_1_controller:
  action_ns: follow_joint_trajectory
  type: FollowJointTrajectory
  default: true
  joints:
    - arm_1_joint_1
    - arm_1_joint_2
    - arm_1_joint_3
    - arm_1_joint_4
    - arm_1_joint_5
    - arm_1_joint_6

arm_2_controller:
  action_ns: follow_joint_trajectory
  type: FollowJointTrajectory
  default: true
  joints:
    - arm_2_joint_1
    - arm_2_joint_2
    - arm_2_joint_3
    - arm_2_joint_4
    - arm_2_joint_5
    - arm_2_joint_6
```


### Step 5: Generate Package

```bash
# Output: niryo_ned2_dual_arm_moveit_config/
# Contains: niryo_ned2_dual_arm.srdf, kinematics.yaml,
#           moveit_controllers.yaml, ros2_controllers.yaml,
#           joint_limits.yaml, moveit.rviz, launch/*.py
```

### Verification

```bash
colcon build --packages-select niryo_ned2_dual_arm_moveit_config
ros2 launch niryo_ned2_dual_arm_moveit_config demo.launch.py
```

![Dual arm moveit config](/mars_ned2/assets/images/dual_arm_moveit.png)

RViz displayed both arms correctly positioned. The demo confirmed:
- Independent arm planning via `arm_1` and `arm_2` groups: 1–2 seconds per arm
- The `dual` group planning both arms simultaneously: 2–5 seconds
- The planner correctly rejecting configurations where padded link volumes overlapped
- The ACM correctly suppressing the false positive at the shared base

---

## What This Configuration Does Not Provide

The Setup Assistant produces a complete and correct MoveIt2 configuration package. What it does not produce is the infrastructure to connect MoveIt2 to the Niryo hardware.

**The planning scene requires a single `/joint_states` topic with prefixed joint names.** The NED2 hardware drivers publish to `/arm_1/joint_states` and `/arm_2/joint_states` with unprefixed names. There is no configuration in the generated package that bridges this gap. That is `JointStateManager`.

**The trajectory dispatcher produces goals with prefixed joint names.** The hardware action servers expect unprefixed names. There is no configuration in the generated package that strips the prefix before dispatch. 


