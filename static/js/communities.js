//Global variables

let currentPage = 1;
const communitiesPerPage = 9;
let totalPages = 1;

// Handle map open/close state
document.addEventListener('DOMContentLoaded', function() {
    // This DOMContentLoaded listener seems to be duplicated.
    // The one further down that calls loadCommunities() is likely the main one.
    // I'll leave this one for now, but you might want to consolidate.
    const mapContainer = document.getElementById('mapContainer');
    const mapToggle = document.getElementById('mapToggle');
    const communitiesContainer = document.getElementById('communitiesContainer');
    const communitiesGrid = document.getElementById('communitiesGrid');

    // Function to toggle map visibility (initial simple version)
    function toggleMapSimple() { // Renamed to avoid conflict with more complex toggleMap below
        const isMapOpen = mapContainer.classList.contains('hidden');
        mapContainer.classList.toggle('hidden');
        mapContainer.classList.toggle('map-open', !isMapOpen);

        // Update communities container height and scrolling
        if (!isMapOpen) { // Map was shown, now hidden
            communitiesContainer.style.height = '600px';
            communitiesContainer.style.overflowY = 'auto';
        } else { // Map was hidden, now shown
            communitiesContainer.style.height = 'auto';
            communitiesContainer.style.overflowY = 'visible';
        }

        // Update grid spacing - This logic seems to be specific to an attribute
        // Make sure 'data-map-open-class' is set if you use this.
        const gapValue = communitiesGrid.getAttribute('data-map-open-gap'); // Changed attribute name for clarity
        if (gapValue) {
            communitiesGrid.style.gap = isMapOpen ? communitiesGrid.dataset.originalGap || '1rem' : gapValue;
        }
    }

    // Initialize map toggle button text (for the simple toggle)
    if (mapToggle && mapContainer) { // Check if elements exist
        mapToggle.textContent = mapContainer.classList.contains('hidden')
            ? 'Show Map'
            : 'Hide Map';
        // Add click event listener to map toggle button - This will be overridden by the setupEventListeners() call later.
        // mapToggle.addEventListener('click', toggleMapSimple);
    }
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
    document.getElementById('mapToggle').addEventListener('click', toggleMap); // Uses the complex toggleMap
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
        communitiesWrapper.classList.remove('lg:w-full');
        communitiesWrapper.classList.add('lg:w-1/2');

        communitiesContainer.style.height = '600px'; // Or use mapContainer.clientHeight if dynamically set
        communitiesContainer.style.overflowY = 'auto';
        communitiesContainer.classList.add('custom-scrollbar');

        communitiesGrid.classList.remove('md:grid-cols-2', 'xl:grid-cols-3');
        communitiesGrid.classList.add('grid-cols-1', 'md:grid-cols-1', 'xl:grid-cols-1');


        mapToggle.innerHTML = svgHideMap;

        if (!map) {
            initializeMap(); // This calls updateMapMarkers internally on success
        } else {
            map.invalidateSize();
            updateMapMarkers();
        }
    } else {
        mapContainer.classList.add('hidden');
        mapContainer.classList.remove('lg:w-1/2');
        communitiesWrapper.classList.remove('lg:w-1/2');
        communitiesWrapper.classList.add('lg:w-full');

        communitiesContainer.style.height = 'auto';
        communitiesContainer.style.overflowY = 'visible';
        communitiesContainer.classList.remove('custom-scrollbar');

        communitiesGrid.classList.remove('grid-cols-1', 'md:grid-cols-1', 'xl:grid-cols-1');
        communitiesGrid.classList.add('md:grid-cols-2', 'xl:grid-cols-3');

        mapToggle.innerHTML = svgShowMap;
    }
    renderCommunities(); // Re-render to apply size-dependent classes in cards
}

function toggleMap() {
    isMapVisible = !isMapVisible;
    adjustLayoutForMap();
}

