import os
from pathlib import Path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

from rclpy import logging

logger = logging.get_logger("mars_ned2.launch")


def generate_launch_description():
    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value="moveit.rviz",
        description="RViz configuration file",
    )

    load_scene_arg = DeclareLaunchArgument(
        "load_scene",
        default_value="true",
        description="Load workspace planning scene on startup",
    )

    urdf_file = os.path.join(
        get_package_share_directory("niryo_ned_description"),
        "urdf/ned2",
        "niryo_ned2_dual_arm.urdf.xacro",
    )

    moveit_config = (
        MoveItConfigsBuilder("niryo_ned2_dual_arm")
        .robot_description(
            file_path=urdf_file,
        )
        .joint_limits(file_path="config/joint_limits.yaml")
        .robot_description_semantic(file_path="config/niryo_ned2_dual_arm.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(
            pipelines=["ompl", "chomp", "pilz_industrial_motion_planner"]
        )
        .to_moveit_configs()
    )

    joint_state_manager_node = Node(
        package="mars_ned2_bringup",
        executable="joint_state_manager.py",
        output="screen",
        parameters=[
            {"robot_namespaces": ["arm_1", "arm_2"]},
            {"publish_frequency": 15.0},
        ],
    )

    trajectory_proxy_node = Node(
        package="mars_ned2_bringup",
        executable="trajectory_proxy.py",
        output="screen",
        parameters=[
            {"robot_namespaces": ["arm_1", "arm_2"]},
            {"trajectory_timeout_sec": 120.0},
            {"server_timeout_sec": 30.0},
        ],
    )

    rsp_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        respawn=True,
        output="screen",
        parameters=[
            moveit_config.robot_description,
            {"publish_frequency": 15.0},
        ],
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {
                "publish_robot_description_semantic": True,
            },
        ],
        arguments=["--ros-args", "--log-level", "info"],
    )

    rviz_base = LaunchConfiguration("rviz_config")
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("niryo_ned2_dual_arm_moveit_config"), "config", rviz_base]
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
        ],
    )

    return LaunchDescription(
        [
            rviz_config_arg,
            load_scene_arg,
            joint_state_manager_node,
            trajectory_proxy_node,
            rsp_node,
            move_group_node,
            rviz_node,
        ]
    )
