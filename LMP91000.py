import smbus2
import RPi.GPIO as GPIO
import time
import ADC161S626

TEMP_INTERCEPT = 1555.0
TEMPSLOPE = -8.0
LMP91000_I2C_ADDRESS = 0x48

LMP91000_STATUS_REG = 0x00  # Read only status register
LMP91000_LOCK_REG = 0x01  # Protection Register
LMP91000_TIACN_REG = 0x10  # TIA Control Register
LMP91000_REFCN_REG = 0x11  # Reference Control Register
LMP91000_MODECN_REG = 0x12  # Mode Control Register

LMP91000_READY = 0x01
LMP91000_NOT_READY = 0x00

LMP91000_TIA_GAIN_EXT = 0x00  # default
LMP91000_TIA_GAIN_2P75K = 0x04
LMP91000_TIA_GAIN_3P5K = 0x08
LMP91000_TIA_GAIN_7K = 0x0C
LMP91000_TIA_GAIN_14K = 0x10
LMP91000_TIA_GAIN_35K = 0x14
LMP91000_TIA_GAIN_120K = 0x18
LMP91000_TIA_GAIN_350K = 0x1C

LMP91000_RLOAD_10OHM = 0x00
LMP91000_RLOAD_33OHM = 0x01
LMP91000_RLOAD_50OHM = 0x02
LMP91000_RLOAD_100OHM = 0x03  # default

LMP91000_REF_SOURCE_INT = 0x00  # default
LMP91000_REF_SOURCE_EXT = 0x80

LMP91000_INT_Z_20PCT = 0x00
LMP91000_INT_Z_50PCT = 0x20  # default
LMP91000_INT_Z_67PCT = 0x40
LMP91000_INT_Z_BYPASS = 0x60

LMP91000_BIAS_SIGN_NEG = 0x00  # default
LMP91000_BIAS_SIGN_POS = 0x10

LMP91000_BIAS_0PCT = 0x00  # default
LMP91000_BIAS_1PCT = 0x01
LMP91000_BIAS_2PCT = 0x02
LMP91000_BIAS_4PCT = 0x03
LMP91000_BIAS_6PCT = 0x04
LMP91000_BIAS_8PCT = 0x05
LMP91000_BIAS_10PCT = 0x06
LMP91000_BIAS_12PCT = 0x07
LMP91000_BIAS_14PCT = 0x08
LMP91000_BIAS_16PCT = 0x09
LMP91000_BIAS_18PCT = 0x0A
LMP91000_BIAS_20PCT = 0x0B
LMP91000_BIAS_22PCT = 0x0C
LMP91000_BIAS_24PCT = 0x0D

LMP91000_FET_SHORT_DISABLED = 0x00  # default
LMP91000_FET_SHORT_ENABLED = 0x80
LMP91000_OP_MODE_DEEP_SLEEP = 0x00  # default
LMP91000_OP_MODE_GALVANIC = 0x01
LMP91000_OP_MODE_STANDBY = 0x02
LMP91000_OP_MODE_AMPEROMETRIC = 0x03
LMP91000_OP_MODE_TIA_OFF = 0x06
LMP91000_OP_MODE_TIA_ON = 0x07

LMP91000_WRITE_LOCK = 0x01  # default
LMP91000_WRITE_UNLOCK = 0x00

LMP91000_NOT_PRESENT = 0xA8  # arbitrary library status code

TIA_GAIN = [2750, 3500, 7000, 14000, 35000, 120000, 350000]
TIA_BIAS = [0, 0.01, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.22, 0.24]
NUM_TIA_BIAS = 14
TIA_ZERO = [0.2, 0.5, 0.67]

