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

  document.getElementById("generated-time").textContent =
    appData.metadata.generated_display;
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
    [-35.4, 16.0],
    [-22.0, 33.4]
  );

  map = L.map("risk-map", {
    minZoom: 5,
    maxZoom: 14,
    maxBounds: southAfricaBounds.pad(0.18),
    maxBoundsViscosity: 0.92,
    zoomControl: true,
    attributionControl: true
  });

  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      subdomains: "abcd",
      maxZoom: 20
    }
  ).addTo(map);

  map.fitBounds(southAfricaBounds, {
    padding: [26, 26]
  });

  cityMarkers = appData.cities.map(city => {
    const colour = riskColour(city.score);

    const icon = L.divIcon({
      className: "intelligence-node-wrapper",
      html: `
        <button
          class="intelligence-node ${riskClass(city.score)}"
          type="button"
          aria-label="${escapeHtml(city.name)}: ${escapeHtml(city.level)} risk, ${city.score} out of 100"
          style="--node-risk-colour:${colour}"
        >
          <span class="intelligence-node-ring"></span>
          <span class="intelligence-node-core">
            <strong>${city.score}</strong>
          </span>
          <span class="intelligence-node-label">
            ${escapeHtml(city.name)}
          </span>
        </button>
      `,
      iconSize: [138, 52],
      iconAnchor: [26, 26]
    });

    const marker = L.marker(
      [city.latitude, city.longitude],
      {
        icon,
        keyboard: true,
        riseOnHover: true,
        title: `${city.name}: ${city.level} risk`
      }
    ).addTo(map);

    marker.on("click", () => selectMapCity(city, true));

    marker.bindTooltip(
      `<strong>${escapeHtml(city.name)}</strong><br>
       ${escapeHtml(city.level)} — ${city.score}/100`,
      {
        direction: "top",
        offset: [0, -20],
        className: "intelligence-tooltip",
        opacity: 1
      }
    );

    return {
      city,
      marker
    };
  });

  const resetButton = document.getElementById("map-reset-button");

  if (resetButton) {
    resetButton.addEventListener("click", resetMapToNational);
  }

  updateSelectedArea(null);

  setTimeout(() => {
    map.invalidateSize();
  }, 150);
}

function selectMapCity(city, moveMap = true) {
  if (!city) return;

  if (moveMap) {
    map.flyTo(
      [city.latitude, city.longitude],
      Math.min(city.default_zoom || 9, 10),
      {
        duration: 0.85
      }
    );
  }

  updateSelectedArea(city);
  updateSelectedMarker(city.id);

  const selector = document.getElementById("city-selector");

  if (selector) {
    selector.value = city.id;
  }
}

function updateSelectedMarker(selectedCityId) {
  cityMarkers.forEach(({ city, marker }) => {
    const element = marker.getElement();

    if (!element) return;

    const node = element.querySelector(".intelligence-node");

    if (!node) return;

    node.classList.toggle(
      "selected",
      city.id === selectedCityId
    );
  });
}

function resetMapToNational() {
  const southAfricaBounds = L.latLngBounds(
    [-35.4, 16.0],
    [-22.0, 33.4]
  );

  map.fitBounds(southAfricaBounds, {
    padding: [26, 26]
  });

  updateSelectedMarker(null);
  updateSelectedArea(null);

  const selector = document.getElementById("city-selector");

  if (selector) {
    selector.value = "national";
  }
}

