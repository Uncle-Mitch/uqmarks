<template>
    <div>
        <GradientText
            :from="theme.global.current.value.colors.titleGradientFrom"
            :to="theme.global.current.value.colors.titleGradientTo"
            tag="h1"
            class="text-primary text-h3 font-weight-bold"
        >
            UQMARKS Grade Calculator
        </GradientText>
        <div v-if="announcement" class="text-h5 mt-3">
            {{ announcement }}
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { getWith1DayExpiry, setWith1DayExpiry } from "../utils/localStorageRetrieval.ts";
import { useTheme } from "vuetify";
import GradientText from "./GradientText.vue";

const announcement = ref("");
const baseUrl = import.meta.env.VITE_API_BASE_URL;
const theme = useTheme();

onMounted(async () => {
    try {
        const cached = getWith1DayExpiry("announcement");
        if (cached) {
            announcement.value = cached;
            return;
        }
        const response = await fetch(`${baseUrl}/api/announcement/`);
        if (!response.ok) throw new Error("Failed to fetch announcement");
        const data = await response.json();
        announcement.value = data.announcement ?? "";
        setWith1DayExpiry("announcement", announcement.value);
    } catch {
        announcement.value = "";
    }
});
</script>

<style lang="scss" scoped>
.page-title {
    color: #d9b3ff;
    margin-bottom: 2rem;
}

.app-container {
    height: 100vh;
}
</style>
