
const DATA_URL = "data/briefing.json";

let appData = null;
let map = null;
let chart = null;
let cityMarkers = [];
let currentNewsCategory = "All";

document.addEventListener("DOMContentLoaded", initialiseApp);

async function initialiseApp() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });

    if (!response.ok) {
      throw new Error(`Could not load ${DATA_URL}`);
    }

    appData = await response.json();

    renderNationalOverview();
    renderMetrics();
    renderTimeline();
    initialiseMap();
    populateSelectors();
    renderIncidents();
    renderNews();
    renderConversationBrief();
  } catch (error) {
    console.error(error);
    document.body.insertAdjacentHTML(
      "afterbegin",
      `<div class="data-warning" style="margin:12px">
        The app could not load its data file. Run it through a local web server rather than opening index.html directly.
      </div>`
    );
  }
}

function renderNationalOverview() {
  const national = appData.national;

  document.getElementById("national-risk-score").textContent = national.score;
  document.getElementById("national-summary").textContent = national.summary;

  const badge = document.getElementById("national-risk-badge");
  badge.textContent = national.level;
  badge.className = `risk-badge ${riskClass(national.score)}`;

  const direction = document.getElementById("risk-direction");
  const movement = national.seven_day_change;

  if (movement > 0) {
    direction.textContent = `▲ ${movement}`;
    direction.className = "trend trend-up";
  } else if (movement < 0) {
    direction.textContent = `▼ ${Math.abs(movement)}`;
    direction.className = "trend trend-down";
  } else {
    direction.textContent = "● Stable";
    direction.className = "trend trend-flat";
  }

  const breakdown = document.getElementById("risk-breakdown");
  breakdown.innerHTML = national.components.map(component => `
    <div class="breakdown-row">
      <span>${escapeHtml(component.name)}</span>
      <div class="breakdown-bar">
        <div class="breakdown-fill" style="width:${component.score}%"></div>
      </div>
      <strong>${component.score}</strong>
    </div>
  `).join("");
}

function renderMetrics() {
  document.getElementById("active-disruptions").textContent =
    appData.incidents.filter(item => item.status === "Active").length;

  document.getElementById("city-count").textContent = appData.cities.length;

  const highest = [...appData.cities].sort((a, b) => b.score - a.score)[0];
  document.getElementById("highest-risk-city").textContent = highest.name;
  document.getElementById("highest-risk-city-score").textContent =
    `${highest.level} — ${highest.score}/100`;

  document.getElementById("generated-time").textContent = appData.metadata.generated_display;
}

function renderTimeline() {
  const context = document.getElementById("riskChart");

  chart = new Chart(context, {
    type: "line",
    data: {
      labels: appData.timeline.map(point => point.date),
      datasets: [{
        label: "National risk score",
        data: appData.timeline.map(point => point.score),
        borderWidth: 3,
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 7,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: "nearest"
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: { stepSize: 20 }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel(context) {
              return appData.timeline[context.dataIndex].explanation;
            }
          }
        }
      },
      onClick(event, elements) {
        if (!elements.length) return;

        const selected = appData.timeline[elements[0].index];
        document.getElementById("timeline-explanation").innerHTML =
          `<strong>${escapeHtml(selected.date)} — ${selected.score}/100:</strong>
           ${escapeHtml(selected.explanation)}`;
      }
    }
  });
}

