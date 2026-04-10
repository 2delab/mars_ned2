var store = [{
        "title": "Introduction",
        "excerpt":"What Is MARS? This project started with a deceptively simple premise: Get two Niryo Ned2 robots to collaborate autonomously. Multi-Arm Robotic Systems (MARS) is about multiple robotic manipulators operating in a shared workspace to collaboratively complete tasks that would be difficult, inefficient, or impossible for a single arm. &gt; Your...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/01/19/what_is_mars.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Understanding ROS2 ",
        "excerpt":"What is ROS2? Let me introduce you to ROS However, before any confusion Let me start with what ros is not ros is not an application, ros is not an operating system, ros is not a firmware ROS is a middleware that enables communication between different programs, even across multiple machines. A...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/01/23/understanding_ros2.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Niryo Ned2",
        "excerpt":"The robotic arm The Niryo Ned2 robotic arm is designed to mimic the six axes of the human arm which reproduced much of the flexibility and precision. As an educational robot with a 49 cm reach, 300 g payload capacity, and ±0.5 mm repeatability, the Ned2 serves as a practical...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/01/26/Niryo_Ned2.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Pyniryo",
        "excerpt":"Introduction to PyNiryo PyNiryo is Niryo’s pythonic interface. The library abstracts ROS1 firmware complexity with clean Python APIs, offers straightforward robot control methods like move_pose() and vision_pick(), and provides async capabilities through Python’s native concurrency primitives. Initial proof-of-concept code demonstrated that single-robot operation and multiple robots can work with python...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/01/28/pyniryo.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Niryo ROS2 Driver",
        "excerpt":"Niryo NED2 and ROS2 The Niryo NED2 runs a ROS1-based control stack onboard. To control it from a our ROS2 development machine, Niryo provides an official ROS2 driver: ned-ros2-driver. This is maintained by Niryo themselves and is the supported path for ROS2 integration. Architecture The driver runs on your development...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/01/30/ned_ros.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Robot Description",
        "excerpt":"How to decribe a robot: The Unified Robot Description Format When you command Ned2 to pick an object detected by its wrist camera, how does the computer know where to move the gripper? How do you know whether a planned motion causes self-collision? We’ll exlore the two critical systems: URDF...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/02/02/robot_description.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Gazebo",
        "excerpt":"Physics simulation Gazebo is a robotics simulator that runs a full virtual environment. It can simulate physics, sensors and time while integrating natively with ROS 2. Unlike a pure dynamics engine, Gazebo can publish on the same topics, services, and TF tree that a real robot would: joint states come...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/02/04/gazebo.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "MuJoCo and the Sim-to-Real Gap",
        "excerpt":"Simulation for reinforcement learning MuJoCo (Multi-Joint dynamics with Contact) is a physics engine optimised for control, reinforcement learning, and dynamics research. Core design: Fast implicit contact dynamics (designed for contact-rich tasks: grasping, pushing, assembly) Fixed timestep, no adaptive stepping (predictable, deterministic, JAX-compilable) Native Python bindings and a C API No...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/02/05/mujoco.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Camera Calibration",
        "excerpt":"The need for camera intrinsics and extrinsics Your brain doesn’t need a manual to understand that parallel lines meet at the horizon, or that a distant car is smaller than it appears. computer vision? Not so lucky. When a camera captures the 3D world onto a 2D sensor, information gets...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/02/10/camera_calibration.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Transport Frames",
        "excerpt":"ROS 2 Transform Library (tf2) The Transform (tf2) library is the backbone of spatial reasoning in ROS 2. If you’ve ever wondered how a robot knows where its sensors are relative to its wheels, or how it tracks objects in 3D space, tf2 is your answer. What is tf2? tf2...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/02/13/transportFrames.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Fiducial Markers",
        "excerpt":"ArUco Tags vs of Classical Pose Estimation A dual-arm system requires consensus on object locations. This post documents why classical pose estimation failed in practice and how ArUco fiducial markers solved the problem for MARS. The Core Problem A collaborative setup requires both robots to pick items from a shared...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/02/18/fuditialmarkers.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "MoveIt2",
        "excerpt":"MoveIt2 setup: From Setup Assistant to Motion Planning What MoveIt2 Actually Is MoveIt2 is a stack of middleware components sitting between high-level task commands and low-level robot joint controllers. When code says “move end effector to position X,Y,Z,” MoveIt2 handles the execution and engineering: Inverse kinematics (IK): Converts Cartesian poses...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/02/24/moveit2.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Multiple Robots in MoveIt2",
        "excerpt":"How to configure Multiple robots for MoveIt2 There is not just a single way to solve the dual arm problem in MoveIt2. here we’ll discuss three distinct architectural approaches, each with different tradeoffs for collision awareness, scalability, and implementation complexity. This post documents each approach, when to use it, and...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/01/how_to_setup_dual_arm_setup.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Dual Arm MoveIt Config",
        "excerpt":"Building a Dual-Arm MoveIt 2 Configuration The Challenge The task required two Niryo Ned2 arms working on a shared work envelope without colliding. The best approach(read previous blog): combine both robots into a single URDF, configure through MoveIt Setup Assistant, and enable collision-aware planning for simultaneous operation. Starting Point: System...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/02/dualarmconfig.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Collision avoidance",
        "excerpt":"Collision aviodance in Practice Collision avoidance in MoveIt 2 operates at planning time only. The planner produces a trajectory that was collision-free against a snapshot of the world at the moment planning ran. What happens during execution is a separate concern. Understanding this distinction requires tracing how collision checking actually...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/04/collision_avoidance.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Literature Review: Multi-Arm Coordination in Robotics",
        "excerpt":"The Market and Research approoaches to MARS Industrial Baselines: Proprietary Control ABB YuMi (IRB 14000) ABB’s dual-arm collaborative robot, introduced in 2015, is an exellent standard for bimanual coordination in production and assembly. It features two 7-DOF arms mounted on a shared torso with a 559 mm reach per arm....","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/05/lit_review.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "MoveItPy",
        "excerpt":"MoveIt’s python API MoveItPy is the official Python binding layer for MoveIt2’s C++ core, implemented via pybind11. It is not a wrapper around the move_group action interface. Where the action interface communicates with a separately running move_group node over ROS2 actions, MoveItPy embeds the MoveIt2 planning stack directly in-process —...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/10/moveitpy.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": " Trajectory Execution with MoveIt2",
        "excerpt":"Synchronous and Asynchronous Execution with MoveIt2 MoveIt2 does not commit to a single execution paradigm. The dual-arm moveit config supports both tightly-coupled synchronous motion and fully independent asynchronous motion, selected purely by which planning group you target. The choice is made at the point of planning. No runtime reconfiguration is...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/12/trajectory_execution.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Interfacing wih Moveit",
        "excerpt":"Interfacing with MoveIt2 here we’ll discuss the five ways to intterface with MoveIt2 1. MoveGroup Action - Production-grade ROS 2 action interface 2. Pure MoveItPy - Python bindings to MoveIt’s C++ core 3. ROS 2 Services - Low-level service calls 4. ROS 2 Topics - Pub/sub monitoring 5. pyMoveIt2 -...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/14/interfacing_with_moveit.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "The Planning Scene",
        "excerpt":"The Planning Scene simplified The MoveIt 2 planning scene is a simplified, static, approximate model of reality that the motion planner uses to check for collisions. What the Planning Scene Contains The planning scene is a data structure maintained by the PlanningSceneMonitor node. It contains: Robot geometry: the collision meshes...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/15/planning_scene.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "State Management",
        "excerpt":"How to manage Multi-arm Robot states The JointStateManager is the node that aggregates two namespace-isolated arms into a single coherent system state. Without it, MoveIt2 cannot plan for both arms simultaneously because it has no unified representation of their joint configurations. The Problem Each Niryo NED2 publishes joint states to...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/16/state_management.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "The Trajectory Proxy ",
        "excerpt":"Distributing trajectories MoveIt2 generates trajectories for a unified 12-DOF robot. The hardware expects two separate 6-DOF trajectory commands, delivered to independent action servers in different namespaces. The TrajectoryProxy is the layer that performs this translation — splitting, stripping, and dispatching planned trajectories to the correct hardware controllers. The Problem After...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/20/trajectory_proxy.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Sync and Async Tests",
        "excerpt":"Testing Coordination MARS has two coordination modes: synchronised and asynchronous motion. Both modes ran on physical Niryo NED2 hardware with joint state data logged at 15 Hz from /arm_1/joint_states and /arm_2/joint_states. The fundamental difference is architectural: the dual 12-DOF planning group produces a single shared trajectory that moves both arms...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/23/test_sync_n_async.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Collision tests",
        "excerpt":"Collision safety validation Test Setup Two collision test scenarios were executed to validate inter-arm collision detection at the planning-time level and confirm zero collisions during execution: Scenario Arm 1 State Arm 2 Motion Configurations Purpose Dynamic Free to move from initial position Moves between two configurations 50 pairs Arm 1...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/26/test_collision.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Accuracy tests",
        "excerpt":"Accuracy and Repeatabiliy Given a target joint configuration, how close does the actual joint position get? How much does this vary across repeated trials? Accuracy is measured as the range (min-max spread) of achieved positions across 9 test cycles. Why Command Accuracy Matters The gap between commanded position and actual...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/03/29/test_accuracy.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "A Practical Summary",
        "excerpt":"What MARS Can Do and What It Cannot Three Coordination Modes MARS provides three selectable modes at runtime, each with different guarantees: Asynchronous mode — both arms plan and execute independently, 6-DOF each. No cross-arm collision checking. This is the mode that delivers the headline result: 28.6% cycle time reduction...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/04/02/featuresandlimits.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": " Future Work",
        "excerpt":"Key improvement areas Driver-Level Synchronisation The largest gap between simulation and hardware for synchronised mode is the 20–50 ms inter-arm start offset caused by sequential trajectory dispatch. A synchronisation shim at the driver level — a barrier that releases both hardware controllers simultaneously via a shared signal — would eliminate...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/04/05/future_work.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      },{
        "title": "Demos",
        "excerpt":"MARS validation demonstrations Demo 1: Pick and Place Claim: dual-arm asynchronous operation achieves measurable throughput gains over sequential single-arm operation. Design: both arms execute pick-and-place cycles simultaneously on spatially partitioned targets. A single-arm baseline (same task, same hardware, sequential) provides the comparison. What it proves: the coordination architecture enables genuine...","categories": [],
        "tags": [],
        "url": "/mars_ned2/2026/04/08/demo.html",
        "teaser": "/mars_ned2/assets/images/photo.jpg"
      }]
