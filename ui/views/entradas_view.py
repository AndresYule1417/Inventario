import sqlite3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QSpacerItem, QSizePolicy, QDateTimeEdit, QMenu, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from database.connection import DatabaseConnection

class EntradasView(QWidget):
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
        title_label = QLabel("Entradas")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        # Espacio flexible
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Botones de opciones
        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.setObjectName("btn_actualizar")
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

        # Formulario de entrada con búsqueda integrada
        form_layout = QHBoxLayout()
        
        # Campos de entrada
        self.codigo_input = QLineEdit()
        self.codigo_input.setFixedWidth(150)
        self.cantidad_input = QLineEdit()
        self.cantidad_input.setFixedWidth(150)
        self.fecha_input = QDateTimeEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDateTime(QDateTime.currentDateTime())
        self.fecha_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.fecha_input.setStyleSheet("QDateTimeEdit { background-color: #f0f0f0; color: #333; border: 1px solid #ccc; border-radius: 5px; padding: 5px; }")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por código")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.search_entry)

        # Añadir campos al layout
        form_layout.addWidget(QLabel("Código:"))
        form_layout.addWidget(self.codigo_input)
        form_layout.addWidget(QLabel("Cantidad:"))
        form_layout.addWidget(self.cantidad_input)
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.fecha_input)
        form_layout.addWidget(QLabel("Buscar:"))
        form_layout.addWidget(self.search_input)

        # Botón Agregar
        self.btn_agregar = QPushButton("Agregar Entrada")
        self.btn_agregar.clicked.connect(self.agregar_entrada)
        form_layout.addWidget(self.btn_agregar)

        layout.addLayout(form_layout)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "Código", "Descripción", "Cantidad", "Fecha"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.show_context_menu)
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

    def agregar_entrada(self):
        codigo = self.codigo_input.text()
        try:
            cantidad = int(self.cantidad_input.text())
            if cantidad <= 0:
                QMessageBox.warning(self, "Error", "La cantidad debe ser mayor que 0.")
                return
        except ValueError:
            QMessageBox.warning(self, "Error", "La cantidad debe ser un número válido.")
            return
        fecha = self.fecha_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        if not codigo:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return

        with self.db.connect() as conn:
            cursor = conn.cursor()
            # Obtener la descripción del producto
            cursor.execute("SELECT descripcion FROM productos WHERE codigo = ?", (codigo,))
            result = cursor.fetchone()
            if result:
                descripcion = result[0]
                try:
                    cursor.execute("""
                        INSERT INTO entradas (codigo, descripcion, cantidad, fecha)
                        VALUES (?, ?, ?, ?)
                    """, (codigo, descripcion, cantidad, fecha))
                    
                    # Actualizar la tabla de productos
                    cursor.execute("""
                        UPDATE productos
                        SET entradas_totales = entradas_totales + ?, 
                            stock = stock + ?,
                            valor_total = (stock + ?) * precio_compra
                        WHERE codigo = ?
                    """, (cantidad, cantidad, cantidad, codigo))
                    
                    conn.commit()
                    QMessageBox.information(self, "Éxito", "Entrada agregada exitosamente")
                    self.load_data()
                    self.data_changed.emit()
                    
                    # Limpiar campos
                    self.codigo_input.clear()
                    self.cantidad_input.clear()
                    
                except sqlite3.Error as e:
                    QMessageBox.warning(self, "Error", f"Error en la base de datos: {str(e)}")
            else:
                QMessageBox.warning(self, "Error", "El código del producto no existe")

    def load_data(self):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, descripcion, cantidad, fecha FROM entradas ORDER BY fecha DESC, id DESC")
            entradas = cursor.fetchall()

            self.tabla.setRowCount(len(entradas))

            for row_idx, entrada in enumerate(entradas):
                codigo, descripcion, cantidad, fecha = entrada

                for col_idx, value in enumerate([codigo, descripcion, cantidad, fecha]):
                    item = QTableWidgetItem(str(value))
                    self.tabla.setItem(row_idx, col_idx, item)

    def search_entry(self):
        search_text = self.search_input.text().lower()
        for row in range(self.tabla.rowCount()):
            codigo_item = self.tabla.item(row, 0)
            descripcion_item = self.tabla.item(row, 1)
            if codigo_item and descripcion_item:
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
            self.edit_entry()
        elif action == delete_action:
            self.delete_entry()

    def edit_entry(self):
        row = self.tabla.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Advertencia", "Seleccione una entrada para editar.")
            return

        codigo = self.tabla.item(row, 0).text()
        cantidad_original = int(self.tabla.item(row, 2).text())
        fecha = self.tabla.item(row, 3).text()

        new_cantidad, ok = QInputDialog.getInt(self, "Editar Cantidad", "Nueva Cantidad:", cantidad_original, 1)
        if ok:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                try:
                    # Iniciar transacción
                    cursor.execute("BEGIN TRANSACTION")
                    
                    # Actualizar entrada
                    cursor.execute("""
                        UPDATE entradas
                        SET cantidad = ?
                        WHERE codigo = ? AND fecha = ?
                    """, (new_cantidad, codigo, fecha))
                    
                    # Actualizar productos
                    diferencia = new_cantidad - cantidad_original
                    cursor.execute("""
                        UPDATE productos
                        SET entradas_totales = entradas_totales + ?,
                            stock = stock + ?,
                            valor_total = (stock + ?) * precio_compra,
                            utilidad = (salidas_totales * precio_venta) - ((entradas_totales + ?) * precio_compra)
                        WHERE codigo = ?
                    """, (diferencia, diferencia, diferencia, diferencia, codigo))
                    
                    cursor.execute("COMMIT")
                    self.load_data()
                    self.data_changed.emit()
                    
                except sqlite3.Error as e:
                    cursor.execute("ROLLBACK")
                    QMessageBox.warning(self, "Error", f"Error en la base de datos: {str(e)}")

    def delete_entry(self):
        row = self.tabla.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Advertencia", "Seleccione una entrada para eliminar.")
            return

        codigo = self.tabla.item(row, 0).text()
        fecha = self.tabla.item(row, 3).text()

        reply = QMessageBox.question(
            self,
            'Confirmar Eliminación',
            f'¿Está seguro de que desea eliminar la entrada con código "{codigo}" y fecha "{fecha}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM entradas WHERE codigo = ? AND fecha = ?", (codigo, fecha))
                conn.commit()
                self.load_data()
                self.data_changed.emit()