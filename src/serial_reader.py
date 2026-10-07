# src/serial_reader.py
import serial
def read_lines(port, baudrate=9600, count =3, timeout=2):#串口设备名，波特率，读取次数，超时
    ser =serial.Serial(port,baudrate,timeout=timeout)
    lines =[]
    try:
        for _ in range(count):
            line =ser.readline()
            if line :
                lines.append(line.decode('ascii',errors='ignore').strip())
    finally:
        ser.close()
    return lines

