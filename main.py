import aiohttp
import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import paho.mqtt.client as mqtt
import socket
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/pc_monitor.log'),
        logging.StreamHandler()
        ]
    )
logger = logging.getLogger(__name__)


# ==================== MQTT 配置 ====================
class MQTTConfig:
    def __init__(self):
        self.broker = ""
        self.port = 1883
        self.username = ""
        self.password = ""
        self.base_topic = "homeassistant/sensor/pc_monitor/"
        self.client_id = f"pc_monitor_{socket.gethostname()}"
        self.qos = 1
        self.retain = True


# ==================== 数据结构 ====================
@dataclass
class MotherboardStats:
    temp_current: Optional[float] = None
    temp_peak: Optional[float] = None


@dataclass
class CPUStats:
    temp_current: Optional[float] = None
    temp_peak: Optional[float] = None
    power_current: Optional[float] = None
    power_peak: Optional[float] = None
    usage_current: Optional[float] = None
    usage_peak: Optional[float] = None
    frequency: Optional[float] = None
    peak_frequency: Optional[float] = None
    _core_freqs: List[float] = field(default_factory=list)
    _peak_core_freqs: List[float] = field(default_factory=list)


@dataclass
class MemoryStats:
    usage: Optional[float] = None
    used: Optional[float] = None
    available: Optional[float] = None


@dataclass
class GPUStats:
    temp_current: Optional[float] = None
    temp_peak: Optional[float] = None
    power_current: Optional[float] = None
    power_peak: Optional[float] = None
    usage_current: Optional[float] = None
    usage_peak: Optional[float] = None
    vram_used: Optional[float] = None
    vram_available: Optional[float] = None
    vram_usage: Optional[float] = None


@dataclass
class NetworkStats:
    upload_speed: Optional[float] = None
    download_speed: Optional[float] = None


