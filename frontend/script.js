// =============================
// SYNC
// =============================
let selectedSite = null;
let selectedDate = null;

let isFetchingWeather = false;
const syncingStates = {}; // track per-site button state


//site selection
function selectSite(site) {
  selectedSite = site;
  selectedDate = null;

  console.log("Selected site:", site);

  // Show calendar panel
  const panel = document.getElementById("calendar-panel");
  panel.classList.remove("hidden");

  loadDatesForSite(site);
  expandSiteCard(site);
  drawChartForSite();
}

//expand site on selection
function expandSiteCard(site) {
  const allCards = document.querySelectorAll(".site-card");

  allCards.forEach(card => {
    if (card.id === `site-card-${site}`) {
      card.classList.remove("hidden");
    } else {
      card.classList.add("hidden");
    }
  });
}

async function loadDatesForSite(site) {
  console.log("Loading dates for:", site);

  const dateList = document.getElementById("date-list");

  const dates = await window.electronAPI.getDates(site);

  dateList.innerHTML = "";

  if (!dates || dates.length === 0) {
    dateList.innerHTML = `
      <span class="text-gray-400">No data available</span>
    `;
    return;
  }

  dates.forEach(date => {
    const el = document.createElement("div");

    el.textContent = date;

    el.className = `
      p-3 rounded-lg cursor-pointer
      text-text-main dark:text-dark-text-main
      hover:bg-secondary dark:hover:bg-dark-secondary
    `;

    el.onclick = () => {
      selectedDate = date;

      document.querySelectorAll("#date-list div").forEach(d => {
        d.classList.remove("bg-accent-blue", "text-white");
      });

      el.classList.add("bg-accent-blue", "text-white");

      console.log("Selected date:", date);

      loadImagesForSelection();
    };

    dateList.appendChild(el);
  });
}


// ========================
// AOI CONFIG (FROM PYTHON)
// ========================
const SITES_CONFIG = {
  site1: [[88.03, 27.72],[88.06, 27.72],[88.06, 27.75],[88.03, 27.75],[88.03, 27.72]],
  site2: [[88.68, 28.03],[88.72, 28.03],[88.72, 28.07],[88.68, 28.07],[88.68, 28.03]],
  site3: [[79.05, 30.72],[79.08, 30.72],[79.08, 30.75],[79.05, 30.75],[79.05, 30.72]],
  site4: [[86.92, 27.87],[86.96, 27.87],[86.96, 27.91],[86.92, 27.91],[86.92, 27.87]],
};

// ========================
// AREA CALCULATION (KM²)
// ========================

// Shoelace formula + lat/lon correction
function calculateAOIAreaKm2(coords) {
  const R = 6371; // Earth radius in km

  let area = 0;

  for (let i = 0; i < coords.length - 1; i++) {
    const [lon1, lat1] = coords[i];
    const [lon2, lat2] = coords[i + 1];

    // Convert degrees → radians
    const x1 = lon1 * Math.PI / 180;
    const y1 = lat1 * Math.PI / 180;
    const x2 = lon2 * Math.PI / 180;
    const y2 = lat2 * Math.PI / 180;

    area += (x2 - x1) * (2 + Math.sin(y1) + Math.sin(y2));
  }

  area = area * (R * R / 2);

  return Math.abs(area); // km²
}


