/**
 * INSYTE — Frontend Application Controller
 * Handles tab navigation, interactive Chart.js visualizations,
 * RFM heatmaps, cohort matrices, semantic search, and SQL insights.
 */

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initGlobalSearch();
  loadOverviewModule();
  loadCustomerModule();
  loadProductModule();
  loadSalesModule();
  loadReviewModule();
  loadHealthModule();
  loadSqlInsightsModule();
});

// -----------------------------------------------------------------------------
// 1. Navigation & Tab Switching
// -----------------------------------------------------------------------------
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  const tabPanels = document.querySelectorAll(".tab-content");
  const pageTitle = document.getElementById("pageTitle");

  const titles = {
    overview: "Overview",
    customers: "Customer Analytics & RFM",
    products: "Product Analytics & Catalog",
    sales: "Sales Trends & Cohort Retention",
    reviews: "Reviews & Media Intelligence",
    health: "Commercial Product Health",
    sql: "SQL Insights & Academic Console"
  };

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const tabId = item.getAttribute("data-tab");

      navItems.forEach(n => n.classList.remove("active"));
      tabPanels.forEach(p => p.classList.remove("active"));

      item.classList.add("active");
      const activePanel = document.getElementById(`tab-${tabId}`);
      if (activePanel) activePanel.classList.add("active");

      pageTitle.textContent = titles[tabId] || "Analytics";
      if (window.feather) feather.replace();
    });
  });
}

// -----------------------------------------------------------------------------
// 2. Global & Semantic Vector Search
// -----------------------------------------------------------------------------
function initGlobalSearch() {
  const searchInput = document.getElementById("globalSearchInput");
  const searchModeBtn = document.getElementById("searchModeBtn");
  const modal = document.getElementById("vectorSearchModal");
  const closeModalBtn = document.getElementById("closeVectorModalBtn");
  const resultsContainer = document.getElementById("vectorSearchResultsList");
  const modalSubtitle = document.getElementById("vectorSearchSubtitle");

  let vectorMode = true;

  searchModeBtn.addEventListener("click", () => {
    vectorMode = !vectorMode;
    searchModeBtn.querySelector("span").textContent = vectorMode ? "Vector AI" : "Keyword";
    searchModeBtn.style.background = vectorMode ? "var(--accent-green-glow)" : "rgba(255,255,255,0.06)";
  });

  searchInput.addEventListener("keypress", async (e) => {
    if (e.key === "Enter") {
      const query = searchInput.value.trim();
      if (!query) return;

      if (vectorMode) {
        modal.style.display = "flex";
        resultsContainer.innerHTML = "<div style='color:var(--text-muted); padding:20px; text-align:center;'>Executing 384-dimensional Oracle Vector Search...</div>";
        modalSubtitle.textContent = `Query: "${query}" via Oracle VECTOR_DISTANCE(embedding, :vec, COSINE)`;

        try {
          const res = await fetch(`/api/search/semantic?q=${encodeURIComponent(query)}`);
          const items = await res.json();
          renderVectorResults(items, resultsContainer);
        } catch (err) {
          resultsContainer.innerHTML = `<div style='color:var(--status-at-risk);'>Error querying Oracle Vector: ${err}</div>`;
        }
      }
    }
  });

  closeModalBtn.addEventListener("click", () => {
    modal.style.display = "none";
  });
}