function populateSelectors() {
  const citySelector =
    document.getElementById("city-selector");

  const incidentFilter =
    document.getElementById("incident-city-filter");

  const newsSelector =
    document.getElementById("news-location-selector");

  appData.cities.forEach(city => {
    citySelector.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHtml(city.id)}">
        ${escapeHtml(city.name)}
      </option>`
    );

    incidentFilter.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHtml(city.name)}">
        ${escapeHtml(city.name)}
      </option>`
    );

    newsSelector.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHtml(city.id)}">
        ${escapeHtml(city.name)} local news
      </option>`
    );
  });

  citySelector.addEventListener(
    "change",
    handleCitySelection
  );

  incidentFilter.addEventListener(
    "change",
    renderIncidents
  );

  document
    .getElementById("incident-type-filter")
    .addEventListener(
      "change",
      renderIncidents
    );

  newsSelector.addEventListener(
    "change",
    () => {
      currentNewsCategory = "All";
      renderNews();
    }
  );
}

function handleCitySelection(event) {
  if (event.target.value === "national") {
    resetMapToNational();
    return;
  }

  const city = appData.cities.find(
    item => item.id === event.target.value
  );

  if (!city) return;

  selectMapCity(city, true);
}

function updateSelectedArea(city) {
  const name =
    document.getElementById("selected-area-name");

  const risk =
    document.getElementById("selected-area-risk");

  const score =
    document.getElementById("selected-area-score");

  const summary =
    document.getElementById("selected-area-summary");

  const action =
    document.getElementById("selected-area-action");

  const status =
    document.getElementById("selected-area-status");

  const monitoredCities =
    document.getElementById("map-monitored-cities");

  const activeDisruptions =
    document.getElementById("map-active-disruptions");

  const generatedTime =
    document.getElementById("map-generated-time");

  if (monitoredCities) {
    monitoredCities.textContent =
      appData.cities.length;
  }

  if (activeDisruptions) {
    activeDisruptions.textContent =
      appData.incidents.filter(
        item => item.status === "Active"
      ).length;
  }

  if (generatedTime) {
    generatedTime.textContent =
      appData.metadata.generated_display || "—";
  }

  if (!city) {
    name.textContent = "South Africa";

    score.textContent =
      appData.national.score;

    risk.textContent =
      `${appData.national.level} national risk`;

    risk.className =
      `selected-risk ${riskClass(appData.national.score)}`;

    summary.textContent =
      appData.national.summary;

    action.textContent =
      buildBusinessImplication(
        appData.national.score,
        null
      );

    status.textContent = "National";
    status.className = "map-status-chip";

    return;
  }

  name.textContent = city.name;

  score.textContent = city.score;

  risk.textContent =
    `${city.level} risk`;

  risk.className =
    `selected-risk ${riskClass(city.score)}`;

  summary.textContent =
    city.summary;

  action.textContent =
    buildBusinessImplication(
      city.score,
      city.name
    );

  status.textContent =
    city.level;

  status.className =
    `map-status-chip ${riskClass(city.score)}`;
}

function buildBusinessImplication(
  score,
  cityName
) {
  const locationText = cityName
    ? ` for travel in ${cityName}`
    : " for travel across South Africa";

  if (score >= 85) {
    return `Severe operational exposure${locationText}. Review whether travel is essential, obtain current security advice and maintain contingency arrangements.`;
  }

  if (score >= 70) {
    return `High operational exposure${locationText}. Review movement plans, allow additional journey time and confirm local security and transport arrangements before departure.`;
  }

  if (score >= 50) {
    return `Elevated operational exposure${locationText}. Maintain situational awareness, confirm transport arrangements and monitor disruption before key movements.`;
  }

  if (score >= 30) {
    return `Guarded operating conditions${locationText}. Normal business travel remains possible, but local disruption should be checked before departure.`;
  }

  return `Lower current operational exposure${locationText}. Continue routine precautions and monitor the live briefing for changes.`;
}

function renderIncidents() {
  const selectedCity =
    document.getElementById(
      "incident-city-filter"
    ).value;

  const selectedType =
    document.getElementById(
      "incident-type-filter"
    ).value.toLowerCase();

  const incidents =
    appData.incidents.filter(
      incident => {
        const cityMatches =
          selectedCity === "all" ||
          incident.location === selectedCity;

        const typeMatches =
          selectedType === "all" ||
          incident.type.toLowerCase() ===
            selectedType;

        return cityMatches && typeMatches;
      }
    );

  const list =
    document.getElementById("incident-list");

  if (!incidents.length) {
    list.innerHTML =
      `<div class="empty-state">
        No incidents match the selected filters.
      </div>`;

    return;
  }

  list.innerHTML =
    incidents.map(
      incident => `
        <article class="incident-card">
          <div class="panel-heading">
            <span class="severity-badge ${severityClass(incident.severity)}">
              ${escapeHtml(incident.severity)}
            </span>

            <span class="news-tag">
              ${escapeHtml(incident.status)}
            </span>
          </div>

          <h3>${escapeHtml(incident.title)}</h3>

          <div class="incident-meta">
            <span>${escapeHtml(incident.location)}</span>
            <span>${escapeHtml(incident.type)}</span>
            <span>${escapeHtml(incident.time_window)}</span>
          </div>

          <p>
            ${escapeHtml(incident.summary)}
          </p>

          <p>
            <strong>Suggested action:</strong>
            ${escapeHtml(incident.action)}
          </p>

          <div class="incident-meta">
            <span>
              Confidence:
              ${escapeHtml(incident.confidence)}
            </span>

            <span>
              Source:
              ${escapeHtml(incident.source)}
            </span>
          </div>
        </article>
      `
    ).join("");
}

function renderNews() {
  const location =
    document.getElementById(
      "news-location-selector"
    ).value;

  const filteredByLocation =
    appData.news.filter(
      story =>
        location === "national"
          ? story.location === "National"
          : story.city_id === location
    );

  const categories = [
    "All",
    ...new Set(
      filteredByLocation.map(
        story => story.category
      )
    )
  ];

  const categoryTabs =
    document.getElementById(
      "news-category-tabs"
    );

  categoryTabs.innerHTML =
    categories.map(
      category => `
        <button
          class="category-button ${
            category === currentNewsCategory
              ? "active"
              : ""
          }"
          data-category="${escapeHtml(category)}"
          type="button"
        >
          ${escapeHtml(category)}
        </button>
      `
    ).join("");

  categoryTabs
    .querySelectorAll("button")
    .forEach(button => {
      button.addEventListener(
        "click",
        () => {
          currentNewsCategory =
            button.dataset.category;

          renderNews();
        }
      );
    });

  const finalStories =
    filteredByLocation.filter(
      story =>
        currentNewsCategory === "All" ||
        story.category === currentNewsCategory
    );

  const newsList =
    document.getElementById("news-list");

  if (!finalStories.length) {
    newsList.innerHTML =
      `<div class="empty-state">
        No demo stories are available for this selection.
      </div>`;

    return;
  }

  newsList.innerHTML =
    finalStories.map(
      story => `
        <article class="news-card">
          <div class="panel-heading">
            <span class="news-tag">
              ${escapeHtml(story.category)}
            </span>

            <span class="severity-badge ${severityClass(story.relevance)}">
              ${escapeHtml(story.relevance)}
              relevance
            </span>
          </div>

          <h3>
            ${escapeHtml(story.title)}
          </h3>

          <div class="news-meta">
            <span>
              ${escapeHtml(story.location)}
            </span>

            <span>
              Published:
              ${escapeHtml(story.published)}
            </span>

            <span>
              Event date:
              ${escapeHtml(story.event_date)}
            </span>
          </div>

          <p>
            ${escapeHtml(story.summary)}
          </p>

          <div class="news-meta">
            <span>
              Source:
              ${escapeHtml(story.source)}
            </span>

            <span>
              Confidence:
              ${escapeHtml(story.confidence)}
            </span>
          </div>
        </article>
      `
    ).join("");
}

function renderConversationBrief() {
  const grid =
    document.getElementById(
      "conversation-grid"
    );

  grid.innerHTML =
    appData.conversation_brief.map(
      item => `
        <article class="conversation-card">
          <span class="news-tag">
            ${escapeHtml(item.topic)}
          </span>

          <h3>
            ${escapeHtml(item.heading)}
          </h3>

          <p>
            ${escapeHtml(item.context)}
          </p>

          <div class="sentence-starter">
            <strong>
              Neutral sentence starter
            </strong>
            <br>
            “${escapeHtml(item.starter)}”
          </div>

          <div class="avoid-box">
            <strong>
              Avoid assuming
            </strong>
            <br>
            ${escapeHtml(item.avoid)}
          </div>
        </article>
      `
    ).join("");
}

function scoreToRadius(score) {
  return Math.max(
    8,
    Math.min(
      19,
      score / 4.8
    )
  );
}

function riskColour(score) {
  if (score >= 85) {
    return "#721c24";
  }

  if (score >= 70) {
    return "#c92a2a";
  }

  if (score >= 50) {
    return "#e87524";
  }

  if (score >= 30) {
    return "#e0a800";
  }

  return "#2e8b57";
}

function riskClass(score) {
  if (score >= 85) {
    return "risk-severe";
  }

  if (score >= 70) {
    return "risk-high";
  }

  if (score >= 50) {
    return "risk-elevated";
  }

  if (score >= 30) {
    return "risk-guarded";
  }

  return "risk-low";
}

function severityClass(value) {
  const normalised =
    String(value).toLowerCase();

  if (
    ["high", "severe"].includes(normalised)
  ) {
    return "severity-high";
  }

  if (
    [
      "medium",
      "moderate",
      "elevated"
    ].includes(normalised)
  ) {
    return "severity-medium";
  }

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