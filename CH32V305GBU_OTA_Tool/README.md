# CH32V305GBU USB OTA 固件升级工具

这是一个用于通过 USB 接口对 CH32V305GBU 微控制器进行 OTA (In-Application Programming) 固件升级的 Python 跨平台工具。

## 目录结构

- `usb_ota_tool.py`: 核心升级脚本
- `requirements.txt`: Python 依赖文件
- `CH32V305GBU6.bin`: 预编译的 APP 固件文件（示例）
- `README.md`: 本说明文档

---

## 1. 环境准备

请确保您的电脑上已经安装了 **Python 3.6** 或更高版本。

### 安装依赖包

在命令行（终端）中进入本工具所在目录，执行以下命令安装依赖：

```bash
pip install -r requirements.txt
```

---

## 2. 操作系统配置与驱动安装

根据您使用的操作系统，可能需要进行额外的配置才能通过 USB 访问设备。

### Windows 系统

在 Windows 下，`pyusb` 需要通过 `libusb` 来访问 USB 设备。当设备处于 **Bootloader 模式**（设备管理器中可能显示为未识别的设备或带有黄色感叹号），您需要使用 **Zadig** 工具为其安装 WinUSB 驱动。

1. 下载并运行 [Zadig](https://zadig.akeo.ie/)。
2. 在菜单栏选择 `Options` -> `List All Devices`。
3. 在下拉列表中找到对应的 USB 设备（VID: `4348`, PID: `55E0`）。
4. 在右侧的目标驱动列表中选择 **WinUSB (v6.1.7600.16385)**。
5. 点击 `Install Driver` 或 `Replace Driver` 按钮。
6. 安装完成后，即可运行 Python 脚本进行烧录。

### Linux 系统

在 Linux 下，普通用户通常没有直接访问 USB 硬件的权限。您可以通过 `sudo` 运行脚本，或者配置 `udev` 规则以免去 `sudo`。

**方法一：使用 sudo (推荐临时测试)**
```bash
sudo python3 usb_ota_tool.py -f CH32V305GBU6.bin
```

**方法二：配置 udev 规则 (推荐长期使用)**
1. 创建一个新的 udev 规则文件：
```bash
sudo nano /etc/udev/rules.d/99-ch32v.rules
```
2. 写入以下内容（对应 VID `4348`）：
```text
SUBSYSTEM=="usb", ATTR{idVendor}=="4348", MODE="0666", GROUP="plugdev"
```
3. 重新加载 udev 规则：
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```
4. 重新插拔 USB 设备，现在您可以直接使用普通用户权限运行脚本了。

### macOS 系统

macOS 原生自带了 libusb 所需的部分支持。您通常可以直接运行本脚本。
如果遇到找不到 `libusb` 后端的错误，可以通过 Homebrew 安装：

```bash
brew install libusb
```

---

## 3. 使用方法

确保设备已经通过 USB 连接到电脑。

### 常用命令

**1. 升级固件 (最常用)**
```bash
python usb_ota_tool.py -f CH32V305GBU6.bin
```
*此命令会自动执行擦除、编程、校验并重启设备。*

**2. 唤醒设备进入 Bootloader**
如果设备当前正在运行 APP，您可以通过以下命令向其发送特定的控制指令，让其自动重启并进入 Bootloader 模式（前提是 APP 代码中实现了相应的监听逻辑）：
```bash
python usb_ota_tool.py -w
```
*唤醒后，再次运行 `-f` 命令进行烧录。*

**3. 列出所有兼容的 USB 设备**
```bash
python usb_ota_tool.py -l
```

**4. 跳过校验步骤**
如果您只想快速烧录而不想等待校验，可以添加 `--no-verify` 参数：
```bash
python usb_ota_tool.py -f CH32V305GBU6.bin --no-verify
```

### 查看所有帮助
```bash
python usb_ota_tool.py -h
```

---

## 4. 常见问题排查

- **[Errno 13] Access denied (insufficient permissions)**
  - Linux: 没有权限访问 USB。请使用 `sudo` 或配置 `udev` 规则。
- **NotImplementedError: Operation not supported or unimplemented on this platform**
  - Windows: 驱动不匹配。请参考上文使用 Zadig 安装 WinUSB 驱动。
- **USB设备连接失败**
  - 检查 USB 线是否具有数据传输功能。
  - 确认设备是否已进入 Bootloader 模式。您可以使用 `-w` 命令尝试唤醒，或者按住 Boot 按键后复位设备。