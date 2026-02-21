<template>
    <div class="space-y-8">
        <!-- Hero Section with Scrape Form -->
        <div class="card bg-gradient-to-r from-youtube to-red-600 text-white">
            <div class="max-w-3xl">
                <h2 class="text-3xl font-bold mb-2">
                    Discover Your Next YouTube Niche
                </h2>
                <p class="text-red-100 mb-6">
                    Analyze competition, find opportunities, and make
                    data-driven decisions before you start creating content.
                </p>

                <!-- Scrape Form -->
                <div class="bg-white rounded-lg p-6 text-gray-900">
                    <form @submit.prevent="handleScrape" class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium mb-2"
                                >Keyword / Niche</label
                            >
                            <input
                                v-model="keyword"
                                type="text"
                                placeholder="e.g., 'beginner woodworking', 'AI tutorials', 'vegan recipes'"
                                class="input-field text-gray-900"
                                :disabled="isScraping"
                                required
                            />
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-2">
                                Max Videos to Analyze ({{ maxVideos }})
                            </label>
                            <input
                                v-model.number="maxVideos"
                                type="range"
                                min="10"
                                max="100"
                                step="10"
                                class="w-full"
                                :disabled="isScraping"
                            />
                            <div
                                class="flex justify-between text-xs text-gray-500 mt-1"
                            >
                                <span>10 (Fast)</span>
                                <span>50 (Balanced)</span>
                                <span>100 (Comprehensive)</span>
                            </div>
                        </div>

                        <button
                            type="submit"
                            class="btn-primary w-full flex items-center justify-center space-x-2"
                            :disabled="isScraping"
                        >
                            <svg
                                v-if="isScraping"
                                class="animate-spin h-5 w-5"
                                fill="none"
                                viewBox="0 0 24 24"
                            >
                                <circle
                                    class="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    stroke-width="4"
                                ></circle>
                                <path
                                    class="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                ></path>
                            </svg>
                            <span>{{
                                isScraping ? 'Analyzing...' : 'Start Analysis'
                            }}</span>
                        </button>

                        <p v-if="scrapeError" class="text-red-600 text-sm">
                            {{ scrapeError }}
                        </p>
                    </form>
                </div>
            </div>
        </div>

        <!-- Topics List -->
        <div>
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-2xl font-bold text-gray-900">
                    Your Analyzed Niches
                </h3>
                <button @click="loadTopics" class="btn-secondary">
                    <svg
                        class="w-5 h-5 inline mr-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                    </svg>
                    Refresh
                </button>
            </div>

            <div v-if="isLoading" class="text-center py-12">
                <div
                    class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-youtube"
                ></div>
                <p class="mt-4 text-gray-600">Loading topics...</p>
            </div>

            <div v-else-if="topics.length === 0" class="card text-center py-12">
                <svg
                    class="w-16 h-16 mx-auto text-gray-400 mb-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                </svg>
                <h3 class="text-lg font-medium text-gray-900 mb-2">
                    No niches analyzed yet
                </h3>
                <p class="text-gray-500">
                    Start by entering a keyword above to begin your competitive
                    analysis.
                </p>
            </div>

            <div
                v-else
                class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
                <div
                    v-for="topic in topics"
                    :key="topic.id"
                    class="card hover:shadow-lg transition-shadow cursor-pointer"
                    @click="viewTopic(topic.id)"
                >
                    <div class="flex items-start justify-between mb-4">
                        <div>
                            <h4 class="text-lg font-semibold text-gray-900">
                                {{ topic.main_keyword }}
                            </h4>
                            <p class="text-sm text-gray-500">
                                {{ formatDate(topic.created_at) }}
                            </p>
                        </div>
                        <span class="badge badge-info"
                            >{{ topic.video_count }} videos</span
                        >
                    </div>

                    <div class="space-y-2">
                        <div class="flex items-center text-sm text-gray-600">
                            <svg
                                class="w-4 h-4 mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                                />
                            </svg>
                            {{ topic.video_count }} videos analyzed
                        </div>
                        <div class="flex items-center text-sm text-gray-600">
                            <svg
                                class="w-4 h-4 mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                                />
                            </svg>
                            {{ topic.channel_count }} channels
                        </div>
                    </div>

                    <button
                        class="mt-4 w-full text-youtube hover:text-red-700 font-medium text-sm"
                    >
                        View Full Analysis →
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue';
import {useRouter} from 'vue-router';
import {useScraperStore} from '../stores/scraper';

const router = useRouter();
const store = useScraperStore();

const keyword = ref('');
const maxVideos = ref(50);
const isScraping = ref(false);
const scrapeError = ref(null);

const topics = computed(() => store.topics);
const isLoading = computed(() => store.isLoading);

onMounted(() => {
    loadTopics();
});

async function loadTopics() {
    await store.fetchTopics();
}

async function handleScrape() {
    if (!keyword.value.trim()) return;

    isScraping.value = true;
    scrapeError.value = null;

    try {
        await store.startScrape(keyword.value, maxVideos.value);
        keyword.value = '';
        maxVideos.value = 50;
    } catch (error) {
        scrapeError.value = error.message || 'Failed to analyze niche';
    } finally {
        isScraping.value = false;
    }
}

function viewTopic(topicId) {
    router.push(`/topic/${topicId}`);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}
</script>
