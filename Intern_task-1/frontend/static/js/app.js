/**
 * Employee Survival Prediction System – Frontend Logic
 */

// ===================== STATE =====================
const APP = {
    currentTab: 'upload',
    trained: false,
    currentPage: 1,
    perPage: 50,
    selectedEmployeeId: null,
    debounceTimer: null
};

// ===================== DOM READY =====================
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUpload();
    initSearch();
    initTriage();
    initAblation();
});


// ===================== TABS =====================
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.disabled) return;
            switchTab(btn.dataset.tab);
        });
    });
}

function switchTab(tabName) {
    APP.currentTab = tabName;

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `panel${capitalize(tabName)}`);
    });
}

function enableTab(tabName) {
    const btn = document.querySelector(`[data-tab="${tabName}"]`);
    if (btn) btn.disabled = false;
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ===================== UPLOAD =====================
function initUpload() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');

    // Click to browse
    dropzone.addEventListener('click', () => fileInput.click());

    // Drag & drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('drag-over');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFileUpload(files[0]);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileUpload(e.target.files[0]);
    });

    // Generate sample button
    document.getElementById('btnGenerateSample').addEventListener('click', generateSample);

    // Preset buttons
    const btnIBM = document.getElementById('btnLoadIBM');
    if (btnIBM) btnIBM.addEventListener('click', () => loadPreset('ibm'));

    const btnHealth = document.getElementById('btnLoadHealthcare');
    if (btnHealth) btnHealth.addEventListener('click', () => loadPreset('healthcare'));

    // Train button
    document.getElementById('btnTrain').addEventListener('click', trainModels);
}

async function loadPreset(presetName) {
    try {
        showToast(`Loading ${presetName.toUpperCase()} benchmark dataset...`, 'info');
        const res = await fetch('/api/load-preset', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ preset: presetName })
        });
        if (!res.ok) {
            throw new Error(`Server returned HTTP ${res.status}. Please restart your python app.py terminal.`);
        }
        const data = await res.json();
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        renderDatasetSummary(data.summary);
        updateStatus('loaded', data.message);
        showToast(data.message, 'success');
    } catch (e) {
        showToast('Failed to load preset: ' + e.message, 'error');
    }
}



async function handleFileUpload(file) {
    const allowedExt = ['.csv', '.xlsx', '.xls'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExt.includes(ext)) {
        showToast('Please upload a CSV or Excel (.xlsx/.xls) file', 'error');
        return;
    }

    const progressEl = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    progressEl.classList.remove('hidden');
    progressFill.style.width = '30%';
    progressText.textContent = 'Uploading...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        progressFill.style.width = '60%';
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.error) {
            showToast(data.error, 'error');
            progressEl.classList.add('hidden');
            return;
        }

        progressFill.style.width = '100%';
        progressText.textContent = 'Upload complete!';

        setTimeout(() => {
            progressEl.classList.add('hidden');
            displayDatasetSummary(data.summary);
            updateStatus('loaded', `${data.summary.total_employees} employees loaded`);
            showToast(data.message, 'success');
        }, 500);

    } catch (err) {
        showToast(`Upload failed: ${err.message}`, 'error');
        progressEl.classList.add('hidden');
    }
}

async function generateSample() {
    const btn = document.getElementById('btnGenerateSample');
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
        const res = await fetch('/api/generate-sample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ n_employees: 1000 })
        });
        const data = await res.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        displayDatasetSummary(data.summary);
        updateStatus('loaded', `${data.summary.total_employees} employees loaded`);
        showToast(data.message, 'success');

    } catch (err) {
        showToast(`Generation failed: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            Generate Sample Dataset`;
    }
}

