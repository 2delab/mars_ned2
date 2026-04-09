---
layout: single
title: "Transport Frames"
date: 2026-02-13
classes: wide
author_profile: false
---

# ROS 2 Transform Library (tf2)

The Transform (tf2) library is the backbone of spatial reasoning in ROS 2. If you've ever wondered how a robot knows where its sensors are relative to its wheels, or how it tracks objects in 3D space, tf2 is your answer.

## What is tf2?
tf2 manages coordinate frame transformations across time. Think of it as a dynamic 3D graph where nodes represent coordinate frames (like "base_link", "camera", "map") and edges represent the spatial relationships between them. The library handles:
- Broadcasting transforms between frames
- Looking up transforms at specific times
- Interpolating between transforms
- Managing transform trees

![tf](/mars_ned2/assets/images/tf1.png){: .align-center}

![tf](/mars_ned2/assets/images/tf2.png){: .align-center}

## The Core Architecture
### Transform Broadcaster
Broadcasting is how you tell the world about spatial relationships. Every node that knows about a transform should publish it:
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
        t.header.frame_id = 'world'
        t.child_frame_id = 'robot'
        # Position
        t.transform.translation.x = 1.0
        t.transform.translation.y = 2.0
        t.transform.translation.z = 0.0
        # Rotation (quaternion)
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0
        self.br.sendTransform(t)
```
**Key insight**: Transforms should be published continuously, typically at 10-100 Hz depending on how dynamic the relationship is.

### Transform Listener
To use transforms, you need a listener with a buffer:
```python
from tf2_ros import TransformListener, Buffer
from rclpy.duration import Duration
class FrameListener(Node):
    def __init__(self):
        super().__init__('frame_listener')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
    def lookup_transform(self):
        try:
            # Look up transform from 'world' to 'robot' at current time
            trans = self.tf_buffer.lookup_transform(
                'world',
                'robot',
                rclpy.time.Time(),
                timeout=Duration(seconds=1.0)
            )
            return trans
        except Exception as e:
            self.get_logger().error(f'Transform lookup failed: {e}')
            return None
```
The buffer stores transform history (default: 10 seconds), enabling time-based queries.

## Static vs Dynamic Transforms
**Static transforms** never change—like the relationship between a camera mount and the camera itself:
```python
from tf2_ros import StaticTransformBroadcaster
self.static_broadcaster = StaticTransformBroadcaster(self)
self.static_broadcaster.sendTransform(static_transform)
```
Static transforms are published once and latched, saving bandwidth.

**Dynamic transforms** change over time—like a robot's position in the world or a moving sensor. These need continuous publishing.

## Transform Trees: The Rules
1. **One parent per frame**: Each frame has exactly one parent (except the root)
2. **No cycles**: The tree must be acyclic
3. **Connected graph**: All frames must connect to a common root
4. **Unique names**: Frame IDs must be unique
Violating these causes lookup failures. Use `ros2 run tf2_tools view_frames` to visualize your tree and catch issues.

## Time Travel with tf2
One of tf2's superpowers is temporal queries. Imagine you receive sensor data timestamped 100ms ago—you can look up where frames were _at that exact moment_:
```python
# Look up transform as it was when sensor data was captured
past_time = rclpy.time.Time(seconds=sensor_msg.header.stamp.sec,
                             nanoseconds=sensor_msg.header.stamp.nanosec)
trans = self.tf_buffer.lookup_transform(
    'map',
    'sensor',
    past_time,
    timeout=Duration(seconds=0.5)
)
```
This is critical for sensor fusion and maintaining temporal consistency.

## Advanced Patterns
### Transform Point Clouds
```python
from tf2_sensor_msgs import do_transform_cloud
transformed_cloud = do_transform_cloud(original_cloud, transform)
```

### Wait for Transform
```python
# Block until transform becomes available
if self.tf_buffer.can_transform('map', 'base_link', rclpy.time.Time()):
    trans = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
```

### Exception Handling
tf2 throws specific exceptions:
- `LookupException`: Transform doesn't exist
- `ConnectivityException`: Frames aren't connected in the tree
- `ExtrapolationException`: Requested time outside buffer range
Always catch and handle these appropriately.

## Debugging tf2
**View the current tree:**
```bash
ros2 run tf2_tools view_frames
```
![tf](/mars_ned2/assets/images/tf_tree.png){: .align-center}

**Echo transforms in real-time:**
```bash
ros2 run tf2_ros tf2_echo map base_link
```

**Monitor tf2 messages:**
```bash
ros2 topic echo /tf
ros2 topic echo /tf_static
```

## Performance Considerations
- **Buffer size**: Default 10-second cache balances memory and utility
- **Publishing rate**: Match the dynamics of your transform (faster for moving frames)
- **Lookup frequency**: Cache transforms when possible rather than looking up repeatedly
- **Thread safety**: tf2 buffers are thread-safe for lookups, but broadcasters are not

## Common Pitfalls
**Time synchronization**: If system clocks aren't synced across machines, tf2 breaks. Use NTP or PTP for distributed systems.

**Zero timestamps**: `rclpy.time.Time()` means "latest available." Never use actual zero timestamps—they're invalid.

**Quaternion normalization**: Always normalize quaternions. tf2 won't do it for you.

**Frame naming**: Use consistent naming conventions. Slashes have special meaning in some contexts—avoid them in frame names.

## Real-World Example: Robot Localization
Here's how tf2 typically flows in a mobile robot:
1. `map` → `odom`: Published by localization (AMCL, SLAM)
2. `odom` → `base_link`: Published by odometry (wheel encoders, IMU fusion)
3. `base_link` → `sensors`: Static transforms from URDF
This three-tier structure separates:
- **Long-term consistency** (map)
- **Short-term accuracy** (odom)
- **Physical structure** (sensors)

## Takeaways
- tf2 is essential for spatial reasoning in ROS 2—master it early
- Always publish transforms continuously (except static ones)
- Use time-aware queries for sensor fusion
- Visualize your transform tree regularly
- Handle exceptions gracefully
- Keep your tree simple and well-structured

Transform management might seem mundane, but it's what turns a collection of sensors into a spatially-aware robot.