/**
 * API Module - Centralized API calls and data fetching
 */

class ParksAPI {
    constructor() {
        this.baseURL = '';
    }

    async fetchParks(limit = 10, filters = {}) {
        try {
            const params = new URLSearchParams({
                limit: limit.toString(),
                ...filters
            });

            const response = await fetch(`${this.baseURL}/api/parks?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching parks:', error);
            throw error;
        }
    }

    async fetchPark(id) {
        try {
            const response = await fetch(`${this.baseURL}/api/parks/${id}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching park:', error);
            throw error;
        }
    }

    async fetchSpecies(limit = 10, filters = {}) {
        try {
            const params = new URLSearchParams({
                limit: limit.toString(),
                ...filters
            });

            const response = await fetch(`${this.baseURL}/api/species?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching species:', error);
            throw error;
        }
    }

    async searchParks(query, filters = {}) {
        try {
            const searchFilters = { ...filters, query };
            return await this.fetchParks(50, searchFilters);
        } catch (error) {
            console.error('Error searching parks:', error);
            throw error;
        }
    }

    async getWeather(parkId) {
        try {
            const response = await fetch(`${this.baseURL}/api/parks/${parkId}/weather`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching weather:', error);
            throw error;
        }
    }
}

// Export for use in other modules
window.ParksAPI = ParksAPI;
