---
layout: single
title: "Interfacing wih Moveit"
date: 2026-03-14
classes: 
  - wide
author_profile: false
---

# Interfacing with MoveIt2

here we'll discuss the five ways to intterface with MoveIt2

**1. MoveGroup Action** - Production-grade ROS 2 action interface  
**2. Pure MoveItPy** - Python bindings to MoveIt's C++ core  
**3. ROS 2 Services** - Low-level service calls  
**4. ROS 2 Topics** - Pub/sub monitoring  
**5. pyMoveIt2** - Community wrapper library

Each approach had it pros and cons.  

## Method 1: MoveGroup Action 
### How It Works

The action-based approach treats MoveIt as a separate service. the script becomes a client sending goals to a running `move_group` node.

```python
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import MotionPlanRequest, Constraints, JointConstraint
from math import radians
import rclpy

rclpy.init()
node = rclpy.create_node("moveit_action_example")
action_client = ActionClient(node, MoveGroup, "/move_action")

# Wait for server
if not action_client.wait_for_server(timeout_sec=5):
    raise RuntimeError("Action server not available")

# Build request
goal = MoveGroup.Goal()
goal.request = MotionPlanRequest()
goal.request.group_name = "arm_1"
goal.request.max_velocity_scaling_factor = 0.1
goal.request.num_planning_attempts = 10
goal.request.allowed_planning_time = 5.0

# Define joint constraints
constraints_list = []
for i in range(1, 7):
    constraint = JointConstraint()
    constraint.joint_name = f"arm_1_joint_{i}"
    constraint.weight = 1.0
    
    if i == 1:
        constraint.position = radians(50)
        constraint.tolerance_above = radians(5)
        constraint.tolerance_below = radians(5)
    else:
        constraint.position = 0.0
        constraint.tolerance_above = radians(1)
        constraint.tolerance_below = radians(1)
    
    constraints_list.append(constraint)

goal.request.goal_constraints.append(
    Constraints(joint_constraints=constraints_list)
)

# Execute
future = action_client.send_goal_async(goal)
rclpy.spin_until_future_complete(node, future, timeout_sec=5)
goal_handle = future.result()

if goal_handle.accepted:
    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future, timeout_sec=30)
    result = result_future.result()
    
    if result.result.error_code.val == 1:
        print("✅ Motion succeeded")
    else:
        print(f"❌ Failed: {result.result.error_code.val}")

rclpy.shutdown()
```

**Critical limitation:** Cannot dynamically add collision objects. The planning scene must be managed externally. Also no cartesian pose goals.

## Method 2: Pure MoveItPy 

### Configuration Requirements

Unlike the action interface, MoveItPy requires explicit configuration:

```yaml
# moveit_py_params.yaml
robot_description: "path/to/urdf"
robot_description_semantic: "path/to/srdf"
robot_description_kinematics: {arm_1: {kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin}}
planning_pipelines: {pipeline_names: ['ompl'], ompl: {planning_plugin: ompl_interface/OMPLPlanner}}
```

### Implementation

```python
from moveit.planning import MoveItPy, PlanRequestParameters
from moveit.core.robot_state import RobotState
from math import radians
import rclpy

config_path = "/workspace/moveit_py_params.yaml"

rclpy.init()
moveit = MoveItPy(
    node_name="moveit_py_example",
    launch_params_filepaths=[config_path]
)

arm = moveit.get_planning_component("arm_1")
arm.set_start_state_to_current_state()

# Create goal state
robot_state = RobotState(moveit.get_robot_model())
robot_state.joint_positions = {
    "arm_1_joint_1": radians(50),
    "arm_1_joint_2": 0,
    "arm_1_joint_3": 0,
    "arm_1_joint_4": 0,
    "arm_1_joint_5": 0,
    "arm_1_joint_6": 0,
}
arm.set_goal_state(robot_state=robot_state)

# Plan with parameters
params = PlanRequestParameters(moveit)
params.max_velocity_scaling_factor = 0.1

plan_result = arm.plan(parameters=params)
if plan_result:
    moveit.execute(plan_result.trajectory)
    print("✅ Execution completed")
else:
    print("❌ Planning failed")

rclpy.shutdown()
```


## Method 3: ROS 2 Services 

Services provide granular control but is synchronous and blocking.

