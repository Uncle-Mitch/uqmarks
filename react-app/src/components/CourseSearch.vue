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
                    rounded="l"
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
                    rounded="l"
                    :loading="loading"
                    hide-details="auto"
                >
                </v-text-field>
            </v-col>
            <v-col cols="12" md="2">
                <v-btn
                    color="secondary"
                    block
                    style="height: 56px; font-size: 1.25rem"
                    type="submit"
                    rounded="l"
                    :loading="loading"
                >
                    Add
                </v-btn>
            </v-col>
        </v-row>
    </v-form>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";

const props = defineProps<{
    initialCourseCode?: string;
    initialSemesterId?: string;
    semesterOptions: Array<{ value: string; label: string }>;
    rules?: ((v: string) => true | string)[];
    errorMessage?: string;
    loading?: boolean;
    submitMode?: "navigate" | "emit";
}>();

const emit = defineEmits<{
    (event: "submitSearch", payload: { courseCode: string; semesterId: string }): void;
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
    { immediate: true },
);
const courseCode = ref((props.initialCourseCode || "").toUpperCase());

const localErrorMessage = ref("");
const errorMessage = computed(() => props.errorMessage || localErrorMessage.value || "");

const isValid = computed(() => {
    return !!(semester.value && courseCode.value);
});

function onSubmit() {
    if (!isValid.value) return;
    const payload = {
        semesterId: semester.value,
        courseCode: courseCode.value,
    };
    if (props.submitMode === "emit") {
        emit("submitSearch", payload);
        return;
    }
    router.push({
        path: "/course",
        query: payload,
    });
}
</script>

<style lang="scss" scoped>
.v-input.v-input--has-state.v-input--is-error .v-field {
    border: 2px solid #f14668 !important;
    border-radius: 8px;
    box-shadow: none;
}
</style>
