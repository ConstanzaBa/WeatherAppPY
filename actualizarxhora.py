import subprocess

print("Actualizando datos meteorologicos...")

# subprocess.run(["python", "data.py"], check=False)

subprocess.run(["python", "actualclima.py"], check=False)

print("Datos meteorologicos actualizados.")
