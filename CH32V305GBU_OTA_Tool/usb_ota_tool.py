#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CH32V305GBU USB OTA 上位机 (命令行版)
支持USB HS接口进行固件升级

功能：
- USB HS高速通信
- 支持BIN和Intel HEX格式固件
- USB通信重试机制
- 固件CRC32/MD5校验
- 详细的日志记录
"""

import sys
import os
import struct
import time
import argparse
import logging
from pathlib import Path

try:
    import usb.core
    import usb.util
    import usb.backend.libusb1
    import libusb_package
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('usb_ota.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IAPCommands:
    """IAP命令定义"""
    PROGRAM = 0x80
    ERASE = 0x81
    VERIFY = 0x82
    END = 0x83
    JUMP = 0x84


class IntelHexParser:
    """Intel HEX文件解析器"""

    @staticmethod
    def parse(hex_file_path):
        """
        解析Intel HEX文件

        Returns:
            dict: {address: data_bytes}
        """
        segments = {}
        base_addr = 0

        with open(hex_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line[0] != ':':
                    continue

                # 解析记录
                data_len = int(line[1:3], 16)
                addr = int(line[3:7], 16)
                record_type = int(line[7:9], 16)
                data = bytes.fromhex(line[9:9 + data_len * 2])
                checksum = int(line[9 + data_len * 2:11 + data_len * 2], 16)

                # 验证校验和
                calc_checksum = (data_len + (addr >> 8) + (addr & 0xFF) + record_type + sum(data)) & 0xFF
                calc_checksum = (~calc_checksum + 1) & 0xFF
                if calc_checksum != checksum:
                    raise ValueError(f"校验和错误: {line}")

                if record_type == 0x00:  # 数据记录
                    full_addr = base_addr + addr
                    if full_addr not in segments:
                        segments[full_addr] = bytearray()
                    segments[full_addr].extend(data)

                elif record_type == 0x01:  # 结束记录
                    break

                elif record_type == 0x04:  # 扩展线性地址记录
                    base_addr = (data[0] << 24) | (data[1] << 16)

                elif record_type == 0x05:  # 起始线性地址记录
                    pass

        return segments

    @staticmethod
    def to_binary(hex_file_path, fill_byte=0xFF):
        """
        将HEX文件转换为二进制数据

        Args:
            hex_file_path: HEX文件路径
            fill_byte: 填充字节

        Returns:
            tuple: (start_address, binary_data)
        """
        segments = IntelHexParser.parse(hex_file_path)

        if not segments:
            raise ValueError("HEX文件为空")

        # 找到最低和最高地址
        min_addr = min(segments.keys())
        max_addr = max(addr + len(data) for addr, data in segments.items())

        # 创建二进制数据
        binary_data = bytearray([fill_byte] * (max_addr - min_addr))

        for addr, data in segments.items():
            offset = addr - min_addr
            binary_data[offset:offset + len(data)] = data

        return min_addr, bytes(binary_data)


class USBDevice:
    """USB设备类"""

    VID = 0x4348  # WCH (Bootloader)
    PID = 0x55e0  # USB MODULE (Bootloader)
    
    # APP模式下的 VID 和 PID
    APP_VID = 0x1A86
    APP_PID = 0x5807

    def __init__(self, max_retries=3, timeout=5000):
        self.dev = None
        self.ep_in = None
        self.ep_out = None
        self.is_connected = False
        self.max_retries = max_retries
        self.timeout = timeout
        
        # 获取 backend
        if USB_AVAILABLE:
            self.backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
        else:
            self.backend = None

    def connect(self):
        """连接USB设备"""
        try:
            # 尝试查找设备
            self.dev = usb.core.find(idVendor=self.VID, idProduct=self.PID, backend=self.backend)
            if self.dev is None:
                return False, "未找到USB设备 (VID: 0x{:04X}, PID: 0x{:04X})".format(self.VID, self.PID)

            # 设置配置
            try:
                self.dev.set_configuration()
            except usb.core.USBError as e:
                if getattr(e, 'errno', None) == 16 or getattr(e, 'backend_error_code', None) == -6:  # Device or resource busy
                    try:
                        if self.dev.is_kernel_driver_active(0):
                            self.dev.detach_kernel_driver(0)
                            logger.info("内核驱动已分离")
                        self.dev.set_configuration()
                    except Exception as detach_e:
                        logger.warning(f"分离内核驱动或重新配置失败: {detach_e}")
                else:
                    logger.warning(f"设置USB配置失败: {e}")
                    # 继续尝试，有时设备已经配置好了
            except NotImplementedError as e:
                logger.error(f"设备驱动不受支持: {e}。请使用 Zadig 将设备的驱动程序 (VID:0x{self.VID:04X}, PID:0x{self.PID:04X}) 替换为 WinUSB。")
                return False, f"驱动不受支持，请使用 Zadig 安装 WinUSB 驱动"


            # 声明接口
            try:
                usb.util.claim_interface(self.dev, 0)
            except usb.core.USBError as e:
                logger.warning(f"声明接口失败: {e}")
            except NotImplementedError:
                pass # Windows上可能不支持

            # 获取端点
            cfg = self.dev.get_active_configuration()
            intf = cfg[(0, 0)]

            self.ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )

            self.ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
            )

            if not self.ep_out or not self.ep_in:
                return False, "未找到USB端点"

            self.is_connected = True
            logger.info(f"USB设备连接成功: EP_OUT=0x{self.ep_out.bEndpointAddress:02X}, EP_IN=0x{self.ep_in.bEndpointAddress:02X}")

            return True, "设备连接成功"

        except usb.core.USBError as e:
            logger.error(f"USB错误: {e}")
            return False, f"USB错误: {str(e)}"
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False, f"连接失败: {str(e)}"

    def disconnect(self):
        """断开USB设备"""
        try:
            if self.dev:
                usb.util.release_interface(self.dev, 0)
                self.dev = None
                self.ep_in = None
                self.ep_out = None
                self.is_connected = False
                logger.info("USB设备已断开")
        except Exception as e:
            logger.warning(f"断开设备时出错: {e}")

    def send_packet(self, cmd, data, data_len=None, retry_count=None, ignore_response=False):
        """
        发送数据包（带重试机制）

        Args:
            cmd: 命令字节
            data: 数据字节
            data_len: 告知设备的有效数据长度，如果为None则取len(data)
            retry_count: 重试次数（默认使用初始化时的max_retries）
            ignore_response: 是否忽略设备响应（用于重启、结束等指令）

        Returns:
            tuple: (success, message, response_data)
        """
        if not self.is_connected:
            return False, "设备未连接", None

        if retry_count is None:
            retry_count = self.max_retries

        if data_len is None:
            data_len = len(data)

        packet = bytes([cmd, data_len]) + data
        if len(packet) < 64:
            packet += b'\x00' * (64 - len(packet))

        for attempt in range(retry_count + 1):
            try:
                # 发送数据
                bytes_written = self.ep_out.write(packet, timeout=self.timeout)
                logger.debug(f"发送数据: {packet[:16].hex()}... ({bytes_written} bytes)")

                if ignore_response:
                    return True, "指令已发送", None

                # 接收响应
                response = self.ep_in.read(64, timeout=self.timeout)
                logger.debug(f"接收响应: {bytes(response).hex()}")

                if len(response) >= 2:
                    status = response[1]
                    if status == 0x00:
                        return True, "成功", bytes(response)
                    else:
                        error_msg = f"设备返回错误 (状态: 0x{status:02X})"
                        logger.warning(error_msg)
                        if attempt < retry_count:
                            time.sleep(0.1 * (attempt + 1))
                            continue
                        return False, error_msg, bytes(response)

                return True, "成功", bytes(response)

            except usb.core.USBTimeoutError:
                error_msg = f"USB超时 (尝试 {attempt + 1}/{retry_count + 1})"
                logger.warning(error_msg)
                if attempt < retry_count:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                return False, error_msg, None

            except Exception as e:
                error_msg = f"发送失败: {str(e)} (尝试 {attempt + 1}/{retry_count + 1})"
                logger.error(error_msg)
                if attempt < retry_count:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                return False, error_msg, None

        return False, "达到最大重试次数", None

    def wake_bootloader(self):
        """
        向APP发送特定的控制传输指令 (bRequest=0xAA)，请求设备跳转到 Bootloader。
        这个指令通常会导致设备断开连接并重新枚举，所以可能会抛出异常，这是正常的。
        """
        try:
            if self.dev is None:
                # 尝试连接 APP 模式的设备
                self.dev = usb.core.find(idVendor=self.APP_VID, idProduct=self.APP_PID, backend=self.backend)
                if self.dev is None:
                    # 也有可能用户手动输入了唤醒指令，但设备其实已经在 Bootloader 模式了
                    self.dev = usb.core.find(idVendor=self.VID, idProduct=self.PID, backend=self.backend)
                    if self.dev is not None:
                        return True, "设备已经在 Bootloader 模式"
                    return False, f"未找到USB设备 (APP VID: 0x{self.APP_VID:04X}, PID: 0x{self.APP_PID:04X})"
            
            logger.info("发送跳转Bootloader的控制指令...")
            # bmRequestType=0x40 (Vendor, Device, Out), bRequest=0xAA
            self.dev.ctrl_transfer(0x40, 0xAA, 0, 0, None, timeout=1000)
            
            return True, "跳转指令已发送，请等待设备重新枚举"
        except usb.core.USBError as e:
            # 设备复位导致断开，这是预期行为
            logger.info("设备已断开连接，正在重启进入Bootloader")
            return True, "设备已断开连接，正在重启进入Bootloader"
        except Exception as e:
            logger.error(f"发送跳转指令失败: {e}")
            return False, f"发送跳转指令失败: {str(e)}"

    def erase_flash(self):
        """
        擦除Flash，根据固件实现，它会自动擦除整片或者指定的区域，不需要传递地址
        """
        # IAP firmware expects an empty packet for CMD_IAP_ERASE
        return self.send_packet(IAPCommands.ERASE, b'\x00\x00\x00\x00')

    def program_flash(self, data):
        """
        编程Flash

        Args:
            data: 数据（最大62字节，因为固件端定义的 program 结构体是 data[62]）
        """
        # 固件端：
        # struct { u8 Cmd; u8 Len; u8 data[62]; } program;
        packet = data[:62]
        return self.send_packet(IAPCommands.PROGRAM, packet)

    def verify_flash(self, address, data):
        """
        校验Flash

        Args:
            address: 当前校验的地址（占位，Bootloader 实际未使用此地址字段）
            data: 数据（最大56字节，因为固件端定义的 verify 结构体是 data[56]）
        """
        # 固件端：
        # typedef union __attribute__ ((aligned(4)))_ISP_CMD {
        # struct{ u8 Cmd; u8 Len; u8 addr[4]; u8 data[56]; } verify;
        # } isp_cmd;
        #
        # 注意：这里 C 编译器不会在 u8 成员间插入 padding。
        # struct 中的内存布局:
        # offset 0: Cmd (1 byte)
        # offset 1: Len (1 byte)
        # offset 2: addr (4 bytes)
        # offset 6: data (56 bytes)
        #
        # Bootloader 端通过 Lenth = packet[1] 来决定要比较多少字节的 data。
        # 因此，packet[1] 必须正好是 len(data)，而不是 len(addr + data)。
        
        addr_bytes = struct.pack('<I', address)
        # 紧凑排列 addr 和 data
        packet_data = addr_bytes + data[:56]
        
        # 传递 data_len=len(data[:56])，使得 packet[1] 恰好等于有效数据的长度
        return self.send_packet(IAPCommands.VERIFY, packet_data, data_len=len(data[:56]))

    def end_upgrade(self):
        """结束升级"""
        # 固件执行 End_Flag = 1 后会直接进入 IAP_2_APP 甚至关闭 USB 中断并重启
        # 因此我们发送完毕后不应该再等待设备响应
        return self.send_packet(IAPCommands.END, b'\x00\x00\x00\x00', ignore_response=True)

    def jump_to_app(self):
        """跳转到应用程序"""
        return self.send_packet(IAPCommands.JUMP, b'\x00\x00\x00\x00', ignore_response=True)


class FirmwareLoader:
    """固件加载器"""

    @staticmethod
    def load_firmware(file_path):
        """
        加载固件文件（支持BIN和HEX格式）

        Returns:
            tuple: (success, message, firmware_data, start_address)
        """
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.hex':
                # 解析Intel HEX文件
                start_addr, firmware_data = IntelHexParser.to_binary(file_path)
                logger.info(f"加载HEX文件: {file_path}, 起始地址: 0x{start_addr:08X}, 大小: {len(firmware_data)} 字节")
                return True, "HEX文件加载成功", firmware_data, start_addr

            elif file_ext == '.bin':
                # 加载二进制文件
                with open(file_path, 'rb') as f:
                    firmware_data = f.read()
                logger.info(f"加载BIN文件: {file_path}, 大小: {len(firmware_data)} 字节")
                return True, "BIN文件加载成功", firmware_data, 0x08005000

            else:
                # 尝试作为BIN文件加载
                with open(file_path, 'rb') as f:
                    firmware_data = f.read()
                logger.info(f"加载文件: {file_path}, 大小: {len(firmware_data)} 字节")
                return True, "文件加载成功", firmware_data, 0x08005000

        except Exception as e:
            logger.error(f"加载固件失败: {e}")
            return False, f"加载固件失败: {str(e)}", None, 0

    @staticmethod
    def calculate_crc32(data):
        """计算CRC32校验值"""
        import binascii
        return binascii.crc32(data) & 0xFFFFFFFF

    @staticmethod
    def calculate_md5(data):
        """计算MD5校验值"""
        import hashlib
        return hashlib.md5(data).hexdigest()


def upgrade_firmware(usb_device, firmware_data, start_address, verify=True, show_progress=True):
    """
    执行固件升级

    Args:
        usb_device: USB设备实例
        firmware_data: 固件数据
        start_address: 起始地址
        verify: 是否校验
        show_progress: 是否显示进度

    Returns:
        tuple: (success, message)
    """
    try:
        print("=" * 60)
        print("开始固件升级...")
        print(f"固件大小: {len(firmware_data)} 字节")
        print(f"起始地址: 0x{start_address:08X}")

        if not usb_device.is_connected:
            return False, "设备未连接"

        # 计算CRC32
        crc32 = FirmwareLoader.calculate_crc32(firmware_data)
        print(f"固件CRC32: 0x{crc32:08X}")
        logger.info(f"固件CRC32: 0x{crc32:08X}")

        # 擦除Flash
        print("\n[1/4] 正在擦除Flash...")
        success, msg, _ = usb_device.erase_flash()
        if not success:
            return False, f"擦除失败: {msg}"
        print("  Flash擦除成功")
        logger.info("Flash擦除成功")

        # 编程Flash
        print("\n[2/4] 正在编程...")
        chunk_size = 60 # IAP program struct max data size is 62, but using 60 is safer and aligns well
        firmware_size = len(firmware_data)
        
        # 为了配合 Bootloader 端 256 字节的缓存逻辑，最好将数据填充为 256 的整数倍
        padded_firmware = bytearray(firmware_data)
        if len(padded_firmware) % 256 != 0:
            padding_len = 256 - (len(padded_firmware) % 256)
            padded_firmware.extend(b'\xFF' * padding_len)
        
        firmware_size = len(padded_firmware)
        total_chunks = (firmware_size + chunk_size - 1) // chunk_size

        for i in range(0, firmware_size, chunk_size):
            chunk = padded_firmware[i:i + chunk_size]

            success, msg, _ = usb_device.program_flash(chunk)
            if not success:
                return False, f"编程失败 @ 进度 {i}/{firmware_size}: {msg}"

            if show_progress:
                progress = (i // chunk_size + 1) * 100 // total_chunks
                print(f"\r  进度: {progress}% ({i + len(chunk)}/{firmware_size} 字节)", end='', flush=True)

        if show_progress:
            print()
        print("  编程完成")
        logger.info("编程完成")

        # 校验Flash
        if verify:
            print("\n[3/4] 正在校验...")
            chunk_size = 56 # IAP verify struct max data size is 56
            
            # 使用已补齐为 256 整数倍的 padded_firmware，不再额外补齐
            verify_size = len(padded_firmware)
            total_chunks = (verify_size + chunk_size - 1) // chunk_size

            for i in range(0, verify_size, chunk_size):
                chunk = padded_firmware[i:i + chunk_size]

                success, msg, _ = usb_device.verify_flash(start_address + i, chunk)
                if not success:
                    return False, f"校验失败 @ 进度 {i}/{verify_size}: {msg}"

                if show_progress:
                    progress = (i // chunk_size + 1) * 100 // total_chunks
                    print(f"\r  校验进度: {progress}%", end='', flush=True)

            if show_progress:
                print()
            print("  校验完成")
            logger.info("校验完成")

        # 结束升级
        print("\n[4/4] 结束升级...")
        success, msg, _ = usb_device.end_upgrade()
        if not success:
            return False, f"结束失败: {msg}"

        print("  升级结束命令已发送")
        logger.info("升级结束")

        print("\n" + "=" * 60)
        print("升级成功!")
        print(f"CRC32: 0x{crc32:08X}")
        print("=" * 60)

        return True, "升级完成"

    except KeyboardInterrupt:
        print("\n升级已取消")
        return False, "用户取消"

    except Exception as e:
        logger.exception("升级失败")
        return False, f"升级失败: {str(e)}"


def list_devices():
    """列出可用的USB设备"""
    print("扫描USB设备...")
    
    if not USB_AVAILABLE:
        print("错误: 未安装pyusb或libusb_package库")
        return

    backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
    devices = list(usb.core.find(find_all=True, idVendor=USBDevice.VID, idProduct=USBDevice.PID, backend=backend))
    
    if devices:
        print(f"\n找到 {len(devices)} 个设备:")
        for i, dev in enumerate(devices):
            print(f"  [{i+1}] VID=0x{dev.idVendor:04X}, PID=0x{dev.idProduct:04X}")
    else:
        print(f"\n未找到设备 (VID=0x{USBDevice.VID:04X}, PID=0x{USBDevice.PID:04X})")
        print("请检查:")
        print("  - USB线缆是否连接正常")
        print("  - 设备是否已上电")
        print("  - USB驱动是否正确安装")


def main():
    parser = argparse.ArgumentParser(
        description='CH32V305GBU USB OTA 上位机 (命令行版)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s -l                          # 列出设备
  %(prog)s -f firmware.bin             # 升级固件（默认校验）
  %(prog)s -f firmware.hex             # 升级HEX格式固件
  %(prog)s -f firmware.bin --no-verify # 升级但不校验
  %(prog)s -f firmware.bin -r 5        # 设置重试次数为5
  %(prog)s -j                          # 跳转到应用程序 (Bootloader中执行)
  %(prog)s -w                          # 发送控制指令让APP进入Bootloader
        """
    )

    parser.add_argument('-f', '--firmware', help='固件文件路径 (BIN或HEX格式)')
    parser.add_argument('-l', '--list', action='store_true', help='列出USB设备')
    parser.add_argument('-j', '--jump', action='store_true', help='跳转到应用程序 (需要设备在Bootloader模式)')
    parser.add_argument('-w', '--wake', action='store_true', help='发送特定的Control Transfer指令，让APP进入Bootloader模式')
    parser.add_argument('--no-verify', action='store_true', default=False, help='跳过固件校验')
    parser.add_argument('-r', '--retries', type=int, default=3, help='USB通信重试次数 (默认: 3)')
    parser.add_argument('-q', '--quiet', action='store_true', help='安静模式，减少输出')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 2.0 (CLI)')

    args = parser.parse_args()

    # 检查USB库
    if not USB_AVAILABLE:
        print("错误: 未安装pyusb库")
        print("请运行: pip install pyusb")
        return 1

    # 列出设备
    if args.list:
        list_devices()
        return 0

    # 跳转到APP
    if args.jump:
        print("正在连接设备(Bootloader模式)...")
        usb_device = USBDevice(max_retries=args.retries)
        success, msg = usb_device.connect()
        if not success:
            print(f"错误: {msg}")
            return 1
        
        print("发送跳转命令...")
        success, msg, _ = usb_device.jump_to_app()
        usb_device.disconnect()
        
        if success:
            print("已发送跳转命令，应用程序即将启动")
            return 0
        else:
            print(f"跳转失败: {msg}")
            return 1

    # 唤醒 Bootloader (向APP发送特定指令)
    if args.wake:
        print("正在向设备发送唤醒 Bootloader 的指令...")
        usb_device = USBDevice(max_retries=args.retries)
        # 不调用标准的 connect，因为 wake_bootloader 里会直接尝试通信
        success, msg = usb_device.wake_bootloader()
        
        if success:
            print(msg)
            print("如果设备重新识别，请再次运行烧录命令 `-f firmware.bin`")
            return 0
        else:
            print(f"错误: {msg}")
            return 1

    # 固件升级
    if args.firmware:
        # 检查文件
        if not os.path.exists(args.firmware):
            print(f"错误: 文件不存在: {args.firmware}")
            return 1

        # 加载固件
        print("加载固件文件...")
        success, msg, firmware_data, start_addr = FirmwareLoader.load_firmware(args.firmware)
        if not success:
            print(f"错误: {msg}")
            return 1

        print(f"  文件: {args.firmware}")
        print(f"  大小: {len(firmware_data)} 字节")
        print(f"  起始地址: 0x{start_addr:08X}")

        # 连接设备
        print("\n正在连接USB设备...")
        usb_device = USBDevice(max_retries=args.retries)
        success, msg = usb_device.connect()
        if not success:
            print(f"错误: {msg}")
            return 1
        print(f"  {msg}")

        try:
            # 执行升级
            verify = not args.no_verify
            show_progress = not args.quiet
            success, msg = upgrade_firmware(usb_device, firmware_data, start_addr, verify, show_progress)
            
            if success:
                return 0
            else:
                print(f"\n错误: {msg}")
                return 1
        finally:
            usb_device.disconnect()

    # 没有参数，显示帮助
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
