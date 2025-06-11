#!/usr/bin/env python3
# -*-coding:utf8-*-
# 注意：此代码需要在安装并配置好 piper_sdk 的环境下运行

import time
import math
from typing import Optional
from piper_sdk import *

def enable_fun(piper: C_PiperInterface_V2):
    '''
    使能机械臂并检测使能状态,尝试5s,如果使能超时则退出程序
    '''
    enable_flag = False
    timeout = 5
    start_time = time.time()
    elapsed_time_flag = False
    while not enable_flag:
        elapsed_time = time.time() - start_time
        print("--------------------")
        enable_flag = (
            piper.GetArmLowSpdInfoMsgs().motor_1.foc_status.driver_enable_status and
            piper.GetArmLowSpdInfoMsgs().motor_2.foc_status.driver_enable_status and
            piper.GetArmLowSpdInfoMsgs().motor_3.foc_status.driver_enable_status and
            piper.GetArmLowSpdInfoMsgs().motor_4.foc_status.driver_enable_status and
            piper.GetArmLowSpdInfoMsgs().motor_5.foc_status.driver_enable_status and
            piper.GetArmLowSpdInfoMsgs().motor_6.foc_status.driver_enable_status
        )
        print("使能状态:", enable_flag)
        piper.EnableArm(7)
        piper.GripperCtrl(0, 1000, 0x01, 0)
        print("--------------------")
        if elapsed_time > timeout:
            print("超时....")
            elapsed_time_flag = True
            break
        time.sleep(1)
    
    if elapsed_time_flag:
        print("程序自动使能超时,退出程序")
        exit(0)

def is_close_to_target(current_pose_msg, target_pose_list, tolerance=5.0):
    """
    检查机械臂当前位置是否足够接近目标位置。
    :param current_pose_msg: 从 piper.GetArmEndPoseMsgs() 获取的当前位置消息
    :param target_pose_list: 目标位置列表 [x, y, z, rx, ry, rz]
    :param tolerance: 容差范围 (mm)
    :return: True 如果足够接近, False 否则
    """
    # SDK返回的位置也需要除以factor来比较
    factor = 1000.0
    current_x = current_pose_msg.x / factor
    current_y = current_pose_msg.y / factor
    current_z = current_pose_msg.z / factor
    
    target_x = target_pose_list[0]
    target_y = target_pose_list[1]
    target_z = target_pose_list[2]
    
    # 计算欧氏距离的平方（避免开方，提高效率）
    distance_sq = (current_x - target_x)**2 + (current_y - target_y)**2 + (current_z - target_z)**2
    
    return distance_sq < tolerance**2


if __name__ == "__main__":
    piper = C_PiperInterface_V2("can0")
    piper.ConnectPort()
    enable_fun(piper=piper)
    
    factor = 1000  # SDK坐标缩放因子

    # ==================== 直线运动参数设置 ====================
    # 1. 定义起始点 A (单位: mm 和 度)
    start_pose = [100.0, -50.0, 250.0, 0.0, 90.0, 0.0]
    
    # 2. 定义终点 B (单位: mm 和 度)
    end_pose = [100.0, 50.0, 250.0, 0.0, 90.0, 0.0]

    # 3. 运动参数
    pause_time = 2.0  # 到达目标点后暂停的时间 (秒)
    # ==========================================================

    # 初始化目标
    current_target_pose = start_pose
    moving_to_end = True  # True表示当前目标是终点B, False表示当前目标是起点A

    print("即将开始直线往复运动...")
    print(f"起始点A: {start_pose}")
    print(f"终点B: {end_pose}")
    time.sleep(3)

    # 进入主循环
    while True:
        # 1. 发送当前的目标点位指令
        X = round(current_target_pose[0] * factor)
        Y = round(current_target_pose[1] * factor)
        Z = round(current_target_pose[2] * factor)
        RX = round(current_target_pose[3] * factor)
        RY = round(current_target_pose[4] * factor)
        RZ = round(current_target_pose[5] * factor)
        
        piper.MotionCtrl_2(0x01, 0x00, 100, 0x00) # 设置运动模式和速度
        piper.EndPoseCtrl(X, Y, Z, RX, RY, RZ)
        
        # 2. 打印当前状态
        current_pose = piper.GetArmEndPoseMsgs()

            
        # 3. 检查是否已到达目标
        if is_close_to_target(current_pose, current_target_pose):
            if moving_to_end:
                print("已到达终点 B。")
                current_target_pose = start_pose # 切换目标到起点
                moving_to_end = False
            else:
                print("已到达起始点 A。")
                current_target_pose = end_pose # 切换目标到终点
                moving_to_end = True
            
            print(f"暂停 {pause_time} 秒...")
            time.sleep(pause_time) # 暂停
        
        # 循环延时
        time.sleep(0.1)