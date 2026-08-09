const DATA_URL = "data/briefing.json";

let appData = null;
let map = null;
let chart = null;
let cityMarkers = [];


document.addEventListener(
  "DOMContentLoaded",
  initialiseApp
);


async function initialiseApp() {
  try {
    const response = await fetch(
      DATA_URL,
      {
        cache: "no-store"
      }
    );

    if (!response.ok) {
      throw new Error(
        `Could not load ${DATA_URL}`
      );
    }

    appData = await response.json();

    renderNationalOverview();
    renderMetrics();
    renderTimeline();

    initialiseMap();
    populateSelectors();

    renderTravelAdvice();
    renderIncidents();
    renderConversationBrief();

  } catch (error) {
    console.error(error);

    document.body.insertAdjacentHTML(
      "afterbegin",
      `
        <div
          class="data-warning"
          style="margin:12px"
        >
          The app could not load its data file.
          Run it through a local web server rather
          than opening index.html directly.
        </div>
      `
    );
  }
}


/* =========================================================
   NATIONAL OVERVIEW
   ========================================================= */


function renderNationalOverview() {
  const national = appData.national;

  document.getElementById(
    "national-risk-score"
  ).textContent = national.score;

  document.getElementById(
    "national-summary"
  ).textContent = national.summary;

  const badge = document.getElementById(
    "national-risk-badge"
  );

  badge.textContent = national.level;

  badge.className =
    `risk-badge ${riskClass(national.score)}`;


  const direction = document.getElementById(
    "risk-direction"
  );

  const movement =
    national.seven_day_change;


  if (movement > 0) {
    direction.textContent =
      `▲ ${movement}`;

    direction.className =
      "trend trend-up";

  } else if (movement < 0) {
    direction.textContent =
      `▼ ${Math.abs(movement)}`;

    direction.className =
      "trend trend-down";

  } else {
    direction.textContent =
      "● Stable";

    direction.className =
      "trend trend-flat";
  }


  const breakdown =
    document.getElementById(
      "risk-breakdown"
    );

  breakdown.innerHTML =
    national.components.map(
      component => `
        <div class="breakdown-row">

          <span>
            ${escapeHtml(component.name)}
          </span>

          <div class="breakdown-bar">

            <div
              class="breakdown-fill"
              style="width:${component.score}%"
            ></div>

          </div>

          <strong>
            ${component.score}
          </strong>

        </div>
      `
    ).join("");
}


/* =========================================================
   KEY METRICS
   ========================================================= */


function renderMetrics() {
  const activeIncidents =
    Array.isArray(appData.incidents)
      ? appData.incidents.filter(
          item =>
            item.status === "Active" ||
            item.status === "Upcoming"
        )
      : [];


  document.getElementById(
    "active-disruptions"
  ).textContent =
    activeIncidents.length;


  document.getElementById(
    "city-count"
  ).textContent =
    appData.cities.length;


  const highest =
    [...appData.cities]
      .sort(
        (a, b) =>
          b.score - a.score
      )[0];


  if (highest) {
    document.getElementById(
      "highest-risk-city"
    ).textContent =
      highest.name;

    document.getElementById(
      "highest-risk-city-score"
    ).textContent =
      `${highest.level} — ${highest.score}/100`;
  }


  document.getElementById(
    "generated-time"
  ).textContent =
    appData.metadata.generated_display ||
    appData.metadata.generated_at ||
    "—";
}


/* =========================================================
   RISK TIMELINE
   ========================================================= */


function renderTimeline() {
  const context =
    document.getElementById(
      "riskChart"
    );


  chart = new Chart(
    context,
    {
      type: "line",

      data: {
        labels:
          appData.timeline.map(
            point => point.date
          ),

        datasets: [
          {
            label:
              "National risk score",

            data:
              appData.timeline.map(
                point => point.score
              ),

            borderWidth: 3,

            tension: 0.3,

            pointRadius: 4,

            pointHoverRadius: 7,

            fill: true
          }
        ]
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

            ticks: {
              stepSize: 20
            }
          }
        },

        plugins: {
          legend: {
            display: false
          },

          tooltip: {
            callbacks: {
              afterLabel(context) {
                return (
                  appData.timeline[
                    context.dataIndex
                  ].explanation
                );
              }
            }
          }
        },


        onClick(
          event,
          elements
        ) {
          if (!elements.length) {
            return;
          }

          const selected =
            appData.timeline[
              elements[0].index
            ];

          document.getElementById(
            "timeline-explanation"
          ).innerHTML =
            `
              <strong>
                ${escapeHtml(selected.date)}
                —
                ${selected.score}/100:
              </strong>

              ${escapeHtml(
                selected.explanation
              )}
            `;
        }
      }
    }
  );
}


