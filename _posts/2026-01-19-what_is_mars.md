---
layout: single
title: "Introduction"
date: 2026-01-19  
classes: wide
author_profile: false
---


## What Is MARS?

I started this project with a deceptively simple premise: Get two Niryo Ned2 robots to **collaborate autonomosly.**

Instead of one robot working alone, Multi-Arm Robotic Systems (MARS)  multiple robotic manipulators operating in a shared workspace to collaboratively complete tasks that would be difficult, inefficient, or impossible for a single arm.

<video width="100%" controls autoplay muted loop>>
  <source src="/mars_ned2/assets/videos/mars.mp4" type="video/mp4">
  Your browser doesn't support HTML5 video.
</video>
See more: [MoveIt PR #2810](https://github.com/moveit/moveit/pull/2810)

Each arm with its own degrees of freedom, sensors, and control systems, yet they must work together toward common goals.  These systems aren't just about having more arms but about enabling capabilities that emerge only through collaboration: i.e performing assembly tasks requiring simultaneous actions from multiple angles, or executing parallel operations that dramatically reduce cycle times.

## The key challenges we're tackling 

### **Shared Workspace Management**

In Multi-Arm Robotic Systems, the primary bottleneck for operational efficiency is collision avoidance. Unlike isolated single-arm setups, MARS requires persistent spatial negotiation within a shared work envelope. The core challenge lies in the real-time synchronization of every arm’s position and projected trajectory to prevent path intersections.

To address this complexity, contemporary solutions utilise the several strategies:

**Centralized collision avoidance**:  A unified planning scene aggregates every joint from all manipulators into a single, high-degree-of-freedom configuration space. Rather than solving for arms individually, the system uses sampling-based or optimization-based planners to compute trajectories that are globally aware of the entire system's geometry, ensuring that the motion of one arm is always valid relative to the current and future positions of all others.

**Dynamic workspace regulation**: Real-time coordination strategies enable arms to "dynamically regulate their movements and execute tasks simultaneously" in shared spaces. Rather than pre-computing the entire solution, systems continuously adjust based on current state.


### **Task Coordination & Synchronization**
In addition, arms must coordinate not just in space, but in time and purpose.

Here we'll consider two different coordination modes:

**Synchronous behavior** is achieved through unified trajectory time-parameterization and synchronized controller execution. The framework ensures that multiple arms coordinate with each other and with moving objects by aligning their time-stamps within a single execution pipeline. This allows the system to meet the precise timing required for complex maneuvers where every arm must arrive at a target configuration simultaneously with the correct orientation.

**Asynchronous behavior** allows each arm to perform independent point-to-point motions without strict timing constraints. This mode maximizes efficiency when tasks vary in duration. One arm might be executing a complex assembly while another performs quick pick-and-place operations.

The magic happens in transitioning between these modes through hierarchical task management. By utilizing a control variable the system can smoothly shift behavior based on context.  This integration allows a multi-arm setup to "re-synchronize and adapt the motion of each arm while avoiding self-collision within milliseconds," moving fluidly between independent operations and tight temporal coordination.

Recent approaches also explore:
**Graph-based task allocation**: By integrating graph-based logic—such as behavioral trees or reinforcement learning within the core motion planning pipeline, the system can perform joint task scheduling and collision-free path generation simultaneously. This allows the framework to solve complex, obstacle-rich scenarios by decomposing global goals into a series of coordinated, collision-aware sub-tasks that are allocated and scheduled across the available manipulators.

### **Joint State Management**
Multi-arm systems also create an addiinal state management problem. With multiple arms, each possessing 6 DOF, the composite state space becomes vast. A dual-arm system with 6-DOF manipulators operates in a 12-dimensional joint space. Scale to three or four arms, and the complexity and computational load becomes vast.

The core challenges:

**State representation**: Defining the complete joint configuration Θ = (θ₁, ..., θᵣ)ᵀ where r represents total joints across all arms, then mapping from joint space to Cartesian space through highly nonlinear operators.

**Real-time inverse kinematics**: Converting desired end-effector motions into joint states requires solving complex inverse mapping problems. Iterative methods via Jacobian matrices and damped least squares approach solutions quickly enough for real-time control.


### **Planning & Trajectory Execution**
The next objective is figuring out how deal with generating executable plans and running them reliably.

Planning operates at two levels:

**High-level planning**: manages task complexity by selecting appropriate agents and generating action sequences for collaborative tasks. By decomposing complex problems into manageable subtasks, the system can coordinate multiple manipulators to work toward a unified goal while maintaining logical consistency across the entire group.

**Low-level control**: Once a plan is generated, the framework deploys control policies that execute manipulation tasks in physically realistic environments. This layer ensures that the hardware follows the planned trajectory while strictly maintaining safety and performance constraints, such as joint limits and obstacle proximity.


## In conclusion 
The transition to Multi-Arm Robotic Systems (MARS) represents a new paradigm in automation. While single-arm setups excel at isolated, repetitive tasks, MARS architectures unlock collaborative manipulation at a higher level.
