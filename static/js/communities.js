
// Handle map open/close state
document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('mapContainer');
    const mapToggle = document.getElementById('mapToggle');
    const communitiesContainer = document.getElementById('communitiesContainer');
    const communitiesGrid = document.getElementById('communitiesGrid');

    // Function to toggle map visibility
    function toggleMap() {
        const isMapOpen = mapContainer.classList.contains('hidden');
        mapContainer.classList.toggle('hidden');
        mapContainer.classList.toggle('map-open', !isMapOpen);
        
        // Update communities container height and scrolling
        if (!isMapOpen) {
            communitiesContainer.style.height = '600px';
            communitiesContainer.style.overflowY = 'auto';
        } else {
            communitiesContainer.style.height = 'auto';
            communitiesContainer.style.overflowY = 'visible';
        }

        // Update grid spacing
        const gapClass = communitiesGrid.getAttribute('data-map-open-class');
        if (gapClass) {
            communitiesGrid.style.gap = isMapOpen ? gapClass : '1rem';
        }
    }

    // Initialize map toggle button text
    mapToggle.textContent = mapContainer.classList.contains('hidden') 
        ? 'Show Map' 
        : 'Hide Map';

    // Add click event listener to map toggle button
    mapToggle.addEventListener('click', toggleMap);
});

// Load configuration
const config = {
    OPENCAGE_API_KEY: '48bcf64904a14f418e6920d63a9945a8' // Replace with your actual key if different
};

let communities = [];
let filteredCommunities = [];
let map = null;
let markerClusterGroup = null;
let isMapVisible = false;

// SVGs for map toggle button
const svgShowMap = `
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon>
<line x1="9" x2="9" y1="3" y2="18"></line>
<line x1="15" x2="15" y1="6" y2="21"></line>
</svg>
<span>Show Map</span>`;

const svgHideMap = `
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
<line x1="8" x2="21" y1="6" y2="6"></line>
<line x1="8" x2="21" y1="12" y2="12"></line>
<line x1="8" x2="21" y1="18" y2="18"></line>
<line x1="3" x2="3.01" y1="6" y2="6"></line>
<line x1="3" x2="3.01" y1="12" y2="12"></line>
<line x1="3" x2="3.01" y1="18" y2="18"></line>
</svg>
<span>Hide Map</span>`;

