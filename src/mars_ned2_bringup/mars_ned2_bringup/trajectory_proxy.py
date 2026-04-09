#!/usr/bin/env python3

import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient, GoalResponse, CancelResponse
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory


class TrajectoryProxy(Node):
    def __init__(self):
        super().__init__("trajectory_proxy")

        self.declare_parameter("robot_namespaces", ["arm_1", "arm_2"])
        self.declare_parameter("trajectory_timeout_sec", 120.0)
        self.declare_parameter("server_timeout_sec", 30.0)

        self.namespaces = self.get_parameter("robot_namespaces").value
        self.traj_timeout = self.get_parameter("trajectory_timeout_sec").value
        self.srv_timeout = self.get_parameter("server_timeout_sec").value

        if not self.namespaces:
            raise ValueError("robot_namespaces cannot be empty")

        self.action_callback_group = ReentrantCallbackGroup()

        self.traj_servers = {}
        self.hw_clients = {}

        self._setup_trajectory_proxy()

        self.get_logger().info(
            f"Trajectory Proxy started for {self.namespaces}, "
            f"server_timeout={self.srv_timeout}s, traj_timeout={self.traj_timeout}s"
        )

    def _setup_trajectory_proxy(self):
        for ns in self.namespaces:
            self.traj_servers[ns] = ActionServer(
                self,
                FollowJointTrajectory,
                f"/{ns}/follow_joint_trajectory_prefixed",
                execute_callback=lambda gh, namespace=ns: self._execute_trajectory(
                    gh, namespace
                ),
                goal_callback=lambda _: GoalResponse.ACCEPT,
                cancel_callback=lambda _: CancelResponse.ACCEPT,
                callback_group=self.action_callback_group,
            )

            self.hw_clients[ns] = ActionClient(
                self,
                FollowJointTrajectory,
                f"/{ns}/niryo_robot_follow_joint_trajectory_controller/follow_joint_trajectory",
                callback_group=self.action_callback_group,
            )

            self.get_logger().info(f"[{ns}] Setup complete")

    def _execute_trajectory(self, goal_handle, namespace: str):
        try:
            self.get_logger().info(f"[{namespace}] Executing trajectory")

            trajectory = goal_handle.request.trajectory
            unprefixed_trajectory = self._remove_prefix(trajectory, namespace)

            hw_client = self.hw_clients[namespace]

            if not hw_client.wait_for_server(timeout_sec=self.srv_timeout):
                self.get_logger().error(f"[{namespace}] Hardware server not available")
                goal_handle.abort()
                return self._create_error_result(
                    FollowJointTrajectory.Result.INVALID_GOAL
                )

            hw_goal = FollowJointTrajectory.Goal(trajectory=unprefixed_trajectory)

            def feedback_callback(feedback):
                goal_handle.publish_feedback(feedback.feedback)

            send_future = hw_client.send_goal_async(
                hw_goal, feedback_callback=feedback_callback
            )

            goal_event = threading.Event()
            hw_goal_handle = None
            goal_error = None

            def on_goal_response(future):
                nonlocal hw_goal_handle, goal_error
                try:
                    hw_goal_handle = future.result()
                except Exception as e:
                    goal_error = str(e)
                finally:
                    goal_event.set()

            send_future.add_done_callback(on_goal_response)

            if not goal_event.wait(timeout=self.srv_timeout):
                self.get_logger().error(f"[{namespace}] Goal acceptance timeout")
                goal_handle.abort()
                return self._create_error_result(
                    FollowJointTrajectory.Result.INVALID_GOAL
                )

            if goal_error or not hw_goal_handle:
                self.get_logger().error(
                    f"[{namespace}] Failed to send goal: {goal_error}"
                )
                goal_handle.abort()
                return self._create_error_result(
                    FollowJointTrajectory.Result.INVALID_GOAL
                )

            if not hw_goal_handle.accepted:
                self.get_logger().warn(f"[{namespace}] Goal rejected by hardware")
                goal_handle.abort()
                return self._create_error_result(
                    FollowJointTrajectory.Result.INVALID_GOAL
                )

            self.get_logger().info(
                f"[{namespace}] Goal accepted, waiting for result..."
            )

            result_future = hw_goal_handle.get_result_async()
            result_event = threading.Event()
            hw_result = None
            result_error = None

            def on_result(future):
                nonlocal hw_result, result_error
                try:
                    hw_result = future.result().result
                except Exception as e:
                    result_error = str(e)
                finally:
                    result_event.set()

            result_future.add_done_callback(on_result)

            start_time = self.get_clock().now()
            while not result_event.is_set():
                if goal_handle.is_cancel_requested:
                    self.get_logger().info(f"[{namespace}] Cancelling trajectory")
                    hw_goal_handle.cancel_goal_async()
                    result_event.wait(timeout=1.0)
                    goal_handle.canceled()
                    return self._create_error_result(
                        FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
                    )

                elapsed = (self.get_clock().now() - start_time).nanoseconds / 1e9
                if elapsed > self.traj_timeout:
                    self.get_logger().error(
                        f"[{namespace}] Execution timeout ({elapsed:.1f}s)"
                    )
                    hw_goal_handle.cancel_goal_async()
                    goal_handle.abort()
                    return self._create_error_result(
                        FollowJointTrajectory.Result.GOAL_TOLERANCE_VIOLATED
                    )

                result_event.wait(timeout=0.01)

            if result_error or not hw_result:
                self.get_logger().error(
                    f"[{namespace}] Failed to get result: {result_error}"
                )
                goal_handle.abort()
                return self._create_error_result(
                    FollowJointTrajectory.Result.INVALID_GOAL
                )

            if hw_result.error_code == FollowJointTrajectory.Result.SUCCESSFUL:
                self.get_logger().info(
                    f"[{namespace}] Trajectory completed successfully"
                )
                goal_handle.succeed()
            else:
                self.get_logger().warn(
                    f"[{namespace}] Trajectory failed with code {hw_result.error_code}"
                )
                goal_handle.abort()

            return hw_result

        except Exception as e:
            self.get_logger().error(f"[{namespace}] Exception: {e}")
            import traceback

            self.get_logger().error(traceback.format_exc())
            goal_handle.abort()
            return self._create_error_result(FollowJointTrajectory.Result.INVALID_GOAL)

    def _remove_prefix(
        self, trajectory: JointTrajectory, namespace: str
    ) -> JointTrajectory:
        unprefixed = JointTrajectory()
        unprefixed.header = trajectory.header
        unprefixed.points = trajectory.points

        prefix = f"{namespace}_"
        unprefixed.joint_names = [
            name[len(prefix) :] if name.startswith(prefix) else name
            for name in trajectory.joint_names
        ]

        return unprefixed

    def _create_error_result(self, error_code: int) -> FollowJointTrajectory.Result:
        result = FollowJointTrajectory.Result()
        result.error_code = error_code
        return result


def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryProxy()

    executor = MultiThreadedExecutor(num_threads=8)
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
