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

const SVG_NS = "http://www.w3.org/2000/svg";
const DENSITY_ROW_H = 32;
const DENSITY_AXIS_H = 26;
const DENSITY_BAR_OFFSET = 21;
const RULE_PALETTE = ["#6B93C0", "#54A0A6", "#6BA576", "#A7A65C", "#CBA14C", "#C9814C", "#C46B6B", "#B074A8", "#8688A0"];

function positionTooltip(card, target, tip) {
  const cardRect = card.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  const tipWidth = tip.offsetWidth;
  const tipHeight = tip.offsetHeight;
  let left = targetRect.left - cardRect.left + targetRect.width / 2 - tipWidth / 2;
  left = Math.max(6, Math.min(left, cardRect.width - tipWidth - 6));
  let top = targetRect.top - cardRect.top - tipHeight - 8;
  if (top < 6) {
    top = targetRect.top - cardRect.top + targetRect.height + 8;
  }
  tip.style.left = `${left}px`;
  tip.style.top = `${top}px`;
  tip.classList.add("is-visible");
}

function tooltipLines(name, stat) {
  const nameEl = document.createElement("div");
  nameEl.className = "chart-tooltip__name";
  nameEl.textContent = name;
  const statEl = document.createElement("div");
  statEl.className = "chart-tooltip__stat";
  statEl.textContent = stat;
  return [nameEl, statEl];
}

function polarToCartesian(cx, cy, radius, angleDeg) {
  const a = (angleDeg - 90) * Math.PI / 180;
  return [cx + radius * Math.cos(a), cy + radius * Math.sin(a)];
}

