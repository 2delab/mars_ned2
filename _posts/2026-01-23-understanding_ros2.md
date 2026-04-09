---
layout: single
title: "Understanding ROS2 "
date: 2026-01-23
classes : wide
author_profile: false
---

## What is ROS2?

ROS2 is not an operating system, not firmware, not a standalone application. Instead, it's **middleware**—the connective tissue that enables distributed programs to communicate seamlessly, even across multiple machines.

For MARS, this matters because: we need two independent robot control loops, a motion planner, a collision detector, and a perception pipeline all running in parallel. ROS2 provides the standardized communication layer that lets these components talk without tight coupling.

**In practical terms:**
- A set of software libraries and tools for building robot applications
- Hardware abstraction layer between the robots' firmware and your control code
- Message-passing infrastructure for inter-process communication
- Package and dependency management system

The DDS Layer: Why ROS2 
Under the hood, it's all **DDS (Data Distribution Service)**
which isn't just a transport but a complete middleware specification with:
- **Discovery**: Nodes find each other automatically via multicast (or discovery servers)
- **QoS Policies**: Fine-grained control over reliability, durability, history, deadlines
- **Real-time capable**: Deterministic timing when configured properly
- **Scalability**: Handles hundreds of nodes without breaking a sweat

The architecture
### Nodes: Your Building Blocks
Every piece of functionality lives in a **node**. A node is just a process that does one thing well. Maybe it reads from a camera. Maybe it plans a path. Maybe it controls a motor.

In MARS, we run separate nodes for each robot's control loop, a unified motion planner, a collision checker, and vision processing. This modularity means we can restart the planner without crashing the hardware interface, or swap the collision detection algorithm without touching the control code.

**Key trait:** Single responsibility—usually just does one thing.

Example:
```python
import rclpy
from rclpy.node import Node

class HelloWorldNode(Node):
    def __init__(self):
        super().__init__('hello_world_node')
        self.get_logger().info('Hello, world from ROS 2!')

def main(args=None):
    rclpy.init(args=args)
    node = HelloWorldNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```


### Topics: Broadcast Communication
Think of a topic as a radio station where any node can tune in. One node publishes data; any number of nodes subscribe. No direct connection needed, no blocking. Perfect for continuous sensor data and state updates.

In MARS:
- **Robot 1** publishes its joint states to `/robot_1/joint_states` at 100Hz
- **Robot 2** publishes its joint states to `/robot_2/joint_states` at 100Hz
- The **motion planner** subscribes to both, always aware of the current configuration
- The **collision detector** subscribes to both, continuously checking for inter-arm conflicts

This decoupling means a slow node won't block the others. If the planner stalls, the joint state publishers keep flowing.

**Key trait:** Asynchronous—no response required.

Example:
```python
class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('publisher')
        self.publisher = self.create_publisher(String, 'chatter', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.count = 0
    
    def timer_callback(self):
        msg = String()
        msg.data = f'Hello World: {self.count}'
        self.publisher.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.count += 1
```

```python
class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__('subscriber')
        self.subscription = self.create_subscription(
            String, 'chatter', self.callback, 10)
    
    def callback(self, msg):
        self.get_logger().info(f'I heard: "{msg.data}"')
```


### Services: Request-Response Communication
A service is a request-response pattern. The client sends a request and waits for the server to respond. Unlike topics (fire-and-forget), services are synchronous and guarantee you get an answer.

In MARS:
- A high-level task planner calls `/request_pick` service to ask robot 1 to pick an object
- Robot 1's gripper controller processes the request and returns success or failure
- The planner waits for this response before proceeding to the next step

Services are ideal for discrete tasks that require confirmation, not continuous streaming.

**Key trait:** Synchronous—client waits for a response.

Example:

```python
# Server
self.service = self.create_service(AddTwoInts, 'add_two_ints', self.handle_service)

def handle_service(self, request, response):
    response.sum = request.a + request.b
    return response

# Client
self.client = self.create_client(AddTwoInts, 'add_two_ints')
request = AddTwoInts.Request()
request.a = 5
request.b = 3
future = self.client.call_async(request)
```
### Actions: Long-Running Goals with Feedback
Actions are built for **long-running tasks** that need real-time feedback and can be cancelled mid-execution. They're more sophisticated than services because they provide progress updates and can be preempted.

