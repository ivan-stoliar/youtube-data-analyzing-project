import {createRouter, createWebHistory} from 'vue-router';
import Dashboard from './views/Dashboard.vue';
import TopicAnalysis from './views/TopicAnalysis.vue';

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard,
    },
    {
        path: '/topic/:id',
        name: 'TopicAnalysis',
        component: TopicAnalysis,
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;
