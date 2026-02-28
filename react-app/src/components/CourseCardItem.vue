<template>
    <v-card elevation="2" rounded="lg" class="course-card">
        <div
            class="course-card-header cursor-pointer"
            role="button"
            tabindex="0"
            @click="emit('toggle-collapse')"
            @keydown.enter.prevent="emit('toggle-collapse')"
            @keydown.space.prevent="emit('toggle-collapse')"
        >
            <div class="text-left d-flex align-baseline ga-3 flex-wrap">
                <div class="text-h6 font-weight-bold">{{ card.courseCode }}</div>
                <div class="text-caption text-medium-emphasis">{{ card.semesterLabel }}</div>
            </div>
            <div class="d-flex align-center justify-end ga-3 flex-nowrap">
                <v-btn
                    variant="text"
                    density="compact"
                    size="x-small"
                    icon
                    class="card-icon-btn remove-card-btn"
                    aria-label="Remove course card"
                    title="Remove"
                    @click.stop="emit('remove-card')"
                >
                    <v-icon icon="fas fa-trash" size="18" />
                </v-btn>
                <v-btn
                    variant="text"
                    density="compact"
                    size="x-small"
                    icon
                    class="card-icon-btn"
                    :aria-label="card.collapsed ? 'Expand course card' : 'Collapse course card'"
                    :title="card.collapsed ? 'Expand' : 'Collapse'"
                    @click.stop="emit('toggle-collapse')"
                >
                    <v-icon :icon="card.collapsed ? 'fas fa-chevron-down' : 'fas fa-chevron-up'" size="18" />
                </v-btn>
            </div>
        </div>

        <v-expand-transition>
            <div v-show="!card.collapsed">
                <v-divider class="mt-2 mb-3" />

                <v-row justify="center" v-if="card.loading">
                    <v-col cols="12">
                        <v-skeleton-loader type="article"></v-skeleton-loader>
                    </v-col>
                </v-row>

                <v-row justify="center" v-if="!card.validInput && !card.loading">
                    <v-col cols="12">
                        <CourseProfileUrlInput
                            :courseCode="card.courseCode"
                            :semesterId="card.semesterId"
                            :semesterOptions="semesterOptions"
                            :url="card.courseProfileUrl"
                            :error-message="card.searchError"
                            :submit-mode="'emit'"
                            @submit-url="(payload) => emit('submit-profile-url', payload.courseProfileUrl)"
                        />
                    </v-col>
                </v-row>

                <v-row justify="center" v-if="card.searchError && !card.validInput && !card.loading">
                    <v-col cols="12">
                        <v-alert
                            elevation="2"
                            prominent
                            color="warning"
                            class="text-left d-flex align-center font-weight-bold"
                        >
                            <template #prepend>
                                <v-icon icon="fas fa-exclamation-triangle" class="warning-icon" />
                            </template>
                            <span>{{ card.searchError }}</span>
                        </v-alert>
                    </v-col>
                </v-row>

                <v-row justify="center" v-if="card.validInput">
                    <v-col cols="12">
                        <v-sheet elevation="2" rounded="lg" class="table-wrapper text-start">
                            <v-data-table
                                :items="card.dataSource"
                                :headers="headers"
                                hide-default-footer
                                class="assessment-table"
                                density="compact"
                                :row-props="assessmentRowProps"
                                :loading="card.loading"
                                items-per-page="-1"
                            >
                                <template #header.weight>
                                    <div class="d-flex align-center">
                                        <span>Weight</span>
                                        <v-icon
                                            @click="toggleWeights"
                                            class="cursor-pointer ml-2"
                                            :aria-label="card.editingWeights ? 'Confirm Weights' : 'Edit Weights'"
                                            :title="card.editingWeights ? 'Confirm Weights' : 'Edit Weights'"
                                            size="x-small"
                                            color="accent"
                                        >
                                            {{ card.editingWeights ? "fas fa-check" : "fas fa-pencil" }}
                                        </v-icon>
                                    </div>
                                </template>
                                <template #loading>
                                    <v-skeleton-loader type="table-row@4"></v-skeleton-loader>
                                </template>
                                <template #item.weight="{ item, index }">
                                    <div class="d-flex justify-start align-center">
                                        <span v-if="!card.editingWeights">{{ item.weight }}</span>
                                        <v-text-field
                                            v-if="card.editingWeights"
                                            v-model="item.weight"
                                            hide-details
                                            density="compact"
                                            @update:model-value="
                                                (value) => handleWeightChange(index, String(value ?? ''))
                                            "
                                            variant="outlined"
                                        />
                                        <v-icon
                                            v-if="!item.validWeight"
                                            class="ml-2"
                                            aria-label="Invalid weight"
                                            title="Invalid weight"
                                            size="x-small"
                                            color="error"
                                        >
                                            fas fa-circle-exclamation
                                        </v-icon>
                                    </div>
                                </template>
                                <template #item.score="{ item, index }">
                                    <v-text-field
                                        v-model="item.score"
                                        placeholder="90, 90%, 9/10"
                                        class="score-input"
                                        hide-details
                                        density="compact"
                                        :disabled="!item.enabled || !item.validWeight"
                                        @update:model-value="(value) => handleScoreChange(index, String(value ?? ''))"
                                        variant="outlined"
                                    />
                                </template>
                                <template #item.enabled="{ item }">
                                    <v-container class="pa-0 table-switch-container">
                                        <v-switch
                                            v-model="item.enabled"
                                            :disabled="!item.validWeight"
                                            inset
                                            density="compact"
                                            hide-details
                                            color="secondary"
                                            @update:model-value="handleEnabledChange"
                                            class="table-switch"
                                        />
                                    </v-container>
                                </template>
                            </v-data-table>
                        </v-sheet>
                    </v-col>
                </v-row>

                <v-row justify="center" class="mt-4" v-if="!card.weightValid && card.validInput && !card.loading">
                    <v-col cols="12">
                        <v-alert
                            elevation="2"
                            prominent
                            color="warning"
                            class="text-left d-flex align-center font-weight-bold"
                        >
                            <template #prepend>
                                <v-icon icon="fas fa-exclamation-triangle" class="warning-icon" />
                            </template>
                            <span> The assessment items do not add up to 100%. </span>
                        </v-alert>
                    </v-col>
                </v-row>

                <CourseCardResults
                    :card="card"
                    :gradeCutoffs="gradeCutoffs"
                    :gradeOptions="gradeOptions"
                    :fromColor="fromColor"
                    :toColor="toColor"
                    :getTimelineScore="getTimelineScore()"
                    :getDebouncedImpossibleStart="getDebouncedImpossibleStart()"
                    :clampPercent="clampPercent"
                    :isGradePassed="isGradePassed"
                    :targetSummary="getCardTargetSummary()"
                    @open-details="emit('open-details')"
                    @set-target-grade="setTargetGrade"
                />
            </div>
        </v-expand-transition>
    </v-card>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { useBreakpoints } from "@vueuse/core";
