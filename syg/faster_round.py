#!/usr/bin/env python3
# -*-coding:utf8-*-
# 注意：此代码需要在安装并配置好 piper_sdk 的环境下运行

import time
import math  # 导入math库用于计算sin和cos
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

if __name__ == "__main__":
    piper = C_PiperInterface_V2("can0")
    piper.ConnectPort()
    enable_fun(piper=piper)
    
    factor = 1000  # SDK坐标缩放因子

    # ==================== 合法范围内的多点运动参数设置 ====================
    # 定义多个目标点的坐标，确保x, y绝对值 < 50cm, z 在 20cm ~ 50cm 之间
    points = [
        (200, 400, 700),  # 目标点1 (200, 200, 250mm)
        (-200, 0, 700),   # 中间点
        (200, -400, 700), # 目标点2 (-100, -150, 400mm)
        (-200, 0, 700)
        # (0, 0, 500)    # 起始点 (0, 0, 300mm)
        # (50, -50, 300),  # 目标点 (50, -50, 300mm)
        # (300, -100, 200), # 目标点 (300, -100, 200mm)
        # (-200, 100, 350)  # 目标点 (-200, 100, 350mm)
    ]
    
    # 2. 定义速度范围，取值范围是0到100
    speed = 100  # 调整为100，根据需要设置更快或更慢的速度
    
    # 3. 定义固定的末端姿态 (单位: 度)
    fixed_rx = 0.0
    fixed_ry = 0.0
    fixed_rz = 0.0
    # ==========================================================

    print("即将开始执行多点快速运动...")
    time.sleep(2)  # 等待3秒，准备开始运动

    # 先移动到第一个点
    start_x, start_y, start_z = points[0]
    piper.MotionCtrl_2(0x01, 0x00, speed, 0x00)  # 使用较慢速度到达起始点
    piper.EndPoseCtrl(round(start_x * factor), 
                      round(start_y * factor), 
                      round(start_z * factor), 
                      round(fixed_rx * factor), 
                      round(fixed_ry * factor), 
                      round(fixed_rz * factor))
    time.sleep(3)  # 等待机械臂到达起始位置

    # 多点循环运动
    while True:
        for point in points:
            # 获取当前目标点的坐标
            # time.sleep(0.001)  # 等待机械臂到达当前目标点
            target_x, target_y, target_z = point
            
            # 输出当前目标点信息
            print(f"运动到目标点: ({target_x}, {target_y}, {target_z})")
            
            # 快速直线运动到当前目标点
            piper.MotionCtrl_2(0x01, 0x00, 100, 0x00)  # 设置运动速度
            piper.EndPoseCtrl(round(target_x * factor), 
                              round(target_y * factor), 
                              round(target_z * factor), 
                              round(fixed_rx * factor), 
                              round(fixed_ry * factor), 
                              round(fixed_rz * factor))
            
            time.sleep(1.2)  # 等待机械臂到达当前目标点,放到后面
        # 循环结束后暂停，准备开始新的循环
        print("循环完成，重新开始运动！")
        # time.sleep(1)