function renderVectorResults(items, container) {
  if (!items || items.length === 0) {
    container.innerHTML = "<div style='color:var(--text-muted); padding:20px; text-align:center;'>No semantic matches found.</div>";
    return;
  }

  container.innerHTML = items.map((item, idx) => `
    <div style="background: rgba(255,255,255,0.03); border:1px solid var(--border-subtle); border-radius: var(--radius-md); padding:16px; display:flex; justify-content:space-between; align-items:center;">
      <div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
          <span style="font-weight:700; color:var(--accent-green-light); font-size:0.85rem;">#${idx+1} [${item.stock_code}]</span>
          <span style="font-weight:600; color:#fff;">${item.description}</span>
        </div>
        <div style="font-size:0.78rem; color:var(--text-muted); display:flex; gap:16px;">
          <span>Price: £${item.unit_price.toFixed(2)}</span>
          <span>Revenue: £${item.revenue.toLocaleString()}</span>
          <span>Rating: ★ ${item.avg_rating} (${item.review_count} revs)</span>
        </div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:1.15rem; font-weight:700; color:var(--accent-green-light);">${Math.round(item.similarity_score * 100)}% Match</div>
        <div style="font-size:0.7rem; color:var(--text-muted);">Cosine Dist: ${item.cosine_distance}</div>
      </div>
    </div>
  `).join("");
}

// -----------------------------------------------------------------------------
// 3. Module 1: Overview
// -----------------------------------------------------------------------------
async function loadOverviewModule() {
  try {
    // 1. Revenue Trends Chart
    const trendsRes = await fetch("/api/overview/trends");
    const trends = await trendsRes.json();
    renderOverviewRevenueChart(trends);

    // 2. Customer Segments Chart
    const segRes = await fetch("/api/customers/rfm-segments");
    const segments = await segRes.json();
    renderOverviewSegmentChart(segments);

    // 3. Country Performance Chart
    const countryRes = await fetch("/api/overview/countries");
    const countries = await countryRes.json();
    renderOverviewCountryChart(countries);

    // 4. Factual Insights List
    const insRes = await fetch("/api/overview/insights");
    const insights = await insRes.json();
    const insightsList = document.getElementById("factualInsightsList");
    insightsList.innerHTML = insights.map(item => `
      <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 12px 14px; display: flex; align-items: center; gap: 12px;">
        <div style="width: 28px; height: 28px; border-radius: 6px; background: var(--accent-green-glow); display: flex; align-items: center; justify-content: center; color: var(--accent-green-light); flex-shrink: 0;">
          <i data-feather="${item.icon}" style="width: 14px; height: 14px;"></i>
        </div>
        <span style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">${item.text}</span>
      </div>
    `).join("");
    if (window.feather) feather.replace();

  } catch (err) {
    console.error("Error loading overview:", err);
  }
}

function renderOverviewRevenueChart(data) {
  const ctx = document.getElementById("overviewRevenueChart").getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map(d => d.period_label),
      datasets: [
        {
          label: "Net Revenue (£)",
          data: data.map(d => d.net_revenue),
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.12)",
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3
        },
        {
          label: "Gross Sales (£)",
          data: data.map(d => d.gross_sales),
          borderColor: "rgba(255, 255, 255, 0.3)",
          borderDash: [4, 4],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#9ca3af", font: { size: 11 } } },
        tooltip: { mode: "index", intersect: false }
      },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280" } },
        y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", callback: v => "£" + (v/1000) + "k" } }
      }
    }
  });
}

function renderOverviewSegmentChart(data) {
  const ctx = document.getElementById("overviewSegmentChart").getContext("2d");
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: data.map(d => d.rfm_segment),
      datasets: [{
        data: data.map(d => d.total_revenue),
        backgroundColor: ["#10b981", "#3b82f6", "#8b5cf6", "#f59e0b", "#ef4444", "#6b7280"],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { color: "#9ca3af", font: { size: 10 } } }
      }
    }
  });
}

function renderOverviewCountryChart(data) {
  const ctx = document.getElementById("overviewCountryChart").getContext("2d");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map(d => d.country),
      datasets: [{
        label: "Revenue (£)",
        data: data.map(d => d.total_revenue),
        backgroundColor: "#10b981",
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#6b7280" } },
        y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", callback: v => "£" + (v/1000000).toFixed(1) + "M" } }
      }
    }
  });
}