```python
from moveit_msgs.srv import GetMotionPlan, ExecuteKnownTrajectory
import rclpy

node = rclpy.create_node("service_example")

# Create service clients
plan_client = node.create_client(GetMotionPlan, '/plan_kinematic_path')
exec_client = node.create_client(ExecuteKnownTrajectory, '/execute_trajectory')

# Wait for services
plan_client.wait_for_service(timeout_sec=5)
exec_client.wait_for_service(timeout_sec=5)

# Build planning request
request = GetMotionPlan.Request()
request.motion_plan_request.group_name = "arm_1"
# ... (50+ lines of constraint building)

# Call planning service
future = plan_client.call_async(request)
rclpy.spin_until_future_complete(node, future)
response = future.result()

if response.motion_plan_response.error_code.val != 1:
    print(f"Planning failed: {response.motion_plan_response.error_code.val}")
else:
    # Build execution request
    exec_request = ExecuteKnownTrajectory.Request()
    exec_request.trajectory = response.motion_plan_response.trajectory
    
    # Call execution service
    exec_future = exec_client.call_async(exec_request)
    rclpy.spin_until_future_complete(node, exec_future)
```

## Method 4: ROS 2 Topics 

Topics are read-only for motion planning. This is critical to add so we can add online collision checks.

```python
from sensor_msgs.msg import JointState
import rclpy

node = rclpy.create_node("topic_monitor")

def joint_callback(msg):
    for i, name in enumerate(msg.name):
        if "arm_1" in name:
            print(f"{name}: {msg.position[i]:.3f} rad")

subscription = node.create_subscription(
    JointState,
    '/joint_states',
    joint_callback,
    10
)

rclpy.spin(node)
```

**Key topics for monitoring:**
- `/joint_states` - Current robot configuration
- `/tf` - Transform tree updates
- `/move_group/display_planned_path` - Visualization of planned trajectories
- `/move_group/status` - Planning pipeline status


## Method 5: pyMoveIt2 

The community wrapper from [AndrejOrsula](https://github.com/AndrejOrsula/pymoveit2) simplifies common operations:

```bash
pip install pymoveit2
```

```python
from pymoveit2 import MoveIt2
from math import radians
import rclpy

rclpy.init()
node = rclpy.create_node("pymoveit2_example")

moveit2 = MoveIt2(
    node=node,
    joint_names=["arm_1_joint_1", "arm_1_joint_2", "arm_1_joint_3",
                 "arm_1_joint_4", "arm_1_joint_5", "arm_1_joint_6"],
    base_link_name="base_link",
    end_effector_name="tool_link"
)

# Move to joint configuration
moveit2.move_to_configuration(
    [radians(50), 0, 0, 0, 0, 0],
    velocity_scaling=0.1
)
moveit2.wait_until_executed()

# Gripper control
moveit2.gripper_open()
moveit2.wait_until_executed()

rclpy.shutdown()
```


**Trade-off:** The library wraps MoveGroup actions internally, so you inherit action-interface limitations (no dynamic obstacles, no multi-pipeline planning). For production systems requiring these features, migrating to MoveItPy becomes necessary.

## Architecture Comparison

### Process Models

**MoveGroup Action:**
```
 Script ──ROS 2 Actions──> move_group node (200MB)
                                       ↓
                                    Planning + Execution
```

**MoveItPy:**
```
Script  ──In-Process──> MoveIt Core
                                     ↓
                                  Planning + Execution
```

**pyMoveIt2:**
```
Script  ──Wrapper──> MoveGroup Actions ──> move_group node
                                                       ↓
                                                   Planning + Execution
```




## Decision Framework

### MoveGroup Action best for:
- Deploying to production (robustness critical)
- Running multiple concurrent motion scripts
- Working with pre-configured planning scenes
- System reliability > convenience

### Pure MoveItPy best for:
- Dynamically adding/removing obstacles
- Comparing multiple planning algorithms
- Learning MoveIt architecture
- Need full planning scene control
- Latency is critical (<5ms)

### pyMoveIt2 When:
- Rapid prototyping required
- Need integrated gripper control
- Simplicity > flexibility
- Community library acceptable

### Use ROS Services When:
- Building custom planning orchestration
- Inserting logic between plan and execution
- Advanced use cases only

### Use ROS Topics When:
- Monitoring system state only
- Building dashboards/telemetry
- Never for commanding motion


MoveItPy's architecture eliminates IPC overhead. For high-frequency replanning (>10 Hz), this difference compounds significantly. it is alsoo easy to impliment for testing the framework which is why i will be using it for testing. 
