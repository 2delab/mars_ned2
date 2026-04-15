#!/usr/bin/env python3
"""
Async Init Library - Handles MoveItPy initialization.
"""

from moveit.planning import MoveItPy


def initialize_moveit_instances(config_file, config_file_dual):
    """
    Initialize MoveItPy instances and planning components.

    Args:
        config_file: Path to the dual gripper config file
        config_file_dual: Path to the dual arm config file

    Returns:
        Tuple of (moveit_py_1, moveit_py_2, moveit_py_dual, arm_1, arm_2)
    """
    print("Creating MoveItPy instances...")
    moveit_py_1 = MoveItPy(
        node_name="moveit_py_arm1", launch_params_filepaths=[config_file]
    )
    moveit_py_2 = MoveItPy(
        node_name="moveit_py_arm2", launch_params_filepaths=[config_file]
    )
    moveit_py_dual = MoveItPy(
        node_name="moveit_py_dual", launch_params_filepaths=[config_file_dual]
    )

    arm_1 = moveit_py_1.get_planning_component("arm_1")
    arm_2 = moveit_py_2.get_planning_component("arm_2")

    arm_1.set_start_state_to_current_state()
    arm_2.set_start_state_to_current_state()

    print("✓ MoveItPy instances created")

    return moveit_py_1, moveit_py_2, moveit_py_dual, arm_1, arm_2
