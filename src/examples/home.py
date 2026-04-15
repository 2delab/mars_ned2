#!/usr/bin/env python3

import os
import rclpy
from ament_index_python.packages import get_package_share_directory
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState
from moveit_msgs.msg import CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose

rclpy.init()

config_file = os.path.join(
    get_package_share_directory("niryo_ned2_dual_arm_moveit_config"),
    "config",
    "moveit_py_params.yaml",
)
moveit_py = MoveItPy(node_name="moveit_py_test", launch_params_filepaths=[config_file])

platform = CollisionObject()
platform.header.frame_id = "world"
platform.id = "workspace_platform"
platform.operation = bytes([0])

primitive = SolidPrimitive()
primitive.type = SolidPrimitive.BOX
primitive.dimensions = [3.0, 3.0, 0.01]
platform.primitives.append(primitive)

pose = Pose()
pose.position.z = -0.015
pose.orientation.w = 1.0
platform.primitive_poses.append(pose)

with moveit_py.get_planning_scene_monitor().read_write() as scene:
    scene.apply_collision_object(platform)

dual_arm = moveit_py.get_planning_component("dual")
robot_state = RobotState(moveit_py.get_robot_model())

dual_arm.set_start_state_to_current_state()
robot_state.set_joint_group_positions("arm_1", [0, 0, 0, 0, 0, 0])
robot_state.set_joint_group_positions("arm_2", [0, 0, 0, 0, 0, 0])
dual_arm.set_goal_state(robot_state=robot_state)

plan_result = dual_arm.plan()
if plan_result:
    moveit_py.execute(plan_result.trajectory, controllers=[])

rclpy.shutdown()
