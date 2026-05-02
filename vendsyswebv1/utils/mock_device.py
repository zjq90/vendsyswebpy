"""
模拟设备数据工具
用于生成测试数据和模拟设备状态更新
"""
import random
import json
from datetime import datetime
from typing import Dict, Any

from models import DeviceStatus, HardwareParams


def mock_device_status_update(device_id: int) -> Dict[str, Any]:
    """
    模拟设备状态更新
    生成随机的设备状态数据用于测试
    Args:
        device_id: 设备ID
    Returns:
        设备状态数据字典
    """
    network_types = ["4G", "5G", "WiFi", "有线"]
    signal_levels = ["excellent", "good", "fair", "poor"]

    # 随机决定是否在线 (85%概率在线)
    is_online = random.random() < 0.85

    if is_online:
        signal_strength = random.randint(30, 100)
        if signal_strength >= 80:
            signal_level = "excellent"
        elif signal_strength >= 60:
            signal_level = "good"
        elif signal_strength >= 40:
            signal_level = "fair"
        else:
            signal_level = "poor"
        network_quality = signal_strength
        latency_ms = random.randint(10, 200)
        packet_loss_rate = round(random.uniform(0, 5), 2)
    else:
        signal_strength = 0
        signal_level = "poor"
        network_quality = 0
        latency_ms = None
        packet_loss_rate = None

    status_data = {
        "device_id": device_id,
        "is_online": is_online,
        "last_online_time": datetime.now() if is_online else None,
        "network_type": random.choice(network_types) if is_online else None,
        "network_quality": network_quality,
        "signal_strength": signal_strength,
        "signal_level": signal_level,
        "latency_ms": latency_ms,
        "packet_loss_rate": packet_loss_rate,
        "ip_address": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}" if is_online else None,
        "apn": "cmnet" if is_online else None,
        "recorded_at": datetime.now()
    }
    return status_data


def mock_hardware_params_update(device_id: int) -> Dict[str, Any]:
    """
    模拟硬件参数更新
    生成随机的硬件参数数据用于测试
    Args:
        device_id: 设备ID
    Returns:
        硬件参数字典
    """
    # 模拟货道电机状态 (假设10个货道)
    lane_motor_status = {}
    motor_fault_count = 0
    for i in range(1, 11):
        # 95%概率正常
        if random.random() < 0.95:
            lane_motor_status[f"lane_{i}"] = "normal"
        else:
            lane_motor_status[f"lane_{i}"] = "fault"
            motor_fault_count += 1

    # 门锁状态
    door_lock_statuses = ["locked", "unlocked", "fault"]
    door_weights = [0.9, 0.08, 0.02]
    door_lock_status = random.choices(door_lock_statuses, weights=door_weights)[0]

    # 温湿度
    temperature = round(random.uniform(2, 10), 1)  # 冷藏温度
    humidity = round(random.uniform(40, 70), 1)
    target_temperature = 4.0

    # 制冷系统状态
    if temperature > target_temperature + 1:
        cooling_system_status = "cooling"
    elif temperature < target_temperature - 1:
        cooling_system_status = "idle"
    else:
        cooling_system_status = random.choice(["idle", "cooling"])

    # 电力状况
    voltage = round(random.uniform(215, 235), 1)
    current = round(random.uniform(0.5, 3.0), 2)
    power = round(voltage * current, 1)

    # 屏幕状态
    screen_statuses = ["on", "off", "standby", "fault"]
    screen_weights = [0.85, 0.1, 0.04, 0.01]
    screen_status = random.choices(screen_statuses, weights=screen_weights)[0]

    # 故障信息
    has_fault = motor_fault_count > 0 or door_lock_status == "fault"
    fault_codes = []
    fault_description = []
    if motor_fault_count > 0:
        fault_codes.append("MOT001")
        fault_description.append(f"有{motor_fault_count}个货道电机故障")
    if door_lock_status == "fault":
        fault_codes.append("DOOR001")
        fault_description.append("门锁故障")

    hardware_data = {
        "device_id": device_id,
        "lane_motor_status": json.dumps(lane_motor_status),
        "motor_fault_count": motor_fault_count,
        "door_lock_status": door_lock_status,
        "door_open_count": random.randint(0, 100),
        "temperature": temperature,
        "humidity": humidity,
        "target_temperature": target_temperature,
        "cooling_system_status": cooling_system_status,
        "heating_system_status": "idle",
        "power_source": "mains",
        "voltage": voltage,
        "current": current,
        "power": power,
        "battery_level": None,
        "battery_voltage": None,
        "screen_status": screen_status,
        "screen_brightness": random.randint(70, 100),
        "current_ad_content": "欢迎光临！今日特惠：可乐3元/瓶",
        "vibration_sensor_triggered": random.random() < 0.01,
        "has_fault": has_fault,
        "fault_codes": json.dumps(fault_codes) if fault_codes else None,
        "fault_description": "; ".join(fault_description) if fault_description else None,
        "recorded_at": datetime.now()
    }
    return hardware_data
