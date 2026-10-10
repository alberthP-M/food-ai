const API_BASE = window.FOOD_AI_API || "http://localhost:8000";

const queryInput = document.querySelector("#query");
const recommendButton = document.querySelector("#recommend-button");
const voiceButton = document.querySelector("#voice-button");
const channelSelect = document.querySelector("#channel");
const resultsGrid = document.querySelector("#results-grid");
const resultsTitle = document.querySelector("#results-title");
const resultMessage = document.querySelector("#result-message");
const safetyNotice = document.querySelector("#safety-notice");
const errorBox = document.querySelector("#error-box");
const loading = document.querySelector("#loading");
const serviceStatus = document.querySelector("#service-status");
const constraintsCard = document.querySelector("#constraints-card");
const constraintList = document.querySelector("#constraint-list");

const labels = {
  vegan: "vegano",
  vegetarian: "vegetariano",
  gluten_free: "sin gluten",
  dairy_free: "sin lácteos",
  low_calorie: "bajo en calorías",
  high_protein: "alto en proteína",
  peanuts: "sin maní",
  nuts: "sin frutos secos",
  milk: "sin leche",
  gluten: "sin gluten",
  egg: "sin huevo",
  soy: "sin soya",
  fish: "sin pescado",
  shellfish: "sin mariscos",
};

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

function showConstraints(constraints) {
  const values = [];
  for (const key of ["diets", "excluded_allergens"]) {
    for (const value of constraints[key] || []) values.push(labels[value] || value);
  }
  if (constraints.protein) values.push(`proteína: ${constraints.protein}`);
  if (constraints.spice_level) values.push(`picante: ${constraints.spice_level}`);
  if (constraints.max_price !== null && constraints.max_price !== undefined) values.push(`hasta Bs ${constraints.max_price}`);
  if (constraints.min_price !== null && constraints.min_price !== undefined) values.push(`desde Bs ${constraints.min_price}`);

  constraintList.innerHTML = values.length
    ? values.map((value) => `<span class="constraint-chip">${escapeHtml(value)}</span>`).join("")
    : "<span class=\"constraint-chip\">búsqueda semántica general</span>";
  constraintsCard.classList.remove("hidden");
}

function renderResults(items) {
  resultsGrid.innerHTML = items.map((item) => {
    const tags = [...(item.diet_tags || []).slice(0, 3), ...(item.allergens || []).map((item) => `contiene ${item}`)].slice(0, 5);
    return `
      <article class="dish-card">
        <p class="dish-category">${escapeHtml(item.category)}</p>
        <h3>${escapeHtml(item.name)}</h3>
        <p class="dish-description">${escapeHtml(item.description)}</p>
        <div class="dish-meta"><span>Bs ${Number(item.price).toFixed(0)}</span><span>${item.prep_minutes} min</span></div>
        <div class="tag-row">${tags.map((tag) => `<span class="tag">${escapeHtml(labels[tag] || tag)}</span>`).join("")}</div>
        <p class="reason">${escapeHtml(item.explanation)}</p>
        <button class="cart-button" data-dish-id="${escapeHtml(item.id)}" type="button">Agregar al carrito</button>
      </article>`;
  }).join("");
  document.querySelectorAll(".cart-button").forEach((button) => {
    button.addEventListener("click", () => {
      button.textContent = "Agregado ✓";
      button.disabled = true;
      button.style.opacity = "0.7";
    });
  });
}

async function loadHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/ready`);
    if (!response.ok) throw new Error("Backend no disponible");
    const data = await response.json();
    serviceStatus.classList.remove("offline");
    serviceStatus.textContent = `Modelo listo · ${data.menu_items} platos`;
  } catch (error) {
    serviceStatus.textContent = "Preparando modelo…";
    serviceStatus.classList.add("offline");
    window.setTimeout(loadHealth, 4000);
  }
}

async function recommend() {
  const query = queryInput.value.trim();
  clearError();
  if (query.length < 3) {
    showError("Escribe una solicitud de al menos tres caracteres.");
    return;
  }
  loading.classList.remove("hidden");
  recommendButton.disabled = true;
  resultsTitle.textContent = "Analizando tu solicitud…";
  resultMessage.classList.add("hidden");
  try {
    const response = await fetch(`${API_BASE}/api/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 3, channel: channelSelect.value }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "No se pudo procesar la solicitud.");
    showConstraints(data.parsed_constraints);
    renderResults(data.recommendations);
    safetyNotice.textContent = data.safety_notice || "Confirma los ingredientes con el personal antes de ordenar.";
    safetyNotice.classList.remove("hidden");
    resultsTitle.textContent = data.recommendations.length ? "Recomendaciones para ti" : "Sin coincidencias seguras";
    if (data.message) {
      resultMessage.textContent = data.message;
      resultMessage.classList.remove("hidden");
    }
  } catch (error) {
    resultsTitle.textContent = "No se pudo completar la búsqueda";
    showError(error.message);
  } finally {
    loading.classList.add("hidden");
    recommendButton.disabled = false;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character]));
}

recommendButton.addEventListener("click", recommend);
queryInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") recommend();
});
document.querySelectorAll("[data-query]").forEach((button) => {
  button.addEventListener("click", () => {
    queryInput.value = button.dataset.query;
    queryInput.focus();
  });
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.lang = "es-BO";
  recognition.interimResults = false;
  voiceButton.addEventListener("click", () => {
    voiceButton.classList.add("listening");
    voiceButton.querySelector("span:last-child").textContent = "Escuchando…";
    recognition.start();
  });
  recognition.addEventListener("result", (event) => {
    queryInput.value = event.results[0][0].transcript;
  });
  recognition.addEventListener("end", () => {
    voiceButton.classList.remove("listening");
    voiceButton.querySelector("span:last-child").textContent = "Hablar";
  });
  recognition.addEventListener("error", () => {
    voiceButton.classList.remove("listening");
    voiceButton.querySelector("span:last-child").textContent = "Hablar";
    showError("No se pudo reconocer la voz. También puedes escribir tu solicitud.");
  });
} else {
  voiceButton.disabled = true;
  voiceButton.title = "Este navegador no admite entrada por voz";
  document.querySelector("#voice-hint").textContent = "Este navegador no admite Web Speech API; usa el campo de texto.";
}

loadHealth();
