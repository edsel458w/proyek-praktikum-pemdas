import time
import board
import busio
import requests
import RPi.GPIO as GPIO
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

# ================= CONFIG BACKEND =================
BACKEND_URL = "http://10.25.217.110:5000/api/kirim"

# ================= PIN CONFIGURATION =================
FAN_PIN = 26
SERVO_PIN = 17
IR_SENSOR_PIN = 27

# ================= GPIO SETUP =================
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.setup(IR_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(FAN_PIN, GPIO.LOW)

GPIO.setup(SERVO_PIN, GPIO.OUT)
servo_pwm = GPIO.PWM(SERVO_PIN, 50)
servo_pwm.start(0)

# ================= SERVO FUNCTION =================
def set_servo_angle(angle):
    duty = 2.5 + (angle / 180.0) * 10
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)
    time.sleep(0.1)

# ================= SEND DATA TO BACKEND =================
def kirim_ke_backend(jenis):
    try:
        payload = {"value": jenis}
        response = requests.post(BACKEND_URL, json=payload, timeout=3)
        print(f"[API] Kirim {payload} | Status: {response.status_code}")
    except Exception as e:
        print(f"[API ERROR] {e}")

# ================= I2C & ADS1115 =================
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
soil_channel = AnalogIn(ads, 1)

# ================= STATUS VARIABLES =================
servo_position = 45
last_ir_state = GPIO.HIGH
jenis_sampah = ""

# ================= INFO =================
print("="*60)
print(" SISTEM TEMPAT SAMPAH PINTAR OTOMATIS ")
print("="*60)
print("IR  : GPIO 27")
print("Servo: GPIO 17")
print("Fan  : GPIO 26")
print("Moisture: ADS1115 A1")
print("="*60)
print("Tekan Ctrl+C untuk keluar\n")

try:
    set_servo_angle(45)

    while True:
        # ===== BACA IR SENSOR =====
        ir_state = GPIO.input(IR_SENSOR_PIN)

        # ===== BACA MOISTURE =====
        raw_value = soil_channel.value
        moisture_percent = 100 - ((raw_value - 10000) / (30000 - 10000) * 100)
        moisture_percent = max(0, min(100, moisture_percent))

        # ===== KONTROL FAN =====
        if moisture_percent > 70 and ir_state == GPIO.LOW:
            GPIO.output(FAN_PIN, GPIO.HIGH)
            fan_status = "ON"
        else:
            GPIO.output(FAN_PIN, GPIO.LOW)
            fan_status = "OFF"

        # ===== DETEKSI SAMPAH =====
        if ir_state == GPIO.LOW and last_ir_state == GPIO.HIGH:

            if moisture_percent > 70:
                # ===== ORGANIK =====
                jenis_sampah = "organik"
                print("\n[!] SAMPAH ORGANIK TERDETEKSI")
                set_servo_angle(90)
                servo_position = 90
                kirim_ke_backend("organik")

            else:
                # ===== ANORGANIK =====
                jenis_sampah = "anorganik"
                print("\n[!] SAMPAH ANORGANIK TERDETEKSI")
                set_servo_angle(0)
                servo_position = 0
                kirim_ke_backend("anorganik")

        elif ir_state == GPIO.HIGH and last_ir_state == GPIO.LOW:
            print(f"[OK] Sampah {jenis_sampah} masuk, menutup...")
            time.sleep(1)
            set_servo_angle(45)
            servo_position = 45
            jenis_sampah = ""

        last_ir_state = ir_state

        # ===== STATUS =====
        print(
            f"Moisture: {moisture_percent:5.1f}% | "
            f"Fan: {fan_status:3s} | "
            f"Servo: {servo_position:3d}"
            f"IR: {'DETECT' if ir_state == GPIO.LOW else 'CLEAR'}"
        )

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nProgram dihentikan")

finally:
    GPIO.output(FAN_PIN, GPIO.LOW)
    set_servo_angle(45)
    servo_pwm.stop()
    GPIO.cleanup()
    print("GPIO dibersihkan. Program selesai.")

