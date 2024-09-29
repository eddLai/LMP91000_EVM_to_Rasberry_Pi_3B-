from LMP91000_EVM import LMP91000_EVM
from LMP91000 import TIA_BIAS, NUM_TIA_BIAS
import time
import math

# Define constants
opVolt = 3300  # milliVolts
resolution = 16  # bits
step = 0  # Global step counter

# Unit: mV, ms
SDA = 2  # SDA.1
SCL = 3  # SCL.1  
# GND12 4|17 
# GPSI3_3 22|10
MOSI_PIN = 10
MISO_PIN = 9
SCLK_PIN = 11  # SCLK
# GND2
CS_PIN = 10  # CE0
MENB_INT = 6
SDRDY = 26
LED = 18  # GPIO1

lmp91000_evm = LMP91000_EVM(SDA, SCL, MOSI_PIN, MISO_PIN, SCLK_PIN, CS_PIN, MENB_INT, SDRDY, LED)

def determineLMP91000Bias(voltage):
    polarity = -1 if voltage < 0 else 1
    voltage = abs(voltage)
    if voltage == 0:
        return 0
    for i in range(NUM_TIA_BIAS - 1):
        v1 = opVolt * TIA_BIAS[i]
        v2 = opVolt * TIA_BIAS[i + 1]
        if voltage == v1:
            return polarity * i
        elif v1 < voltage < v2:
            return polarity * (i if abs(voltage - v1) < abs(voltage - v2) else i + 1)
    return 0

def runAmp(user_gain, pre_stepV, quietTime, v1, t1, v2, t2, samples, range):
    lmp91000_evm.potentialStat.disableFET()
    lmp91000_evm.potentialStat.setGain(user_gain)
    lmp91000_evm.potentialStat.setRLoad(0)
    lmp91000_evm.potentialStat.setIntRefSource()
    lmp91000_evm.potentialStat.setIntZ(1)
    lmp91000_evm.potentialStat.setMode(3)  # Set to three-lead mode
    lmp91000_evm.potentialStat.setBias(0)

    # Print column headers
    current_units = {
        12: "Current(pA)",
        9: "Current(nA)",
        6: "Current(uA)",
        3: "Current(mA)"
    }
    current_count = current_units.get(range, "SOME ERROR")
    print("Voltage(mV),Time(ms),{}".format(current_count))

    voltageArray = [pre_stepV, v1, v2]
    timeArray = [quietTime, t1, t2]

    global step
    step = 0

    for i in range(3):
        fs = timeArray[i] / samples  # Time per sample in ms
        bias_index = determineLMP91000Bias(voltageArray[i])

        # Set bias sign
        lmp91000_evm.potentialStat.setBiasSign(0 if bias_index < 0 else 1)
        lmp91000_evm.potentialStat.setBias(abs(bias_index))

        startTime = time.time()
        while (time.time() - startTime) * 1000 < timeArray[i]:
            sign = bias_index / abs(bias_index) if bias_index != 0 else 0
            computedValue = int(opVolt * TIA_BIAS[abs(bias_index)] * sign)
            timestamp = int((time.time() - startTime) * 1000)
            vout = lmp91000_evm.getVolt()
            current = math.pow(10, range) * lmp91000_evm.get_current()
            print("{}, {}, {:.2f}, {:.6f}, {}".format(step, computedValue, vout * 1000, current, timestamp))
            time.sleep(fs / 1000.0)
            step += 1

    # End at 0V
    lmp91000_evm.potentialStat.setBias(0)

# Parameters
v0 = 0    # milliVolts
v1 = 800  # milliVolts
v2 = 0    # milliVolts

# Run the amperometric measurement
runAmp(2, v0, 100, v1, 5000, v2, 5000, 300, 6)