function initialiseMap() {
  const southAfricaBounds = L.latLngBounds(
    [-35.3, 16.2],
    [-22.0, 33.2]
  );

  map = L.map("risk-map", {
    minZoom: 5,
    maxZoom: 17,
    maxBounds: southAfricaBounds,
    maxBoundsViscosity: 1.0,
    zoomControl: true
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    noWrap: true,
    bounds: southAfricaBounds
  }).addTo(map);

  cityMarkers = appData.cities.map(city => {
    const marker = L.circleMarker(
      [city.latitude, city.longitude],
      {
        radius: scoreToRadius(city.score),
        color: riskColour(city.score),
        fillColor: riskColour(city.score),
        fillOpacity: 0.78,
        weight: 2
      }
    ).addTo(map);

    marker.bindPopup(`
      <strong>${escapeHtml(city.name)}</strong><br>
      ${escapeHtml(city.level)} risk — ${city.score}/100<br>
      <small>${escapeHtml(city.summary)}</small>
    `);

    marker.on("click", () => updateSelectedArea(city));

    return {
      city,
      marker
    };
  });

  map.fitBounds(southAfricaBounds, {
    padding: [10, 10]
  });

  setTimeout(() => {
    map.invalidateSize();
    map.fitBounds(southAfricaBounds, {
      padding: [10, 10]
    });
  }, 200);
}

function populateSelectors() {
  const citySelector = document.getElementById("city-selector");
  const incidentFilter = document.getElementById("incident-city-filter");
  const newsSelector = document.getElementById("news-location-selector");

  appData.cities.forEach(city => {
    citySelector.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHtml(city.id)}">${escapeHtml(city.name)}</option>`
    );

    incidentFilter.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHtml(city.name)}">${escapeHtml(city.name)}</option>`
    );

    newsSelector.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHtml(city.id)}">${escapeHtml(city.name)} local news</option>`
    );
  });

  citySelector.addEventListener("change", handleCitySelection);
  incidentFilter.addEventListener("change", renderIncidents);
  document.getElementById("incident-type-filter").addEventListener("change", renderIncidents);
  newsSelector.addEventListener("change", () => {
    currentNewsCategory = "All";
    renderNews();
  });
}

function handleCitySelection(event) {
  if (event.target.value === "national") {
    map.fitBounds(L.latLngBounds([-35.2, 16.0], [-22.0, 33.5]));
    updateSelectedArea(null);
    return;
  }

  const city = appData.cities.find(item => item.id === event.target.value);
  if (!city) return;

  map.flyTo([city.latitude, city.longitude], city.default_zoom || 11, {
    duration: 1.1
  });

  updateSelectedArea(city);

  const markerEntry = cityMarkers.find(entry => entry.city.id === city.id);
  if (markerEntry) markerEntry.marker.openPopup();
}

function updateSelectedArea(city) {
  const name = document.getElementById("selected-area-name");
  const risk = document.getElementById("selected-area-risk");
  const summary = document.getElementById("selected-area-summary");

  if (!city) {
    name.textContent = "South Africa";
    risk.textContent = `National risk: ${appData.national.score}/100`;
    summary.textContent = appData.national.summary;
    return;
  }

  name.textContent = city.name;
  risk.textContent = `${city.level} risk: ${city.score}/100`;
  summary.textContent = city.summary;

  document.getElementById("city-selector").value = city.id;
}

function renderIncidents() {
  const selectedCity = document.getElementById("incident-city-filter").value;
  const selectedType = document.getElementById("incident-type-filter").value.toLowerCase();

  const incidents = appData.incidents.filter(incident => {
    const cityMatches = selectedCity === "all" || incident.location === selectedCity;
    const typeMatches = selectedType === "all" || incident.type.toLowerCase() === selectedType;
    return cityMatches && typeMatches;
  });

  const list = document.getElementById("incident-list");

  if (!incidents.length) {
    list.innerHTML = `<div class="empty-state">No incidents match the selected filters.</div>`;
    return;
  }

  list.innerHTML = incidents.map(incident => `
    <article class="incident-card">
      <div class="panel-heading">
        <span class="severity-badge ${severityClass(incident.severity)}">
          ${escapeHtml(incident.severity)}
        </span>
        <span class="news-tag">${escapeHtml(incident.status)}</span>
      </div>
      <h3>${escapeHtml(incident.title)}</h3>
      <div class="incident-meta">
        <span>${escapeHtml(incident.location)}</span>
        <span>${escapeHtml(incident.type)}</span>
        <span>${escapeHtml(incident.time_window)}</span>
      </div>
      <p>${escapeHtml(incident.summary)}</p>
      <p><strong>Suggested action:</strong> ${escapeHtml(incident.action)}</p>
      <div class="incident-meta">
        <span>Confidence: ${escapeHtml(incident.confidence)}</span>
        <span>Source: ${escapeHtml(incident.source)}</span>
      </div>
    </article>
  `).join("");
}

