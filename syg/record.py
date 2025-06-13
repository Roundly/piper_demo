#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#record to txt.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import re
from piper_sdk import C_PiperInterface_V2

# --- 配置参数 ---
# 采集频率 (Hz)
FREQUENCY_HZ = 50
# 输出的文本文件名
OUTPUT_FILENAME = "joint_trajectory.txt"

def parse_joint_msgs(raw_string: str) -> list[float]:
    """
    使用正则表达式从机械臂返回的字符串中解析出六个关节的角度值。
    :param raw_string: piper.GetArmJointMsgs() 返回的原始字符串。
    :return: 包含六个关节角度的浮点数列表。
    """
    pattern = re.compile(r"Joint \d+:\s*[\d-]+,\s*([-?\d\.]+)")
    matches = pattern.findall(raw_string)
    
    if len(matches) == 6:
        return [float(angle) for angle in matches]
    return []

def main():
    """
    主函数，用于连接机械臂、读取数据、打印并写入TXT文件。
    """
    # --- 1. 初始化机械臂连接 ---
    piper = C_PiperInterface_V2()
    if not piper.ConnectPort():
        print("错误：无法连接到机械臂，请检查连接。")
        return

    # --- 2. 打开文件准备写入 ---
    output_file = None
    try:
        # 使用 'w' 模式打开文件，如果文件已存在则覆盖
        output_file = open(OUTPUT_FILENAME, 'w', encoding='utf-8')
        
        # 写入表头 (以'#'开头作为注释，方便读取时忽略)
        header = "# Timestamp, Joint 1, Joint 2, Joint 3, Joint 4, Joint 5, Joint 6\n"
        output_file.write(header)
        
        print(f"成功创建文件 '{OUTPUT_FILENAME}'，准备写入数据...")
        
    except IOError as e:
        print(f"错误：无法打开或写入文件。 {e}")
        if output_file:
            output_file.close()
        return

    # --- 3. 开始循环读取和写入数据 ---
    print(f"已连接机械臂，开始以 {FREQUENCY_HZ} Hz 的频率记录关节角度。")
    print("按下 Ctrl+C 停止记录并保存文件。")
    
    sleep_duration = 1.0 / FREQUENCY_HZ
    
    try:
        while True:
            loop_start_time = time.perf_counter()
            
            joint_data_str = piper.GetArmJointMsgs()
            
            if joint_data_str:
                joint_angles = parse_joint_msgs(joint_data_str)
                
                if joint_angles:
                    current_timestamp = time.time()
                    
                    # 格式化数据为逗号分隔的字符串
                    # [时间戳, 角度1, 角度2, ..., 角度6]
                    data_list = [f"{current_timestamp:.6f}"] + [f"{angle:.4f}" for angle in joint_angles]
                    data_line = ",".join(data_list) + "\n"
                    
                    # 写入文件
                    output_file.write(data_line)
                    
                    # 在控制台打印，方便查看
                    angles_str_print = ", ".join([f"{angle:8.3f}" for angle in joint_angles])
                    print(f"时间戳: {current_timestamp:.4f} | 关节角度: [ {angles_str_print} ]")

            elapsed_time = time.perf_counter() - loop_start_time
            time.sleep(max(0, sleep_duration - elapsed_time))

    except KeyboardInterrupt:
        print("\n检测到中断信号 (Ctrl+C)，正在停止记录...")
        
    finally:
        # --- 4. 关闭文件 ---
        if output_file:
            output_file.close()
            print(f"✅ 数据已成功保存到 '{OUTPUT_FILENAME}'")

if __name__ == "__main__":
    main()