# ==================== MQTT 发布器 ====================
class AsyncMQTTPublisher:
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client = self._setup_client()

    def _setup_client(self) -> mqtt.Client:
        client = mqtt.Client(
            client_id=self.config.client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        client.username_pw_set(self.config.username, self.config.password)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.connect(self.config.broker, self.config.port)
        client.loop_start()
        return client

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT连接成功")
        else:
            logger.error(f"MQTT连接失败，错误码: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"MQTT断开连接，错误码: {rc}")

    def publish(self, topic_suffix: str, payload: Any):
        """发布MQTT消息"""
        full_topic = f"{self.config.base_topic}{topic_suffix}"
        self.client.publish(
            full_topic,
            payload=json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload),
            qos=self.config.qos,
            retain=self.config.retain
            )
        logger.debug(f"发布到 {full_topic}: {payload}")

    def publish_all_sensor_configs(self):
        """发布所有传感器的自动发现配置"""
        configs = {
        # 主板传感器
        "mb_temp": {
            "name": "主板温度",
            "unit_of_meas": "°C",
            "device_class": "temperature",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.mb_temp }}",
            "unique_id": f"{self.config.client_id}_mb_temp",

        },
        "mb_temp_peak": {
            "name": "主板温度峰值",
            "unit_of_meas": "°C",
            "device_class": "temperature",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.mb_temp_peak }}",
            "unique_id": f"{self.config.client_id}_mb_temp_peak",

        },

        # CPU传感器
        "cpu_temp": {
            "name": "CPU温度",
            "unit_of_meas": "°C",
            "device_class": "temperature",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.cpu_temp }}",
            "unique_id": f"{self.config.client_id}_cpu_temp",

        },
        "cpu_temp_peak": {
            "name": "CPU温度峰值",
            "unit_of_meas": "°C",
            "device_class": "temperature",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.cpu_temp_peak }}",
            "unique_id": f"{self.config.client_id}_cpu_temp_peak",

        },
        "cpu_power": {
            "name": "CPU功耗",
            "unit_of_meas": "W",
            "device_class": "power",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.cpu_power }}",
            "unique_id": f"{self.config.client_id}_cpu_power",

        },
        "cpu_power_peak": {
            "name": "CPU功耗峰值",
            "unit_of_meas": "W",
            "device_class": "power",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.cpu_power_peak }}",
            "unique_id": f"{self.config.client_id}_cpu_power_peak",

        },
        "cpu_usage": {
            "name": "CPU使用率",
            "unit_of_meas": "%",
            "device_class": "power_factor",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.cpu_usage }}",
            "unique_id": f"{self.config.client_id}_cpu_usage",

        },
        "cpu_usage_peak": {
            "name": "CPU使用率峰值",
            "unit_of_meas": "%",
            "device_class": "power_factor",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.cpu_usage_peak }}",
            "unique_id": f"{self.config.client_id}_cpu_usage_peak",

        },
        "cpu_freq": {
            "name": "CPU频率",
            "unit_of_meas": "GHz",
            "icon": "mdi:speedometer",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.cpu_freq }}",
            "unique_id": f"{self.config.client_id}_cpu_freq",

        },
        "cpu_freq_peak": {
            "name": "CPU频率峰值",
            "unit_of_meas": "GHz",
            "icon": "mdi:speedometer",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.cpu_freq_peak }}",
            "unique_id": f"{self.config.client_id}_cpu_freq_peak",

        },

        # 内存传感器
        "mem_usage": {
            "name": "内存使用率",
            "unit_of_meas": "%",
            "icon": "mdi:memory",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.mem_usage }}",
            "unique_id": f"{self.config.client_id}_mem_usage",

        },
        "mem_used": {
            "name": "已用内存",
            "unit_of_meas": "GB",
            "icon": "mdi:memory",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.mem_used }}",
            "unique_id": f"{self.config.client_id}_mem_used",

        },
        "mem_available": {
            "name": "可用内存",
            "unit_of_meas": "GB",
            "icon": "mdi:memory",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.mem_available }}",
            "unique_id": f"{self.config.client_id}_mem_available",

        },

        # 显卡传感器
        "gpu_temp": {
            "name": "显卡温度",
            "unit_of_meas": "°C",
            "device_class": "temperature",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_temp }}",
            "unique_id": f"{self.config.client_id}_gpu_temp",

        },
        "gpu_temp_peak": {
            "name": "显卡温度峰值",
            "unit_of_meas": "°C",
            "device_class": "temperature",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_temp_peak }}",
            "unique_id": f"{self.config.client_id}_gpu_temp_peak",

        },
        "gpu_power": {
            "name": "显卡功耗",
            "unit_of_meas": "W",
            "device_class": "power",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_power }}",
            "unique_id": f"{self.config.client_id}_gpu_power",

        },
        "gpu_power_peak": {
            "name": "显卡功耗峰值",
            "unit_of_meas": "W",
            "device_class": "power",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_power_peak }}",
            "unique_id": f"{self.config.client_id}_gpu_power_peak",

        },
        "gpu_usage": {
            "name": "显卡使用率",
            "unit_of_meas": "%",
            "icon": "mdi:gpu",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_usage }}",
            "unique_id": f"{self.config.client_id}_gpu_usage",

        },
        "gpu_usage_peak": {
            "name": "显卡使用率峰值",
            "unit_of_meas": "%",
            "icon": "mdi:gpu",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_usage_peak }}",
            "unique_id": f"{self.config.client_id}_gpu_usage_peak",

        },
        "gpu_vram_used": {
            "name": "显存使用量",
            "unit_of_meas": "GB",
            "icon": "mdi:memory",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_vram_used }}",
            "unique_id": f"{self.config.client_id}_gpu_vram_used",

        },
        "gpu_vram_available": {
            "name": "可用显存",
            "unit_of_meas": "GB",
            "icon": "mdi:memory",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_vram_available }}",
            "unique_id": f"{self.config.client_id}_gpu_vram_available",

        },
        "gpu_vram_usage": {
            "name": "显存使用率",
            "unit_of_meas": "%",
            "icon": "mdi:memory",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.gpu_vram_usage }}",
            "unique_id": f"{self.config.client_id}_gpu_vram_usage",

        },

        # 网络传感器
        "net_upload": {
            "name": "上传速度",
            "unit_of_meas": "MB/s",
            "icon": "mdi:upload-network",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.net_upload }}",
            "unique_id": f"{self.config.client_id}_net_upload",

        },
        "net_download": {
            "name": "下载速度",
            "unit_of_meas": "MB/s",
            "icon": "mdi:download-network",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.net_download }}",
            "unique_id": f"{self.config.client_id}_net_download",

        },

        # 系统状态
        "monitor_status": {
            "name": "监控状态",
            "icon": "mdi:heart-pulse",
            "state_topic": f"{self.config.base_topic}state",
            "value_template": "{{ value_json.status }}",
            "unique_id": f"{self.config.client_id}_status",

        }

            }

        for sensor_id, config in configs.items():
            self.publish(f"{sensor_id}/config", config)


