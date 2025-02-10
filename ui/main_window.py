from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from .views.productos_view import ProductosView
from .views.entradas_view import EntradasView
from .views.salidas_view import SalidasView
from .views.reporte_view import ReporteView
from .views.historial_view import HistorialView  # Importar la nueva vista

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Sistema de Inventario')
        self.setGeometry(100, 100, 1200, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Crear tabs
        tabs = QTabWidget()
        tabs.addTab(ProductosView(), "Productos")
        tabs.addTab(EntradasView(), "Entradas")
        tabs.addTab(SalidasView(), "Salidas")
        tabs.addTab(ReporteView(), "Reportes")
        tabs.addTab(HistorialView(), "Historial")  # Añadir la nueva pestaña

        layout.addWidget(tabs)