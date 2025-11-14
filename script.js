// !!! IMPORTANT !!! The API Key you provided is kept here.
const API_KEY = "a9e47096638b684adcbbf9078735d0c0";

// FIX: Corrected Base URL for standard OpenWeatherMap API endpoints
const API_BASE_URL = "https://api.openweathermap.org/data/2.5/";

const messageArea = document.getElementById("message-area");
const rootElement = document.documentElement; // For dynamic background change

// Modal elements
const locationModal = document.getElementById("location-modal");
const openMapModalButton = document.getElementById("open-map-modal");
const closeModalButton = document.getElementById("close-modal");
const modalCityInput = document.getElementById("modal-city-input");
const modalFetchButton = document.getElementById("modal-fetch-button");
const mainSearchButton = document.getElementById("main-search-button");

// NEW ELEMENT: Current Location Button
const currentLocationButton = document.getElementById(
  "current-location-button"
);

let activeTab = "current";

// Storage for fetched data
let weatherData = {
  current: null,
  forecast: null,
  name: "N/A",
  country: "N/A",
};

// --- Utility Functions ---

function showMessage(message, isError = false) {
  // Note: messageArea element is not defined in the HTML body, so we use console.log as fallback
  const msgBox = document.createElement("div");
  msgBox.className = `fixed top-4 right-4 p-3 text-sm rounded-lg ${
    isError ? "bg-red-700" : "bg-green-700"
  } text-white z-[60]`;
  msgBox.textContent = message;
  document.body.appendChild(msgBox);
  setTimeout(() => msgBox.remove(), 5000);
  console.log(isError ? "ERROR:" : "INFO:", message);
}

function clearMessage() {
  // No longer needed as messages auto-remove
}

function toCelsius(kelvin) {
  // OpenWeatherMap returns temperature in Kelvin by default
  return (kelvin - 273.15).toFixed(0); // Round to whole number for cleaner UI
}

function getDayName(timestamp) {
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString("en-US", { weekday: "short" });
}

// Dynamic Background Swapping and ACCENT COLOR UPDATER
function updateBackground(conditionId) {
  let bgUrl = "";
  let accentColor = "#f97316"; // Default: Orange (for Clear Sky)

  // Weather condition ID ranges (OpenWeatherMap)
  if (conditionId >= 200 && conditionId < 300) {
    // Thunderstorm
    bgUrl = "images/storm.jpeg";
    accentColor = "#4a2c00"; // Dark Brown
  } else if (conditionId >= 300 && conditionId < 600) {
    // Drizzle/Rain
    bgUrl = "images/rain.jpeg";
    accentColor = "#3b82f6"; // Deep Blue
  } else if (conditionId >= 600 && conditionId < 700) {
    // Snow
    bgUrl = "images/snow.jpeg";
    accentColor = "#bfdbfe"; // Icy Light Blue
  } else if (conditionId === 800) {
    // Clear
    bgUrl = "images/clear.jpeg";
    accentColor = "#f97316"; // Orange
  } else if (conditionId > 800) {
    // Clouds (any ID above 800 but not 800 itself)
    bgUrl = "images/cloudy.jpeg";
    accentColor = "#d1d5db"; // Light Gray
  } else {
    // Atmosphere (700-799: Mist, Smoke, Haze, Fog, Sand, Dust, Ash, Squall, Tornado)
    bgUrl = "images/misty.jpeg";
    accentColor = "#84a98c"; // Muted Sea Green / Sage
  }

  document.body.style.backgroundImage = `url('${bgUrl}')`;
  // FIX: Set the dynamic accent color CSS variable
  document.documentElement.style.setProperty(
    "--dynamic-accent-color",
    accentColor
  );
}

// Helper for API calls with exponential backoff for robustness
async function fetchWithBackoff(url, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        const errorBody = await response.text();
        // Append error body to the message if available
        let message = "Unknown error.";
        try {
          const jsonError = JSON.parse(errorBody);
          message = jsonError.message || message;
        } catch (e) {
          message = errorBody || message;
        }
        const errorMessage = `HTTP error! Status: ${response.status}. ${message}`;
        throw new Error(errorMessage);
      }
      return response.json();
    } catch (error) {
      if (i === retries - 1) {
        throw error;
      }
      const delay = Math.pow(2, i) * 1000;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
}

// --- Rendering Functions ---

