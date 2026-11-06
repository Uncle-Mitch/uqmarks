<template>
    <main class="analytics-page">
        <header class="analytics-header">
            <GradientText
                :from="theme.global.current.value.colors.titleGradientFrom"
                :to="theme.global.current.value.colors.titleGradientTo"
                tag="h1"
                class="page-heading"
                >Search Analytics</GradientText
            >
        </header>

        <nav class="analytics-navigation" aria-label="Analytics views">
            <div class="analytics-tab-track">
                <div class="analytics-tab-pill" :style="pillStyle" aria-hidden="true"></div>
                <v-btn-toggle v-model="tab" class="analytics-tabs" mandatory>
                    <v-btn value="home" variant="text" :ripple="false">Total Searches</v-btn>
                    <v-btn value="courses" variant="text" :ripple="false">Course Ranking</v-btn>
                    <v-btn value="hourly" variant="text" :ripple="false">Hourly Usage</v-btn>
                </v-btn-toggle>
            </div>
        </nav>

        <iframe
            ref="dashboardFrame"
            @load="syncDashboardTheme"
            v-if="!isMobile"
            :src="iframeSrc"
            title="Search analytics dashboard"
            class="analytics-frame"
        ></iframe>
        <div v-else class="analytics-mobile-message">Analytics is available on desktop and larger screens.</div>
    </main>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useBreakpoints } from "@vueuse/core";
import { useTheme } from "vuetify";
import GradientText from "../components/GradientText.vue";

const theme = useTheme();

const baseUrl = import.meta.env.VITE_API_BASE_URL;

const tab = ref("home");
const pillStyle = computed(() => ({
    transform: `translateX(${["home", "courses", "hourly"].indexOf(tab.value) * 100}%)`,
}));
const dashboardFrame = ref<HTMLIFrameElement>();
const dashboardTheme = computed(() => (theme.global.current.value.dark ? "dark" : "light"));
const iframeSrc = computed(() => `${baseUrl}/dash/${tab.value}`);
function syncDashboardTheme() {
    const frame = dashboardFrame.value;
    if (!frame) return;
    frame.contentWindow?.postMessage(
        { type: "uqmarks:theme", theme: dashboardTheme.value },
        new URL(frame.src, window.location.href).origin,
    );
}
watch(dashboardTheme, syncDashboardTheme);
const breakpoints = useBreakpoints({
    mobile: 0,
    tablet: 600,
    desktop: 1024,
});
const isMobile = breakpoints.smaller("tablet"); // < 600px
</script>

<style lang="scss" scoped>
.analytics-page {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    width: 100%;
    max-width: 1240px;
    margin: 0 auto;
    padding: 48px 28px 32px;
}

.analytics-header {
    margin-bottom: 32px;
    text-align: center;
}

.analytics-navigation {
    width: 100%;
    min-width: 0;
    margin-bottom: 28px;
}

.analytics-tab-track {
    display: grid;
    box-sizing: border-box;
    width: min(100%, 560px);
    padding: 0;
    border: 1px solid rgb(var(--v-theme-surfaceBorder));
    border-radius: 999px;
    background: rgb(var(--v-theme-surface));
}

.analytics-tab-pill {
    grid-area: 1 / 1;
    width: calc(100% / 3);
    border-radius: 999px;
    background: rgb(var(--v-theme-on-background));
    box-shadow: 0 2px 6px rgb(0 0 0 / 15%);
    transition: transform 240ms cubic-bezier(0.23, 1, 0.32, 1);
    pointer-events: none;
}

.analytics-tabs {
    grid-area: 1 / 1;
    position: relative;
    display: flex;
    width: 100%;
    height: auto !important;
    background: transparent;
    border-radius: 999px !important;
}

.analytics-tabs .v-btn {
    flex: 1 1 0;
    min-width: 0;
    height: 44px !important;
    padding: 0 12px;
    border-radius: 999px !important;
    text-transform: none;
    letter-spacing: 0;
    font-size: 16px;
    font-weight: 700;
    color: rgb(var(--v-theme-on-background), 0.7);
    transition: color 160ms ease;
}

.analytics-tabs .v-btn--active {
    color: rgb(var(--v-theme-background)) !important;
}

.analytics-tabs :deep(.v-btn__overlay) {
    opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
    .analytics-tab-pill,
    .analytics-tabs .v-btn {
        transition: none;
    }
}

.analytics-frame {
    display: block;
    width: 100%;
    min-width: 0;
    margin: 0;
    padding: 0;
    min-height: 720px;
    border: 0;
    color-scheme: v-bind(dashboardTheme);
}

.analytics-mobile-message {
    padding: 32px 16px;
    text-align: center;
    color: rgb(var(--v-theme-on-background), 0.65);
}

@media (max-width: 600px) {
    .analytics-page {
        padding: 32px 16px;
    }
    .analytics-tabs {
        display: flex;
    }
    .analytics-tabs .v-btn {
        padding: 0 12px;
        font-size: 16px;
    }
}
</style>
