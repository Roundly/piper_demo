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

    # ==================== 圆形轨迹参数设置 ====================
    # 1. 定义圆心坐标 (单位: mm)
    center_x = 156
    center_y = 0.0
    z_height = 385  # 圆所在平面的Z轴高度

    # 2. 定义圆的半径 (单位: mm)
    radius = 50
    # 3. 定义固定的末端姿态 (单位: 度)
    #    这个姿态在整个画圆过程中将保持不变
    fixed_rx = 0.0
    fixed_ry = 90.0
    fixed_rz = 0.0
    
    # 4. 运动参数
    angle_step = 1  # 每次循环增加的角度(度), 控制速度和圆的平滑度
    angle_deg = 0.0 # 初始角度
    # ==========================================================

    print("即将开始绘制圆形轨迹...")
    print(f"圆心: ({center_x}, {center_y}, {z_height}), 半径: {radius}, 姿态: ({fixed_rx}, {fixed_ry}, {fixed_rz})")
    time.sleep(3) # 等待3秒，准备开始运动

    # 先移动到圆的起始点 (angle=0的位置)
    start_x = center_x + radius
    start_y = center_y
    piper.MotionCtrl_2(0x01, 0x00, 100, 0x00) # 使用一个较慢的速度移动到起始点
    piper.EndPoseCtrl(round(start_x * factor), 
                      round(start_y * factor), 
                      round(z_height * factor), 
                      round(fixed_rx * factor), 
                      round(fixed_ry * factor), 
                      round(fixed_rz * factor))
    time.sleep(5) # 等待机械臂到达起始位置

    # 进入画圆的循环
    while True:
        # 将角度从度转换为弧度，以供sin/cos函数使用
        angle_rad = math.radians(angle_deg)
        
        # 使用参数方程计算目标坐标
        target_x = center_x + radius * math.cos(angle_rad)
        target_y = center_y + radius * math.sin(angle_rad)
        
        # 将浮点数坐标乘以因子并四舍五入为整数
        X = round(target_x * factor)
        Y = round(target_y * factor)
        Z = round(z_height * factor)
        RX = round(fixed_rx * factor)
        RY = round(fixed_ry * factor)
        RZ = round(fixed_rz * factor)
        
        # 打印当前的目标点位信息
        print(f"角度: {angle_deg:.1f}°, 目标点: X={X}, Y={Y}, Z={Z}")
        
        # 发送运动控制指令
        piper.MotionCtrl_2(0x01, 0x00, 100, 0x00)
        piper.EndPoseCtrl(X, Y, Z, RX, RY, RZ)
        
        # 更新下一个点的角度
        angle_deg += angle_step
        # 如果角度超过360度，可以归零重新开始画圆
        if angle_deg >= 360:
            angle_deg = 0
            
        # 循环间的延时，控制发送指令的频率
        time.sleep(0.02)