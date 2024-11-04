import RPi.GPIO as GPIO
from LMP_class.LMP91000_EVM import LMP91000_EVM
import spidev
import time
import math

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
SDA = 2 # SDA.1
SCL = 3 #SCL.1  
# GND12 4|17 
# GPSI3_3 22|10
MOSI_PIN = 10
MISO_PIN = 9
SCLK_PIN = 11 #SCLK
# GND2
CS_PIN = 10 #CE0
MENB_INT = 6
SDRDY = 26
LED = 18 #GPIO1

GPIO.setup(MOSI_PIN, GPIO.OUT)
GPIO.setup(MISO_PIN, GPIO.IN)
GPIO.setup(SCLK_PIN, GPIO.OUT)
GPIO.setup(CS_PIN, GPIO.OUT)

spi = spidev.SpiDev()
spi.open(0, 0)  # 0 代表 SPI 0 介面，0 代表 CE0 (CS 引腳)
spi.max_speed_hz = 5000000  # 設置 SPI 時鐘速度，具體根據應用要求設置
spi.mode = 0b00  # 設置 SPI 模式 (根據 LMP91000 的要求選擇 mode 0-3)

opVolt = 3300  # 工作電壓 (mV)
resolution = 16
adc_volt = 0.0
current_step = 0  # 使用 current_step 代替 step 變量避免衝突

# SPI 傳輸資料的 
def spi_transfer(data):
    response = spi.xfer2([data])  # 發送一個字節並接收回應
    return response[0]

# 讀取 LMP91000 寄存器數據
def read_register(register):
    GPIO.output(CS_PIN, GPIO.LOW)
    spi_transfer(register)  # 傳輸寄存器地址
    value = spi_transfer(0x00)  # 讀取寄存器內容
    GPIO.output(CS_PIN, GPIO.HIGH)  # 結束通信
    print(f"讀取寄存器 0x{register:02X} 值: {value}")
    return value

# 寫入 LMP91000 寄存器數據
def write_register(register, value):
    GPIO.output(CS_PIN, GPIO.LOW)  # 啟用 SPI 通信
    spi_transfer(register)  # 傳輸寄存器地址
    spi_transfer(value)  # 傳輸數值
    GPIO.output(CS_PIN, GPIO.HIGH)  # 結束通信
    print(f"寫入寄存器 0x{register:02X} 值: {value}")

# 配置 LMP91000 的函數
def configure_lmp91000():
    # 配置傳感器模式（根據具體應用，這裡寫入示例值）
    write_register(0x10, 0x03)  # 設定寄存器
    time.sleep(1)  # 模擬傳感器啟動時間

# 計算電壓和電流並列印
def run_amp(user_gain, pre_stepV, quietTime, v1, t1, v2, t2, samples, amp_range):
    print(f"開始 runAmp...")

    current_count = {
        12: "Current(pA)",
        9: "Current(nA)",
        6: "Current(uA)",
        3: "Current(mA)"
    }.get(amp_range, "SOME ERROR")
    
    print(f"Voltage(mV), Time(ms), {current_count}")

    voltage_array = [pre_stepV, v1, v2]
    time_array = [quietTime, t1, t2]
    
    current_step = 0  # 使用 current_step 代替 step 變量
    for i in range(3):
        fs = time_array[i] // samples  # 確認這裡的樣本數不會引發除以零錯誤
        voltage_array[i] = determine_lmp91000_bias(voltage_array[i])
        
        # 設置正負偏壓
        if voltage_array[i] < 0:
            set_neg_bias()
        else:
            set_pos_bias()
        
        start_time = time.time() * 1000  # 以毫秒計算
        set_bias(abs(voltage_array[i]))
        
        while (time.time() * 1000 - start_time) < time_array[i]:
            current_time = time.time() * 1000 - start_time  # 計算相對於開始時間的時間戳
            computed_value = lmp91000_evm.getVolt()  # 使用 LMP91000_EVM 的 getVolt() 方法來獲取真實的輸出電壓  # 使用 LMP91000 的 Vout 值作為輸出的電壓值  # 修正這裡的計算公式，避免過大的電壓值
            adc_volt = lmp91000_evm.getVolt()  # 使用 LMP91000_EVM 的 getVolt() 方法來獲取真實的 ADC 電壓  # 假設讀取到的 ADC 數據
            print(f"Step: {current_step}, Computed Value: {computed_value} mV, Timestamp: {current_time:.2f} ms")
            print(f"Vout: {(adc_volt - 1.5) / 1000} mV")
            current = math.pow(10, amp_range) * get_current(adc_volt, opVolt / 1000.0, resolution)
            print(f"Current: {current} {current_count}")
            current_step += 1  # 修改為 current_step 避免衝突
            time.sleep(fs / 1000)

    # 重置為 0V
    set_bias(0)

# 假設的設置偏壓函數 (根據 LMP91000 的設置)
def set_neg_bias():
    print("設置負偏壓")

def set_pos_bias():
    print("設置正偏壓")

def set_bias(voltage):
    print(f"設置偏壓: {voltage} mV")

def get_current(adc_out, op_volt, resolution):
    # 根據你的應用需求計算電流
    return (adc_out / resolution) * op_volt

# 假設的 bias 計算函數
def determine_lmp91000_bias(voltage):
    polarity = -1 if voltage < 0 else 1
    voltage = abs(voltage)
    return polarity * voltage

# 讀取模擬 ADC 數據 (根據實際情況，這裡是模擬讀取 ADC 數據)
def read_adc():
    # 使用 ADC161S626 類中的 read_adc 方法來讀取真實的 ADC 數據
    return lmp91000_evm.adc.read_adc()

# 清理引腳
def cleanup():
    GPIO.cleanup()
    spi.close()

# 主程式入口
# 初始化 LMP91000_EVM 類
lmp91000_evm = LMP91000_EVM(SDA, SCL, MOSI_PIN, MISO_PIN, SCLK_PIN, CS_PIN, MENB_INT, SDRDY, LED)

def main():
    configure_lmp91000()
    
    # 測試 runAmp
    run_amp(1, 0, 0, 200, 10000, 0, 0, 300, 6)

    # 清理引腳
    cleanup()

if __name__ == "__main__":
    main()