# ==================== 硬件监控器 ====================
class HardwareMonitor:
    def __init__(self, url: str, interval: int = 2):
        self.url = url
        self.interval = interval
        self.mqtt = AsyncMQTTPublisher(MQTTConfig())

        # 初始化数据结构
        self.motherboard = MotherboardStats()
        self.cpu = CPUStats()
        self.memory = MemoryStats()
        self.gpu = GPUStats()
        self.network = NetworkStats()

        self._running = False
        self._last_update = None
        self._connection_failures = 0  # 跟踪连续失败次数
        self.MAX_FAILURES = 1  # 失败1次后立即标记为离线

    async def start(self):
        """启动监控服务"""
        self._running = True
        self.mqtt.publish_all_sensor_configs()

        while self._running:
            try:
                await self._update()
                self._connection_failures = 0  # 成功则重置失败计数
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"监控循环错误: {str(e)}")
                self._connection_failures += 1
                if self._connection_failures >= self.MAX_FAILURES:
                    self._set_offline_state()
                await asyncio.sleep(5)  # 错误后等待5秒重试

    def _set_offline_state(self):
        """将所有数据设置为离线状态（0）并发布到MQTT"""
        offline_value = 0  # 改为0而不是"--"

        # 重置所有数据为0
        self.motherboard.temp_current = offline_value
        self.motherboard.temp_peak = offline_value

        self.cpu.temp_current = offline_value
        self.cpu.temp_peak = offline_value
        self.cpu.power_current = offline_value
        self.cpu.power_peak = offline_value
        self.cpu.usage_current = offline_value
        self.cpu.usage_peak = offline_value
        self.cpu.frequency = offline_value
        self.cpu.peak_frequency = offline_value

        self.memory.usage = offline_value
        self.memory.used = offline_value
        self.memory.available = offline_value

        self.gpu.temp_current = offline_value
        self.gpu.temp_peak = offline_value
        self.gpu.power_current = offline_value
        self.gpu.power_peak = offline_value
        self.gpu.usage_current = offline_value
        self.gpu.usage_peak = offline_value
        self.gpu.vram_used = offline_value
        self.gpu.vram_available = offline_value
        self.gpu.vram_usage = offline_value

        self.network.upload_speed = offline_value
        self.network.download_speed = offline_value

        # 发布离线状态（确保MQTT消息包含所有字段）
        payload = {
            "timestamp": datetime.now().isoformat(),
            "mb_temp": self.motherboard.temp_current,
            "mb_temp_peak": self.motherboard.temp_peak,

            "cpu_temp": self.cpu.temp_current,
            "cpu_temp_peak": self.cpu.temp_peak,
            "cpu_power": self.cpu.power_current,
            "cpu_power_peak": self.cpu.power_peak,
            "cpu_usage": self.cpu.usage_current,
            "cpu_usage_peak": self.cpu.usage_peak,
            "cpu_freq": self.cpu.frequency,
            "cpu_freq_peak": self.cpu.peak_frequency,

            "mem_usage": self.memory.usage,
            "mem_used": self.memory.used,
            "mem_available": self.memory.available,

            "gpu_temp": self.gpu.temp_current,
            "gpu_temp_peak": self.gpu.temp_peak,
            "gpu_power": self.gpu.power_current,
            "gpu_power_peak": self.gpu.power_peak,
            "gpu_usage": self.gpu.usage_current,
            "gpu_usage_peak": self.gpu.usage_peak,
            "gpu_vram_used": self.gpu.vram_used,
            "gpu_vram_available": self.gpu.vram_available,
            "gpu_vram_usage": self.gpu.vram_usage,

            "net_upload": self.network.upload_speed,
            "net_download": self.network.download_speed,
            "status": "OFFLINE"  # 明确标记为离线
        }
        self.mqtt.publish("state", payload)  # 确保MQTT消息发送成功

    async def _update(self):
        """更新所有传感器数据"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=3) as response:
                    if response.status != 200:
                        raise ConnectionError(f"HTTP状态码异常: {response.status}")
                    data = await response.json()
                    self._parse_data(data)
                    self._publish_all_data()
                    self._last_update = datetime.now()
        except Exception as e:
            logger.error(f"数据更新失败: {str(e)}")
            raise

    def _parse_data(self, node: dict):
        """解析原始JSON数据"""
        # 重置临时数据
        self.cpu._core_freqs = []
        self.cpu._peak_core_freqs = []

        def _scan(n: dict):
            sensor_id = n.get("SensorId", "")
            value = self._extract_value(n.get("Value"))
            max_val = self._extract_value(n.get("Max"))

            # 主板温度
            if sensor_id == "/lpc/nct6687d/0/temperature/1":
                self.motherboard.temp_current = value
                self.motherboard.temp_peak = max_val

            # CPU数据
            elif sensor_id == "/amdcpu/0/temperature/2":
                self.cpu.temp_current = value
                self.cpu.temp_peak = max_val
            elif sensor_id == "/amdcpu/0/power/0":
                self.cpu.power_current = value
                self.cpu.power_peak = max_val
            elif sensor_id == "/amdcpu/0/load/0":
                self.cpu.usage_current = value
                self.cpu.usage_peak = max_val
            elif sensor_id.startswith("/amdcpu/0/clock/") and sensor_id != "/amdcpu/0/clock/0":
                if value is not None:
                    self.cpu._core_freqs.append(value)
                if max_val is not None:
                    self.cpu._peak_core_freqs.append(max_val)

            # 内存数据
            elif sensor_id == "/ram/load/0":
                self.memory.usage = value
            elif sensor_id == "/ram/data/0":
                self.memory.used = value
            elif sensor_id == "/ram/data/1":
                self.memory.available = value

            # 显卡数据
            elif sensor_id == "/gpu-amd/0/temperature/0":
                self.gpu.temp_current = value
                self.gpu.temp_peak = max_val
            elif sensor_id == "/gpu-amd/0/power/3":
                self.gpu.power_current = value
                self.gpu.power_peak = max_val
            elif sensor_id == "/gpu-amd/0/load/0":
                self.gpu.usage_current = value
                self.gpu.usage_peak = max_val
            elif sensor_id == "/gpu-amd/0/smalldata/0":
                self.gpu.vram_used = value /1024
            elif sensor_id == "/gpu-amd/0/smalldata/1":
                self.gpu.vram_available = value /1024
                if self.gpu.vram_used is not None and self.gpu.vram_available is not None:
                    total = self.gpu.vram_used + self.gpu.vram_available
                    if total > 0:
                        self.gpu.vram_usage = (self.gpu.vram_used / total) * 100

            # 网络数据
            elif sensor_id == "/nic/%7B3946F6E6-AFE8-4E7E-8839-2719C6CFA81C%7D/throughput/7":
                self.network.upload_speed = value
            elif sensor_id == "/nic/%7B3946F6E6-AFE8-4E7E-8839-2719C6CFA81C%7D/throughput/8":
                self.network.download_speed = value

            # 递归扫描子节点
            if "Children" in n:
                for child in n["Children"]:
                    _scan(child)

        _scan(node)

        # 计算CPU频率
        if self.cpu._core_freqs:
            self.cpu.frequency = sum(self.cpu._core_freqs) / len(self.cpu._core_freqs) /1024
        if self.cpu._peak_core_freqs:
            self.cpu.peak_frequency = sum(self.cpu._peak_core_freqs) / len(self.cpu._peak_core_freqs) /1024

    def _publish_all_data(self):
        """发布所有传感器数据到MQTT"""
        payload = {
            "timestamp": datetime.now().isoformat(),
            "mb_temp": self.motherboard.temp_current,
            "mb_temp_peak": self.motherboard.temp_peak,

            "cpu_temp": self.cpu.temp_current,
            "cpu_temp_peak": self.cpu.temp_peak,
            "cpu_power": self.cpu.power_current,
            "cpu_power_peak": self.cpu.power_peak,
            "cpu_usage": self.cpu.usage_current,
            "cpu_usage_peak": self.cpu.usage_peak,
            "cpu_freq": self.cpu.frequency,
            "cpu_freq_peak": self.cpu.peak_frequency,

            "mem_usage": self.memory.usage,
            "mem_used": self.memory.used,
            "mem_available": self.memory.available,

            "gpu_temp": self.gpu.temp_current,
            "gpu_temp_peak": self.gpu.temp_peak,
            "gpu_power": self.gpu.power_current,
            "gpu_power_peak": self.gpu.power_peak,
            "gpu_usage": self.gpu.usage_current,
            "gpu_usage_peak": self.gpu.usage_peak,
            "gpu_vram_used": self.gpu.vram_used,
            "gpu_vram_available": self.gpu.vram_available,
            "gpu_vram_usage": self.gpu.vram_usage,

            "net_upload": self.network.upload_speed,
            "net_download": self.network.download_speed,

            "status": "ONLINE"
            }

        # 清理None值
        payload = {k: v for k, v in payload.items() if v is not None}
        self.mqtt.publish("state", payload)

    @staticmethod
    def _extract_value(value: Optional[str]) -> Optional[float]:
        """从字符串中提取数值 (如 '45.2 °C' -> 45.2)"""
        if value is None:
            return None
        try:
            return float(str(value).split()[0])
        except (ValueError, IndexError, AttributeError):
            return None


# ==================== 主程序 ====================
async def main():
    monitor = HardwareMonitor("http://192.168.100.245:8097/data.json") #LibreHardware的ip和端口
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("监控服务正常停止")


if __name__ == "__main__":
    asyncio.run(main())