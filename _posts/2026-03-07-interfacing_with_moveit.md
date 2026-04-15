---
layout: single
title: "Interfacing with MoveIt2"
header:
  teaser: /assets/images/posts/interfacing_moveit.png
date: 2026-03-07
classes: 
  - wide
author_profile: false
---

# Interfacing with MoveIt2

how should we interface with MoveIt2 for dual-arm setups? The choice will have major consequences as it determines how the planning scene is managed, whether dynamic collision objects are possible, whether two arms can execute concurrently etc. 

Five interfaces were considered. Here is what each does, what was tried, and why MoveItPy was chosen.

**1. MoveGroup Action**: Production-grade ROS2 action interface  
**2. Pure MoveItPy**: Python bindings to MoveIt2's C++ core  
**3. ROS2 Services**: Low-level service calls  
**4. ROS2 Topics**: Pub/sub monitoring  
**5. pyMoveIt2**: Community wrapper library

---

## Method 1: MoveGroup Action

### How It Works

The action-based approach treats MoveIt2 as a separate service. The script becomes a client sending goals to a running `move_group` node.

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
        print("Motion succeeded")
    else:
        print(f"Failed: {result.result.error_code.val}")

rclpy.shutdown()
```

This was the first interface i tried. It works correctly for single-arm motion. The two limitations that ended the evaluation:


## Major flaw
**No concurrent execution from the same action server.** Both arms dispatching goals to a single `move_group` action server produces serialised execution; the second goal queues behind the first. Parallel execution requires two independent `move_group` nodes, one per arm, with the namespace and state management consequences that involves.


---

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
    print("Execution completed")
else:
    print("Planning failed")

rclpy.shutdown()
```

MoveItPy embeds the planning stack directly in-process via pybind11. There is no separately running `move_group` node; the planner, planning scene, and execution manager all live in the same Python process. The planning scene is a live in-memory object: a collision object written through the Python API is visible to the next `plan()` call immediately, with no serialisation or inter-process communication.

---

## Method 3: ROS2 Services

Services provide granular control but are synchronous and blocking.

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

The service interface is the most verbose of the five approaches. It is appropriate for custom orchestration layers that need to insert logic between planning and execution, for example validating a planned trajectory against an external constraint before dispatching it. For MARS, `TrajectoryProxy` already occupies that role and is cleaner when composed with MoveItPy's planning API.

---

## Method 4: ROS2 Topics

Topics are read-only for motion planning. Useful for monitoring and the foundation for any runtime state checks.

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
- `/joint_states`: current robot configuration (published by `JointStateManager`)
- `/tf`: transform tree updates
- `/move_group/display_planned_path`: visualisation of planned trajectories
- `/move_group/status`: planning pipeline status

Topics cannot be used to command motion. They are diagnostic and monitoring infrastructure.

---

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

This library was evaluated as a rapid-prototyping path. The API is significantly simpler than raw MoveItPy for basic single-arm moves, and the integrated gripper control is convenient. The decisive limitation: pyMoveIt2 wraps MoveGroup actions internally, so it inherits the action interface's planning scene constraint. MARS requires writing the workspace platform collision object to each of three independent planning scenes at startup. That is not possible through pyMoveIt2 without bypassing its abstraction entirely, at which point using MoveItPy directly is the cleaner choice.


---

## Architecture Comparison

### Process Models

**MoveGroup Action:**
```
Script ──ROS2 Actions──> move_group node (200MB)
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

---

## Decision Framework

### MoveGroup Action best for:
- Deploying to production (robustness critical)
- Running multiple concurrent motion scripts
- Working with pre-configured planning scenes
- System reliability > convenience

### Pure MoveItPy best for:
- Dynamically adding/removing obstacles
- Comparing multiple planning algorithms
- Need full planning scene control
- Latency is critical

### pyMoveIt2 when:
- Rapid prototyping required
- Need integrated gripper control
- Simplicity > flexibility
- Community library acceptable

### ROS2 Services when:
- Building custom planning orchestration
- Inserting logic between plan and execution
- Advanced use cases only

### ROS2 Topics when:
- Monitoring system state only
- Building dashboards/telemetry
- Never for commanding motion

---

## Why MARS Uses MoveItPy

Two MARS requirements eliminated the alternatives:

**Dynamic planning scene management.** The workspace platform collision object must be added to the planning scene at startup. With MoveItPy, this is a direct write to the in-process scene via `read_write()` context manager, visible to the next `plan()` call immediately. The action interface and pyMoveIt2 require an external service call to a separately running `move_group` node, which introduces a race condition at startup and couples the script's lifecycle to the node's.

**Concurrent execution across multiple instances.** `MoveItPy.execute()` releases the Python GIL during trajectory dispatch. Three independent MoveItPy instances (`moveit_py_arm1`, `moveit_py_arm2`, and `moveit_py_dual`) each run their own background executor thread with their own controller action clients. Both arms can call `execute()` concurrently without blocking each other. Achieving the same with the action interface requires two separately running `move_group` nodes with all the namespace and state management complexity that entails.

MoveItPy's architecture eliminates IPC overhead. The planning scene is an in-memory object in the same process; collision objects written through the Python API appear in the next plan without serialisation. For the coordination tests where planning overhead must be minimised so that timing measurements reflect coordination behaviour rather than planning latency, this matters. 