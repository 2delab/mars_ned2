---
layout: single
title: "ROS2 "
header:
  teaser: /assets/images/posts/understanding_ros2.png
date: 2026-01-23
classes : wide
author_profile: false
---

## What is ROS2?

Let me introduce you to ROS

However, before any confusion

Let's start with what ROS is not
ROS is not an application, it is not an operating system and it is not a firmware.

ROS is a **middleware** that enables communication between different programs, even across multiple machines.
it's **set of software libraries and tools** for building robot applications
It's not a standalone application, but the backbone that connects your robotic systems by providing services like hardware abstraction, message-passing between processes, and package management.

For MARS, this matters because: we need two independent robot control loops, a motion planner, a collision detector, and a perception pipeline all running in parallel. ROS2 provides the standardised communication layer that lets these components talk without tight coupling.

Here's we'll cover some major components and the setup for the project.

### The DDS Layer:  

Under the hood, it's all **DDS (Data Distribution Service)**
which isn't just a transport but a complete middleware specification with:
- **Discovery**: Nodes find each other automatically via multicast (or discovery servers)
- **QoS Policies**: Fine-grained control over reliability, durability, history, deadlines
- **Real-time capable**: Deterministic timing when configured properly
- **Scalability**: Handles hundreds of nodes without breaking a sweat

The architecture
### Nodes: Your Building Blocks
Every piece of functionality lives in a **node**. A node is just a process that does one thing well. Maybe it reads from a camera. Maybe it plans a path. Maybe it controls a motor.

For MARS, we can run separate nodes for each robot's control loop, a unified motion planner, a collision checker, and vision processing. This modularity means we can restart the planner without crashing the hardware interface, or swap the collision detection algorithm without touching the control code.

**Key trait:** Single responsibility. Each node usually does one thing.

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

With MARS:
- **Robot 1** publishes its joint states to `/robot_1/joint_states` at 100Hz
- **Robot 2** publishes its joint states to `/robot_2/joint_states` at 100Hz
- The **motion planner** subscribes to both, always aware of the current configuration
- The **collision detector** subscribes to both, continuously checking for inter-arm conflicts

This decoupling means a slow node won't block the others. If the planner stalls, the joint state publishers keep flowing.

**Key trait:** Asynchronous, no response required.

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
- A high-level task planner can call `/request_gripper_close` service to ask robot 1 to pick an object
- Robot 1's gripper controller processes the request and returns success or failure
- The planner waits for this response before proceeding to the next step

Services are ideal for discrete tasks that require confirmation, not continuous streaming.

**Key trait:** Synchronous, client waits for a response.

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
- A high-level task can send a `MoveIt2` action goal: "move arm 1 to pose (x, y, z)"
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


# Setting Up the MARS Workspace

ROS demands a structured approach to workspace organisation, dependency management, and build processes. 

## 1. Initialising the Workspace

The workspace is the project's container, holding all packages, dependencies, and build artifacts. The `src/` directory holds all source code; the build system automatically generates the rest.

```bash
mkdir -p ~/mars_ned2/src
cd ~/mars_ned2
```

## 2. Creating Packages

In ROS 2, code is organised into packages. ROS 2 supports two build types: `ament_python` for Python and `ament_cmake` for C++.

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

Your new package will contain the following structure:

- **`package.xml`**: Defines metadata (version, maintainer) and lists dependencies.
- **`CMakeLists.txt` / `setup.py`**: Instructions for Colcon on how to compile and install your code.
- **`src/` or `my_package/`**: The directory containing your source scripts or source files.
- **`resource/`**: Used by the indexer to identify the package in the environment.

Always declare dependencies explicitly in `package.xml`
```xml
<depend>rclcpp</depend>
<depend>std_msgs</depend>
<build_depend>octomap</build_depend>
<run_depend>octomap</run_depend>
```

**Version Control:** Keep only `src/` under Git; exclude `build/`, `install/`, and `log/`.


## 4. Managing System Dependencies

One of the most common pitfalls in ROS 2 development is missing system dependencies. Use `rosdep` to automatically install everything listed in your `package.xml` files. The `-r` flag continues even if some packages fail; `-y` auto-confirms installations.

```bash
cd ~/mars_ned2
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```


## 5. Building the Workspace

Colcon is ROS 2's build tool, replacing the older catkin with improved performance and cleaner separation of concerns. During development, the `--symlink-install` flag lets you modify Python scripts and config files (like YAMLs) without a full rebuild.

```bash
cd ~/mars_ned2
colcon build --symlink-install
```

To rebuild only one package:
```bash
colcon build --packages-select my_package
```

When facing mysterious build issues, a clean build usually helps:
```bash
rm -rf build/ install/ log/
colcon build
```

After your first build you'll see three additional directories:

- `build/`: Intermediate build files
- `install/`: Compiled packages ready to run
- `log/`: Build and runtime logs


## 6. Sourcing the Environment

Once built, you must source the workspace so your terminal recognises the new packages and nodes.

```bash
source install/setup.bash
```

To avoid doing this manually every time you open a new terminal:

```bash
echo "source ~/mars_ned2/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```


## 7. Verification and Execution

Verify that ROS 2 can locate your package and run the boilerplate node created in Step 2.

```bash
ros2 pkg list | grep my_package
ros2 run my_package my_node
```


## The Ecosystem

ROS2 is more than middleware; it's a growing ecosystem of specialised packages:
- **Nav2**: Advanced navigation stack (mobile robots)
- **MoveIt2**: Motion planning and collision checking for manipulators, critical for MARS
- **Gazebo**: Physics simulation for testing dual-arm scenarios safely
- **RViz2**: 3D visualisation of robot state, trajectories, and transforms
- **ros2_control**: Hardware abstraction layer (enables switching between simulation and real hardware)
- **tf2**: Transform management (essential for multi-robot spatial reasoning)

For MARS specifically, **MoveIt2** and **tf2** are the backbone. MoveIt2 handles dual-arm planning and execution, while tf2 maintains the transform tree linking both arms' end-effectors to a shared world frame.

---

## Reference: Essential CLI Commands

| Task | Command |
| :--- | :--- |
| **Build Specific Package** | `colcon build --packages-select <pkg_name>` |
| **Clean Build** | `rm -rf build/ install/ log/ && colcon build` |
| **Check Dependencies** | `rosdep check --from-paths src --ignore-src` |
| **Install Dependencies** | `rosdep install --from-paths src --ignore-src -r -y` |