In MARS:
- A high-level task sends a `MoveIt2` action goal: "move arm 1 to pose (x, y, z)"
- The motion planner immediately returns feedback: "planning 20% complete", "planning 80% complete"
- Once planned, execution feedback flows: "trajectory 10% complete", "trajectory 50% complete"
- If a collision risk emerges, the high-level task can cancel the goal before completion

This feedback loop is essential for monitoring long-running manipulation tasks and responding to dynamic changes.

**Key trait:** Long-running tasks with progress feedback and cancellation support.

```python
# Action client sending a goal
action_client = ActionClient(self, Fibonacci, 'fibonacci')
goal_msg = Fibonacci.Goal()
goal_msg.order = 10
future = action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_cb)

def feedback_cb(self, feedback_msg):
    self.get_logger().info(f'Progress: {feedback_msg.feedback.sequence}')
```


Ros2 project management
ros demands a structured approach to workspace organization, dependency management, and build processes. 
follow these guidelines to set up and maintain ROS 2 projects.
## Workspace Architecture

The foundation of any ROS 2 project is the workspace. Think of it as your project's container, holding all packages, dependencies, and build artifact

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
```
This simple structure separates source code (`src/`) from build artifacts and installation files. After building, you'll see three additional directories:

- `build/` - Intermediate build files
- `install/` - Compiled packages ready to run
- `log/` - Build and runtime logs

### The Colcon Build System

Colcon is the new and improved ROS 2's build tool, it replaced catkin bringing improved performance and cleaner separation of concerns
Basic build:

```bashs
cd ~/ros2_ws
colcon build
```
For development workflows, symlink installation prevents rebuilding Python packages:
```bash
colcon build --symlink-install
```
Selective building speeds up iteration:
```bash
colcon build --packages-select my_package
```

Environment Setup
```bash
source install/setup.bash
```
Automate this in your shell:
```bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

### Dependency Management with rosdep
automate the process of tracking dependencies with `rosdep` 
```bash
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```
This scans your workspace's `package.xml` files and installs all system dependencies. The `-r` flag continues even if some packages fail, while `-y` auto-confirms installations.

### Creating Packages
ROS 2 supports two build types: `ament_cmake` for C++ and `ament_python` for Python
C++ package:
```bash
cd src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 --node-name my_node my_package
```
Python package with dependencies:
```bash
cd src
ros2 pkg create --build-type ament_python --dependencies rclpy std_msgs --node-name hello_world_node my_hello_world
```

### Package Management Best Practices
**Dependency Declaration**: Always specify dependencies in `package.xml`:
```xml
<depend>rclcpp</depend>
<depend>std_msgs</depend>
<build_depend>octomap</build_depend>
<run_depend>octomap</run_depend>
```
**Clean Builds**: When facing mysterious build issues:

```bash
rm -rf build/ install/ log/
colcon build
```
**Version Control**: Keep `src/` under Git; exclude `build/`, `install/`, and `log/`

## The Ecosystem

ROS2 is more than middleware—it's a growing ecosystem of specialized packages:
- **Nav2**: Advanced navigation stack (mobile robots)
- **MoveIt2**: Motion planning and collision checking for manipulators—critical for MARS
- **Gazebo**: Physics simulation for testing dual-arm scenarios safely
- **RViz2**: 3D visualization of robot state, trajectories, and transforms
- **ros2_control**: Hardware abstraction layer (enables switching between simulation and real hardware)
- **tf2**: Transform management (essential for multi-robot spatial reasoning)

For MARS specifically, **MoveIt2** and **tf2** are the backbone. MoveIt2 handles collision-aware planning for the dual 6-DOF system, while tf2 maintains the transform tree linking both arms' end-effectors to a shared world frame.

## How MARS Uses ROS2

In a concrete MARS workflow:

1. **Hardware Interface Node** (ros2_control): Reads `/joint_commands` from controllers, writes actual joint positions to `/robot_1/joint_states` and `/robot_2/joint_states`

