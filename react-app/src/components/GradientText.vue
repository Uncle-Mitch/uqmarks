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

.gradient-text.page-heading {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: clamp(32px, 4vw, 48px);
    font-weight: 700;
    letter-spacing: -1.5px;
    line-height: 1.15;
}
</style>
