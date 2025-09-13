<template>
    <v-form @submit.prevent="onSubmit" lazy-validation>
        <v-row dense>
            <v-col cols="12" md="5">
                <v-select
                    v-model="semester"
                    :items="semesterOptions"
                    label="Semester"
                    item-title="label"
                    item-value="value"
                    rounded-xl
                    variant="solo-filled"
                    style="font-size: 1.25rem"
                    :hide-details="true"
                />
            </v-col>
            <v-col cols="12" md="5">
                <v-text-field
                    v-model="courseCode"
                    placeholder="Course Code"
                    :rules="rules"
                    :error="!!errorMessage"
                    :error-messages="errorMessage"
                    style="font-size: 5rem"
                    variant="solo-filled"
                    rounded-xl
                    :loading="loading"
                    hide-details="auto"
                >
                </v-text-field>
            </v-col>
            <v-col cols="12" md="2">
                <v-btn
                    color="secondary"
                    class="white--text"
                    block
                    style="height: 56px; font-size: 1.25rem"
                    type="submit"
                    :loading="loading"
                >
                    Go
                </v-btn>
            </v-col>
        </v-row>
    </v-form>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
const baseUrl = import.meta.env.VITE_API_BASE_URL;

const props = defineProps<{
    initialCourseCode?: string;
    initialSemesterId?: string;
    semesterOptions: Array<{ value: string; label: string }>;
    rules?: ((v: string) => true | string)[];
    errorMessage?: string;
    loading?: boolean;
}>();

const router = useRouter();

const semester = ref(props.initialSemesterId || "");
watch(
    () => props.semesterOptions,
    (options) => {
        if (!props.initialSemesterId && options?.length) {
            semester.value = options[0].value;
        }
    },
    { immediate: true }
);
const courseCode = ref((props.initialCourseCode || "").toUpperCase());

const localErrorMessage = ref("");
const errorMessage = computed(() => props.errorMessage || localErrorMessage.value || "");

const isValid = computed(() => {
    return !!(semester.value && courseCode.value);
});

function onSubmit() {
    if (!isValid.value) return;
    router.push({
        path: "/course",
        query: {
            semesterId: semester.value,
            courseCode: courseCode.value,
        },
    });
}
</script>

<style lang="scss" scoped>
.v-input.v-input--has-state.v-input--is-error .v-field {
    border: 2px solid #f14668 !important;
    border-radius: 8px;
    box-shadow: none;
}

::v-deep(.v-messages__message) {
    font-weight: 600;
    color: #fbd4c6;
}
</style>