function renderUI() {
  const data = weatherData.current;
  const forecast = weatherData.forecast;

  if (!data || !forecast) return;

  // 1. Update Current Weather Details
  const tempC = toCelsius(data.main.temp);
  const tempMaxC = toCelsius(data.main.temp_max);
  const tempMinC = toCelsius(data.main.temp_min);
  const description = data.weather[0].description.replace(/\b\w/g, (l) =>
    l.toUpperCase()
  );
  const conditionId = data.weather[0].id;
  const dateOptions = { weekday: "long", month: "long", day: "numeric" };

  // Handle location display: use stored name/country, or try to reverse geocode if only coordinates were provided
  let locationName = weatherData.name;
  if (locationName === "N/A" && data.coord) {
    // If we have coordinates but no name (from direct lat/lon search), use the reverse geocoding to display the location
    locationName = `[${data.coord.lat.toFixed(
      2
    )}, ${data.coord.lon.toFixed(2)}]`;
  }

  const locationString = `${locationName}, ${
    weatherData.country
  } (${new Date().toLocaleDateString("en-US", dateOptions)})`;

  // Main Content updates
  document.getElementById("current-location-text").textContent =
    locationString;
  document.getElementById(
    "map-location-display"
  ).textContent = `${locationName}, ${weatherData.country}`;
  document.getElementById("main-temp").textContent = `${tempC}°`;
  document.getElementById("temp-max").textContent = toCelsius(
    data.main.temp_max
  );
  document.getElementById("temp-min").textContent = toCelsius(
    data.main.temp_min
  );
  document.getElementById("weather-description").textContent =
    description;
  document.getElementById(
    "weather-icon"
  ).src = `https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png`;

  // Update Background and Dynamic Accent Color based on weather ID
  updateBackground(conditionId);

  // 2. Update Forecast (Bottom)
  const forecastContainer = document.getElementById("forecast-days");
  forecastContainer.innerHTML = "";

  // Filter the forecast list to get one entry per day for the next 6 days
  const dailyForecasts = {};
  // The API provides data every 3 hours (8 entries per day). We filter for one entry per day.
  for (let i = 0; i < forecast.list.length; i++) {
    const day = new Date(forecast.list[i].dt * 1000).toLocaleDateString();
    if (!dailyForecasts[day]) {
      // Only store the first entry for each new day
      dailyForecasts[day] = forecast.list[i];
    }
  }

  // Convert object to array and skip the current day (first key)
  const forecastItems = Object.values(dailyForecasts).slice(1, 7);

  if (forecastItems.length === 0) {
    showMessage("Could not generate 6-day forecast from API data.", true);
  }

  forecastItems.forEach((dayData) => {
    const dayName = getDayName(dayData.dt);
    // Use the main day temperature from the forecast entry
    const tempDayC = toCelsius(dayData.main.temp);

    const itemHtml = `
                  <div class="text-center w-1/6 min-w-[100px] flex-shrink-0 opacity-90 transition hover:opacity-100 transform hover:scale-105">
                      <p class="text-sm font-medium">${dayName}</p>
                      <img src="https://openweathermap.org/img/wn/${dayData.weather[0].icon}@2x.png" alt="${dayData.weather[0].description}" class="w-12 h-12 mx-auto mt-2"/>
                      <p class="text-3xl font-light mt-1">${tempDayC}°</p>
                  </div>
              `;
    forecastContainer.insertAdjacentHTML("beforeend", itemHtml);
  });

  // 3. Update Recent Searches (Mocked for design purposes)
  const recentCards = document.getElementById("recent-cards-container");
  recentCards.innerHTML = `
              <div class="glass-card p-3 rounded-xl w-32 flex flex-col items-center text-xs">
                  <span class="font-medium dynamic-accent-text text-sm">Liverpool, UK</span>
                  <span class="text-3xl font-light">16°</span>
                  <span class="opacity-70 text-sm">Partly Cloudy</span>
              </div>
              <div class="glass-card p-3 rounded-xl w-32 flex flex-col items-center text-xs">
                  <span class="font-medium dynamic-accent-text text-sm">Palermo, Italy</span>
                  <span class="text-3xl font-light">-2°</span>
                  <span class="opacity-70 text-sm">Rain/Thunder</span>
              </div>
          `;
}

// --- API & Core Logic ---

