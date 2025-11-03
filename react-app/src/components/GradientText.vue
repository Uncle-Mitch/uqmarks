<template>
    <component
        :is="tag"
        class="gradient-text"
        :style="{
            background: `linear-gradient(${direction}, ${from}, ${to})`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'inline-block',
        }"
    >
        <slot />
    </component>
</template>

<script setup lang="ts">
const props = defineProps({
    from: { type: String },
    to: { type: String },
    direction: { type: String, default: "to right" },
    tag: { type: String, default: "h3" },
});
</script>

<style scoped>
.gradient-text {
    font-weight: 700;
}
</style>