function renderNews() {
  const location = document.getElementById("news-location-selector").value;
  const filteredByLocation = appData.news.filter(story =>
    location === "national" ? story.location === "National" : story.city_id === location
  );

  const categories = ["All", ...new Set(filteredByLocation.map(story => story.category))];
  const categoryTabs = document.getElementById("news-category-tabs");

  categoryTabs.innerHTML = categories.map(category => `
    <button
      class="category-button ${category === currentNewsCategory ? "active" : ""}"
      data-category="${escapeHtml(category)}"
      type="button"
    >
      ${escapeHtml(category)}
    </button>
  `).join("");

  categoryTabs.querySelectorAll("button").forEach(button => {
    button.addEventListener("click", () => {
      currentNewsCategory = button.dataset.category;
      renderNews();
    });
  });

  const finalStories = filteredByLocation.filter(story =>
    currentNewsCategory === "All" || story.category === currentNewsCategory
  );

  const newsList = document.getElementById("news-list");

  if (!finalStories.length) {
    newsList.innerHTML = `<div class="empty-state">No demo stories are available for this selection.</div>`;
    return;
  }

  newsList.innerHTML = finalStories.map(story => `
    <article class="news-card">
      <div class="panel-heading">
        <span class="news-tag">${escapeHtml(story.category)}</span>
        <span class="severity-badge ${severityClass(story.relevance)}">
          ${escapeHtml(story.relevance)} relevance
        </span>
      </div>
      <h3>${escapeHtml(story.title)}</h3>
      <div class="news-meta">
        <span>${escapeHtml(story.location)}</span>
        <span>Published: ${escapeHtml(story.published)}</span>
        <span>Event date: ${escapeHtml(story.event_date)}</span>
      </div>
      <p>${escapeHtml(story.summary)}</p>
      <div class="news-meta">
        <span>Source: ${escapeHtml(story.source)}</span>
        <span>Confidence: ${escapeHtml(story.confidence)}</span>
      </div>
    </article>
  `).join("");
}

function renderConversationBrief() {
  const grid = document.getElementById("conversation-grid");

  grid.innerHTML = appData.conversation_brief.map(item => `
    <article class="conversation-card">
      <span class="news-tag">${escapeHtml(item.topic)}</span>
      <h3>${escapeHtml(item.heading)}</h3>
      <p>${escapeHtml(item.context)}</p>
      <div class="sentence-starter">
        <strong>Neutral sentence starter</strong><br>
        “${escapeHtml(item.starter)}”
      </div>
      <div class="avoid-box">
        <strong>Avoid assuming</strong><br>
        ${escapeHtml(item.avoid)}
      </div>
    </article>
  `).join("");
}

function scoreToRadius(score) {
  return Math.max(8, Math.min(19, score / 4.8));
}

function riskColour(score) {
  if (score >= 85) return "#721c24";
  if (score >= 70) return "#c92a2a";
  if (score >= 50) return "#e87524";
  if (score >= 30) return "#e0a800";
  return "#2e8b57";
}

function riskClass(score) {
  if (score >= 85) return "risk-severe";
  if (score >= 70) return "risk-high";
  if (score >= 50) return "risk-elevated";
  if (score >= 30) return "risk-guarded";
  return "risk-low";
}

function severityClass(value) {
  const normalised = String(value).toLowerCase();

  if (["high", "severe"].includes(normalised)) return "severity-high";
  if (["medium", "moderate", "elevated"].includes(normalised)) return "severity-medium";
  return "severity-low";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