/* =========================================================
   OPERATIONAL RISK MAP
   ========================================================= */


function initialiseMap() {
  const southAfricaBounds =
    L.latLngBounds(
      [-35.4, 16.0],
      [-22.0, 33.4]
    );


  map = L.map(
    "risk-map",
    {
      minZoom: 5,

      maxZoom: 14,

      maxBounds:
        southAfricaBounds.pad(0.18),

      maxBoundsViscosity: 0.92,

      zoomControl: true,

      attributionControl: true
    }
  );


  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    {
      attribution:
        '&copy; OpenStreetMap contributors &copy; CARTO',

      subdomains: "abcd",

      maxZoom: 20
    }
  ).addTo(map);


  map.fitBounds(
    southAfricaBounds,
    {
      padding: [26, 26]
    }
  );


  cityMarkers =
    appData.cities.map(
      city => {

        const colour =
          riskColour(city.score);


        const icon =
          L.divIcon(
            {
              className:
                "intelligence-node-wrapper",

              html: `
                <button
                  class="
                    intelligence-node
                    ${riskClass(city.score)}
                  "
                  type="button"
                  aria-label="
                    ${escapeHtml(city.name)}:
                    ${escapeHtml(city.level)} risk,
                    ${city.score} out of 100
                  "
                  style="
                    --node-risk-colour:${colour}
                  "
                >

                  <span
                    class="intelligence-node-ring"
                  ></span>

                  <span
                    class="intelligence-node-core"
                  >
                    <strong>
                      ${city.score}
                    </strong>
                  </span>

                  <span
                    class="intelligence-node-label"
                  >
                    ${escapeHtml(city.name)}
                  </span>

                </button>
              `,

              iconSize: [138, 52],

              iconAnchor: [26, 26]
            }
          );


        const marker =
          L.marker(
            [
              city.latitude,
              city.longitude
            ],
            {
              icon,

              keyboard: true,

              riseOnHover: true,

              title:
                `${city.name}: ${city.level} risk`
            }
          )
          .addTo(map);


        marker.on(
          "click",
          () =>
            selectMapCity(
              city,
              true
            )
        );


        marker.bindTooltip(
          `
            <strong>
              ${escapeHtml(city.name)}
            </strong>

            <br>

            ${escapeHtml(city.level)}
            —
            ${city.score}/100
          `,
          {
            direction: "top",

            offset: [0, -20],

            className:
              "intelligence-tooltip",

            opacity: 1
          }
        );


        return {
          city,
          marker
        };
      }
    );


  const resetButton =
    document.getElementById(
      "map-reset-button"
    );


  if (resetButton) {
    resetButton.addEventListener(
      "click",
      resetMapToNational
    );
  }


  updateSelectedArea(null);


  setTimeout(
    () => {
      map.invalidateSize();
    },
    150
  );
}


function selectMapCity(
  city,
  moveMap = true
) {
  if (!city) {
    return;
  }


  if (moveMap) {
    map.flyTo(
      [
        city.latitude,
        city.longitude
      ],

      Math.min(
        city.default_zoom || 9,
        10
      ),

      {
        duration: 0.85
      }
    );
  }


  updateSelectedArea(city);

  updateSelectedMarker(
    city.id
  );


  const selector =
    document.getElementById(
      "city-selector"
    );


  if (selector) {
    selector.value =
      city.id;
  }
}


function updateSelectedMarker(
  selectedCityId
) {
  cityMarkers.forEach(
    ({
      city,
      marker
    }) => {

      const element =
        marker.getElement();


      if (!element) {
        return;
      }


      const node =
        element.querySelector(
          ".intelligence-node"
        );


      if (!node) {
        return;
      }


      node.classList.toggle(
        "selected",
        city.id === selectedCityId
      );
    }
  );
}


function resetMapToNational() {
  const southAfricaBounds =
    L.latLngBounds(
      [-35.4, 16.0],
      [-22.0, 33.4]
    );


  map.fitBounds(
    southAfricaBounds,
    {
      padding: [26, 26]
    }
  );


  updateSelectedMarker(null);

  updateSelectedArea(null);


  const selector =
    document.getElementById(
      "city-selector"
    );


  if (selector) {
    selector.value =
      "national";
  }
}


