<template>
    <div class="min-h-screen bg-gray-50">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div class="flex items-center space-x-3">
                        <svg
                            class="w-8 h-8 text-youtube"
                            fill="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"
                            />
                        </svg>
                        <div>
                            <h1 class="text-xl font-bold text-gray-900">
                                YouTube Niche Analyzer
                            </h1>
                            <p class="text-xs text-gray-500">
                                Competitive Intelligence Dashboard
                            </p>
                        </div>
                    </div>

                    <!-- API Quota Badge -->
                    <div v-if="quota" class="flex items-center space-x-2">
                        <span class="text-sm text-gray-600">API Quota:</span>
                        <div class="w-32 bg-gray-200 rounded-full h-2">
                            <div
                                class="h-2 rounded-full transition-all"
                                :class="getQuotaColor(quota.percentage)"
                                :style="{width: quota.percentage + '%'}"
                            ></div>
                        </div>
                        <span class="text-sm font-medium"
                            >{{ quota.used }} / {{ quota.limit }}</span
                        >
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <router-view />
        </main>

        <!-- Footer -->
        <footer class="bg-white border-t border-gray-200 mt-12">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <p class="text-center text-sm text-gray-500">
                    YouTube Niche Analyzer &copy; 2024 - Analyze, Compete,
                    Succeed
                </p>
            </div>
        </footer>
    </div>
</template>

<script setup>
import {onMounted, computed} from 'vue';
import {useScraperStore} from './stores/scraper';

const store = useScraperStore();

const quota = computed(() => store.quota);

onMounted(() => {
    store.fetchQuota();
    // Refresh quota every 30 seconds
    setInterval(() => store.fetchQuota(), 30000);
});

function getQuotaColor(percentage) {
    if (percentage < 50) return 'bg-green-500';
    if (percentage < 80) return 'bg-yellow-500';
    return 'bg-red-500';
}
</script>
