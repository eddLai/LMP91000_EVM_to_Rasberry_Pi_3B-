import RPi.GPIO as GPIO
from LMP_class.LMP91000_EVM import LMP91000_EVM
import spidev
import time
import math

GPIO.setmode(GPIO.BCM)
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

GPIO.setup(LED, GPIO.OUT)
GPIO.output(LED, GPIO.HIGH)
GPIO.output(LED, GPIO.LOW)

spi = spidev.SpiDev()
spi.open(0, 0)  # 0 代表 SPI 0 介面，0 代表 CE0 (CS 引腳)
spi.max_speed_hz = 5000000  # 設置 SPI 時鐘速度，具體根據應用要求設置
spi.mode = 0b00  # 設置 SPI 模式 (根據 LMP91000 的要求選擇 mode 0-3)

opVolt = 3300  # 工作電壓 (mV)
resolution = 16
adc_volt = 0.0
current_step = 0  # 使用 current_step 代替 step 變量避免衝突

lmp91000_evm = LMP91000_EVM(SDA, SCL, MOSI_PIN, MISO_PIN, SCLK_PIN, CS_PIN, MENB_INT, SDRDY, LED)