function updateSelectedArea(
  city
) {
  const name =
    document.getElementById(
      "selected-area-name"
    );

  const risk =
    document.getElementById(
      "selected-area-risk"
    );

  const score =
    document.getElementById(
      "selected-area-score"
    );

  const summary =
    document.getElementById(
      "selected-area-summary"
    );

  const action =
    document.getElementById(
      "selected-area-action"
    );

  const status =
    document.getElementById(
      "selected-area-status"
    );


  const monitoredCities =
    document.getElementById(
      "map-monitored-cities"
    );

  const activeDisruptions =
    document.getElementById(
      "map-active-disruptions"
    );

  const generatedTime =
    document.getElementById(
      "map-generated-time"
    );


  if (monitoredCities) {
    monitoredCities.textContent =
      appData.cities.length;
  }


  if (activeDisruptions) {
    activeDisruptions.textContent =
      Array.isArray(appData.incidents)
        ? appData.incidents.length
        : 0;
  }


  if (generatedTime) {
    generatedTime.textContent =
      appData.metadata.generated_display ||
      appData.metadata.generated_at ||
      "—";
  }


  if (!city) {
    name.textContent =
      "South Africa";

    score.textContent =
      appData.national.score;

    risk.textContent =
      `${appData.national.level} national risk`;

    risk.className =
      `selected-risk ${riskClass(
        appData.national.score
      )}`;

    summary.textContent =
      appData.national.summary;

    action.textContent =
      buildBusinessImplication(
        appData.national.score,
        null
      );

    status.textContent =
      "National";

    status.className =
      "map-status-chip";

    return;
  }


  name.textContent =
    city.name;

  score.textContent =
    city.score;

  risk.textContent =
    `${city.level} risk`;

  risk.className =
    `selected-risk ${riskClass(
      city.score
    )}`;

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
    `map-status-chip ${riskClass(
      city.score
    )}`;
}


function buildBusinessImplication(
  score,
  cityName
) {
  const locationText =
    cityName
      ? ` for travel in ${cityName}`
      : " for travel across South Africa";


  if (score >= 85) {
    return (
      `Severe operational exposure${locationText}. ` +
      "Review whether travel is essential, obtain current " +
      "security advice and maintain contingency arrangements."
    );
  }


  if (score >= 70) {
    return (
      `High operational exposure${locationText}. ` +
      "Review movement plans, allow additional journey time " +
      "and confirm local security and transport arrangements " +
      "before departure."
    );
  }


  if (score >= 50) {
    return (
      `Elevated operational exposure${locationText}. ` +
      "Maintain situational awareness, confirm transport " +
      "arrangements and monitor disruption before key movements."
    );
  }


  if (score >= 30) {
    return (
      `Guarded operating conditions${locationText}. ` +
      "Normal business travel remains possible, but local " +
      "disruption should be checked before departure."
    );
  }


  return (
    `Lower current operational exposure${locationText}. ` +
    "Continue routine precautions and monitor the live " +
    "briefing for changes."
  );
}


/* =========================================================
   SELECTORS
   ========================================================= */


function populateSelectors() {
  const citySelector =
    document.getElementById(
      "city-selector"
    );


  const incidentFilter =
    document.getElementById(
      "incident-city-filter"
    );


  appData.cities.forEach(
    city => {

      if (citySelector) {
        citySelector.insertAdjacentHTML(
          "beforeend",
          `
            <option
              value="${escapeHtml(city.id)}"
            >
              ${escapeHtml(city.name)}
            </option>
          `
        );
      }


      if (incidentFilter) {
        incidentFilter.insertAdjacentHTML(
          "beforeend",
          `
            <option
              value="${escapeHtml(city.name)}"
            >
              ${escapeHtml(city.name)}
            </option>
          `
        );
      }

    }
  );


  if (citySelector) {
    citySelector.addEventListener(
      "change",
      handleCitySelection
    );
  }


  if (incidentFilter) {
    incidentFilter.addEventListener(
      "change",
      renderIncidents
    );
  }


  const typeFilter =
    document.getElementById(
      "incident-type-filter"
    );


  if (typeFilter) {
    typeFilter.addEventListener(
      "change",
      renderIncidents
    );
  }
}


function handleCitySelection(
  event
) {
  if (
    event.target.value ===
    "national"
  ) {
    resetMapToNational();
    return;
  }


  const city =
    appData.cities.find(
      item =>
        item.id ===
        event.target.value
    );


  if (!city) {
    return;
  }


  selectMapCity(
    city,
    true
  );
}


/* =========================================================
   UK GOVERNMENT TRAVEL ADVICE
   ========================================================= */


