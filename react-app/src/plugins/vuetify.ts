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
                    error: "#AD0022",
                    success: "#1E9646",
                    primary: "#D9B3FF",
                    secondary: "#652C9E",
                    background: "#ffffff",
                    warning: "#FFD700",
                    surface: "#F5F5F7",
                    surfacedark: "#F2F2F2",
                    surfaceBorder: "#C9BCD9",
                    navbar: "#F7EFFF",
                    titleGradientFrom: "#E226B6",
                    titleGradientTo: "#652C9E",
                    secondaryTextGradientFrom: "#487395",
                    secondaryTextGradientTo: "#183D5B",
                    accent: "#0071E3",
                    contrast: "#652C9E",
                },
            },
            dark: {
                dark: true,
                colors: {
                    error: "#FFA8BA",
                    success: "#69D791",
                    primary: "#AF7DE0",
                    secondary: "#7C52A5",
                    background: "#1A0A28",
                    warning: "#FFE068",
                    navbar: "#231035",
                    surface: "#26133A",
                    surfaceBorder: "#4E3E62",
                    titleGradientFrom: "#D2AAE0",
                    titleGradientTo: "#7D3AC1",
                    secondaryTextGradientFrom: "#A9CAEF",
                    secondaryTextGradientTo: "#3AACEE",
                    accent: "#0071E3",
                    contrast: "#D2AAE0",
                },
            },
        },
    },
});
