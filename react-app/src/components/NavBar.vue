<template>
    <v-navigation-drawer v-model="sidebar" app temporary>
        <v-list>
            <v-list-item v-for="item in menuItems" :key="item.title" :to="item.path">
                {{ item.title }}
            </v-list-item>
        </v-list>
    </v-navigation-drawer>

    <v-toolbar app :color="navbarColor" flat class="px-0">
        <span class="d-md-none">
            <v-btn icon @click="sidebar = true">
                <v-icon class="fas fa-bars" style="font-size: 20px" />
            </v-btn>
        </span>
        <div class="d-flex align-center" style="gap: 16px">
            <router-link to="/" style="align-items: center">
                <GradientText
                    :from="theme.global.current.value.colors.titleGradientFrom"
                    :to="theme.global.current.value.colors.titleGradientTo"
                    tag="h1"
                    class="text-primary font-weight-bold px-2"
                >
                    UQMARKS
                </GradientText>
            </router-link>
            <div class="d-none d-md-flex" style="gap: 8px">
                <v-btn v-for="item in menuItems" :key="item.title" :to="item.path" variant="text" class="nav-btn">
                    {{ item.title }}
                </v-btn>
            </div>
        </div>
        <v-spacer />
        <v-btn icon @click="toggleTheme">
            <v-icon>{{ isDark ? "fas fa-sun" : "fas fa-moon" }}</v-icon>
        </v-btn>
    </v-toolbar>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useTheme } from "vuetify";
import logo from "@/assets/images/uqmarks_logo.png";
import GradientText from "./GradientText.vue";

const route = useRoute();
const tab = ref(route.path);
const sidebar = ref(false);
const theme = useTheme();
const isDark = ref(theme.global.current.value.dark);
const navbarColor = computed(() => theme.global.current.value.colors.navbar);

function toggleTheme() {
    theme.global.name.value = theme.global.current.value.dark ? "light" : "dark";
    isDark.value = theme.global.current.value.dark;
}

const menuItems = [
    { title: "Grade Calculator", path: "/" },
    { title: "Quiz Calculator", path: "/quiz" },
    { title: "Analytics", path: "/analytics" },
];

watch(
    () => route.path,
    (newPath) => {
        tab.value = newPath;
    },
);
</script>

<style scoped>
.nav-btn {
    &:hover {
        background-color: #b266ff !important;
    }
}

.sidebar {
    background-color: #48206c;
}
</style>
