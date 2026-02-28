<template>
    <v-dialog v-model="open" max-width="680">
        <v-card class="details-dialog-card">
            <div class="details-dialog-header">
                <div class="details-dialog-title">
                    Grade Breakdown: {{ props.selectedCard?.courseCode }} {{ props.selectedCard?.semesterLabel }}
                </div>
                <v-btn
                    variant="text"
                    density="compact"
                    size="x-small"
                    icon
                    class="text-medium-emphasis"
                    aria-label="Close details modal"
                    title="Close"
                    @click="open = false"
                >
                    <v-icon icon="fas fa-times" size="16" />
                </v-btn>
            </div>
            <v-sheet elevation="0" rounded="lg" class="text-start">
                <v-data-table
                    :items="props.rows"
                    :headers="props.resultsHeaders"
                    hide-default-footer
                    density="comfortable"
                    :row-props="props.rowProps"
                    class="results-table"
                    :loading="props.selectedCard?.loading ?? false"
                >
                    <template #loading>
                        <v-skeleton-loader type="table-row@7"></v-skeleton-loader>
                    </template>
                </v-data-table>
            </v-sheet>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { CourseCard, GradeDetailsRow } from "../types/home";

const props = defineProps<{
    modelValue: boolean;
    selectedCard: CourseCard | null;
    rows: GradeDetailsRow[];
    resultsHeaders: Array<{ title: string; value: string }>;
    rowProps: (row: any) => Record<string, string> | object;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: boolean): void;
}>();

const open = computed({
    get: () => props.modelValue,
    set: (value: boolean) => emit("update:modelValue", value),
});
</script>

<style lang="scss" scoped>
.details-dialog-card {
    padding: 0.75rem;
}

.details-dialog-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 0.4rem;
}

.details-dialog-title {
    font-size: 0.95rem;
    font-weight: 700;
    margin-bottom: 0;
}

:deep(.achieved-row) {
    background-color: var(--achieved-row-bg) !important;
}

:deep(.unobtainable-row) {
    background-color: var(--unobtainable-row-bg) !important;
}

:deep(.results-table thead th) {
    font-weight: 700 !important;
}
</style>