function renderTravelAdvice() {
  const advice =
    appData.travel_advice || {};


  const title =
    document.getElementById(
      "travel-advice-title"
    );

  const status =
    document.getElementById(
      "travel-advice-status"
    );

  const summary =
    document.getElementById(
      "travel-advice-summary"
    );

  const updated =
    document.getElementById(
      "travel-advice-updated"
    );

  const checked =
    document.getElementById(
      "travel-advice-checked"
    );

  const confidence =
    document.getElementById(
      "travel-advice-confidence"
    );

  const link =
    document.getElementById(
      "travel-advice-link"
    );


  if (!title) {
    return;
  }


  title.textContent =
    advice.section ||
    "South Africa travel advice";


  status.textContent =
    advice.available === false
      ? "Check GOV.UK"
      : (
          advice.status ||
          "Official source"
        );


  summary.textContent =
    advice.summary ||
    (
      "Current official UK Government travel advice " +
      "is available through GOV.UK."
    );


  updated.textContent =
    advice.last_updated ||
    "Not stated";


  checked.textContent =
    formatDisplayDate(
      advice.last_checked
    );


  confidence.textContent =
    advice.confidence ||
    "Official source";


  if (advice.url) {
    link.href =
      advice.url;
  }
}


/* =========================================================
   ACTIVE OPERATIONAL NOTICES
   ========================================================= */


function renderIncidents() {
  const list =
    document.getElementById(
      "incident-list"
    );


  if (!list) {
    return;
  }


  const selectedCity =
    document.getElementById(
      "incident-city-filter"
    )?.value || "all";


  const selectedType =
    document.getElementById(
      "incident-type-filter"
    )?.value.toLowerCase() ||
    "all";


  const incidents =
    Array.isArray(appData.incidents)
      ? appData.incidents
      : [];


  const filtered =
    incidents.filter(
      incident => {

        const cityMatches =
          selectedCity === "all" ||
          incident.location ===
            selectedCity;


        const incidentType =
          String(
            incident.type || ""
          ).toLowerCase();


        const typeMatches =
          selectedType === "all" ||
          incidentType ===
            selectedType;


        return (
          cityMatches &&
          typeMatches
        );
      }
    );


  if (!filtered.length) {
    list.innerHTML =
      `
        <div
          class="empty-state operational-empty-state"
        >

          <span
            class="empty-state-icon"
            aria-hidden="true"
          >
            ✓
          </span>

          <strong>
            No significant operational
            disruptions currently identified
          </strong>

          <p>
            No current or imminent road closures,
            demonstrations, major sporting fixtures
            or music events match this selection.
          </p>

        </div>
      `;

    return;
  }


  list.innerHTML =
    filtered.map(
      incident => {

        const type =
          incident.type ||
          "Operational notice";


        return `
          <article
            class="
              operational-notice-card
              ${noticeTypeClass(type)}
            "
          >

            <div
              class="operational-notice-header"
            >

              <div
                class="notice-identity"
              >

                <span
                  class="
                    notice-icon
                    ${noticeTypeClass(type)}
                  "
                  aria-hidden="true"
                >
                  ${noticeIcon(type)}
                </span>


                <div>

                  <span
                    class="
                      notice-category
                      ${noticeTypeClass(type)}
                    "
                  >
                    ${escapeHtml(type)}
                  </span>

                  <span
                    class="notice-location"
                  >
                    ${escapeHtml(
                      incident.location ||
                      "South Africa"
                    )}
                  </span>

                </div>

              </div>


              <span
                class="
                  notice-status
                  ${statusClass(
                    incident.status
                  )}
                "
              >
                ${escapeHtml(
                  incident.status ||
                  "Current"
                )}
              </span>

            </div>


            <h3>
              ${escapeHtml(
                incident.title ||
                "Operational notice"
              )}
            </h3>


            <div
              class="notice-time-row"
            >

              <span>
                ${escapeHtml(
                  incident.time_window ||
                  "Current"
                )}
              </span>

              <span
                class="
                  severity-badge
                  ${severityClass(
                    incident.severity
                  )}
                "
              >
                ${escapeHtml(
                  incident.severity ||
                  "Low"
                )}
                impact
              </span>

            </div>


            <div
              class="notice-intelligence"
            >

              <div>

                <span
                  class="notice-detail-label"
                >
                  Operational impact
                </span>

                <p>
                  ${escapeHtml(
                    incident.summary ||
                    "No additional operational detail available."
                  )}
                </p>

              </div>


              <div
                class="notice-action-box"
              >

                <span
                  class="notice-detail-label"
                >
                  Recommended action
                </span>

                <p>
                  ${escapeHtml(
                    incident.action ||
                    "Check local conditions before travel."
                  )}
                </p>

              </div>

            </div>


            <div
              class="notice-footer"
            >

              <div>

                <span>
                  Source
                </span>

                <strong>
                  ${escapeHtml(
                    incident.source ||
                    "Reported source"
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Confidence
                </span>

                <strong>
                  ${escapeHtml(
                    incident.confidence ||
                    "Reported"
                  )}
                </strong>

              </div>


              ${
                incident.url
                  ? `
                    <a
                      href="${escapeHtml(
                        incident.url
                      )}"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Source ↗
                    </a>
                  `
                  : ""
              }

            </div>

          </article>
        `;
      }
    ).join("");
}


