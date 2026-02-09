# Raspberry Pi Pico (RP2040) + Sensirion SCD41 (SCD4x family) over I2C
# Wiring (per your note):
#   Pico 5V   -> module VCC (module accepts 2.4–5.5V)
#   Pico GND  -> module GND
#   Pico GP2  -> SDA
#   Pico GP3  -> SCL
#
# Notes:
# - SCD4x I2C address is 0x62. [file:1]
# - Periodic measurement update interval is 5 seconds. [file:1]
# - Data words are followed by 8-bit CRC (poly 0x31, init 0xFF). [file:1]

from machine import Pin, I2C
import time

SCD4X_ADDR = 0x62

# Commands (16-bit)
CMD_START_PERIODIC_MEAS = 0x21B1
CMD_STOP_PERIODIC_MEAS  = 0x3F86
CMD_GET_DATA_READY      = 0xE4B8
CMD_READ_MEASUREMENT    = 0xEC05

# ---------- CRC8 (Sensirion) ----------
def crc8_sensirion(two_bytes: bytes) -> int:
    crc = 0xFF
    poly = 0x31
    for b in two_bytes:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) & 0xFF) ^ poly
            else:
                crc = (crc << 1) & 0xFF
    return crc

def check_crc(word_bytes: bytes, crc_byte: int) -> bool:
    return crc8_sensirion(word_bytes) == crc_byte

# ---------- Low-level I2C helpers ----------
def write_command(i2c: I2C, cmd: int):
    # Commands are 16-bit, MSB first; command words are not followed by CRC. [file:1]
    buf = bytes([(cmd >> 8) & 0xFF, cmd & 0xFF])
    i2c.writeto(SCD4X_ADDR, buf)

def read_words_with_crc(i2c: I2C, num_words: int) -> list[int]:
    # Each word is 2 bytes + 1 CRC byte. [file:1]
    raw = i2c.readfrom(SCD4X_ADDR, num_words * 3)
    words = []
    for i in range(num_words):
        msb = raw[i*3 + 0]
        lsb = raw[i*3 + 1]
        crc = raw[i*3 + 2]
        wb = bytes([msb, lsb])
        if not check_crc(wb, crc):
            raise ValueError("CRC mismatch on word {}".format(i))
        words.append((msb << 8) | lsb)
    return words

# ---------- SCD4x high-level functions ----------
def scd4x_start_periodic(i2c: I2C):
    write_command(i2c, CMD_START_PERIODIC_MEAS)  # update interval 5s [file:1]

def scd4x_stop_periodic(i2c: I2C):
    write_command(i2c, CMD_STOP_PERIODIC_MEAS)
    time.sleep_ms(500)  # sensor only responds after 500ms [file:1]

def scd4x_data_ready(i2c: I2C) -> bool:
    write_command(i2c, CMD_GET_DATA_READY)
    time.sleep_ms(1)  # execution time 1ms [file:1]
    status = read_words_with_crc(i2c, 1)[0]
    # If least significant 11 bits are 0 => not ready, else ready. [file:1]
    return (status & 0x07FF) != 0

def scd4x_read_measurement(i2c: I2C):
    # read_measurement returns 3 words: CO2, T, RH. [file:1]
    write_command(i2c, CMD_READ_MEASUREMENT)
    time.sleep_ms(1)  # execution time 1ms [file:1]
    co2, t_raw, rh_raw = read_words_with_crc(i2c, 3)

    # Conversions from datasheet: [file:1]
    #   T[°C]  = -45 + 175 * word[1] / (2^16 - 1)
    #   RH[%]  = 100 * word[2] / (2^16 - 1)
    temp_c = -45.0 + 175.0 * (t_raw / 65535.0)
    rh = 100.0 * (rh_raw / 65535.0)
    return co2, temp_c, rh

# ---------- Main ----------
i2c = I2C(
    1,
    scl=Pin(3),
    sda=Pin(2),
    freq=100_000  # SCD4x supports I2C standard-mode up to 100kHz. [file:1]
)

# Give sensor time to power up into idle (up to 1000ms). [file:1]
time.sleep_ms(1100)

print("Starting SCD41 periodic measurement...")
scd4x_start_periodic(i2c)

# First valid reading typically comes after the first update interval (~5s). [file:1]
try:
    while True:
        # Poll data-ready to avoid NACKs on read. [file:1]
        if scd4x_data_ready(i2c):
            co2, temp_c, rh = scd4x_read_measurement(i2c)
            print("CO2: {:5d} ppm | T: {:6.2f} C | RH: {:6.2f} %".format(co2, temp_c, rh))
        time.sleep_ms(500)
except KeyboardInterrupt:
    pass
finally:
    print("Stopping periodic measurement...")
    scd4x_stop_periodic(i2c)

