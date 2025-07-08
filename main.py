from machine import Pin, PWM
import ubluetooth
import struct

class BLEPeripheral:
    def __init__(self, name="PicoW-BLE"):
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.bt_irq)
        self.name = name

        # PWM on GPIO6 and GPIO12
        self.pwm6 = PWM(Pin(6))
        self.pwm12 = PWM(Pin(12))
        self.pwm6.freq(1000)
        self.pwm12.freq(1000)

        # GPIOs 18–21
        self.gpios = [Pin(n, Pin.OUT) for n in (18, 19, 20, 21)]

        # Variable A/B/0
        self.var = b"0"

        # UUIDs (random example UUIDs, you may want to generate new ones!)
        SERVICE_UUID = ubluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
        PWM6_UUID = ubluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
        PWM12_UUID = ubluetooth.UUID("12345678-1234-5678-1234-56789abcdef2")
        GPIO_UUID = ubluetooth.UUID("12345678-1234-5678-1234-56789abcdef3")
        VAR_UUID = ubluetooth.UUID("12345678-1234-5678-1234-56789abcdef4")

        self.pwm6_handle = None
        self.pwm12_handle = None
        self.gpio_handle = None
        self.var_handle = None

        self.service = (
            SERVICE_UUID,
            (
                (PWM6_UUID, ubluetooth.FLAG_WRITE | ubluetooth.FLAG_READ),
                (PWM12_UUID, ubluetooth.FLAG_WRITE | ubluetooth.FLAG_READ),
                (GPIO_UUID, ubluetooth.FLAG_WRITE | ubluetooth.FLAG_READ),
                (VAR_UUID, ubluetooth.FLAG_WRITE | ubluetooth.FLAG_READ),
            ),
        )

        ((self.pwm6_handle, self.pwm12_handle, self.gpio_handle, self.var_handle),) = self.ble.gatts_register_services((self.service,))
        self.ble.gap_advertise(100_000, adv_data=self._advertise_payload(self.name))
        
        # Initialize default values
        self.ble.gatts_write(self.pwm6_handle, struct.pack("<H", 0))
        self.ble.gatts_write(self.pwm12_handle, struct.pack("<H", 0))
        self.ble.gatts_write(self.gpio_handle, bytes([0, 0, 0, 0]))  # All low
        self.ble.gatts_write(self.var_handle, b"0")

    def bt_irq(self, event, data):
        if event == 3: # WRITE
            conn_handle, attr_handle = data
            if attr_handle == self.pwm6_handle:
                pwm_val = struct.unpack("<H", self.ble.gatts_read(self.pwm6_handle))[0]
                self.pwm6.duty_u16(pwm_val)
            elif attr_handle == self.pwm12_handle:
                pwm_val = struct.unpack("<H", self.ble.gatts_read(self.pwm12_handle))[0]
                self.pwm12.duty_u16(pwm_val)
            elif attr_handle == self.gpio_handle:
                vals = self.ble.gatts_read(self.gpio_handle)
                for i, val in enumerate(vals[:4]):
                    self.gpios[i].value(val)
            elif attr_handle == self.var_handle:
                val = self.ble.gatts_read(self.var_handle)
                if val in [b"A", b"B", b"0"]:
                    self.var = val

    def _advertise_payload(self, name):
        # Simple advertising payload: name only
        payload = bytearray()
        payload += bytes((len(name) + 1, 0x09)) + name.encode()
        return payload

def main():
    ble_device = BLEPeripheral("PicoW-BLE")
    print("BLE device running. Waiting for connections...")

if __name__ == "__main__":
    main()
