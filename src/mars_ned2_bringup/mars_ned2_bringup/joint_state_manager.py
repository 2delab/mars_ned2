#!/usr/bin/env python3

import threading
from typing import Dict, Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from sensor_msgs.msg import JointState


class JointStateManager(Node):
    def __init__(self):
        super().__init__("joint_state_manager")

        self.declare_parameter("robot_namespaces", ["arm_1", "arm_2"])
        self.declare_parameter("publish_frequency", 40.0)

        self.namespaces = self.get_parameter("robot_namespaces").value
        self.pub_freq = self.get_parameter("publish_frequency").value

        if not self.namespaces:
            raise ValueError("robot_namespaces cannot be empty")

        callback_group = MutuallyExclusiveCallbackGroup()

        self.joint_states: Dict[str, Optional[JointState]] = {
            ns: None for ns in self.namespaces
        }
        self.state_lock = threading.Lock()

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.joint_state_pub = self.create_publisher(JointState, "/joint_states", qos)

        for ns in self.namespaces:
            self.create_subscription(
                JointState,
                f"/{ns}/joint_states",
                lambda msg, namespace=ns: self._on_joint_state(msg, namespace),
                qos,
                callback_group=callback_group,
            )

        self.create_timer(
            1.0 / self.pub_freq,
            self._publish_combined_states,
            callback_group=callback_group,
        )

        self.get_logger().info(
            f"Joint State Manager started for {self.namespaces} at {self.pub_freq}Hz"
        )

    def _on_joint_state(self, msg: JointState, namespace: str):
        with self.state_lock:
            self.joint_states[namespace] = msg

    def _publish_combined_states(self):
        with self.state_lock:
            if any(state is None for state in self.joint_states.values()):
                return

            combined = JointState()
            combined.header.stamp = self.get_clock().now().to_msg()

            for ns in sorted(self.joint_states.keys()):
                arm_state = self.joint_states[ns]
                num_joints = len(arm_state.name)

                combined.name.extend([f"{ns}_{joint}" for joint in arm_state.name])
                combined.position.extend(arm_state.position)

                if arm_state.velocity:
                    combined.velocity.extend(arm_state.velocity)
                else:
                    combined.velocity.extend([0.0] * num_joints)

                if arm_state.effort:
                    combined.effort.extend(arm_state.effort)
                else:
                    combined.effort.extend([0.0] * num_joints)

                combined.name.extend(
                    [f"{ns}_joint_base_to_mors_1", f"{ns}_joint_base_to_mors_2"]
                )
                combined.position.extend([0.0, 0.0])
                combined.velocity.extend([0.0, 0.0])
                combined.effort.extend([0.0, 0.0])

            if combined.name:
                self.joint_state_pub.publish(combined)


def main(args=None):
    rclpy.init(args=args)
    node = JointStateManager()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
