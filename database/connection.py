import sqlite3
from pathlib import Path

class DatabaseConnection:
    def __init__(self):
        # Crear directorio de base de datos si no existe
        db_path = Path("src/database")
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.db_file = db_path / "inventario.db"

    def connect(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Esto permite acceder a los resultados como diccionarios
        return conn

    def create_tables(self):
        sql_productos = '''
        CREATE TABLE IF NOT EXISTS productos (
            codigo TEXT PRIMARY KEY,
            descripcion TEXT,
            entradas_totales INTEGER DEFAULT 0,
            salidas_totales INTEGER DEFAULT 0,
            stock INTEGER DEFAULT 0,
            precio_compra REAL,
            precio_venta REAL,
            valor_total REAL DEFAULT 0,
            utilidad REAL DEFAULT 0
        )'''

        sql_entradas = '''
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            descripcion TEXT,
            cantidad INTEGER,
            fecha TEXT,
            FOREIGN KEY (codigo) REFERENCES productos(codigo)
        )'''

        sql_salidas = '''
        CREATE TABLE IF NOT EXISTS salidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            descripcion TEXT,
            cantidad INTEGER,
            fecha TEXT,
            FOREIGN KEY (codigo) REFERENCES productos(codigo)
        )'''

        with self.connect() as conn:
            cursor = conn.cursor()
            
            # Primero creamos las tablas
            cursor.execute(sql_productos)
            cursor.execute(sql_entradas)
            cursor.execute(sql_salidas)
            
            # Verificamos si necesitamos agregar la columna utilidad
            cursor.execute("PRAGMA table_info(productos)")
            columnas = cursor.fetchall()
            columnas_nombres = [columna[1] for columna in columnas]
            
            if 'utilidad' not in columnas_nombres:
                try:
                    cursor.execute("ALTER TABLE productos ADD COLUMN utilidad REAL DEFAULT 0")
                except sqlite3.Error:
                    pass  # La columna ya existe
            
            conn.commit()