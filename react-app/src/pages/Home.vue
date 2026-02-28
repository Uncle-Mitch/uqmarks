<template>
    <v-container class="text-center pa-5 full-height" fluid>
        <PageTitle />
        <v-row justify="center" class="mt-8">
            <v-col cols="12" md="8">
                <CourseSearch
                    :semester-options="semesterOptions"
                    :rules="[rules.code]"
                    :submit-mode="'emit'"
                    :initialCourseCode="initialCourseCode"
                    :initialSemesterId="initialSemesterId"
                    @submit-search="handleSearchSubmit"
                />
            </v-col>
        </v-row>
        <v-row justify="center" v-if="addError">
            <v-col cols="12" md="8">
                <v-alert
                    elevation="2"
                    prominent
                    color="warning"
                    class="add-error-alert text-left d-flex align-center font-weight-bold"
                >
                    <template #prepend>
                        <v-icon icon="fas fa-exclamation-triangle" class="warning-icon" />
                    </template>
                    <span>{{ addError }}</span>
                    <template #append>
                        <v-btn
                            icon="fas fa-times"
                            variant="text"
                            density="comfortable"
                            color="black"
                            @click="addError = ''"
                        />
                    </template>
                </v-alert>
            </v-col>
        </v-row>
        <v-row justify="center" v-if="!cards.length" class="mt-6">
            <v-col cols="12" md="8">
                <v-sheet class="empty-state" elevation="4" rounded="xl">
                    <div class="empty-title">Add Courses</div>
                    <div class="empty-subtitle">Search above to start tracking your grades</div>
                </v-sheet>
            </v-col>
        </v-row>
        <template v-for="group in groupedCards" :key="group.semesterId">
            <v-row justify="center" class="mt-4">
                <v-col cols="12" md="8">
                    <div class="semester-group-header">
                        <div class="semester-group-title">{{ group.semesterLabel }}</div>
                    </div>
                </v-col>
            </v-row>
            <v-row justify="center" v-for="card in group.cards" :key="card.id" class="mt-3">
                <v-col cols="12" md="8">
                    <CourseCardItem
                        :card="card"
                        :semesterOptions="semesterOptions"
                        :gradeCutoffs="gradeCutoffs"
                        :gradeOptions="gradeOptions"
                        :fromColor="fromColor"
                        :toColor="toColor"
                        @remove-card="removeCard(card)"
                        @toggle-collapse="toggleCollapse(card)"
                        @submit-profile-url="(url) => handleProfileUrlSubmit(card, url)"
                        @open-details="openCardDetails(card)"
                        @persist-state="persistCards()"
                    />
                </v-col>
            </v-row>
        </template>
        <GradeDetailsDialog
            v-model="gradeDetailsDialogOpen"
            :selectedCard="selectedDetailsCard"
            :rows="selectedDetailsRows"
            :resultsHeaders="resultsHeaders"
            :rowProps="rowProps"
        />
    </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import CourseSearch from "../components/CourseSearch.vue";
import PageTitle from "../components/PageTitle.vue";
import CourseCardItem from "../components/CourseCardItem.vue";
import GradeDetailsDialog from "../components/GradeDetailsDialog.vue";
import { getWith1DayExpiry, setWith1DayExpiry } from "../utils/localStorageRetrieval.ts";
import { getJsonCookie, setJsonCookie } from "../utils/cookieStorage";
import { useTheme } from "vuetify";
import type { CourseCard, GradeDetailsRow, SemesterOption, StoredCard } from "../types/home";
import { calculateTotalScore, getGradeDetailsRows, isWeightValid } from "../utils/courseCardCalculations";

const theme = useTheme();
const fromColor = computed(() => theme.global.current.value.colors.secondaryTextGradientFrom);
const toColor = computed(() => theme.global.current.value.colors.secondaryTextGradientTo);
const baseUrl = import.meta.env.VITE_API_BASE_URL;

