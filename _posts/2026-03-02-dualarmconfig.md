---
layout: single
title: "Dual Arm MoveIt Config"
header:
  teaser: /assets/images/photo.jpg
date: 2026-03-02
classes: 
  - wide
author_profile: false
---

# Building a Dual-Arm MoveIt 2 Configuration

## The Challenge

The task required two Niryo Ned2 arms working on a shared work envelope without colliding. The best approach(read previous blog): combine both robots into a single URDF, configure through MoveIt Setup Assistant, and enable collision-aware planning for simultaneous operation.


## Starting Point: System Geometry

Initial assumption:  Two Ned2 robots, positioned 80 cm apart, facing each other over a sorting table. 


**Why unified configuration?** Separate MoveIt configs require external coordination, manual collision checking between arms, and state polling from both planners. A unified config lets MoveIt handle arm-to-arm collisions natively—any planner (OMPL, Trajopt, etc.) sees both arms in one planning scene.

## Constructing the Dual-Arm URDF

### Extracting the Base URDF

```bash
ros2 pkg prefix ned2_description
# Output: /opt/ros/humble/share/ned2_description

cp -r /opt/ros/humble/share/ned2_description ~/ws_dual_arm/src/
```

Processing the Xacro to plain URDF:
```bash
xacro ned2_description/urdf/ned2.urdf.xacro > ned2_single.urdf
```

The structure: `world` → `base_link` → kinematic chain (`shoulder_link` → `arm_link_1` → ... → `end_effector_link`). Approximately 400 lines of collision geometry, visuals, inertials, and joint definitions.



### Assembly Strategy

**Option A:** Two separate base links with independent chains. Problem: MoveIt treats them as unrelated objects; collision checking lacks context.

**Option B (chosen):** One world frame with two independently-actuated subtrees. This maintains kinematic relationships for proper collision checking.

Created `ned2_dual_arm.urdf.xacro`:

```xml
<?xml version="1.0" ?>
<robot name="dual_ned2" xmlns:xacro="http://www.ros.org/wiki/xacro">
  <xacro:include filename="$(find ned2_description)/urdf/ned2_defs.xacro" />
  
  <link name="world" />
  
  <!-- LEFT ARM: offset -40cm -->
  <joint name="left_base_mount" type="fixed">
    <parent link="world" />
    <child link="left_base_link" />
    <origin xyz="-0.4 0 0.55" rpy="0 0 0" />
  </joint>
  
  <!-- Left arm link/joint definitions with "left_" prefix -->
  <link name="left_base_link">
    <inertial>
      <mass value="0.5" />
      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01" />
    </inertial>
    <collision>
      <geometry>
        <mesh filename="package://ned2_description/meshes/collision/base.stl" />
      </geometry>
    </collision>
    <visual>
      <geometry>
        <mesh filename="package://ned2_description/meshes/visual/base.dae" />
      </geometry>
    </visual>
  </link>
  
  <joint name="left_joint_1" type="revolute">
    <parent link="left_base_link" />
    <child link="left_arm_link_1" />
    <axis xyz="0 0 1" />
    <limit lower="-3.05" upper="3.05" effort="10" velocity="2.0" />
  </joint>
  
  <!-- Remaining left arm chain... -->
  
  <!-- RIGHT ARM: offset +40cm, rotated 180° -->
  <joint name="right_base_mount" type="fixed">
    <parent link="world" />
    <child link="right_base_link" />
    <origin xyz="0.4 0 0.55" rpy="0 0 3.14159" />
  </joint>
  
  <!-- Right arm definitions with "right_" prefix... -->
  
  <!-- Table surface -->
  <link name="table">
    <collision>
      <geometry>
        <box size="1.2 0.8 0.05" />
      </geometry>
    </collision>
  </link>
  
  <joint name="table_mount" type="fixed">
    <parent link="world" />
    <child link="table" />
    <origin xyz="0 0 0.55" rpy="0 0 0" />
  </joint>
</robot>
```

