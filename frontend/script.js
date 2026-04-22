// =============================
// SYNC
// =============================

let isFetchingWeather = false;
const syncingStates = {}; // track per-site button state

function appendLog(logsDiv, line) {
  logsDiv.appendChild(line);
  while (logsDiv.children.length > 200) {
    logsDiv.removeChild(logsDiv.firstChild);
  }
  logsDiv.scrollTop = logsDiv.scrollHeight;
}

async function startSync(site) {
  const statusEl = document.getElementById(`status-${site}`);
  const btnEl    = document.getElementById(`sync-btn-${site}`);

  if (syncingStates[site]) return;
  syncingStates[site] = true;

  if (statusEl) statusEl.innerText = "Syncing...";
  if (btnEl)    btnEl.disabled = true;

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

document.addEventListener('DOMContentLoaded', function () {
  const canvas = document.getElementById('chartCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');

  const data = [
    { index: 1, value: 45 },
    { index: 2, value: 55 },
    { index: 3, value: 65 },
    { index: 4, value: 80 },
    { index: 5, value: 75 },
    { index: 6, value: 90 },
    { index: 7, value: 98 }
  ];

  const MIN = 40;
  const MAX = 100;
  const CYAN = 65;
  const RED = 80;

  function getY(value, height, pad) {
    const range = MAX - MIN;
    const norm = (value - MIN) / range;
    return canvas.height - pad - (height * norm);
  }

  function drawChart() {
    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;

    const pad = 20;
    const w = canvas.width - 2 * pad;
    const h = canvas.height - 2 * pad;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#333';
    ctx.setLineDash([4, 4]);
    for (let i = 1; i < 4; i++) {
      const y = pad + h * (i / 4);
      ctx.beginPath();
      ctx.moveTo(pad, y);
      ctx.lineTo(canvas.width - pad, y);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    const yCyan = getY(CYAN, h, pad);
    const yRed  = getY(RED, h, pad);

    ctx.strokeStyle = '#00FFFF';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad, yCyan);
    ctx.lineTo(canvas.width - pad, yCyan);
    ctx.stroke();

    ctx.strokeStyle = '#EF4444';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad, yRed);
    ctx.lineTo(canvas.width - pad, yRed);
    ctx.stroke();

    ctx.strokeStyle = '#00E676';
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (let i = 0; i < data.length; i++) {
      const x = pad + w * (i / (data.length - 1));
      const y = getY(data[i].value, h, pad);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  drawChart();
  window.addEventListener('resize', drawChart);
});


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

  const searchInput  = document.getElementById('search-input');
  const searchButton = document.getElementById('search-button');
  const loading      = document.getElementById('loading-indicator');

  const temp = document.getElementById('temp-value');
  const max  = document.getElementById('temp-max');
  const min  = document.getElementById('temp-min');
  const cond = document.getElementById('current-condition');
  const loc  = document.getElementById('current-location');
  const icon = document.getElementById('current-icon');

  function updateUI(data) {
    temp.textContent = Math.round(data.main.temp);
    max.textContent  = Math.round(data.main.temp_max);
    min.textContent  = Math.round(data.main.temp_min);
    cond.textContent = data.weather[0].description;
    loc.textContent  = `${data.name}, ${data.sys.country}`;
    icon.innerHTML   = `<img src="https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png" alt="weather icon">`;
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