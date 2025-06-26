import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, Date, MetaData, text
from faker import Faker
import random
import os
from datetime import datetime

# Crear carpetas necesarias
os.makedirs("data", exist_ok=True)
os.makedirs("database", exist_ok=True)

# Inicializar Faker
fake = Faker()

# Generar datos de ventas ficticios
def generar_datos(n=100):
    data = []
    for _ in range(n):
        data.append({
            "cliente": fake.name(),
            "producto": random.choice(["Laptop", "Celular", "Tablet", "Monitor"]),
            "cantidad": random.randint(1, 5),
            "precio_unitario": round(random.uniform(100.0, 1000.0), 2),
            "fecha": fake.date_this_year()
        })
    return pd.DataFrame(data)

# Crear conexión y base de datos SQLite si no existe
db_path = "database/sales.db"
engine = create_engine(f"sqlite:///{db_path}")
conn = engine.connect()
metadata = MetaData()

# Definir tabla si no existe
ventas = Table('ventas', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('cliente', String),
    Column('producto', String),
    Column('cantidad', Integer),
    Column('precio_unitario', Float),
    Column('fecha', Date)
)

# Crear la tabla si no existe
metadata.create_all(engine)

# Verificar si la tabla ya tiene datos
result = conn.execute(text("SELECT COUNT(*) FROM ventas"))
count = result.fetchone()[0]

if count == 0:
    # Generar y guardar datos si la tabla está vacía
    df = generar_datos(200)
    df.to_csv("data/generated_data.csv", index=False)
    df.to_sql("ventas", con=engine, if_exists="append", index=False)
    print("📦 Datos generados e insertados en la base de datos.")
else:
    print("📂 Ya existen datos en la tabla. No se generaron nuevos.")

# Leer desde SQL
df_sql = pd.read_sql("SELECT * FROM ventas", con=engine)

# Calcular total
df_sql["total"] = df_sql["cantidad"] * df_sql["precio_unitario"]

# Agrupar por producto
resumen = df_sql.groupby("producto").agg({
    "cantidad": "sum",
    "total": ["sum", "mean"]
}).reset_index()

# Guardar resumen a TXT
with open("data/summary.txt", "w") as f:
    f.write("Resumen de Ventas por Producto:\n")
    f.write(resumen.to_string())

# Exportar a Excel
resumen.columns = ['Producto', 'Cantidad Total', 'Ventas Totales', 'Promedio Venta']
resumen.to_excel("data/report.xlsx", index=False)

# Generar gráfico
plt.figure(figsize=(8, 5))
df_sql.groupby("producto")["total"].sum().plot(kind="bar", color="orange")
plt.title("Total de Ventas por Producto")
plt.ylabel("Ventas ($)")
plt.tight_layout()
plt.savefig("data/sales_plot.png")
plt.close()

print("✅ Proceso completado. Archivos generados en la carpeta 'data'")