// -----------------------------------------------------------------------------
// 4. Module 2: Customer Analytics & RFM
// -----------------------------------------------------------------------------
async function loadCustomerModule() {
  try {
    // 1. RFM Heatmap
    const heatRes = await fetch("/api/customers/rfm-heatmap");
    const heatData = await heatRes.json();
    const heatmapGrid = document.getElementById("rfmHeatmapGrid");
    heatmapGrid.innerHTML = heatData.map(cell => {
      const alpha = Math.min(0.85, 0.15 + (cell.count / 700));
      return `
        <div class="heatmap-cell" style="background: rgba(16, 185, 129, ${alpha});" title="Recency: R${cell.r}, Frequency: F${cell.f} (${cell.segment})">
          <div class="heatmap-cell-val">${cell.count}</div>
          <div class="heatmap-cell-label">R${cell.r} · F${cell.f}</div>
        </div>
      `;
    }).join("");

    // 2. RFM Segments Table
    const segRes = await fetch("/api/customers/rfm-segments");
    const segments = await segRes.json();
    const segTable = document.querySelector("#rfmSegmentTable tbody");
    segTable.innerHTML = segments.map(s => `
      <tr>
        <td style="font-weight:600; color:#fff;">${s.rfm_segment}</td>
        <td>${s.customer_count.toLocaleString()}</td>
        <td>${s.customer_pct}%</td>
        <td style="color:var(--accent-green-light); font-weight:600;">£${s.total_revenue.toLocaleString()}</td>
        <td>${s.avg_order_frequency} orders</td>
      </tr>
    `).join("");

    // 3. Customer Registry Table
    loadCustomerRegistry();
    document.getElementById("customerSegmentSelect").addEventListener("change", (e) => {
      loadCustomerRegistry(e.target.value);
    });

  } catch (err) {
    console.error("Error loading customer analytics:", err);
  }
}

async function loadCustomerRegistry(segment = "ALL") {
  const res = await fetch(`/api/customers/list?segment=${segment}`);
  const customers = await res.json();
  const table = document.querySelector("#customerRegistryTable tbody");
  table.innerHTML = customers.map(c => `
    <tr>
      <td style="font-family: var(--font-mono); color: #fff; font-weight: 500;">${c.customer_id}</td>
      <td>${c.country}</td>
      <td>${c.recency_days} days ago</td>
      <td>${c.frequency_orders}</td>
      <td style="color:var(--accent-green-light); font-weight:600;">£${c.monetary_spend.toLocaleString()}</td>
      <td style="font-family: var(--font-mono);">${c.r_score}${c.f_score}${c.m_score}</td>
      <td><span class="badge ${c.rfm_segment === 'Champions' ? 'badge-healthy' : (c.rfm_segment === 'At Risk' ? 'badge-at-risk' : 'badge-watch')}">${c.rfm_segment}</span></td>
    </tr>
  `).join("");
}

// -----------------------------------------------------------------------------
// 5. Module 3: Product Analytics
// -----------------------------------------------------------------------------
async function loadProductModule() {
  loadProductCatalog();
  document.getElementById("productSortSelect").addEventListener("change", (e) => {
    loadProductCatalog(e.target.value);
  });
}

async function loadProductCatalog(sortBy = "revenue") {
  const res = await fetch(`/api/products/list?sort_by=${sortBy}`);
  const products = await res.json();
  const table = document.querySelector("#productCatalogTable tbody");
  table.innerHTML = products.map(p => `
    <tr>
      <td style="font-family: var(--font-mono); color: #fff;">${p.stock_code}</td>
      <td style="max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${p.description}</td>
      <td>£${p.unit_price.toFixed(2)}</td>
      <td style="color:var(--accent-green-light); font-weight:600;">£${p.revenue.toLocaleString()}</td>
      <td>${p.units_sold.toLocaleString()}</td>
      <td>${p.order_count.toLocaleString()}</td>
      <td>★ ${p.avg_rating} (${p.review_count})</td>
      <td><button class="filter-select" style="padding: 3px 8px; font-size: 0.72rem;" onclick="showProductJson('${p.stock_code}')">Inspect JSON</button></td>
    </tr>
  `).join("");
}