2. **Motion Planning Node** (MoveIt2): Subscribes to both joint state topics, accepts planning requests via action server, checks collision against both arms simultaneously

3. **Collision Detection Node**: Subscribes to both joint states, monitors `/tf` transforms, raises alerts if inter-arm distance drops below safety threshold

4. **High-Level Task Coordinator**: Orchestrates multi-step assembly tasks by sending goals to the motion planner, monitoring feedback, and handling synchronization between arms

5. **Vision Node**: Publishes detected object poses on `/detected_objects`, enabling pick-and-place targeting

This modular architecture is what enables MARS to function as a cohesive system while remaining flexible and testable.



# Setting Up the MARS Workspace

This guide walks through initializing a ROS2 environment for MARS: creating packages, managing dependencies, and structuring the workspace for multi-arm control.

## 1. Initializing Your Workspace

The MARS workspace is where you develop and build all ROS2 packages. The standard structure separates source code from build artifacts.

```bash
mkdir -p ~/mars_ned2/src
cd ~/mars_ned2
```

The `src/` directory holds all source code. The build system automatically generates `build/`, `install/`, and `log/` directories after compilation.

For MARS, you'll typically have packages like:
- `niryo_ned2_interface`: Hardware abstraction for both robots
- `mars_motion_planning`: MoveIt2 configuration and planning
- `mars_collision_checker`: Custom collision detection
- `mars_vision`: ArUco marker detection and object localization
- `mars_task_coordinator`: High-level multi-arm task execution


## 2. Creating Your First Package
In ROS 2, code is organized into packages. This modularity allows for easier debugging and code sharing. Depending on your project requirements, you will likely choose between Python or C++.

### Option A: Python-Based Package
Use this for rapid prototyping and high-level logic.
```bash
cd ~/mars_ned2/src
ros2 pkg create --build-type ament_python --dependencies rclpy std_msgs --node-name my_node my_package
```

### Option B: C++ Based Package
Use this for performance-critical applications and real-time processing.
```bash
cd ~/mars_ned2/src
ros2 pkg create --build-type ament_cmake --dependencies rclcpp std_msgs --node-name my_node my_package
```



## 3. Understanding the Package Architecture
A professional developer must understand the metadata that drives the build system. Your new package will contain the following structure:

- **`package.xml`**: Defines metadata (version, maintainer) and lists dependencies.
- **`CMakeLists.txt` / `setup.py`**: Instructions for the build tool (Colcon) on how to compile and install your code.
- **`src/` or `my_package/`**: The directory containing your source scripts or source files.
- **`resource/`**: Used by the indexer to identify the package in the environment.



## 4. Managing System Dependencies
One of the most common pitfalls in ROS 2 development is missing system dependencies. Use `rosdep` to automatically install the libraries required by your `package.xml`.

```bash
cd ~/mars_ned2
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```



## 5. Building the Workspace
ROS 2 uses the `colcon` build tool. While a standard build is straightforward, we recommend using the `--symlink-install` flag during development. This allows you to modify Python scripts and configuration files (like YAMLs) and see the changes without rebuilding the entire workspace.

```bash
cd ~/mars_ned2
colcon build --symlink-install
```



## 6. Sourcing the Environment
Once built, you must "source" the workspace so that your terminal recognizes the new packages and nodes.

```bash
source install/setup.bash
```

**Professional Tip:** To avoid manually sourcing every time you open a new terminal, add this command to your shell configuration file:

```bash
echo "source ~/mars_ned2/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```


## 7. Verification and Execution
To ensure your environment is configured correctly, verify that ROS 2 can locate your package and execute the boilerplate node created in Step 2.

**List your package:**
```bash
ros2 pkg list | grep my_package
```

**Run your node:**
```bash
ros2 run my_package my_node
```

---

## Reference: Essential CLI Commands
To maintain a development workspace, keep these commands in your repertoire:

| Task | Command |
| :--- | :--- |
| **Build Specific Package** | `colcon build --packages-select <pkg_name>` |
| **Clean Build** | `rm -rf build/ install/ log/ && colcon build` |
| **Check Dependencies** | `rosdep check --from-paths src --ignore-src` |
| **Install Dependecies** | `rosdep install --from-paths src --ignore-src -r -y` |


