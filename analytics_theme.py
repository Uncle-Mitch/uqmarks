"""Analytics colors matched to the normal app's Vuetify dark theme."""

COLORS = {
    "background": "#1A0A28",
    "surface": "#291E35",
    "border": "#493A56",
    "primary": "#AF7DE0",
    "secondary": "#7C52A5",
    "contrast": "#D2AAE0",
    "accent": "#0071E3",
    "text": "#FFFFFF",
}


def apply_chart_theme(fig):
    """Apply the same readable dark surfaces, axes and tooltips to every chart."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        height=440,
        margin=dict(l=64, r=32, t=80, b=64),
        title=dict(x=0.035, y=0.93, xanchor="left", font=dict(size=16, color="#F4EFF8")),
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", size=16, color="#C6BACF"),
        hoverlabel=dict(
            bgcolor=COLORS["background"],
            bordercolor=COLORS["border"],
            font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", size=16, color=COLORS["text"]),
        ),
    )
    fig.update_xaxes(tickfont_size=16, title_font_size=16, gridcolor="rgba(210,170,224,0.08)", zerolinecolor=COLORS["border"],
                     spikecolor=COLORS["contrast"])
    fig.update_yaxes(tickfont_size=16, title_font_size=16, gridcolor="rgba(210,170,224,0.08)", zerolinecolor=COLORS["border"])
    return fig