import CourseProfileUrlInput from "./CourseProfileUrlInput.vue";
import CourseCardResults from "./CourseCardResults.vue";
import type { CourseCard, GradeCutoff, SemesterOption, TargetSummary } from "../types/home";
import {
    calculateImpossibleStart,
    calculateTotalScore,
    clampPercent,
    getTargetSummary,
    isWeightValid,
    parseWeight,
} from "../utils/courseCardCalculations";

const props = defineProps<{
    card: CourseCard;
    semesterOptions: SemesterOption[];
    gradeCutoffs: GradeCutoff[];
    gradeOptions: number[];
    fromColor: string;
    toColor: string;
}>();

const emit = defineEmits<{
    (event: "remove-card"): void;
    (event: "toggle-collapse"): void;
    (event: "open-details"): void;
    (event: "submit-profile-url", url: string): void;
    (event: "persist-state"): void;
}>();

const { card, semesterOptions, gradeCutoffs, gradeOptions, fromColor, toColor } = props;

const breakpoints = useBreakpoints({
    mobile: 0,
    tablet: 600,
    desktop: 1024,
});
const isMobile = breakpoints.smallerOrEqual("tablet");

const headers = computed(() => {
    const baseHeaders = [
        { title: "Assessment", value: "assessment", width: "30%" },
        { title: "Weight", value: "weight", width: isMobile.value ? "15%" : "20%" },
    ];

    baseHeaders.push({
        title: "Your Score",
        value: "score",
        width: !isMobile.value || !card.editingWeights ? (isMobile.value ? "30%" : "20%") : "5%",
    });

    baseHeaders.push({
        title: "",
        value: "enabled",
        width: isMobile.value ? "15%" : "10%",
    });

    return baseHeaders;
});

