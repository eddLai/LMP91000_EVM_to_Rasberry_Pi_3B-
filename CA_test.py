import RPi.GPIO as GPIO
import time
import LMP91000_EVM
import LMP91000

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

def run_ca(bias_voltage_mv, total_time_ms, sample_interval_ms, tia_gain, tia_zero, current_range):
    """
    Perform constant potential coulometry (CA) measurement.

    :param bias_voltage_mv: Bias voltage in millivolts (mV)
    :param total_time_ms: Total measurement time in milliseconds (ms)
    :param sample_interval_ms: Sampling interval in milliseconds (ms)
    :param tia_gain: TIA gain setting (based on LMP91000 configuration)
    :param tia_zero: TIA zero setting (based on LMP91000 configuration)
    :param current_range: Current range indicator (e.g., 12 for pA, 9 for nA, etc.)
    """
    # Configure LMP91000
    lmp91000_evm.potentialStat.setTIAGain(tia_gain)
    lmp91000_evm.potentialStat.setTIAZero(tia_zero)
    lmp91000_evm.potentialStat.setBias(bias_voltage_mv)
    lmp91000_evm.potentialStat.setMode(LMP91000.MODE_AMPEROMETRIC)
    
    # Wait for the device to stabilize
    time.sleep(0.1)
    
    # Initialize data storage
    times = []
    currents = []
    current_unit = {
        12: "pA",
        9: "nA",
        6: "μA",
        3: "mA"
    }.get(current_range, "Unknown Unit")
    
    print(f"Starting constant potential coulometry measurement, bias: {bias_voltage_mv} mV, total time: {total_time_ms} ms, sample interval: {sample_interval_ms} ms")
    print(f"Time(ms), Current({current_unit})")
    
    start_time = time.time()
    elapsed_time_ms = 0

    while elapsed_time_ms < total_time_ms:
        # Read voltage and calculate current
        voltage = lmp91000_evm.getVolt()
        raw_current = lmp91000_evm.get_current()
        # Adjust unit based on current range
        adjusted_current = raw_current * (10 ** current_range)
        
        # Get current time
        elapsed_time_ms = (time.time() - start_time) * 1000  # Convert to milliseconds
        times.append(elapsed_time_ms)
        currents.append(adjusted_current)
        
        # Output data
        print(f"{elapsed_time_ms:.2f}, {adjusted_current}")
        
        # Wait for the next sample
        time.sleep(sample_interval_ms / 1000.0)
    
    # After measurement, set LMP91000 mode to standby
    lmp91000_evm.potentialStat.setMode(LMP91000.MODE_STANDBY)
    
    # Return data for further processing or saving
    return times, currents

def main():
    # Example parameters
    bias_voltage_mv = 500  # Bias voltage in mV
    total_time_ms = 60000  # Total measurement time in ms (e.g., 60 seconds)
    sample_interval_ms = 1000  # Sampling interval in ms (e.g., sample once per second)
    tia_gain = LMP91000.TIA_GAIN_EXT  # Use external TIA gain (replace based on your configuration)
    tia_zero = LMP91000.TIA_ZERO_50  # TIA zero setting (replace based on your configuration)
    current_range = 6  # Current range (6 indicates μA)

    # Run constant potential coulometry measurement
    times, currents = run_ca(bias_voltage_mv, total_time_ms, sample_interval_ms, tia_gain, tia_zero, current_range)
    
    # Optionally, save the data to a CSV file
    with open('ca_data.csv', 'w') as f:
        f.write('Time(ms),Current\n')
        for t, i in zip(times, currents):
            f.write(f"{t},{i}\n")
    print("Measurement completed, data saved to ca_data.csv")

if __name__ == "__main__":
    main()