const MAX_CARDS = 40;
const RECENT_SEARCHES_COOKIE = "uqm_recent_searches";
const COURSE_CARDS_COOKIE = "uqm_course_cards";
const semesterOptions = ref<SemesterOption[]>([]);
const cards = ref<CourseCard[]>([]);
const addError = ref("");
const recentSearches = ref<Array<{ courseCode: string; semesterId: string }>>(
    getJsonCookie(RECENT_SEARCHES_COOKIE) ?? [],
);
const initialCourseCode = computed(() => recentSearches.value[0]?.courseCode ?? "");
const initialSemesterId = computed(() => recentSearches.value[0]?.semesterId ?? "");
const gradeDetailsDialogOpen = ref(false);
const selectedDetailsCardId = ref<string | null>(null);
const groupedCards = computed(() => {
    const groups = new Map<
        string,
        { semesterId: string; semesterLabel: string; cards: CourseCard[]; sortKey: number }
    >();

    for (const card of cards.value) {
        const match = /^(\d{4})S([1-3])$/.exec(card.semesterId);
        const sortKey = match ? parseInt(match[1], 10) * 10 + parseInt(match[2], 10) : 0;
        const existing = groups.get(card.semesterId);
        if (existing) {
            existing.cards.push(card);
        } else {
            groups.set(card.semesterId, {
                semesterId: card.semesterId,
                semesterLabel: card.semesterLabel,
                cards: [card],
                sortKey,
            });
        }
    }

    return Array.from(groups.values())
        .sort((a, b) => b.sortKey - a.sortKey)
        .map(({ semesterId, semesterLabel, cards }) => ({ semesterId, semesterLabel, cards }));
});
const selectedDetailsCard = computed(() =>
    selectedDetailsCardId.value ? (cards.value.find((card) => card.id === selectedDetailsCardId.value) ?? null) : null,
);
const selectedDetailsRows = computed<GradeDetailsRow[]>(() => {
    if (!selectedDetailsCard.value) return [];
    return getGradeDetailsRows(selectedDetailsCard.value.dataSource, gradeCutoffs);
});
const resultsHeaders = [
    { title: "Grade", value: "grade" },
    { title: "Cutoff (%)", value: "cutoff" },
    { title: "Required (%)", value: "requiredPercent" },
    { title: "Required Score", value: "requiredScore" },
];

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

const gradeOptions = [1, 2, 3, 4, 5, 6, 7];

const gradeCutoffs = [
    { grade: 1, cutoff: 0 },
    { grade: 2, cutoff: 30 },
    { grade: 3, cutoff: 45 },
    { grade: 4, cutoff: 50 },
    { grade: 5, cutoff: 65 },
    { grade: 6, cutoff: 75 },
    { grade: 7, cutoff: 85 },
];

onMounted(() => {
    restoreCardsFromCookie();
    void loadSemesterOptions();
    void sendPageLoadAnalytics();
});

async function loadSemesterOptions() {
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
}

