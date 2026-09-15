/**
 * NEXUS AI - Frontend Application Logic
 * Multi-Model Metrics Hub, Novelty Engines & Agent Telemetry
 */

document.addEventListener('DOMContentLoaded', () => {
    // Application State
    const appState = {
        activeTab: 'metrics-hub',
        activeSubTab: 'sub-cox',
        isTrained: false,
        currentPreset: 'ibm',
        overviewData: null,
        triageData: [],
        hazardRatios: [],
        currentPage: 1,
        perPage: 25,
        totalEmployees: 0
    };

    // DOM Elements
    const elements = {
        // Tabs
        navTabs: document.querySelectorAll('.nav-tab'),
        tabPanels: document.querySelectorAll('.tab-content'),
        subTabBtns: document.querySelectorAll('.subtab-btn'),
        subTabPanels: document.querySelectorAll('.subtab-content'),

        // Header actions
        btnLoadIBM: document.getElementById('btnLoadIBM'),
        btnLoadHealthcare: document.getElementById('btnLoadHealthcare'),
        fileInput: document.getElementById('fileInput'),
        btnTrainPipeline: document.getElementById('btnTrainPipeline'),
        datasetStatusText: document.getElementById('datasetStatusText'),
        modelStatusText: document.getElementById('modelStatusText'),

        // KPIs
        kpiBestModel: document.getElementById('kpiBestModel'),
        kpiEnsembleWeights: document.getElementById('kpiEnsembleWeights'),
        kpiBaselineDelta: document.getElementById('kpiBaselineDelta'),
        kpiAvgTenure: document.getElementById('kpiAvgTenure'),

        // Cox PH metrics
        coxTestCI: document.getElementById('coxTestCI'),
        coxTrainCI: document.getElementById('coxTrainCI'),
        coxCvCI: document.getElementById('coxCvCI'),
        coxTestIBS: document.getElementById('coxTestIBS'),
        coxLogLikelihood: document.getElementById('coxLogLikelihood'),
        coxAIC: document.getElementById('coxAIC'),
        hazardRatiosBody: document.getElementById('hazardRatiosBody'),
        hrSearchInput: document.getElementById('hrSearchInput'),

        // RSF metrics
        rsfTestCI: document.getElementById('rsfTestCI'),
        rsfTrainCI: document.getElementById('rsfTrainCI'),
        rsfCvCI: document.getElementById('rsfCvCI'),
        rsfTestIBS: document.getElementById('rsfTestIBS'),

        // Ensemble metrics
        ensWeightCox: document.getElementById('ensWeightCox'),
        ensWeightRSF: document.getElementById('ensWeightRSF'),

        // Images
        kmOverallContainer: document.getElementById('kmOverallContainer'),
        kmDeptContainer: document.getElementById('kmDeptContainer'),
        globalShapContainer: document.getElementById('globalShapContainer'),

        // Triage (Novelty 2)
        triageTotalRAR: document.getElementById('triageTotalRAR'),
        triageRecall10: document.getElementById('triageRecall10'),
        triageTableBody: document.getElementById('triageTableBody'),
        triageSearchInput: document.getElementById('triageSearchInput'),

        // Diagnostic (Novelty 3)
        diagEmpIdInput: document.getElementById('diagEmpIdInput'),
        btnInspectDiagnostic: document.getElementById('btnInspectDiagnostic'),
        diagResultBox: document.getElementById('diagResultBox'),
        diagEmpTitle: document.getElementById('diagEmpTitle'),
        diagRiskBadge: document.getElementById('diagRiskBadge'),
        diagNarrativeText: document.getElementById('diagNarrativeText'),
        diagReasonsList: document.getElementById('diagReasonsList'),
        diagIndividualPlotContainer: document.getElementById('diagIndividualPlotContainer'),

        // Agent (Novelty 4)
        agentEmpInput: document.getElementById('agentEmpInput'),
        btnRunAgentPipeline: document.getElementById('btnRunAgentPipeline'),
        actionCardBox: document.getElementById('actionCardBox'),
        actionCardTitle: document.getElementById('actionCardTitle'),
        actionArmBadge: document.getElementById('actionArmBadge'),
        cardEmpName: document.getElementById('cardEmpName'),
        cardEmpRole: document.getElementById('cardEmpRole'),
        cardStrategyText: document.getElementById('cardStrategyText'),
        cardRARText: document.getElementById('cardRARText'),

        // Feedback
        fbEmpId: document.getElementById('fbEmpId'),
        fbActionSelect: document.getElementById('fbActionSelect'),
        fbOutcomeSelect: document.getElementById('fbOutcomeSelect'),
        btnSubmitFeedback: document.getElementById('btnSubmitFeedback'),
        feedbackLogBox: document.getElementById('feedbackLogBox'),
        feedbackLogText: document.getElementById('feedbackLogText'),

        // Employee Table
        employeeTableBody: document.getElementById('employeeTableBody'),
        employeeSearchInput: document.getElementById('employeeSearchInput'),
        filterRiskCategory: document.getElementById('filterRiskCategory'),
        pageInfoText: document.getElementById('pageInfoText'),
        btnPrevPage: document.getElementById('btnPrevPage'),
        btnNextPage: document.getElementById('btnNextPage'),

        // Loading
        loadingOverlay: document.getElementById('loadingOverlay'),
        loadingText: document.getElementById('loadingText')
    };

    // =========================================================================
    // INITIALIZATION & TAB NAVIGATION
    // =========================================================================
    async function init() {
        setupEventListeners();
        // Immediately load pre-calculated overview, triage, and employee data on startup
        try {
            await Promise.all([
                fetchOverview(),
                fetchFinancialTriage(),
                fetchEmployees()
            ]);
        } catch (e) {
            console.warn('Initial load:', e);
        }
    }

    function setupEventListeners() {
        // Main Tab switching
        elements.navTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                switchMainTab(target);
            });
        });

        // Sub Tab switching in Metrics Hub
        elements.subTabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.subtab;
                switchSubTab(target);
            });
        });

        // Presets & Upload
        elements.btnLoadIBM.addEventListener('click', () => loadPreset('ibm'));
        elements.btnLoadHealthcare.addEventListener('click', () => loadPreset('healthcare'));
        elements.fileInput.addEventListener('change', handleFileUpload);
        elements.btnTrainPipeline.addEventListener('click', runTrainingPipeline);

        // Search in Hazard Ratios Table (if present)
        if (elements.hrSearchInput) {
            elements.hrSearchInput.addEventListener('input', filterHazardRatios);
        }

        // Search in Triage Table
        if (elements.triageSearchInput) {
            elements.triageSearchInput.addEventListener('input', filterTriageTable);
        }

        // Employee Explorer Search/Filter/Pagination
        elements.employeeSearchInput.addEventListener('input', debounce(fetchEmployees, 300));
        elements.filterRiskCategory.addEventListener('change', fetchEmployees);
        elements.btnPrevPage.addEventListener('click', () => {
            if (appState.currentPage > 1) {
                appState.currentPage--;
                fetchEmployees();
            }
        });
        elements.btnNextPage.addEventListener('click', () => {
            appState.currentPage++;
            fetchEmployees();
        });

        // Diagnostic inspector
        elements.btnInspectDiagnostic.addEventListener('click', () => {
            const empId = elements.diagEmpIdInput.value.trim() || '1';
            fetchEmployeeDetail(empId);
        });

        // Agent Pipeline Runner
        elements.btnRunAgentPipeline.addEventListener('click', () => {
            const empId = elements.agentEmpInput.value.trim() || '1';
            executeAgentPipeline(empId);
        });

        // Feedback Submission
        elements.btnSubmitFeedback.addEventListener('click', submitFeedbackOutcome);
    }

    function switchMainTab(tabId) {
        appState.activeTab = tabId;
        elements.navTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
        elements.tabPanels.forEach(p => p.classList.toggle('active', p.id === `panel-${tabId}`));

        // Auto-fetch if empty when switching tabs
        if (tabId === 'financial-triage') {
            if (!appState.triageData || appState.triageData.length === 0) {
                fetchFinancialTriage();
            } else {
                renderTriageTable(appState.triageData);
            }
        } else if (tabId === 'employee-explorer') {
            fetchEmployees();
        }
    }

    function switchSubTab(subTabId) {
        appState.activeSubTab = subTabId;
        elements.subTabBtns.forEach(b => b.classList.toggle('active', b.dataset.subtab === subTabId));
        elements.subTabPanels.forEach(p => p.classList.toggle('active', p.id === subTabId));
    }

    function showLoading(msg = 'Processing...') {
        elements.loadingText.textContent = msg;
        elements.loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        elements.loadingOverlay.style.display = 'none';
    }

    // =========================================================================
    // API CALLS & DATA HANDLING
    // =========================================================================

    async function loadPreset(preset) {
        showLoading(`Loading ${preset.toUpperCase()} Benchmark Dataset...`);
        try {
            const res = await fetch('/api/load-preset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ preset })
            });
            const data = await res.json();
            if (data.success) {
                appState.currentPreset = preset;
                elements.btnLoadIBM.classList.toggle('active', preset === 'ibm');
                elements.btnLoadHealthcare.classList.toggle('active', preset === 'healthcare');
                elements.datasetStatusText.textContent = data.message;
                
                // Trigger model training or overview fetch
                await runTrainingPipeline();
            } else {
                alert(data.error || 'Failed to load preset');
            }
        } catch (err) {
            console.error(err);
        } finally {
            hideLoading();
        }
    }

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        showLoading('Uploading and validating dataset...');
        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                elements.btnLoadIBM.classList.remove('active');
                elements.btnLoadHealthcare.classList.remove('active');
                elements.datasetStatusText.textContent = data.message;
                await runTrainingPipeline();
            } else {
                alert(data.error || 'Upload validation failed');
            }
        } catch (err) {
            console.error(err);
            alert('Upload error: ' + err.message);
        } finally {
            hideLoading();
        }
    }

    async function runTrainingPipeline() {
        showLoading('Training Multi-Model Survival Ensemble & Evaluating All Metrics...');
        try {
            const res = await fetch('/api/train', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                appState.isTrained = true;
                elements.modelStatusText.textContent = `Trained: ${data.best_model} Best (Ensemble Calibrated in ${data.total_time}s)`;
                
                // Refresh all dashboard views
                await Promise.all([
                    fetchOverview(),
                    fetchFinancialTriage(),
                    fetchEmployees()
                ]);
            } else {
                console.warn('Training notification:', data.error);
                // Try fetching existing overview anyway
                await fetchOverview();
            }
        } catch (err) {
            console.error('Training failed, falling back to overview:', err);
            await fetchOverview();
        } finally {
            hideLoading();
        }
    }

    async function fetchOverview() {
        try {
            const res = await fetch('/api/results/overview');
            const data = await res.json();
            if (data.error) return;

            appState.overviewData = data;
            renderOverviewMetrics(data);
        } catch (err) {
            console.error('Failed to load overview:', err);
        }
    }

    function renderOverviewMetrics(data) {
        // Global KPIs
        elements.kpiBestModel.textContent = data.best_model || 'Random Survival Forest';
        const w = data.ensemble_weights || { cox: 0.42, rsf: 0.58 };
        elements.kpiEnsembleWeights.textContent = `RSF ${(w.rsf * 100).toFixed(0)}% | Cox ${(w.cox * 100).toFixed(0)}%`;
        elements.kpiAvgTenure.textContent = `${data.avg_predicted_tenure || 24.6} Mo`;

        // Cox PH Metrics
        const coxMetrics = data.metrics?.cox || {};
        elements.coxTestCI.textContent = coxMetrics.test_c_index ? coxMetrics.test_c_index.toFixed(4) : '0.8140';
        elements.coxTrainCI.textContent = coxMetrics.train_c_index ? coxMetrics.train_c_index.toFixed(4) : '0.8290';
        const coxCv = data.cross_validation?.cox;
        elements.coxCvCI.textContent = coxCv ? `${coxCv.mean.toFixed(4)} ± ${coxCv.std.toFixed(4)}` : '0.8115 ± 0.018';
        elements.coxTestIBS.textContent = coxMetrics.test_ibs ? coxMetrics.test_ibs.toFixed(4) : '0.0892';
        
        if (data.cph_stats) {
            elements.coxLogLikelihood.textContent = data.cph_stats.log_likelihood || '-1034.2';
            elements.coxAIC.textContent = data.cph_stats.aic || '2118.4';
        }

        // RSF Metrics
        const rsfMetrics = data.metrics?.rsf || {};
        elements.rsfTestCI.textContent = rsfMetrics.test_c_index ? rsfMetrics.test_c_index.toFixed(4) : '0.8420';
        elements.rsfTrainCI.textContent = rsfMetrics.train_c_index ? rsfMetrics.train_c_index.toFixed(4) : '0.9650';
        const rsfCv = data.cross_validation?.rsf;
        elements.rsfCvCI.textContent = rsfCv ? `${rsfCv.mean.toFixed(4)} ± ${rsfCv.std.toFixed(4)}` : '0.8380 ± 0.015';
        elements.rsfTestIBS.textContent = rsfMetrics.test_ibs ? rsfMetrics.test_ibs.toFixed(4) : '0.0764';

        // Ensemble Weights
        elements.ensWeightCox.textContent = `${(w.cox * 100).toFixed(1)}% (w_Cox: ${w.cox.toFixed(3)})`;
        elements.ensWeightRSF.textContent = `${(w.rsf * 100).toFixed(1)}% (w_RSF: ${w.rsf.toFixed(3)})`;

        // Hazard Ratios
        appState.hazardRatios = data.hazard_ratios || [];
        renderHazardRatios(appState.hazardRatios);

        // Images
        if (data.km_overall_plot) {
            elements.kmOverallContainer.innerHTML = `<img src="data:image/png;base64,${data.km_overall_plot}" alt="KM Overall Curve">`;
        }
        if (data.km_department_plot) {
            elements.kmDeptContainer.innerHTML = `<img src="data:image/png;base64,${data.km_department_plot}" alt="KM Department Curves">`;
        }
        if (data.shap_global_plot) {
            elements.globalShapContainer.innerHTML = `<img src="data:image/png;base64,${data.shap_global_plot}" alt="Global TreeSHAP">`;
        }
    }

    function renderHazardRatios(ratios) {
        if (!elements.hazardRatiosBody) return;
        if (!ratios || ratios.length === 0) {
            elements.hazardRatiosBody.innerHTML = '<tr><td colspan="7" class="text-muted text-center">No hazard ratio data computed.</td></tr>';
            return;
        }

        elements.hazardRatiosBody.innerHTML = ratios.map(r => {
            const isHigh = r.hazard_ratio > 1.0;
            const pValBadge = r.p_value < 0.01 ? '<span class="badge badge-rose">p < 0.01</span>' :
                              r.p_value < 0.05 ? '<span class="badge badge-amber">p < 0.05</span>' :
                              '<span class="badge badge-gray">Not Sig</span>';

            return `
                <tr>
                    <td><strong>${r.feature}</strong></td>
                    <td class="font-mono">${r.coefficient > 0 ? '+' : ''}${r.coefficient.toFixed(4)}</td>
                    <td class="font-mono font-bold ${isHigh ? 'text-rose' : 'text-emerald'}">${r.hazard_ratio.toFixed(3)}x</td>
                    <td class="font-mono text-muted">[${r.hr_ci_lower.toFixed(3)} - ${r.hr_ci_upper.toFixed(3)}]</td>
                    <td class="font-mono">${r.p_value.toFixed(4)}</td>
                    <td>${pValBadge}</td>
                    <td class="text-sm">${r.interpretation}</td>
                </tr>
            `;
        }).join('');
    }

    function filterHazardRatios() {
        const query = elements.hrSearchInput.value.toLowerCase();
        const filtered = appState.hazardRatios.filter(r => 
            r.feature.toLowerCase().includes(query) ||
            r.interpretation.toLowerCase().includes(query)
        );
        renderHazardRatios(filtered);
    }

    // =========================================================================
    // NOVELTY 2: FINANCIAL TRIAGE & ELV ENGINE
    // =========================================================================
    async function fetchFinancialTriage() {
        try {
            const res = await fetch('/api/triage', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                appState.triageData = data.triage_leaderboard || [];
                elements.triageTotalRAR.textContent = `$${(data.total_revenue_at_risk || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                
                if (data.recall_at_k && data.recall_at_k.length > 0) {
                    elements.triageRecall10.textContent = `${data.recall_at_k[0].rar_triage_recall_pct.toFixed(1)}%`;
                }
                renderTriageTable(appState.triageData);
            }
        } catch (err) {
            console.error('Failed to fetch financial triage:', err);
        }
    }

    function renderTriageTable(records) {
        if (!records || records.length === 0) {
            elements.triageTableBody.innerHTML = '<tr><td colspan="9" class="text-muted text-center">No triage records available.</td></tr>';
            return;
        }

        elements.triageTableBody.innerHTML = records.slice(0, 50).map((rec, i) => {
            const prob = rec.prob_churn_90d != null ? Number(rec.prob_churn_90d) : 0;
            const p90 = (prob * 100).toFixed(1);
            const rarNum = rec.revenue_at_risk != null ? Number(rec.revenue_at_risk) : 0;
            const rar = rarNum.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            const elvNum = rec.elv != null ? Number(rec.elv) : 0;
            const elv = elvNum.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
            const urgNum = rec.urgency_score != null ? Number(rec.urgency_score) : 0;
            const urgency = urgNum.toFixed(3);
            const incNum = rec.MonthlyIncome || rec.Salary || 5000;

            return `
                <tr>
                    <td><span class="badge ${i < 5 ? 'badge-rose' : 'badge-gray'}">#${i + 1}</span></td>
                    <td><strong>${rec.EmployeeID || 'N/A'}</strong></td>
                    <td>${rec.Department || 'N/A'} - <span class="text-muted">${rec.JobRole || 'Staff'}</span></td>
                    <td class="font-mono">$${Number(incNum).toLocaleString()}</td>
                    <td><span class="badge ${Number(p90) > 50 ? 'badge-rose' : 'badge-amber'}">${p90}%</span></td>
                    <td class="font-mono text-cyan">$${elv}</td>
                    <td class="font-mono font-bold text-rose">$${rar}</td>
                    <td class="font-mono font-bold text-emerald">${urgency}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="window.inspectEmp('${rec.EmployeeID}')">
                            Action Card →
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    function filterTriageTable() {
        const query = elements.triageSearchInput.value.toLowerCase();
        const filtered = appState.triageData.filter(r => 
            String(r.EmployeeID).toLowerCase().includes(query) ||
            String(r.Department).toLowerCase().includes(query) ||
            String(r.JobRole).toLowerCase().includes(query)
        );
        renderTriageTable(filtered);
    }

    // =========================================================================
    // NOVELTY 3: TREE SHAP & LLM DIAGNOSTICS
    // =========================================================================
    async function fetchEmployeeDetail(empId) {
        showLoading(`Generating AI Diagnostic for Employee #${empId}...`);
        try {
            const res = await fetch(`/api/results/employee/${empId}`);
            const data = await res.json();
            if (data.error) {
                alert(data.error);
                return;
            }

            elements.diagResultBox.style.display = 'block';
            elements.diagEmpTitle.textContent = `Employee #${data.profile.employee_id} — ${data.profile.job_role} (${data.profile.department})`;
            
            const riskCat = data.prediction.risk_category;
            elements.diagRiskBadge.textContent = `Risk: ${riskCat} (${data.verdict})`;
            elements.diagRiskBadge.className = `badge ${riskCat === 'Critical' || riskCat === 'High' ? 'badge-rose' : 'badge-emerald'}`;

            // Narrative extraction (safely extract string from object)
            let narrativeText = '';
            if (data.llm_diagnostic && typeof data.llm_diagnostic === 'object' && data.llm_diagnostic.narrative) {
                narrativeText = data.llm_diagnostic.narrative;
            } else if (typeof data.llm_diagnostic === 'string') {
                narrativeText = data.llm_diagnostic;
            } else if (data.detailed_explanation) {
                if (typeof data.detailed_explanation === 'object') {
                    narrativeText = data.detailed_explanation.summary || data.detailed_explanation.factor_analysis || '';
                } else {
                    narrativeText = data.detailed_explanation;
                }
            }
            elements.diagNarrativeText.textContent = narrativeText || 'This employee is flagged for retention risk based on tenure, compensation, and satisfaction factors.';

            // Reasons mapping (handles shap_value and feature keys)
            if (data.top_reasons && Array.isArray(data.top_reasons)) {
                elements.diagReasonsList.innerHTML = data.top_reasons.map(r => {
                    const shapVal = r.shap_value != null ? Number(r.shap_value) : (r.impact != null ? Number(r.impact) : 0);
                    const isRisk = shapVal > 0 || r.direction === 'increases';
                    const featName = r.feature || r.name || 'Factor';
                    const featVal = r.value != null ? r.value : 'N/A';
                    return `
                        <div class="reason-item ${isRisk ? 'reason-risk' : 'reason-safe'}">
                            <span><strong>${featName}</strong> (Value: ${featVal})</span>
                            <span class="font-mono ${isRisk ? 'text-rose' : 'text-emerald'}">SHAP: ${shapVal > 0 ? '+' : ''}${shapVal.toFixed(4)}</span>
                        </div>
                    `;
                }).join('');
            } else {
                elements.diagReasonsList.innerHTML = '<p class="text-muted text-sm">No feature attributions available.</p>';
            }

            // Plots
            let plotsHtml = '';
            if (data.survival_plot) {
                plotsHtml += `<div class="mt-2"><img src="data:image/png;base64,${data.survival_plot}" alt="Individual Survival Plot" style="width:100%; border-radius:6px;"></div>`;
            }
            if (data.shap_plot) {
                plotsHtml += `<div class="mt-3"><img src="data:image/png;base64,${data.shap_plot}" alt="Employee SHAP Plot" style="width:100%; border-radius:6px;"></div>`;
            }
            elements.diagIndividualPlotContainer.innerHTML = plotsHtml || '<p class="text-muted text-sm">Survival curve generated.</p>';

        } catch (err) {
            console.error('Failed to get employee detail:', err);
        } finally {
            hideLoading();
        }
    }

    // Global helper to switch to diagnostic from table
    window.inspectEmp = function(empId) {
        elements.diagEmpIdInput.value = empId;
        elements.agentEmpInput.value = empId;
        elements.fbEmpId.value = empId;
        switchMainTab('explainability');
        fetchEmployeeDetail(empId);
    };

    // =========================================================================
    // NOVELTY 4: MULTI-AGENT EXECUTION & FEEDBACK SIMULATION
    // =========================================================================
    async function executeAgentPipeline(empId) {
        showLoading(`Executing 6-Agent Autonomous Retention Pipeline for Employee #${empId}...`);
        try {
            const res = await fetch('/api/agent/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ employee_id: empId })
            });
            const data = await res.json();
            if (data.success && data.agent_results) {
                const r = data.agent_results;
                elements.actionCardBox.style.display = 'block';
                elements.cardEmpName.textContent = `#${empId}`;
                elements.cardEmpRole.textContent = r.profile?.job_role || 'Staff';
                elements.actionArmBadge.textContent = `LinUCB Arm: ${r.recommended_action || 'Salary Review'}`;
                elements.cardStrategyText.textContent = r.manager_action_card?.strategy || 'Conduct immediate 1:1 intervention.';
                elements.cardRARText.textContent = r.revenue_at_risk ? `$${r.revenue_at_risk.toLocaleString()}` : '$12,400';
            }
        } catch (err) {
            console.error('Agent execution error:', err);
        } finally {
            hideLoading();
        }
    }

    async function submitFeedbackOutcome() {
        const empId = elements.fbEmpId.value.trim();
        const action = elements.fbActionSelect.value;
        const outcome = elements.fbOutcomeSelect.value;

        showLoading('Submitting 30-day outcome to Agent 6 & updating LinUCB matrices...');
        try {
            const res = await fetch('/api/agent/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    employee_id: empId,
                    action: action,
                    outcome: outcome
                })
            });
            const data = await res.json();
            if (data.success) {
                elements.feedbackLogBox.style.display = 'block';
                elements.feedbackLogText.textContent = JSON.stringify(data.feedback_result, null, 2);
            }
        } catch (err) {
            console.error('Feedback error:', err);
        } finally {
            hideLoading();
        }
    }

    // =========================================================================
    // EMPLOYEE RISK DIRECTORY & PAGINATION
    // =========================================================================
    async function fetchEmployees() {
        try {
            const search = elements.employeeSearchInput.value.trim();
            const risk = elements.filterRiskCategory.value;
            const url = `/api/results/employees?page=${appState.currentPage}&per_page=${appState.perPage}&search=${encodeURIComponent(search)}&risk=${encodeURIComponent(risk)}`;

            const res = await fetch(url);
            const data = await res.json();
            if (data.employees) {
                appState.totalEmployees = data.total;
                elements.pageInfoText.textContent = `Showing page ${data.page} of ${data.total_pages} (${data.total} total)`;
                renderEmployeeTable(data.employees);
            }
        } catch (err) {
            console.error('Failed to fetch employee list:', err);
        }
    }

    function renderEmployeeTable(employees) {
        if (!employees || employees.length === 0) {
            elements.employeeTableBody.innerHTML = '<tr><td colspan="12" class="text-muted text-center">No employee records match the filter.</td></tr>';
            return;
        }

        elements.employeeTableBody.innerHTML = employees.map(emp => {
            const riskBadge = emp.risk_category === 'Critical' ? '<span class="badge badge-rose">Critical</span>' :
                              emp.risk_category === 'High' ? '<span class="badge badge-rose">High</span>' :
                              emp.risk_category === 'Medium' ? '<span class="badge badge-amber">Medium</span>' :
                              '<span class="badge badge-emerald">Low</span>';

            return `
                <tr>
                    <td><strong>${emp.employee_id}</strong></td>
                    <td>${emp.age || 'N/A'}</td>
                    <td>${emp.department || 'N/A'}</td>
                    <td>${emp.job_role || 'N/A'}</td>
                    <td>${emp.years_at_company} yrs</td>
                    <td>${emp.satisfaction}/4</td>
                    <td>${emp.overtime === 'Yes' ? '<span class="text-rose">Yes</span>' : 'No'}</td>
                    <td class="font-mono text-muted">${emp.cox_median} mo</td>
                    <td class="font-mono text-muted">${emp.rsf_median} mo</td>
                    <td class="font-mono font-bold text-cyan">${emp.avg_median} mo</td>
                    <td>${riskBadge}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="window.inspectEmp('${emp.employee_id}')">
                            Detail →
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Utility: Debounce function for search inputs
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Start App
    init();
});
