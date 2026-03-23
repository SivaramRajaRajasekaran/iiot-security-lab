import time
import json
import random
import paho.mqtt.client as mqtt

# we define all 3 machines here
# Each machine has its own id, topic, and realistic ON/OFF ratio
# on_probability = how likely the machine is ON each cycle
MACHINES = [
    {
        "id": "machine1",
        "topic": "factory/machine1/data",
        "on_probability": 0.80  # 80% ON, 20% OFF
    },
    {
        "id": "machine2",
        "topic": "factory/machine2/data",
        "on_probability": 0.82  # 82% ON, 18% OFF
    },
    {
        "id": "machine3",
        "topic": "factory/machine3/data",
        "on_probability": 0.86  # 86% ON, 14% OFF
    },
    {
        "id": "machine4",
        "topic": "factory/machine4/data",
        "on_probability": 0.85  # 85% ON, 15% OFF
    }
]
# We track production count separately per machine
# so each machine has its own independent counter
production_counts = {
    "machine1": 0,
    "machine2": 0,
    "machine3": 0,
    "machine4": 0
}

broker = "mosquitto"
port = 1883

client = mqtt.Client()
client.connect(broker, port, 60)

print("Simulator started — sending data for 4 machines...")

while True:
    for machine in MACHINES:
        mid = machine["id"]

        # random.random(): generates a number between 0 and 1
        # if it's less than on_probability, machine is ON
        # e.g. 0.80 means 80% of the time the random number
        # will be below 0.80, so status = ON
        status = "ON" if random.random() < machine["on_probability"] else "OFF"

        if status == "ON":
            # WHY different ranges per machine:
            # makes each machine tell a different story in Grafana
            if mid == "machine1":
                temperature = round(random.uniform(45, 75), 2)
                production_counts[mid] += random.randint(1, 5)
            elif mid == "machine2":
                temperature = round(random.uniform(50, 80), 2)
                production_counts[mid] += random.randint(1, 4)
            elif mid == "machine3":                
                temperature = round(random.uniform(40, 70), 2)
                production_counts[mid] += random.randint(1, 6)
            elif mid == "machine4":
                temperature = round(random.uniform(42, 72), 2)
                production_counts[mid] += random.randint(1, 5)
            else:
                temperature = round(random.uniform(40, 70), 2)
                production_counts[mid] += random.randint(1, 6)
        else:
            # Machine OFF = lower idle temperature
            temperature = round(random.uniform(30, 40), 2)

        data = {
            "machine_id": mid,
            "status": status,
            "temperature": temperature,
            "production_count": production_counts[mid],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        payload = json.dumps(data)
        client.publish(machine["topic"], payload)
        print(f"Sent [{mid}]: {payload}")

    # WHY 3 seconds: matches our Node-RED interval calculation
    # all 3 machines send once every 3 seconds
    time.sleep(3)