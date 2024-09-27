import spidev
import RPi.GPIO as GPIO

ADC_BIT = 16

class ADC161S626:
    def __init__(self, cs_pin, mosi_pin, miso_pin, sclk_pin, adc_vref):
        # Initialize SPI and GPIO pins
        self.cs_pin = cs_pin
        self.mosi_pin = mosi_pin
        self.miso_pin = miso_pin
        self.sclk_pin = sclk_pin
        self.vref = adc_vref

        # Setup GPIO mode and pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.mosi_pin, GPIO.OUT)
        GPIO.setup(self.miso_pin, GPIO.IN)
        GPIO.setup(self.sclk_pin, GPIO.OUT)
        GPIO.setup(self.cs_pin, GPIO.OUT)

        # Initialize SPI interface
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # Use SPI bus 0, chip select 0
        self.spi.max_speed_hz = 5000000  # Set max SPI speed
        self.spi.mode = 0b00  # Set SPI mode

        # ADC161S626 specifications
        self.sclk_frequency_min = 1e6  # 1 MHz
        self.sclk_frequency_max = 5e6  # 5 MHz
        self.cs_setup_time_min = 8e-9  # 8 ns
        self.sclk_high_low_time_min = 20e-9  # 20 ns
        self.dout_access_time_min = 18e-9  # 18 ns
        self.dout_access_time_max = 41e-9  # 41 ns
        self.dout_hold_time_min = 6e-9  # 6 ns
        self.dout_hold_time_max = 11e-9  # 11 ns
        self.sclk_cycles_per_conversion = 18  # 18 SCLK cycles required per conversion

    def __repr__(self):
        return (f"ADC161S626(CS={self.cs_pin}, SCLK={self.sclk_pin}, DOUT={self.miso_pin})")

    def read_adc(self):
        # Start ADC read process
        GPIO.output(self.cs_pin, GPIO.LOW)  # Select ADC by pulling CS low

        # Read two bytes of data from the ADC
        adc_response = self.spi.xfer2([0x00, 0x00])
        result = (adc_response[0] << 8) | adc_response[1]  # Combine the two bytes

        GPIO.output(self.cs_pin, GPIO.HIGH)  # Deselect ADC by pulling CS high

        # Handle two's complement result
        if result & 0x8000:  # Check if the result is negative (bit 15 is set)
            result -= 65536  # Convert from two's complement

        return result

    def get_Volt(self):
        adc_value = self.read_adc()

        # Calculate the corresponding voltage using VREF and 16-bit resolution
        voltage = (adc_value / 65536) * (2 * self.vref)

        return voltage

    def validate_sclk_frequency(self, frequency):
        # Check if the SCLK frequency is within valid range
        return self.sclk_frequency_min <= frequency <= self.sclk_frequency_max

    def validate_cs_setup_time(self, cs_time):
        # Check if the CS setup time meets the minimum requirement
        return cs_time >= self.cs_setup_time_min

    def validate_sclk_high_low_time(self, sclk_time):
        # Check if the SCLK high/low time meets the minimum requirement
        return sclk_time >= self.sclk_high_low_time_min

    def validate_dout_access_time(self, dout_time):
        # Check if the DOUT access time is within the valid range
        return self.dout_access_time_min <= dout_time <= self.dout_access_time_max

    def validate_dout_hold_time(self, dout_time):
        # Check if the DOUT hold time is within the valid range
        return self.dout_hold_time_min <= dout_time <= self.dout_hold_time_max
