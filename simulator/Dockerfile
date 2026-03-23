# python:3.11-slim: a lightweight Python image
# 'slim' means minimal size — no unnecessary extras
FROM python:3.11-slim

# WORKDIR: sets the working directory inside the container
# like doing cd /app
WORKDIR /app

# copy requirements first: Docker caches layers
# if requirements don't change, it won't reinstall libraries
# every time you rebuild — saves time
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the simulator script into the container
COPY machine_simulator.py .

# CMD: this is what runs when the container starts
CMD ["python", "machine_simulator.py"]
