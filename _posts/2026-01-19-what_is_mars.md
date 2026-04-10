---
layout: single
title: "Introduction"
header:
  teaser: /assets/images/photo.jpg
date: 2026-01-19  
classes: wide
author_profile: false
---


## What Is MARS?

This project started with a deceptively simple premise: Get two Niryo Ned2 robots to **collaborate autonomously**.

Multi-Arm Robotic Systems (MARS) is about multiple robotic manipulators operating in a shared workspace to collaboratively complete tasks that would be difficult, inefficient, or impossible for a single arm.

<video width="100%" controls autoplay muted loop>>
  <source src="/mars_ned2/assets/videos/mars.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>
See more: [MoveIt PR #2810](https://github.com/moveit/moveit/pull/2810)

Each arm has its own degrees of freedom, sensors, and control systems, yet they must work together toward common goals. Multi-arm systems aren't just about having more actuators—they enable capabilities that emerge only through collaboration: assembly tasks requiring simultaneous actions from multiple angles, or parallel operations that dramatically reduce cycle times.

## Core Challenges

### **Shared Workspace Management**

In multi-arm systems, the primary bottleneck for operational efficiency is collision avoidance. Unlike single-arm setups, MARS requires persistent spatial negotiation within a shared workspace. The core challenge is real-time synchronization of every arm's position and projected trajectory to prevent path intersections.

To address this, several strategies exist:

**Centralized collision avoidance**:  A unified planning scene aggregates every joint from all manipulators into a single, high-degree-of-freedom configuration space. Rather than solving for arms individually, the system uses sampling-based or optimization-based planners to compute trajectories that are globally aware of the entire system's geometry, ensuring that the motion of one arm is always valid relative to the current and future positions of all others.

**Dynamic workspace regulation**: Real-time coordination strategies enable arms to "dynamically regulate their movements and execute tasks simultaneously" in shared spaces. Rather than pre-computing the entire solution, systems continuously adjust based on current state.


### **Task Coordination & Synchronization**
In addition, arms must coordinate not just in space, but in time and purpose.

Here we'll consider two different coordination modes:

**Synchronous behavior** is achieved through unified trajectory time-parameterization and synchronized controller execution. The framework ensures that multiple arms coordinate with each other and with moving objects by aligning their time-stamps within a single execution pipeline. This allows the system to meet the precise timing required for complex maneuvers where every arm must arrive at a target configuration simultaneously with the correct orientation.

**Asynchronous behavior** allows each arm to perform independent point-to-point motions without strict timing constraints. This maximizes efficiency when tasks vary in duration—one arm executes complex assembly while another performs quick pick-and-place.

**Mode selection** can be automated through hierarchical task management. The system monitors arm separation and workspace sharing, switching to synchronous mode when arms approach each other and asynchronous when they're in separate zones. This allows fluid transitions between independent operation and tight coordination.

### **Joint State Management**

Multi-arm systems create an additional state management problem. With multiple arms, each possessing 6 DOF, the composite state space becomes vast. A dual-arm system operates in 12-dimensional joint space. Scale to three or four arms, and complexity and computational load grow exponentially.

The core challenges:

**State representation**: Defining the complete joint configuration Θ = (θ₁, ..., θᵣ)ᵀ where r represents total joints across all arms, then mapping from joint space to Cartesian space through highly nonlinear operators.

**Real-time inverse kinematics**: Converting desired end-effector motions into joint states requires solving complex inverse mapping problems. Iterative methods via Jacobian matrices and damped least squares approach solutions quickly enough for real-time control.


### **Planning & Trajectory Execution**
The next objective is figuring out how deal with generating executable plans and running them reliably.

Planning operates at two levels:

**High-level planning**: manages task complexity by selecting appropriate agents and generating action sequences for collaborative tasks. By decomposing complex problems into manageable subtasks, the system can coordinate multiple manipulators to work toward a unified goal while maintaining logical consistency across the entire group.

**Low-level control**: Once a plan is generated, the framework deploys control policies that execute manipulation tasks in physically realistic environments. This layer ensures that the hardware follows the planned trajectory while strictly maintaining safety and performance constraints, such as joint limits and obstacle proximity.


## Conclusion

The transition to multi-arm robotic systems represents a fundamental shift in automation capability. While single-arm setups optimize for isolated, repetitive tasks, MARS architectures enable collaborative manipulation that transcends simple repetition.

This project demonstrates that with proper spatial coordination, synchronized execution, and robust state management, two Niryo Ned2 robots can operate as a unified system. The result: tasks that would be inefficient or impossible for a single arm become manageable—assembly requiring simultaneous access from multiple angles, parallel operations that halve cycle times, and collaborative workflows that mirror human team dynamics.

The key insight is that coordination isn't a single problem to solve, but a layered challenge: collision avoidance in shared space, synchronization across multiple timelines, state management in high-dimensional joint spaces, and planning that orchestrates it all. Each layer is critical; weakness in any breaks the entire system.

Multi-arm robotics is no longer theoretical. With proper architecture and careful design, it's achievable with commercial hardware and open-source frameworks.
