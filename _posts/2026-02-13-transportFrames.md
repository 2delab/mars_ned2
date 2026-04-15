---
layout: single
title: "Transport Frames"
header:
  teaser: /assets/images/posts/transport_frames.png
date: 2026-02-13
classes: wide
author_profile: false
---

# ROS2 Transform Library (tf2)

The Transform Library is the mechanism by which the robot knows where every link is. The planning scene, IK solver, and collision checker all consume the TF tree directly. 

## The NED2 Single-Arm TF Tree

The `robot_state_publisher` node reads the URDF, subscribes to `/joint_states`, and publishes a live transform for every joint in the kinematic chain. For the NED2, that produces the following tree:

```
base_link
  └── shoulder_link       (joint_1, revolute, dynamic)
        └── arm_link      (joint_2, revolute, dynamic)
              └── elbow_link          (joint_3, revolute, dynamic)
                    └── forearm_link  (joint_4, revolute, dynamic)
                          └── wrist_link   (joint_5, revolute, dynamic)
                                └── hand_link    (joint_6, revolute, dynamic)
                                      └── tool_link    (fixed, static)
                                            └── camera_link  (fixed, static)
```

Six transforms are **dynamic**: they change with every joint movement and are published continuously as RSP processes incoming `/joint_states` messages. Two are **static**: `tool_link` and `camera_link` are bolted to the wrist; their relationship to `hand_link` never changes and is published once and latched.


![tf](/mars_ned2/assets/images/tf1.png){: .align-center}

![tf](/mars_ned2/assets/images/tf2.png){: .align-center}

---

## What is tf2?

tf2 manages coordinate frame transformations across time. It maintains a directed tree where each node is a named coordinate frame and each edge is the spatial transform between a parent and child frame. The library handles:

- Broadcasting transforms between frames
- Looking up transforms at specific times
- Interpolating between transforms
- Managing the full transform tree

Any node in the system can query: "what is the pose of frame A expressed in frame B, at time T?" tf2 walks the tree from A to the common ancestor of A and B, then down to B, composing the chain of transforms. If any transform in that chain is missing or outside the buffer's time range, the query throws.

---

## The Core Architecture

### Transform Broadcaster

Broadcasting is how a node publishes a spatial relationship. Every node that owns a transform should publish it:

```python
from geometry_msgs.msg import TransformStamped
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster

class FramePublisher(Node):
    def __init__(self):
        super().__init__('frame_publisher')
        self.br = TransformBroadcaster(self)

    def publish_transform(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'shoulder_link'
        # Translation from base_link origin to shoulder_link origin
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.103  # 103 mm base height
        # Rotation as quaternion
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0
        self.br.sendTransform(t)
```

Dynamic transforms should be published continuously, typically at 10–100 Hz. For the NED2, `robot_state_publisher` handles this automatically from `/joint_states`. A custom broadcaster like the above is needed when publishing a transform not derived from joint states, for example a detected object's pose relative to the camera frame.

### Transform Listener

To use transforms, create a listener backed by a buffer:

```python
from tf2_ros import TransformListener, Buffer
from rclpy.duration import Duration

class FrameListener(Node):
    def __init__(self):
        super().__init__('frame_listener')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def get_tool_pose(self):
        try:
            # Where is tool_link right now, expressed in base_link frame?
            trans = self.tf_buffer.lookup_transform(
                'base_link',
                'tool_link',
                rclpy.time.Time(),
                timeout=Duration(seconds=1.0)
            )
            return trans
        except Exception as e:
            self.get_logger().error(f'Transform lookup failed: {e}')
            return None
```

The buffer stores transform history (default: 10 seconds), enabling time-based queries. `rclpy.time.Time()` with no arguments means "latest available", the most recent transform in the buffer.

---

## Static vs Dynamic Transforms

**Static transforms** never change. For the NED2 these are the fixed joints, such as the camera mount on the wrist and the tool adapter on the hand:

```python
from tf2_ros import StaticTransformBroadcaster

self.static_broadcaster = StaticTransformBroadcaster(self)
self.static_broadcaster.sendTransform(static_transform)
```

Static transforms are published once and latched. Any new subscriber receives the last published value immediately. `robot_state_publisher` handles static transforms from the URDF's `<joint type="fixed">` elements automatically; there is no need to publish them manually unless adding a frame outside the URDF.

**Dynamic transforms** change over time. For the NED2 these are the six revolute joints. They require continuous publishing: RSP republishes them every time a new `/joint_states` message arrives. The transform tree is only as current as the most recent joint state.