function initializeMap() {
    const mapElement = document.getElementById('map');
    const mapToggle = document.getElementById('mapToggle');
    try {
        map = L.map(mapElement).setView([52.3676, 4.9041], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
        }).addTo(map);
        markerClusterGroup = L.markerClusterGroup();
        map.addLayer(markerClusterGroup);
        updateMapMarkers();
        map.invalidateSize(); // Ensure map size is correct after initialization
        mapToggle.disabled = false; // Ensure toggle is enabled
    } catch (error) {
        console.error('Error initializing map:', error);
        if (mapToggle) {
            mapToggle.disabled = true;
            mapToggle.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-red-500">
                <path d="m21.73 18.73-5-5L8 18l-6-6 6-6 1.27 1.27"></path>
                <path d="M12 18"></path>
            </svg>
            <span>Map Error</span>`;
        }
        if (mapElement) {
            mapElement.innerHTML = `
            <div class="w-full h-full bg-gradient-to-br from-orange-100 to-red-100 flex items-center justify-center">
                <div class="text-center text-orange-700">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-16 w-16 mx-auto mb-4">
                        <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon>
                        <line x1="9" x2="9" y1="3" y2="18"></line>
                        <line x1="15" x2="15" y1="6" y2="21"></line>
                    </svg>
                    <p class="text-lg font-semibold">Map Currently Unavailable</p>
                    <p class="text-sm text-red-600">There was an issue loading the map. Please refresh the page.</p>
                </div>
            </div>`;
        }
    }
}


function updateMapMarkers() {
    if (!map || !markerClusterGroup) {
        // console.warn("Map or marker cluster group not initialized. Skipping marker update.");
        return;
    }
    try {
        markerClusterGroup.clearLayers();
        filteredCommunities.forEach(community => {
            // Ensure Location and Name are present before attempting to geocode
            if (community.Location && community.Location.trim() !== "" && community.Name) {
                geocodeAddress(community.Location, community);
            } else {
                // console.warn(`Skipping geocoding for community '${community.Name || 'Unnamed'}' due to missing or empty location.`);
            }
        });
    } catch (error) {
        console.error('Error updating map markers:', error);
    }
}

// --- START OF MODIFIED GEOCODING FUNCTIONS ---

/**
 * Creates the HTML content for a marker's popup.
 * Assumes it's only called for successfully geocoded locations.
 */
function createPopupContentForMarker(community, displayAddress) { // Renamed to avoid conflict if you have other createPopupContent
    return `
        <div class="p-2 max-w-xs">
            <h3 class="font-bold text-sm mb-1">${community.Name || 'N/A'}</h3>
            <p class="text-xs mb-0.5">Location: ${displayAddress || 'N/A'}</p>
            <p class="text-xs mb-0.5">Sport: ${community.Sport || 'N/A'}</p>
            <p class="text-xs mb-0.5">Cost: ${getCostDisplayText(community.Cost)}</p>
            <p class="text-xs mb-0.5">Student: ${community['Student-based'] === 'Yes' ? 'Yes' : (community['Student-based'] === 'No' ? 'No' : 'N/A')}</p>
            ${community.website ? `<p class="text-xs"><a href="${community.website}" target="_blank" class="text-orange-600 hover:text-orange-700 font-semibold">Visit Website</a></p>` : ''}
        </div>
    `;
}

/**
 * Adds a marker to the map for a successfully geocoded community.
 */
function addSuccessfullyGeocodedMarker(community, coordinates, displayAddress) {
    if (!map || !markerClusterGroup) return; // Should not happen if called correctly, but good guard

    const marker = L.marker([coordinates.lat, coordinates.lng], {
        title: community.Name,
        icon: L.icon({
            iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34]
        })
    });
    marker.bindPopup(createPopupContentForMarker(community, displayAddress));
    markerClusterGroup.addLayer(marker);
}

/**
 * Geocodes an address and adds a marker to the map if successful.
 * If geocoding fails or address is invalid, no marker is added.
 */
async function geocodeAddress(address, community) {
    const apiKey = config.OPENCAGE_API_KEY;
    const communityNameForLog = community.Name || 'Unnamed Community';

    if (!apiKey || apiKey === 'YOUR_OPENCAGE_API_KEY') {
        console.error(`(${communityNameForLog}) No valid OpenCage API key configured. Skipping marker.`);
        return;
    }

    const originalAddress = address;
    let cleanedAddress = address ? String(address) : "";

    if (cleanedAddress) {
        cleanedAddress = cleanedAddress
            .replace(/\d{4}\s[A-Z]{2}\s*/g, '')
            .replace(/, /g, ',')
            // Optional: Further clean common city/country names if they might interfere
            // .replace(/,\s*Amsterdam/gi, '')
            // .replace(/,\s*Netherlands/gi, '')
            .trim();
    }

    if (!cleanedAddress) {
        console.warn(`(${communityNameForLog}) Address ('${originalAddress}') is empty or became unusable after cleaning. Skipping marker.`);
        return;
    }

    const query = `${encodeURIComponent(cleanedAddress)}, Amsterdam, Netherlands`;
    const apiUrl = `https://api.opencagedata.com/geocode/v1/json?q=${query}&key=${apiKey}&limit=1&countrycode=NL&bounds=4.7271_52.2780_5.0791_52.4311&no_annotations=1`;

    try {
        const response = await fetch(apiUrl);
        let responseDataForLog = {}; // For logging in case of errors

        if (!response.ok) {
            let errorDetails = `Status: ${response.status} ${response.statusText}`;
            try {
                responseDataForLog = await response.json(); // Attempt to get JSON error body
                errorDetails += `, Body: ${JSON.stringify(responseDataForLog)}`;
            } catch (e) {
                try {
                    const textError = await response.text(); // Fallback to text if not JSON
                    errorDetails += `, Body: ${textError}`;
                } catch (textE) {/* ignore */}
            }
            console.error(`(${communityNameForLog}) Geocoding HTTP error for address '${originalAddress}' (cleaned: '${cleanedAddress}'). ${errorDetails}. Skipping marker.`);
            return;
        }

        const data = await response.json();
        responseDataForLog = data; // For logging successful but no-result cases

        if (data.results && data.results.length > 0) {
            const result = data.results[0];
            const { lat, lng } = result.geometry;
            const confidence = result.confidence || 0;

            // Set your desired confidence threshold (e.g., 7 out of 10)
            // Lower values are less reliable.
            if (confidence < 7) {
                 console.warn(`(${communityNameForLog}) Geocoding for '${originalAddress}' (cleaned: '${cleanedAddress}') has low confidence: ${confidence}. Result: ${result.formatted}. Components: ${JSON.stringify(result.components)}. Skipping marker.`);
                 return;
            }

            const displayAddressForPopup = result.formatted || cleanedAddress;
            addSuccessfullyGeocodedMarker(community, { lat, lng }, displayAddressForPopup);
        } else {
            const statusInfo = data.status ? `(API Status: ${data.status.code} - ${data.status.message})` : '';
            console.warn(`(${communityNameForLog}) Geocoding failed for address: '${originalAddress}' (cleaned: '${cleanedAddress}'). No results found ${statusInfo}. Response: ${JSON.stringify(responseDataForLog)}. Skipping marker.`);
            return;
        }
    } catch (error) {
        console.error(`(${communityNameForLog}) Error during geocoding process for address '${originalAddress}' (cleaned: '${cleanedAddress}'): ${error.message}. Skipping marker.`);
        return;
    }
}
// --- END OF MODIFIED GEOCODING FUNCTIONS ---

// The addDefaultMarker function is no longer called by geocodeAddress,
// so it can be removed if not used elsewhere. I'll comment it out.
/*
function addDefaultMarker(community, originalAddress, message) {
    // Default Amsterdam location
    const defaultCoords = { lat: 52.3676, lng: 4.9041 };
    // addMarkerToMap(community, defaultCoords, originalAddress, true, message); // This would need addMarkerToMap to be reinstated or changed
    console.warn(`Default marker was requested for ${community.Name} but is now disabled for geocoding failures.`);
}
*/

// The old addMarkerToMap and createPopupContent that handled errors are no longer needed
// as we separated them. I've renamed the new ones to createPopupContentForMarker and addSuccessfullyGeocodedMarker.
// If you had an 'addMarkerToMap' that the commented out 'addDefaultMarker' was using, it would need to be reinstated
// or its logic combined if you still need default markers for *other* reasons.


function handleSearch() { applyFilters(); }
function handleFilter() { applyFilters(); }

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const costFilterValue = document.getElementById('costFilter').value;
    const studentFilterValue = document.getElementById('studentFilter').value;
    const sportFilterValue = document.getElementById('sportFilter').value;

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
        else if (communityCostNormalized === "null" || communityCostNormalized === "undefined") communityCostNormalized = "na";


        const matchesCost = costFilterValue === "all" ||
            (costFilterValue === "Free" && communityCostNormalized === "free") ||
            (costFilterValue === "Paid" && communityCostNormalized !== "free" && communityCostNormalized !== "na") ||
            (costFilterValue === "NA" && communityCostNormalized === "na");

        const communityStudentBased = community['Student-based'] || '';
        const matchesStudent = studentFilterValue === "all" || communityStudentBased === studentFilterValue;

        const communitySport = community.Sport || '';
        const matchesSport = sportFilterValue === "all" || communitySport.toLowerCase().split(',').map(s=>s.trim()).includes(sportFilterValue.toLowerCase());


        return matchesSearch && matchesCost && matchesStudent && matchesSport;
    });

    renderCommunities();
    if (isMapVisible && map) {
        updateMapMarkers();
    }
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('costFilter').value = 'all';
    document.getElementById('studentFilter').value = 'all';
    document.getElementById('sportFilter').value = 'all';

    filteredCommunities = [...communities];
    currentPage = 1; // Reset to page 1
    renderCommunities();
    if (isMapVisible && map) {
        updateMapMarkers();
    }
}

