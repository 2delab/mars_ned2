from glob import glob
from setuptools import find_packages, setup

package_name = "mars_ned2_bringup"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ros2",
    maintainer_email="2dellab@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "joint_state_manager.py=mars_ned2_bringup.joint_state_manager:main",
            "trajectory_proxy.py=mars_ned2_bringup.trajectory_proxy:main",
        ],
    },
)
