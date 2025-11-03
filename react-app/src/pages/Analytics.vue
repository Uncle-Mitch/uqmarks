<template>
    <v-container class="text-center pa-5" fluid>
        <GradientText
            :from="theme.global.current.value.colors.titleGradientFrom"
            :to="theme.global.current.value.colors.titleGradientTo"
            tag="h1"
            class="text-primary text-h3 font-weight-bold"
        >
            Search Analytics
        </GradientText>
        <v-container fluid class="analytics-bg mt-6">
            <v-row justify="start">
                <v-btn-toggle v-model="tab" rounded="pill" class="pill-toggle" group>
                    <div class="pill-slider" :style="sliderStyle"></div>
                    <v-btn value="home" variant="flat" rounded="pill">Total Searches</v-btn>
                    <v-btn value="courses" variant="flat" rounded="pill">Course Ranking</v-btn>
                    <v-btn value="hourly" variant="flat" rounded="pill">Hourly Usage</v-btn>
                </v-btn-toggle>
            </v-row>

            <v-row justify="center" class="mt-6">
                <template v-if="!isMobile">
                    <iframe
                        :src="iframeSrc"
                        class="w-100"
                        style="min-height: 80vh; border: none; border-radius: 16px"
                    ></iframe>
                </template>
                <template v-else>
                    <div class="pa-8 text-center text-grey">
                        <div class="text-h6">Sorry, analytics view is only available on desktop or larger screens.</div>
                    </div>
                </template>
            </v-row>
        </v-container>
    </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useBreakpoints } from "@vueuse/core";
import { useTheme } from "vuetify";
import GradientText from "../components/GradientText.vue";

const baseUrl = import.meta.env.VITE_API_BASE_URL;

const tab = ref("home");
const iframeSrc = computed(() => `${baseUrl}/dash/${tab.value}?darkmode=${isDarkMode.value}`);
const breakpoints = useBreakpoints({
    mobile: 0,
    tablet: 600,
    desktop: 1024,
});
const isMobile = breakpoints.smaller("tablet"); // < 600px
const theme = useTheme();
const isDarkMode = computed(() => theme.global.current.value.dark);

const buttons = ["home", "courses", "hourly"];
const sliderStyle = computed(() => {
    const index = buttons.indexOf(tab.value);
    const percent = 100 / buttons.length;
    return {
        left: `${index * percent}%`,
        width: `${percent}%`,
    };
});
</script>

<style lang="scss" scoped>
.custom-tabs .v-tab {
    text-transform: none !important;
    font-weight: 500;
    letter-spacing: normal;
    font-size: 1rem;
}

.custom-tabs .v-tab--selected {
    color: #9eace9 !important;
    font-weight: bold;
}

.analytics-bg {
    background: --v-theme-surface;
    border-radius: 18px;
    margin-top: 50px;
}

.pill-toggle {
    background-color: rgb(var(--v-theme-surfacedark));
    padding: 4px;
    border-radius: 9999px;
}

.pill-toggle .v-btn {
    background-color: transparent !important;
    color: var(--v-theme-dark) !important;
    text-transform: none;
    font-weight: 500;
}

.pill-toggle .v-btn.v-btn--active {
    background-color: rgb(var(--v-theme-accent)) !important;
    color: white !important;
    box-shadow: none !important;
}
</style>