// Helper functions for styling consistency
const getCostBadgeColor = (cost) => {
    switch (String(cost)) {
    case "Free":
    case "0":
        return "bg-green-100 text-green-700 border-green-200";
    case "Paid": // This will catch any non-Free, non-NA string
        return "bg-orange-100 text-orange-700 border-orange-200";
    case "NA":
    default: // Handles undefined, null, or other unexpected values as "NA" for badge
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
};

const getCostDisplayText = (cost) => {
    const costStr = String(cost);
    if (costStr === "NA" || costStr === "null" || costStr === "undefined") return "Contact for pricing";
    if (costStr === "Free" || costStr === "0") return "Free";
    return costStr; // For "Paid" or specific prices
};


document.addEventListener('DOMContentLoaded', function() {
    loadCommunities();
    setupEventListeners();
    adjustLayoutForMap(); // Initial layout adjustment
});

async function loadCommunities() {
    showLoadingState();
    try {
        const response = await fetch('/static/data/communities.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        communities = await response.json();
        filteredCommunities = [...communities];
        
        populateSportFilter();
        renderCommunities(); // This will also update the count
    } catch (error) {
        console.error('Error loading communities:', error);
        showNoResults();
        document.getElementById('communitiesCount').textContent = 'Communities (0)';
    } finally {
        hideLoadingState();
    }
}

function setupEventListeners() {
    document.getElementById('mapToggle').addEventListener('click', toggleMap);
    document.getElementById('searchInput').addEventListener('input', debounce(handleSearch, 300));
    document.getElementById('costFilter').addEventListener('change', handleFilter);
    document.getElementById('studentFilter').addEventListener('change', handleFilter);
    document.getElementById('sportFilter').addEventListener('change', handleFilter);
    document.getElementById('clearFilters').addEventListener('click', clearFilters);
}

function populateSportFilter() {
    const sports = new Set();
    communities.forEach(community => {
        if (community.Sport) {
            community.Sport.split(',').forEach(sport => {
                sports.add(sport.trim());
            });
        }
    });

    const sportFilterEl = document.getElementById('sportFilter');
    // Clear existing options except the first one ("All Sports")
    Array.from(sportFilterEl.options).slice(1).forEach(option => sportFilterEl.remove(option.index));
    
    Array.from(sports).sort().forEach(sport => {
        const option = document.createElement('option');
        option.value = sport;
        option.textContent = sport;
        sportFilterEl.appendChild(option);
    });
}

function adjustLayoutForMap() {
    const mapContainer = document.getElementById('mapContainer');
    const communitiesWrapper = document.getElementById('communitiesWrapper');
    const communitiesContainer = document.getElementById('communitiesContainer');
    const communitiesGrid = document.getElementById('communitiesGrid');
    const mapToggle = document.getElementById('mapToggle');

    if (isMapVisible) {
        mapContainer.classList.remove('hidden');
        mapContainer.classList.add('lg:w-1/2');
        communitiesWrapper.classList.remove('lg:w-full'); // Explicitly remove if it was set
        communitiesWrapper.classList.add('lg:w-1/2');
        
        communitiesContainer.style.height = '600px'; // Match map height
        communitiesContainer.style.overflowY = 'auto';
        communitiesContainer.classList.add('custom-scrollbar'); // Ensure this class is defined in your CSS if needed

        communitiesGrid.classList.remove('md:grid-cols-2', 'xl:grid-cols-3');
        communitiesGrid.classList.add('grid-cols-1'); // Simpler, always single column if map visible
        communitiesGrid.classList.add('md:grid-cols-1', 'xl:grid-cols-1');


        mapToggle.innerHTML = svgHideMap;
        // tsx styles for "Hide map": border border-orange-300 bg-white hover:bg-orange-100 hover:text-orange-600 text-orange-700
        // Keep existing classes and let the initial setup define the look:
        // mapToggle.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        // mapToggle.classList.add('bg-gray-600', 'hover:bg-gray-700'); // Example of alternative style
        
        if (!map) {
            initializeMap();
        } else {
            map.invalidateSize();
            updateMapMarkers();
        }
    } else {
        mapContainer.classList.add('hidden');
        mapContainer.classList.remove('lg:w-1/2');
        communitiesWrapper.classList.remove('lg:w-1/2');
        communitiesWrapper.classList.add('lg:w-full'); // Ensure it takes full width when map is hidden

        communitiesContainer.style.height = 'auto';
        communitiesContainer.style.overflowY = 'visible';
        communitiesContainer.classList.remove('custom-scrollbar');

        communitiesGrid.classList.remove('grid-cols-1', 'md:grid-cols-1', 'xl:grid-cols-1');
        communitiesGrid.classList.add('md:grid-cols-2', 'xl:grid-cols-3');

        mapToggle.innerHTML = svgShowMap;
        // tsx styles for "Show map": border border-orange-300 bg-white hover:bg-orange-100 hover:text-orange-600 text-orange-700
        // mapToggle.classList.remove('bg-gray-600', 'hover:bg-gray-700');
        // mapToggle.classList.add('bg-blue-600', 'hover:bg-blue-700'); // Example
    }
    renderCommunities(); // Re-render to apply size-dependent classes in cards if any
}

function toggleMap() {
    isMapVisible = !isMapVisible;
    adjustLayoutForMap();
}

function initializeMap() {
    try {
        map = L.map('map').setView([52.3676, 4.9041], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
        }).addTo(map);
        markerClusterGroup = L.markerClusterGroup();
        map.addLayer(markerClusterGroup);
        updateMapMarkers();
        map.invalidateSize();
    } catch (error) {
        console.error('Error initializing map:', error);
        const mapToggle = document.getElementById('mapToggle');
        mapToggle.disabled = true;
        mapToggle.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-red-500"><path d="m21.73 18.73-5-5L8 18l-6-6 6-6 1.27 1.27"></path><path d="M12 18러스터 그룹에 추가합니다.다리 사이"></path></svg><span>Map Error</span>`;
        // Show the placeholder in the map div again if init fails
        document.getElementById('map').innerHTML = `
            <div class="w-full h-full bg-gradient-to-br from-orange-100 to-red-100 flex items-center justify-center">
            <div class="text-center text-orange-700">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-16 w-16 mx-auto mb-4"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" x2="9" y1="3" y2="18"></line><line x1="15" x2="15" y1="6" y2="21"></line></svg>
                <p class="text-lg font-semibold">Map Currently Unavailable</p>
                <p class="text-sm text-red-600">There was an issue loading the map.</p>
            </div>
            </div>`;
    }
}

function updateMapMarkers() {
    if (!map || !markerClusterGroup) return;
    try {
        markerClusterGroup.clearLayers();
        filteredCommunities.forEach(community => {
            if (community.Location && community.Name) {
                geocodeAddress(community.Location, community);
            }
        });
    } catch (error) {
        console.error('Error updating map markers:', error);
    }
}

async function geocodeAddress(address, community) {
    const apiKey = config.OPENCAGE_API_KEY;
    if (!apiKey || apiKey === 'YOUR_OPENCAGE_API_KEY' || apiKey === '48bcf64904a14f418e6920d63a9945a8') { // Added the example key here
        console.warn("OpenCage API key is a sample or not configured. Geocoding might be limited or fail. Address:", address);
        // Do not attempt to geocode if using the placeholder key publicly or if it's missing.
        // You might want to add a visual indicator on the map or card that location is approximate or unavailable.
        if (apiKey === '48bcf64904a14f418e6920d63a9945a8') return; // Don't proceed with the example key for actual calls
    }

    try {
        const response = await fetch(`https://api.opencagedata.com/geocode/v1/json?q=${encodeURIComponent(address)}&key=${apiKey}&pretty=1&limit=1&countrycode=NL&bounds=4.7271_52.2780_5.0791_52.4311`);
        const data = await response.json();
        if (data.results && data.results.length > 0) {
            const { lat, lng } = data.results[0].geometry;
            const marker = L.marker([lat, lng], {
                title: community.Name,
                icon: L.icon({
                    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
                    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34]
                })
            });
            marker.bindPopup(`
                <div class="p-1 max-w-xs">
                    <h3 class="font-bold text-md mb-1">${community.Name || 'N/A'}</h3>
                    <p class="text-xs mb-0.5">Sport: ${community.Sport || 'N/A'}</p>
                    <p class="text-xs mb-0.5">Cost: ${getCostDisplayText(community.Cost)}</p>
                    <p class="text-xs mb-0.5">Student: ${community['Student-based'] === 'Yes' ? 'Yes' : (community['Student-based'] === 'No' ? 'No' : 'N/A')}</p>
                    <p class="text-xs mb-0.5">Location: ${community.Location || 'N/A'}</p>
                    ${community.website ? `<p class="text-xs"><a href="${community.website}" target="_blank" class="text-orange-600 hover:text-orange-700 font-semibold">Visit Website</a></p>` : ''}
                </div>
            `);
            markerClusterGroup.addLayer(marker);
        } else {
            console.warn(`Geocoding failed for address: ${address}. No results. Response:`, data);
        }
    } catch (error) {
        console.error(`Error geocoding address '${address}':`, error);
    }
}

