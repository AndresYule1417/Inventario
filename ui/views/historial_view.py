from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QTableWidget, QTableWidgetItem, QGroupBox, QPushButton,
                            QStackedWidget, QHeaderView, QScrollArea)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QDateTimeAxis
from PyQt6.QtGui import QPainter, QColor
from database.connection import DatabaseConnection
import sqlite3

class HistorialView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.db = DatabaseConnection()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Título
        title_label = QLabel("Historial de Productos")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)

        # Panel de búsqueda y botones
        control_panel = QHBoxLayout()
        
        search_group = QGroupBox("Búsqueda")
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por código o descripción")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.buscar_historial)
        search_layout.addWidget(self.search_input)
        search_group.setLayout(search_layout)
        
        control_panel.addWidget(search_group)

        # Botones de vista en un GroupBox
        view_group = QGroupBox("Vista")
        view_layout = QHBoxLayout()
        btn_ver_tabla = QPushButton("Ver Tabla")
        btn_ver_tabla.setStyleSheet("padding: 5px 15px;")
        btn_ver_tabla.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_ver_grafica = QPushButton("Ver Gráfica")
        btn_ver_grafica.setStyleSheet("padding: 5px 15px;")
        btn_ver_grafica.clicked.connect(self.mostrar_grafica)
        
        view_layout.addWidget(btn_ver_tabla)
        view_layout.addWidget(btn_ver_grafica)
        view_group.setLayout(view_layout)
        
        control_panel.addWidget(view_group)
        control_panel.addStretch()
        
        main_layout.addLayout(control_panel)

        # Contenedor para tabla y gráfica
        self.stacked_widget = QStackedWidget()
        
        # Configuración de la tabla
        self.historial_table = QTableWidget()
        self.historial_table.setColumnCount(11)
        self.historial_table.setHorizontalHeaderLabels([
            "Fecha", "Código", "Descripción", "Tipo Mov.", 
            "Cantidad", "Stock Final", "Precio Compra", "Precio Venta",
            "Valor Movimiento", "Valor Stock", "Utilidad"
        ])
        header = self.historial_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Configuración del área de gráficos
        self.graficas_widget = QWidget()
        self.graficas_layout = QVBoxLayout(self.graficas_widget)
        self.graficas_layout.setSpacing(20)  # Espacio entre gráficas
        
        # Crear un QScrollArea para las gráficas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.graficas_widget)
        
        # Agregar widgets al stacked widget
        self.stacked_widget.addWidget(self.historial_table)
        self.stacked_widget.addWidget(scroll_area)
        
        main_layout.addWidget(self.stacked_widget)

    def crear_chart_view(self, chart, height=300):
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(height)
        chart_view.setMaximumHeight(height)
        return chart_view

    def buscar_historial(self, texto_busqueda):
        if len(texto_busqueda) >= 3:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                
                # Consulta unificada de movimientos
                query = """
                WITH movimientos AS (
                    -- Entradas
                    SELECT 
                        e.fecha,
                        p.codigo,
                        p.descripcion,
                        'Entrada' as tipo_movimiento,
                        e.cantidad,
                        p.stock as stock_final,
                        p.precio_compra,
                        p.precio_venta,
                        (e.cantidad * p.precio_compra) as valor_movimiento,
                        (p.stock * p.precio_compra) as valor_stock,
                        0 as utilidad
                    FROM productos p
                    JOIN entradas e ON p.codigo = e.codigo
                    WHERE p.codigo LIKE ? OR p.descripcion LIKE ?
                    
                    UNION ALL
                    
                    -- Salidas
                    SELECT 
                        s.fecha,
                        p.codigo,
                        p.descripcion,
                        'Salida' as tipo_movimiento,
                        s.cantidad * -1,
                        p.stock as stock_final,
                        p.precio_compra,
                        p.precio_venta,
                        (s.cantidad * p.precio_venta) as valor_movimiento,
                        (p.stock * p.precio_compra) as valor_stock,
                        ((s.cantidad * p.precio_venta) - (s.cantidad * p.precio_compra)) as utilidad
                    FROM productos p
                    JOIN salidas s ON p.codigo = s.codigo
                    WHERE p.codigo LIKE ? OR p.descripcion LIKE ?
                )
                SELECT * FROM movimientos
                ORDER BY fecha DESC
                """
                
                cursor.execute(query, (
                    f'%{texto_busqueda}%', 
                    f'%{texto_busqueda}%',
                    f'%{texto_busqueda}%', 
                    f'%{texto_busqueda}%'
                ))
                
                resultados = cursor.fetchall()
                
                self.historial_table.setRowCount(len(resultados))
                for row, dato in enumerate(resultados):
                    for col, value in enumerate(dato):
                        item = QTableWidgetItem()
                        
                        # Formato especial para valores monetarios
                        if col in [6, 7, 8, 9, 10]:  # Precios, valores y utilidad
                            item.setText(f"${value:,.3f}")
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        # Formato especial para cantidades
                        elif col == 4:  # Cantidad
                            item.setText(f"{value:,}")
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        else:
                            item.setText(str(value))
                            
                        self.historial_table.setItem(row, col, item)

    def mostrar_grafica(self):
        codigo = self.search_input.text()
        if not codigo:
            return
            
        # Limpiar el layout de gráficas existente
        for i in reversed(range(self.graficas_layout.count())): 
            self.graficas_layout.itemAt(i).widget().setParent(None)

        with self.db.connect() as conn:
            cursor = conn.cursor()
            
            # Contenedor para las gráficas superiores
            top_charts_container = QWidget()
            top_charts_layout = QHBoxLayout(top_charts_container)
            
            # Gráfica de línea (entradas y salidas por meses)
            chart_entradas_salidas = self.crear_grafica_entradas_salidas(cursor, codigo)
            chart_view1 = self.crear_chart_view(chart_entradas_salidas)
            top_charts_layout.addWidget(chart_view1)
            
            # Gráfica de stock
            chart_stock = self.crear_grafica_stock(cursor, codigo)
            chart_view2 = self.crear_chart_view(chart_stock)
            top_charts_layout.addWidget(chart_view2)
            
            self.graficas_layout.addWidget(top_charts_container)
            
            # Gráfica de comparación con otros productos (abajo, ancho completo)
            chart_comparacion = self.crear_grafica_comparacion_productos(cursor)
            chart_view3 = self.crear_chart_view(chart_comparacion, 350)
            self.graficas_layout.addWidget(chart_view3)
            
            # Cuadro de observaciones
            observaciones = self.generar_observaciones(cursor, codigo)
            observaciones_group = QGroupBox("Observaciones")
            observaciones_layout = QVBoxLayout()
            observaciones_label = QLabel(observaciones)
            observaciones_label.setWordWrap(True)
            observaciones_label.setStyleSheet("""
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                font-size: 12px;
                line-height: 1.4;
            """)
            observaciones_layout.addWidget(observaciones_label)
            observaciones_group.setLayout(observaciones_layout)
            self.graficas_layout.addWidget(observaciones_group)
            
        self.stacked_widget.setCurrentIndex(1)

    def crear_grafica_entradas_salidas(self, cursor, codigo):
        query_entradas_salidas = """
        SELECT strftime('%Y-%m', fecha) as mes, 
               SUM(CASE WHEN tipo_movimiento = 'Entrada' THEN cantidad ELSE 0 END) as entradas,
               SUM(CASE WHEN tipo_movimiento = 'Salida' THEN cantidad ELSE 0 END) as salidas
        FROM (
            SELECT fecha, 'Entrada' as tipo_movimiento, cantidad
            FROM entradas
            WHERE codigo = ?
            UNION ALL
            SELECT fecha, 'Salida' as tipo_movimiento, cantidad
            FROM salidas
            WHERE codigo = ?
        )
        GROUP BY mes
        ORDER BY mes
        """
        
        cursor.execute(query_entradas_salidas, (codigo, codigo))
        datos_entradas_salidas = cursor.fetchall()
        
        chart = QChart()
        series_entradas = QLineSeries()
        series_salidas = QLineSeries()
        
        # Establecer colores y estilos
        pen_entradas = series_entradas.pen()
        pen_entradas.setWidth(2)
        pen_entradas.setColor(QColor("#2ecc71"))
        series_entradas.setPen(pen_entradas)
        series_entradas.setName("Entradas")
        
        pen_salidas = series_salidas.pen()
        pen_salidas.setWidth(2)
        pen_salidas.setColor(QColor("#e74c3c"))
        series_salidas.setPen(pen_salidas)
        series_salidas.setName("Salidas")
        
        for mes, entradas, salidas in datos_entradas_salidas:
            dt = QDateTime.fromString(mes, "yyyy-MM")
            series_entradas.append(dt.toMSecsSinceEpoch(), entradas)
            series_salidas.append(dt.toMSecsSinceEpoch(), salidas)
        
        chart.addSeries(series_entradas)
        chart.addSeries(series_salidas)
        
        # Configurar ejes
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MM/yyyy")
        axis_x.setTitleText("Mes")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series_entradas.attachAxis(axis_x)
        series_salidas.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Cantidad")
        axis_y.setLabelsAngle(-90)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series_entradas.attachAxis(axis_y)
        series_salidas.attachAxis(axis_y)
        
        chart.setTitle("Movimientos por Mes")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        return chart

    def crear_grafica_stock(self, cursor, codigo):
        query_stock = """
        WITH movimientos AS (
            SELECT fecha, cantidad as cambio_stock
            FROM entradas
            WHERE codigo = ?
            UNION ALL
            SELECT fecha, -cantidad as cambio_stock
            FROM salidas
            WHERE codigo = ?
        )
        SELECT fecha,
                SUM(cambio_stock) OVER (ORDER BY fecha) as stock_acumulado
        FROM movimientos
        ORDER BY fecha
        """
        
        cursor.execute(query_stock, (codigo, codigo))
        datos_stock = cursor.fetchall()
        
        chart = QChart()
        series = QLineSeries()
        
        # Establecer color y estilo
        pen = series.pen()
        pen.setWidth(2)
        pen.setColor(QColor("#3498db"))
        series.setPen(pen)
        series.setName("Stock")
        
        for fecha, stock in datos_stock:
            dt = QDateTime.fromString(fecha, "yyyy-MM-dd HH:mm:ss")
            series.append(dt.toMSecsSinceEpoch(), stock)
        
        chart.addSeries(series)
        
        # Configurar ejes
        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd/MM/yyyy")
        axis_x.setTitleText("Fecha")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Stock")
        axis_y.setLabelsAngle(-90)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        chart.setTitle("Evolución del Stock")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        return chart

    def crear_grafica_comparacion_productos(self, cursor):
        query_comparacion = """
        WITH total_movimientos AS (
            SELECT p.codigo, p.descripcion,
                   COALESCE(SUM(e.cantidad), 0) as entradas,
                   COALESCE(SUM(s.cantidad), 0) as salidas
            FROM productos p
            LEFT JOIN entradas e ON p.codigo = e.codigo
            LEFT JOIN salidas s ON p.codigo = s.codigo
            GROUP BY p.codigo, p.descripcion
        )
        SELECT codigo, descripcion, entradas, salidas
        FROM total_movimientos
        WHERE entradas > 0 OR salidas > 0
        ORDER BY (entradas + salidas) DESC
        LIMIT 5
        """
        
        cursor.execute(query_comparacion)
        datos_comparacion = cursor.fetchall()
        
        chart = QChart()
        
        # Crear dos series separadas para entradas y salidas
        series_entradas = QBarSeries()
        series_salidas = QBarSeries()
        
        # Definir colores para las barras
        set_entradas = QBarSet("Entradas")
        set_entradas.setColor(QColor("#2ecc71"))  # Verde
        
        set_salidas = QBarSet("Salidas")
        set_salidas.setColor(QColor("#e74c3c"))   # Rojo
        
        categorias = []
        for codigo, descripcion, entradas, salidas in datos_comparacion:
            # Agregar datos a cada set
            set_entradas.append(entradas)
            set_salidas.append(salidas)
            # Usar descripción corta para las categorías
            categorias.append(descripcion[:15] + "..." if len(descripcion) > 15 else descripcion)
        
        series_entradas.append(set_entradas)
        series_salidas.append(set_salidas)
        
        chart.addSeries(series_entradas)
        chart.addSeries(series_salidas)
        
        # Configurar eje X (categorías)
        axis_x = QBarCategoryAxis()
        axis_x.append(categorias)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series_entradas.attachAxis(axis_x)
        series_salidas.attachAxis(axis_x)
        
        # Configurar eje Y (valores)
        axis_y = QValueAxis()
        axis_y.setTitleText("Cantidad")
        axis_y.setLabelsAngle(-90)
        
        # Calcular el máximo valor para establecer el rango del eje Y
        max_valor = max([max([e, s]) for _, _, e, s in datos_comparacion])
        axis_y.setRange(0, max_valor * 1.1)  # Agregar 10% de espacio arriba
        
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series_entradas.attachAxis(axis_y)
        series_salidas.attachAxis(axis_y)
        
        # Configurar título y leyenda
        chart.setTitle("Comparación de Movimientos")
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        # Configurar animaciones
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        return chart

    def generar_observaciones(self, cursor, codigo):
        query_observaciones = """
        WITH movimientos AS (
            SELECT e.fecha, 'Entrada' as tipo, e.cantidad,
                   p.precio_compra, p.precio_venta
            FROM entradas e
            JOIN productos p ON e.codigo = p.codigo
            WHERE e.codigo = ?
            UNION ALL
            SELECT s.fecha, 'Salida' as tipo, s.cantidad,
                   p.precio_compra, p.precio_venta
            FROM salidas s
            JOIN productos p ON s.codigo = p.codigo
            WHERE s.codigo = ?
        )
        SELECT 
            COUNT(*) as total_movimientos,
            SUM(CASE WHEN tipo = 'Entrada' THEN cantidad ELSE 0 END) as total_entradas,
            SUM(CASE WHEN tipo = 'Salida' THEN cantidad ELSE 0 END) as total_salidas,
            AVG(CASE WHEN tipo = 'Entrada' THEN cantidad ELSE NULL END) as promedio_entradas,
            AVG(CASE WHEN tipo = 'Salida' THEN cantidad ELSE NULL END) as promedio_salidas,
            MIN(CASE WHEN tipo = 'Entrada' THEN precio_compra ELSE NULL END) as min_precio_compra,
            MAX(CASE WHEN tipo = 'Entrada' THEN precio_compra ELSE NULL END) as max_precio_compra,
            MIN(CASE WHEN tipo = 'Salida' THEN precio_venta ELSE NULL END) as min_precio_venta,
            MAX(CASE WHEN tipo = 'Salida' THEN precio_venta ELSE NULL END) as max_precio_venta
        FROM movimientos
        """
        
        cursor.execute(query_observaciones, (codigo, codigo))
        datos = cursor.fetchone()
        
        observaciones = "OBSERVACIONES:\n\n"
        observaciones += f"1. Movimientos totales: {datos[0]}\n"
        observaciones += f"   - Total entradas: {datos[1]}\n"
        observaciones += f"   - Total salidas: {datos[2]}\n\n"
        
        observaciones += f"2. Promedios:\n"
        observaciones += f"   - Promedio de entradas: {datos[3]:.2f}\n" if datos[3] is not None else "   - Promedio de entradas: N/A\n"
        observaciones += f"   - Promedio de salidas: {datos[4]:.2f}\n" if datos[4] is not None else "   - Promedio de salidas: N/A\n\n"
        
        observaciones += f"3. Precios:\n"
        observaciones += f"   - Rango de precio de compra: ${datos[5]:.2f} - ${datos[6]:.2f}\n" if datos[5] is not None and datos[6] is not None else "   - Rango de precio de compra: N/A\n"
        observaciones += f"   - Rango de precio de venta: ${datos[7]:.2f} - ${datos[8]:.2f}\n" if datos[7] is not None and datos[8] is not None else "   - Rango de precio de venta: N/A\n"
        
        variacion_compra = ((datos[6] - datos[5]) / datos[5]) * 100 if datos[5] and datos[6] else 0
        variacion_venta = ((datos[8] - datos[7]) / datos[7]) * 100 if datos[7] and datos[8] else 0
        
        observaciones += f"\n4. Variaciones de precio:\n"
        observaciones += f"   - Variación en precio de compra: {variacion_compra:.2f}%\n" if variacion_compra else "   - Variación en precio de compra: N/A\n"
        observaciones += f"   - Variación en precio de venta: {variacion_venta:.2f}%\n" if variacion_venta else "   - Variación en precio de venta: N/A\n"
        
        return observaciones