function makeId() {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
        return crypto.randomUUID();
    }
    return `card_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function handleSearchSubmit(payload: { courseCode: string; semesterId: string }) {
    addError.value = "";
    if (cards.value.length >= MAX_CARDS) {
        addError.value = "You have reached the maximum of 10 courses.";
        return;
    }
    const courseCode = payload.courseCode.toUpperCase();
    const semesterId = payload.semesterId;
    const duplicate = cards.value.find((card) => card.courseCode === courseCode && card.semesterId === semesterId);
    if (duplicate) {
        addError.value = "That course is already on your dashboard.";
        return;
    }

    const semesterLabel = semesterOptions.value.find((opt) => opt.value === semesterId)?.label ?? semesterId;
    const newCard = reactive<CourseCard>({
        id: makeId(),
        courseCode,
        semesterId,
        semesterLabel,
        loading: true,
        showURLRequest: false,
        searchError: "",
        validInput: false,
        editingWeights: false,
        collapsed: false,
        dataSource: [],
        totalScore: 0,
        weightValid: true,
        targetGrade: 5,
    });
    cards.value = [newCard, ...cards.value];
    fetchCourseData(newCard);
}

async function fetchCourseData(card: CourseCard) {
    card.showURLRequest = false;
    card.searchError = "";
    card.loading = true;
    card.dataSource = [];
    card.totalScore = 0;

    const params = new URLSearchParams({
        courseCode: card.courseCode,
        semesterId: card.semesterId,
    });

    if (card.courseProfileUrl?.length) {
        params.append("courseProfileUrl", card.courseProfileUrl);
    }

    try {
        const res = await fetch(`${baseUrl}/api/getcourse/?${params.toString()}`);
        let json: any = null;
        try {
            json = await res.json();
        } catch {
            json = null;
        }
        if (!res.ok) {
            card.validInput = false;
            card.showURLRequest = !!json?.showURLRequest;
            const message = typeof json?.error === "string" ? json.error : "";
            if (card.showURLRequest && !message) {
                card.searchError = "";
                return;
            }
            const fallbackMessage = `Request failed (${res.status})`;
            card.showURLRequest = true;
            const finalMessage = message || fallbackMessage;
            throw new Error(finalMessage);
        }
        const items = json.assessmentItems as Array<{ title: string; weight: string }>;
        if (!items?.length) {
            card.validInput = false;
            card.showURLRequest = true;
            throw new Error("No assessment items returned. Please provide the course profile URL.");
        }
        card.dataSource = items.map((item, idx) => ({
            key: idx,
            assessment: item.title,
            weight: item.weight,
            score: "",
            enabled: true,
            validWeight: !!parseFloat(item.weight),
        }));
        card.validInput = true;
        refreshCardSummary(card);
        saveRecentSearch(card);
        persistCards();
    } catch (err: any) {
        card.validInput = false;
        card.showURLRequest = true;
        const message = typeof err?.message === "string" ? err.message : "";
        card.searchError = message || "Something went wrong while loading this course.";
    } finally {
        card.loading = false;
    }
}

function handleProfileUrlSubmit(card: CourseCard, courseProfileUrl: string) {
    card.courseProfileUrl = courseProfileUrl;
    fetchCourseData(card);
}

function toggleCollapse(card: CourseCard) {
    card.collapsed = !card.collapsed;
    persistCards();
}

function openCardDetails(card: CourseCard) {
    selectedDetailsCardId.value = card.id;
    gradeDetailsDialogOpen.value = true;
}

function refreshCardSummary(card: CourseCard) {
    card.totalScore = calculateTotalScore(card.dataSource).score;
    card.weightValid = isWeightValid(card.dataSource);
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

function removeCard(card: CourseCard) {
    cards.value = cards.value.filter((entry) => entry.id !== card.id);
    persistCards();
}

function saveRecentSearch(card: CourseCard) {
    const entry = {
        courseCode: card.courseCode,
        semesterId: card.semesterId,
        semesterLabel: card.semesterLabel,
        searchedAt: new Date().toISOString(),
    };
    const existing = getJsonCookie<any[]>(RECENT_SEARCHES_COOKIE) ?? [];
    const filtered = existing.filter(
        (item) => !(item.courseCode === entry.courseCode && item.semesterId === entry.semesterId),
    );
    const updated = [entry, ...filtered].slice(0, 6);
    setJsonCookie(RECENT_SEARCHES_COOKIE, updated, { days: 30 });
    recentSearches.value = updated;
}

function persistCards() {
    const payload = {
        version: 1,
        updatedAt: new Date().toISOString(),
        cards: cards.value
            .filter((card) => card.validInput && !card.showURLRequest)
            .map<StoredCard>((card) => ({
                courseCode: card.courseCode,
                semesterId: card.semesterId,
                semesterLabel: card.semesterLabel,
                dataSource: card.dataSource,
                targetGrade: card.targetGrade,
                collapsed: card.collapsed,
            })),
    };
    setJsonCookie(COURSE_CARDS_COOKIE, payload, { days: 30 });
}

function restoreCardsFromCookie() {
    const stored = getJsonCookie<{ cards: StoredCard[] }>(COURSE_CARDS_COOKIE);
    if (!stored?.cards?.length) return;
    cards.value = stored.cards.slice(0, MAX_CARDS).map((card) => {
        const restored = reactive<CourseCard>({
            id: makeId(),
            courseCode: card.courseCode,
            semesterId: card.semesterId,
            semesterLabel: card.semesterLabel,
            loading: false,
            showURLRequest: false,
            searchError: "",
            validInput: true,
            editingWeights: false,
            collapsed: card.collapsed ?? false,
            dataSource: card.dataSource,
            totalScore: 0,
            weightValid: true,
            targetGrade: card.targetGrade ?? 5,
        });
        refreshCardSummary(restored);
        return restored;
    });
}

async function sendPageLoadAnalytics() {
    const entries = cards.value
        .filter((card) => card.courseCode && card.semesterId)
        .map((card) => ({
            courseCode: card.courseCode,
            semesterId: card.semesterId,
        }));

    if (!entries.length) return;

    try {
        await fetch(`${baseUrl}/api/analytics/page-load/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ entries }),
            keepalive: true,
        });
    } catch {}
}
</script>

<style lang="scss" scoped>
.add-error-alert :deep(.v-alert__append) {
    margin-left: auto;
}

.empty-state {
    padding: 2rem 1.5rem;
    background: rgba(var(--v-theme-surface), 0.9);
    border: 1px dashed rgba(var(--v-theme-surfaceBorder), 0.75);
}

.empty-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: rgb(var(--v-theme-on-surface));
}

.empty-subtitle {
    font-size: 0.95rem;
    color: rgba(var(--v-theme-on-surface), 0.7);
}

.semester-group-title {
    text-align: left;
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(var(--v-theme-on-surface), 0.68);
}

.semester-group-header {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 0.75rem;
}

.full-height {
    min-height: 100vh;
}
</style>
