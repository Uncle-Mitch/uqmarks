<template>
    <div>
        <div class="text-h3 font-weight-bold text-primary">UQMARKS Grade Calculator</div>
        <div v-if="announcement" class="text-h5 mt-3">
            {{ announcement }}
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getWith1DayExpiry, setWith1DayExpiry } from "../utils/localStorageRetrieval.ts";

const announcement = ref("");
const baseUrl = import.meta.env.VITE_API_BASE_URL;

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