async function loadImagesForSelection() {
  if (!selectedSite || !selectedDate) return;

  const types = ["rgb", "prob", "overlay", "contour"];

  const ids = {
    rgb: "img-rgb",
    prob: "img-prob",
    overlay: "img-overlay",
    contour: "img-contour"
  };

  // Hide ALL placeholders when images load
  document.getElementById("rgb-placeholder")?.classList.add("hidden");
  document.getElementById("prob-placeholder")?.classList.add("hidden");
  document.getElementById("-placeholder")?.classList.add("hidden");

  // ========================
  // LOAD IMAGES
  // ========================

  for (const type of types) {
    const path = await window.electronAPI.getImagePath(
      selectedSite,
      selectedDate,
      type
    );

    const img = document.getElementById(ids[type]);

    if (img) {
      img.src = path + "?t=" + new Date().getTime();
      img.classList.remove("hidden");
    }
  }

  // Hide contour placeholder
  document.getElementById("contour-placeholder")?.classList.add("hidden");

  // ========================
  // LOAD METRICS (FIXED)
  // ========================
  const metrics = await window.electronAPI.getMetrics(
    selectedSite,
    selectedDate
  );

  console.log("METRICS:", metrics);

  const statsDiv = document.getElementById("stats-content");

  if (!metrics) {
    statsDiv.innerHTML = `<p class="text-gray-400">No data available</p>`;
    return;
  }

  // Extract values safely
  const area =
    metrics.metrics?.lake_area_km2 ?? metrics.lake_area_km2;

  const coverage =
    metrics.metrics?.lake_coverage_percent ??
    metrics.lake_coverage_percent;

  // ========================
// COMPUTE TOTAL AREA (FROM AOI)
// ========================
const totalArea = calculateAOIAreaKm2(SITES_CONFIG[selectedSite]);

// ========================
// COMPUTE CHANGE + GROWTH
// ========================

// Get all dates for this site
const dates = await window.electronAPI.getDates(selectedSite);

// Find current index
const index = dates.indexOf(selectedDate);

// Get previous date
const prevDate = index > 0 ? dates[index - 1] : null;

let change = null;
let changePercent = null;
let growthRate = null;

if (prevDate) {
  const prevMetrics = await window.electronAPI.getMetrics(
    selectedSite,
    prevDate
  );

  const prevArea =
    prevMetrics?.metrics?.lake_area_km2 ??
    prevMetrics?.lake_area_km2;

  if (prevArea !== undefined && area !== undefined && prevArea !== 0) {
    change = area - prevArea;
    changePercent = (change / prevArea) * 100;

    // Assuming 14-day interval
    const daysBetween = 14;
    growthRate = change / daysBetween;
  }
}

  // Final UI (MAIN PART)
  if (area !== undefined && coverage !== undefined) {
    statsDiv.innerHTML = `
    <div class="space-y-3">
     

      <p><span class="font-semibold">Date:</span> ${selectedDate}</p>

      <p><span class="font-semibold">Total Area:</span> ${
          totalArea !== undefined ? totalArea.toFixed(2) : "—"
      } km²</p>

      <p><span class="font-semibold">Water Area:</span> ${area.toFixed(3)} km²</p>
      <p><span class="font-semibold">Coverage:</span> ${coverage.toFixed(2)}%</p>

      

      <p><span class="font-semibold">Change:</span> ${change !== undefined ? change.toFixed(3) : "—"
      } km² (${changePercent !== null ? changePercent.toFixed(2) : "—"}%)</p>

      <p><span class="font-semibold">Growth Rate:</span> ${growthRate !== null ? growthRate.toFixed(4) : "—"} km²/day</p>


    </div>
  `;
  } else {
    console.error("Invalid metrics format:", metrics);
    statsDiv.innerHTML = `<p class="text-gray-400">Invalid data</p>`;
  }
}

  function appendLog(logsDiv, line) {
    logsDiv.appendChild(line);
    while (logsDiv.children.length > 200) {
      logsDiv.removeChild(logsDiv.firstChild);
    }
    logsDiv.scrollTop = logsDiv.scrollHeight;
  }

  async function startSync(site) {
    const statusEl = document.getElementById(`status-${site}`);
    const btnEl = document.getElementById(`sync-btn-${site}`);

    if (syncingStates[site]) return;
    syncingStates[site] = true;

    if (statusEl) statusEl.innerText = "Syncing...";
    if (btnEl) btnEl.disabled = true;

    try {
      const result = await window.electronAPI.syncData(site);

      if (result.status === "success") {
        if (statusEl) statusEl.innerText = "Up to date";
      } else if (result.status === "busy") {
        if (statusEl) statusEl.innerText = "Already running";
      } else {
        if (statusEl) statusEl.innerText = `Error: ${result.message}`;
      }

    } catch (err) {
      console.error(err);
      if (statusEl) statusEl.innerText = "Failed";
    } finally {
      syncingStates[site] = false;
      if (btnEl) btnEl.disabled = false;
    }
  }

  if (window.electronAPI) {
    window.electronAPI.onLog(({ site, msg }) => {
      console.log(`LOG [${site}]:`, msg);
      const logsDiv = document.getElementById("logs");
      if (logsDiv) {
        const line = document.createElement("div");
        line.textContent = `[${site}] ${msg}`;
        appendLog(logsDiv, line);
      }
    });

    window.electronAPI.onError(({ site, msg }) => {
      console.error(`ERROR [${site}]:`, msg);
      const logsDiv = document.getElementById("logs");
      if (logsDiv) {
        const line = document.createElement("div");
        line.textContent = `ERROR [${site}]: ${msg}`;
        line.style.color = "#f87171";
        appendLog(logsDiv, line);
      }
    });
  }

  window.addEventListener('beforeunload', () => {
    if (window.electronAPI) window.electronAPI.removeListeners();
  });


  // =============================
  // CHART LOGIC
  // =============================

// =============================
// CHART LOGIC (FINAL)
// =============================

document.addEventListener('DOMContentLoaded', function () {
  const canvas = document.getElementById('chartCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');

  // Empty state
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = 240;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#9CA3AF";
  ctx.font = "14px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("Select a site to view chart", canvas.width / 2, canvas.height / 2);
});


