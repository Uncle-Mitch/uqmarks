import { createRouter, createWebHistory } from "vue-router";
import Home from "@/pages/Home.vue";
import Course from "@/pages/Course.vue";
import Quiz from "@/pages/Quiz.vue";
import Analytics from "@/pages/Analytics.vue";

const routes = [
    { path: "/", name: "Home", component: Home },
    { path: "/course", name: "Course", component: Course },
    { path: "/quiz", name: "Quiz", component: Quiz },
    { path: "/analytics", name: "Analytics", component: Analytics },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;
