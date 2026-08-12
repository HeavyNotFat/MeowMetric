from __future__ import annotations

from typing import Sequence

from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QRectF, QPointF, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QBrush

STYLESHEET = """
QWidget {
    background-color: #f4f6f9;
}
QWidget#central_container {
    background-color: #f4f6f9;
    border-radius: 10px;
}

/* 数据卡片 */
QFrame[class="card"] {
    background-color: #ffffff;
    border-radius: 12px;
}
QLabel#stat_title {
    color: #7f8c8d;
    font-size: 13px;
    font-weight: normal;
}
QLabel#stat_value {
    color: #2c3e50;
    font-size: 22px;
    font-weight: bold;
}

/* 工具按钮 */
QPushButton.tool-btn {
    background-color: #3498db;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton.tool-btn:hover {
    background-color: #2c80b4;
}
QPushButton#btn_clear {
    background-color: #e74c3c;
}
QPushButton#btn_clear:hover {
    background-color: #c0392b;
}
"""


class StatCard(QFrame):
    """统计卡片组件，支持趋势指示与数值滚动动画"""

    def __init__(self, title: str, value: int | float | str, trend: float | None = None, parent=None):
        """
        :param title: 卡片标题
        :param value: 初始数值（int/float 才会有滚动动画，str 直接显示）
        :param trend: 同比/环比变化百分比，正数显示绿色↑，负数显示红色↓，None 则不显示
        """
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setObjectName("card")
        self._value = value
        self._anim = QVariantAnimation(self)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setDuration(400)
        self._anim.valueChanged.connect(self._on_anim_value)

        # 只保留一份样式定义，避免和全局 STYLESHEET 重复/互相覆盖
        self.setStyleSheet("""
            QFrame[class="card"] {
                background: white;
                border-radius: 10px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)

        lbl_t = QLabel(title)
        lbl_t.setObjectName("stat_title")
        lbl_t.setStyleSheet("font-size:13px; color:#7f8c8d; font-weight:bold;")

        row = QHBoxLayout()
        row.setSpacing(8)

        self.lbl_value = QLabel(str(value))
        self.lbl_value.setObjectName("stat_value")
        self.lbl_value.setStyleSheet("font-size:32px; color:#2c3e50; font-weight:800;")
        row.addWidget(self.lbl_value)

        self.lbl_trend = QLabel()
        self.lbl_trend.setStyleSheet("font-size:13px; font-weight:600;")
        row.addWidget(self.lbl_trend)
        row.addStretch()

        layout.addWidget(lbl_t)
        layout.addLayout(row)
        layout.addStretch()

        if trend is not None:
            self.set_trend(trend)

    def _on_anim_value(self, v):
        # 整数就取整显示，浮点保留一位小数
        if isinstance(self._value, int):
            self.lbl_value.setText(str(int(round(v))))
        else:
            self.lbl_value.setText(f"{v:.1f}")

    def set_trend(self, trend: float):
        """更新涨跌趋势标签"""
        if trend > 0:
            self.lbl_trend.setText(f"▲ {trend:.1f}%")
            self.lbl_trend.setStyleSheet("font-size:13px; font-weight:600; color:#2ecc71;")
        elif trend < 0:
            self.lbl_trend.setText(f"▼ {abs(trend):.1f}%")
            self.lbl_trend.setStyleSheet("font-size:13px; font-weight:600; color:#e74c3c;")
        else:
            self.lbl_trend.setText("— 0%")
            self.lbl_trend.setStyleSheet("font-size:13px; font-weight:600; color:#95a5a6;")

    def update_value(self, value: int | float | str, trend: float | None = None, animate: bool = True):
        """更新数值，数字类型默认带滚动动画；字符串直接替换"""
        old = self._value
        self._value = value
        if trend is not None:
            self.set_trend(trend)

        if animate and isinstance(value, (int, float)) and isinstance(old, (int, float)):
            self._anim.stop()
            self._anim.setStartValue(float(old))
            self._anim.setEndValue(float(value))
            self._anim.start()
        else:
            self.lbl_value.setText(str(value))


class ChartWidget(QWidget):
    """图表基类：统一背景、边距、调色板与"无数据"占位"""

    PALETTE = ["#3498db", "#e74c3c", "#f1c40f", "#2ecc71", "#9b59b6", "#1abc9c", "#e67e22"]
    MARGIN = 40
    CORNER_RADIUS = 12
    SAFE_INSET = 6

    def __init__(self):
        super().__init__()
        self.bg = QColor("#FFFFFF")
        self.text = QColor("#2c3e50")
        self.muted = QColor("#95a5a6")
        self.setMinimumSize(260, 200)

        self.zoom = 1.0

        self.offset = 0
        self.offset_x = 0
        self.offset_y = 0

        self.dragging = False
        self.last_mouse_pos = None

        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.CORNER_RADIUS, self.CORNER_RADIUS)
        painter.setClipPath(path)
        painter.fillPath(path, QBrush(self.bg))

        self.draw(painter)

    def draw(self, painter):
        pass

    def draw_no_data(self, painter):
        painter.setPen(self.muted)
        painter.setFont(QFont("Microsoft YaHei", 12))
        painter.drawText(self.rect(), Qt.AlignCenter, "暂无数据")

    def text_draw(self, painter, text, x, y, size=12, color=None):
        painter.setPen(color or self.text)
        painter.setFont(QFont("Microsoft YaHei", size))
        painter.drawText(int(x), int(y), text)

    def draw_axes(self, painter, plot_rect, v_min, v_max, x_labels=None, n=None,
                  y_ticks=5, value_fmt="{:.0f}", center_ticks=False, nice=True):
        x0, y0, x1, y1 = plot_rect

        if nice:
            v_min, v_max, step = self._nice_ticks(v_min, v_max, y_ticks)
            num_lines = max(1, round((v_max - v_min) / step))
        else:
            step = (v_max - v_min) / y_ticks
            num_lines = y_ticks

        grid_pen = QPen(QColor(0, 0, 0, 18), 1, Qt.DashLine)
        axis_pen = QPen(QColor("#dfe4ea"), 1.2)

        for i in range(num_lines + 1):
            value = v_min + step * i
            try:
                y = y1 - (value - v_min) / (v_max - v_min) * (y1 - y0)
            except (ZeroDivisionError, ValueError):
                return
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(x0, y), QPointF(x1, y))
            self.text_draw(painter, value_fmt.format(value), 4, y + 4, 9, self.muted)

        painter.setPen(axis_pen)
        painter.drawLine(QPointF(x0, y0), QPointF(x0, y1))
        painter.drawLine(QPointF(x0, y1), QPointF(x1, y1))

        if x_labels and n:
            step_x = max(1, len(x_labels) // 8)
            for i, label in enumerate(x_labels):
                if i % step_x != 0 and i != len(x_labels) - 1:
                    continue
                if center_ticks:
                    slot = (x1 - x0) / n
                    x = x0 + (i + 0.5) * slot
                else:
                    x = x0 + i * (x1 - x0) / (n - 1) if n > 1 else (x0 + x1) / 2
                label_str = str(label)
                x -= len(label_str) * 2.6
                self.text_draw(painter, label_str, x, y1 + 16, 9, self.muted)

        return v_min, v_max  # 把整理过的范围返回给调用方，保证画点用同一套范围

    @staticmethod
    def _nice_ticks(v_min, v_max, ticks=5):
        """把任意 v_min~v_max 归整成好看的整数级差刻度，比如 0/20/40/60/80/100"""
        import math
        span = (v_max - v_min) or 1
        raw_step = span / ticks
        magnitude = 10 ** math.floor(math.log10(raw_step))
        residual = raw_step / magnitude
        if residual > 5:
            step = 10 * magnitude
        elif residual > 2:
            step = 5 * magnitude
        elif residual > 1:
            step = 2 * magnitude
        else:
            step = magnitude
        nice_min = math.floor(v_min / step) * step
        nice_max = math.ceil(v_max / step) * step
        return nice_min, nice_max, step

    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        if delta > 0:
            self.zoom *= 1.2
        else:
            self.zoom /= 1.2

        self.zoom = max(1, min(self.zoom, 50))
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            dx = (event.pos().x() - self.last_mouse_pos.x()) // 2
            dy = event.y() - self.last_mouse_pos.y()
            self.offset -= int(dx)
            self.offset = max(0, self.offset)
            self.offset_x += dx
            self.offset_y += dy
            self.last_mouse_pos = event.pos()

            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False


# 折线图
class LineChart(ChartWidget):
    # 四个方向的独立边距：左侧要留给 Y 轴数值，底部要留给 X 轴类目文字
    MARGIN_LEFT = 46
    MARGIN_RIGHT = 20
    MARGIN_TOP = 20
    MARGIN_BOTTOM = 28

    def __init__(self, data: Sequence[float] | None = None, x_labels: Sequence[str] | None = None):
        super().__init__()
        self.line_color = QColor(self.PALETTE[0])
        self.data = list(data) if data else []
        self.x_labels = list(x_labels) if x_labels else []

    def set_data(self, data, x_labels=None):
        self.data = list(data) if data else []
        if x_labels is not None:
            self.x_labels = list(x_labels)
        self.update()

    def clear(self):
        self.set_data([])

    def draw(self, painter):
        self.text_draw(
            painter,
            f"{self.zoom:.1f}x",
            self.width() - 80,
            10,
            10,
            self.muted
        )
        if not self.data:
            self.draw_no_data(painter)
            return

        w, h = self.width(), self.height()
        total = len(self.data)
        visible = int(total / self.zoom)
        start = self.offset

        end = min(
            total,
            start + visible
        )
        raw_data = self.data[start:end]

        max_points = self.width() * 3
        if len(raw_data) > max_points:
            step = len(raw_data) / max_points
            data = [
                raw_data[int(i * step)]
                for i in range(max_points)
            ]
        else:
            data = raw_data

        n = len(data)
        has_x_labels = bool(self.x_labels)

        x0, x1 = self.MARGIN_LEFT, w - self.MARGIN_RIGHT
        y0 = self.MARGIN_TOP
        y1 = h - (self.MARGIN_BOTTOM if has_x_labels else self.MARGIN_BOTTOM - 12) - 12

        try:
            raw_min, raw_max = min(data), max(data)
        except ValueError: return
        v_min, v_max, _step = self._nice_ticks(raw_min, raw_max, ticks=5)

        def to_y(value):
            try: return y1 - (value - v_min) / (v_max - v_min) * (y1 - y0)
            except ZeroDivisionError: return 0

        def to_x(i):
            return x0 + i * (x1 - x0) / (n - 1) if n > 1 else (x0 + x1) / 2

        self.draw_axes(painter, (x0, y0, x1, y1), v_min, v_max,
                       x_labels=self.x_labels or None, n=n, y_ticks=5, nice=False)

        if n == 1:
            x, y = to_x(0), to_y(data[0])
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.line_color)
            painter.drawEllipse(QPointF(x, y), 5, 5)
            self.text_draw(painter, str(data[0]), x + 10, y + 4, 10)
            return

        points = [QPointF(to_x(i), to_y(v)) for i, v in enumerate(data)]

        # 面积渐变填充
        area = QPainterPath()
        area.moveTo(points[0].x(), y1)
        for p in points:
            area.lineTo(p)
        area.lineTo(points[-1].x(), y1)
        area.closeSubpath()
        fill_color = QColor(self.line_color)
        fill_color.setAlpha(35)
        painter.setPen(Qt.NoPen)
        painter.setBrush(fill_color)
        painter.drawPath(area)

        # 折线
        painter.setPen(QPen(self.line_color, 3, cap=Qt.RoundCap, join=Qt.RoundJoin))
        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for p in points[1:]:
            line_path.lineTo(p)
        painter.drawPath(line_path)

        max_i = data.index(raw_max)
        min_i = data.index(raw_min)
        painter.setPen(Qt.NoPen)
        for i, p in enumerate(points):
            if i in (max_i, min_i):
                painter.setPen(QPen(Qt.white, 2))
                painter.setBrush(self.line_color)
                painter.drawEllipse(p, 6, 6)
                painter.setPen(Qt.NoPen)
            else:
                painter.setBrush(self.line_color)
                painter.drawEllipse(p, 4, 4)


# 饼图
class PieChart(ChartWidget):
    def __init__(self, data: Sequence[float] | None = None, labels: Sequence[str] | None = None):
        super().__init__()
        self.colors = self.PALETTE
        self.data = list(data) if data else []
        self.labels = list(labels) if labels else []

    def set_data(self, data, labels=None):
        self.data = list(data) if data else []
        if labels is not None:
            self.labels = list(labels)
        self.update()

    def clear(self):
        self.set_data([])

    def draw(self, painter):
        total = sum(self.data) if self.data else 0
        if not self.data or total <= 0:
            self.draw_no_data(painter)
            return

        w, h = self.width(), self.height()
        # 饼图区域随控件大小自适应，右侧预留图例空间
        diameter = max(60, min(w * 0.55, h) - self.MARGIN)
        cx, cy = self.MARGIN + diameter / 2, h / 2
        rect = (cx - diameter / 2, cy - diameter / 2, diameter, diameter)

        start = 0
        painter.setPen(QPen(Qt.white, 2))
        legend_x = cx + diameter / 2 + 24
        legend_y = cy - diameter / 2 + 8

        for i, value in enumerate(self.data):
            fraction = value / total
            angle = int(fraction * 360 * 16)
            color = QColor(self.colors[i % len(self.colors)])
            painter.setBrush(color)
            painter.drawPie(*[int(v) for v in rect], start, angle)
            start += angle

            # 图例：色块 + 名称 + 百分比
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(int(legend_x), int(legend_y), 10, 10, 2, 2)
            label = self.labels[i] if i < len(self.labels) else f"项 {i + 1}"
            self.text_draw(painter, f"{label} {fraction * 100:.0f}%", legend_x + 16, legend_y + 10, 10)
            legend_y += 20
            painter.setPen(QPen(Qt.white, 2))


# 柱状图
class BarChart(ChartWidget):
    MARGIN_LEFT = 46
    MARGIN_RIGHT = 16
    MARGIN_TOP = 24
    MARGIN_BOTTOM = 36

    def __init__(
        self,
        data: Sequence[float] | None = None,
        x_labels: Sequence[str] | None = None,
        buckets: Sequence[tuple] | None = None,
        auto_bucket: bool = True
    ):
        super().__init__()

        self.bar_color = QColor("#9b59b6")

        self.raw_data = list(data) if data else []
        self.data = []
        self.x_labels = []

        self.buckets = buckets
        self.auto_bucket = auto_bucket

        if auto_bucket:
            self.set_raw_data(self.raw_data)
        else:
            self.data = self.raw_data
            self.x_labels = list(x_labels) if x_labels else []

    def set_data(
        self,
        data,
        x_labels=None
    ):
        self.raw_data = list(data) if data else []

        if self.auto_bucket:
            self._apply_bucket()
        else:
            self.data = self.raw_data

            if x_labels is not None:
                self.x_labels = list(x_labels)

        self.update()

    def set_raw_data(self, data):
        self.raw_data = list(data) if data else []

        self._apply_bucket()
        self.update()

    def set_buckets(self, buckets):
        """
        手动指定分桶
        """
        self.buckets = buckets
        self.auto_bucket = True
        self._apply_bucket()
        self.update()

    def _apply_bucket(self):
        if not self.raw_data:
            self.data = []
            self.x_labels = []
            return

        if self.buckets is None:
            self.buckets = self._auto_generate_buckets(
                self.raw_data
            )

        counts = []
        labels = []

        for low, high in self.buckets:
            count = sum(
                1
                for v in self.raw_data
                if low <= v <= high
            )

            counts.append(count)
            labels.append(
                f"{low}-{high}"
            )

        self.data = counts
        self.x_labels = labels

    def _auto_generate_buckets(self, values):
        vmin = min(values)
        vmax = max(values)
        if vmin >= 0 and vmax <= 100:
            return [
                (0,59),
                (60,79),
                (80,89),
                (90,100),
            ]
        elif vmin >= 0 and vmax <= 150:
            return [
                (0,89),
                (90,104),
                (105,119),
                (120,129),
                (130,150)
            ]

        import math
        count = min(
            8,
            max(
                4,
                int(math.sqrt(len(values)))
            )
        )

        span = vmax - vmin
        step = math.ceil(
            span / count
        )
        buckets = []
        start = int(vmin)
        while start <= vmax:
            end = start + step - 1
            buckets.append(
                (
                    start,
                    end
                )
            )
            start = end + 1
        return buckets

    def clear(self):
        self.set_data([])

    def draw(self, painter):
        if not self.data or max(self.data) <= 0:
            self.draw_no_data(painter)
            return

        w,h = self.width(), self.height()

        n = len(self.data)
        x0 = self.MARGIN_LEFT
        x1 = w - self.MARGIN_RIGHT

        y0 = self.MARGIN_TOP
        y1 = h - self.MARGIN_BOTTOM

        max_value = max(self.data)
        v_min = 0
        v_max = max_value * 1.15

        self.draw_axes(
            painter,
            (
                x0,
                y0,
                x1,
                y1
            ),
            v_min,
            v_max,
            x_labels=self.x_labels,
            n=n,
            center_ticks=True
        )
        slot = (
            x1-x0
        ) / n
        bar_width = min(
            50,
            slot*0.65
        )
        gap = slot-bar_width
        painter.setPen(Qt.NoPen)

        for i,value in enumerate(self.data):
            height = (
                value /
                v_max *
                (y1-y0)
            )

            x = (
                x0+
                i*slot+
                gap/2
            )

            y = y1-height

            painter.setBrush(
                self.bar_color
            )
            painter.drawRoundedRect(
                int(x),
                int(y),
                int(bar_width),
                int(height),
                5,
                5
            )

            self.text_draw(
                painter,
                str(value),
                x+bar_width/2-5,
                y-6,
                9
            )

# 矩形热力图
class RectChart(ChartWidget):
    def __init__(self, data: Sequence[Sequence[float]] | None = None):
        super().__init__()
        self.data = [list(row) for row in data] if data else []

    def set_data(self, data):
        self.data = [list(row) for row in data] if data else []
        self.update()

    def clear(self):
        self.set_data([])

    def draw(self, painter):
        if not self.data or not any(self.data):
            self.draw_no_data(painter)
            return

        rows = len(self.data)
        cols = max(len(x) for x in self.data)

        w, h = self.width(), self.height()

        margin = 30

        available_w = w - margin * 2
        available_h = h - margin * 2

        base_cell = min(
            available_w / cols,
            available_h / rows
        )

        if base_cell >= 18:
            cell = 18

        elif base_cell >= 10:
            cell = 10

        else:
            cell = max(2, base_cell)

        cell *= self.zoom
        start_x = self.offset_x + margin
        start_y = self.offset_y + margin
        painter.setPen(Qt.NoPen)
        painter.save()
        painter.setClipRect(
            0,
            0,
            w,
            h
        )

        for r, row in enumerate(self.data):
            y = start_y + r * cell

            if y > h or y + cell < 0:
                continue

            for c, value in enumerate(row):
                x = start_x + c * cell
                if x > w or x + cell < 0:
                    continue

                if value is None:
                    continue

                value = max(
                    0,
                    min(100, value)
                )

                t = max(0.0, min(1.0, value / 100.0))
                hue = int(120 * t)
                color = QColor.fromHsl(hue, 255, 128)

                painter.setBrush(color)
                painter.drawRect(
                    int(x),
                    int(y),
                    int(cell - 1),
                    int(cell - 1)
                )

                if cell >= 25:
                    painter.setFont(QFont("Microsoft YaHei", 12))
                    text_color = Qt.white if t < 0.4 else Qt.black
                    painter.setPen(text_color)
                    painter.drawText(
                        QRectF(x, y, cell, cell),
                        Qt.AlignCenter,
                        str(value)
                    )
                    painter.setPen(Qt.NoPen)

        painter.restore()
        self.text_draw(
            painter,
            f"{self.zoom:.1f}x",
            w - 40,
            20,
            10,
            self.muted
        )
