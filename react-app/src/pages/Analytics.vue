<template>
    <v-container class="text-center pa-5" fluid>
        <div class="text-h3 font-weight-bold text-primary">UQMARKS Search Analytics</div>
        <v-container fluid class="analytics-bg mt-6">
            <v-row justify="start">
                <v-tabs v-model="tab" class="custom-tabs" slider-color="##485fc7" align-tabs="start">
                    <v-tab value="home">Total Searches</v-tab>
                    <v-tab value="courses">Course Ranking</v-tab>
                    <v-tab value="hourly">Hourly Usage</v-tab>
                </v-tabs>
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

const baseUrl = import.meta.env.VITE_API_BASE_URL;

const tab = ref("home");
const iframeSrc = computed(() => `${baseUrl}/dash/${tab.value}`);
const breakpoints = useBreakpoints({
    mobile: 0,
    tablet: 600,
    desktop: 1024,
});
const isMobile = breakpoints.smaller("tablet"); // < 600px
</script>

<style lang="scss" scoped>
.custom-tabs {
    color: #000;
}
.custom-tabs .v-tab {
    text-transform: none !important;
    font-weight: 500;
    letter-spacing: normal;
    font-size: 1rem;
}

.custom-tabs .v-tab--selected {
    color: #485fc7 !important;
    font-weight: bold;
}

.analytics-bg {
    background: #f4eaff;
    border-radius: 18px;
    margin-top: 50px;
}
</style>
