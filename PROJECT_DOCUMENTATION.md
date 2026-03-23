# Project Documentation
## Industry 4.0 Machine Monitoring System

---

# Die deutsche Version finden Sie weiter unten.
# The German version can be found below.

---

## 🇬🇧 English

### Project Overview

This project implements a complete Industry 4.0 monitoring pipeline for a simulated factory environment. It demonstrates how modern industrial systems collect, transmit, process, store and visualise machine data in real time — using the same tools and protocols found in professional industrial environments.

The system monitors 4 machines simultaneously, calculates OEE (Overall Equipment Effectiveness) metrics, tracks downtime, and presents data through two dashboards: a live operator view (Node-RED) and a historical analytics view (Grafana).

---

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Environment                       │
│                                                             │
│  ┌──────────────┐    MQTT      ┌──────────────┐             │
│  │  Simulator   │ ──────────▶  │  Mosquitto   │            │
│  │ (4 machines) │  port 1883   │  MQTT Broker │             │
│  └──────────────┘              └──────┬───────┘             │
│                                       │ MQTT                │
│                                       ▼                     │
│                               ┌──────────────┐              │
│                               │   Node-RED   │              │
│                               │  port 1880   │              │
│                               └──────┬───────┘              │
│                                      │                      │
│                    ┌─────────────────┼──────────────┐       │
│                    ▼                 ▼               ▼      │
│             ┌──────────┐    ┌──────────────┐  ┌─────────┐   │
│             │ Node-RED │    │   InfluxDB   │  │ Grafana │   │
│             │Dashboard │    │  port 8086   │  │port 3000│   │
│             │port 1880 │    └──────────────┘  └─────────┘   │
│             └──────────┘                                    │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. Python simulator generates machine data every 3 seconds for 4 machines
2. Data published to MQTT topics: `factory/machine1/data` ... `factory/machine4/data`
3. Node-RED subscribes to `factory/+/data` (wildcard — all machines in one subscription)
4. Node-RED validates, processes, and calculates OEE metrics per machine
5. Processed data stored in InfluxDB time-series database
6. Node-RED Dashboard shows live current values per machine
7. Grafana Dashboard shows historical trends, OEE gauges, and time-series charts

---

### Technologies Used

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Machine data simulator |
| paho-mqtt | 1.6.1 | MQTT client library |
| Docker | Latest | Container orchestration |
| Eclipse Mosquitto | Latest | MQTT broker |
| Node-RED | Latest | Data processing & live dashboard |
| node-red-contrib-influxdb | Latest | InfluxDB integration for Node-RED |
| @flowfuse/node-red-dashboard | 1.30.2 | Node-RED Dashboard 2.0 |
| InfluxDB | 2.7 | Time-series database |
| Grafana | 10.4.0 | Historical analytics dashboard |

---

### Technology Choices — Why These Tools?

**MQTT + Mosquitto** — MQTT is the industry standard lightweight protocol for IoT sensor data. It uses a publish-subscribe model, meaning machines (publishers) send data to a broker, and Node-RED (subscriber) receives it without the machines needing to know who is listening. This decoupling is essential in real factory environments.

**Node-RED** — A flow-based programming tool widely used in industrial IoT. It allows visual wiring of data flows without complex code. Used here for data validation, OEE calculation, and live dashboard display.

**InfluxDB** — A time-series database purpose-built for sensor data. Unlike relational databases, it is optimised for storing and querying data points with timestamps — exactly what machine monitoring generates every 3 seconds.

**Grafana** — The industry standard for operational dashboards. Used by companies like Siemens, Bosch, and ABB for industrial monitoring. Connected to InfluxDB, it enables historical analysis, trend visualisation, and threshold-based alerting.

**Docker** — Containerisation ensures the entire system runs identically on any machine. All 5 services (simulator, broker, Node-RED, database, dashboard) start with a single command.

---

### Machine Configuration

| Machine | ON Probability | OFF Probability | Temp Range (ON) | Temp Range (OFF) |
|---------|---------------|-----------------|-----------------|------------------|
| Machine 1 | 80% | 20% | 45–75°C | 30–40°C |
| Machine 2 | 82% | 18% | 50–80°C | 30–40°C |
| Machine 3 | 86% | 14% | 40–70°C | 30–40°C |
| Machine 4 | 85% | 15% | 42–72°C | 30–40°C |

Each machine publishes every 3 seconds with:
- `machine_id` — unique identifier
- `status` — ON or OFF
- `temperature` — current reading in °C
- `production_count` — cumulative units produced
- `timestamp` — ISO format datetime

---

### OEE Calculation

OEE (Overall Equipment Effectiveness) is the global standard for measuring manufacturing productivity. Full OEE = Availability × Performance × Quality.

This project implements **Availability-based OEE** — a simplified but valid approach when Performance and Quality sensor data are not available:

```
Availability = (Total Time - Downtime) / Total Time × 100
```

Where:
- **Total Time** = number of messages received × 3 seconds
- **Downtime** = number of OFF messages × 3 seconds
- **Runtime** = Total Time - Downtime

**Industry OEE Thresholds:**
- 🔴 Below 50% — Poor performance, immediate attention required
- 🟡 50–85% — Acceptable, room for improvement
- 🟢 Above 85% — World Class manufacturing performance

---

### Node-RED Flow Design

The flow uses a single tab handling all 4 machines:

**Parse & Validate** — Single entry point for all MQTT messages. Converts raw JSON string to object, validates required fields, drops malformed messages. Acts as a guard clause preventing downstream crashes.

**MQTT Wildcard** — The topic `factory/+/data` uses MQTT's single-level wildcard `+` to subscribe to all 4 machine topics simultaneously in one node.

**Machine-specific filters** — Each display widget receives data from a small function node that filters by `machine_id` — only the relevant machine's data reaches each widget.

