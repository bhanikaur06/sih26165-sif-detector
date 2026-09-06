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