function donutSegmentPath(cx, cy, outerR, innerR, startAngle, endAngle) {
  const [ox0, oy0] = polarToCartesian(cx, cy, outerR, startAngle);
  const [ox1, oy1] = polarToCartesian(cx, cy, outerR, endAngle);
  const [ix1, iy1] = polarToCartesian(cx, cy, innerR, endAngle);
  const [ix0, iy0] = polarToCartesian(cx, cy, innerR, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${ox0} ${oy0} A ${outerR} ${outerR} 0 ${largeArc} 1 ${ox1} ${oy1} `
    + `L ${ix1} ${iy1} A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix0} ${iy0} Z`;
}

function fullRingPath(cx, cy, outerR, innerR) {
  return `M ${cx} ${cy - outerR} A ${outerR} ${outerR} 0 1 1 ${cx - 0.01} ${cy - outerR} Z `
    + `M ${cx} ${cy - innerR} A ${innerR} ${innerR} 0 1 0 ${cx - 0.01} ${cy - innerR} Z`;
}

function renderDensityChart(groups) {
  const container = document.getElementById("density-chart-body");
  const rows = groups.slice().sort((a, b) => b.density - a.density);
  container.innerHTML = "";

  if (!rows.length) {
    const empty = document.createElement("p");
    empty.className = "svg-bar-chart__empty";
    empty.textContent = "No groups match this filter.";
    container.appendChild(empty);
    return;
  }

  const svgHeight = DENSITY_AXIS_H + rows.length * DENSITY_ROW_H;
  const gridFractions = [0.25, 0.5, 0.75, 1];

  const gridMarkup = gridFractions.map(f =>
    `<line x1="${f * 100}" y1="${DENSITY_AXIS_H - 4}" x2="${f * 100}" y2="${svgHeight}" vector-effect="non-scaling-stroke"/>`
  ).join("");

  const barMarkup = rows.map((item, i) => {
    const y = DENSITY_AXIS_H + i * DENSITY_ROW_H + DENSITY_BAR_OFFSET;
    const tier = densityTier(item.density);
    const width = (item.density * 100).toFixed(2);
    return `<rect class="svg-bar-chart__track" x="0" y="${y}" width="100" height="8"/>`
      + `<rect class="svg-bar-chart__fill svg-bar-chart__fill--${tier}" x="0" y="${y}" width="${width}" height="8"/>`;
  }).join("");

  container.insertAdjacentHTML("beforeend",
    `<svg class="svg-bar-chart__grid" viewBox="0 0 100 ${svgHeight}" preserveAspectRatio="none" aria-hidden="true">${gridMarkup}${barMarkup}</svg>`);

  const axis = document.createElement("div");
  axis.className = "svg-bar-chart__axis";
  axis.setAttribute("aria-hidden", "true");
  gridFractions.forEach(f => {
    const span = document.createElement("span");
    span.style.left = `${f * 100}%`;
    span.textContent = `${f * 100}%`;
    axis.appendChild(span);
  });
  container.appendChild(axis);

  const list = document.createElement("ul");
  list.className = "svg-bar-chart__rows";
  list.setAttribute("role", "list");

  rows.forEach(item => {
    const pct = (item.density * 100).toFixed(1);
    const li = document.createElement("li");
    li.className = "svg-bar-chart__row";
    li.tabIndex = 0;
    li.setAttribute("role", "listitem");
    li.setAttribute("aria-label",
      `${item.group}: ${pct}% density, ${item.sif_count} of ${item.total_reports} reports flagged`);
    li.dataset.group = item.group;
    li.dataset.total = item.total_reports;
    li.dataset.sif = item.sif_count;
    li.dataset.pct = pct;

    const label = document.createElement("span");
    label.className = "svg-bar-chart__label";
    label.textContent = item.group;

    const value = document.createElement("span");
    value.className = "svg-bar-chart__value";
    value.textContent = `${pct}%`;

    li.append(label, value);
    list.appendChild(li);
  });

  container.appendChild(list);

  const tip = document.getElementById("density-tooltip");
  const card = document.getElementById("density-chart");
  const hide = () => tip.classList.remove("is-visible");
  [...list.children].forEach(row => {
    const show = () => {
      tip.replaceChildren(...tooltipLines(
        row.dataset.group,
        `${row.dataset.pct}%  ·  ${row.dataset.sif} SIF / ${row.dataset.total} reports`));
      positionTooltip(card, row, tip);
    };
    row.addEventListener("mouseenter", show);
    row.addEventListener("focus", show);
    row.addEventListener("mouseleave", hide);
    row.addEventListener("blur", hide);
  });
}

function renderRuleChart(rules) {
  const container = document.getElementById("rule-chart-body");
  const rows = rules.slice().sort((a, b) => b.count - a.count);
  container.innerHTML = "";
  if (!rows.length) return;

  const total = rows.reduce((sum, item) => sum + item.count, 0);
  const cx = 120;
  const cy = 120;
  const outerR = 112;
  const innerR = 68;

  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "donut__svg");
  svg.setAttribute("viewBox", "0 0 240 240");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `Life-Saving Rule breakdown across ${rows.length} categories`);

  const segGroup = document.createElementNS(SVG_NS, "g");
  segGroup.setAttribute("class", "donut__segs");
  segGroup.setAttribute("role", "list");

  const meta = [];
  let cursor = 0;
  rows.forEach((item, i) => {
    const frac = total ? item.count / total : 0;
    const startAngle = cursor * 360;
    const endAngle = (cursor + frac) * 360;
    cursor += frac;
    const color = RULE_PALETTE[i % RULE_PALETTE.length];
    const pct = (frac * 100).toFixed(1);
    meta.push({ name: item.life_saving_rule, count: item.count, pct, color });

    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("class", "donut__seg");
    if (frac >= 0.9999) {
      path.setAttribute("d", fullRingPath(cx, cy, outerR, innerR));
      path.setAttribute("fill-rule", "evenodd");
    } else {
      path.setAttribute("d", donutSegmentPath(cx, cy, outerR, innerR, startAngle, endAngle));
    }
    path.setAttribute("fill", color);
    path.setAttribute("tabindex", "0");
    path.setAttribute("role", "listitem");
    path.setAttribute("aria-label", `${item.life_saving_rule}: ${item.count} reports, ${pct}% of tagged`);
    segGroup.appendChild(path);
  });
  svg.appendChild(segGroup);

  const totalText = document.createElementNS(SVG_NS, "text");
  totalText.setAttribute("class", "donut__total");
  totalText.setAttribute("x", "120");
  totalText.setAttribute("y", "118");
  totalText.setAttribute("text-anchor", "middle");
  totalText.textContent = String(total);

  const totalLabel = document.createElementNS(SVG_NS, "text");
  totalLabel.setAttribute("class", "donut__total-label");
  totalLabel.setAttribute("x", "120");
  totalLabel.setAttribute("y", "136");
  totalLabel.setAttribute("text-anchor", "middle");
  totalLabel.textContent = "TAGGED";
  svg.append(totalText, totalLabel);

  const legend = document.createElement("ul");
  legend.className = "donut__legend";
  meta.forEach(entry => {
    const li = document.createElement("li");
    li.className = "donut__legend-item";

    const swatch = document.createElement("i");
    swatch.className = "donut__legend-swatch";
    swatch.style.background = entry.color;

    const name = document.createElement("span");
    name.className = "donut__legend-name";
    name.textContent = entry.name;

    const count = document.createElement("span");
    count.className = "donut__legend-count";
    count.textContent = String(entry.count);

    li.append(swatch, name, count);
    legend.appendChild(li);
  });

  container.append(svg, legend);

  const segs = [...segGroup.children];
  const tip = document.getElementById("rule-tooltip");
  const card = document.getElementById("rule-chart");

  const activate = (i, target) => {
    svg.classList.add("is-hovering");
    segs.forEach((s, j) => s.classList.toggle("is-active", j === i));
    tip.replaceChildren(...tooltipLines(
      meta[i].name, `${meta[i].count} reports  ·  ${meta[i].pct}% of tagged`));
    positionTooltip(card, target, tip);
  };
  const clear = () => {
    svg.classList.remove("is-hovering");
    segs.forEach(s => s.classList.remove("is-active"));
    tip.classList.remove("is-visible");
  };

  segs.forEach((seg, i) => {
    seg.addEventListener("mouseenter", () => activate(i, seg));
    seg.addEventListener("focus", () => activate(i, seg));
    seg.addEventListener("mouseleave", clear);
    seg.addEventListener("blur", clear);
  });
  [...legend.children].forEach((li, i) => {
    li.addEventListener("mouseenter", () => activate(i, segs[i]));
    li.addEventListener("mouseleave", clear);
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

function animateStatValue(el, target, format) {
  if (document.hidden || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    el.textContent = format(target);
    return;
  }
  const duration = 600;
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    el.textContent = format(target * (1 - Math.pow(1 - t, 3)));
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function renderStatCards(stats) {
  animateStatValue(document.getElementById("stat-total-reports"), stats.total_reports, v => String(Math.round(v)));
  animateStatValue(document.getElementById("stat-sif-count"), stats.sif_count, v => String(Math.round(v)));
  animateStatValue(document.getElementById("stat-density"), stats.density * 100, v => `${v.toFixed(1)}%`);
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
