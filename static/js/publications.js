class PublicationsManager {
    constructor() {
        this.publications = [];
        this.filteredPublications = [];
        this.currentType = 'research_article';
        this.currentPage = 0;
        this.itemsPerPage = 10;
        this.searchQuery = '';
        this.filters = {
            year: 'all',
            category: 'all',
            author: 'all'
        };
        
        this.init();
    }

    async init() {
        try {
            await this.loadPublications();
            this.setupEventListeners();
            this.populateFilters();
            this.filterAndDisplay();
        } catch (error) {
            console.error('Error initializing publications:', error);
            document.getElementById('results-count').textContent = 'Error loading publications';
        }
    }

    async loadPublications() {
        const response = await fetch('/static/json/publications.json');
        this.publications = await response.json();
    }

    setupEventListeners() {
        // Tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.type, e.target);
            });
        });

        // Search input
        const searchInput = document.getElementById('search');
        searchInput.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase();
            this.currentPage = 0;
            this.filterAndDisplay();
        });

        // Filter selects
        document.getElementById('year').addEventListener('change', (e) => {
            this.filters.year = e.target.value;
            this.currentPage = 0;
            this.filterAndDisplay();
        });

        document.getElementById('category').addEventListener('change', (e) => {
            this.filters.category = e.target.value;
            this.currentPage = 0;
            this.filterAndDisplay();
        });

        document.getElementById('author').addEventListener('change', (e) => {
            this.filters.author = e.target.value;
            this.currentPage = 0;
            this.filterAndDisplay();
        });

        // Reset filters button
        document.getElementById('reset-filters').addEventListener('click', () => {
            this.resetFilters();
        });

        // Load more button
        document.getElementById('load-more').addEventListener('click', () => {
            this.currentPage++;
            this.displayPublications(false);
        });
    }

    populateFilters() {
        // Populate year filter
        const years = [...new Set(this.publications.map(p => p.year))]
            .sort((a, b) => b - a);
        const yearSelect = document.getElementById('year');
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearSelect.appendChild(option);
        });

        // Populate category filter
        const categories = [...new Set(
            this.publications.flatMap(p => p.research_area || [])
        )].sort();
        const categorySelect = document.getElementById('category');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = this.formatCategoryName(category);
            categorySelect.appendChild(option);
        });

        // Populate author filter
        const authors = [...new Set(
            this.publications.flatMap(p => p.authors)
        )].sort();
        const authorSelect = document.getElementById('author');
        authors.forEach(author => {
            const option = document.createElement('option');
            option.value = author;
            option.textContent = author;
            authorSelect.appendChild(option);
        });
    }

    formatCategoryName(category) {
        return category.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    switchTab(type, button) {
        // Update tab appearance
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.className = 'px-4 py-2 text-sm font-medium border-b-2 border-transparent hover:text-blue-600 hover:border-blue-600 tab-button';
        });
        button.className = 'px-4 py-2 text-sm font-medium border-b-2 border-blue-600 text-blue-600 tab-button';

        // Update current type and reset pagination
        this.currentType = type;
        this.currentPage = 0;
        
        // Update section title
        const titles = {
            'research_article': 'Journal Articles',
            'review_article': 'Reviews',
            'book_chapter': 'Book Chapters',
            'preprint': 'Preprints'
        };
        document.getElementById('section-title').textContent = titles[type];

        this.filterAndDisplay();
    }

    filterAndDisplay() {
        this.filteredPublications = this.publications.filter(pub => {
            // Filter by type
            if (pub.type !== this.currentType) return false;

            // Filter by search query
            if (this.searchQuery) {
                const searchText = `${pub.title} ${pub.authors.join(' ')} ${(pub.research_area || []).join(' ')}`.toLowerCase();
                if (!searchText.includes(this.searchQuery)) return false;
            }

            // Filter by year
            if (this.filters.year !== 'all' && pub.year.toString() !== this.filters.year) return false;

            // Filter by category
            if (this.filters.category !== 'all' && !(pub.research_area || []).includes(this.filters.category)) return false;

            // Filter by author
            if (this.filters.author !== 'all' && !pub.authors.includes(this.filters.author)) return false;

            return true;
        });

        this.displayPublications(true);
    }

    displayPublications(clearExisting = true) {
        const container = document.getElementById('publications-list');
        const loadMoreButton = document.getElementById('load-more');

        if (clearExisting) {
            container.innerHTML = '';
            this.currentPage = 0;
        }

        const startIndex = this.currentPage * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const publicationsToShow = this.filteredPublications.slice(startIndex, endIndex);

        publicationsToShow.forEach(pub => {
            const pubElement = this.createPublicationElement(pub);
            container.appendChild(pubElement);
        });

        // Update results count
        const totalResults = this.filteredPublications.length;
        const currentCount = Math.min(endIndex, totalResults);
        document.getElementById('results-count').textContent = 
            `Showing ${currentCount} of ${totalResults} ${this.getTypeName()}`;

        // Show/hide load more button
        if (endIndex < totalResults) {
            loadMoreButton.style.display = 'block';
        } else {
            loadMoreButton.style.display = 'none';
        }
    }

    getTypeName() {
        const typeNames = {
            'research_article': 'articles',
            'review_article': 'reviews',
            'book_chapter': 'chapters',
            'preprint': 'preprints'
        };
        return typeNames[this.currentType] || 'publications';
    }

    createPublicationElement(pub) {
        const div = document.createElement('div');
        div.className = 'rounded-lg border bg-white shadow-sm overflow-hidden transition-all hover:border-blue-300';

        const researchAreas = (pub.research_area || []).map(area => 
            `<span class="inline-flex items-center rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-600">
                ${this.formatCategoryName(area)}
            </span>`
        ).join(' ');

        const abstract = pub.abstract ? 
            `<p class="text-sm text-gray-500 line-clamp-3">${pub.abstract}</p>` : '';

        div.innerHTML = `
            <div class="p-6">
                <div class="grid gap-4 md:grid-cols-4">
                    <div class="md:col-span-3 space-y-3">
                        <div class="space-y-1">
                            <div class="flex items-center gap-2">
                                <span class="inline-flex items-center rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-600">
                                    ${pub.year}
                                </span>
                                ${researchAreas}
                            </div>
                            <h3 class="text-xl font-bold">${pub.title}</h3>
                            <p class="text-sm text-gray-500">
                                <span class="font-medium">Authors:</span> ${pub.authors.join(', ')}
                            </p>
                            <p class="text-sm text-gray-500">
                                <span class="font-medium">Journal:</span> ${pub.journal}${pub.volume ? `, ${pub.volume}` : ''}${pub.pages ? `, ${pub.pages}` : ''}
                            </p>
                        </div>
                        ${abstract}
                    </div>

                    <div class="flex flex-col justify-center gap-3 md:border-l md:pl-6">
                        ${pub.pubmed_url ? `
                        <a href="${pub.pubmed_url}" target="_blank" class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-gray-200 bg-white hover:bg-gray-100 hover:text-blue-600 h-10 px-4 py-2 w-full gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" class="h-4 w-4">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" x2="21" y1="14" y2="3"></line>
                            </svg>
                            <span>View on PubMed</span>
                        </a>` : ''}
                        
                        ${pub.doi ? `
                        <a href="${pub.doi}" target="_blank" class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-gray-200 bg-white hover:bg-gray-100 hover:text-blue-600 h-10 px-4 py-2 w-full gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" class="h-4 w-4">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" x2="21" y1="14" y2="3"></line>
                            </svg>
                            <span>Journal Website</span>
                        </a>` : ''}
                        
                        <a href="#" class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-gray-50 h-10 px-4 py-2 w-full gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" class="h-4 w-4">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" x2="12" y1="15" y2="3"></line>
                            </svg>
                            <span>PDF</span>
                        </a>
                    </div>
                </div>
            </div>
        `;

        return div;
    }

    resetFilters() {
        // Reset search input
        document.getElementById('search').value = '';
        this.searchQuery = '';

        // Reset filter selects
        document.getElementById('year').value = 'all';
        document.getElementById('category').value = 'all';
        document.getElementById('author').value = 'all';

        // Reset filter values
        this.filters = {
            year: 'all',
            category: 'all',
            author: 'all'
        };

        // Reset pagination and display
        this.currentPage = 0;
        this.filterAndDisplay();
    }
}

// Initialize the publications manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PublicationsManager();
});