var store = [{
        "title": "Introduction",
        "excerpt":"What Is MARS? I started this project with a deceptively simple premise: Get two Niryo Ned2 robots to collaborate autonomosly. Instead of one robot working alone, Multi-Arm Robotic Systems (MARS) multiple robotic manipulators operating in a shared workspace to collaboratively complete tasks that would be difficult, inefficient, or impossible for...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/01/19/what_is_mars.html",
        "teaser": null
      },{
        "title": "Understanding ROS2 ",
        "excerpt":"Let me introduce you to ROS However, before any confusion Let me start with what ros is not ros is not an application, ros is not an operating system, ros is not a firmware ROS is a middleware that enables communication between different programs, even across multiple machines. A set of software...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/01/23/understanding_ros2.html",
        "teaser": null
      },{
        "title": "Niryo Ned2",
        "excerpt":"The robotic arm The Niryo Ned2 robotic arm is designed to mimic the six axes of the human arm which reproduced much of the flexibility and precision. As an educational robot with a 49 cm reach, 300 g payload capacity, and ±0.5 mm repeatability, the Ned2 serves as a practical...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/01/26/Niryo_Ned2.html",
        "teaser": null
      },{
        "title": "Pyniryo",
        "excerpt":"PyNiryo PyNiryo presents an appeling pythonic interface. The library abstracts ROS1 firmware complexity with clean Python APIs, offers straightforward robot control methods like move_pose() and vision_pick(), and provides async capabilities through Python’s native concurrency primitives. Initial proof-of-concept code demonstrated that single-robot operation and multiple robots can work with python elegantly....","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/01/28/pyniryo.html",
        "teaser": null
      },{
        "title": "Niryo NED2 ROS2 Driver",
        "excerpt":"Getting Started with Niryo NED2 and ROS2 The Niryo NED2 runs a ROS1-based control stack onboard. To control it from a our ROS2 development machine, Niryo provides an official ROS2 driver: ned-ros2-driver. This is maintained by Niryo themselves and is the supported path for ROS2 integration. Architecture The driver runs...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/01/30/ned_ros.html",
        "teaser": null
      },{
        "title": "Robot Description",
        "excerpt":"How to decribe a robot: The Unified Robot Description Format When you command Ned2 to pick an object detected by its wrist camera, how does the computer know where to move the gripper? How do you know whether a planned motion causes self-collision? We’ll exlore the two critical systems: URDF...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/02/02/robot_description.html",
        "teaser": null
      },{
        "title": "Gazebo",
        "excerpt":"What Is Gazebo? Gazebo is a robotics simulator that runs a full virtual environment. It can simulate physics, sensors and time while integrating natively with ROS 2. Unlike a pure dynamics engine, Gazebo can publish on the same topics, services, and TF tree that a real robot would: joint states...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/02/04/gazebo.html",
        "teaser": null
      },{
        "title": "MuJoCo and the Sim-to-Real Gap",
        "excerpt":"What Is MuJoCo? MuJoCo (Multi-Joint dynamics with Contact) is a physics engine optimised for control, reinforcement learning, and dynamics research. Core design: Fast implicit contact dynamics (designed for contact-rich tasks: grasping, pushing, assembly) Fixed timestep, no adaptive stepping (predictable, deterministic, JAX-compilable) Native Python bindings and a C API No scenegraph,...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/02/05/mujoco.html",
        "teaser": null
      },{
        "title": "Camera Calibration",
        "excerpt":"The need for camera intrinsics and extrinsics Your brain doesn’t need a manual to understand that parallel lines meet at the horizon, or that a distant car is smaller than it appears. computer vision? Not so lucky. When a camera captures the 3D world onto a 2D sensor, information gets...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/02/10/camera_calibration.html",
        "teaser": null
      },{
        "title": "Transport Frames",
        "excerpt":"ROS 2 Transform Library (tf2) The Transform (tf2) library is the backbone of spatial reasoning in ROS 2. If you’ve ever wondered how a robot knows where its sensors are relative to its wheels, or how it tracks objects in 3D space, tf2 is your answer. What is tf2? tf2...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/02/13/transportFrames.html",
        "teaser": null
      },{
        "title": "Fudutial Markers",
        "excerpt":"Choosing ArUco Tags insead of Classical Pose Estimation The Core Problem A collaborative setup requires both robots to pick items from a shared table. Both need to know where things are, and need to agree on those positions. Hardcoding won’t work on dynamic environments. The naive approach: run individual pose...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/02/18/fuditialmarkers.html",
        "teaser": null
      },{
        "title": "MoveIt2",
        "excerpt":"Getting MoveIt2 Working: From Setup Assistant to Collision-Aware Motion Planning What MoveIt2 Actually Is MoveIt2 is a stack of middleware components sitting between high-level task commands and low-level robot joint controllers. When code says “move end effector to position X,Y,Z,” MoveIt2 handles the execution and engineering: Inverse kinematics (IK): Converts...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/02/24/moveit2.html",
        "teaser": null
      },{
        "title": "Multiple Robots in MoveIt2",
        "excerpt":"Choosing how to configure Multiple robots in MoveIt2 There is not just a single way to solve the dual arm problem in MoveIt2. here we’ll discuss three distinct architectural approaches, each with different tradeoffs for collision awareness, scalability, and implementation complexity. This post documents each approach, when to use it,...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/01/how_to_setup_dual_arm_setup.html",
        "teaser": null
      },{
        "title": "Dual Arm MoveIt Config",
        "excerpt":"Building a Dual-Arm MoveIt 2 Configuration The Challenge The task required two Niryo Ned2 arms working on a shared work envelope without colliding. The best approach(read previous blog): combine both robots into a single URDF, configure through MoveIt Setup Assistant, and enable collision-aware planning for simultaneous operation. Starting Point: System...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/02/dualarmconfig.html",
        "teaser": null
      },{
        "title": "Collision avoidance",
        "excerpt":"How collision aviodance works Collision avoidance in MoveIt 2 operates at planning time only. The planner produces a trajectory that was collision-free against a snapshot of the world at the moment planning ran. What happens during execution is a separate concern. Understanding this distinction requires tracing how collision checking actually...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/04/collision_avoidance.html",
        "teaser": null
      },{
        "title": "Literature Review: Multi-Arm Coordination in Robotics",
        "excerpt":"Coordinating multiple robotic arms in a shared space is a long-standing problem with many existing solutions. However, no single method has been adopted as an open-source standard. Industrial Baselines: Proprietary Control ABB YuMi (IRB 14000) ABB’s dual-arm collaborative robot, introduced in 2015, is an exellent standard for bimanual coordination in...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/05/lit_review.html",
        "teaser": null
      },{
        "title": "MoveItPy",
        "excerpt":"MoveItPy MoveItPy is the official Python binding layer for MoveIt2’s C++ core, implemented via pybind11. It is not a wrapper around the move_group action interface. Where the action interface communicates with a separately running move_group node over ROS2 actions, MoveItPy embeds the MoveIt2 planning stack directly in-process — planning, scene...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/10/moveitpy.html",
        "teaser": null
      },{
        "title": " Trajectory Execution with MoveIt2",
        "excerpt":"Synchronous and Asynchronous Execution with MoveIt2 MoveIt2 does not commit to a single execution paradigm. The dual-arm moveit config supports both tightly-coupled synchronous motion and fully independent asynchronous motion, selected purely by which planning group you target. The choice is made at the point of planning. No runtime reconfiguration is...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/12/trajectory_execution.html",
        "teaser": null
      },{
        "title": "Interfacing wih Moveit",
        "excerpt":"Interfacing with MoveIt2 here we’ll discuss the five ways to intterface with MoveIt2 1. MoveGroup Action - Production-grade ROS 2 action interface 2. Pure MoveItPy - Python bindings to MoveIt’s C++ core 3. ROS 2 Services - Low-level service calls 4. ROS 2 Topics - Pub/sub monitoring 5. pyMoveIt2 -...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/14/interfacing_with_moveit.html",
        "teaser": null
      },{
        "title": "The Planning Scene",
        "excerpt":"The MoveIt 2 planning scene is a simplified, static, approximate model of reality that the motion planner uses to check for collisions. What the Planning Scene Contains The planning scene is a data structure maintained by the PlanningSceneMonitor node. It contains: Robot geometry: the collision meshes for every link of...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/15/planning_scene.html",
        "teaser": null
      },{
        "title": "State Management",
        "excerpt":"The JointStateManager is the node that aggregates two namespace-isolated arms into a single coherent system state. Without it, MoveIt2 cannot plan for both arms simultaneously because it has no unified representation of their joint configurations. The Problem Each Niryo NED2 publishes joint states to its own namespaced topic: /arm_1/joint_states →...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/16/state_management.html",
        "teaser": null
      },{
        "title": "The TrajectoryProxy Pattern",
        "excerpt":"MoveIt2 generates trajectories for a unified 12-DOF robot. The hardware expects two separate 6-DOF trajectory commands, delivered to independent action servers in different namespaces. The TrajectoryProxy is the layer that performs this translation — splitting, stripping, and dispatching planned trajectories to the correct hardware controllers. The Problem After planning, MoveIt2...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/20/trajectory_proxy.html",
        "teaser": null
      },{
        "title": "Sync and Async Tests",
        "excerpt":"MARS has two coordination modes. synchronised and asynchronous motion. Both modes ran on physical Niryo NED2 hardware with joint state data logged at 15 Hz from /arm_1/joint_states and /arm_2/joint_states. The fundamental difference between the two modes is the planning group used: the dual 12-DOF group produces a single shared trajectory;...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/23/test_sync_n_async.html",
        "teaser": null
      },{
        "title": "The TrajectoryProxy Pattern",
        "excerpt":"The collision safety validation is the most straightforward result in MARS: 100 hardware tests across two scenarios, zero unplanned collisions. Test Setup Two collision test scenarios were executed: Dynamic tests (50 configurations): arm_2 moves between two configurations while arm_1 is free to move from its position. Static tests (50 configurations):...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/26/test_collision.html",
        "teaser": null
      },{
        "title": "Repeatability test",
        "excerpt":"The most important result from the pick-and-place validation is not the 28.6% throughput gain. It is the 0.5% coefficient of variation across repeated dual-arm tasks. This is the result that determines whether the system is deployable. its not how fast it is, but how consistently it behaves. Why Repeatability Is...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/03/29/test_accurracy.html",
        "teaser": null
      },{
        "title": "What MARS Can Do and What It Cannot: A Practical Summary",
        "excerpt":"This is the complete picture of what the final MARS implementation delivers and where the boundaries are. If you are considering MARS for your own dual-arm system, this post tells you what you are getting and what you are not. What It Does Three Coordination Modes MARS provides three selectable...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/04/02/featuresandlimits.html",
        "teaser": null
      },{
        "title": " Future Work",
        "excerpt":"MARS solves a specific problem: coordinated dual-arm manipulation on namespace-isolated ROS2 hardware, with planning-time collision safety and three selectable coordination modes. It does not solve the general multi-arm coordination problem. This post maps the open problems and the directions where the architecture extends naturally versus where new work is needed....","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/04/05/future_work.html",
        "teaser": null
      },{
        "title": "Demos",
        "excerpt":"The MARS validation campaign uses six demonstrations, each designed to prove a specific claim about the coordination architecture. This post maps each demonstration to the claim it validates and explains the design choice behind it. Demo 1: Pick and Place (Asynchronous Mode) Claim: dual-arm asynchronous operation achieves measurable throughput gains...","categories": [],
        "tags": [],
        "url": "/mars-ned2/2026/04/08/demo.html",
        "teaser": null
      }]
