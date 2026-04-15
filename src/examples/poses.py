#!/usr/bin/env python3

import os
import sys
import time
import threading
import rclpy
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from moveit_msgs.msg import CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose

sys.path.insert(0, os.path.dirname(__file__))
from async_init_lib import initialize_moveit_instances

ORIENTATIONS = {
    "default": {"x": 0.0, "y": 0.7071, "z": 0.0, "w": 0.7071},
    "orientation_1": {"x": 0.468, "y": 0.561, "z": -0.435, "w": 0.568},
    "orientation_2": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
}

TASKS = [
    {
        "name": "Task 1",
        "arm_1": {
            "poses": [
                {"position": (0.2, 0.0, 0.35), "orientation": "orientation_2"},
                {"position": (0.2, 0.0, 0.35), "orientation": "efault"},
                {"position": (0.3, 0.0, 0.35), "orientation": "orientation_2"},
            ]
        },
        "arm_2": {
            "poses": [
                {"position": (0.2, 0.0, 0.35), "orientation": "orientation_2"},
                {"position": (0.2, 0.0, 0.35), "orientation": "default"},
                {"position": (0.3, 0.0, 0.35), "orientation": "orientation_2"},
            ]
        },
    },
    {
        "name": "Task 2",
        "arm_1": {
            "poses": [
                {"position": (0.2, 0.03, 0.35), "orientation": "default"},
                {"position": (0., 0.0, 0.35), "orientation": "orientation_1"},
                {"position": (0.3, 0.03, 0.35), "orientation": "default"},
            ]
        },
        "arm_2": {
            "poses": [
                {"position": (0.2, -0.03, 0.35), "orientation": "default"},
                {"position": (0.3, 0.0, 0.35), "orientation": "orientation_1"},
                {"position": (0.2, -0.03, 0.35), "orientation": "default"},
            ]
        },
    },
]

rclpy.init()

config_file_single = os.path.join(
    get_package_share_directory("niryo_ned2_dual_gripper_moveit_config"),
    "config",
    "moveit_py_params.yaml",
)
config_file_dual = os.path.join(
    get_package_share_directory("niryo_ned2_dual_arm_moveit_config"),
    "config",
    "moveit_py_params.yaml",
)

moveit_py_1, moveit_py_2, moveit_py_dual, arm_1, arm_2 = initialize_moveit_instances(
    config_file_single, config_file_dual
)

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
with moveit_py_dual.get_planning_scene_monitor().read_write() as scene:
    scene.apply_collision_object(platform)

for task in TASKS:
    for spec1, spec2 in zip(task["arm_1"]["poses"], task["arm_2"]["poses"]):
        x1, y1, z1 = spec1["position"]
        x2, y2, z2 = spec2["position"]
        o1 = ORIENTATIONS[spec1.get("orientation", "default")]
        o2 = ORIENTATIONS[spec2.get("orientation", "default")]

        ps1 = PoseStamped()
        ps1.header.frame_id = "arm_1_base_link"
        ps1.pose.position.x, ps1.pose.position.y, ps1.pose.position.z = x1, y1, z1
        ps1.pose.orientation.x, ps1.pose.orientation.y = o1["x"], o1["y"]
        ps1.pose.orientation.z, ps1.pose.orientation.w = o1["z"], o1["w"]

        ps2 = PoseStamped()
        ps2.header.frame_id = "arm_2_base_link"
        ps2.pose.position.x, ps2.pose.position.y, ps2.pose.position.z = x2, y2, z2
        ps2.pose.orientation.x, ps2.pose.orientation.y = o2["x"], o2["y"]
        ps2.pose.orientation.z, ps2.pose.orientation.w = o2["z"], o2["w"]

        arm_1.set_start_state_to_current_state()
        arm_2.set_start_state_to_current_state()
        arm_1.set_goal_state(pose_stamped_msg=ps1, pose_link="arm_1_tool_link")
        arm_2.set_goal_state(pose_stamped_msg=ps2, pose_link="arm_2_tool_link")

        plan_result_1 = arm_1.plan()
        plan_result_2 = arm_2.plan()

        if plan_result_1 and plan_result_2:
            t1 = threading.Thread(
                target=lambda r=plan_result_1: moveit_py_1.execute(
                    r.trajectory, controllers=[]
                )
            )
            t2 = threading.Thread(
                target=lambda r=plan_result_2: moveit_py_2.execute(
                    r.trajectory, controllers=[]
                )
            )
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        time.sleep(0.5)

rclpy.shutdown()
