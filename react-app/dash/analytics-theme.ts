// Generated into assets/analytics-theme.js by npm run build:dash. Edit this source.
(() => {
    type Theme = "light" | "dark";
    interface ThemeMessage {
        type: "uqmarks:theme";
        theme: Theme;
    }
    interface PlotlyChart extends HTMLElement {
        layout?: { paper_bgcolor?: string };
    }
    interface PlotlyApi {
        relayout(chart: PlotlyChart, layout: Record<string, string>): Promise<unknown>;
    }
    const plotlyWindow = window as Window & { Plotly?: PlotlyApi };
    function isThemeMessage(data: unknown): data is ThemeMessage {
        return (
            typeof data === "object" &&
            data !== null &&
            "type" in data &&
            data.type === "uqmarks:theme" &&
            "theme" in data &&
            (data.theme === "light" || data.theme === "dark")
        );
    }
    let scheduled = false;
    const parentOrigin = document.referrer ? new URL(document.referrer).origin : window.location.origin;
    function updateCharts() {
        scheduled = false;
        const plotly = plotlyWindow.Plotly;
        if (!plotly) return;
        const css = getComputedStyle(document.documentElement);
        const color = (name: string) => css.getPropertyValue(`--analytics-${name}`).trim();
        document.querySelectorAll<PlotlyChart>(".js-plotly-plot").forEach((chart) => {
            if (!chart.layout || chart.layout.paper_bgcolor === color("surface")) return;
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
        if (scheduled) return;
        scheduled = true;
        requestAnimationFrame(updateCharts);
    }
    window.addEventListener("message", (event: MessageEvent<unknown>) => {
        if (event.source !== window.parent || event.origin !== parentOrigin) return;
        if (!isThemeMessage(event.data)) return;
        document.documentElement.dataset.bsTheme = event.data.theme;
        schedule();
    });
    function init() {
        new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
        schedule();
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
})();
