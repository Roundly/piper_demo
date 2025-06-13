#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#record to txt.py

import time
from piper_sdk import C_PiperInterface_V2

# --- 配置参数 ---
# 轨迹数据来源文件
TRAJECTORY_FILENAME = "joint_trajectory.txt"
# 角度转为控制指令的缩放系数
# 在joint_ctrl.py中, rad*57295.7795 ≈ deg*1000
# 我们记录的是度(deg), 所以这里用1000
CONTROL_SCALE_FACTOR = 1000.0

# -----------------------------------------------------
#  以下是您提供的使能函数，直接复用
# -----------------------------------------------------
def enable_fun(piper: C_PiperInterface_V2):
    '''
    使能机械臂并检测使能状态,尝试5s,如果使能超时则退出程序
    '''
    # (您的 enable_fun 代码原封不动地放在这里)
    enable_flag = False
    timeout = 5
    start_time = time.time()
    elapsed_time_flag = False
    while not (enable_flag):
        elapsed_time = time.time() - start_time
        print("--------------------")
        low_spd_info = piper.GetArmLowSpdInfoMsgs() # 优化：只获取一次消息
        enable_flag = (low_spd_info.motor_1.foc_status.driver_enable_status and
                       low_spd_info.motor_2.foc_status.driver_enable_status and
                       low_spd_info.motor_3.foc_status.driver_enable_status and
                       low_spd_info.motor_4.foc_status.driver_enable_status and
                       low_spd_info.motor_5.foc_status.driver_enable_status and
                       low_spd_info.motor_6.foc_status.driver_enable_status)
        print("使能状态:", enable_flag)
        piper.EnableArm(7)
        piper.GripperCtrl(0, 1000, 0x01, 0)
        print("--------------------")
        if elapsed_time > timeout:
            print("超时....")
            elapsed_time_flag = True
            break
        time.sleep(1)
    if (elapsed_time_flag):
        print("程序自动使能超时,退出程序")
        exit(0)

def read_trajectory_from_file(filename: str) -> list:
    """
    从指定的文本文件中读取轨迹数据。
    文件格式: timestamp,j1,j2,j3,j4,j5,j6
    """
    trajectory = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                # 忽略以 '#' 开头的注释行(表头)
                if line.startswith('#'):
                    continue
                # 去除行尾的换行符并按逗号分割
                parts = line.strip().split(',')
                # 将字符串转换为浮点数
                if len(parts) == 7:
                    # [timestamp, j1, j2, j3, j4, j5, j6]
                    point = [float(p) for p in parts]
                    trajectory.append(point)
    except FileNotFoundError:
        print(f"错误：找不到轨迹文件 '{filename}'")
        return []
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return []
    
    print(f"成功从 '{filename}' 读取 {len(trajectory)} 个轨迹点。")
    return trajectory

def main():
    # --- 1. 读取轨迹 ---
    trajectory_points = read_trajectory_from_file(TRAJECTORY_FILENAME)
    if not trajectory_points:
        print("无轨迹数据，程序退出。")
        return

    # --- 2. 初始化并使能机械臂 ---
    piper = C_PiperInterface_V2("can0")
    piper.ConnectPort()
    enable_fun(piper=piper)
    
    print("\n机械臂已使能，准备开始回放轨迹...")
    time.sleep(2) # 等待2秒，准备开始

    # --- 3. 循环回放轨迹 ---
    # 将上一个点的时间戳初始化为第一个点的时间戳
    last_timestamp = trajectory_points[0][0]
    
    for i, point in enumerate(trajectory_points):
        # 从数据点中解析出时间戳和关节角度
        current_timestamp = point[0]
        joint_angles = point[1:]
        
        # 计算与上一个点的时间差，以决定休眠多久
        sleep_duration = current_timestamp - last_timestamp
        
        # 确保休眠时间不为负
        if sleep_duration > 0:
            time.sleep(sleep_duration)
        
        # 将浮点数角度转换为API需要的整数指令
        joint_commands = [round(angle * CONTROL_SCALE_FACTOR) for angle in joint_angles]
        
        # 发送控制指令
        piper.MotionCtrl_2(0x01, 0x01, 100, 0x00) # 根据您的代码添加
        piper.JointCtrl(*joint_commands) # 使用 * 解包列表作为参数
        
        # 打印当前状态
        print(f"回放点 {i+1}/{len(trajectory_points)} | 延时: {sleep_duration:.4f}s | 指令: {joint_commands}")
        
        # 更新时间戳以供下一次循环计算
        last_timestamp = current_timestamp

    print("\n✅ 轨迹回放完成。")
    # 可以选择禁用机械臂
    # piper.DisableArm(7)


if __name__ == "__main__":
    main()