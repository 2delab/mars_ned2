#!/usr/bin/env python3

import os
import rclpy
from ament_index_python.packages import get_package_share_directory
from moveit.planning import MoveItPy
from geometry_msgs.msg import PoseStamped

rclpy.init()

config_file = os.path.join(
    get_package_share_directory("niryo_ned2_dual_arm_moveit_config"),
    "config",
    "moveit_py_params.yaml",
)
moveit_py = MoveItPy(node_name="moveit_py_test", launch_params_filepaths=[config_file])

arm_2 = moveit_py.get_planning_component("arm_2")
arm_2.set_start_state_to_current_state()

pose_goal = PoseStamped()
pose_goal.header.frame_id = "arm_2_base_link"
pose_goal.pose.position.x = 0.4
pose_goal.pose.position.y = 0.1
pose_goal.pose.position.z = 0.4
pose_goal.pose.orientation.x = 0.0
pose_goal.pose.orientation.y = 0.0
pose_goal.pose.orientation.z = 0.0
pose_goal.pose.orientation.w = 1.0

arm_2.set_goal_state(pose_stamped_msg=pose_goal, pose_link="arm_2_tool_link")

plan_result = arm_2.plan()
if plan_result:
    moveit_py.execute(plan_result.trajectory, controllers=[])

rclpy.shutdown()
