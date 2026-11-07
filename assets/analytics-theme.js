"use strict";
// Generated into assets/analytics-theme.js by npm run build:dash. Edit this source.
(() => {
    const plotlyWindow = window;
    function isThemeMessage(data) {
        return (typeof data === "object" &&
            data !== null &&
            "type" in data &&
            data.type === "uqmarks:theme" &&
            "theme" in data &&
            (data.theme === "light" || data.theme === "dark"));
    }
    let scheduled = false;
    const parentOrigin = document.referrer ? new URL(document.referrer).origin : window.location.origin;
    function updateCharts() {
        scheduled = false;
        const plotly = plotlyWindow.Plotly;
        if (!plotly)
            return;
        const css = getComputedStyle(document.documentElement);
        const color = (name) => css.getPropertyValue(`--analytics-${name}`).trim();
        document.querySelectorAll(".js-plotly-plot").forEach((chart) => {
            if (!chart.layout || chart.layout.paper_bgcolor === color("surface"))
                return;
            void plotly.relayout(chart, {
                paper_bgcolor: color("surface"),
                plot_bgcolor: color("surface"),
                "font.color": color("muted"),
                "title.font.color": color("text"),
                "xaxis.gridcolor": color("border"),
                "yaxis.gridcolor": color("border"),
                "xaxis.zerolinecolor": color("border"),
                "yaxis.zerolinecolor": color("border"),
                "hoverlabel.bgcolor": color("surface"),
                "hoverlabel.bordercolor": color("border"),
                "hoverlabel.font.color": color("text"),
            });
        });
    }
    function schedule() {
        if (scheduled)
            return;
        scheduled = true;
        requestAnimationFrame(updateCharts);
    }
    window.addEventListener("message", (event) => {
        if (event.source !== window.parent || event.origin !== parentOrigin)
            return;
        if (!isThemeMessage(event.data))
            return;
        document.documentElement.dataset.bsTheme = event.data.theme;
        schedule();
    });
    function init() {
        new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
        schedule();
    }
    if (document.readyState === "loading")
        document.addEventListener("DOMContentLoaded", init);
    else
        init();
})();