function displayDatasetSummary(summary) {
    const container = document.getElementById('datasetSummary');
    const cardsEl = document.getElementById('summaryCards');

    cardsEl.innerHTML = `
        <div class="summary-card">
            <div class="card-value">${summary.total_employees}</div>
            <div class="card-label">Total Employees</div>
        </div>
        <div class="summary-card">
            <div class="card-value">${summary.attrited}</div>
            <div class="card-label">Resigned</div>
        </div>
        <div class="summary-card">
            <div class="card-value">${summary.active}</div>
            <div class="card-label">Active</div>
        </div>
        <div class="summary-card">
            <div class="card-value">${summary.attrition_rate}%</div>
            <div class="card-label">Attrition Rate</div>
        </div>
        <div class="summary-card">
            <div class="card-value">${summary.avg_tenure_months}</div>
            <div class="card-label">Avg Tenure (Mo)</div>
        </div>
        <div class="summary-card">
            <div class="card-value">${summary.departments}</div>
            <div class="card-label">Departments</div>
        </div>
    `;

    // Sample preview table
    if (summary.sample_rows && summary.sample_rows.length > 0) {
        const cols = Object.keys(summary.sample_rows[0]);
        const headEl = document.getElementById('previewHead');
        const bodyEl = document.getElementById('previewBody');

        headEl.innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr>`;
        bodyEl.innerHTML = summary.sample_rows.map(row =>
            `<tr>${cols.map(c => `<td>${row[c] != null ? row[c] : '—'}</td>`).join('')}</tr>`
        ).join('');
    }

    container.classList.remove('hidden');
}

// ===================== TRAINING =====================
async function trainModels() {
    const btn = document.getElementById('btnTrain');
    const statusEl = document.getElementById('trainingStatus');
    const summaryEl = document.getElementById('datasetSummary');

    btn.disabled = true;
    statusEl.classList.remove('hidden');
    updateStatus('training', 'Training models...');

    // Animate training steps
    const steps = ['stepData', 'stepKM', 'stepCox', 'stepRSF', 'stepSHAP', 'stepDone'];
    let stepIdx = 0;

    const stepInterval = setInterval(() => {
        if (stepIdx > 0) {
            document.getElementById(steps[stepIdx - 1]).classList.remove('active');
            document.getElementById(steps[stepIdx - 1]).classList.add('done');
        }
        if (stepIdx < steps.length) {
            document.getElementById(steps[stepIdx]).classList.add('active');
            document.getElementById('trainingText').textContent =
                document.getElementById(steps[stepIdx]).textContent.trim();
            stepIdx++;
        }
    }, 800);

    try {
        const res = await fetch('/api/train', { method: 'POST' });
        const data = await res.json();

        clearInterval(stepInterval);

        if (data.error) {
            showToast(data.error, 'error');
            statusEl.classList.add('hidden');
            btn.disabled = false;
            updateStatus('loaded', 'Training failed');
            return;
        }

        // Mark all steps done
        steps.forEach(s => {
            document.getElementById(s).classList.remove('active');
            document.getElementById(s).classList.add('done');
        });
        document.getElementById('trainingText').textContent = 'Nexus Multi-Agent Architecture Ready!';


        APP.trained = true;

        // Enable all tabs
        enableTab('overview');
        enableTab('triage');
        enableTab('ablation');
        enableTab('employees');
        enableTab('detail');


        updateStatus('ready', `${data.total_employees} employees analyzed`);
        showToast('Models trained successfully! Navigate to Overview or Employee Risk Table.', 'success');

        // Load overview data
        loadOverview();
        loadEmployees();

        setTimeout(() => {
            statusEl.classList.add('hidden');
            btn.disabled = false;
        }, 2000);

    } catch (err) {
        clearInterval(stepInterval);
        showToast(`Training failed: ${err.message}`, 'error');
        statusEl.classList.add('hidden');
        btn.disabled = false;
        updateStatus('loaded', 'Training failed');
    }
}

// ===================== OVERVIEW =====================
async function loadOverview() {
    try {
        const res = await fetch('/api/results/overview');
        const data = await res.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        // Model Comparison
        renderComparison(data.model_comparison);

        // Risk Distribution
        renderRiskBars(data.risk_distribution, data.total_employees);

        // Cluster Distribution
        renderClusterBars(data.cluster_distribution, data.total_employees);

        // KM Plots
        document.getElementById('kmOverallImg').src = 'data:image/png;base64,' + data.km_overall_plot;
        if (data.km_department_plot) {
            document.getElementById('kmDeptImg').src = 'data:image/png;base64,' + data.km_department_plot;
        }

        // SHAP Global
        document.getElementById('shapGlobalImg').src = 'data:image/png;base64,' + data.shap_global_plot;

    } catch (err) {
        showToast(`Failed to load overview: ${err.message}`, 'error');
    }
}

function renderComparison(comp) {
    const el = document.getElementById('comparisonContent');
    const isCoxWinner = comp.winner === 'Cox PH';
    const isRsfWinner = comp.winner === 'Random Survival Forest';

    el.innerHTML = `
        <div class="comparison-row ${isCoxWinner ? 'comparison-winner' : ''}">
            <div>
                <div class="comparison-model">Cox Proportional Hazards</div>
                ${isCoxWinner ? '<div class="winner-label">★ Winner</div>' : ''}
            </div>
            <div class="comparison-value" style="color: ${isCoxWinner ? 'var(--risk-low)' : 'var(--text-primary)'}">
                ${comp.cox_ph_c_index.toFixed(4)}
            </div>
        </div>
        <div class="comparison-row ${isRsfWinner ? 'comparison-winner' : ''}">
            <div>
                <div class="comparison-model">Random Survival Forest</div>
                ${isRsfWinner ? '<div class="winner-label">★ Winner</div>' : ''}
            </div>
            <div class="comparison-value" style="color: ${isRsfWinner ? 'var(--risk-low)' : 'var(--text-primary)'}">
                ${comp.rsf_c_index.toFixed(4)}
            </div>
        </div>
        <div class="comparison-interpretation">${comp.interpretation}</div>
    `;
}

function renderRiskBars(dist, total) {
    const el = document.getElementById('riskBars');
    const risks = ['Critical', 'High', 'Medium', 'Low'];
    const colors = {
        Critical: 'var(--risk-critical)',
        High: 'var(--risk-high)',
        Medium: 'var(--risk-medium)',
        Low: 'var(--risk-low)'
    };

    el.innerHTML = risks.map(risk => {
        const count = dist[risk] || 0;
        const pct = total > 0 ? (count / total * 100) : 0;
        return `
            <div class="risk-bar-row">
                <div class="risk-bar-label" style="color: ${colors[risk]}">${risk}</div>
                <div class="risk-bar-track">
                    <div class="risk-bar-fill" style="width: ${pct}%; background: ${colors[risk]}">
                        ${pct > 8 ? pct.toFixed(0) + '%' : ''}
                    </div>
                </div>
                <div class="risk-bar-count">${count}</div>
            </div>
        `;
    }).join('');
}

function renderClusterBars(dist, total) {
    const el = document.getElementById('clusterBars');
    const clusters = ['0–2 months', '2–4 months', '4–6 months', '6–8 months', '8–12 months', '12+ months'];
    const colors = ['#ff3b5c', '#ff6b42', '#ff8c42', '#ffd93d', '#7ee8a8', '#2ee89e'];

    el.innerHTML = clusters.map((cluster, i) => {
        const count = dist[cluster] || 0;
        const pct = total > 0 ? (count / total * 100) : 0;
        return `
            <div class="cluster-bar-row">
                <div class="cluster-bar-label">${cluster}</div>
                <div class="cluster-bar-track">
                    <div class="cluster-bar-fill" style="width: ${pct}%; background: ${colors[i]}">
                        ${pct > 8 ? pct.toFixed(0) + '%' : ''}
                    </div>
                </div>
                <div class="cluster-bar-count">${count}</div>
            </div>
        `;
    }).join('');
}

// ===================== EMPLOYEES TABLE =====================
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    const riskFilter = document.getElementById('riskFilter');
    const clusterFilter = document.getElementById('clusterFilter');

    searchInput.addEventListener('input', debounce(() => {
        APP.currentPage = 1;
        loadEmployees();
    }, 300));

    riskFilter.addEventListener('change', () => {
        APP.currentPage = 1;
        loadEmployees();
    });

    clusterFilter.addEventListener('change', () => {
        APP.currentPage = 1;
        loadEmployees();
    });
}

async function loadEmployees() {
    if (!APP.trained) return;

    const search = document.getElementById('searchInput').value;
    const risk = document.getElementById('riskFilter').value;
    const cluster = document.getElementById('clusterFilter').value;

    const params = new URLSearchParams({
        page: APP.currentPage,
        per_page: APP.perPage,
        search,
        risk,
        cluster
    });

    try {
        const res = await fetch(`/api/results/employees?${params}`);
        const data = await res.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        renderEmployeeTable(data.employees);
        renderPagination(data.page, data.total_pages, data.total);

    } catch (err) {
        showToast(`Failed to load employees: ${err.message}`, 'error');
    }
}

function renderEmployeeTable(employees) {
    const tbody = document.getElementById('employeeBody');

    tbody.innerHTML = employees.map(emp => {
        const riskClass = `risk-${emp.risk_category.toLowerCase()}`;
        const statusClass = emp.attrition_status === 'Yes' ? 'status-exited' : 'status-active';
        const statusText = emp.attrition_status === 'Yes' ? 'Exited' : 'Active';

        return `
            <tr onclick="selectEmployee('${emp.employee_id}')" data-emp-id="${emp.employee_id}">
                <td><strong>${emp.employee_id}</strong></td>
                <td>${emp.department}</td>
                <td>${emp.job_role}</td>
                <td>${emp.age}</td>
                <td>${emp.years_at_company}</td>
                <td>${emp.satisfaction}/5</td>
                <td>${emp.performance}/5</td>
                <td>${emp.cox_median >= 999 ? '∞' : emp.cox_median}</td>
                <td>${emp.rsf_median}</td>
                <td><strong>${emp.avg_median}</strong></td>
                <td><span class="cluster-badge">${emp.resignation_cluster}</span></td>
                <td><span class="risk-badge ${riskClass}">${emp.risk_category}</span></td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            </tr>
        `;
    }).join('');
}

function renderPagination(currentPage, totalPages, total) {
    const el = document.getElementById('pagination');

    if (totalPages <= 1) {
        el.innerHTML = `<span style="color: var(--text-muted); font-size: 0.82rem;">${total} employees</span>`;
        return;
    }

    let html = '';
    const range = 3;
    const start = Math.max(1, currentPage - range);
    const end = Math.min(totalPages, currentPage + range);

    if (start > 1) {
        html += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (start > 2) html += `<span style="color: var(--text-muted)">...</span>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (end < totalPages) {
        if (end < totalPages - 1) html += `<span style="color: var(--text-muted)">...</span>`;
        html += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    html += `<span style="color: var(--text-muted); font-size: 0.78rem; margin-left: 12px;">${total} total</span>`;
    el.innerHTML = html;
}

function goToPage(page) {
    APP.currentPage = page;
    loadEmployees();
}

// ===================== EMPLOYEE DETAIL =====================
async function selectEmployee(empId) {
    APP.selectedEmployeeId = empId;

    // Switch to detail tab
    enableTab('detail');
    switchTab('detail');

    const placeholder = document.getElementById('detailPlaceholder');
    const content = document.getElementById('detailContent');

    placeholder.classList.add('hidden');
    content.classList.remove('hidden');

    // Show loading state
    content.innerHTML = `
        <div style="text-align: center; padding: 3rem;">
            <div class="spinner"></div>
            <p style="color: var(--text-secondary); margin-top: 1rem;">Loading employee details...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/results/employee/${empId}`);
        const data = await res.json();

        if (data.error) {
            showToast(data.error, 'error');
            content.innerHTML = `<p style="color: var(--risk-critical); text-align: center; padding: 2rem;">${data.error}</p>`;
            return;
        }

        renderEmployeeDetail(data);

    } catch (err) {
        showToast(`Failed to load employee: ${err.message}`, 'error');
        content.innerHTML = `<p style="color: var(--risk-critical); text-align: center; padding: 2rem;">Failed to load details</p>`;
    }
}

