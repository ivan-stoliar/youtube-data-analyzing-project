<template>
    <div v-if="isLoading" class="text-center py-12">
        <div
            class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-youtube"
        ></div>
        <p class="mt-4 text-gray-600">Loading analysis...</p>
    </div>

    <div v-else-if="analysis" class="space-y-8">
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div>
                <button
                    @click="$router.back()"
                    class="text-gray-600 hover:text-gray-900 mb-2 flex items-center"
                >
                    <svg
                        class="w-5 h-5 mr-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M10 19l-7-7m0 0l7-7m-7 7h18"
                        />
                    </svg>
                    Back to Dashboard
                </button>
                <h1 class="text-3xl font-bold text-gray-900">
                    {{ analysis.topic.main_keyword }}
                </h1>
                <p class="text-gray-500">
                    Analyzed on {{ formatDate(analysis.topic.created_at) }}
                </p>
            </div>
        </div>

        <!-- Key Metrics -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div
                class="card bg-gradient-to-br from-blue-500 to-blue-600 text-white"
            >
                <p class="text-blue-100 text-sm font-medium">Total Videos</p>
                <p class="text-3xl font-bold mt-2">
                    {{ analysis.stats.total_videos || 0 }}
                </p>
            </div>
            <div
                class="card bg-gradient-to-br from-green-500 to-green-600 text-white"
            >
                <p class="text-green-100 text-sm font-medium">
                    Active Channels
                </p>
                <p class="text-3xl font-bold mt-2">
                    {{ analysis.stats.total_channels || 0 }}
                </p>
            </div>
            <div
                class="card bg-gradient-to-br from-purple-500 to-purple-600 text-white"
            >
                <p class="text-purple-100 text-sm font-medium">Avg Views</p>
                <p class="text-3xl font-bold mt-2">
                    {{ formatNumber(analysis.stats.avg_views) }}
                </p>
            </div>
            <div
                class="card bg-gradient-to-br from-yellow-500 to-yellow-600 text-white"
            >
                <p class="text-yellow-100 text-sm font-medium">
                    Engagement Rate
                </p>
                <p class="text-3xl font-bold mt-2">
                    {{ analysis.stats.avg_engagement_rate?.toFixed(2) }}%
                </p>
            </div>
        </div>

        <!-- Recommendations -->
        <div
            v-if="recommendations"
            class="card bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
        >
            <h3 class="text-2xl font-bold mb-4">
                🎯 Strategic Recommendations
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div
                    v-for="(rec, index) in recommendations.recommendations"
                    :key="index"
                    class="bg-white/10 backdrop-blur rounded-lg p-4"
                >
                    <div class="flex items-start space-x-3">
                        <div class="flex-shrink-0">
                            <span
                                v-if="rec.type === 'opportunity'"
                                class="text-2xl"
                                >💡</span
                            >
                            <span
                                v-else-if="rec.type === 'warning'"
                                class="text-2xl"
                                >⚠️</span
                            >
                            <span v-else class="text-2xl">ℹ️</span>
                        </div>
                        <div>
                            <h4 class="font-semibold mb-1">{{ rec.title }}</h4>
                            <p class="text-sm text-white/90 mb-2">
                                {{ rec.description }}
                            </p>
                            <p class="text-xs font-medium text-yellow-200">
                                → {{ rec.action }}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row 1 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Top Channels Chart -->
            <div class="card">
                <h3 class="text-xl font-bold mb-4">
                    Top 10 Channels by Video Count
                </h3>
                <Bar :data="channelsChartData" :options="chartOptions" />
            </div>

            <!-- Shorts vs Regular -->
            <div class="card">
                <h3 class="text-xl font-bold mb-4">Shorts vs Regular Videos</h3>
                <Doughnut :data="shortsChartData" :options="doughnutOptions" />
            </div>
        </div>

        <!-- Charts Row 2 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Duration Distribution -->
            <div class="card">
                <h3 class="text-xl font-bold mb-4">
                    Video Duration Distribution
                </h3>
                <Bar :data="durationChartData" :options="chartOptions" />
            </div>

            <!-- Top Videos Performance -->
            <div class="card">
                <h3 class="text-xl font-bold mb-4">Top 10 Videos by Views</h3>
                <Bar
                    :data="topVideosChartData"
                    :options="horizontalChartOptions"
                />
            </div>
        </div>

        <!-- Top Videos Table -->
        <div class="card">
            <h3 class="text-xl font-bold mb-4">Top Performing Videos</h3>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                            >
                                Video
                            </th>
                            <th
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                            >
                                Channel
                            </th>
                            <th
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                            >
                                Type
                            </th>
                            <th
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                            >
                                Views
                            </th>
                            <th
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                            >
                                Likes
                            </th>
                            <th
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                            >
                                Engagement
                            </th>
                            <th
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                            >
                                Link
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <tr
                            v-for="video in analysis.top_videos.slice(0, 10)"
                            :key="video.youtube_video_id"
                            class="hover:bg-gray-50"
                        >
                            <td class="px-6 py-4">
                                <div
                                    class="text-sm font-medium text-gray-900 max-w-xs truncate"
                                >
                                    {{ video.title }}
                                </div>
                                <div class="text-xs text-gray-500">
                                    {{ formatDate(video.published_at) }}
                                </div>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-900">
                                {{ video.channel_name }}
                            </td>
                            <td class="px-6 py-4">
                                <span
                                    v-if="video.is_shorts"
                                    class="badge badge-warning"
                                    >Short</span
                                >
                                <span v-else class="badge badge-info"
                                    >Regular</span
                                >
                            </td>
                            <td
                                class="px-6 py-4 text-sm font-medium text-gray-900"
                            >
                                {{ formatNumber(video.view_count) }}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-900">
                                {{ formatNumber(video.like_count) }}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-900">
                                {{ video.engagement_rate }}%
                            </td>
                            <td class="px-6 py-4">
                                <a
                                    :href="`https://youtube.com/watch?v=${video.youtube_video_id}`"
                                    target="_blank"
                                    class="text-youtube hover:text-red-700"
                                >
                                    <svg
                                        class="w-5 h-5"
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                    >
                                        <path
                                            d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"
                                        />
                                        <path
                                            d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"
                                        />
                                    </svg>
                                </a>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Competition Analysis -->
        <div class="card bg-gray-50 border-2 border-gray-200">
            <h3 class="text-xl font-bold mb-4">🔍 Competition Analysis</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-white rounded-lg p-4">
                    <p class="text-gray-600 text-sm mb-1">Competition Level</p>
                    <p class="text-2xl font-bold text-gray-900">
                        {{ getCompetitionLevel(analysis.stats.total_channels) }}
                    </p>
                    <p class="text-xs text-gray-500 mt-1">
                        Based on {{ analysis.stats.total_channels }} active
                        channels
                    </p>
                </div>
                <div class="bg-white rounded-lg p-4">
                    <p class="text-gray-600 text-sm mb-1">Entry Barrier</p>
                    <p class="text-2xl font-bold text-gray-900">
                        {{ getEntryBarrier(analysis.stats.max_views) }}
                    </p>
                    <p class="text-xs text-gray-500 mt-1">
                        Max views: {{ formatNumber(analysis.stats.max_views) }}
                    </p>
                </div>
                <div class="bg-white rounded-lg p-4">
                    <p class="text-gray-600 text-sm mb-1">Recommended Action</p>
                    <p class="text-2xl font-bold text-youtube">
                        {{
                            getRecommendedAction(analysis.stats.total_channels)
                        }}
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue';
import {useRoute} from 'vue-router';
import {useScraperStore} from '../stores/scraper';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
} from 'chart.js';
import {Bar, Doughnut} from 'vue-chartjs';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
);