window.showProductJson = async function(stockCode) {
  const res = await fetch(`/api/products/${stockCode}`);
  const data = await res.json();
  alert(`Oracle JSON Metadata for [${stockCode}]:\n` + JSON.stringify(data.metadata_json, null, 2));
};

// -----------------------------------------------------------------------------
// 6. Module 4: Sales & Trends
// -----------------------------------------------------------------------------
async function loadSalesModule() {
  // 1. Gross vs Net Breakdown Chart
  const trendsRes = await fetch("/api/overview/trends");
  const trends = await trendsRes.json();
  const ctxGross = document.getElementById("salesGrossNetChart").getContext("2d");
  new Chart(ctxGross, {
    type: "bar",
    data: {
      labels: trends.map(t => t.period_label),
      datasets: [
        { label: "Net Revenue (£)", data: trends.map(t => t.net_revenue), backgroundColor: "#10b981" },
        { label: "Returns / Cancels (£)", data: trends.map(t => t.returns), backgroundColor: "#ef4444" }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: "#6b7280" } },
        y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", callback: v => "£" + (v/1000) + "k" } }
      }
    }
  });

  // 2. AOV Trend Chart
  const aovRes = await fetch("/api/sales/aov");
  const aovData = await aovRes.json();
  const ctxAov = document.getElementById("salesAovChart").getContext("2d");
  new Chart(ctxAov, {
    type: "line",
    data: {
      labels: aovData.map(a => a.period),
      datasets: [{
        label: "Average Order Value (£)",
        data: aovData.map(a => a.aov),
        borderColor: "#38bdf8",
        borderWidth: 2,
        tension: 0.3,
        pointRadius: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: "#6b7280" } },
        y: { min: 190, max: 215, grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", callback: v => "£" + v } }
      }
    }
  });

  // 3. Cohort Retention Matrix
  const cohortRes = await fetch("/api/sales/cohorts");
  const cohorts = await cohortRes.json();
  const cohortTable = document.querySelector("#cohortMatrixTable tbody");
  cohortTable.innerHTML = cohorts.map(c => `
    <tr>
      <td style="font-weight:600; color:#fff;">${c.cohort_month}</td>
      <td>${c.cohort_size}</td>
      <td style="background: rgba(16, 185, 129, 0.4); text-align:center;">100%</td>
      <td style="background: rgba(16, 185, 129, ${c.m1_retention_pct ? c.m1_retention_pct/100 : 0}); text-align:center;">${c.m1_retention_pct ? c.m1_retention_pct + '%' : '-'}</td>
      <td style="background: rgba(16, 185, 129, ${c.m2_retention_pct ? c.m2_retention_pct/100 : 0}); text-align:center;">${c.m2_retention_pct ? c.m2_retention_pct + '%' : '-'}</td>
      <td style="background: rgba(16, 185, 129, ${c.m3_retention_pct ? c.m3_retention_pct/100 : 0}); text-align:center;">${c.m3_retention_pct ? c.m3_retention_pct + '%' : '-'}</td>
      <td style="background: rgba(16, 185, 129, ${c.m4_retention_pct ? c.m4_retention_pct/100 : 0}); text-align:center;">${c.m4_retention_pct ? c.m4_retention_pct + '%' : '-'}</td>
      <td style="background: rgba(16, 185, 129, ${c.m5_retention_pct ? c.m5_retention_pct/100 : 0}); text-align:center;">${c.m5_retention_pct ? c.m5_retention_pct + '%' : '-'}</td>
      <td style="background: rgba(16, 185, 129, ${c.m6_retention_pct ? c.m6_retention_pct/100 : 0}); text-align:center;">${c.m6_retention_pct ? c.m6_retention_pct + '%' : '-'}</td>
    </tr>
  `).join("");
}

