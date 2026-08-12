import math

from .. import get_translation
from .. import ui
from ..ui import stats

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QWidget
from PyQt5.Qt import QSizePolicy

HEATMAP_COLS = 10


class DashboardWidget(ui.PageWidget):
    def __init__(self):
        super().__init__(get_translation("ui.sub.dashboard"))

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        self.average_score = stats.StatCard(
            get_translation("ui.sub.dashboard.average_score"),
            0,
            0,
            self
        )
        self.pass_rate = stats.StatCard(
            get_translation("ui.sub.dashboard.pass_rate"),
            "0%",
            0,
            self
        )
        self.highest_score = stats.StatCard(
            get_translation("ui.sub.dashboard.highest_score"),
            0,
            0,
            self
        )
        self.total_students = stats.StatCard(
            get_translation("ui.sub.dashboard.total_students"),
            0,
            0,
            self
        )
        for card in (
            self.average_score,
            self.pass_rate,
            self.highest_score,
            self.total_students,
        ):
            card.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )
            cards_layout.addWidget(card)

        # 折线图：成绩走势（按学生顺序）
        self.trend_chart = stats.LineChart()

        # 柱状图：分数段人数分布
        self.distribution_chart = stats.BarChart()

        # 饼图：及格 / 不及格占比，用语义色区分
        self.status_chart = stats.PieChart()
        self.status_chart.colors = ["#2ecc71", "#e74c3c"]

        # 热力图：原始成绩铺成网格，一眼看出整体分布
        self.heatmap_chart = stats.RectChart()

        charts_layout = QGridLayout()
        charts_layout.setSpacing(12)
        charts_layout.addWidget(
            self._wrap_chart(get_translation("ui.sub.dashboard.score_trend"), self.trend_chart),
            0, 0
        )
        charts_layout.addWidget(
            self._wrap_chart(get_translation("ui.sub.dashboard.score_distribution"), self.distribution_chart),
            0, 1
        )
        charts_layout.addWidget(
            self._wrap_chart(get_translation("ui.sub.dashboard.pass_status"), self.status_chart),
            1, 0
        )
        charts_layout.addWidget(
            self._wrap_chart(get_translation("ui.sub.dashboard.score_heatmap"), self.heatmap_chart),
            1, 1
        )
        charts_layout.setRowStretch(0, 1)
        charts_layout.setRowStretch(1, 1)
        charts_layout.setColumnStretch(0, 1)
        charts_layout.setColumnStretch(1, 1)

        layout = self.get_content_layout()
        layout.addLayout(cards_layout)
        layout.addLayout(charts_layout, 1)

        # self.update_data([random.randint(0, 100) for _ in range(60)], 100)

    def _wrap_chart(self, title: str, widget: QWidget) -> QWidget:
        """给图表加一个统一样式的标题，图表本身自带白色圆角卡片背景"""
        container = QWidget(self)
        box = QVBoxLayout(container)
        box.setContentsMargins(2, 0, 2, 0)
        box.setSpacing(6)

        label = QLabel(title)
        label.setStyleSheet("font-size:13px; color:#7f8c8d; font-weight:bold;")
        box.addWidget(label)

        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        box.addWidget(widget, 1)
        return container

    def _score_heatmap_matrix(self, scores: list) -> list[list]:
        """把一维成绩列表铺成固定列数的网格，最后一行不足的用 None 占位（不绘制）"""
        cols = min(HEATMAP_COLS, len(scores)) or 1
        rows = math.ceil(len(scores) / cols)
        matrix = []
        for r in range(rows):
            row = scores[r * cols: (r + 1) * cols]
            row = row + [None] * (cols - len(row))
            matrix.append(row)
        return matrix

    def update_data(
            self,
            scores: list[int | float],
            max_score: int | float | None = None,
            previous_scores: list[int | float] | None = None
    ):
        """
        :param scores: 当前成绩数据
        :param max_score: 满分，计算及格线
        :param previous_scores: 用于计算趋势的数据
        """
        total = len(scores)

        if total == 0:
            self.average_score.update_value(0, 0)
            self.pass_rate.update_value("0%", 0)
            self.highest_score.update_value(0, 0)
            self.total_students.update_value(0, 0)

            self.trend_chart.clear()
            self.distribution_chart.clear()
            self.status_chart.clear()
            self.heatmap_chart.clear()
            return

        # 当前统计
        average = sum(scores) / total
        passed = sum(1 for s in scores if s >= int(max_score * 0.6))
        failed = total - passed
        pass_rate = passed / total * 100
        highest = max(scores)

        # 默认趋势
        avg_trend = 0
        pass_trend = 0
        high_trend = 0
        total_trend = 0

        # 如果存在上一组数据，计算变化
        if previous_scores:

            old_total = len(previous_scores)

            if old_total:
                old_average = sum(previous_scores) / old_total
                old_pass = (
                        sum(1 for s in previous_scores if s >= int(max_score * 0.6))
                        / old_total
                        * 100
                )
                old_highest = max(previous_scores)

                avg_trend = round(average - old_average, 1)
                pass_trend = round(pass_rate - old_pass, 1)
                high_trend = highest - old_highest
                total_trend = total - old_total

        # 更新统计卡
        self.average_score.update_value(
            round(average, 1),
            avg_trend
        )

        self.pass_rate.update_value(
            f"{pass_rate:.1f}%",
            pass_trend
        )

        self.highest_score.update_value(
            highest,
            high_trend
        )

        self.total_students.update_value(
            total,
            total_trend
        )

        # 图表使用当前数据
        self.trend_chart.set_data(scores)
        self.distribution_chart.set_data(scores)
        self.status_chart.set_data(
            [passed, failed],
            labels=[
                get_translation("ui.sub.dashboard.passed"),
                get_translation("ui.sub.dashboard.failed"),
            ],
        )
        self.heatmap_chart.set_data(
            self._score_heatmap_matrix(scores)
        )