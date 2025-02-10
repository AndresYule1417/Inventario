from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QFileDialog, QDateEdit, QSpacerItem, QSizePolicy,
                            QHeaderView, QMessageBox, QLineEdit, QMenu)
from PyQt6.QtCore import Qt, QDate, QDateTime, QPoint
from PyQt6.QtGui import QColor
from database.connection import DatabaseConnection
from utils.reporte_excel_generator import ReporteExcelGenerator
from datetime import datetime
import os
import shutil

class ReporteView(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.fecha_inicio = QDateEdit()
        self.fecha_fin = QDateEdit()
        self.reportes_table = None
        self.reportes_generados = {}  # Diccionario para almacenar rutas de archivos generados
        self.init_ui()
        self.crear_tabla_historial()
        self.cargar_historial()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Título y botones
        header_layout = QHBoxLayout()
        title_label = QLabel("Generación de Reportes")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, 
                                                QSizePolicy.Policy.Minimum))
        main_layout.addLayout(header_layout)

        # Filtros en línea horizontal
        filters_layout = QHBoxLayout()
        
        # Campo de búsqueda
        filters_layout.addWidget(QLabel("Buscar:"))
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Buscar por fecha o descripción")
        self.search_field.setFixedWidth(200)  # Ajustar el tamaño del cajón de búsqueda
        self.search_field.textChanged.connect(self.buscar_en_historial)
        filters_layout.addWidget(self.search_field)
        
        # Fecha inicio
        filters_layout.addWidget(QLabel("Fecha inicio:"))
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_inicio.setStyleSheet("QDateEdit { padding: 5px; }")  # Aplicar estilo
        filters_layout.addWidget(self.fecha_inicio)
        
        # Fecha fin
        filters_layout.addWidget(QLabel("Fecha fin:"))
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setStyleSheet("QDateEdit { padding: 5px; }")  # Aplicar estilo
        filters_layout.addWidget(self.fecha_fin)
        
        # Botón generar
        self.btn_generar_reporte = QPushButton("Generar Reporte Excel")
        self.btn_generar_reporte.clicked.connect(self.generar_reporte)
        filters_layout.addWidget(self.btn_generar_reporte)
        
        main_layout.addLayout(filters_layout)

        # Nueva tabla de historial de reportes
        self.reportes_table = QTableWidget()
        self.reportes_table.setColumnCount(4)
        self.reportes_table.setHorizontalHeaderLabels([
            "FECHA", "DESCRIPCIÓN", "TEMPORALIDAD", "DESCARGAR"
        ])
        self.reportes_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.reportes_table.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        self.reportes_table.itemChanged.connect(self.actualizar_descripcion)
        main_layout.addWidget(self.reportes_table)
        
        # Configurar el ancho de las columnas
        header = self.reportes_table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Conectar eventos
        self.reportes_table.cellEntered.connect(self.hover_descargar)
        self.reportes_table.cellClicked.connect(self.descargar_reporte)

    def mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        """Muestra un mensaje al usuario"""
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        
        if tipo == "info":
            msg.setIcon(QMessageBox.Icon.Information)
        elif tipo == "error":
            msg.setIcon(QMessageBox.Icon.Critical)
        elif tipo == "warning":
            msg.setIcon(QMessageBox.Icon.Warning)
        
        msg.exec()

    def calcular_temporalidad(self, fecha_inicio, fecha_fin):
        """Calcula la temporalidad entre dos fechas"""
        delta = fecha_fin - fecha_inicio
        dias = delta.days
        
        if dias < 30:
            return f"0 mes(es), {dias} día(s)"
        else:
            meses = dias // 30
            dias_restantes = dias % 30
            return f"{meses} mes(es), {dias_restantes} día(s)"

    def agregar_reporte_a_historial(self, fecha_actual, nombre_archivo, temporalidad, file_path):
        """Agrega una nueva fila a la tabla de historial de reportes"""
        row_position = self.reportes_table.rowCount()
        self.reportes_table.insertRow(0)  # Insertar en la primera fila
        
        # Fecha
        fecha_item = QTableWidgetItem(fecha_actual.toString("dd/MM/yyyy HH:mm:ss"))
        self.reportes_table.setItem(0, 0, fecha_item)
        
        # Descripción
        desc_item = QTableWidgetItem(nombre_archivo)
        desc_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
        self.reportes_table.setItem(0, 1, desc_item)
        
        # Temporalidad
        temp_item = QTableWidgetItem(temporalidad)
        self.reportes_table.setItem(0, 2, temp_item)
        
        # Texto de descarga
        item_descargar = QTableWidgetItem("Descargar")
        item_descargar.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_descargar.setForeground(QColor(0, 0, 255))  # Blue color
        item_descargar.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.reportes_table.setItem(0, 3, item_descargar)
        
        # Almacenar la ruta del archivo generado
        self.reportes_generados[nombre_archivo] = file_path

        # Guardar el historial en la base de datos
        self.guardar_historial_db(fecha_actual, nombre_archivo, temporalidad, file_path)

    def verificar_archivo_guardado(self, ruta_archivo):
        """Verifica si el archivo existe y es accesible"""
        try:
            if os.path.exists(ruta_archivo):
                # Intenta abrir el archivo para verificar acceso
                with open(ruta_archivo, 'rb') as f:
                    return True
            return False
        except Exception:
            return False

    def generar_reporte(self):
        try:
            fecha_inicio = self.fecha_inicio.date().toPyDate()
            fecha_fin = self.fecha_fin.date().toPyDate()
            fecha_actual = QDateTime.currentDateTime()
            
            # Obtener datos de la base de datos
            with self.db.connect() as conn:
                cursor = conn.cursor()
                
                # Consulta para inventario con cálculos correctos
                cursor.execute("""
                    SELECT 
                        p.codigo,
                        p.descripcion,
                        COALESCE(SUM(CASE WHEN e.fecha BETWEEN ? AND ? THEN e.cantidad ELSE 0 END), 0) as entradas,
                        COALESCE(SUM(CASE WHEN s.fecha BETWEEN ? AND ? THEN s.cantidad ELSE 0 END), 0) as salidas,
                        p.stock,
                        p.precio_compra,
                        p.precio_venta,
                        COALESCE(SUM(CASE WHEN e.fecha BETWEEN ? AND ? THEN e.cantidad * p.precio_compra ELSE 0 END), 0) as valor_compra_total,
                        COALESCE(SUM(CASE WHEN s.fecha BETWEEN ? AND ? THEN s.cantidad * p.precio_venta ELSE 0 END), 0) as valor_venta_total,
                        COALESCE(SUM(CASE WHEN s.fecha BETWEEN ? AND ? THEN s.cantidad * p.precio_venta ELSE 0 END), 0) - 
                        COALESCE(SUM(CASE WHEN e.fecha BETWEEN ? AND ? THEN e.cantidad * p.precio_compra ELSE 0 END), 0) as utilidad
                    FROM productos p
                    LEFT JOIN entradas e ON p.codigo = e.codigo
                    LEFT JOIN salidas s ON p.codigo = s.codigo
                    GROUP BY p.codigo, p.descripcion, p.stock, p.precio_compra, p.precio_venta
                """, (fecha_inicio, fecha_fin, fecha_inicio, fecha_fin, fecha_inicio, fecha_fin, 
                        fecha_inicio, fecha_fin, fecha_inicio, fecha_fin, fecha_inicio, fecha_fin))
                data_inventario = cursor.fetchall()
                
                # Consulta para entradas
                cursor.execute("""
                    SELECT 
                        datetime(e.fecha) as fecha,
                        e.codigo,
                        p.descripcion,
                        e.cantidad,
                        p.precio_compra,
                        e.cantidad * p.precio_compra as valor_total
                    FROM entradas e
                    JOIN productos p ON e.codigo = p.codigo
                    WHERE e.fecha BETWEEN ? AND ?
                    ORDER BY e.fecha DESC
                """, (fecha_inicio, fecha_fin))
                data_entradas = cursor.fetchall()
                
                # Consulta para salidas
                cursor.execute("""
                    SELECT 
                        datetime(s.fecha) as fecha,
                        s.codigo,
                        p.descripcion,
                        s.cantidad,
                        p.precio_venta,
                        s.cantidad * p.precio_venta as valor_total
                    FROM salidas s
                    JOIN productos p ON s.codigo = p.codigo
                    WHERE s.fecha BETWEEN ? AND ?
                    ORDER BY s.fecha DESC
                """, (fecha_inicio, fecha_fin))
                data_salidas = cursor.fetchall()

            # Generar el reporte
            generator = ReporteExcelGenerator()
            wb = generator.generate_report(
                data_inventario=data_inventario,
                data_entradas=data_entradas,
                data_salidas=data_salidas,
                start_date=fecha_inicio,
                end_date=fecha_fin
            )
            
            # Definir el nombre del archivo
            nombre_archivo = f"reporte_{fecha_actual.toString('yyyyMMdd_HHmmss')}"
            
            # Guardar el archivo temporalmente
            file_path = os.path.join(os.path.expanduser("~"), "Documents", f"{nombre_archivo}.xlsx")
            wb.save(file_path)
            print(f"Reporte generado: {file_path}")
            
            # Calcular la temporalidad
            temporalidad = self.calcular_temporalidad(fecha_inicio, fecha_fin)
            
            # Agregar el nuevo reporte al historial
            self.agregar_reporte_a_historial(fecha_actual, nombre_archivo, temporalidad, file_path)
                
        except Exception as e:
            self.mostrar_mensaje(
                "Error",
                f"Error al generar el reporte:\n{str(e)}",
                "error"
            )

    def descargar_reporte(self, row, column):
        if column == 3:  # Columna "DESCARGAR"
            descripcion = self.reportes_table.item(row, 1).text()
            file_path = self.reportes_generados.get(descripcion)
            if file_path and os.path.exists(file_path):
                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Guardar Reporte Excel",
                    os.path.join(os.path.expanduser("~"), "Downloads", f"{descripcion}.xlsx"),
                    "Excel Files (*.xlsx);;All Files (*)"
                )
                if save_path:
                    try:
                        shutil.copy(file_path, save_path)
                        self.mostrar_mensaje("Éxito", "El archivo se ha descargado exitosamente.", "info")
                    except Exception as e:
                        self.mostrar_mensaje("Error", f"Hubo un error al descargar el archivo: {str(e)}", "error")
            else:
                self.mostrar_mensaje("Error", "El archivo original no se encuentra.", "error")

    def hover_descargar(self, row, column):
        if column == 3:  # Columna "DESCARGAR"
            item = self.reportes_table.item(row, column)
            item.setForeground(QColor(255, 0, 0))  # Red color on hover
        else:
            for r in range(self.reportes_table.rowCount()):
                item = self.reportes_table.item(r, 3)
                item.setForeground(QColor(0, 0, 255))  # Reset to blue

    def buscar_en_historial(self):
        """Filtra la tabla de historial de reportes según el texto de búsqueda"""
        texto_busqueda = self.search_field.text().lower()
        for row in range(self.reportes_table.rowCount()):
            fecha_item = self.reportes_table.item(row, 0)
            descripcion_item = self.reportes_table.item(row, 1)
            if fecha_item and descripcion_item and (texto_busqueda in fecha_item.text().lower() or texto_busqueda in descripcion_item.text().lower()):
                self.reportes_table.setRowHidden(row, False)
            else:
                self.reportes_table.setRowHidden(row, True)

    def guardar_historial_db(self, fecha, descripcion, temporalidad, file_path):
        """Guarda el historial de reportes en la base de datos"""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historial_reportes (fecha, descripcion, temporalidad, file_path)
                VALUES (?, ?, ?, ?)
            """, (fecha.toString("dd/MM/yyyy HH:mm:ss"), descripcion, temporalidad, file_path))
            conn.commit()

    def actualizar_descripcion(self, item):
        """Actualiza la descripción del reporte en la base de datos"""
        if item.column() == 1:  # Columna "DESCRIPCIÓN"
            fila = item.row()
            nueva_descripcion = item.text()
            fecha_item = self.reportes_table.item(fila, 0)
            temporalidad_item = self.reportes_table.item(fila, 2)
            if fecha_item and temporalidad_item:
                fecha = fecha_item.text()
                temporalidad = temporalidad_item.text()
                file_path = self.reportes_generados.pop(self.reportes_table.item(fila, 1).text(), None)
                self.reportes_generados[nueva_descripcion] = file_path
                with self.db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE historial_reportes
                        SET descripcion = ?
                        WHERE fecha = ? AND temporalidad = ?
                    """, (nueva_descripcion, fecha, temporalidad))
                    conn.commit()

    def cargar_historial(self):
        """Carga el historial de reportes desde la base de datos"""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fecha, descripcion, temporalidad, file_path FROM historial_reportes")
            historial = cursor.fetchall()
            for reporte in historial:
                fecha = QDateTime.fromString(reporte[0], "dd/MM/yyyy HH:mm:ss")
                descripcion = reporte[1]
                temporalidad = reporte[2]
                file_path = reporte[3]
                self.agregar_reporte_a_historial(fecha, descripcion, temporalidad, file_path)

    def crear_tabla_historial(self):
        """Crea la tabla historial_reportes si no existe"""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial_reportes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    descripcion TEXT,
                    temporalidad TEXT,
                    file_path TEXT
                )
            """)
            conn.commit()

    def mostrar_menu_contextual(self, posicion):
        """Muestra un menú contextual para eliminar una fila"""
        indices = self.reportes_table.selectedIndexes()
        if indices:
            menu = QMenu()
            eliminar_action = menu.addAction("Eliminar fila")
            action = menu.exec(self.reportes_table.viewport().mapToGlobal(posicion))
            if action == eliminar_action:
                fila = indices[0].row()
                descripcion = self.reportes_table.item(fila, 1).text()
                self.reportes_table.removeRow(fila)
                self.eliminar_reporte_db(descripcion)

    def eliminar_reporte_db(self, descripcion):
        """Elimina un reporte de la base de datos"""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historial_reportes WHERE descripcion = ?", (descripcion,))
            conn.commit()
