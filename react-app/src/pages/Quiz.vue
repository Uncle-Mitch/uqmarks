<template>
    <v-container class="text-center pa-5" fluid>
        <GradientText
            :from="theme.global.current.value.colors.titleGradientFrom"
            :to="theme.global.current.value.colors.titleGradientTo"
            tag="h1"
            class="text-primary text-h3 font-weight-bold"
        >
            Quiz Calculator
        </GradientText>
        <v-row justify="center" class="mt-8">
            <v-col cols="12" md="8">
                <v-row class="mt-2">
                    <v-col cols="6" class="text-left">
                        <div class="text-h6">Total Quizzes:</div>
                        <v-number-input
                            v-model.number="totalQuizzes"
                            control-variant="stacked"
                            density="compact"
                            :hide-input="false"
                            :min="0"
                            :max="50"
                            variant="solo-filled"
                            :inset="false"
                            rounded-xl
                            style="max-width: 200px"
                        />
                    </v-col>
                </v-row>
                <v-row class="mt-2">
                    <v-col cols="6" class="text-left">
                        <div class="text-h6">Quizzes counted towards grade:</div>
                        <v-number-input
                            v-model.number="countBest"
                            controlVariant="stacked"
                            :hideInput="false"
                            :min="0"
                            :max="totalQuizzes"
                            density="compact"
                            variant="solo-filled"
                            rounded-xl
                            style="max-width: 200px"
                        />
                    </v-col>
                </v-row>
                <v-sheet elevation="2" rounded="lg" class="table-wrapper text-start">
                    <v-data-table
                        :items="quizzes"
                        :headers="headers"
                        hide-default-footer
                        class="assessment-table"
                        items-per-page="-1"
                    >
                        <template #item.key="{ index }">
                            <span>{{ index + 1 }}</span>
                        </template>
                        <template #item.score="{ item }">
                            <v-text-field
                                v-model="item.score"
                                hide-details
                                density="compact"
                                variant="outlined"
                                @update:model-value="(value) => (item.percentage = parseScore(value))"
                                style="max-width: 150px"
                                placeholder="90%, 9/10"
                            />
                        </template>
                        <template #item.percentage="{ item }">
                            {{ item.percentage !== undefined ? item.percentage.toFixed(2) + "%" : "0.00%" }}
                        </template>
                        <template #item.counted="{ item }">
                            <v-icon
                                v-if="item.counted"
                                color="green"
                                size="small"
                                icon="fas  fa-check-circle"
                                title="Counted in total score"
                            />
                            <v-icon
                                v-else
                                color="red"
                                size="small"
                                icon="fas  fa-times-circle"
                                title="Not counted in total score"
                            />
                        </template>
                    </v-data-table>
                </v-sheet>
            </v-col>
        </v-row>

        <v-row justify="center" class="mt-12">
            <v-col cols="12" md="5">
                <GradientText :from="fromColor" :to="toColor" tag="h4" class="text-primary text-h4 font-weight-bold">
                    Total Score
                </GradientText>
                <br></br>
                <GradientText :from="fromColor" :to="toColor" tag="h4" class="text-primary text-h4 font-weight-bold">
                    {{ totalScore.toFixed(2) }}%
                </GradientText>             
            </v-col>
        </v-row>
    </v-container>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useTheme } from "vuetify";
import GradientText from "../components/GradientText.vue";

const theme = useTheme();
const fromColor = computed(() => theme.global.current.value.colors.secondaryTextGradientFrom);
const toColor = computed(() => theme.global.current.value.colors.secondaryTextGradientTo);

interface Quiz {
    key: number;
    score?: number;
    percentage?: number;
    counted?: boolean;
}

const totalQuizzes = ref(0);
const countBest = ref(0);
const quizzes = ref<Quiz[]>([]);

const headers = [
    { title: "Quiz Number", value: "key", width: "25%" },
    { title: "Your Score", value: "score", width: "25%" },
    { title: "Percentage", value: "percentage", width: "25%" },
    { title: "Counted", value: "counted", width: "25%" },
];

watch(totalQuizzes, (total) => {
    const arr: Quiz[] = [];
    for (let i = 0; i < (total ?? 0); i++) arr.push({ key: i });
    quizzes.value = arr;
    if (countBest.value > total) {
        countBest.value = total;
    }
});

watch(countBest, (val) => {
    if (val > totalQuizzes.value) countBest.value = totalQuizzes.value;
});

const totalScore = computed(() => {
    if (countBest.value <= 0) {
        quizzes.value.forEach((q) => (q.counted = false));
        return 0;
    }
    const sorted = quizzes.value
        .map((q, i) => ({ ...q, index: i }))
        .filter((q) => q.percentage !== undefined && q.percentage > 0)
        .sort((a, b) => b.percentage! - a.percentage!);

    const top = sorted.slice(0, countBest.value);
    quizzes.value.forEach((q) => (q.counted = false));
    top.forEach((q) => {
        quizzes.value[q.index].counted = true;
    });

    const sum = top.reduce((a, b) => a + (b.percentage || 0), 0);
    const average = sum / countBest.value;
    return top.length > 0 ? average : 0;
});

function parseScore(value: string): number | undefined {
    if (!value) return undefined;
    const pct = /^([0-9]+(?:\.[0-9]+)?)%$/.exec(value);
    if (pct) return parseFloat(pct[1]);

    const fraction = /^([0-9]+(?:\.[0-9]+)?)\/([0-9]+(?:\.[0-9]+)?)$/.exec(value);
    if (fraction) {
        const num = parseFloat(fraction[1]);
        const denom = parseFloat(fraction[2]);
        if (denom !== 0) return (num / denom) * 100;
    }

    const numMatch = /^([0-9]+(?:\.[0-9]+)?)$/.exec(value);
    if (numMatch) return parseFloat(numMatch[1]);

    return undefined;
}
</script>

<style lang="scss" scoped>
.page-title {
    color: #d9b3ff;
    margin-bottom: 2rem;
}

.assessment-table thead th {
    background-color: #ebe5f7 !important;
    font-weight: 700 !important;
    color: #333;
}

.assessment-table td,
.assessment-table th {
    padding: 12px 18px !important;
}

.results-title {
    color: #d9b3ff;
}

.total-score {
    color: #d9b3ff;
    margin-top: 0.5rem;
}

:deep .assessment-table thead th,
:deep .results-table thead th {
    font-weight: 700 !important;
}
</style>