---

## Transform Trees: The Rules

1. **One parent per frame**: each frame has exactly one parent (except the root)
2. **No cycles**: the tree must be acyclic
3. **Connected graph**: all frames must connect to a common root
4. **Unique names**: frame IDs must be globally unique

Violating any of these causes lookup failures. The tree rules have a practical consequence for multi-robot systems: two robots with separate TF trees rooted at different frames cannot have their frames queried against each other. Cross-robot transform queries require a common root that both trees connect to. This is why the choice of root frame matters when multiple robots share a workspace.

```bash
ros2 run tf2_tools view_frames
```

![tf](/mars_ned2/assets/images/tf_tree.png){: .align-center}

`view_frames` renders the live tree to a PDF. It is the first tool to reach for when a transform lookup fails; it shows exactly which frames exist, which are connected, and at what rates they are being published.

---

## Time and tf2

One of tf2's most important capabilities is temporal queries. When sensor data arrives with a timestamp from the past, you can look up where frames were at that exact moment:

```python
# Where was the camera when this image was captured?
image_time = rclpy.time.Time(
    seconds=image_msg.header.stamp.sec,
    nanoseconds=image_msg.header.stamp.nanosec
)
trans = self.tf_buffer.lookup_transform(
    'base_link',
    'camera_link',
    image_time,
    timeout=Duration(seconds=0.5)
)
```

---

## Advanced Patterns

### Wait for Transform

```python
# Block until the tool_link transform is available before commanding motion
if self.tf_buffer.can_transform('base_link', 'tool_link', rclpy.time.Time()):
    trans = self.tf_buffer.lookup_transform('base_link', 'tool_link', rclpy.time.Time())
```

At startup there is a race: the listener is created, but `robot_state_publisher` may not have published its first transform yet. Querying immediately throws `LookupException`. The `can_transform()` check with a timer loop, or `wait_for_transform()` in the launch sequence, prevents this.

### Exception Handling

tf2 throws specific exceptions:

- `LookupException`: the requested frame does not exist in the tree
- `ConnectivityException`: the frames exist but there is no path connecting them
- `ExtrapolationException`: the requested timestamp is outside the buffer's history range

Always catch and handle these. A generic `except Exception` works for prototyping; in production code, catching the specific exception type and responding appropriately (retry, abort, log) matters.

---

## Debugging tf2

**View the current tree:**
```bash
ros2 run tf2_tools view_frames
```

**Echo a specific transform in real-time:**
```bash
ros2 run tf2_ros tf2_echo base_link tool_link
```

**Monitor all published transforms:**
```bash
ros2 topic echo /tf
ros2 topic echo /tf_static
```

The distinction between `/tf` (dynamic) and `/tf_static` (static, latched) is useful for diagnosing publish rate problems: if `/tf` is silent but `/tf_static` is publishing, the dynamic joint state pipeline has stopped somewhere.

---

## Performance Considerations

- **Buffer size**: default 10-second cache. For slow-moving arms this is generous; for high-frequency replanning, a shorter buffer reduces memory pressure without losing useful history
- **Publishing rate**: match the dynamics of the frame. Joint transforms for the NED2 at 50 Hz hardware rate are fine; a stationary camera mount needs no republishing after the static transform is latched
- **Lookup frequency**: cache transforms when possible. A motion monitoring loop that calls `lookup_transform` at 100 Hz is querying the buffer 100 times per second for values that may change at 15 Hz; most queries return the same result. Cache the result and refresh only on new `/joint_states` callbacks
- **Thread safety**: tf2 buffers are thread-safe for reads (lookups can be called from any thread); broadcasters are not thread-safe and should be called from a single thread

---

## Common Pitfalls

**Time synchronisation**: on a distributed system (e.g. a laptop running ROS2 and a robot controller running a separate clock), unsynchronised clocks cause every temporal query to fail with `ExtrapolationException`. Use NTP or PTP. On a single machine this is not an issue.

**Zero timestamps**: `rclpy.time.Time()` (no arguments) means "latest available transform." Passing an explicit zero timestamp (`rclpy.time.Time(seconds=0)`) is invalid and will throw. Always use the no-argument form for current-time queries.

**Frame naming**: use consistent conventions and avoid slashes in frame names. `arm_1/tool_link` is not the same as `arm_1_tool_link` and some tf2 tools handle slashes inconsistently.

---

