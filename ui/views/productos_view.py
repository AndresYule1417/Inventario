from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QSpacerItem, QSizePolicy, QDateEdit, QMenu, QDialog, QInputDialog)
from PyQt6.QtGui import QAction, QPixmap  
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from database.connection import DatabaseConnection
import sqlite3
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis

class ProductosView(QWidget):
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.db = DatabaseConnection()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Encabezado con logo y botones
        header_layout = QHBoxLayout()
        
        # Título
        title_label = QLabel("Gestión de Productos")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        layout.addLayout(header_layout)
        
        # Espacio flexible
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Botones de opciones
        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.setObjectName("btn_actualizar")
        btn_actualizar.clicked.connect(self.load_data)
        self.btn_formatear = QPushButton("Formatear")
        self.btn_formatear.setObjectName("btn_formatear")
        btn_tema = QPushButton("Cambiar Tema")
        btn_tema.setObjectName("btn_tema")
        
        header_layout.addWidget(btn_actualizar)
        header_layout.addWidget(self.btn_formatear)
        header_layout.addWidget(btn_tema)
        
        layout.addLayout(header_layout)

        # Configurar el botón de formateo
        self.setup_format_button()

        # Barra de búsqueda
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por código o descripción")
        self.search_input.setFixedWidth(200)  # Ajustar tamaño del campo de búsqueda
        self.search_input.textChanged.connect(self.search_product)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Formulario de entrada
        form_layout = QHBoxLayout()
        
        # Campos de entrada
        self.codigo_input = QLineEdit()
        self.codigo_input.setFixedWidth(150)  # Ajustar tamaño del campo de código
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setFixedWidth(200)  # Ajustar tamaño del campo de descripción
        self.precio_compra_input = QLineEdit()
        self.precio_venta_input = QLineEdit()

        # Etiquetas
        form_layout.addWidget(QLabel("Código:"))
        form_layout.addWidget(self.codigo_input)
        form_layout.addWidget(QLabel("Descripción:"))
        form_layout.addWidget(self.descripcion_input)
        form_layout.addWidget(QLabel("Precio Compra:"))
        form_layout.addWidget(self.precio_compra_input)
        form_layout.addWidget(QLabel("Precio Venta:"))
        form_layout.addWidget(self.precio_venta_input)

        # Botón Agregar
        self.btn_agregar = QPushButton("Agregar Producto")
        self.btn_agregar.clicked.connect(self.agregar_producto)
        form_layout.addWidget(self.btn_agregar)

        layout.addLayout(form_layout)

        # Tabla de productos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(10)
        self.tabla.setHorizontalHeaderLabels([
            "Código", "Descripción", "Entradas", "Salidas", 
            "Stock", "Precio Compra", "Precio Venta", "Valor Compra Total", "Valor Venta Total", "Utilidad"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.show_context_menu)
        self.tabla.cellDoubleClicked.connect(self.show_product_details)
        layout.addWidget(self.tabla)

    def setup_format_button(self):
        # Crear el menú para el botón Formatear
        self.format_menu = QMenu(self)
        
        # Agregar las opciones al menú
        self.action_eliminar_columna = self.format_menu.addAction("Eliminar Columna")
        self.action_eliminar_tabla = self.format_menu.addAction("Eliminar Tabla Completa")
        
        # Conectar las acciones con sus respectivas funciones
        self.action_eliminar_columna.triggered.connect(self.eliminar_columna)
        self.action_eliminar_tabla.triggered.connect(self.eliminar_tabla)
        
        # Asignar el menú al botón Formatear
        self.btn_formatear.setMenu(self.format_menu)

    def eliminar_columna(self):
        # Obtener los nombres de las columnas
        headers = []
        for col in range(self.tabla.columnCount()):
            headers.append(self.tabla.horizontalHeaderItem(col).text())
        
        # Mostrar diálogo para seleccionar la columna
        columna, ok = QInputDialog.getItem(
            self,
            "Seleccionar Columna",
            "Elija la columna a eliminar:",
            headers,
            0,
            False
        )
        
        if ok and columna:
            # Encontrar el índice de la columna seleccionada
            col_index = headers.index(columna)
            
            # Confirmar la eliminación
            reply = QMessageBox.question(
                self,
                'Confirmar Eliminación',
                f'¿Está seguro de que desea eliminar la columna "{columna}"?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Eliminar los datos de la columna
                for row in range(self.tabla.rowCount()):
                    self.tabla.setItem(row, col_index, QTableWidgetItem(""))

    def eliminar_tabla(self):
        # Confirmar la eliminación
        reply = QMessageBox.question(
            self,
            'Confirmar Eliminación',
            '¿Está seguro de que desea eliminar todos los datos de la tabla?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Eliminar todos los datos manteniendo la estructura
            for row in range(self.tabla.rowCount()):
                for col in range(self.tabla.columnCount()):
                    self.tabla.setItem(row, col, QTableWidgetItem(""))

    def agregar_producto(self):
        codigo = self.codigo_input.text()
        descripcion = self.descripcion_input.text()
        try:
            precio_compra = float(self.precio_compra_input.text())
            precio_venta = float(self.precio_venta_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Los precios deben ser números válidos.")
            return

        if not codigo or not descripcion:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return

        with self.db.connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO productos (
                        codigo, descripcion, precio_compra, precio_venta,
                        entradas_totales, salidas_totales, stock, valor_total
                    )
                    VALUES (?, ?, ?, ?, 0, 0, 0, 0)
                """, (codigo, descripcion, precio_compra, precio_venta))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Producto agregado exitosamente")
                self.load_data()
                self.data_changed.emit()
                
                # Limpiar campos
                self.codigo_input.clear()
                self.descripcion_input.clear()
                self.precio_compra_input.clear()
                self.precio_venta_input.clear()
                
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "El código del producto ya existe")

    def load_data(self):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos")
            productos = cursor.fetchall()

            self.tabla.setRowCount(len(productos) + 1)  # +1 para la fila de totales
            total_entradas = 0
            total_salidas = 0
            total_stock = 0
            total_precio_compra = 0
            total_precio_venta = 0
            total_precio_compra_total = 0
            total_precio_venta_total = 0
            total_utilidad = 0

            for row, producto in enumerate(productos):
                entradas_totales = producto["entradas_totales"]
                salidas_totales = producto["salidas_totales"]
                stock = producto["stock"]
                precio_compra = producto["precio_compra"]
                precio_venta = producto["precio_venta"]
                valor_compra_total = entradas_totales * precio_compra
                valor_venta_total = salidas_totales * precio_venta
                utilidad = valor_venta_total - valor_compra_total

                total_entradas += entradas_totales
                total_salidas += salidas_totales
                total_stock += stock
                total_precio_compra += precio_compra
                total_precio_venta += precio_venta
                total_precio_compra_total += valor_compra_total
                total_precio_venta_total += valor_venta_total
                total_utilidad += utilidad

                self.tabla.setItem(row, 0, QTableWidgetItem(producto["codigo"]))
                self.tabla.setItem(row, 1, QTableWidgetItem(producto["descripcion"]))
                self.tabla.setItem(row, 2, QTableWidgetItem(str(entradas_totales)))
                self.tabla.setItem(row, 3, QTableWidgetItem(str(salidas_totales)))
                self.tabla.setItem(row, 4, QTableWidgetItem(str(stock)))
                self.tabla.setItem(row, 5, QTableWidgetItem(f"${precio_compra:,.3f}"))
                self.tabla.setItem(row, 6, QTableWidgetItem(f"${precio_venta:,.3f}"))
                self.tabla.setItem(row, 7, QTableWidgetItem(f"${valor_compra_total:,.3f}"))
                self.tabla.setItem(row, 8, QTableWidgetItem(f"${valor_venta_total:,.3f}"))
                self.tabla.setItem(row, 9, QTableWidgetItem(f"${utilidad:,.3f}"))

            # Fila de totales
            total_row = len(productos)
            self.tabla.setItem(total_row, 0, QTableWidgetItem("TOTALES"))
            self.tabla.setItem(total_row, 2, QTableWidgetItem(str(total_entradas)))
            self.tabla.setItem(total_row, 3, QTableWidgetItem(str(total_salidas)))
            self.tabla.setItem(total_row, 4, QTableWidgetItem(str(total_stock)))
            self.tabla.setItem(total_row, 5, QTableWidgetItem(f"${total_precio_compra:,.3f}"))
            self.tabla.setItem(total_row, 6, QTableWidgetItem(f"${total_precio_venta:,.3f}"))
            self.tabla.setItem(total_row, 7, QTableWidgetItem(f"${total_precio_compra_total:,.3f}"))
            self.tabla.setItem(total_row, 8, QTableWidgetItem(f"${total_precio_venta_total:,.3f}"))
            self.tabla.setItem(total_row, 9, QTableWidgetItem(f"${total_utilidad:,.3f}"))

            # Estilo en negrilla para la fila de totales
            for col in range(10):
                item = self.tabla.item(total_row, col)
                if item:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

    def search_product(self):
        search_text = self.search_input.text().lower()
        for row in range(self.tabla.rowCount()):
            codigo_item = self.tabla.item(row, 0)
            descripcion_item = self.tabla.item(row, 1)
            if codigo_item is not None and descripcion_item is not None:
                codigo = codigo_item.text().lower()
                descripcion = descripcion_item.text().lower()
                if search_text in codigo or search_text in descripcion:
                    self.tabla.showRow(row)
                else:
                    self.tabla.hideRow(row)

    def show_context_menu(self, position):
        menu = QMenu()
        edit_action = menu.addAction("✏️ Editar")
        delete_action = menu.addAction("❌ Eliminar")

        action = menu.exec(self.tabla.viewport().mapToGlobal(position))
        if action == edit_action:
            self.edit_product()
        elif action == delete_action:
            self.delete_product()

    def edit_product(self):
        row = self.tabla.currentRow()
        codigo = self.tabla.item(row, 0).text()
        descripcion = self.tabla.item(row, 1).text()
        precio_compra = self.tabla.item(row, 5).text().replace("$", "").replace(",", "")
        precio_venta = self.tabla.item(row, 6).text().replace("$", "").replace(",", "")

        self.codigo_input.setText(codigo)
        self.descripcion_input.setText(descripcion)
        self.precio_compra_input.setText(precio_compra)
        self.precio_venta_input.setText(precio_venta)

        self.btn_agregar.setText("Guardar Cambios")
        self.btn_agregar.clicked.disconnect()
        self.btn_agregar.clicked.connect(lambda: self.save_changes(row))

    def save_changes(self, row):
        codigo = self.codigo_input.text()
        descripcion = self.descripcion_input.text()
        try:
            precio_compra = float(self.precio_compra_input.text())
            precio_venta = float(self.precio_venta_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Los precios deben ser números válidos.")
            return

        with self.db.connect() as conn:
            cursor = conn.cursor()
            try:
                # Iniciar transacción
                cursor.execute("BEGIN TRANSACTION")
                
                # Obtener los valores actuales
                cursor.execute("""
                    SELECT entradas_totales, salidas_totales, stock 
                    FROM productos 
                    WHERE codigo = ?
                """, (codigo,))
                result = cursor.fetchone()
                if result:
                    entradas_totales = result['entradas_totales']
                    salidas_totales = result['salidas_totales']
                    stock = result['stock']
                    
                    # Calcular los nuevos valores
                    valor_total = stock * precio_compra
                    utilidad = (salidas_totales * precio_venta) - (entradas_totales * precio_compra)
                    
                    # Actualizar producto
                    cursor.execute("""
                        UPDATE productos
                        SET descripcion = ?, 
                            precio_compra = ?, 
                            precio_venta = ?,
                            valor_total = ?,
                            utilidad = ?
                        WHERE codigo = ?
                    """, (descripcion, precio_compra, precio_venta, valor_total, utilidad, codigo))
                    
                    # Actualizar descripción en tablas relacionadas
                    cursor.execute("UPDATE entradas SET descripcion = ? WHERE codigo = ?", 
                                 (descripcion, codigo))
                    cursor.execute("UPDATE salidas SET descripcion = ? WHERE codigo = ?", 
                                 (descripcion, codigo))
                    
                    cursor.execute("COMMIT")
                    QMessageBox.information(self, "Éxito", "Producto actualizado exitosamente")
                    self.load_data()
                    self.data_changed.emit()
                else:
                    cursor.execute("ROLLBACK")
                    QMessageBox.warning(self, "Error", "No se encontró el producto")

            except sqlite3.Error as e:
                cursor.execute("ROLLBACK")
                QMessageBox.warning(self, "Error", f"Error en la base de datos: {str(e)}")

        self.btn_agregar.setText("Agregar Producto")
        self.btn_agregar.clicked.disconnect()
        self.btn_agregar.clicked.connect(self.agregar_producto)
        
        # Limpiar campos
        self.codigo_input.clear()
        self.descripcion_input.clear()
        self.precio_compra_input.clear()
        self.precio_venta_input.clear()

    def delete_product(self):
        row = self.tabla.currentRow()
        codigo = self.tabla.item(row, 0).text()

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM productos WHERE codigo = ?", (codigo,))
            conn.commit()
            QMessageBox.information(self, "Éxito", "Producto eliminado exitosamente")
            self.load_data()
            self.data_changed.emit()

    def show_product_details(self, row, col):
        if col == 0 or col == 1:  # Código o Descripción
            codigo = self.tabla.item(row, 0).text()
            self.open_product_details_window(codigo)

    def open_product_details_window(self, codigo):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Detalles del Producto: {codigo}")
        layout = QVBoxLayout()

        # Obtener información detallada del producto
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, 
                       (SELECT COUNT(*) FROM entradas WHERE codigo = p.codigo) as compras_count,
                       (SELECT COUNT(*) FROM salidas WHERE codigo = p.codigo) as ventas_count
                FROM productos p
                WHERE p.codigo = ?
            """, (codigo,))
            producto = cursor.fetchone()

            if producto:
                # Mostrar información básica
                layout.addWidget(QLabel(f"Código: {producto['codigo']}"))
                layout.addWidget(QLabel(f"Descripción: {producto['descripcion']}"))
                layout.addWidget(QLabel(f"Stock actual: {producto['stock']}"))
                layout.addWidget(QLabel(f"Precio de compra: ${producto['precio_compra']:.3f}"))
                layout.addWidget(QLabel(f"Precio de venta: ${producto['precio_venta']:.3f}"))
                layout.addWidget(QLabel(f"Compras totales: {producto['compras_count']}"))
                layout.addWidget(QLabel(f"Ventas totales: {producto['ventas_count']}"))

                # Obtener historial de compras y ventas
                cursor.execute("""
                    SELECT 'Compra' as tipo, fecha, cantidad FROM entradas WHERE codigo = ?
                    UNION ALL
                    SELECT 'Venta' as tipo, fecha, cantidad FROM salidas WHERE codigo = ?
                    ORDER BY fecha DESC LIMIT 10
                """, (codigo, codigo))
                historial = cursor.fetchall()

                layout.addWidget(QLabel("Últimas 10 transacciones:"))
                for transaccion in historial:
                    layout.addWidget(QLabel(f"{transaccion['tipo']} - Fecha: {transaccion['fecha']}, Cantidad: {transaccion['cantidad']}"))

                # Crear gráfico de comparación
                chart = QChart()
                series = QBarSeries()
                set_stock = QBarSet("Stock")
                set_entradas = QBarSet("Entradas Totales")
                set_salidas = QBarSet("Salidas Totales")

                set_stock.append(producto['stock'])
                set_entradas.append(producto['entradas_totales'])
                set_salidas.append(producto['salidas_totales'])

                series.append(set_stock)
                series.append(set_entradas)
                series.append(set_salidas)

                chart.addSeries(series)
                chart.setTitle("Comparación de Stock")

                categories = [""]
                axis_x = QBarCategoryAxis()
                axis_x.append(categories)
                chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
                series.attachAxis(axis_x)

                axis_y = QValueAxis()
                chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
                series.attachAxis(axis_y)

                chart_view = QChartView(chart)
                chart_view.setMinimumSize(400, 300)
                layout.addWidget(chart_view)

            else:
                layout.addWidget(QLabel("Producto no encontrado"))

        dialog.setLayout(layout)
        dialog.exec()

        pass