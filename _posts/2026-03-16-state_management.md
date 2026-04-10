---
layout: single
title: "State Management"
header:
  teaser: /assets/images/photo.jpg
date: 2026-03-16
classes: wide
author_profile: false
---

# How to manage Multi-arm Robot states

The `JointStateManager` is the node that aggregates two namespace-isolated arms into a single coherent system state. Without it, MoveIt2 cannot plan for both arms simultaneously because it has no unified representation of their joint configurations.

---

## The Problem

Each Niryo NED2 publishes joint states to its own namespaced topic:

```
/arm_1/joint_states  → {joint_1: val, joint_2: val, ..., joint_6: val}
/arm_2/joint_states  → {joint_1: val, joint_2: val, ..., joint_6: val}
```

Both messages use identical joint names (`joint_1` through `joint_6`). There is no disambiguation. The Robot State Publisher — which computes TF transforms from joint states — expects a single `/joint_states` topic. If you give it both raw messages, it receives conflicting values for identically named joints.

MoveIt2's `PlanningSceneMonitor` has the same requirement: one joint state topic representing the entire robot.

---

## The Solution: Bidirectional Name Translation

The `JointStateManager` solves this with a symmetric translation layer:

**Forward path (hardware → planning):**
```
/arm_1/joint_states: {joint_1: 0.5, joint_2: -0.3, ...}
/arm_2/joint_states: {joint_1: 0.2, joint_2: -0.1, ...}
                           ↓ prefix and merge
/joint_states: {arm_1_joint_1: 0.5, arm_1_joint_2: -0.3, ...,
                arm_2_joint_1: 0.2, arm_2_joint_2: -0.1, ...}
```

**Reverse path (planning → hardware):**
```
MoveIt2 generates trajectory for arm_1 group:
{arm_1_joint_1: target, arm_1_joint_2: target, ...}
                           ↓ strip prefix
/arm_1/joint_trajectory_controller/follow_joint_trajectory:
{joint_1: target, joint_2: target, ...}
```

The Robot State Publisher consumes the unified `/joint_states` topic and produces a TF tree containing all 12 DOF. MoveIt2 plans against this unified state. The hardware controllers receive stripped trajectories matching their expected joint names.

---

## Implementation

```python
# Pseudocode: JointStateManager

class JointStateManager(Node):
    def __init__(self):
        super().__init__('joint_state_manager')
        
        self.arm_states = {'arm_1': None, 'arm_2': None}
        self.lock = threading.Lock()
        
        # Subscribe to both arms
        self.sub_1 = self.create_subscription(
            JointState, '/arm_1/joint_states', 
            lambda msg: self.callback(msg, 'arm_1'), 10)
        self.sub_2 = self.create_subscription(
            JointState, '/arm_2/joint_states',
            lambda msg: self.callback(msg, 'arm_2'), 10)
        
        # Publish unified state
        self.pub = self.create_publisher(JointState, '/joint_states', 10)
        
        # Timer: publish at 15 Hz
        self.timer = self.create_timer(1/15.0, self.publish_unified)
    
    def callback(self, msg, arm_name):
        with self.lock:
            # Prefix joint names
            prefixed = JointState()
            prefixed.name = [f"{arm_name}_{j}" for j in msg.name]
            prefixed.position = msg.position
            prefixed.velocity = msg.velocity
            prefixed.effort = msg.effort
            self.arm_states[arm_name] = prefixed
    
    def publish_unified(self):
        with self.lock:
            # Only publish when both arms have reported
            if None in self.arm_states.values():
                return
            
            unified = JointState()
            unified.header.stamp = self.get_clock().now().to_msg()
            for state in self.arm_states.values():
                unified.name.extend(state.name)
                unified.position.extend(state.position)
                unified.velocity.extend(state.velocity)
                unified.effort.extend(state.effort)
        
        self.pub.publish(unified)
```

The critical detail is the startup guard: the manager withholds publication until both arms have reported at least one message. Publishing a partial state (only 6 of 12 DOF) to the Robot State Publisher causes it to compute transforms with undefined joint positions — producing incorrect collision geometry in the planning scene.

---

## The MORS Passive Joints

The Niryo NED2 URDF contains four passive joints for the gripper mechanism (the `mors_joint` assemblage). These joints are not actuated and do not appear in the hardware joint state message. The Robot State Publisher requires values for all joints in the URDF — including passive ones — to compute a complete TF tree.

The `JointStateManager` injects fixed zero-value entries for these passive joints on every publish cycle:

```python
# Pseudocode: passive joint injection
PASSIVE_JOINTS = ['arm_1_mors_1', 'arm_1_mors_2', 'arm_2_mors_1', 'arm_2_mors_2']

def publish_unified(self):
    # ... merge active joints ...
    
    # Inject passive joints at fixed values
    unified.name.extend(PASSIVE_JOINTS)
    unified.position.extend([0.0] * len(PASSIVE_JOINTS))
    unified.velocity.extend([0.0] * len(PASSIVE_JOINTS))
    unified.effort.extend([0.0] * len(PASSIVE_JOINTS))
```

The result: `/joint_states` contains 16 DOF (12 active + 4 passive) at 15 Hz, providing a complete representation to all downstream consumers.

---

## Publication Rate

The manager publishes at 15 Hz — the native rate of the Niryo hardware drivers. The timer is set to 1/15.0 s. If either arm's driver publishes at a lower rate during high load, the manager continues publishing the last known state for that arm. This prevents the planning scene from going stale if one driver momentarily lags.

---

## Transparency to Downstream Consumers

The design goal is that no downstream consumer requires modification. MoveIt2, the Robot State Publisher, and RViz2 all receive standard ROS2 messages on standard topic names. The namespace complexity is fully contained within the `JointStateManager`. This is tested empirically: all three coordination modes, 100 collision tests, and all pick-and-place trials operate against an unchanged MoveIt2 stack.
