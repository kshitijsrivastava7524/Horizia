
// OpenWeatherMap API Constants
// const API_KEY = "a9e47096638b684adcbbf9078735d0c0"; // Using the key provided by the user
const API_BASE_URL = "https://api.openweathermap.org/data/2.5/";
const GEO_API_URL = "https://api.openweathermap.org/geo/1.0/direct";

// Helper function to convert UNIX timestamp to a formatted time string
const formatTime = (timestamp, timezoneOffset) => {
    if (!timestamp) return 'N/A';
    const date = new Date((timestamp + timezoneOffset) * 1000);
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
        timeZone: 'UTC' // Important: treat the timestamp as UTC and let the offset handle the actual time
    });
};

// Helper function to convert UNIX timestamp to a day name
const formatDay = (timestamp, timezoneOffset) => {
    if (!timestamp) return 'N/A';
    const date = new Date((timestamp + timezoneOffset) * 1000);
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        timeZone: 'UTC'
    });
};


// =======================================================
// CHART LOGIC
// =======================================================


document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('chartCanvas');
    const ctx = canvas.getContext('2d');

    // Data points adjusted to fit the 40-100 range
    const data = [
        { index: 1, value: 45 },
        { index: 2, value: 55 },
        { index: 3, value: 65 }, // Point at cyan threshold
        { index: 4, value: 80 }, // Point at red danger line
        { index: 5, value: 75 },
        { index: 6, value: 90 },
        { index: 7, value: 98 }
    ];

    // Define the fixed display range and threshold values
    const MIN_DISPLAY_VALUE = 40;
    const MAX_DISPLAY_VALUE = 100;
    const CYAN_THRESHOLD = 65;
    const RED_DANGER_LINE = 80;
    const PRIMARY_LINE_COLOR = '#00E676';
    const CYAN_THRESHOLD_COLOR = '#00FFFF';
    const DANGER_COLOR = '#EF4444';

    // Helper function to get the Y-coordinate on the canvas for a given value
    function getYCoordinate(value, chartHeight, padding) {
        const range = MAX_DISPLAY_VALUE - MIN_DISPLAY_VALUE;
        if (range === 0) return padding + chartHeight / 2; // Avoid division by zero

        // Scale value to chart height: (value - min) / range
        const normalizedValue = (value - MIN_DISPLAY_VALUE) / range;
        // Invert Y-axis (high values are low Y coordinates)
        return canvas.height - padding - (chartHeight * normalizedValue);
    }

    // Function to draw the entire chart
    function drawChart() {

        // Set canvas size based on parent container
        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;

        const padding = 20;
        const chartWidth = canvas.width - 2 * padding;
        const chartHeight = canvas.height - 2 * padding;

        // Clear the canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // --- 1. Draw Grid Lines ---
        ctx.strokeStyle = '#333333';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);

        // Horizontal grid lines (excluding thresholds)
        for (let i = 0; i < 5; i++) {
            // This uses the *visual* space, not value scaling, but we'll adapt.
            // We draw the standard grid lines evenly spaced for structure.
            const y = padding + chartHeight * (i / 4);
            if (i > 0 && i < 4) { // Draw middle lines
                ctx.beginPath();
                ctx.moveTo(padding, y);
                ctx.lineTo(canvas.width - padding, y);
                ctx.stroke();
            }
        }

        // Vertical grid lines (for points/index)
        ctx.setLineDash([2, 6]);
        for (let i = 1; i < data.length - 1; i++) {
            const x = padding + chartWidth * (i / (data.length - 1));
            ctx.beginPath();
            ctx.moveTo(x, padding);
            ctx.lineTo(x, canvas.height - padding * 2);
            ctx.stroke();
        }
        ctx.setLineDash([]); // Reset to solid line

        // --- 2. Draw Threshold Lines (Solid) ---

        // CYAN THRESHOLD (65)
        const yCyan = getYCoordinate(CYAN_THRESHOLD, chartHeight, padding);
        ctx.strokeStyle = PRIMARY_LINE_COLOR;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(padding, yCyan);
        ctx.lineTo(canvas.width - padding, yCyan);
        ctx.stroke();

        // RED DANGER LINE (80)
        const yRed = getYCoordinate(RED_DANGER_LINE, chartHeight, padding);
        ctx.strokeStyle = DANGER_COLOR;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(padding, yRed);
        ctx.lineTo(canvas.width - padding, yRed);
        ctx.stroke();

        // --- 3. Draw the Line Graph (Bezier for smooth curve) ---
        ctx.strokeStyle = PRIMARY_LINE_COLOR;
        ctx.lineWidth = 3;
        ctx.shadowColor = PRIMARY_LINE_COLOR;
        ctx.shadowBlur = 15;

        ctx.beginPath();

        // Move to the starting point
        const startX = padding;
        const startY = getYCoordinate(data[0].value, chartHeight, padding);
        ctx.moveTo(startX, startY);

        // Calculate points and draw curve segments
        let points = [];
        for (let i = 0; i < data.length; i++) {
            const x = padding + chartWidth * (i / (data.length - 1));
            const y = getYCoordinate(data[i].value, chartHeight, padding);
            points.push({ x, y, value: data[i].value });

            if (i < data.length - 1) {
                const p2 = data[i + 1];
                const x2 = padding + chartWidth * ((i + 1) / (data.length - 1));
                const y2 = getYCoordinate(p2.value, chartHeight, padding);

                // Control points for a smooth curve (Bezier curve approximation)
                const cpx = (x + x2) / 2;
                ctx.bezierCurveTo(cpx, y, cpx, y2, x2, y2);
            }
        }
        ctx.stroke();

        // --- 4. Draw Data Points and Highlight Threshold Crossings ---
        ctx.shadowBlur = 0;

        points.forEach(p => {
            let dotColor = 'white';
            let borderColor = PRIMARY_LINE_COLOR;
            let borderWidth = 3;

            // Highlight point at 65 (Cyan)
            if (p.value === CYAN_THRESHOLD) {
                dotColor = CYAN_THRESHOLD_COLOR;
                borderColor = 'white';
                borderWidth = 1.5;
            }
            // Highlight point at 80 (Red)
            else if (p.value === RED_DANGER_LINE) {
                dotColor = DANGER_COLOR;
                borderColor = 'white';
                borderWidth = 1.5;
            }

            // Draw fill (inner dot)
            ctx.fillStyle = dotColor;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
            ctx.fill();

            // Draw stroke (border)
            ctx.strokeStyle = borderColor;
            ctx.lineWidth = borderWidth;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
            ctx.stroke();
        });


        // --- 5. Draw X-axis Labels (Months) ---
        ctx.fillStyle = '#999999';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'center';
        const labelY = canvas.height - 5; // Position near the bottom edge

        const monthLabels = ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'];

        for (let i = 0; i < data.length; i++) {
            const x = padding + chartWidth * (i / (data.length - 1));
            const newLabel = monthLabels[i];
            ctx.fillText(newLabel, x, labelY);
        }

        // --- 6. Mark Threshold and Danger Labels
        ctx.fillStyle = '#FFFFFF';
        const threshold_label = 'threshold(65)';
        const danger_label = 'danger(80)';
        const x = padding + 50;
        ctx.fillText(threshold_label, x, getYCoordinate(65 + 1, chartHeight, padding));
        ctx.fillText(danger_label, x, getYCoordinate(80 + 1, chartHeight, padding));

    }

    // Draw initially and on resize
    drawChart();
    window.addEventListener('resize', drawChart);
});

