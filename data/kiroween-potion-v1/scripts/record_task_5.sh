#!/bin/bash
# Record episodes for: Pick up the eyeball and place it in the purple cup
# Task 5
# This script ADDS to the existing dataset (--resume=true)

lerobot-record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM1 \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{ camera1: {type: intelrealsense, serial_number_or_name: '030522070314', width: 640, height: 480, fps: 30}, camera2: {type: opencv, index_or_path: 8, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM0 \
    --teleop.id=my_awesome_leader_arm \
    --display_data=true \
    --dataset.repo_id=jlamperez/kiroween-potion-v1 \
    --dataset.num_episodes=10 \
    --dataset.episode_time_s=15 \
    --dataset.reset_time_s=20 \
    --dataset.single_task="Pick up the eyeball and place it in the purple cup" \
    --resume=true