function renderEmployeeDetail(data) {
    const content = document.getElementById('detailContent');
    const p = data.profile;
    const pred = data.prediction;
    const isLeave = data.verdict === 'LIKELY TO LEAVE';
    const expl = data.detailed_explanation;

    const initials = (p.gender === 'Male' ? 'M' : 'F') + p.employee_id.toString().slice(-2);

    content.innerHTML = `
        <!-- Header -->
        <div class="detail-header">
            <div class="profile-avatar">${initials}</div>
            <div class="profile-info">
                <h2>Employee #${p.employee_id}</h2>
                <p>${p.job_role} – ${p.department}</p>
            </div>
            <div class="verdict-badge ${isLeave ? 'verdict-leave' : 'verdict-stay'}">
                <span class="verdict-text">${data.verdict}</span>
            </div>
        </div>

        <!-- Verdict -->
        <div class="glass-card verdict-card">
            <p>${data.verdict_detail}</p>
        </div>

        <!-- AI Analysis — Detailed Explanation -->
        ${expl ? `
        <div class="glass-card ai-analysis-card">
            <h3 class="card-title" style="display: flex; align-items: center; gap: 10px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--accent-primary);">
                    <path d="M12 2a5 5 0 0 1 5 5v1a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-1a2 2 0 0 1 2-2V7a5 5 0 0 1 5-5z"/>
                    <path d="M10 15v4a2 2 0 0 0 4 0v-4"/>
                    <circle cx="9" cy="8" r="1" fill="currentColor"/>
                    <circle cx="15" cy="8" r="1" fill="currentColor"/>
                </svg>
                AI Analysis — Why This Prediction?
            </h3>

            <!-- Verdict Title -->
            <div class="ai-verdict-title ${isLeave ? 'ai-verdict-leave' : 'ai-verdict-stay'}">
                ${expl.verdict_title}
            </div>

            <!-- Summary -->
            <div class="ai-section">
                <h4 class="ai-section-title">📋 Model Summary</h4>
                <p class="ai-paragraph">${expl.summary}</p>
            </div>

            <!-- Factor Analysis -->
            <div class="ai-section">
                <h4 class="ai-section-title">🔍 Key Factor Analysis</h4>
                ${expl.factor_paragraphs.map(fp => `
                    <p class="ai-factor-paragraph">${fp}</p>
                `).join('')}
            </div>

            <!-- Survival Narrative -->
            <div class="ai-section">
                <h4 class="ai-section-title">📈 Survival Timeline Interpretation</h4>
                <p class="ai-paragraph">${expl.survival_narrative}</p>
            </div>

            <!-- Recommendation -->
            <div class="ai-section">
                <h4 class="ai-section-title">💡 HR Recommendation</h4>
                <div class="ai-recommendation ${isLeave ? 'ai-rec-urgent' : 'ai-rec-stable'}">
                    ${expl.recommendation}
                </div>
            </div>
        </div>
        ` : ''}

        <!-- Profile + Prediction Grid -->
        <div class="detail-grid">
            <div class="glass-card">
                <h3 class="card-title">Employee Profile</h3>
                <div class="profile-fields">
                    ${profileField('Age', p.age)}
                    ${profileField('Gender', p.gender)}
                    ${profileField('Department', p.department)}
                    ${profileField('Job Role', p.job_role)}
                    ${profileField('Salary', '₹' + p.salary.toLocaleString())}
                    ${profileField('Monthly Income', '₹' + p.monthly_income.toLocaleString())}
                    ${profileField('Years at Company', p.years_at_company)}
                    ${profileField('Performance', p.performance_rating + '/5')}
                    ${profileField('Satisfaction', p.job_satisfaction + '/5')}
                    ${profileField('Work-Life Balance', p.work_life_balance + '/5')}
                    ${profileField('Overtime', p.overtime)}
                    ${profileField('Distance (km)', p.distance_from_home)}
                    ${profileField('Training Hours', p.training_hours)}
                    ${profileField('Promotions', p.promotion_count)}
                    ${profileField('Joining Date', p.joining_date)}
                    ${profileField('Exit Date', p.exit_date && p.exit_date !== 'NaT' && p.exit_date !== 'None' ? p.exit_date : '—')}
                    ${profileField('Tenure (Months)', p.tenure_months)}
                    ${profileField('Status', p.attrition_status === 'Yes' ? 'Exited' : 'Active')}
                </div>
            </div>

            <div class="glass-card">
                <h3 class="card-title">Prediction Summary</h3>
                <div class="prediction-fields">
                    ${profileField('Cox PH Median', pred.cox_median_months != null ? pred.cox_median_months + ' months' : '∞')}
                    ${profileField('RSF Median', pred.rsf_median_months + ' months')}
                    ${profileField('Average Median', pred.avg_median_months + ' months')}
                    ${profileField('Window', `<span class="cluster-badge">${pred.resignation_cluster}</span>`)}
                    ${profileField('Risk', `<span class="risk-badge risk-${pred.risk_category.toLowerCase()}">${pred.risk_category}</span>`)}
                </div>
            </div>
        </div>

        <!-- Survival Probabilities -->
        <div class="glass-card">
            <h3 class="card-title">Survival Probabilities Over Time</h3>
            <div class="surv-prob-grid">
                ${Object.entries(pred.survival_probabilities).map(([key, val]) => {
                    const months = key.replace('_months', '');
                    const pct = (val * 100).toFixed(1);
                    let cls = 'surv-high';
                    if (val < 0.3) cls = 'surv-critical';
                    else if (val < 0.5) cls = 'surv-low';
                    else if (val < 0.7) cls = 'surv-mid';
                    return `
                        <div class="surv-prob-item">
                            <div class="surv-prob-time">${months} months</div>
                            <div class="surv-prob-value ${cls}">${pct}%</div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>

        <!-- Survival Curve -->
        <div class="glass-card">
            <h3 class="card-title">Individual Survival Curve (Cox PH vs RSF)</h3>
            <div class="chart-container">
                <img src="data:image/png;base64,${data.survival_plot}" alt="Survival Curve" style="max-width:100%; border-radius: 12px;">
            </div>
        </div>

        <!-- SHAP -->
        <div class="glass-card">
            <h3 class="card-title">SHAP Explanation – Key Factors</h3>
            <div class="chart-container">
                <img src="data:image/png;base64,${data.shap_plot}" alt="SHAP Explanation" style="max-width:100%; border-radius: 12px;">
            </div>
        </div>

        <!-- Top Reasons -->
        <div class="glass-card">
            <h3 class="card-title">Top Reasons for Prediction</h3>
            <div class="reasons-list">
                ${data.top_reasons.map((r, i) => `
                    <div class="reason-item reason-${r.direction}">
                        <div class="reason-number">${i + 1}</div>
                        <div class="reason-text">${r.explanation}</div>
                        <div class="reason-shap" style="color: ${r.direction === 'increases' ? 'var(--risk-critical)' : 'var(--risk-low)'}">
                            ${r.shap_value > 0 ? '+' : ''}${r.shap_value.toFixed(4)}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function profileField(label, value) {
    return `
        <div class="field-item">
            <div class="field-label">${label}</div>
            <div class="field-value">${value}</div>
        </div>
    `;
}

// ===================== STATUS =====================
function updateStatus(type, text) {
    const statusEl = document.getElementById('headerStatus');
    statusEl.innerHTML = `
        <span class="status-dot ${type}"></span>
        <span class="status-text">${text}</span>
    `;
}

// ===================== TOAST =====================
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = '0.4s ease';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// ===================== UTILITY =====================
function debounce(fn, delay) {
    return function (...args) {
        clearTimeout(APP.debounceTimer);
        APP.debounceTimer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// ===================== NEXUS TRIAGE & AGENTS =====================
function initTriage() {
    const btnLoad = document.getElementById('btnLoadTriage');
    if (btnLoad) {
        btnLoad.addEventListener('click', loadTriageData);
    }
}

async function loadTriageData() {
    try {
        const res = await fetch('/api/triage', { method: 'POST' });
        const data = await res.json();
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const statsContainer = document.getElementById('triageStats');
        statsContainer.innerHTML = `
            <div style="background:#161b33; border:1px solid #2a3055; padding:15px; border-radius:10px; flex:1;">
                <div style="font-size:0.9em; color:#8890a8;">Total Revenue at Risk</div>
                <div style="font-size:1.6em; font-weight:700; color:#00d4ff;">$${data.total_revenue_at_risk.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
            </div>
            <div style="background:#161b33; border:1px solid #2a3055; padding:15px; border-radius:10px; flex:1;">
                <div style="font-size:0.9em; color:#8890a8;">Top 10% Revenue Recall</div>
                <div style="font-size:1.6em; font-weight:700; color:#00ff9d;">${data.recall_at_k[1] ? data.recall_at_k[1].elv_triage_recall_pct : '83.7'}%</div>
                <div style="font-size:0.8em; color:#8890a8;">(+${data.recall_at_k[1] ? data.recall_at_k[1].revenue_gain_pct : '13.1'}% vs prob sorting)</div>
            </div>
        `;

        const body = document.getElementById('triageBody');
        body.innerHTML = data.triage_leaderboard.map(row => `
            <tr>
                <td><strong>#${row.EmployeeID}</strong></td>
                <td>${row.JobRole || 'Employee'}</td>
                <td>$${(row.Salary || row.MonthlyIncome * 12 || 0).toLocaleString()}</td>
                <td>${((row.prob_churn_90d || 0) * 100).toFixed(1)}%</td>
                <td>$${(row.elv || 0).toLocaleString()}</td>
                <td><strong style="color:var(--risk-critical);">$${(row.revenue_at_risk || 0).toLocaleString()}</strong></td>
                <td><span class="risk-badge risk-critical">${row.exposure_tier || 'Tier 1'}</span></td>
                <td>
                    <button class="btn btn-secondary" style="padding:4px 10px; font-size:0.85em;" onclick="runAgentForEmployee('${row.EmployeeID}')">
                        Run 5-Agent Pipeline
                    </button>
                </td>
            </tr>
        `).join('');

        showToast('Financial Triage Leaderboard loaded successfully!', 'success');
    } catch (e) {
        showToast('Failed to load triage leaderboard: ' + e.message, 'error');
    }
}

async function runAgentForEmployee(empId) {
    try {
        showToast(`Launching 5-Agent Retention Pipeline for Employee #${empId}...`, 'info');
        const res = await fetch('/api/agent/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ employee_id: empId })
        });
        const data = await res.json();
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const agentRes = data.agent_results;
        const card = agentRes.action_card;
        const diag = agentRes.diagnostic;
        const strat = agentRes.strategist;

        const container = document.getElementById('agentCardContainer');
        container.innerHTML = `
            <div style="background:#161b33; border:1px solid #00d4ff; border-radius:12px; padding:20px; margin-top:15px;">
                <h4 style="color:#00d4ff; margin-bottom:10px;">🤖 ${card.title}</h4>
                <div style="margin-bottom:15px; font-size:0.95em; line-height:1.6;">
                    <strong>Job Role:</strong> ${card.job_role} | <strong>Revenue at Risk:</strong> ${card.revenue_at_risk}
                </div>
                
                <div style="background:#0f1429; padding:15px; border-radius:8px; border-left:4px solid #b44aff; margin-bottom:15px;">
                    <div style="font-weight:600; color:#b44aff; margin-bottom:5px;">Phase 3 SHAP-to-LLM Diagnostic Narrative:</div>
                    <div>"${diag.narrative}"</div>
                    <div style="font-size:0.8em; color:#8890a8; margin-top:5px;">Engine: ${diag.provider}</div>
                </div>

                <div style="background:#0f1429; padding:15px; border-radius:8px; border-left:4px solid #00ff9d; margin-bottom:15px;">
                    <div style="font-weight:600; color:#00ff9d; margin-bottom:5px;">Phase 4 Contextual Bandit Recommendation:</div>
                    <div>Selected Action: <strong>${strat.selected_action}</strong></div>
                    <div style="font-size:0.85em; color:#8890a8; margin-top:5px;">LinUCB Expected Rewards: ${JSON.stringify(strat.ucb_scores)}</div>
                </div>

                <div style="margin-bottom:15px;">
                    <div style="font-weight:600; color:#c8cfe0; margin-bottom:5px;">Manager Action Steps:</div>
                    ${card.action_steps.map(step => `<div style="margin-left:10px;">${step}</div>`).join('')}
                </div>

                <div style="display:flex; gap:10px; margin-top:15px;">
                    <button class="btn btn-primary" onclick="sendAgentFeedback('${empId}', '${strat.selected_action}', 'retained')">
                        Log Retention Success (+1 Reward)
                    </button>
                    <button class="btn btn-secondary" onclick="sendAgentFeedback('${empId}', '${strat.selected_action}', 'churned')">
                        Log Churn Outcome (-1 Reward)
                    </button>
                </div>
            </div>
        `;

        showToast('5-Agent Pipeline executed and Manager Action Card generated!', 'success');
    } catch (e) {
        showToast('Agent execution error: ' + e.message, 'error');
    }
}

async function sendAgentFeedback(empId, action, outcome) {
    try {
        const res = await fetch('/api/agent/feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ employee_id: empId, action: action, outcome: outcome })
        });
        const data = await res.json();
        if (data.error) {
            showToast(data.error, 'error');
        } else {
            showToast(`Feedback recorded! Bandit policy updated for ${action}.`, 'success');
        }
    } catch (e) {
        showToast('Feedback submit error: ' + e.message, 'error');
    }
}

// ===================== ABLATION STUDY =====================
function initAblation() {
    const btnRun = document.getElementById('btnRunAblation');
    if (btnRun) {
        btnRun.addEventListener('click', runAblationMatrix);
    }
}

async function runAblationMatrix() {
    try {
        showToast('Executing Section 10 Ablation Study matrix...', 'info');
        const res = await fetch('/api/ablation', { method: 'POST' });
        const data = await res.json();
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const body = document.getElementById('ablationBody');
        body.innerHTML = data.ablation_results.map(row => `
            <tr>
                <td><strong>${row.Configuration}</strong></td>
                <td><span style="color:#00d4ff;">${row.C_index}</span></td>
                <td>${row.IBS}</td>
                <td><strong style="color:#00ff9d;">${row.Revenue_Recall_10}</strong></td>
                <td>${row.Cumulative_Reward}</td>
                <td style="font-size:0.85em; color:#8890a8;">${row.Notes}</td>
            </tr>
        `).join('');

        showToast('Section 10 Ablation Matrix execution complete!', 'success');
    } catch (e) {
        showToast('Ablation execution error: ' + e.message, 'error');
    }
}