function renderCommunities() {
    const grid = document.getElementById('communitiesGrid');
    const noResultsEl = document.getElementById('noResults');
    const communitiesCountEl = document.getElementById('communitiesCount');
    const paginationEl = document.getElementById('pagination');

    // Calculate pagination
    totalPages = Math.ceil(filteredCommunities.length / communitiesPerPage);
    const startIndex = (currentPage - 1) * communitiesPerPage;
    const endIndex = startIndex + communitiesPerPage;
    const paginatedCommunities = filteredCommunities.slice(startIndex, endIndex);

    communitiesCountEl.textContent = `Communities (${filteredCommunities.length})`;

    if (filteredCommunities.length === 0) {
        grid.innerHTML = '';
        grid.classList.add('hidden');
        noResultsEl.classList.remove('hidden');
        paginationEl.classList.add('hidden');
        return;
    }

    noResultsEl.classList.add('hidden');
    grid.classList.remove('hidden');
    
    // Show pagination if more than one page
    if (totalPages > 1) {
        paginationEl.classList.remove('hidden');
        updatePaginationControls();
    } else {
        paginationEl.classList.add('hidden');
    }

    // Rest of your existing card rendering code, but use paginatedCommunities instead of filteredCommunities
    grid.innerHTML = paginatedCommunities.map(community => {
        const communityName = community.Name || 'Unnamed Community';
        const currentCostBadgeColor = getCostBadgeColor(community.Cost);
        const currentCostDisplayText = getCostDisplayText(community.Cost);

        const imagePlaceholderSvg = `
        <div class="absolute inset-0 flex w-full h-full items-center justify-center bg-gradient-to-br from-orange-100 to-red-100">
            <div class="text-center text-orange-700 p-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-12 w-12 mx-auto mb-2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                <p class="text-sm font-medium">${communityName}</p>
            </div>
        </div>`;

        const imageSectionClass = isMapVisible ? "aspect-[4/3] sm:aspect-[3/4] h-32 sm:h-40" : "aspect-video";
        const contentPaddingClass = isMapVisible ? "p-2 sm:p-3" : "p-4 sm:p-6";
        const titleClass = isMapVisible ? "text-base sm:text-sm" : "text-lg";
        const detailsMbClass = isMapVisible ? "mb-1 sm:mb-2" : "mb-3 sm:mb-4";
        const iconSizeClass = isMapVisible ? "h-3.5 w-3.5 sm:h-3 w-3" : "h-4 w-4";
        const sportIconOuter = isMapVisible ? "w-3.5 h-3.5 sm:w-3 h-3" : "w-4 h-4";
        const actionButtonHeightClass = isMapVisible ? "h-7 sm:h-8 px-2 py-1 text-xs sm:text-sm" : "h-9 px-4 py-2 text-sm";

        return `
        <div class="group bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-orange-100 hover:border-orange-300 overflow-hidden flex flex-col">
            <div class="${imageSectionClass} bg-gradient-to-br from-orange-100 to-red-100 relative overflow-hidden">
                ${community.image_url ? `
                    <img
                        src="${community.image_url}"
                        alt="${communityName}"
                        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onerror="this.onerror=null; this.style.display='none'; this.nextElementSibling.style.display='flex';"
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
                <h3 class="${titleClass} font-semibold text-orange-700 group-hover:text-orange-600 transition-colors mb-2 sm:mb-3">
                    ${communityName}
                </h3>
                <div class="space-y-2 sm:space-y-3 ${detailsMbClass} flex-grow">
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <div class="${sportIconOuter} bg-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-volleyball-icon lucide-volleyball text-white ${isMapVisible ? 'w-2 h-2' : 'w-2.5 h-2.5'}"><path d="M11.1 7.1a16.55 16.55 0 0 1 10.9 4"/><path d="M12 12a12.6 12.6 0 0 1-8.7 5"/><path d="M16.8 13.6a16.55 16.55 0 0 1-9 7.5"/><path d="M20.7 17a12.8 12.8 0 0 0-8.7-5 13.3 13.3 0 0 1 0-10"/><path d="M6.3 3.8a16.55 16.55 0 0 0 1.9 11.5"/><circle cx="12" cy="12" r="10"/></svg></div>
                        <span class="truncate" title="${community.Sport || 'N/A'}">${community.Sport || 'N/A'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${iconSizeClass} text-orange-500 flex-shrink-0"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                        <span class="truncate" title="${community.Location || 'N/A'}">${community.Location || 'N/A'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${iconSizeClass} text-orange-500 flex-shrink-0"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        <span class="truncate" title="${community['Student-based'] === 'Yes' ? 'Student-focused' : (community['Student-based'] === 'No' ? 'Open to all' : 'N/A')}">${community['Student-based'] === 'Yes' ? 'Student-focused' : (community['Student-based'] === 'No' ? 'Open to all' : 'N/A')}</span>
                    </div>
                </div>
                <div class="flex gap-2 mt-auto pt-2 sm:pt-3">
                    ${community.website ? `
                        <a href="${community.website}" target="_blank" rel="noopener noreferrer" class="flex-1 inline-flex items-center justify-center rounded-lg font-medium bg-orange-500 hover:bg-orange-600 text-white ${actionButtonHeightClass} transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 mr-1 sm:mr-1.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" x2="21" y1="14" y2="3"></line></svg>
                            Website
                        </a>` : '<div class="flex-1"></div>'}
                    ${community.email ? `
                        <a href="mailto:${community.email}" class="flex-1 inline-flex items-center justify-center rounded-lg font-medium border border-orange-300 bg-white hover:bg-orange-50 text-orange-700 ${actionButtonHeightClass} transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 mr-1 sm:mr-1.5"><rect width="20" height="16" x="2" y="4" rx="2"></rect><path d="m22 7-10 5L2 7"></path></svg>
                            Contact
                        </a>` : '<div class="flex-1"></div>'}
                </div>
            </div>
        </div>
    `}).join('');
}

function updatePaginationControls() {
    const paginationEl = document.getElementById('pagination');
    
    let paginationHTML = `
        <div class="flex items-center justify-center space-x-2">
            <button 
                id="prevPage" 
                ${currentPage === 1 ? 'disabled' : ''} 
                class="px-3 py-2 text-sm font-medium text-orange-600 bg-white border border-orange-300 rounded-lg hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-colors"
            >
                Previous
            </button>
            <div class="flex space-x-1">
    `;
    
    // Show page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
            paginationHTML += `
                <button class="px-3 py-2 text-sm font-medium text-white bg-orange-500 border border-orange-500 rounded-lg">
                    ${i}
                </button>
            `;
        } else {
            paginationHTML += `
                <button 
                    class="px-3 py-2 text-sm font-medium text-orange-600 bg-white border border-orange-300 rounded-lg hover:bg-orange-50 transition-colors"
                    onclick="goToPage(${i})"
                >
                    ${i}
                </button>
            `;
        }
    }
    
    paginationHTML += `
            </div>
            <button 
                id="nextPage" 
                ${currentPage === totalPages ? 'disabled' : ''} 
                class="px-3 py-2 text-sm font-medium text-orange-600 bg-white border border-orange-300 rounded-lg hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white transition-colors"
            >
                Next
            </button>
        </div>
    `;
    
    paginationEl.innerHTML = paginationHTML;
    
    // Add event listeners for prev/next buttons
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderCommunities();
        }
    });
    
    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderCommunities();
        }
    });
}

function goToPage(page) {
    currentPage = page;
    renderCommunities();
}


function showLoadingState() {
    document.getElementById('loadingState').classList.remove('hidden');
    document.getElementById('communitiesGrid').classList.add('hidden');
    document.getElementById('noResults').classList.add('hidden');
}

function hideLoadingState() {
    document.getElementById('loadingState').classList.add('hidden');
}

function showNoResults() {
    hideLoadingState();
    document.getElementById('noResults').classList.remove('hidden');
    document.getElementById('communitiesGrid').classList.add('hidden');
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