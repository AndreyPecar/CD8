"""
═══════════════════════════════════════════════════════════════
    TRANSMISOR (TX) con Sistema de Contraseña/Emparejamiento
═══════════════════════════════════════════════════════════════
"""
# TX: Pico + nRF24L01 (SPI0) + OLED (I2C0) + Joystick
from machine import Pin, SPI, I2C, ADC
from ssd1306 import SSD1306_I2C
from nrf24l01 import NRF24L01
import utime, struct

# --- OLED (I2C0 GP9/GP8) ---
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
utime.sleep_ms(300)
oled = SSD1306_I2C(128, 64, i2c)

# --- nRF24L01 (SPI0 GP6/7/4; CE=14, CSN=15) ---
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
ce  = Pin(14, Pin.OUT, value=0)
csn = Pin(15, Pin.OUT, value=1)

PIPE_TX = b'\xe1\xf0\xf0\xf0\xf0'   # a quién envío
PIPE_RX = b'\xd2\xf0\xf0\xf0\xf0'   # pipe para respuestas (no usado)

nrf = NRF24L01(spi, csn, ce, channel=76, payload_size=32)
# Potencia/velocidad: soporta versiones de librería distintas
try:
    nrf.set_power_speed(NRF24L01.PA_MAX, NRF24L01.SPEED_1MBPS)
except:
    try: nrf.set_power_speed(3, 0)   # 3=PA_MAX, 0=1Mbps
    except: pass
try: nrf.set_retries(5, 15)
except: pass

nrf.open_tx_pipe(PIPE_TX)
nrf.open_rx_pipe(1, PIPE_RX)
nrf.stop_listening()

# --- Joystick ---
vrx = ADC(26)  # 0..65535
vry = ADC(27)

cnt = 0

def read_joy_8bit():
    x = vrx.read_u16() // 256  # 0..255
    y = vry.read_u16() // 256
    return x, y

def draw_tx(cnt, x, y, ok=True):
    oled.fill(0)
    oled.text("TX NRF24L01", 8, 0)
    oled.text("CNT: {:5d}".format(cnt), 0, 18)
    oled.text("X:{:3d}".format(x), 0, 36)
    oled.text("Y:{:3d}".format(y), 64, 36)
    oled.text("ENVIADO" if ok else "FALLO TX", 0, 54)
    oled.show()

while True:
    x, y = read_joy_8bit()
    payload = struct.pack('<HBB', cnt & 0xFFFF, x, y)  # 4 bytes + relleno si quisieras
    ok = True
    try:
        nrf.send(payload)
        print("TX → cnt:", cnt, "X:", x, "Y:", y)
    except Exception as e:
        ok = False
        print("send failed:", e)
    draw_tx(cnt, x, y, ok)
    cnt = (cnt + 1) & 0xFFFF
    utime.sleep_ms(150)