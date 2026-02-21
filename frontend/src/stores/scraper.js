import {defineStore} from 'pinia';
import axios from 'axios';

const API_URL = '/api';

export const useScraperStore = defineStore('scraper', {
    state: () => ({
        topics: [],
        currentTopic: null,
        quota: null,
        isLoading: false,
        error: null,
    }),

    actions: {
        async fetchQuota() {
            try {
                const response = await axios.get(`${API_URL}/quota`);
                this.quota = response.data;
            } catch (error) {
                console.error('Error fetching quota:', error);
                this.error = error.message;
            }
        },

        async fetchTopics() {
            this.isLoading = true;
            try {
                const response = await axios.get(`${API_URL}/topics`);
                this.topics = response.data;
            } catch (error) {
                console.error('Error fetching topics:', error);
                this.error = error.message;
            } finally {
                this.isLoading = false;
            }
        },

        async startScrape(keyword, maxVideos = 50) {
            this.isLoading = true;
            this.error = null;

            try {
                const response = await axios.post(`${API_URL}/scrape`, {
                    keyword,
                    max_videos: maxVideos,
                    fetch_comments: false,
                    fetch_transcripts: false,
                });

                const jobId = response.data.job_id;

                // Poll for completion
                return await this.pollScrapingJob(jobId);
            } catch (error) {
                console.error('Error starting scrape:', error);
                this.error = error.message;
                throw error;
            } finally {
                this.isLoading = false;
            }
        },

        async pollScrapingJob(jobId, maxAttempts = 60) {
            let attempts = 0;

            while (attempts < maxAttempts) {
                try {
                    const response = await axios.get(
                        `${API_URL}/scrape/status/${jobId}`,
                    );
                    const status = response.data;

                    if (status.status === 'completed') {
                        await this.fetchTopics();
                        return status;
                    } else if (status.status === 'failed') {
                        throw new Error(status.error || 'Scraping failed');
                    }

                    // Wait 2 seconds before next poll
                    await new Promise((resolve) => setTimeout(resolve, 2000));
                    attempts++;
                } catch (error) {
                    console.error('Error polling job:', error);
                    throw error;
                }
            }

            throw new Error('Scraping timeout');
        },

        async fetchTopicAnalysis(topicId) {
            this.isLoading = true;
            try {
                const response = await axios.get(
                    `${API_URL}/topics/${topicId}/analysis`,
                );
                this.currentTopic = response.data;
                return response.data;
            } catch (error) {
                console.error('Error fetching topic analysis:', error);
                this.error = error.message;
                throw error;
            } finally {
                this.isLoading = false;
            }
        },

        async fetchRecommendations(topicId) {
            try {
                const response = await axios.get(
                    `${API_URL}/topics/${topicId}/recommendations`,
                );
                return response.data;
            } catch (error) {
                console.error('Error fetching recommendations:', error);
                throw error;
            }
        },
    },
});
