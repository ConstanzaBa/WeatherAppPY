import subprocess

print("Actualizando datos meteorologicos...")

subprocess.run(["python", "actualclima.py"], check=False)

print("Datos meteorologicos actualizados.")