**Downtime & Availability** — A single function node handles all 4 machines using `machine_id` as a key for separate flow context variables (`downtime_machine1`, `downtime_machine2` etc.). This prevents cross-machine data mixing.

**Save to InfluxDB** — Receives the complete enriched payload (including calculated downtime and availability) and writes one data point per message cycle.

---

### Dashboard Design

**Node-RED Dashboard (Live Operator View)**
- Purpose: Real-time monitoring — what is happening right now
- Updates every 3 seconds (matches simulator interval)
- Shows: Status (ON/OFF), Temperature gauge, Production count, Downtime, Availability
- 4 machine groups on one page for side-by-side comparison

**Grafana Dashboard (Historical Analytics View)**
- Purpose: Trend analysis — what happened over time
- Auto-refreshes every 5–10 seconds
- Per-machine rows, collapsible
- Panels: OEE gauge, Temperature time-series, Downtime trend, Production count trend
- Uses Flux query language with `pivot` to filter by machine_id

---

### OT Security Module *(Coming Soon)*

> 🚧 **Under Development**

The next phase will simulate real-world OT security scenarios:

**Attack Simulation**
- Rogue MQTT client injecting false sensor data
- Unauthorised topic injection
- Data spoofing — sending fabricated machine_id values

**Detection**
- Node-RED anomaly detection rules
- Temperature spike alerts (outside normal operating range)
- Unknown machine_id detection
- Grafana alert panels

**Prevention**
- MQTT broker authentication (username/password)
- MQTT ACL (Access Control Lists) — restricting which clients can publish to which topics
- TLS encryption for MQTT connections
- Alert notifications via Grafana

This module will directly demonstrate the security vulnerabilities inherent in unauthenticated MQTT systems — a common attack surface in real ICS/SCADA environments.

---
---

## 🇩🇪 Deutsch

### Projektüberblick

Dieses Projekt implementiert eine vollständige Industrie-4.0-Überwachungspipeline für eine simulierte Fabrikumgebung. Es demonstriert, wie moderne Industriesysteme Maschinendaten in Echtzeit erfassen, übertragen, verarbeiten, speichern und visualisieren — mit denselben Werkzeugen und Protokollen, die in professionellen Industrieumgebungen eingesetzt werden.

Das System überwacht 4 Maschinen gleichzeitig, berechnet OEE-Kennzahlen (Overall Equipment Effectiveness), verfolgt Stillstandszeiten und präsentiert Daten über zwei Dashboards: eine Live-Betreiberansicht (Node-RED) und eine historische Analyseansicht (Grafana).

---

### Verwendete Technologien

| Technologie | Version | Verwendungszweck |
|------------|---------|-----------------|
| Python | 3.11 | Maschinendaten-Simulator |
| paho-mqtt | 1.6.1 | MQTT-Client-Bibliothek |
| Docker | Aktuell | Container-Orchestrierung |
| Eclipse Mosquitto | Aktuell | MQTT-Broker |
| Node-RED | Aktuell | Datenverarbeitung & Live-Dashboard |
| InfluxDB | 2.7 | Zeitreihendatenbank |
| Grafana | 10.4.0 | Historisches Analyse-Dashboard |

---

### Maschinenkonfiguration

| Maschine | EIN-Wahrscheinlichkeit | AUS-Wahrscheinlichkeit | Temperaturbereich (EIN) |
|----------|----------------------|----------------------|------------------------|
| Maschine 1 | 80% | 20% | 45–75°C |
| Maschine 2 | 82% | 18% | 50–80°C |
| Maschine 3 | 86% | 14% | 40–70°C |
| Maschine 4 | 85% | 15% | 42–72°C |

---

### OEE-Berechnung

OEE (Overall Equipment Effectiveness) ist der globale Standard zur Messung der Fertigungsproduktivität. Dieses Projekt implementiert eine **verfügbarkeitsbasierte OEE**:

```
Verfügbarkeit = (Gesamtzeit - Stillstandszeit) / Gesamtzeit × 100
```

**OEE-Schwellenwerte (Industriestandard):**
- 🔴 Unter 50% — Schlecht, sofortiger Handlungsbedarf
- 🟡 50–85% — Akzeptabel, Verbesserungspotenzial vorhanden
- 🟢 Über 85% — Weltklasse-Fertigungsleistung

---

### Dashboard-Design

**Node-RED Dashboard (Live-Betreiberansicht)**
- Zweck: Echtzeit-Überwachung — was passiert gerade jetzt
- Aktualisierung alle 3 Sekunden
- Zeigt: Status (EIN/AUS), Temperaturanzeige, Produktionszähler, Stillstandszeit, Verfügbarkeit

**Grafana Dashboard (Historische Analyseansicht)**
- Zweck: Trendanalyse — was ist im Laufe der Zeit passiert
- Pro-Maschinen-Zeilen, einklappbar
- Panels: OEE-Anzeige, Temperatur-Zeitreihe, Stillstandstrend, Produktionszähltrend

---

### OT-Sicherheitsmodul *(Demnächst verfügbar)*

> 🚧 **In Entwicklung**

**Angriffssimulation**
- Rogue MQTT-Client injiziert falsche Sensordaten
- Unbefugte Topic-Injektion
- Datenverfälschung durch gefälschte machine_id-Werte

**Erkennung**
- Node-RED Anomalieerkennung
- Temperaturspitzen-Alarme
- Erkennung unbekannter machine_id-Werte

**Prävention**
- MQTT-Broker-Authentifizierung
- MQTT-ACL (Zugriffskontrolllisten)
- TLS-Verschlüsselung für MQTT-Verbindungen
- Grafana-Benachrichtigungen

---

*Built with ❤️ as an Industry 4.0 portfolio project*
