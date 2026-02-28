<template>
    <v-row justify="center" class="mt-6" v-if="props.card.validInput">
        <v-col cols="12">
            <v-sheet elevation="2" rounded="lg" class="goal-card text-start">
                <div class="d-flex align-center justify-space-between ga-3 flex-wrap mb-2">
                    <div class="d-flex align-baseline ga-2 total-score">
                        <span class="text-overline text-medium-emphasis">Total Score</span>
                        <GradientText
                            v-bind="totalScoreGradientProps"
                            class="text-h5 font-weight-bold"
                            style="line-height: 1"
                        >
                            {{ props.card.totalScore.toFixed(2) }}%
                        </GradientText>
                    </div>
                    <v-btn variant="flat" size="x-small" color="accent" @click.stop="emit('open-details')">
                        More details
                    </v-btn>
                </div>
                <div class="grade-timeline" aria-label="Grade timeline">
                    <div class="grade-track"></div>
                    <div
                        class="grade-progress"
                        :style="{ width: `${props.clampPercent(props.getTimelineScore)}%` }"
                    ></div>
                    <div
                        class="grade-unreachable-zone"
                        :style="{
                            left: `${props.getDebouncedImpossibleStart}%`,
                            opacity: props.getDebouncedImpossibleStart < 100 ? 1 : 0,
                        }"
                    ></div>
                    <div
                        v-for="grade in props.gradeCutoffs"
                        :key="`timeline-${grade.grade}`"
                        class="grade-marker"
                        :class="{
                            passed: props.isGradePassed(grade.cutoff),
                            start: grade.cutoff === 0,
                            target: grade.grade === props.card.targetGrade,
                            targetPassed: grade.grade === props.card.targetGrade && props.isGradePassed(grade.cutoff),
                        }"
                        :style="{ left: `${grade.cutoff}%` }"
                        role="button"
                        tabindex="0"
                        :aria-label="`Set target grade ${grade.grade}`"
                        @click="emit('set-target-grade', grade.grade)"
                        @keydown.enter.prevent="emit('set-target-grade', grade.grade)"
                        @keydown.space.prevent="emit('set-target-grade', grade.grade)"
                    >
                        <span class="grade-marker-line"></span>
                        <span class="grade-marker-label">{{ grade.grade }}</span>
                    </div>
                </div>
                <div class="goal-summary-row">
                    <div class="goal-summary-item goal-summary-target">
                        <span class="text-caption text-medium-emphasis text-uppercase">Target grade</span>
                        <v-select
                            :model-value="props.card.targetGrade"
                            :items="props.gradeOptions"
                            density="compact"
                            variant="outlined"
                            hide-details
                            class="goal-select"
                            @update:model-value="(value) => emit('set-target-grade', Number(value))"
                        />
                    </div>
                    <div class="goal-summary-metrics">
                        <div class="goal-summary-item">
                            <span class="text-caption text-medium-emphasis text-uppercase">Need</span>
                            <span class="goal-summary-value">
                                {{ props.targetSummary.requiredPercent }}% on remaining
                                {{ props.targetSummary.remainingWeight }}%
                            </span>
                        </div>
                        <div class="goal-summary-item">
                            <span class="text-caption text-medium-emphasis text-uppercase">Required score</span>
                            <span class="goal-summary-value">{{ props.targetSummary.requiredScore }}</span>
                        </div>
                    </div>
                </div>
            </v-sheet>
        </v-col>
    </v-row>
</template>

<script setup lang="ts">
import { computed } from "vue";
import GradientText from "./GradientText.vue";
import type { CourseCard, GradeCutoff, TargetSummary } from "../types/home";

const props = defineProps<{
    card: CourseCard;
    gradeCutoffs: GradeCutoff[];
    gradeOptions: number[];
    fromColor: string;
    toColor: string;
    getTimelineScore: number;
    getDebouncedImpossibleStart: number;
    clampPercent: (value: number) => number;
    isGradePassed: (cutoff: number) => boolean;
    targetSummary: TargetSummary;
}>();

const emit = defineEmits<{
    (event: "open-details"): void;
    (event: "set-target-grade", grade: number): void;
}>();

const totalScoreGradientProps = computed(() => ({
    from: props.fromColor,
    to: props.toColor,
    tag: "span",
}));
</script>

