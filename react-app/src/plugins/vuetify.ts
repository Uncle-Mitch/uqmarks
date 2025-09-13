import "@fortawesome/fontawesome-free/css/all.css";
import "vuetify/styles/main.css";
import "@/assets/style/style.scss";
import { createVuetify } from "vuetify";
import { aliases, fa } from "vuetify/iconsets/fa";

export const vuetify = createVuetify({
    icons: {
        defaultSet: "fa",
        aliases,
        sets: {
            fa,
        },
    },
    theme: {
        defaultTheme: "light",
        themes: {
            light: {
                dark: false,
                colors: {
                    error: "#F14668",
                    primary: "#D9B3FF",
                    secondary: "#B461FF",
                    background: "#48206C",
                    warning: "#FFD700",
                    surface: "#F4EAFF",
                },
            },
            dark: {
                dark: true,
                colors: {
                    error: "#F14668",
                    primary: "#D9B3FF",
                    secondary: "#6E32A8",
                    background: "#2D1443",
                    warning: "#FFD700",
                },
            },
        },
    },
});