/* =========================================================
   CONVERSATION BRIEF
   ========================================================= */


function renderConversationBrief() {
  const grid =
    document.getElementById(
      "conversation-grid"
    );


  if (!grid) {
    return;
  }


  const items =
    Array.isArray(
      appData.conversation_brief
    )
      ? appData.conversation_brief
      : [];


  if (!items.length) {
    grid.innerHTML =
      `
        <div class="empty-state">
          No conversation guidance is
          available in the current briefing.
        </div>
      `;

    return;
  }


  grid.innerHTML =
    items.map(
      item => `
        <article
          class="conversation-card"
        >

          <span class="news-tag">
            ${escapeHtml(item.topic)}
          </span>

          <h3>
            ${escapeHtml(item.heading)}
          </h3>

          <p>
            ${escapeHtml(item.context)}
          </p>


          <div
            class="sentence-starter"
          >

            <strong>
              Neutral sentence starter
            </strong>

            <br>

            “${escapeHtml(item.starter)}”

          </div>


          <div
            class="avoid-box"
          >

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


/* =========================================================
   NOTICE HELPERS
   ========================================================= */


function noticeTypeClass(
  type
) {
  const normalised =
    String(type)
      .toLowerCase();


  if (
    normalised.includes(
      "road"
    )
  ) {
    return "notice-road";
  }


  if (
    normalised.includes(
      "demonstration"
    ) ||
    normalised.includes(
      "protest"
    )
  ) {
    return "notice-demonstration";
  }


  if (
    normalised.includes(
      "sport"
    )
  ) {
    return "notice-sport";
  }


  if (
    normalised.includes(
      "music"
    )
  ) {
    return "notice-music";
  }


  return "notice-general";
}


function noticeIcon(
  type
) {
  const normalised =
    String(type)
      .toLowerCase();


  if (
    normalised.includes(
      "road"
    )
  ) {
    return "↔";
  }


  if (
    normalised.includes(
      "demonstration"
    ) ||
    normalised.includes(
      "protest"
    )
  ) {
    return "!";
  }


  if (
    normalised.includes(
      "sport"
    )
  ) {
    return "●";
  }


  if (
    normalised.includes(
      "music"
    )
  ) {
    return "♪";
  }


  return "•";
}


function statusClass(
  status
) {
  const normalised =
    String(status)
      .toLowerCase();


  if (
    normalised ===
    "active"
  ) {
    return "status-active";
  }


  if (
    normalised ===
    "upcoming"
  ) {
    return "status-upcoming";
  }


  return "status-current";
}


function formatDisplayDate(
  value
) {
  if (!value) {
    return "—";
  }


  const parsed =
    new Date(value);


  if (
    Number.isNaN(
      parsed.getTime()
    )
  ) {
    return value;
  }


  return parsed.toLocaleString(
    "en-GB",
    {
      day: "2-digit",

      month: "short",

      year: "numeric",

      hour: "2-digit",

      minute: "2-digit",

      timeZone:
        "Europe/London"
    }
  );
}


/* =========================================================
   RISK HELPERS
   ========================================================= */


function riskColour(
  score
) {
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


function riskClass(
  score
) {
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


function severityClass(
  value
) {
  const normalised =
    String(value)
      .toLowerCase();


  if (
    [
      "high",
      "severe"
    ].includes(
      normalised
    )
  ) {
    return "severity-high";
  }


  if (
    [
      "medium",
      "moderate",
      "elevated"
    ].includes(
      normalised
    )
  ) {
    return "severity-medium";
  }


  return "severity-low";
}


/* =========================================================
   SECURITY / ESCAPING
   ========================================================= */


function escapeHtml(
  value
) {
  return String(
    value ?? ""
  )
    .replaceAll(
      "&",
      "&amp;"
    )
    .replaceAll(
      "<",
      "&lt;"
    )
    .replaceAll(
      ">",
      "&gt;"
    )
    .replaceAll(
      '"',
      "&quot;"
    )
    .replaceAll(
      "'",
      "&#039;"
    );
}