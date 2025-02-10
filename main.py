import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from database.connection import DatabaseConnection

def main():
    # Inicializar la base de datos y crear tablas
    db = DatabaseConnection()
    db.create_tables()
    
    app = QApplication([])
    
    # Cargar estilos QSS
    try:
        with open('resources/styles/style.qss', 'r') as f:
            style = f.read()
            app.setStyleSheet(style)
    except FileNotFoundError:
        print("Archivo de estilo no encontrado.")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()