// =============================
// DRAW CHART ON SITE SELECT
// =============================

async function drawChartForSite() {
  if (!selectedSite) return;

  const canvas = document.getElementById('chartCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');

  const container = canvas.parentElement;
  canvas.width = container.clientWidth;
  canvas.height = 240;

  // ========================
  // FETCH DATA
  // ========================
  const dates = await window.electronAPI.getDates(selectedSite);

  const data = [];

  for (let i = 0; i < dates.length; i++) {
    const m = await window.electronAPI.getMetrics(selectedSite, dates[i]);

    const val =
      m?.metrics?.lake_area_km2 ?? m?.lake_area_km2;

    if (val !== undefined) {
      data.push({ index: i, value: val });
    }
  }

  if (data.length === 0) return;

  // ========================
  // SCALE
  // ========================
  const values = data.map(d => d.value);
  const MIN = Math.min(...values);
  const MAX = Math.max(...values);

  const pad = 30;
  const w = canvas.width - 2 * pad;
  const h = canvas.height - 2 * pad;

  function getY(value) {
    const range = MAX - MIN || 1;
    const norm = (value - MIN) / range;
    return canvas.height - pad - (h * norm);
  }

  // ========================
  // CLEAR
  // ========================
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // ========================
  // AXES
  // ========================
  ctx.strokeStyle = '#888';
  ctx.lineWidth = 1;

  // Y-axis
  ctx.beginPath();
  ctx.moveTo(pad, pad);
  ctx.lineTo(pad, canvas.height - pad);
  ctx.stroke();

  // X-axis
  ctx.beginPath();
  ctx.moveTo(pad, canvas.height - pad);
  ctx.lineTo(canvas.width - pad, canvas.height - pad);
  ctx.stroke();

  // ========================
  // Y LABELS
  // ========================
  ctx.fillStyle = '#aaa';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'right';

  ctx.fillText(MAX.toFixed(2), pad - 5, pad + 5);
  ctx.fillText(MIN.toFixed(2), pad - 5, canvas.height - pad);

  // ========================
  // X LABELS (DATES)
  // ========================
  ctx.textAlign = 'center';

  const step = Math.ceil(data.length / 4);

  for (let i = 0; i < data.length; i += step) {
    const x = pad + w * (i / (data.length - 1));

    ctx.fillText(
      dates[i],
      x,
      canvas.height - pad + 12
    );
  }

  // ========================
  // LINE
  // ========================
  ctx.strokeStyle = '#00E676';
  ctx.lineWidth = 2;

  ctx.beginPath();

  for (let i = 0; i < data.length; i++) {
    const x = pad + w * (i / (data.length - 1));
    const y = getY(data[i].value);

    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }

  ctx.stroke();
}

  // =============================
  // DARK MODE
  // =============================

  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('dark-mode-toggle');
    if (btn) {
      btn.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
      });
    }
  });


  // =============================
  // WEATHER SEARCH
  // =============================

  document.addEventListener('DOMContentLoaded', () => {

    const API_KEY = process.env.OWM_API_KEY || "YOUR_API_KEY";

    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const loading = document.getElementById('loading-indicator');

    const temp = document.getElementById('temp-value');
    const max = document.getElementById('temp-max');
    const min = document.getElementById('temp-min');
    const cond = document.getElementById('current-condition');
    const loc = document.getElementById('current-location');
    const icon = document.getElementById('current-icon');

    function updateUI(data) {
      temp.textContent = Math.round(data.main.temp);
      max.textContent = Math.round(data.main.temp_max);
      min.textContent = Math.round(data.main.temp_min);
      cond.textContent = data.weather[0].description;
      loc.textContent = `${data.name}, ${data.sys.country}`;
      icon.innerHTML = `<img src="https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png" alt="weather icon">`;
    }

    async function searchCity() {
      if (isFetchingWeather) return;
      const q = searchInput.value.trim();
      if (!q) return;

      isFetchingWeather = true;
      loading.classList.remove('hidden');

      try {
        const geo = await fetch(
          `https://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(q)}&limit=1&appid=${API_KEY}`
        );
        if (!geo.ok) throw new Error("Geocoding request failed");
        const geoData = await geo.json();
        if (!geoData.length) throw new Error("City not found");

        const { lat, lon } = geoData[0];

        const weather = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`
        );
        if (!weather.ok) throw new Error("Weather request failed");
        const data = await weather.json();

        updateUI(data);

      } catch (e) {
        alert(e.message);
      } finally {
        isFetchingWeather = false;
        loading.classList.add('hidden');
      }
    }

    if (searchButton) searchButton.addEventListener('click', searchCity);
    if (searchInput) {
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') searchCity();
      });
    }
  });