// -----------------------------------------------------------------------------
// 7. Module 5: Reviews & Media
// -----------------------------------------------------------------------------
async function loadReviewModule() {
  // 1. Rating Distribution Chart
  const rateRes = await fetch("/api/reviews/ratings");
  const ratings = await rateRes.json();
  const ctxRate = document.getElementById("reviewRatingChart").getContext("2d");
  new Chart(ctxRate, {
    type: "bar",
    data: {
      labels: ratings.map(r => r.star_rating + " Stars"),
      datasets: [{ label: "Count", data: ratings.map(r => r.review_count), backgroundColor: "#f59e0b", borderRadius: 4 }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280" } },
        y: { grid: { display: false }, ticks: { color: "#6b7280" } }
      }
    }
  });

  // 2. Media Comparison Chart
  const mediaRes = await fetch("/api/reviews/media-comparison");
  const mediaData = await mediaRes.json();
  const ctxMedia = document.getElementById("reviewMediaChart").getContext("2d");
  new Chart(ctxMedia, {
    type: "bar",
    data: {
      labels: mediaData.map(m => m.media_type),
      datasets: [
        { label: "Avg Rating (out of 5)", data: mediaData.map(m => m.avg_rating), backgroundColor: "#10b981", yAxisID: "y" },
        { label: "Satisfaction %", data: mediaData.map(m => m.satisfaction_rate), backgroundColor: "#38bdf8", yAxisID: "y1" }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { type: "linear", position: "left", max: 5, ticks: { color: "#6b7280" } },
        y1: { type: "linear", position: "right", max: 100, ticks: { color: "#6b7280" }, grid: { display: false } }
      }
    }
  });

  // 3. Media Gallery Cards
  const galRes = await fetch("/api/reviews/gallery?limit=6");
  const gallery = await galRes.json();
  const galleryGrid = document.getElementById("mediaGalleryGrid");
  galleryGrid.innerHTML = gallery.map(item => `
    <div class="media-card">
      <img src="${item.media_url}" class="media-thumbnail" alt="${item.product_name}" onerror="this.src='https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=400'">
      <div class="media-body">
        <div class="media-product">${item.product_name}</div>
        <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">★ ${item.rating} · ${item.sentiment}</div>
        <div class="media-review-snippet">"${item.review_text}"</div>
        <div style="font-size:0.7rem; color:var(--text-muted);">${item.review_date}</div>
      </div>
    </div>
  `).join("");

  // 4. Review Explorer Table
  loadReviewExplorer();
  document.getElementById("reviewSentimentSelect").addEventListener("change", (e) => {
    loadReviewExplorer(e.target.value);
  });
}

async function loadReviewExplorer(sentiment = "ALL") {
  const res = await fetch(`/api/reviews/explorer?sentiment=${sentiment}`);
  const reviews = await res.json();
  const table = document.querySelector("#reviewExplorerTable tbody");
  table.innerHTML = reviews.map(r => `
    <tr>
      <td style="font-family: var(--font-mono);">${r.review_id}</td>
      <td style="font-weight:500; color:#fff;">${r.product_name}</td>
      <td>★ ${r.rating}</td>
      <td><span class="badge ${r.sentiment === 'POSITIVE' ? 'badge-healthy' : (r.sentiment === 'NEGATIVE' ? 'badge-at-risk' : 'badge-watch')}">${r.sentiment}</span></td>
      <td style="max-width:320px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${r.review_text}</td>
      <td>${r.has_media ? '📷 Yes' : '—'}</td>
      <td>${r.review_date}</td>
    </tr>
  `).join("");
}

// -----------------------------------------------------------------------------
// 8. Module 6: Commercial Product Health
// -----------------------------------------------------------------------------
async function loadHealthModule() {
  loadHealthMatrix();
  document.getElementById("healthStatusSelect").addEventListener("change", (e) => {
    loadHealthMatrix(e.target.value);
  });
}

