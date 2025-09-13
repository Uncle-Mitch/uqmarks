<template>
    <v-container class="text-center pa-5 app-container" fluid>
        <PageTitle />
        <v-row justify="center" class="mt-8">
            <v-col cols="12" md="8">
                <CourseSearch :semester-options="semesterOptions" />
            </v-col>
        </v-row>
    </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import CourseSearch from "../components/CourseSearch.vue";
import PageTitle from "../components/PageTitle.vue";
import { getWith1DayExpiry, setWith1DayExpiry } from "../utils/localStorageRetrieval.ts";

const baseUrl = import.meta.env.VITE_API_BASE_URL;
const semesterOptions = ref<Array<{ value: string; label: string }>>([]);
onMounted(async () => {
    try {
        const cached = getWith1DayExpiry("semesterOptions");
        if (cached) {
            semesterOptions.value = JSON.parse(cached);
            return;
        }
        const response = await fetch(`${baseUrl}/api/semesters/`);
        if (!response.ok) throw new Error("Failed to fetch semesters");
        const data = await response.json();
        semesterOptions.value = data;
        setWith1DayExpiry("semesterOptions", JSON.stringify(data));
    } catch (e) {
        semesterOptions.value = [];
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
