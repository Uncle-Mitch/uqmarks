<template>
    <v-container class="text-center pa-5 full-height" fluid>
        <PageTitle />
        <v-row justify="center" class="mt-8">
            <v-col cols="12" md="8">
                <CourseSearch
                    :initialCourseCode="courseCode"
                    :initialSemesterId="semesterId"
                    :semester-options="semesterOptions"
                    :rules="[rules.code]"
                    :error-message="showURLRequest ? '' : searchError"
                    :loading="loading"
                />
            </v-col>
        </v-row>
        <v-row justify="center" v-if="showURLRequest && !loading">
            <v-col cols="12" md="8">
                <CourseProfileUrlInput
                    :courseCode="courseCode"
                    :semesterId="semesterId"
                    :semesterOptions="semesterOptions"
                    :url="courseProfileUrl"
                    :error-message="searchError"
                />
            </v-col>
        </v-row>
        <v-row justify="center" v-if="validInput && isMobile">
            <v-col cols="12" md="8">
                <div class="d-flex align-start">
                    <v-btn
                        variant="flat"
                        @click="() => (editingWeights = !editingWeights)"
                        rounded="pill"
                        color="accent"
                        style="text-transform: none"
                        :aria-label="editingWeights ? 'Confirm' : 'Edit Weight'"
                        :title="editingWeights ? 'Confirm' : 'Edit Weight'"
                        >{{ editingWeights ? "Confirm" : "Edit Weights" }}</v-btn
                    >
                </div>
            </v-col>
        </v-row>
        <v-row justify="center" v-if="validInput">
            <v-col cols="12" md="8">
                <v-sheet elevation="2" rounded="lg" class="table-wrapper text-start">
                    <v-data-table
                        :items="dataSource"
                        :headers="headers"
                        hide-default-footer
                        class="assessment-table"
                        :row-props="assessmentRowProps"
                        :loading="loading"
                        items-per-page="-1"
                    >
                        <template v-slot:header.weight>
                            <div class="d-flex align-center">
                                <span>Weight</span>
                                <v-icon
                                    v-if="!isMobile"
                                    @click="() => (editingWeights = !editingWeights)"
                                    class="clickable"
                                    style="margin-left: 10px"
                                    :aria-label="editingWeights ? 'Confirm' : 'Edit Weight'"
                                    :title="editingWeights ? 'Confirm' : 'Edit Weight'"
                                    size="x-small"
                                    color="accent"
                                    flat
                                >
                                    {{ editingWeights ? "fas fa-check" : "fas fa-pencil" }}
                                </v-icon>
                            </div>
                        </template>
                        <template v-slot:loading>
                            <v-skeleton-loader type="table-row@4"></v-skeleton-loader>
                        </template>
                        <template #item.weight="{ item, index }">
                            <div style="display: flex; justify-content: left; align-items: center">
                                <span v-if="!editingWeights">{{ item.weight }}</span>
                                <v-text-field
                                    v-if="editingWeights"
                                    v-model="item.weight"
                                    hide-details
                                    density="compact"
                                    @update:model-value="(value) => handleWeightChange(index, value)"
                                    variant="outlined"
                                />
                                <v-icon
                                    v-if="!item.validWeight"
                                    style="margin-left: 10px"
                                    aria-label="Invalid weight"
                                    title="Invalid weight"
                                    size="x-small"
                                    color="red"
                                >
                                    fas fa-circle-exclamation
                                </v-icon>
                            </div>
                        </template>
                        <template #item.score="{ item, index }">
                            <v-text-field
                                v-model="item.score"
                                placeholder="90, 90%, 9/10"
                                hide-details
                                density="compact"
                                :disabled="!item.enabled || !item.validWeight"
                                @update:model-value="(value) => handleScoreChange(index, value)"
                                variant="outlined"
                            />
                        </template>
                        <template #item.enabled="{ item }">
                            <v-container justify="center" style="padding: 0; height: 40px">
                                <v-switch
                                    v-model="item.enabled"
                                    :disabled="!item.validWeight"
                                    inset
                                    density="compact"
                                    hide-details
                                    color="secondary"
                                    style="transform: scale(0.6); margin: 0"
                                />
                            </v-container>
                        </template>
                    </v-data-table>
                </v-sheet>
            </v-col>
        </v-row>
        <v-row justify="center" class="mt-4" v-if="!weightValid && validInput && !loading">
            <v-col cols="12" md="8">
                <v-alert elevation="2" prominent color="warning" class="text-left d-flex align-center font-weight-bold">
                    <template #prepend>
                        <v-icon icon="fas fa-exclamation-triangle" class="warning-icon" />
                    </template>
                    <span> The assessment items do not add up to 100%. </span>
                </v-alert>
            </v-col>
        </v-row>

        <v-row justify="center" class="mt-12" v-if="validInput">
            <v-col cols="12" md="5">
                <GradientText :from="fromColor" :to="toColor" tag="h4" class="text-primary text-h4 font-weight-bold">
                    Total Score
                </GradientText>
                <br />
                <GradientText :from="fromColor" :to="toColor" tag="h4" class="text-primary text-h4 font-weight-bold">
                    {{ totalScore.toFixed(2) }}%
                </GradientText>
            </v-col>
        </v-row>
        <v-row justify="center" class="mt-4" v-if="validInput">
            <v-col cols="12" md="8">
                <v-sheet elevation="2" rounded="lg" class="results-wrapper text-start">
                    <v-data-table
                        :items="gradeResultsData"
                        :headers="resultsHeaders"
                        hide-default-footer
                        density="comfortable"
                        :row-props="rowProps"
                        class="results-table"
                        :loading="loading"
                    >
                        <template v-slot:loading>
                            <v-skeleton-loader type="table-row@7"></v-skeleton-loader>
                        </template>
                    </v-data-table>
                </v-sheet>
            </v-col>
        </v-row>
    </v-container>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useBreakpoints } from "@vueuse/core";