async function fetchWeatherData(query, isCoord = false) {
  clearMessage();
  document.getElementById("weather-description").textContent =
    "Fetching weather data...";
  document.getElementById("main-temp").textContent = "--°";

  try {
    if (!API_KEY) {
      throw new Error(
        "OpenWeatherMap API Key is missing! Please replace the placeholder."
      );
    }

    let lat, lon, name, country;

    if (isCoord) {
      // Coordinates were passed directly
      lat = query.lat;
      lon = query.lon;
      name = "Current Location";
      country = "GPS";

      // Optional: Reverse Geocoding to get a real city name for display
      const reverseGeoUrl = `https://api.openweathermap.org/geo/1.0/reverse?lat=${lat}&lon=${lon}&limit=1&appid=${API_KEY}`;
      const reverseGeoData = await fetchWithBackoff(reverseGeoUrl);

      if (reverseGeoData && reverseGeoData.length > 0) {
        name = reverseGeoData[0].name;
        country = reverseGeoData[0].country;
      }
    } else {
      // City name was passed (Standard Geo-Coding)
      // --- STEP 1: Geo-Coding (City Name -> Coordinates) ---
      const geoUrl = `https://api.openweathermap.org/geo/1.0/direct?q=${query}&limit=1&appid=${API_KEY}`;
      const geoData = await fetchWithBackoff(geoUrl);

      if (!geoData || geoData.length === 0) {
        throw new Error(
          `Location not found for "${query}". Please try a different name.`
        );
      }

      lat = geoData[0].lat;
      lon = geoData[0].lon;
      name = geoData[0].name;
      country = geoData[0].country;
    }

    // --- STEP 2: Fetch Current Weather ---
    const weatherUrl = `${API_BASE_URL}weather?lat=${lat}&lon=${lon}&appid=${API_KEY}`;
    const currentData = await fetchWithBackoff(weatherUrl);

    // --- STEP 3: Fetch 5-Day Forecast (Hourly/3-hr steps) ---
    const forecastUrl = `${API_BASE_URL}forecast?lat=${lat}&lon=${lon}&appid=${API_KEY}`;
    const forecastData = await fetchWithBackoff(forecastUrl);

    if (!currentData || !forecastData) {
      throw new Error("Could not retrieve all necessary weather data.");
    }

    // Store Location info
    weatherData.name = name;
    weatherData.country = country;

    // Map current weather data
    weatherData.current = currentData;

    // Map forecast data
    weatherData.forecast = forecastData;

    showMessage(
      `Weather data successfully loaded for ${name}, ${country}!`
    );
    renderUI();
  } catch (error) {
    console.error("API Fetch Error:", error.message);
    // Reset data on error
    weatherData.current = null;
    weatherData.forecast = null;
    document.getElementById("weather-description").textContent =
      "Failed to load weather.";
    document.getElementById("main-temp").textContent = "--°";
    showMessage(`Failed to fetch weather: ${error.message}`, true);
  }
}

// --- Geolocation Functions ---

function getCurrentLocation() {
  closeModal();
  showMessage("Requesting current location from browser...");

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        showMessage("Location retrieved. Fetching weather...");
        const coords = {
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        };
        fetchWeatherData(coords, true); // Pass coordinates and flag as coordinates
      },
      (error) => {
        let errorMessage = "Geolocation failed. ";
        if (error.code === error.PERMISSION_DENIED) {
          errorMessage +=
            "Please enable location services and grant permission to the browser.";
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          errorMessage +=
            "Location information is currently unavailable.";
        } else if (error.code === error.TIMEOUT) {
          errorMessage += "Request timed out. Try again.";
        } else {
          errorMessage += "An unknown error occurred.";
        }
        showMessage(errorMessage, true);
      },
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );
  } else {
    showMessage("Geolocation is not supported by this browser.", true);
  }
}

// --- Modal Control Functions ---

function openModal() {
  locationModal.classList.remove("hidden");
  locationModal.classList.add("flex");

  modalCityInput.focus();
}

function closeModal() {
  locationModal.classList.add("hidden");
  locationModal.classList.remove("flex");
}

async function handleSearch(inputElement) {
  const city = inputElement.value.trim();
  if (city) {
    // Close modal if search came from modal
    if (inputElement.id === "modal-city-input") {
      closeModal();
    }
    // Fetch the weather data using city name
    await fetchWeatherData(city, false);
  } else {
    showMessage("Please enter a valid city name.", true);
  }
}

// --- Event Listeners ---

// Main Search Icon Button (opens the location modal)
mainSearchButton.addEventListener("click", openModal);

// Modal Open Button (Map click)
openMapModalButton.addEventListener("click", openModal);

// Modal Close Button
closeModalButton.addEventListener("click", closeModal);

// Modal Fetch Button
modalFetchButton.addEventListener("click", () =>
  handleSearch(modalCityInput)
);
modalCityInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    handleSearch(modalCityInput);
  }
});

// NEW LISTENER: Current Location Button
currentLocationButton.addEventListener("click", getCurrentLocation);

// Initialize state (empty)
// Set the initial dark background placeholder
document.body.style.backgroundImage = `var(--bg-image)`;