### Without extraction

## Step-by-Step Process

1. **Import Parameters**
   - File: `$(find niryo_ned_description)/urdf/ned2/niryo_ned2_param.urdf.xacro`
   - Defines:
	 - PI constant
	 - deg_to_rad conversion factor
	 - Joint limits for each axis (shoulder, arm, elbow, forearm, wrist, hand)
	 - Safety margins and tool distance

2. **Import Gripper Macro**
   - File: `$(find niryo_ned_description)/urdf/tools/niryo_gripper1.urdf.xacro`
   - Provides: gripper_1 macro definition

3. **Define Camera Properties**
   - Local properties for camera visualization added to each robot instance

4. **Create Macro for Single Robot**
   - Parameters:
	 - `prefix`: Namespace for links/joints (e.g., ned1_, ned2_)
	 - `base_x`, `base_y`, `base_z`: Position in world
	 - `base_yaw`: Rotation angle
   - Contains:
	 - 8 links (base, shoulder, arm, elbow, forearm, wrist, hand, tool, camera, led_ring)
	 - 6 revolute joints for arm movement (joints 1-6)
	 - Fixed joints connecting base to world and tool to gripper
	 - Gripper macro call: `<xacro:gripper_1 prefix="${prefix}"/>`
	 - Camera link and joint attached to wrist

5. **Create World Reference**
   - `<link name="world"/>` - Common reference frame for both robots

6. **Instantiate Dual Robots**
   - **Robot 1 (ned1)** - Left robot facing right:
	 ```xml
	 <xacro:ned2_robot prefix="ned1_" base_x="-0.40" base_y="0" base_z="0" base_yaw="0"/>
	 ```
   - **Robot 2 (ned2)** - Right robot facing left (rotated 180°):
	 ```xml
	 <xacro:ned2_robot prefix="ned2_" base_x="0.40" base_y="0" base_z="0" base_yaw="${PI}"/>
	 ```
---

Instead of exctracing and duplicating the entire robot definition, the file uses xacro macros to:
1. Define robot structure once (ned2_robot macro)
2. Instantiate it twice with different parameters
3. Each instance gets namespaced links (e.g., ned1_base_link, ned2_base_link)
4. Separation of 0.8m (0.4m on each side of origin)


Validation:
```bash
urdf_to_graphviz ned2_dual_arm.urdf
ros2 launch urdf_tutorial display.launch.py model:=$(pwd)/ned2_dual_arm.urdf
```

Both arms rendered correctly in RViz: 80 cm apart, facing each other. 

# Next: Create a MoveIt config for the two robots

we will revisit most of the steps we used for the single arm moveit config

## Step 1: Launch MoveIt Setup Assistant

```bash
ros2 launch moveit_setup_assistant setup_assistant.launch.py
```

## Step 2: Load the URDF

- Click **Create New MoveIt Configuration Package**
- Browse to: `src/ned-ros2-driver/niryo_ned_description/urdf/ned2/niryo_ned2_dual_arm.urdf.xacro`
- Click **Load Files**

The Setup Assistant parses the URDF and extracts:
- All links (base_link, shoulder_link, arm_link, etc.) × 2 (ned1_ and ned2_ prefixes)
- All joints (6 arm joints + gripper joints) × 2
- Collision meshes and visual models

## Step 3: Generate Self-Collision Matrix

- Go to **Self-Collisions** pane
- Set sampling density (higher = more accurate, takes longer)
- Click **Generate Collision Matrix**

**Output:** The system tests thousands of random robot poses to identify which link pairs can safely disable collision checking (adjacency, never colliding, etc.)

**Result saved:** `<disable_collisions>` tags in the SRDF


## Step 4: Add Planning Groups

This is where you define which joints/links MoveIt will control together. For dual-arm setup, create 5 groups:

1. **ned1_arm**
    - Kinematics solver: `kdl_kinematics_plugin/KDLKinematicsPlugin`
    - Joints: arm_1_joint_1 through arm_1_joint_6

