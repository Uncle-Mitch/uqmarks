<template>
    <v-navigation-drawer v-model="sidebar" app temporary location="right">
        <v-list>
            <v-list-item v-for="item in menuItems" :key="item.title" :to="item.path">
                {{ item.title }}
            </v-list-item>
        </v-list>
    </v-navigation-drawer>

    <v-toolbar app :color="navbarColor" flat class="px-0">
        <div class="d-flex align-center" style="gap: 12px">
            <v-btn
                @click="navigateHome"
                style="align-items: center"
                active-class=""
                variant="text"
                class="nav-btn ml-2"
                rounded="xl"
            >
                <GradientText
                    :from="theme.global.current.value.colors.titleGradientFrom"
                    :to="theme.global.current.value.colors.titleGradientTo"
                    tag="h1"
                    class="text-primary font-weight-bold px-2"
                >
                    UQMARKS
                </GradientText>
            </v-btn>
            <div class="d-none d-md-flex" style="gap: 8px">
                <v-btn
                    v-for="item in menuItems"
                    :key="item.title"
                    :to="item.path"
                    variant="text"
                    class="nav-btn"
                    rounded="xl"
                    :class="{ 'v-btn--active': item.title === 'Grades' && isGradeCalculatorActive }"
                >
                    {{ item.title }}
                </v-btn>
            </div>
        </div>
        <v-spacer />
        <v-btn icon @click="toggleTheme">
            <v-icon>{{ isDark ? "fas fa-sun" : "fas fa-moon" }}</v-icon>
        </v-btn>
        <span class="d-md-none">
            <v-btn icon @click="toggleSidebar">
                <v-icon class="fas fa-bars" style="font-size: 20px" />
            </v-btn>
        </span>
    </v-toolbar>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useTheme } from "vuetify";
import GradientText from "./GradientText.vue";
import { useBreakpoints } from "@vueuse/core";

const route = useRoute();
const tab = ref(route.path);
const sidebar = ref(false);
const theme = useTheme();
const isDark = ref(theme.global.current.value.dark);
const navbarColor = computed(() => theme.global.current.value.colors.navbar);
const router = useRouter();

onMounted(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
        theme.global.name.value = savedTheme === "dark" ? "dark" : "light";
        isDark.value = theme.global.current.value.dark;
    } else {
        theme.global.name.value = "dark";
    }
});

function toggleTheme() {
    theme.global.name.value = theme.global.current.value.dark ? "light" : "dark";
    isDark.value = theme.global.current.value.dark;
    localStorage.setItem("theme", isDark.value ? "dark" : "light");
}

const breakpoints = useBreakpoints({
    mobile: 0,
    tablet: 600,
    desktop: 1024,
});

const isMobile = computed(() => breakpoints.smallerOrEqual("tablet").value);

function toggleSidebar() {
    if (isMobile.value) {
        sidebar.value = !sidebar.value;
    }
}
function navigateHome() {
    router.push("/");
}

const menuItems = [
    { title: "Grades", path: "/" },
    { title: "Quizzes", path: "/quiz" },
    { title: "Analytics", path: "/analytics" },
];

const isGradeCalculatorActive = computed(() => {
    return route.path === "/" || route.path === "/course";
});

watch(
    () => route.path,
    (newPath) => {
        tab.value = newPath;
    },
);
</script>

<style lang="scss" scoped>
:deep(.v-btn .v-btn__content) {
    text-transform: none !important;
}
:deep(.v-btn--active) {
    color: #ffffff !important;
    background-color: rgb(var(--v-theme-accent)) !important;
}
.sidebar {
    background-color: #48206c;
}
</style>