function handleSearch() { applyFilters(); }
function handleFilter() { applyFilters(); }

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const costFilterValue = document.getElementById('costFilter').value; // "all", "Free", "Paid", "NA"
    const studentFilterValue = document.getElementById('studentFilter').value; // "all", "Yes", "No"
    const sportFilterValue = document.getElementById('sportFilter').value; // "all", or specific sport

    filteredCommunities = communities.filter(community => {
        const name = (community.Name || '').toLowerCase();
        const sport = (community.Sport || '').toLowerCase();
        const location = (community.Location || '').toLowerCase();
        
        const matchesSearch = !searchTerm || 
            name.includes(searchTerm) ||
            sport.includes(searchTerm) ||
            location.includes(searchTerm);

        let communityCostNormalized = String(community.Cost).toLowerCase();
        if (communityCostNormalized === "0") communityCostNormalized = "free";

        const matchesCost = costFilterValue === "all" ||
            (costFilterValue === "Free" && communityCostNormalized === "free") ||
            (costFilterValue === "Paid" && communityCostNormalized !== "free" && communityCostNormalized !== "na") ||
            (costFilterValue === "NA" && communityCostNormalized === "na");
        
        const communityStudentBased = community['Student-based'] || ''; // "Yes", "No", ""
        const matchesStudent = studentFilterValue === "all" || communityStudentBased === studentFilterValue;
        
        const communitySport = community.Sport || '';
        const matchesSport = sportFilterValue === "all" || communitySport.toLowerCase().includes(sportFilterValue.toLowerCase());

        return matchesSearch && matchesCost && matchesStudent && matchesSport;
    });

    renderCommunities();
    if (isMapVisible && map) { // Ensure map is initialized
        updateMapMarkers();
    }
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('costFilter').value = 'all';
    document.getElementById('studentFilter').value = 'all';
    document.getElementById('sportFilter').value = 'all';
    
    filteredCommunities = [...communities];
    renderCommunities();
    if (isMapVisible && map) {
        updateMapMarkers();
    }
}

