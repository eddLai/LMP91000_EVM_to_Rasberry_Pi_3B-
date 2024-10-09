from ADC161S626 import ADC161S626
from LMP91000 import LMP91000, TIA_BIAS, NUM_TIA_BIAS, TIA_ZERO, TIA_GAIN
import time

class LMP91000_EVM:
    def __init__(self, sda, scl, mosi, miso, sclk, cs, menb, sdrdy, led_debug) -> None:
        bus_num = None
        if sda == 2 and scl == 3: bus_num = 1 
        else: print("U should use I2C.1")
        self.potentialStat = LMP91000(bus_num, menb) #include set BCM mode
        self.adc = ADC161S626(cs, mosi, miso, sclk, adc_vref=3.3)

    def getVolt(self):
        return self.adc.get_Volt()
    
    def get_temp(self):
        self.potentialStat.setMode(5)
        time.sleep(0.1)  # Wait for the sensor to stabilize 
        # Read ADC value
        voltage = self.adc.get_Volt()
        # Calculate temperature
        temperature = (voltage - LMP91000.TEMP_INTERCEPT) / LMP91000.TEMPSLOPE
        return temperature
    
    def get_current(self, isExtGain=0):
        voltage = self.getVolt()
        voltage_zero = self.adc.vref * TIA_ZERO[self.potentialStat.zero]
        if isExtGain != 0:
            current = (voltage - voltage_zero) / isExtGain
        else:
            current = (voltage - voltage_zero) / TIA_GAIN[self.potentialStat.gain]
        return current
    
