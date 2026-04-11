#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
libusb485max.py
USB485Max Python Register Control Library
Implements index-based Read/Write register communication over EP1/EP2
"""

import usb.core
import usb.util
import usb.backend.libusb1
import libusb_package
import struct

# Device Constants
USB_VID = 0x1A86
USB_PID = 0x5807

EP_OUT = 0x01
EP_IN  = 0x82

# Protocol Constants
CMD_READ_ST = 0x01
CMD_WRITE_CMD = 0x02
CMD_READ_CMD = 0x03

ACK_READ_OK = 0x81
ACK_WRITE_OK = 0x82
ACK_READ_CMD_OK = 0x83

class USB485MaxRegCtrl:
    def __init__(self):
        self.device = None
        self.interface = None

    def connect(self) -> bool:
        """Finds and connects to the USB device."""
        backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
        self.device = usb.core.find(idVendor=USB_VID, idProduct=USB_PID, backend=backend)
        if self.device is None:
            print("Error: USB device not found.")
            return False
            
        try:
            # Set active configuration
            self.device.set_configuration()
            print(f"Connected to USB device (VID: {USB_VID:04X}, PID: {USB_PID:04X})")
            return True
        except usb.core.USBError as e:
            if e.errno == 16:  # Device or resource busy
                try:
                    if self.device.is_kernel_driver_active(0):
                        self.device.detach_kernel_driver(0)
                    self.device.set_configuration()
                    print("Kernel driver detached and device connected.")
                    return True
                except Exception as detach_e:
                    print(f"Failed to detach kernel driver: {detach_e}")
            else:
                print(f"Failed to set configuration: {e}")
            return False

    def read_register(self, index: int, count: int = 1) -> list:
        """
        Reads `count` 32-bit registers starting from `index` from the ST buffer.
        """
        if not self.device:
            raise RuntimeError("Device not connected")

        if count < 1 or count > 126:
            raise ValueError("Count must be between 1 and 126")

        if index + count > 256:
            raise ValueError("Index + Count exceeds max register index (256)")

        # Pack the 4-byte header: [CMD(0x01)] [Index] [Count] [Reserved(0x00)]
        header = struct.pack('<BBBB', CMD_READ_ST, index, count, 0x00)

        try:
            # Send request via EP1
            self.device.write(EP_OUT, header, 1000)

            # Receive response via EP2
            # Max expected size is 4 bytes header + count * 4 bytes data
            expected_size = 4 + count * 4
            response = self.device.read(EP_IN, 512, 1000)

            if len(response) >= 4:
                resp_cmd, resp_idx, resp_count, _ = struct.unpack('<BBBB', response[:4])
                
                if resp_cmd != ACK_READ_OK:
                    print(f"Error: Unexpected response command 0x{resp_cmd:02X}")
                    return None
                    
                if resp_idx != index or resp_count != count:
                    print(f"Error: Mismatched response index/count ({resp_idx}, {resp_count})")
                    return None

                # Unpack the data payload
                data_bytes = response[4:4 + count * 4]
                data_ints = list(struct.unpack('<' + 'i' * count, data_bytes))
                return data_ints
            else:
                print("Error: Incomplete response received.")
                return None

        except usb.core.USBError as e:
            print(f"USB Error during read_register: {e}")
            return None

    def read_cmd_register(self, index: int, count: int = 1) -> list:
        """
        Reads `count` 32-bit registers starting from `index` from the CMD buffer.
        """
        if not self.device:
            raise RuntimeError("Device not connected")

        if count < 1 or count > 126:
            raise ValueError("Count must be between 1 and 126")

        if index + count > 256:
            raise ValueError("Index + Count exceeds max register index (256)")

        # Pack the 4-byte header: [CMD(0x03)] [Index] [Count] [Reserved(0x00)]
        header = struct.pack('<BBBB', CMD_READ_CMD, index, count, 0x00)

        try:
            # Send request via EP1
            self.device.write(EP_OUT, header, 1000)

            # Receive response via EP2
            response = self.device.read(EP_IN, 512, 1000)

            if len(response) >= 4:
                resp_cmd, resp_idx, resp_count, _ = struct.unpack('<BBBB', response[:4])
                
                if resp_cmd != ACK_READ_CMD_OK:
                    print(f"Error: Unexpected response command 0x{resp_cmd:02X}")
                    return None
                    
                if resp_idx != index or resp_count != count:
                    print(f"Error: Mismatched response index/count ({resp_idx}, {resp_count})")
                    return None

                # Unpack the data payload
                data_bytes = response[4:4 + count * 4]
                data_ints = list(struct.unpack('<' + 'i' * count, data_bytes))
                return data_ints
            else:
                print("Error: Incomplete response received.")
                return None

        except usb.core.USBError as e:
            print(f"USB Error during read_cmd_register: {e}")
            return None

    def write_register(self, index: int, values: list) -> bool:
        """
        Writes a list of 32-bit integers to the CMD buffer starting at `index`.
        """
        if not self.device:
            raise RuntimeError("Device not connected")

        count = len(values)
        if count < 1 or count > 126:
            raise ValueError("Count must be between 1 and 126")

        if index + count > 256:
            raise ValueError("Index + Count exceeds max register index (256)")

        # Pack the 4-byte header: [CMD(0x02)] [Index] [Count] [Reserved(0x00)]
        header = struct.pack('<BBBB', CMD_WRITE_CMD, index, count, 0x00)
        
        # Pack the data payload (array of 32-bit ints)
        data_payload = struct.pack('<' + 'i' * count, *values)
        
        # Full packet
        packet = header + data_payload

        try:
            # Send request + data via EP1
            self.device.write(EP_OUT, packet, 1000)

            # Receive ACK via EP2
            response = self.device.read(EP_IN, 512, 1000)

            if len(response) >= 4:
                resp_cmd, resp_idx, resp_count, _ = struct.unpack('<BBBB', response[:4])
                
                if resp_cmd == ACK_WRITE_OK and resp_idx == index and resp_count == count:
                    return True
                else:
                    print(f"Error: Write failed or mismatched ACK: Cmd=0x{resp_cmd:02X}")
                    return False
            else:
                print("Error: Incomplete ACK received.")
                return False

        except usb.core.USBError as e:
            print(f"USB Error during write_register: {e}")
            return False