<style lang="scss" scoped>
.goal-card {
    padding: 0.75rem 1rem;
    border: 1px solid rgba(var(--v-theme-surfaceBorder), 0.7);
}

.total-score {
    min-height: 36px;
}

.goal-select {
    max-width: 100px;
}

.goal-summary-row {
    margin-top: 0.25rem;
    padding-top: 0.45rem;
    border-top: 1px solid rgba(var(--v-theme-on-surface), 0.14);
    display: grid;
    grid-template-columns: auto 1fr;
    align-items: start;
    gap: 0.75rem;
}

.goal-summary-item {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
}

.goal-summary-value {
    font-size: 0.9rem;
    font-weight: 700;
    color: rgb(var(--v-theme-on-surface));
}

.goal-summary-target {
    min-width: 130px;
}

.goal-summary-metrics {
    display: flex;
    align-items: start;
    gap: 1rem;
    justify-content: flex-start;
    flex-wrap: wrap;
}

.grade-timeline {
    position: relative;
    height: 52px;
    margin-bottom: 0.4rem;
}

.grade-track {
    position: absolute;
    left: 0;
    right: 0;
    top: 18px;
    height: 8px;
    border-radius: 999px;
    background: rgba(var(--v-theme-on-surface), 0.14);
}

.grade-progress {
    position: absolute;
    left: 0;
    top: 18px;
    height: 8px;
    border-radius: 999px;
    background: linear-gradient(
        90deg,
        rgb(var(--v-theme-secondaryTextGradientFrom)),
        rgb(var(--v-theme-secondaryTextGradientTo))
    );
    transition: width 360ms ease-out;
}

.grade-unreachable-zone {
    position: absolute;
    top: 18px;
    right: 0;
    height: 8px;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(var(--v-theme-error), 0.22), rgba(var(--v-theme-error), 0.36));
    box-shadow: inset 0 0 0 1px rgba(var(--v-theme-error), 0.32);
    transition:
        left 360ms ease-out,
        opacity 220ms ease-out;
}

.grade-marker {
    position: absolute;
    top: 0;
    transform: translateX(-50%);
    display: grid;
    justify-items: center;
    gap: 2px;
    cursor: pointer;
}

.grade-marker-line {
    width: 2px;
    height: 18px;
    background: rgba(var(--v-theme-on-surface), 0.32);
    transition:
        height 220ms ease,
        width 220ms ease,
        background-color 220ms ease,
        transform 220ms ease;
}

.grade-marker-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: rgba(var(--v-theme-on-surface), 0.72);
    margin-top: 8px;
    transition:
        color 220ms ease,
        font-size 220ms ease,
        transform 220ms ease,
        font-weight 220ms ease;
}

.grade-marker.start {
    transform: none;
}

.grade-marker.start .grade-marker-label {
    justify-self: start;
}

.grade-marker.passed .grade-marker-line {
    background: rgb(var(--v-theme-success));
}

.grade-marker.passed .grade-marker-label {
    color: rgb(var(--v-theme-success));
}

.grade-marker.target .grade-marker-line {
    height: 22px;
    width: 3px;
    background-color: rgb(var(--v-theme-contrast));
    transform: scaleY(1.03);
}

.grade-marker.target .grade-marker-label {
    font-size: 0.96rem;
    font-weight: 800;
    color: rgb(var(--v-theme-contrast));
    transform: translateY(-1px);
}

.grade-marker.targetPassed .grade-marker-line {
    background: rgba(var(--v-theme-success), 0.95);
}

.grade-marker.targetPassed .grade-marker-label {
    color: rgb(var(--v-theme-success));
}

@media (max-width: 600px) {
    :deep(.text-h5) {
        font-size: 1.2rem !important;
    }

    .goal-summary-row {
        grid-template-columns: 1fr;
        gap: 0.4rem;
        align-items: start;
    }

    .goal-summary-metrics {
        gap: 0.5rem;
    }

    .grade-timeline {
        height: 48px;
    }

    .grade-track,
    .grade-progress {
        top: 16px;
    }

    .grade-unreachable-zone {
        top: 16px;
    }

    .grade-marker-line {
        height: 16px;
    }

    .grade-marker-label {
        font-size: 0.64rem;
        margin-top: 9px;
    }
}
</style>