import CourseSearch from "../components/CourseSearch.vue";
import PageTitle from "../components/PageTitle.vue";
import CourseProfileUrlInput from "../components/CourseProfileUrlInput.vue";
import { getWith1DayExpiry, setWith1DayExpiry } from "../utils/localStorageRetrieval.ts";
import GradientText from "../components/GradientText.vue";
import { useTheme } from "vuetify";
const theme = useTheme();
const fromColor = computed(() => theme.global.current.value.colors.secondaryTextGradientFrom);
const toColor = computed(() => theme.global.current.value.colors.secondaryTextGradientTo);
const breakpoints = useBreakpoints({
    mobile: 0,
    tablet: 600,
    desktop: 1024,
});
const isMobile = breakpoints.smallerOrEqual("tablet");
const baseUrl = import.meta.env.VITE_API_BASE_URL;

const route = useRoute();
const courseCode = computed(() => route.query.courseCode as string);
const semesterId = computed(() => route.query.semesterId as string);
const courseProfileUrl = computed(() => route.query.courseProfileUrl as string);
const searchError = ref("");

const loading = ref(true);
const editingWeights = ref(false);
const showURLRequest = ref(false);
const dataSource = ref<
    Array<{
        key: number;
        assessment: string;
        weight: string;
        score: string;
        enabled: boolean;
        validWeight: boolean;
    }>
>([]);
const totalScore = computed(() => calculateTotalScore());
const gradeResultsData = ref<Array<any>>([]);
const validInput = ref(false);
const rules = {
    code: (value: string) => {
        const pattern = /^[aA-zZ]{4}[0-9]{4}$/;
        return pattern.test(value) || "Invalid course code";
    },
    semesterId: (value: string) => {
        const pattern = /^\d{4}S[1-3]$/;
        return pattern.test(value) || "Invalid semester ID";
    },
    courseProfileUrl: (value: string) => {
        const pattern = /^https:\/\/course-profiles\.uq\.edu\.au\/course-profiles\/[A-Za-z]{4}[0-9]{4}-\d+-\d+(#.+)?$/;
        return pattern.test(value) || "Invalid course profile URL";
    },
};

const headers = computed(() => {
    const baseHeaders = [
        { title: "Assessment", value: "assessment", width: isMobile.value ? "30%" : "30%" },
        { title: "Weight", value: "weight", width: isMobile.value ? "15%" : "20%" },
    ];

    // Only add "Your Score" column if not on mobile or if editing weights on mobile
    if (!isMobile.value || !editingWeights.value) {
        baseHeaders.push({
            title: "Your Score",
            value: "score",
            width: isMobile.value ? "30%" : "20%",
        });
    } else {
        baseHeaders.push({
            title: "Your Score",
            value: "score",
            width: "5%",
        });
    }

    baseHeaders.push({
        title: "",
        value: "enabled",
        width: isMobile.value ? "15%" : "10%",
    });

    return baseHeaders;
});
const resultsHeaders = [
    { title: "Grade", value: "grade" },
    { title: "Cutoff (%)", value: "cutoff" },
    { title: "Required (%)", value: "requiredPercent" },
    { title: "Required Score", value: "requiredScore" },
];

const gradeCutoffs = [
    { grade: 1, cutoff: 0 },
    { grade: 2, cutoff: 30 },
    { grade: 3, cutoff: 45 },
    { grade: 4, cutoff: 50 },
    { grade: 5, cutoff: 65 },
    { grade: 6, cutoff: 75 },
    { grade: 7, cutoff: 85 },
];
const semesterOptions = ref<Array<{ value: string; label: string }>>([]);
onMounted(async () => {
    searchError.value = "";
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
        searchError.value = "Something went wrong. Try again later";
    }
});