const route = useRoute();
const store = useScraperStore();

const analysis = ref(null);
const recommendations = ref(null);
const isLoading = computed(() => store.isLoading);

onMounted(async () => {
    const topicId = route.params.id;
    analysis.value = await store.fetchTopicAnalysis(topicId);
    recommendations.value = await store.fetchRecommendations(topicId);
});

// Chart data
const channelsChartData = computed(() => {
    if (!analysis.value) return {labels: [], datasets: []};

    return {
        labels: analysis.value.top_channels.map((c) => c.channel_name),
        datasets: [
            {
                label: 'Video Count',
                data: analysis.value.top_channels.map((c) => c.video_count),
                backgroundColor: 'rgba(255, 0, 0, 0.6)',
                borderColor: 'rgba(255, 0, 0, 1)',
                borderWidth: 1,
            },
        ],
    };
});

const shortsChartData = computed(() => {
    if (!analysis.value) return {labels: [], datasets: []};

    const shortsData = analysis.value.shorts_analysis;
    return {
        labels: shortsData.map((s) =>
            s.is_shorts ? 'Shorts' : 'Regular Videos',
        ),
        datasets: [
            {
                data: shortsData.map((s) => s.count),
                backgroundColor: ['#FF6384', '#36A2EB'],
                hoverBackgroundColor: ['#FF6384', '#36A2EB'],
            },
        ],
    };
});

const durationChartData = computed(() => {
    if (!analysis.value) return {labels: [], datasets: []};

    return {
        labels: analysis.value.duration_distribution.map(
            (d) => d.duration_range,
        ),
        datasets: [
            {
                label: 'Video Count',
                data: analysis.value.duration_distribution.map((d) => d.count),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
            },
        ],
    };
});

const topVideosChartData = computed(() => {
    if (!analysis.value) return {labels: [], datasets: []};

    const top10 = analysis.value.top_videos.slice(0, 10);
    return {
        labels: top10.map((v) => v.title.substring(0, 30) + '...'),
        datasets: [
            {
                label: 'Views',
                data: top10.map((v) => v.view_count),
                backgroundColor: 'rgba(153, 102, 255, 0.6)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1,
            },
        ],
    };
});

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false,
        },
    },
};

const horizontalChartOptions = {
    ...chartOptions,
    indexAxis: 'y',
};

const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
        },
    },
};

function formatNumber(num) {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

function getCompetitionLevel(channels) {
    if (channels < 20) return '🟢 Low';
    if (channels < 100) return '🟡 Medium';
    return '🔴 High';
}

function getEntryBarrier(maxViews) {
    if (maxViews < 10000) return '🟢 Low';
    if (maxViews < 100000) return '🟡 Medium';
    return '🔴 High';
}

function getRecommendedAction(channels) {
    if (channels < 20) return '✅ Enter Now';
    if (channels < 100) return '⚠️ Proceed with Caution';
    return '🛑 Find Sub-Niche';
}
</script>

<style scoped>
canvas {
    max-height: 300px;
}
</style>