class LMP91000:
    
    def __init__(self, bus_number, menb):
        self._MENB = menb  # IO pin for enabling and disabling I2C commands
        self._gain = None
        self._zero = None
        self._ready = False
        self._locked = True
        self.i2c_address = LMP91000_I2C_ADDRESS
        GPIO.setmode(GPIO.BCM)
        self.bus = smbus2.SMBus(bus_number)

    # in Linner Lab Arduino code is called setMENB
    def initMENB(self, pin: int):
        self._MENB = pin
        GPIO.setup(self._MENB, GPIO.OUT)
    
    def enable(self):
        GPIO.output(self._MENB, GPIO.LOW)

    def disable(self):
        GPIO.output(self._MENB, GPIO.HIGH)

    def isReady(self) -> bool:
        self._ready = self.bus.read_byte_data(self.i2c_address, LMP91000_STATUS_REG)==LMP91000_READY
        return self._ready
    
    def isLocked(self) -> bool:
        reg_value = self.bus.read_byte_data(self.i2c_address, LMP91000_LOCK_REG)
        # check the first bit, i = 0
        return (reg_value & 0x01) == LMP91000_WRITE_LOCK
    
    def lock(self):
        self.bus.write_byte_data(self.i2c_address, LMP91000_LOCK_REG, LMP91000_WRITE_LOCK)

    def unlock(self):
        self.bus.write_byte_data(self.i2c_address, LMP91000_LOCK_REG, LMP91000_WRITE_UNLOCK)

    # 0 - 000 - External resistor
    # 1 - 001 - 2.75 kOhm
    # 2 - 010 - 3.5 kOhm
    # 3 - 011 - 7 kOhm
    # 4 - 100 - 14 kOhm
    # 5 - 101 - 35 kOhm
    # 6 - 110 - 120 kOhm
    # 7 - 111 - 350 kOhm
    def setGain(self, user_gain: int):
        self.gain = user_gain
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_TIACN_REG)
        # 清除第2-4位（用於增益設置）
        data &= ~(0x07 << 2)
        # 將user_gain參數的3個LSB寫入第2, 3, 4位
        data |= (user_gain & 0x07 << 2)
        self.bus.write_byte_data(self.i2c_address, LMP91000_TIACN_REG, data)
        self.lock()
        self.gain = user_gain

    def getGain(self) -> float:
        if self.gain == 0:
            return 0  # External resistor
        else:
            return TIA_GAIN[self.gain - 1]
    
    # 0 - 00 - 10 Ohm
    # 1 - 01 - 33 Ohm
    # 2 - 10 - 50 Ohm
    # 3 - 11 - 100 Ohm
    def setRLoad(self, load: int):
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_TIACN_REG)
        # 清除第0-1位（這些位元是用於負載設置的）
        data &= ~(0x03)  # 0x03代表2個LSB
        data |= (load & 0x03)
        self.bus.write_byte_data(self.i2c_address, LMP91000_TIACN_REG, data)
        self.lock()
    
    # 0 - internal reference
    # 1 - external reference
    def setRefSource(self, source: int):
        if source == 0:
            self.setIntRefSource()
        else:
            self.setExtRefSource()

    def setIntRefSource(self):
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_REFCN_REG)
        data &= ~(1 << 7)  # 清除第7位
        self.bus.write_byte_data(self.i2c_address, LMP91000_REFCN_REG, data)

    def setExtRefSource(self):
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_REFCN_REG)
        data |= (1 << 7)  # 設置第7位
        self.bus.write_byte_data(self.i2c_address, LMP91000_REFCN_REG, data)

    # set the divider on V-ref
    # 0 - 00 - 20%
    # 1 - 01 - 50%
    # 2 - 10 - 67%
    # 3 - 11 - bypassed
    def setIntZ(self, intZ: int):
        self.zero = intZ
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_REFCN_REG)
        data &= ~(3 << 5)  # 清除第5和第6位
        data |= (intZ << 5)  # 設置 intZ 值到第5和第6位
        self.bus.write_byte_data(self.i2c_address, LMP91000_REFCN_REG, data)

    def getIntZ(self) -> float:
        return TIA_ZERO[self.zero]
    

    def setBiasSign(self, sign: int):
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_REFCN_REG)
        if sign == 0:
            data &= ~(1 << 4)  # 清除第4位，設置為負偏壓
        else:
            data |= (1 << 4)  # 設置第4位，設置為正偏壓
        self.bus.write_byte_data(self.i2c_address, LMP91000_REFCN_REG, data)
    def setBias(self, bias: int):
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_REFCN_REG)
        data &= ~(0x0F)  # 清除前4位
        data |= bias  # 設置偏壓值
        self.bus.write_byte_data(self.i2c_address, LMP91000_REFCN_REG, data)
    # 0 is negative and 1 is positive
    def setBiasWithSign(self, bias: int, sign: int):
        sign = 1 if sign > 0 else 0
        bias = bias if bias <= 13 else 0

        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_REFCN_REG)
        data &= ~(0x1F)  # 清除前5位
        data |= bias  # 設置偏壓值
        data |= (sign << 4)  # 設置偏壓的符號位
        self.bus.write_byte_data(self.i2c_address, LMP91000_REFCN_REG, data)

    def setFET(self, selection: int):
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_MODECN_REG)
        
        if selection == 0:
            data &= ~(1 << 7)  # 清除第7位以禁用 FET
        else:
            data |= (1 << 7)   # 設置第7位以啟用 FET
        
        self.bus.write_byte_data(self.i2c_address, LMP91000_MODECN_REG, data)
        self.lock()


    # (mode == 2) standby();
    # (mode == 3) setThreeLead();
    # (mode == 1) setTwoLead();
    # (mode == 4) measureCell();
    # (mode == 5) getTemp();
    def setMode(self, mode: int):
        self.unlock()
        data = self.bus.read_byte_data(self.i2c_address, LMP91000_MODECN_REG)
        data &= ~(0x07)
        if mode == 0:
            # 000
            pass
        elif mode == 1:
            # 001
            data |= (0x01)
        elif mode == 2:
            # 010
            data |= (0x02)
        elif mode == 3:
            # 011
            data |= (0x03)
        elif mode == 4:
            # 110
            data |= (0x06)
        elif mode == 5:
            # 100
            data |= (0x07)
        else:
            pass

        self.bus.write_byte_data(self.i2c_address, self.LMP91000_MODECN_REG, data)
        self.lock()

    # # sets and gets MENB pin for enabling and disabling I2C commands
    # setMENB = None
    # getMENB = None
    # setTempSensor = None
    # getTempSensor = None
    # write = None
    # read = None
    # # enables and disables LMP91000 for I2C commands
    # # default state is not ready
    # enable = None
    # disable = None
    # isReady = None
    # # locks and unlocks the transimpedance amplifier
    # # and reference control registers for editing
    # # default state is locked (read-only)
    # lock = None
    # unlock = None
    # isLocked = None
    # # sets the gain of the transimpedance amplifier
    # setGain = None
    # getGain = None
    # # sets the load for compensating voltage differences
    # setRLoad = None
    # # sets the source for the bias voltage
    # setRefSource = None
    # setIntRefSource = None
    # setExtRefSource = None
    # # sets reference voltage for transimpedance amplifier
    # setIntZ = None
    # getIntZ = None
    # # sets bias voltage for electrochemical cell
    # setBiasSign = None
    # setNegBias = None
    # setPosBias = None
    # setBias = None
    # setBiasWithSign = None
    # # enable and disable FET for deep sleep mode
    # setFET = None
    # disableFET = None
    # enableFET = None
    # # set operating modes for the LMP91000
    # setMode = None
    # sleep = None
    # setTwoLead = None
    # standby = None
    # setThreeLead = None
    # measureCell = None
    # # temperature and output methods
    # getTemp = None
    # getTempWithParams = None
    # getOutput = None
    # getVoltage = None
    # getCurrent = None
    # getCurrentWithExtGain = None