<template>
    <v-form @submit.prevent="onSubmit" lazy-validation>
        <VCard class="pa-4" elevation="3">
            <VCardTitle class="text-wrap">
                🎉 You are the first one to search <strong>{{ courseCode }}</strong> for {{ semesterText }}!
            </VCardTitle>
            <VCardText> Please enter the course profile URL so we can retrieve the assessment details. </VCardText>

            <VTextField
                v-model="courseProfileUrl"
                label="Course Profile URL"
                placeholder="https://course-profiles.uq.edu.au/course-profiles/..."
                variant="outlined"
                density="comfortable"
                :error-messages="errorMessage"
                clearable
            />

            <VCardActions>
                <VSpacer />
                <VBtn @click="onSubmit" color="secondary" variant="flat" type="submit"> Submit </VBtn>
            </VCardActions>
        </VCard>
    </v-form>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";

const props = defineProps<{
    courseCode: string;
    semesterId: string;
    semesterOptions: Array<{ value: string; label: string }>;
    url?: string;
    errorMessage?: string;
    submitMode?: "navigate" | "emit";
}>();

const emit = defineEmits<{
    (event: "submitUrl", payload: { courseProfileUrl: string }): void;
}>();

const router = useRouter();

const courseProfileUrl = ref(props.url || "");
const semesterText = computed(() => {
    const semesterObj = props.semesterOptions.find((opt) => opt.value === props.semesterId);
    return semesterObj ? semesterObj.label : props.semesterId;
});

const isValid = computed(() => {
    return !!(props.semesterId && props.courseCode && courseProfileUrl.value);
});

function onSubmit() {
    if (!isValid.value) return;
    const payload = {
        semesterId: props.semesterId,
        courseCode: props.courseCode,
        courseProfileUrl: courseProfileUrl.value,
    };
    if (props.submitMode === "emit") {
        emit("submitUrl", { courseProfileUrl: courseProfileUrl.value });
        return;
    }
    router.push({
        path: "/course",
        query: payload,
    });
}
</script>
<style scoped></style>