async function loadHealthMatrix(status = "ALL") {
  const res = await fetch(`/api/health/matrix?status=${status}`);
  const matrix = await res.json();
  const table = document.querySelector("#healthMatrixTable tbody");
  table.innerHTML = matrix.map(m => `
    <tr>
      <td style="font-family: var(--font-mono); color:#fff;">${m.stock_code}</td>
      <td style="font-weight:500; color:#fff;">${m.description}</td>
      <td>£${m.unit_price.toFixed(2)}</td>
      <td style="color:var(--accent-green-light); font-weight:600;">£${m.revenue.toLocaleString()}</td>
      <td>${m.units_sold.toLocaleString()}</td>
      <td style="color: ${m.return_rate_pct > 5 ? 'var(--status-at-risk)' : 'var(--text-secondary)'}; font-weight:600;">${m.return_rate_pct}%</td>
      <td>★ ${m.avg_rating}</td>
      <td><span class="badge ${m.health_status === 'HEALTHY' ? 'badge-healthy' : (m.health_status === 'AT_RISK' ? 'badge-at-risk' : 'badge-watch')}">${m.health_status}</span></td>
      <td style="font-size:0.78rem; color:var(--text-secondary);">${m.rationale || 'Normal commercial velocity'}</td>
    </tr>
  `).join("");
}

// -----------------------------------------------------------------------------
// 9. Module 7: SQL Insights & Academic Console
// -----------------------------------------------------------------------------
async function loadSqlInsightsModule() {
  const res = await fetch("/api/sql/catalog");
  const catalog = await res.json();
  const list = document.getElementById("sqlCatalogList");

  list.innerHTML = catalog.map(item => `
    <button class="sql-item-btn" data-qid="${item.id}">
      <div style="font-weight:600; color:#fff;">${item.title}</div>
      <div style="font-size:0.7rem; color:var(--accent-green-light);">${item.category}</div>
    </button>
  `).join("");

  const buttons = list.querySelectorAll(".sql-item-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadQueryDetails(btn.getAttribute("data-qid"));
    });
  });

  if (buttons.length > 0) {
    buttons[0].click();
  }

  // Data Dictionary Quick Buttons
  document.getElementById("dictTablesBtn").addEventListener("click", () => showDataDictionary("tables"));
  document.getElementById("dictIndexesBtn").addEventListener("click", () => showDataDictionary("indexes"));
  document.getElementById("dictMviewsBtn").addEventListener("click", () => showDataDictionary("mviews"));
}

async function loadQueryDetails(queryId) {
  const res = await fetch(`/api/sql/query/${queryId}`);
  const details = await res.json();

  document.getElementById("sqlViewTitle").textContent = details.title;
  document.getElementById("sqlViewCategory").textContent = `Category: ${details.category}`;
  document.getElementById("sqlExecTime").textContent = `${details.execution_time_ms} ms (Oracle)`;
  document.getElementById("sqlViewDesc").textContent = details.description;

  const tags = document.getElementById("sqlFeatureTags");
  tags.innerHTML = details.academic_features.map(f => `
    <span style="font-size:0.7rem; background:rgba(255,255,255,0.06); border:1px solid var(--border-subtle); padding:2px 8px; border-radius:4px; color:var(--accent-green-light);">
      ${f}
    </span>
  `).join("");

  document.getElementById("sqlCodeBlock").textContent = details.sql;
  document.getElementById("sqlExplainBlock").textContent = Array.isArray(details.explain_plan) 
    ? details.explain_plan.join("\n") 
    : JSON.stringify(details.explain_plan, null, 2);
}

async function showDataDictionary(category) {
  const res = await fetch(`/api/sql/dictionary/${category}`);
  const data = await res.json();
  alert(`Oracle 23ai Data Dictionary [${category.toUpperCase()}]:\n` + JSON.stringify(data, null, 2));
}
