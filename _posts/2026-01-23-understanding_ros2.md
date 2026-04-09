---
layout: single
title: "Understanding ROS2 "
date: 2026-01-23
classes : wide
author_profile: false
---

Let me introduce you to ROS

However, before any confusion

Let me start with what ros is not
ros is not an application, ros is not an operating system, ros is not a firmware

ROS is a **middleware** that enables communication between different programs, even across multiple machines.
**A set of software libraries and tools** for building robot applications
It's not a standalone application, but rather the backbone that connects your robotic systems. 
**A communication infrastructure** that provides services like hardware abstraction, message-passing between processes, and package management.

The DDS Layer: Why ROS2 
Under the hood, it's all **DDS (Data Distribution Service)**
which isn't just a transport but a complete middleware specification with:
- **Discovery**: Nodes find each other automatically via multicast (or discovery servers)
- **QoS Policies**: Fine-grained control over reliability, durability, history, deadlines
- **Real-time capable**: Deterministic timing when configured properly
- **Scalability**: Handles hundreds of nodes without breaking a sweat

The architecture
### Nodes: Your Building Blocks
Every piece of functionality lives in a **node**. A node is just a process that does one thing well. Maybe it reads from a camera. Maybe it plans a path. Maybe it controls a motor.
 key trait: single responsibility - usually just does one thing.  
e.g.
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


### Topics: Broadcast
think of it as a radio station where any one can tune in. so one node publishes data; any number of nodes can subscribe. No direct connection needed. No blocking. Perfect for sensor data streaming.
- **Key trait:** Asynchronous - no response required
e.g.
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


### 2. Services (Request and response)
The ROS2 service is functionally equivalent to an API (Application Programming Interface) in that it provides a standardized way for nodes to request and receive responses, similar to how APIs enable communication between software systems. so the client sends a request and has to wait until the server responds. They are useful for quick tasks like getting a program’s status or running a short calculation The system works with service **servers** and service **clients**. The **server** processes requests and sends back responses. It does not send data continuously
- **Key trait:** Synchronous - waits for response
e.g.

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
### 3. Actions
Actions are the sophisticated sibling, they are used for **long-running tasks** that need **response** and can be stopped if needed.
- **Key trait:** longer tasks, that can be cancelled mid-execution. also with progress feedback.

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

ROS2 isn't just the ROS2 middleware also , it's an ecosystem:
- **Nav2**: Advanced navigation stack
- **MoveIt 2**: Motion planning for manipulators
- **Gazebo**: Physics simulation
- **RViz2**: 3D visualization
- **ros2_control**: Hardware abstraction for controllers
- **micro-ROS**: For microcontrollers (ESP32, STM32)

We'll comeback to these but feel free to browse.



# A Guide to Setting Up our Workspace


In this guide, we will walk through the practical workflow for initializing a ROS 2 environment, creating packages, and managing dependencies for our project.


## 1. Initializing Your Workspace
A ROS 2 workspace is the directory where you develop, build, and install your ROS 2 packages. By convention, developers often name this `ros2_ws`. 

Open your terminal and execute the following to create the standard directory structure:

```bash
mkdir -p ~/mars_ned2/src
cd ~/mars_ned2
```

The `src/` directory is critical—it is the only place where your source code should reside. The build system will automatically generate other folders (`build`, `install`, and `log`) in the root of the workspace.


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
To maintain a high-velocity development workflow, keep these commands in your repertoire:

| Task | Command |
| :--- | :--- |
| **Build Specific Package** | `colcon build --packages-select <pkg_name>` |
| **Clean Build** | `rm -rf build/ install/ log/ && colcon build` |
| **Check Dependencies** | `rosdep check --from-paths src --ignore-src` |
| **Install Dependecies** | `rosdep install --from-paths src --ignore-src -r -y` |


