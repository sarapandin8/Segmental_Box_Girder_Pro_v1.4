from __future__ import annotations

import plotly.graph_objects as go

from visualization.figure_system import (
    apply_engineering_figure_layout,
    figure_view_badge_text,
    normalize_figure_view_mode,
    plotly_config_for_view_mode,
)


def test_global_figure_view_config_modes_are_distinct():
    assert normalize_figure_view_mode("Interactive review") == "interactive"
    assert normalize_figure_view_mode("Report preview") == "report"
    assert plotly_config_for_view_mode("Interactive review")["displayModeBar"] is True
    assert plotly_config_for_view_mode("Report preview")["displayModeBar"] is False
    assert "toolbar on" in figure_view_badge_text("Interactive review")
    assert "toolbar hidden" in figure_view_badge_text("Report preview")


def test_apply_engineering_figure_layout_sets_common_axes_and_background():
    fig = go.Figure()
    fig.add_scatter(x=[0, 1], y=[0, 1], name="line")
    apply_engineering_figure_layout(fig, title="Test figure", x_title="x", y_title="y")
    assert fig.layout.paper_bgcolor == "#ffffff"
    assert fig.layout.plot_bgcolor == "#ffffff"
    assert fig.layout.xaxis.title.text == "x"
    assert fig.layout.yaxis.title.text == "y"
    assert fig.layout.xaxis.showgrid is True
    assert fig.layout.yaxis.showgrid is True