function renderCommunities() {
    const grid = document.getElementById('communitiesGrid');
    const noResultsEl = document.getElementById('noResults');
    const communitiesCountEl = document.getElementById('communitiesCount');

    communitiesCountEl.textContent = `Communities (${filteredCommunities.length})`;

    if (filteredCommunities.length === 0) {
        grid.innerHTML = '';
        grid.classList.add('hidden'); // Hide grid if it was visible
        noResultsEl.classList.remove('hidden');
        return;
    }

    noResultsEl.classList.add('hidden');
    grid.classList.remove('hidden'); // Show grid
    
    const cardClasses = isMapVisible ? "text-sm" : ""; // For elements inside the card that might change size

    grid.innerHTML = filteredCommunities.map(community => {
        const communityName = community.Name || 'Unnamed Community';
        const currentCostBadgeColor = getCostBadgeColor(community.Cost);
        const currentCostDisplayText = getCostDisplayText(community.Cost);

        // Placeholder for image
        const imagePlaceholderSvg = `
        <div class="absolute inset-0 flex w-full h-full items-center justify-center bg-gradient-to-br from-orange-100 to-red-100">
            <div class="text-center text-orange-700 p-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-12 w-12 mx-auto mb-2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                <p class="text-sm font-medium">${communityName}</p>
            </div>
        </div>`;

        const imageSectionClass = isMapVisible ? "aspect-[4/3]" : "aspect-video";
        const contentPaddingClass = isMapVisible ? "p-4" : "p-6";
        const titleClass = isMapVisible ? "text-base" : "text-lg";
        const detailsMbClass = isMapVisible ? "mb-3" : "mb-4";
        const iconSizeClass = isMapVisible ? "h-3 w-3" : "h-4 w-4";
        const sportIconOuter = isMapVisible ? "w-3 h-3" : "w-4 h-4";
        const sportIconInner = isMapVisible ? "text-[10px]" : "text-xs";
        const actionButtonHeightClass = isMapVisible ? "h-8 px-3 py-1" : "h-9 px-4 py-2";


        return `
        <div class="group bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-orange-100 hover:border-orange-300 overflow-hidden flex flex-col ${cardClasses}">
            <div class="${imageSectionClass} bg-gradient-to-br from-orange-100 to-red-100 relative overflow-hidden">
                ${community.image_url ? `
                    <img 
                        src="${community.image_url}" 
                        alt="${communityName}"
                        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                    />
                    <div style="display:none;">${imagePlaceholderSvg}</div>
                ` : imagePlaceholderSvg}
                <div class="absolute top-2 right-2">
                    <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border ${currentCostBadgeColor}">
                        ${currentCostDisplayText}
                    </span>
                </div>
            </div>
            <div class="${contentPaddingClass} flex flex-col flex-grow">
                <h3 class="${titleClass} font-semibold text-orange-700 group-hover:text-orange-600 transition-colors mb-3">
                    ${communityName}
                </h3>
                <div class="space-y-3 ${detailsMbClass} flex-grow">
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <div class="${sportIconOuter} bg-orange-500 rounded-full flex items-center justify-center">
                        <span class="${sportIconInner} text-white font-bold">S</span>
                        </div>
                        <span>${community.Sport || 'N/A'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${iconSizeClass} text-orange-500"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                        <span>${community.Location || 'N/A'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${iconSizeClass} text-orange-500"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        <span>${community['Student-based'] === 'Yes' ? 'Student-focused' : (community['Student-based'] === 'No' ? 'Open to all' : 'N/A')}</span>
                    </div>
                </div>
                <div class="flex gap-2 mt-auto">
                    ${community.website ? `
                        <a href="${community.website}" target="_blank" rel="noopener noreferrer" class="flex-1 inline-flex items-center justify-center rounded-lg text-sm font-medium bg-orange-500 hover:bg-orange-600 text-white ${actionButtonHeightClass} transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 mr-1"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" x2="21" y1="14" y2="3"></line></svg>
                            Website
                        </a>` : '<div class="flex-1"></div>'}
                    ${community.email ? `
                        <a href="mailto:${community.email}" class="flex-1 inline-flex items-center justify-center rounded-lg text-sm font-medium border border-orange-300 bg-white hover:bg-orange-50 text-orange-700 ${actionButtonHeightClass} transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 mr-1"><rect width="20" height="16" x="2" y="4" rx="2"></rect><path d="m22 7-10 5L2 7"></path></svg>
                            Contact
                        </a>` : '<div class="flex-1"></div>'}
                </div>
            </div>
        </div>
    `}).join('');
}

function showLoadingState() {
    document.getElementById('loadingState').classList.remove('hidden');
    document.getElementById('communitiesGrid').classList.add('hidden');
    document.getElementById('noResults').classList.add('hidden');
}

function hideLoadingState() {
    document.getElementById('loadingState').classList.add('hidden');
    // communitiesGrid and noResults visibility handled by renderCommunities
}

function showNoResults() {
    hideLoadingState(); // Ensure loading is hidden
    document.getElementById('noResults').classList.remove('hidden');
    document.getElementById('communitiesGrid').classList.add('hidden'); // Ensure grid is hidden
    document.getElementById('communitiesGrid').innerHTML = '';
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => { clearTimeout(timeout); func(...args); };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
