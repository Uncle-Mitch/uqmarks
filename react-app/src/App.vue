<template>
    <v-app>
        <v-container fluid fill-height class="d-flex justify-center align-center pa-0">
            <v-main>
                <NavBar />
                <RouterView />
            </v-main>
        </v-container>
        <SiteFooter />
    </v-app>
</template>

<script setup lang="ts">
import { RouterView } from "vue-router";
import NavBar from "./components/NavBar.vue";
import SiteFooter from "./components/SiteFooter.vue";
</script>
