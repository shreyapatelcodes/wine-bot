// Category descriptions mapping
const categoryDescriptions = {
    'CRISP MINERALITY': 'crisp, mineral-driven white wines with high acidity and refreshing character',
    'NAPA CABS': 'bold Napa Valley Cabernet Sauvignon with rich tannins and dark fruit flavors',
    'NATURAL & FUNKY': 'natural, low-intervention wines with funky characteristics and unique terroir expression',
    'BORDEAUX BLENDS': 'structured Bordeaux-style red blends with elegance and aging potential'
};

// Loading messages
const loadingMessages = [
    "Curating your collection...",
    "Analyzing regional varietals...",
    "Matching flavor profiles...",
    "Verifying availability..."
];

let messageIndex = 0;
let loadingInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
    initializeCategoryChips();
});

// Form initialization
function initializeForm() {
    const form = document.getElementById('wineForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

// Category chips initialization
function initializeCategoryChips() {
    const chips = document.querySelectorAll('.category-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const category = chip.dataset.category;
            const description = categoryDescriptions[category];
            if (description) {
                document.getElementById('wineDescription').value = description;
            }
        });
    });
}

// Form submission handler
async function handleFormSubmit(event) {
    event.preventDefault();

    // Hide any existing error messages
    hideError();

    // Collect form data
    const description = document.getElementById('wineDescription').value.trim();
    const minPrice = parseFloat(document.getElementById('minPrice').value) || 10;
    const maxPrice = parseFloat(document.getElementById('maxPrice').value) || 100;

    // Validate input
    if (!description) {
        showError('Please describe your wine preferences');
        return;
    }

    if (minPrice >= maxPrice) {
        showError('Max budget must be greater than min budget');
        return;
    }

    if (minPrice < 5 || maxPrice > 500) {
        showError('Please enter a budget between $5 and $500');
        return;
    }

    // Prepare request data
    const preferences = {
        description: description,
        budget_min: minPrice,
        budget_max: maxPrice,
        food_pairing: null,
        wine_type_pref: null
    };

    // Show loading overlay
    showLoadingOverlay();

    try {
        // Make API request
        const response = await fetch('/api/recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(preferences)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to get recommendations');
        }

        if (!data.recommendations || data.recommendations.length === 0) {
            hideLoadingOverlay();
            showError(data.message || 'No wines found matching your criteria. Try adjusting your budget or preferences.');
            return;
        }

        // Store recommendations in sessionStorage
        sessionStorage.setItem('recommendations', JSON.stringify(data));

        // Navigate to results page
        window.location.href = '/results.html';

    } catch (error) {
        hideLoadingOverlay();
        showError(error.message || 'An error occurred while getting recommendations. Please try again.');
        console.error('Error:', error);
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.querySelector('p').textContent = message;
        errorDiv.classList.remove('hidden');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            hideError();
        }, 5000);
    }
}

// Hide error message
function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.classList.add('hidden');
    }
}

// Show loading overlay
function showLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');

        // Reset message index
        messageIndex = 0;

        // Cycle through loading messages
        loadingInterval = setInterval(() => {
            messageIndex = (messageIndex + 1) % loadingMessages.length;
            const messageEl = document.getElementById('loadingMessage');
            if (messageEl) {
                messageEl.textContent = loadingMessages[messageIndex];
            }
        }, 800);
    }
}

// Hide loading overlay
function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');

        // Clear interval
        if (loadingInterval) {
            clearInterval(loadingInterval);
            loadingInterval = null;
        }

        // Reset message index
        messageIndex = 0;
    }
}

// Render recommendations (used in results.html)
function renderRecommendations(recommendations) {
    const container = document.getElementById('recommendations');
    if (!container) return;

    container.innerHTML = '';

    recommendations.forEach((rec, index) => {
        const wine = rec.wine;

        // Build characteristics tags
        const charTags = wine.characteristics.slice(0, 3).map(char =>
            `<span class="char-tag inline-block px-4 py-2 rounded-full text-xs bg-primary/5 border border-primary/10 mr-2 mb-2">${char}</span>`
        ).join('');

        // Build wine card HTML
        const wineCard = `
            <div class="wine-card bg-white/60 backdrop-blur-sm border border-primary/10 rounded-lg p-8 md:p-12 shadow-xl hover:shadow-2xl transition-shadow">
                <div class="text-[10px] uppercase tracking-widest opacity-30 mb-2 font-mono">0${index + 1}</div>

                <h2 class="font-display text-4xl md:text-5xl text-primary mb-2">${wine.name}</h2>

                <p class="font-sans italic text-lg opacity-70 mb-1">${wine.varietal}</p>
                <p class="font-sans italic text-lg opacity-70 mb-6">${wine.region}, ${wine.country}</p>

                <p class="font-mono text-3xl font-bold mb-8">$${wine.price_usd.toFixed(2)}</p>

                <div class="bg-primary/5 border-l-4 border-primary p-6 rounded mb-8">
                    <div class="text-[10px] uppercase tracking-widest opacity-50 mb-3 font-bold">Why We Chose This</div>
                    <p class="font-sans italic text-lg leading-relaxed">"${rec.explanation}"</p>
                </div>

                <div class="grid grid-cols-2 gap-6 mb-8">
                    <div>
                        <span class="text-[10px] uppercase tracking-widest opacity-50 font-bold">Varietal</span>
                        <p class="font-mono text-sm mt-1">${wine.varietal}</p>
                    </div>
                    <div>
                        <span class="text-[10px] uppercase tracking-widest opacity-50 font-bold">Region</span>
                        <p class="font-mono text-sm mt-1">${wine.region}</p>
                    </div>
                </div>

                <div class="mb-8">
                    <div class="text-[10px] uppercase tracking-widest opacity-50 mb-3 font-bold">Characteristics</div>
                    <div class="flex flex-wrap">
                        ${charTags}
                    </div>
                </div>

                <div class="mb-8">
                    <div class="text-[10px] uppercase tracking-widest opacity-50 mb-3 font-bold">Flavor Notes</div>
                    <p class="font-sans italic text-base leading-relaxed">${wine.flavor_notes.join(', ')}</p>
                </div>

                <div class="flex justify-center mt-8">
                    <a href="${wine.vivino_url}" target="_blank" class="inline-flex items-center space-x-2 bg-primary text-white px-6 py-3 rounded-full font-bold uppercase tracking-[0.15em] text-xs hover:scale-105 transition-transform shadow-lg">
                        <span>Buy Now</span>
                        <span class="material-icons text-sm">shopping_cart</span>
                    </a>
                </div>
            </div>
        `;

        container.innerHTML += wineCard;
    });
}
