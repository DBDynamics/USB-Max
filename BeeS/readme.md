# 如何在MacOS下使用pystlink升级固件

本教程将指导您如何在 MacOS 系统下，使用 `pystlink` 工具为设备刷入最新的 `BeeS2.bin` 固件。

## 1. 准备工作

* **硬件准备**：
  * ST-Link V2 下载器（或兼容的调试器）。
  * 目标设备（BeeS），以及连接 ST-Link 与目标板的杜邦线（必须连接 `SWDIO`, `SWCLK`, `GND`, 以及供电引脚 `3.3V` 或 `5V`）。
* **软件环境**：
  * MacOS 系统已安装 Python 3 环境（如果未安装，可通过 Homebrew 安装：`brew install python`）。

## 2. 安装 pystlink

打开终端（Terminal），使用 `pip` 安装 `pystlink` 库和命令行工具：

```bash
pip3 install pystlink
```
*(注：如果提示权限或环境错误，建议使用虚拟环境，或添加 `--break-system-packages` / `--user` 参数)*

## 3. 连接硬件设备

将 ST-Link 插入 Mac 的 USB 接口，并确保其与目标板的引脚正确连接：
* ST-Link `SWDIO`  -> 目标板 `SWDIO`
* ST-Link `SWCLK`  -> 目标板 `SWCLK`
* ST-Link `GND`    -> 目标板 `GND`
* ST-Link `3.3V`   -> 目标板 `3.3V`

## 4. 刷入固件

在终端中，通过 `cd` 命令切换到包含 `BeeS2.bin` 固件的目录：

```bash
cd ~/Documents/GitHub/USB-Max/BeeS
```

执行以下命令测试 ST-Link 是否正常连接并识别到芯片：

```bash
pystlink -i
```

如果成功识别到芯片信息，接着执行固件烧录命令：

```bash
pystlink flash:w:BeeS2.bin
```

等待终端打印擦除、写入和校验的进度。当出现 `Verified OK` 或类似成功提示时，说明固件已成功升级！

## 5. 常见问题排查

* **找不到 ST-Link (No ST-Link detected)**：请检查 USB 是否插紧，或者尝试更换 Mac 的 USB 接口/扩展坞。在系统信息(System Information) -> USB 中确认是否识别到 ST-Link 设备。
* **无法连接到目标芯片 (Target not found)**：请仔细检查 `SWDIO` 和 `SWCLK` 接线是否松动或接反，确认目标板已正常供电。如果芯片被锁，可能需要执行解锁命令。
