document.addEventListener('DOMContentLoaded', () => {
    // Configuration
    const PUBLICATIONS_JSON_PATH = '/static/data/publications.json'; // Adjust if your JSON is elsewhere
    const ITEMS_PER_PAGE = 5; // Number of items to load at a time

    // DOM Elements
    const publicationsListContainer = document.getElementById('publications-list');
    const searchInput = document.getElementById('search');
    const yearFilter = document.getElementById('year');
    const categoryFilter = document.getElementById('category'); // Research Area
    const affiliationFilter = document.getElementById('affiliation');
    const resetFiltersButton = document.getElementById('reset-filters');
    const loadMoreButton = document.getElementById('load-more');
    const resultsCountElement = document.getElementById('results-count');
    const sectionTitleElement = document.getElementById('section-title');
    const tabButtons = document.querySelectorAll('.tab-button');

    // State Variables
    let allPublications = []; // Stores all fetched publications, original sort order
    let currentlyDisplayedPublications = []; // Stores currently filtered and sorted publications for display
    let currentPage = 1;
    let activeTabType = 'research_article'; // Default active tab: 'research_article' for 'data_article' type

    // --- Initialization ---
    async function initializeApp() {
        try {
            const rawData = await fetchPublications();
            // Sort publications by year (descending) then title (ascending) as a default
            allPublications = rawData.sort((a, b) => {
                if (b.year !== a.year) {
                    return b.year - a.year;
                }
                return a.title.localeCompare(b.title);
            });

            populateDropdowns();
            setupEventListeners();
            setActiveTab(activeTabType); // Set initial active tab styles and title
            applyFiltersAndRender();
        } catch (error) {
            console.error("Error initializing app:", error);
            if (publicationsListContainer) {
                publicationsListContainer.innerHTML = "<p class='text-red-500'>Failed to load publications. Please try again later.</p>";
            }
             if (resultsCountElement) {
                resultsCountElement.textContent = "Error loading data";
            }
        }
    }

    async function fetchPublications() {
        const response = await fetch(PUBLICATIONS_JSON_PATH);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} - Failed to fetch ${PUBLICATIONS_JSON_PATH}`);
        }
        return await response.json();
    }

    // --- Populate UI Elements ---
    function populateDropdowns() {
        const years = [...new Set(allPublications.map(p => p.year))].sort((a, b) => b - a);
        const researchAreas = [...new Set(allPublications.map(p => p.research_area).filter(Boolean))].sort();
        const affiliations = [...new Set(allPublications.map(p => p.project_affiliation).filter(Boolean))].sort();

        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearFilter.appendChild(option);
        });

        researchAreas.forEach(area => {
            const option = document.createElement('option');
            option.value = area;
            option.textContent = area;
            categoryFilter.appendChild(option);
        });

        affiliations.forEach(affiliation => {
            const option = document.createElement('option');
            option.value = affiliation;
            option.textContent = affiliation.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            affiliationFilter.appendChild(option);
        });
    }

    function setActiveTab(activeType) {
        activeTabType = activeType;
        tabButtons.forEach(button => {
            if (button.dataset.type === activeType) {
                button.classList.add('border-blue-600', 'text-blue-600');
                button.classList.remove('border-transparent', 'hover:text-gray-600', 'hover:border-gray-300'); // Adjusted hover classes
                if (sectionTitleElement) sectionTitleElement.textContent = button.textContent.trim();
            } else {
                button.classList.remove('border-blue-600', 'text-blue-600');
                button.classList.add('border-transparent', 'hover:text-gray-600', 'hover:border-gray-300'); // Adjusted hover classes
            }
        });
    }

    // --- Event Listeners Setup ---
    function setupEventListeners() {
        searchInput.addEventListener('input', handleFilterChange);
        yearFilter.addEventListener('change', handleFilterChange);
        categoryFilter.addEventListener('change', handleFilterChange);
        affiliationFilter.addEventListener('change', handleFilterChange);
        
        resetFiltersButton.addEventListener('click', handleResetFilters);
        loadMoreButton.addEventListener('click', handleLoadMore);

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                setActiveTab(button.dataset.type);
                handleFilterChange(); // Re-filter and render for the new tab
            });
        });
    }

    // --- Filtering Logic ---
    function filterPublications() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedYear = yearFilter.value;
        const selectedCategory = categoryFilter.value;
        const selectedAffiliation = affiliationFilter.value;

        currentlyDisplayedPublications = allPublications.filter(pub => {
            const typeMatch = activeTabType === 'research_article' ?
                pub.type === 'data_article' :
                ['review_article', 'opinion_piece', 'book_chapter'].includes(pub.type);

            const searchMatch = !searchTerm ||
                pub.title.toLowerCase().includes(searchTerm) ||
                pub.authors.toLowerCase().includes(searchTerm) ||
                (pub.research_area && pub.research_area.toLowerCase().includes(searchTerm));

            const yearMatch = selectedYear === 'all' || pub.year.toString() === selectedYear;
            const categoryMatch = selectedCategory === 'all' || pub.research_area === selectedCategory;
            const affiliationMatch = selectedAffiliation === 'all' || pub.project_affiliation === selectedAffiliation;

            return typeMatch && searchMatch && yearMatch && categoryMatch && affiliationMatch;
        });
    }

    // --- Rendering Logic ---
    function applyFiltersAndRender() {
        currentPage = 1; // Reset to first page on any filter change
        filterPublications();
        renderPublicationItems();
        updateResultsCount();
        updateLoadMoreButtonVisibility();
    }
    
    function renderPublicationItems() {
        if (currentPage === 1) {
            publicationsListContainer.innerHTML = ''; // Clear previous items for a new filter/page 1
        }

        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIndex = startIndex + ITEMS_PER_PAGE;
        const itemsToRender = currentlyDisplayedPublications.slice(startIndex, endIndex);

        if (itemsToRender.length === 0 && currentPage === 1) {
            publicationsListContainer.innerHTML = "<p>No publications found matching your criteria.</p>";
        } else {
            itemsToRender.forEach(pub => {
                const pubElement = createPublicationElement(pub);
                publicationsListContainer.appendChild(pubElement);
            });
        }
    }

    function createPublicationElement(publication) {
        const div = document.createElement('div');
        div.className = "rounded-lg border bg-white shadow-sm overflow-hidden transition-all hover:border-blue-300";

        let doiLink = '#';
        let pubMedLink = '#';
        if (publication.doi) {
            if (publication.doi.startsWith('http')) {
                doiLink = publication.doi;
            } else {
                doiLink = `https://doi.org/${publication.doi}`;
            }
            // Basic extraction for PubMed link, assumes DOI is the part after "doi.org/" or the whole string if not a URL
            const doiIdentifier = publication.doi.includes('doi.org/') ? publication.doi.split('doi.org/')[1] : publication.doi;
            pubMedLink = `https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(doiIdentifier)}`;
        }

        const pdfLink = publication.pdf_url || '#'; // Use provided pdf_url or fallback

        div.innerHTML = `
            <div class="p-6">
                <div class="grid gap-4 md:grid-cols-4">
                    <div class="md:col-span-3 space-y-3">
                        <div class="space-y-1">
                            <div class="flex items-center gap-2">
                                <span class="inline-flex items-center rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-600">
                                    ${publication.year}
                                </span>
                                ${publication.research_area ? `
                                <span class="inline-flex items-center rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-600">
                                    ${publication.research_area}
                                </span>` : ''}
                            </div>
                            <h3 class="text-xl font-bold">${publication.title}</h3>
                            <p class="text-sm text-gray-500">
                                <span class="font-medium">Authors:</span> ${publication.authors}
                            </p>
                            <p class="text-sm text-gray-500">
                                <span class="font-medium">Journal:</span> ${publication.journal}
                            </p>
                        </div>
                        ${publication.abstract ? `
                        <p class="text-sm text-gray-500 line-clamp-3">
                            ${publication.abstract}
                        </p>` : ''}
                    </div>
                    <div class="flex flex-col justify-center gap-3 md:border-l md:pl-6">
                        <a href="${pubMedLink}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-gray-200 bg-white hover:bg-gray-100 hover:text-blue-600 h-10 px-4 py-2 w-full gap-2 ${!publication.doi ? 'opacity-50 pointer-events-none' : ''}">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" class="h-4 w-4"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" x2="21" y1="14" y2="3"></line></svg>
                            <span>View on PubMed</span>
                        </a>
                        <a href="${doiLink}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-gray-200 bg-white hover:bg-gray-100 hover:text-blue-600 h-10 px-4 py-2 w-full gap-2 ${!publication.doi ? 'opacity-50 pointer-events-none' : ''}">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" class="h-4 w-4"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" x2="21" y1="14" y2="3"></line></svg>
                            <span>Journal Website</span>
                        </a>
                        <a href="${pdfLink}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-gray-50 h-10 px-4 py-2 w-full gap-2 ${pdfLink === '#' ? 'opacity-50 pointer-events-none' : ''}">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" class="h-4 w-4"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" x2="12" y1="15" y2="3"></line></svg>
                            <span>PDF</span>
                        </a>
                    </div>
                </div>
            </div>
        `;
        return div;
    }

    // --- UI Updates ---
    function updateResultsCount() {
        const totalFiltered = currentlyDisplayedPublications.length;
        const currentlyShown = Math.min(totalFiltered, currentPage * ITEMS_PER_PAGE);
        if (resultsCountElement) {
            resultsCountElement.textContent = `Showing ${currentlyShown} of ${totalFiltered} results`;
        }
    }

    function updateLoadMoreButtonVisibility() {
        const totalFiltered = currentlyDisplayedPublications.length;
        if (currentPage * ITEMS_PER_PAGE >= totalFiltered) {
            loadMoreButton.style.display = 'none';
        } else {
            loadMoreButton.style.display = 'inline-flex';
        }
    }

    // --- Event Handlers ---
    function handleFilterChange() {
        applyFiltersAndRender();
    }

    function handleLoadMore() {
        currentPage++;
        renderPublicationItems(); // Append next page items
        updateResultsCount();
        updateLoadMoreButtonVisibility();
    }

    function handleResetFilters() {
        searchInput.value = '';
        yearFilter.value = 'all';
        categoryFilter.value = 'all';
        affiliationFilter.value = 'all';
        // activeTabType remains the same unless you want to reset it too.
        // If you want to reset to the default tab:
        // setActiveTab('research_article'); 
        applyFiltersAndRender();
    }

    // Start the application
    initializeApp();
});