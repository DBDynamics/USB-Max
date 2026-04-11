#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
libBeeS.py
BeeS Motor Operations Class over USB485Max
"""

from libUSBMax import USB485MaxRegCtrl

class BeeS:
    """
    Class for handling motor operations.
    """
    def __init__(self):
        self.ctrl = USB485MaxRegCtrl()
        if not self.ctrl.connect():
            raise RuntimeError("Failed to connect to USB device.")
        
    def setPowerOn(self, node_id: int) -> bool:
        """
        Enables power on for a specific node ID by setting the corresponding bit in cmd_enable register.
        """
        cmd_enable_index = 0  # The register index for cmd_enable
        
        # 1. Read the current cmd_enable value
        current_data = self.ctrl.read_cmd_register(cmd_enable_index, count=1)
        if not current_data:
            print("Error: Could not read cmd_enable register for setPowerOn.")
            return False
            
        current_val = current_data[0]
        
        # 2. Modify the value (set the specific bit)
        new_val = current_val | (0x1 << node_id)
        
        # 3. Write back the new value
        print(f"Setting Power On for ID {node_id} (cmd_enable: {current_val:08X} -> {new_val:08X})")
        return self.ctrl.write_register(cmd_enable_index, [new_val])

    def setPowerOff(self, node_id: int) -> bool:
        """
        Disables power on for a specific node ID by clearing the corresponding bit in cmd_enable register.
        """
        cmd_enable_index = 0  # The register index for cmd_enable
        
        # 1. Read the current cmd_enable value
        current_data = self.ctrl.read_cmd_register(cmd_enable_index, count=1)
        if not current_data:
            print("Error: Could not read cmd_enable register for setPowerOff.")
            return False
            
        current_val = current_data[0]
        
        # 2. Modify the value (clear the specific bit using bitwise AND with NOT)
        new_val = current_val & ~(0x1 << node_id)
        
        # 3. Write back the new value
        print(f"Setting Power Off for ID {node_id} (cmd_enable: {current_val:08X} -> {new_val:08X})")
        return self.ctrl.write_register(cmd_enable_index, [new_val])

    def setHomingLevel(self, node_id: int, value: int) -> bool:
        """
        Sets the homing level for a specific node ID by modifying the corresponding bit in cmd_homing_level register.
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return False
            
        cmd_homing_level_index = 1
        
        # 1. Read the current cmd_homing_level value
        current_data = self.ctrl.read_cmd_register(cmd_homing_level_index, count=1)
        if not current_data:
            print(f"Error: Could not read cmd_homing_level register for setHomingLevel.")
            return False
            
        current_val = current_data[0]
        
        # 2. Modify the value
        if value:
            new_val = current_val | (0x1 << node_id)
        else:
            new_val = current_val & ~(0x1 << node_id)
            
        # 3. Write back the new value
        print(f"Setting Homing Level for ID {node_id} to {value} (cmd_homing_level: {current_val:08X} -> {new_val:08X})")
        return self.ctrl.write_register(cmd_homing_level_index, [new_val])

    def getHomingLevel(self, node_id: int) -> int:
        """
        Gets the homing level for a specific node ID by reading the cmd_homing_level register (index 1).
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return None
            
        cmd_homing_level_index = 1
        
        data = self.ctrl.read_cmd_register(cmd_homing_level_index, count=1)
        if data:
            current_val = data[0]
            # Extract the specific bit
            return (current_val >> node_id) & 0x1
        else:
            print(f"Error: Could not read homing level for ID {node_id}")
            return None

    def setHomingDir(self, node_id: int, value: int) -> bool:
        """
        Sets the homing direction for a specific node ID by modifying the corresponding bit in cmd_homing_dir register.
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return False
            
        cmd_homing_dir_index = 2
        
        # 1. Read the current cmd_homing_dir value
        current_data = self.ctrl.read_cmd_register(cmd_homing_dir_index, count=1)
        if not current_data:
            print(f"Error: Could not read cmd_homing_dir register for setHomingDir.")
            return False
            
        current_val = current_data[0]
        
        # 2. Modify the value
        if value:
            new_val = current_val | (0x1 << node_id)
        else:
            new_val = current_val & ~(0x1 << node_id)
            
        # 3. Write back the new value
        print(f"Setting Homing Dir for ID {node_id} to {value} (cmd_homing_dir: {current_val:08X} -> {new_val:08X})")
        return self.ctrl.write_register(cmd_homing_dir_index, [new_val])

    def getHomingDir(self, node_id: int) -> int:
        """
        Gets the homing direction for a specific node ID by reading the cmd_homing_dir register (index 2).
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return None
            
        cmd_homing_dir_index = 2
        
        data = self.ctrl.read_cmd_register(cmd_homing_dir_index, count=1)
        if data:
            current_val = data[0]
            # Extract the specific bit
            return (current_val >> node_id) & 0x1
        else:
            print(f"Error: Could not read homing dir for ID {node_id}")
            return None

    def setAccTime(self, node_id: int, value: int) -> bool:
        """
        Sets the acceleration time (ac0) for a specific node ID.
        The acceleration times are stored sequentially starting at cmd_ac0 (index 74).
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return False
            
        base_ac_index = 74  # cmd_ac0
        target_index = base_ac_index + node_id
        
        print(f"Setting Acceleration Time for ID {node_id} to {value} at index {target_index}")
        return self.ctrl.write_register(target_index, [value])

    def getAccTime(self, node_id: int) -> int:
        """
        Gets the acceleration time (ac0) for a specific node ID.
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return None
            
        base_ac_index = 74  # cmd_ac0
        target_index = base_ac_index + node_id
        
        data = self.ctrl.read_cmd_register(target_index, count=1)
        if data:
            return data[0]
        else:
            print(f"Error: Could not read acceleration time for ID {node_id}")
            return None

    def setStateInit(self) -> bool:
        """
        Sets the global command state (cmd_state) to Init (value 5).
        """
        cmd_state_index = 3
        print(f"Setting global state to Init (5) at cmd_state index {cmd_state_index}")
        return self.ctrl.write_register(cmd_state_index, [5])

    def setStateRun(self) -> bool:
        """
        Sets the global command state (cmd_state) to Run (value 6).
        """
        cmd_state_index = 3
        print(f"Setting global state to Run (6) at cmd_state index {cmd_state_index}")
        return self.ctrl.write_register(cmd_state_index, [6])

    def getState(self) -> int:
        """
        Gets the current global command state (cmd_state) (index 3).
        """
        cmd_state_index = 3
        data = self.ctrl.read_cmd_register(cmd_state_index, count=1)
        if data:
            return data[0]
        else:
            print("Error: Could not read cmd_state register.")
            return None

    def scanDevices(self) -> list:
        """
        Scans for online devices by reading the st_online register (index 0).
        Returns a list of node IDs that are currently online (bit is 1).
        """
        st_online_index = 0
        online_ids = []
        
        # Read the st_online register from the status buffer (use read_register, not read_cmd_register)
        data = self.ctrl.read_register(st_online_index, count=1)
        
        if not data:
            print("Error: Could not read st_online register.")
            return online_ids
            
        current_val = data[0]
        
        # Check each bit from 0 to 31
        for node_id in range(32):
            if (current_val >> node_id) & 0x1:
                online_ids.append(node_id)
                
        return online_ids

    def getEnable(self, node_id: int) -> bool:
        """
        Gets the current enable (power on) status for a specific node ID.
        Reads the st_on register (index 2) and checks the corresponding bit.
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return False
            
        st_on_index = 2
        
        # Read the st_on register from the status buffer
        data = self.ctrl.read_register(st_on_index, count=1)
        
        if not data:
            print(f"Error: Could not read st_on register for getEnable.")
            return False
            
        current_val = data[0]
        # Return True if the bit is 1, False otherwise
        return bool((current_val >> node_id) & 0x1)

    def setTargetVelocity(self, node_id: int, velocity: int) -> bool:
        """
        Sets the target velocity for a specific node ID.
        The target velocities are stored sequentially starting at cmd_tv0 (index 42).
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return False
            
        base_tv_index = 42  # cmd_tv0
        target_index = base_tv_index + node_id
        
        print(f"Setting Target Velocity for ID {node_id} to {velocity} at index {target_index}")
        return self.ctrl.write_register(target_index, [velocity])

    def getTargetVelocity(self, node_id: int) -> int:
        """
        Gets the target velocity for a specific node ID.
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return None
            
        base_tv_index = 42  # cmd_tv0
        target_index = base_tv_index + node_id
        
        data = self.ctrl.read_cmd_register(target_index, count=1)
        if data:
            return data[0]
        else:
            print(f"Error: Could not read target velocity for ID {node_id}")
            return None

    def setTargetPosition(self, node_id: int, position: int) -> bool:
        """
        Sets the target position for a specific node ID.
        The target positions are stored sequentially starting at cmd_tp0 (index 10).
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return False
            
        base_tp_index = 10  # cmd_tp0
        target_index = base_tp_index + node_id
        
        print(f"Setting Target Position for ID {node_id} to {position} at index {target_index}")
        return self.ctrl.write_register(target_index, [position])

    def setTp(self, positions: list) -> bool:
        """
        Sets the target position for multiple nodes at once, starting from ID 0.
        The target positions are stored sequentially starting at cmd_tp0 (index 10).
        """
        if not positions or len(positions) > 32:
            print(f"Error: positions array must have between 1 and 32 elements. Got {len(positions)}.")
            return False
            
        base_tp_index = 10  # cmd_tp0
        print(f"Setting {len(positions)} Target Positions starting at index {base_tp_index}")
        return self.ctrl.write_register(base_tp_index, positions)

    def getTargetPosition(self, node_id: int) -> int:
        """
        Gets the target position for a specific node ID.
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return None
            
        base_tp_index = 10  # cmd_tp0
        target_index = base_tp_index + node_id
        
        data = self.ctrl.read_cmd_register(target_index, count=1)
        if data:
            return data[0]
        else:
            print(f"Error: Could not read target position for ID {node_id}")
            return None

    def getActualPosition(self, node_id: int) -> int:
        """
        Gets the actual position for a specific node ID.
        The actual positions are stored in the ST buffer starting at st_ap0 (index 41).
        """
        if node_id < 0 or node_id > 31:
            print(f"Error: node_id {node_id} out of range (0-31).")
            return None
            
        base_ap_index = 41  # st_ap0
        target_index = base_ap_index + node_id
        
        # Note: Actual position is in the status (ST) buffer, so we use read_register
        data = self.ctrl.read_register(target_index, count=1)
        if data:
            return data[0]
        else:
            print(f"Error: Could not read actual position for ID {node_id}")
            return None