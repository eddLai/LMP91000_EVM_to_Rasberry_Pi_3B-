import ADC161S626
import LMP91000
import time

class LMP91000_EVM:
    def __init__(self, sda, scl, mosi, miso, sclk, cs, menb, sdrdy, led_debug) -> None:
        if sda == 2 & scl == 3: bus_num = 1 
        else: print("U should use I2C.1")
        self.potentialStat = LMP91000(bus_num, menb) #include set BCM mode
        self.adc = ADC161S626(cs, mosi, miso, sclk, adc_ref=3.3)

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
        voltage_zero = ADC161S626.vref * LMP91000.TIA_ZERO[self.zero]
        if isExtGain != 0:
            current = (voltage - voltage_zero) / isExtGain
        else:
            current = (voltage - voltage_zero) / LMP91000.TIA_GAIN[self.gain]
        return current
    