2. **ned1_gripper**
    - Kinematics solver: None
    - Joints: arm_1_joint_base_to_mors_1, arm_1_joint_base_to_mors_2

3. **ned2_arm** (same as ned1_arm but with arm_2_ prefix)

4. **ned2_gripper** (same as ned1_gripper but with arm_2_ prefix)

5. **dual_arm** (composite group)
    - Type: Subgroup
    - Subgroups: arm_1_arm + arm_2_arm
    - Purpose: Plan both arms simultaneously

**Result saved in SRDF:** `<group>` tags (lines 12-41 in existing config)


## Step 5: Label End Effectors

- Go to **End Effectors** pane
- **Ned1 Gripper:**
  - Name: `arm_1_gripper`
  - Group: `arm_1_gripper`
  - Parent Link: `arm_1_hand_link`
  - Parent Group: `arm_1_arm`
- **Ned2 Gripper:** (same but with ned2_ prefix)

**Result saved:** `<end_effector>` tags in SRDF (lines 74-75)

## Step 6: ros2_control URDF Modification 

- Adds command/state interface tags for joints
- Select command interfaces (default: `position`)
- Select state interfaces (default: `position`)

**Result:** Modified URDF with control tags

## Step 7: ROS 2 Controllers

Define low-level controllers that drive the hardware:
- JointTrajectoryController for arm joints
- GripperActionController for gripper joints
- Repeat for both arm_1 and arm_2

## Step 8: MoveIt Controllers

Define controllers that MoveIt uses to execute trajectories:
- FollowJointTrajectory type for arms
- Gripper Command type for grippers
- Must match ROS 2 controller names

**Result saved:** `config/moveit_controllers.yaml`


## Step 9: Launch Files Review

View the list of auto-generated launch files (demo, move_group, rviz, etc.)

## Step 13: Author Information

Enter your name and email.

## Step 14: Generate Package

- Click **Configuration Files**
- Select output directory: `src/ned-ros2-driver/niryo_ned_moveit_configs/`
- Name: `niryo_ned2_dual_arm_moveit_config`
- Click **Generate Package**

## Output Files Generated

| File | Purpose |
|------|---------|
| `.setup_assistant` | Metadata (URDF path, author info) |
| `niryo_ned2_dual_arm.srdf` | Semantic Robot Description (groups, poses, collisions) |
| `kinematics.yaml` | IK solver config for each arm |
| `moveit_controllers.yaml` | How MoveIt executes trajectories |
| `ros2_controllers.yaml` | Low-level controller config |
| `joint_limits.yaml` | Joint velocity/effort limits |
| `moveit.rviz` | RViz visualization config |
| `launch/*.py` | Launch files (demo, move_group, etc.) |
| `CMakeLists.txt` & `package.xml` | ROS 2 package configuration |

## Key Differences for Dual-Arm

The dual-arm setup adds complexity:
- Separate planning groups for each arm (ned1_arm, ned2_arm)
- Composite group (dual_arm) that combines both
- Two grippers with separate end effector definitions
- Separate kinematics for each arm
- Collision matrix accounts for inter-robot collisions (ned1 links vs ned2 links)

## Testing the Configuration

### Build and Launch

```bash
cd ~/ws_dual_arm
colcon build --packages-select niryo_ned2_dual_moveit_config

ros2 launch niryo_ned2_dual_moveit_config demo.launch.py

```
![Dual arm moveit config](/mars_ned2/assets/images/dual_arm_moveit.png)


RViz displayed both arms correctly positioned with the table surface.
Results confirmed:
-  Independent arm planning: 1-2 seconds per arm
-  Collision detection working between arms
-  Planner correctly rejects invalid goal states


## Key Takeaways

**What worked:**
- Three-tier planning groups (left_arm, right_arm, dual_arm) enable flexible planning strategies
- OMPL handles 14 DoFs with appropriate parameter tuning




