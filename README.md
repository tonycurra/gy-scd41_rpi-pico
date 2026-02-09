# gy-scd41_rpi-pico
Micropython repo for sensor gy-scd41 readings on serial monitor and raspberry pi pico 



# pico-micropython-scd4x

MicroPython driver + examples for the Sensirion SCD4x family (tested with **SCD41**) on the **Raspberry Pi Pico / RP2040** via I2C.

This reads:
- CO2 (ppm)
- Temperature (°C)
- Relative Humidity (%RH)

The SCD4x uses I2C address **0x62** and returns 16-bit measurement words with an 8-bit CRC after each word (CRC-8 polynomial **0x31**, init **0xFF**) as described in the datasheet.  
Periodic measurement is started with command **0x21B1**, data-ready status with **0xE4B8**, and measurements are read with **0xEC05**. [web:29]

## Hardware
- Raspberry Pi Pico / Pico W (RP2040)
- GY-SCD41 module (or bare SCD41/SCD40)
- USB cable
- Wiring (your setup):
  - Pico **VBUS/5V** -> SCD41 **VCC**
  - Pico **GND** -> SCD41 **GND**
  - Pico **GP2 (SDA)** -> SCD41 **SDA**
  - Pico **GP3 (SCL)** -> SCD41 **SCL**

Note: Many GY modules include I2C pull-ups (often 10k). The SCD4x supports I2C standard mode up to 100 kHz. [web:29]

## Software setup (Thonny)
1. Install Thonny.
2. Plug in the Pico.
3. In Thonny: **Run → Select interpreter → MicroPython (Raspberry Pi Pico)**.
4. Copy files to the Pico:
   - `src/scd4x.py`
   - `src/example_periodic.py`

## Running the example
### Option A: Run manually
Open `example_periodic.py` in Thonny and click **Run**.

### Option B: Run on boot
Save the example onto the Pico as `main.py`. MicroPython runs `main.py` at boot (after `boot.py` if present). [web:21]

## Example output
CO2: 612 ppm | T: 23.61 C | RH: 41.20%
CO2: 605 ppm | T: 23.60 C | RH: 41.10%
...

## How it works (quick overview)
- Start periodic measurements (`0x21B1`), which updates every ~5 seconds. [web:29]
- Poll data-ready (`0xE4B8`) to avoid NACK when no new sample is available. [web:29]
- Read measurement (`0xEC05`) which returns 3 words: CO2, temperature, humidity. [web:29]
- Convert raw values:
  - `T(°C) = -45 + 175 * raw / 65535`
  - `RH(%) = 100 * raw / 65535`  [web:29]

## License
MIT

## References
- Sensirion SCD4x Datasheet (commands, CRC, conversions). [web:29]
- https://github.com/Sensirion/arduino-i2c-scd4x
- https://www.tinytronics.nl/en/sensors/air/humidity/gy-scd41-module-co2-humidity-temperature-sensor-i2c