// dark mode button event listener
document.addEventListener('DOMContentLoaded', () => {
  const themeBtn = document.getElementById('dark-mode-toggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      document.documentElement.classList.toggle('dark');
    });
  }
});


// =======================================================
// SEARCH BAR LOGIC
// =======================================================


// Wait for the DOM to be fully loaded before running the script
// Wait for the DOM to be fully loaded before running the script
document.addEventListener('DOMContentLoaded', () => {

    const API_KEY = "a9e47096638b684adcbbf9078735d0c0"; 

    // =======================================================
    // ELEMENT REFERENCES
    // =======================================================
    const searchContainer = document.getElementById('search-container');
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const loadingIndicator = document.getElementById('loading-indicator');

    // Weather Card Elements
    const tempValue = document.getElementById('temp-value');
    const tempMax = document.getElementById('temp-max');
    const tempMin = document.getElementById('temp-min');
    const currentCondition = document.getElementById('current-condition');
    const currentLocation = document.getElementById('current-location');
    const currentIcon = document.getElementById('current-icon');

    // Keep track of the search bar state
    let isExpanded = false;

    // =======================================================
    // WEATHER HELPER FUNCTIONS
    // =======================================================

    /**
     * Updates the weather card UI with new data
     * @param {object} data - The weather data from the API
     */
    function updateWeatherUI(data) {
        // Round temperatures to the nearest whole number
        tempValue.textContent = Math.round(data.main.temp);
        tempMax.textContent = Math.round(data.main.temp_max);
        tempMin.textContent = Math.round(data.main.temp_min);
        
        // Format location and condition
        currentLocation.textContent = `${data.name}, ${data.sys.country}`;
        currentCondition.textContent = capitalizeWords(data.weather[0].description);
        
        // Get and set the weather icon
        currentIcon.innerHTML = ''; // Clear out the old emoji or icon
        const iconImg = document.createElement('img');
        iconImg.src = `https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png`;
        iconImg.alt = data.weather[0].description;
        // Add classes for size - 8xl text is ~96px, so w-24 h-24 is a good fit.
        iconImg.className = "w-24 h-24"; 
        currentIcon.appendChild(iconImg);
    }

    /**
     * Converts a string to Title Case.
     * e.g., "scattered clouds" -> "Scattered Clouds"
     */
    function capitalizeWords(str) {
        return str.replace(/\b\w/g, char => char.toUpperCase());
    }


    // =======================================================
    // SEARCH BAR LOGIC
    // =======================================================

    // --- Tailwind classes for animation ---
    const expandClasses = [
        'w-64', 
        'pl-4', 
        'pr-12', 
        'placeholder-dark-text-main', 
        'dark:placeholder-dark-text-main'
    ];
    const collapseClasses = [
        'w-11', 
        'pl-0', 
        'pr-0', 
        'placeholder-transparent',
        'dark:placeholder-transparent'
    ];

    /**
     * Expands the search bar.
     */
    function expandSearch() {
        if (!isExpanded) {
            searchInput.classList.remove(...collapseClasses);
            searchInput.classList.add(...expandClasses);
            isExpanded = true;
        }
    }

    /**
     * Collapses the search bar, clears value, and removes focus.
     */
    function collapseSearch() {
        if (isExpanded) {
            searchInput.classList.remove(...expandClasses);
            searchInput.classList.add(...collapseClasses);
            searchInput.value = '';     // Clear the text
            searchInput.blur();     // Remove focus
            isExpanded = false;
        }
    }

    /**
     * Handles the search logic (API call).
     */
    async function handleSearch() {
        const query = searchInput.value;

        if (query.trim() === '') {
            console.log("Empty query, not searching.");
            return;
        }

        console.log(`Searching for: ${query}`);
        
        // Show the loading indicator
        loadingIndicator.classList.remove('hidden');

        try {
            // --- STEP 1: Geo-Coding (City Name -> Coordinates) ---
            const geoUrl = `https://api.openweathermap.org/geo/1.0/direct?q=${query}&limit=1&appid=${API_KEY}`;
            
            const geoResponse = await fetch(geoUrl);
            const geoData = await geoResponse.json();

            // Check if location was found
            if (!geoData || geoData.length === 0) {
                throw new Error(`Location not found for "${query}"`);
            }

            const { lat, lon } = geoData[0]; // Get lat/lon from geo data

            // --- STEP 2: Fetch Weather (Coordinates -> Weather) ---
            const weatherUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`;
            
            const weatherResponse = await fetch(weatherUrl);
            const weatherData = await weatherResponse.json();

            // Hide loading indicator
            loadingIndicator.classList.add('hidden');

            if (weatherData.cod === 200) { // Success
                console.log("API Success:", weatherData);
                
                // Update the UI
                updateWeatherUI(weatherData);

                // On success, collapse the search bar
                collapseSearch();
            } else {
                // Handle API errors (e.g., city not found)
                throw new Error(weatherData.message || "Weather data not found");
            }

        } catch (error) {
            // Hide loading indicator
            loadingIndicator.classList.add('hidden');

            // Handle all errors (Network, Geo, Weather)
            console.error("Search Error:", error.message);
            alert(`Error: ${error.message}. Please check the location name.`);
            
            // --- DO NOT COLLAPSE ---
            // Let the user see their typo and fix it.
        }
    }

    // =======================================================
    // EVENT LISTENERS (Unchanged from your code)
    // =======================================================

    // 1. Hovering over the whole container expands it
    searchContainer.addEventListener('mouseenter', expandSearch);

    // 2. Clicking into the input field expands it (locks it)
    searchInput.addEventListener('focus', expandSearch);

    // 3. When the mouse leaves, only collapse if NOT focused
    searchContainer.addEventListener('mouseleave', () => {
        if (document.activeElement !== searchInput) {
            collapseSearch();
        }
    });

    // 4. Clicking the search button
    searchButton.addEventListener('click', async (event) => { // <-- Add 'async'
        event.preventDefault(); 
        if (!isExpanded) {
            expandSearch();
            searchInput.focus(); 
        } else {
            await handleSearch(); // <-- Add 'await'
        }
    });

    // 5. Pressing "Enter" in the input field
    searchInput.addEventListener('keydown', async (event) => { // <-- Add 'async'
        if (event.key === 'Enter') {
            await handleSearch(); // <-- Add 'await'
        }
    });

    // 6. When the input loses focus (blur)
    searchInput.addEventListener('blur', (event) => {
        const newFocusTarget = event.relatedTarget;
        if (!searchContainer.contains(newFocusTarget)) {
            collapseSearch();
        }
    });
});