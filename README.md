# USB-Max

## 介绍
- USB485-Max是一款超级USB-485转换器 用于高效率数据同步

## 特性
- USB2.0接口通信速度高达480Mbps
- RS485收发器的通信速度高达20Mbps
- 协处理器实时处理数据

## 硬件
- MCU CH32V305
- RS485收发器: 

## 通信协议
- 大体思路： 512bytes 内存同步 同步周期 1ms
- 内存中包括了 32个节点的全部信息 平均每个节点 512/32=16bytes
- 客户端为PC侧 发送的消息为cmd message
- 服务端为MCU侧 发送的消息为status message
```c
typedef struct
{
    unsigned char cmd; 
}cmdObj;
```