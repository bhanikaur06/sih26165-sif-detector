const API_BASE = "http://127.0.0.1:5001";

async function loadDashboardSummary() {
  const response = await fetch(`${API_BASE}/api/dashboard/summary`);
  return response.json();
}

function densityTier(density) {
  if (density > 0.20) return "high";
  if (density >= 0.10) return "mid";
  return "low";
}

function renderDensityChart(groups) {
  const container = document.getElementById("density-chart-body");
  const rows = groups.slice().sort((a, b) => b.density - a.density);
  const peak = rows.length ? rows[0].density : 1;

  container.innerHTML = "";

  rows.forEach(item => {
    const li = document.createElement("li");
    li.className = "bar-list__row";

    const label = document.createElement("span");
    label.className = "bar-list__label";
    label.textContent = item.group;

    const value = document.createElement("span");
    value.className = "bar-list__value";
    value.textContent = `${(item.density * 100).toFixed(1)}%`;

    const track = document.createElement("span");
    track.className = "bar-list__track";
    const bar = document.createElement("span");
    bar.className = `bar-list__bar bar-list__bar--${densityTier(item.density)}`;
    bar.style.width = `${(item.density / peak) * 100}%`;
    track.appendChild(bar);

    li.append(label, value, track);
    container.appendChild(li);
  });
}

function renderRuleChart(rules) {
  const container = document.getElementById("rule-chart-body");
  const rows = rules.slice().sort((a, b) => b.count - a.count);
  const peak = rows.length ? rows[0].count : 1;

  container.innerHTML = "";

  rows.forEach(item => {
    const li = document.createElement("li");
    li.className = "bar-list__row";

    const label = document.createElement("span");
    label.className = "bar-list__label";
    label.textContent = item.life_saving_rule;

    const value = document.createElement("span");
    value.className = "bar-list__value";
    value.textContent = item.count;

    const track = document.createElement("span");
    track.className = "bar-list__track";
    const bar = document.createElement("span");
    bar.className = "bar-list__bar";
    bar.style.width = `${(item.count / peak) * 100}%`;
    track.appendChild(bar);

    li.append(label, value, track);
    container.appendChild(li);
  });
}

function renderDetailTable(groups) {
  const tbody = document.getElementById("detail-table-body");
  tbody.innerHTML = "";

  groups.forEach(item => {
    const tier = densityTier(item.density);
    const tr = document.createElement("tr");

    const group = document.createElement("td");
    group.textContent = item.group;

    const type = document.createElement("td");
    type.textContent = item.group_type;

    const totalReports = document.createElement("td");
    totalReports.textContent = item.total_reports;

    const sifCount = document.createElement("td");
    sifCount.textContent = item.sif_count;

    const density = document.createElement("td");
    const densityWrap = document.createElement("span");
    densityWrap.className = `detail-table__density detail-table__value--${tier}`;
    const dot = document.createElement("i");
    dot.className = `detail-table__dot detail-table__dot--${tier}`;
    const densityText = document.createElement("span");
    densityText.textContent = `${(item.density * 100).toFixed(1)}%`;
    densityWrap.append(dot, densityText);
    density.appendChild(densityWrap);

    tr.append(group, type, totalReports, sifCount, density);
    tbody.appendChild(tr);
  });
}

function renderStatCards(stats) {
  document.getElementById("stat-total-reports").textContent = stats.total_reports;
  document.getElementById("stat-sif-count").textContent = stats.sif_count;
  document.getElementById("stat-density").textContent = `${(stats.density * 100).toFixed(1)}%`;
}

let dashboardData = null;

function filterGroupsBySeverity(groups, tier) {
  if (tier === "all") return groups;
  return groups.filter(item => densityTier(item.density) === tier);
}

function applySeverityFilter() {
  const tier = document.getElementById("severity-filter").value;
  const filtered = filterGroupsBySeverity(dashboardData.precursor_density_by_group, tier);
  renderDensityChart(filtered);
  renderDetailTable(filtered);
}

document.getElementById("severity-filter").addEventListener("change", applySeverityFilter);

loadDashboardSummary().then(data => {
  dashboardData = data;
  renderStatCards(data.summary_stats);
  renderRuleChart(data.rule_breakdown);
  applySeverityFilter();
});

async function classifyNarrative(narrative) {
  const response = await fetch(`${API_BASE}/api/classify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ narrative }),
  });
  if (!response.ok) {
    throw new Error(`server responded ${response.status}`);
  }
  return response.json();
}

function renderClassification(result) {
  const labelEl = document.getElementById("try-live-label");
  const probabilityEl = document.getElementById("try-live-probability");
  const ruleEl = document.getElementById("try-live-rule");

  const flagged = result.sif_label === 1;
  labelEl.textContent = flagged ? "SIF Precursor" : "Not flagged";
  labelEl.className = `try-live__label try-live__label--${flagged ? "flagged" : "clear"}`;
  probabilityEl.textContent = `${(result.sif_probability * 100).toFixed(1)}%`;

  if (result.life_saving_rule) {
    ruleEl.textContent = `Life-Saving Rule: ${result.life_saving_rule}`;
    ruleEl.hidden = false;
  } else {
    ruleEl.textContent = "";
    ruleEl.hidden = true;
  }

  document.getElementById("try-live-result").hidden = false;
}

async function handleClassifySubmit() {
  const input = document.getElementById("try-live-input");
  const submit = document.getElementById("try-live-submit");
  const errorEl = document.getElementById("try-live-error");
  const narrative = input.value.trim();

  errorEl.hidden = true;

  if (!narrative) {
    errorEl.textContent = "Enter a narrative to classify.";
    errorEl.hidden = false;
    return;
  }

  const restingLabel = submit.textContent;
  submit.disabled = true;
  submit.textContent = "Scoring…";

  try {
    const result = await classifyNarrative(narrative);
    renderClassification(result);
  } catch (err) {
    document.getElementById("try-live-result").hidden = true;
    errorEl.textContent = `Could not reach the classifier (${err.message}). Is the backend running on ${API_BASE}?`;
    errorEl.hidden = false;
  } finally {
    submit.disabled = false;
    submit.textContent = restingLabel;
  }
}

document.getElementById("try-live-submit").addEventListener("click", handleClassifySubmit);
