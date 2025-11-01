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
        defaultTheme: "dark",
        themes: {
            light: {
                dark: false,
                colors: {
                    error: "#F14668",
                    primary: "#D9B3FF",
                    secondary: "#652C9E",
                    background: "#FBFBFD",
                    warning: "#FFD700",
                    surface: "#F5F5F7",
                    surfacedark: "#D1C7E2",
                    navbar: "#F7EFFF",
                    titleGradientFrom: "#652C9E",
                    titleGradientTo: "#E226B6",
                    secondaryTextGradientFrom: "#183D5B",
                    secondaryTextGradientTo: "#487395",
                    accent: "#0071E3",
                },
            },
            dark: {
                dark: true,
                colors: {
                    error: "#F14668",
                    primary: "#AF7DE0",
                    secondary: "#7C52A5",
                    background: "#1A0A28",
                    warning: "#FFD700",
                    navbar: "#231035",
                    surface: "#26133A",
                    titleGradientFrom: "#7D3AC1",
                    titleGradientTo: "#D2AAE0",
                    secondaryTextGradientFrom: "#3AACEE",
                    secondaryTextGradientTo: "#A9CAEF",
                    accent: "#0071E3",
                },
            },
        },
    },
});