async function fetchData() {
    showURLRequest.value = false;
    const codeValid = rules.code(courseCode.value);
    const semesterValid = rules.semesterId(semesterId.value);

    if (!courseCode.value || !semesterId.value || codeValid !== true || semesterValid !== true) {
        loading.value = false;
        searchError.value = "";
        return;
    }
    loading.value = true;
    dataSource.value = [];
    gradeResultsData.value = [];

    const params = new URLSearchParams({
        courseCode: courseCode.value,
        semesterId: semesterId.value,
    });

    if (courseProfileUrl.value?.length > 0) {
        params.append("courseProfileUrl", courseProfileUrl.value);
    }
    try {
        const res = await fetch(`${baseUrl}/api/getcourse/?${params.toString()}`);
        const json = await res.json();
        if (!res.ok) {
            validInput.value = false;
            showURLRequest.value = json.showURLRequest ?? false;
            throw new Error(json?.error);
        }
        const items = json.assessmentItems as Array<{ title: string; weight: string }>;

        dataSource.value = items.map((item, idx) => ({
            key: idx,
            assessment: item.title,
            weight: item.weight,
            score: "",
            enabled: true,
            validWeight: !!parseFloat(item.weight),
        }));
        validInput.value = true;
        searchError.value = "";
    } catch (err: any) {
        validInput.value = false;
        searchError.value = err.message;
    } finally {
        loading.value = false;
    }
}

function parseScore(value: string): number | null {
    if (!value) return null;
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

    return null;
}

function calculateTotalScore() {
    let weightedSum = 0;
    let totalWeight = 0;
    for (const item of dataSource.value) {
        if (!item.enabled) break;

        const sc = parseScore(item.score);
        const wt = parseFloat(item.weight) / 100;
        if (sc !== null && !isNaN(wt)) {
            const capped = Math.max(Math.min(sc, 100), 0);
            weightedSum += capped * wt;
            totalWeight += wt;
        }
    }

    const rounded = parseFloat(weightedSum.toFixed(2));
    updateGradeResults(rounded, totalWeight);
    return rounded;
}

function parseWeight(value: string) {
    const match = value.match(/^(\d+(\.\d+)?)%$/);
    if (!match) {
        return null;
    }
    return parseFloat(match[1]);
}

function handleScoreChange(index: number, value: string) {
    dataSource.value[index].score = value;
}

function handleWeightChange(index: number, value: string) {
    if (value.length > 0 && !!parseWeight(value)) {
        dataSource.value[index].validWeight = true;
    } else {
        dataSource.value[index].validWeight = false;
    }
    dataSource.value[index].weight = value;
}

function updateGradeResults(currentScore: number, totalWeight: number) {
    gradeResultsData.value = gradeCutoffs.map((info) => {
        const remainingWeight = isNaN(totalWeight) ? 1 : 1 - totalWeight;
        const reqInc = info.cutoff - currentScore;
        const reqIncCapped = Math.max(reqInc, 0);
        const reqWithRemaining = reqIncCapped / remainingWeight;
        const obtainable = remainingWeight > 0 && reqInc <= remainingWeight * 100;

        const fmt = (v: number) => (v === 0 ? "0" : parseFloat(v.toFixed(2)).toString());

        return {
            key: info.grade,
            grade: info.grade,
            cutoff: info.cutoff,
            requiredPercent: reqWithRemaining >= 0 ? parseFloat(reqWithRemaining.toFixed(2)) : 0,
            requiredScore: `${fmt(reqIncCapped)}/${Math.round(remainingWeight * 100)}`,
            achieved: currentScore >= info.cutoff,
            obtainable,
        };
    });
}

function assessmentRowProps(row: any) {
    if (row.item?.enabled === undefined) {
        return {};
    }
    const rowClass = row.item?.enabled ? "" : "disabled-row";
    return {
        class: rowClass,
    };
}

function rowProps(row: any) {
    if (row.item?.achieved === undefined || row.item?.obtainable === undefined) {
        return {};
    }
    const rowClass = row.item?.achieved ? "achieved-row" : !row.item?.obtainable ? "unobtainable-row" : "";
    return {
        class: rowClass,
    };
}

watch(() => [route.query.courseCode, route.query.semesterId, route.query.courseProfileUrl], fetchData, {
    immediate: true,
});

const totalEnabledWeight = computed(() => {
    return dataSource.value.filter((item) => item.enabled).reduce((sum, item) => sum + parseFloat(item.weight), 0);
});

const weightValid = computed(() => Math.round(totalEnabledWeight.value) === 100);
</script>

<style lang="scss" scoped>
.page-title {
    color: #d9b3ff;
    margin-bottom: 2rem;
}

.assessment-table th,
.results-wrapper th {
    background-color: #ebe5f7 !important;
    font-weight: 600;
    color: #333;
}

.results-title {
    color: #d9b3ff;
}

.total-score {
    color: #d9b3ff;
    margin-top: 0.5rem;
}

:deep(.achieved-row) {
    background-color: var(--achieved-row-bg) !important;
}
:deep(.unobtainable-row) {
    background-color: var(--unobtainable-row-bg) !important;
}
:deep(.disabled-row) {
    background-color: var(--disabled-row-bg) !important;
}

:deep(.assessment-table thead th),
:deep(.results-table thead th) {
    font-weight: 700 !important;
}

.full-height {
    min-height: 100vh;
}

// Override padding for mobile
@media (max-width: 600px) {
    :deep(.v-data-table__td),
    :deep(.v-data-table__th) {
        padding: 2px 4px !important;
    }
}
</style>
