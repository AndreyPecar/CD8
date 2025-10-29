"""
═══════════════════════════════════════════════════════════════
    RECEPTOR (RX) con Sistema de Contraseña/Emparejamiento
═══════════════════════════════════════════════════════════════
"""
# RX: Pico + nRF24L01 (SPI0) + OLED (I2C0) + Servo (GP16)
from machine import Pin, SPI, I2C, PWM
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

PIPE_RX = b'\xe1\xf0\xf0\xf0\xf0'   # lo que TX usa para enviar
PIPE_TX = b'\xd2\xf0\xf0\xf0\xf0'   # reservada (no usada)

nrf = NRF24L01(spi, csn, ce, channel=76, payload_size=32)
try:
    nrf.set_power_speed(NRF24L01.PA_MAX, NRF24L01.SPEED_1MBPS)
except:
    try: nrf.set_power_speed(3, 0)
    except: pass
try: nrf.set_retries(5, 15)
except: pass

nrf.open_rx_pipe(1, PIPE_RX)
nrf.open_tx_pipe(PIPE_TX)
nrf.start_listening()

# --- Servo en GP16 ---
servo = PWM(Pin(16))
servo.freq(50)  # 50 Hz típico

# Mover por pulsos en microsegundos para precisión
def servo_write_us(us):
    # duty_u16 = us / periodo * 65535 ; periodo = 1/f = 20_000 us
    duty = int(us * 65535 * servo.freq() / 1_000_000)
    servo.duty_u16(duty)

def mover_servo_angulo(ang):
    ang = max(0, min(180, int(ang)))
    us = 500 + (ang/180) * (2500 - 500)  # 0°≈500us, 180°≈2500us
    servo_write_us(int(us))

def map_x_to_angle(x):  # x: 0..255 -> 0..180
    return int((x / 255) * 180)

def draw_rx(cnt, x, y, ang):
    oled.fill(0)
    oled.text("RX NRF24L01", 10, 0)
    oled.text("CNT: {:5d}".format(cnt), 0, 18)
    oled.text("X:{:3d} Y:{:3d}".format(x, y), 0, 34)
    oled.text("SERVO:{:3d} deg".format(ang), 0, 50)
    oled.show()

# Pantalla inicial
oled.fill(0); oled.text("Esperando datos...", 0, 24); oled.show()

while True:
    if nrf.any():
        data = nrf.recv()
        if len(data) >= 4:
            cnt, x, y = struct.unpack('<HBB', data[:4])
            ang = map_x_to_angle(x)
            mover_servo_angulo(ang)
            print("RX ← cnt:", cnt, "X:", x, "Y:", y, "ANG:", ang)
            draw_rx(cnt, x, y, ang)
        else:
            print("Paquete corto:", data)
    utime.sleep_ms(30)