function assessmentRowProps(row: any) {
    if (row.item?.enabled === undefined) return {};
    return { class: row.item.enabled ? "" : "disabled-row" };
}

const timelineScore = ref(card.totalScore);
const timelineImpossibleStart = ref(calculateImpossibleStart(card.dataSource));
let timelineTimer: ReturnType<typeof setTimeout> | null = null;

function scheduleTimelineUpdate() {
    if (timelineTimer) {
        clearTimeout(timelineTimer);
    }

    timelineTimer = setTimeout(() => {
        timelineScore.value = card.totalScore;
        timelineImpossibleStart.value = calculateImpossibleStart(card.dataSource);
        timelineTimer = null;
    }, 500);
}

function recalculateCard() {
    const { score } = calculateTotalScore(card.dataSource);
    card.totalScore = score;
    card.weightValid = isWeightValid(card.dataSource);
    scheduleTimelineUpdate();
}

function handleScoreChange(index: number, value: string) {
    card.dataSource[index].score = value;
    recalculateCard();
    emit("persist-state");
}

function handleWeightChange(index: number, value: string) {
    card.dataSource[index].validWeight = value.length > 0 && !!parseWeight(value);
    card.dataSource[index].weight = value;
    recalculateCard();
    emit("persist-state");
}

function handleEnabledChange() {
    recalculateCard();
    emit("persist-state");
}

function toggleWeights() {
    card.editingWeights = !card.editingWeights;
}

function setTargetGrade(grade: number) {
    if (card.targetGrade === grade) return;
    card.targetGrade = grade;
    emit("persist-state");
}

function getTimelineScore() {
    return timelineScore.value;
}

function getDebouncedImpossibleStart() {
    return timelineImpossibleStart.value;
}

function isGradePassed(cutoff: number) {
    return clampPercent(getTimelineScore()) >= cutoff;
}

function getCardTargetSummary(): TargetSummary {
    return getTargetSummary(card.dataSource, card.targetGrade, gradeCutoffs);
}

recalculateCard();

onBeforeUnmount(() => {
    if (timelineTimer) {
        clearTimeout(timelineTimer);
    }
});
</script>

<style lang="scss" scoped>
.course-card {
    padding: 0.8rem 1rem;
    border: 1px solid rgba(var(--v-theme-surfaceBorder), 0.7);
}

.course-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
}

.header-divider {
    margin-top: 0.5rem;
}

.card-icon-btn {
    color: rgba(var(--v-theme-on-surface), 0.82) !important;
    min-width: 0 !important;
    width: 20px;
    height: 20px;
    padding: 0 !important;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.remove-card-btn:hover {
    color: rgb(var(--v-theme-error)) !important;
}

:deep(.disabled-row) {
    background-color: var(--disabled-row-bg) !important;
}

:deep(.assessment-table thead th) {
    font-weight: 700 !important;
}

:deep(.assessment-table .v-data-table__th),
:deep(.assessment-table .v-data-table__td) {
    padding-top: 8px !important;
    padding-bottom: 8px !important;
}

:deep(.assessment-table) {
    --v-table-header-height: 28px;
}

:deep(.assessment-table thead .v-data-table__th) {
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    line-height: 1.1 !important;
}

:deep(.assessment-table .v-data-table-header__content) {
    min-height: 0 !important;
}

:deep(.assessment-table thead tr) {
    height: 28px !important;
}

:deep(.assessment-table .v-field) {
    --v-input-control-height: 32px;
}

:deep(.assessment-table .score-input .v-field) {
    --v-input-control-height: 28px;
}

:deep(.assessment-table .score-input .v-field__input) {
    min-height: 28px !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
}

.table-switch-container {
    height: 32px;
}

.table-switch {
    transform: scale(0.6);
    margin: 0;
}

@media (max-width: 600px) {
    .course-card {
        padding: 0.65rem 0.8rem;
    }

    :deep(.v-data-table__td),
    :deep(.v-data-table__th) {
        padding: 2px 4px !important;
    }
}
</style>
