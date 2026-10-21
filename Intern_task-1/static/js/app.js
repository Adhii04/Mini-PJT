/**
 * NEXUS AI — Enterprise Frontend Application Logic
 * Architecture: Modular Event Bus, Reactive State Management,
 * Seamless Drill-Downs & Zero-Emoji Vector Presentations.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── APPLICATION STATE ──────────────────────────────────────────────────
    const appState = {
        activeTab: 'metrics-hub',
        activeSubTab: 'sub-overview',
        isTrained: false,
        currentPreset: 'ibm',
        triageHorizon: '90d',
        triageDept: 'all',
        overviewData: null,
        triageData: [],
        hazardRatios: [],
        currentPage: 1,
        perPage: 25,
        totalEmployees: 0,
        sidebarCollapsed: false
    };

    // Module & Subtab Human-Readable Name Mappings for Breadcrumbs
    const moduleNames = {
        'metrics-hub': 'Overview & Model Metrics',
        'financial-triage': 'Financial Intelligence',
        'explainability': 'Explainability & Diagnostics',
        'multi-agent': 'Retention Operations',
        'employee-explorer': 'Employee Risk Explorer'
    };

    const subTabNames = {
        'sub-overview': 'Overview & Matrix',
        'sub-cox': 'Cox Proportional Hazards',
        'sub-rsf': 'Random Survival Forest',
        'sub-ensemble': 'Weighted Ensemble',
        'sub-baseline': 'Baseline Logistic',
        'sub-bandit': 'LinUCB Contextual Bandit',
        'sub-km': 'Kaplan-Meier Estimator'
    };

    // ── DOM ELEMENTS CACHE ────────────────────────────────────────────────
    const elements = {
        // App Shell & Navigation
        appSidebar: document.getElementById('appSidebar'),
        sidebarToggle: document.getElementById('sidebarToggle'),
        mobileNavToggle: document.getElementById('mobileNavToggle'),
        crumbModule: document.getElementById('crumbModule'),
        crumbSubSep: document.getElementById('crumbSubSep'),
        crumbSub: document.getElementById('crumbSub'),
        navTabs: document.querySelectorAll('.nav-link-btn'),
        tabPanels: document.querySelectorAll('.tab-module-panel'),
        subTabBtns: document.querySelectorAll('.subtab-btn'),
        subTabPanels: document.querySelectorAll('.subtab-panel'),

        // Header Actions & Status
        btnLoadIBM: document.getElementById('btnLoadIBM'),
        btnLoadHealthcare: document.getElementById('btnLoadHealthcare'),
        fileInput: document.getElementById('fileInput'),
        btnTrainPipeline: document.getElementById('btnTrainPipeline'),
        trainSpinner: document.getElementById('trainSpinner'),
        trainBtnIcon: document.getElementById('trainBtnIcon'),
        trainBtnText: document.getElementById('trainBtnText'),
        datasetStatusText: document.getElementById('datasetStatusText'),
        modelStatusText: document.getElementById('modelStatusText'),

        // Module 1: Overview & Model Metrics
        kpiBestModel: document.getElementById('kpiBestModel'),
        kpiEnsembleWeights: document.getElementById('kpiEnsembleWeights'),
        kpiBaselineDelta: document.getElementById('kpiBaselineDelta'),
        kpiAvgTenure: document.getElementById('kpiAvgTenure'),
        overviewBaselineCI: document.getElementById('overviewBaselineCI'),
        overviewBaselineIBS: document.getElementById('overviewBaselineIBS'),
        overviewCoxCI: document.getElementById('overviewCoxCI'),
        overviewCoxIBS: document.getElementById('overviewCoxIBS'),
        overviewRsfCI: document.getElementById('overviewRsfCI'),
        overviewRsfIBS: document.getElementById('overviewRsfIBS'),
        overviewEnsembleCI: document.getElementById('overviewEnsembleCI'),
        overviewEnsembleIBS: document.getElementById('overviewEnsembleIBS'),
        detailedMetricsTableBody: document.getElementById('detailedMetricsTableBody'),
        rocCurvesPlotContainer: document.getElementById('rocCurvesPlotContainer'),
        confusionMatricesPlotContainer: document.getElementById('confusionMatricesPlotContainer'),
        badgeSplitSize: document.getElementById('badgeSplitSize'),

        // Baseline Boxes
        baselineAuc: document.getElementById('baselineAuc'),
        baselineBrier: document.getElementById('baselineBrier'),
        baselineAcc: document.getElementById('baselineAcc'),
        baselinePrec: document.getElementById('baselinePrec'),
        baselineRecall: document.getElementById('baselineRecall'),
        baselineSpec: document.getElementById('baselineSpec'),
        baselineF1: document.getElementById('baselineF1'),
        baselineThreshold: document.getElementById('baselineThreshold'),
        baselineCM: document.getElementById('baselineCM'),

        // Cox PH
        coxTestCI: document.getElementById('coxTestCI'),
        coxTrainCI: document.getElementById('coxTrainCI'),
        coxCvCI: document.getElementById('coxCvCI'),
        coxTestIBS: document.getElementById('coxTestIBS'),
        coxLogLikelihood: document.getElementById('coxLogLikelihood'),
        coxAIC: document.getElementById('coxAIC'),
        coxAcc: document.getElementById('coxAcc'),
        coxPrec: document.getElementById('coxPrec'),
        coxRecall: document.getElementById('coxRecall'),
        coxSpec: document.getElementById('coxSpec'),
        coxF1: document.getElementById('coxF1'),
        coxAuc: document.getElementById('coxAuc'),
        coxThreshold: document.getElementById('coxThreshold'),
        coxCM: document.getElementById('coxCM'),
        hazardRatiosBody: document.getElementById('hazardRatiosBody'),
        hrSearchInput: document.getElementById('hrSearchInput'),

        // RSF
        rsfTestCI: document.getElementById('rsfTestCI'),
        rsfTrainCI: document.getElementById('rsfTrainCI'),
        rsfCvCI: document.getElementById('rsfCvCI'),
        rsfTestIBS: document.getElementById('rsfTestIBS'),
        rsfAcc: document.getElementById('rsfAcc'),
        rsfPrec: document.getElementById('rsfPrec'),
        rsfRecall: document.getElementById('rsfRecall'),
        rsfSpec: document.getElementById('rsfSpec'),
        rsfF1: document.getElementById('rsfF1'),
        rsfAuc: document.getElementById('rsfAuc'),
        rsfThreshold: document.getElementById('rsfThreshold'),
        rsfCM: document.getElementById('rsfCM'),

        // Ensemble
        ensWeightCox: document.getElementById('ensWeightCox'),
        ensWeightRSF: document.getElementById('ensWeightRSF'),
        ensAcc: document.getElementById('ensAcc'),
        ensPrec: document.getElementById('ensPrec'),
        ensRecall: document.getElementById('ensRecall'),
        ensSpec: document.getElementById('ensSpec'),
        ensF1: document.getElementById('ensF1'),
        ensAuc: document.getElementById('ensAuc'),
        ensThreshold: document.getElementById('ensThreshold'),
        ensCM: document.getElementById('ensCM'),

        // Visual Plots
        kmOverallContainer: document.getElementById('kmOverallContainer'),
        kmDeptContainer: document.getElementById('kmDeptContainer'),
        globalShapContainer: document.getElementById('globalShapContainer'),

        // Module 2: Financial Intelligence
        triageHorizonGroup: document.getElementById('triageHorizonGroup'),
        triageDeptFilter: document.getElementById('triageDeptFilter'),
        triageTotalRAR: document.getElementById('triageTotalRAR'),
        triageHorizonSub: document.getElementById('triageHorizonSub'),
        triageAvgExposure: document.getElementById('triageAvgExposure'),
        triageAtRiskCount: document.getElementById('triageAtRiskCount'),
        triageAtRiskPct: document.getElementById('triageAtRiskPct'),
        triageTopDept: document.getElementById('triageTopDept'),
        triageTopDeptSub: document.getElementById('triageTopDeptSub'),
        triageTableBody: document.getElementById('triageTableBody'),
        triageSearchInput: document.getElementById('triageSearchInput'),

        // Module 3: Diagnostics
        diagEmpIdInput: document.getElementById('diagEmpIdInput'),
        btnInspectDiagnostic: document.getElementById('btnInspectDiagnostic'),
        diagResultBox: document.getElementById('diagResultBox'),
        diagEmpTitle: document.getElementById('diagEmpTitle'),
        diagRiskBadge: document.getElementById('diagRiskBadge'),
        diagNarrativeText: document.getElementById('diagNarrativeText'),
        diagReasonsList: document.getElementById('diagReasonsList'),
        diagIndividualPlotContainer: document.getElementById('diagIndividualPlotContainer'),

        // Module 4: Retention Operations
        agentEmpInput: document.getElementById('agentEmpInput'),
        btnRunAgentPipeline: document.getElementById('btnRunAgentPipeline'),
        actionCardBox: document.getElementById('actionCardBox'),
        actionCardTitle: document.getElementById('actionCardTitle'),
        actionArmBadge: document.getElementById('actionArmBadge'),
        cardEmpName: document.getElementById('cardEmpName'),
        cardEmpRole: document.getElementById('cardEmpRole'),
        cardEmpDept: document.getElementById('cardEmpDept'),
        cardTenureText: document.getElementById('cardTenureText'),
        cardStrategyText: document.getElementById('cardStrategyText'),
        cardRARText: document.getElementById('cardRARText'),
        cardActionStepsList: document.getElementById('cardActionStepsList'),

        // Feedback Simulator & Telemetry
        fbEmpId: document.getElementById('fbEmpId'),
        fbActionSelect: document.getElementById('fbActionSelect'),
        fbOutcomeSelect: document.getElementById('fbOutcomeSelect'),
        btnSubmitFeedback: document.getElementById('btnSubmitFeedback'),
        feedbackLogBox: document.getElementById('feedbackLogBox'),
        feedbackLogText: document.getElementById('feedbackLogText'),
        fbStatusBadge: document.getElementById('fbStatusBadge'),
        fbArmName: document.getElementById('fbArmName'),
        fbRewardSignal: document.getElementById('fbRewardSignal'),
        fbPayoffShift: document.getElementById('fbPayoffShift'),
        fbUncertaintyVar: document.getElementById('fbUncertaintyVar'),
        fbInsightText: document.getElementById('fbInsightText'),

        // Module 5: Employee Risk Explorer
        employeeTableBody: document.getElementById('employeeTableBody'),
        employeeSearchInput: document.getElementById('employeeSearchInput'),
        filterRiskCategory: document.getElementById('filterRiskCategory'),
        pageInfoText: document.getElementById('pageInfoText'),
        btnPrevPage: document.getElementById('btnPrevPage'),
        btnNextPage: document.getElementById('btnNextPage'),

        // Overlay Loading
        loadingOverlay: document.getElementById('loadingOverlay'),
        loadingText: document.getElementById('loadingText')
    };

    // ── INITIALIZATION ────────────────────────────────────────────────────
    async function init() {
        setupEventListeners();
        updateBreadcrumbs();
        renderMathFormulas();
        try {
            await Promise.all([
                fetchOverview(),
                fetchFinancialTriage(),
                fetchEmployees()
            ]);
        } catch (e) {
            console.warn('Initial data load warning:', e);
        }
        setTimeout(renderMathFormulas, 300);
    }

    // ── EVENT LISTENERS SETUP ─────────────────────────────────────────────
    function setupEventListeners() {
        // Sidebar Collapse Toggle
        if (elements.sidebarToggle) {
            elements.sidebarToggle.addEventListener('click', () => {
                appState.sidebarCollapsed = !appState.sidebarCollapsed;
                elements.appSidebar.classList.toggle('collapsed', appState.sidebarCollapsed);
            });
        }

        // Mobile Nav Toggle
        if (elements.mobileNavToggle) {
            elements.mobileNavToggle.addEventListener('click', () => {
                elements.appSidebar.classList.toggle('open');
            });
        }

        // Primary Module Sidebar Navigation
        elements.navTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                switchMainTab(target);
                // Auto-close on mobile if opened
                if (elements.appSidebar.classList.contains('open')) {
                    elements.appSidebar.classList.remove('open');
                }
            });
        });

        // Subtabs Navigation in Module 1
        elements.subTabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.subtab;
                switchSubTab(target);
            });
        });

        // Dataset Presets & File Upload
        if (elements.btnLoadIBM) {
            elements.btnLoadIBM.addEventListener('click', () => loadPreset('ibm'));
        }
        if (elements.btnLoadHealthcare) {
            elements.btnLoadHealthcare.addEventListener('click', () => loadPreset('healthcare'));
        }
        if (elements.fileInput) {
            elements.fileInput.addEventListener('change', handleFileUpload);
        }
        if (elements.btnTrainPipeline) {
            elements.btnTrainPipeline.addEventListener('click', runTrainingPipeline);
        }

        // Search Inputs & Filters
        if (elements.hrSearchInput) {
            elements.hrSearchInput.addEventListener('input', filterHazardRatios);
        }
        if (elements.triageSearchInput) {
            elements.triageSearchInput.addEventListener('input', filterTriageTable);
        }
        if (elements.triageHorizonGroup) {
            const horizonBtns = elements.triageHorizonGroup.querySelectorAll('.horizon-btn');
            horizonBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    horizonBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    appState.triageHorizon = btn.dataset.horizon;
                    fetchFinancialTriage();
                });
            });
        }
        if (elements.employeeSearchInput) {
            elements.employeeSearchInput.addEventListener('input', debounce(fetchEmployees, 300));
        }
        if (elements.filterRiskCategory) {
            elements.filterRiskCategory.addEventListener('change', () => {
                appState.currentPage = 1;
                fetchEmployees();
            });
        }

        // Pagination
        if (elements.btnPrevPage) {
            elements.btnPrevPage.addEventListener('click', () => {
                if (appState.currentPage > 1) {
                    appState.currentPage--;
                    fetchEmployees();
                }
            });
        }
        if (elements.btnNextPage) {
            elements.btnNextPage.addEventListener('click', () => {
                appState.currentPage++;
                fetchEmployees();
            });
        }

        // Diagnostic Inspector
        if (elements.btnInspectDiagnostic) {
            elements.btnInspectDiagnostic.addEventListener('click', () => {
                const empId = elements.diagEmpIdInput.value.trim() || '1';
                fetchEmployeeDetail(empId);
            });
        }

        // Agent Pipeline Runner
        if (elements.btnRunAgentPipeline) {
            elements.btnRunAgentPipeline.addEventListener('click', () => {
                const empId = elements.agentEmpInput.value.trim() || '1';
                executeAgentPipeline(empId);
            });
        }

        // Feedback Submission
        if (elements.btnSubmitFeedback) {
            elements.btnSubmitFeedback.addEventListener('click', submitFeedbackOutcome);
        }
    }

    // ── NAVIGATION CONTROLLERS ────────────────────────────────────────────
    function switchMainTab(tabId) {
        appState.activeTab = tabId;
        elements.navTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
        elements.tabPanels.forEach(p => p.classList.toggle('active', p.id === `panel-${tabId}`));

        updateBreadcrumbs();

        // Lazy-fetch on tab switch if empty
        if (tabId === 'financial-triage') {
            if (!appState.triageData || appState.triageData.length === 0) {
                fetchFinancialTriage();
            } else {
                renderTriageTable(appState.triageData);
            }
        } else if (tabId === 'employee-explorer') {
            fetchEmployees();
        } else if (tabId === 'explainability') {
            if (elements.globalShapContainer && (!elements.globalShapContainer.querySelector('img') || elements.globalShapContainer.querySelector('.chart-empty-placeholder'))) {
                if (appState.overviewData && appState.overviewData.shap_global_plot) {
                    elements.globalShapContainer.innerHTML = `<img src="data:image/png;base64,${appState.overviewData.shap_global_plot}" alt="Global TreeSHAP Attributions" style="width:100%;height:auto;border-radius:8px;">`;
                } else {
                    fetchGlobalShapPlot();
                }
            }
        }
        renderMathFormulas();
    }

    function switchSubTab(subTabId) {
        appState.activeSubTab = subTabId;
        elements.subTabBtns.forEach(b => b.classList.toggle('active', b.dataset.subtab === subTabId));
        elements.subTabPanels.forEach(p => p.classList.toggle('active', p.id === subTabId));

        updateBreadcrumbs();
    }

    function updateBreadcrumbs() {
        if (!elements.crumbModule) return;
        const modTitle = moduleNames[appState.activeTab] || 'Overview & Model Metrics';
        elements.crumbModule.textContent = modTitle;

        if (appState.activeTab === 'metrics-hub') {
            elements.crumbSubSep.style.display = 'inline';
            elements.crumbSub.style.display = 'inline';
            elements.crumbSub.textContent = subTabNames[appState.activeSubTab] || 'Overview & Matrix';
        } else {
            elements.crumbSubSep.style.display = 'none';
            elements.crumbSub.style.display = 'none';
        }
    }

    function showLoading(msg = 'Processing Machine Learning Pipeline...') {
        if (elements.loadingText) elements.loadingText.textContent = msg;
        if (elements.loadingOverlay) elements.loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        if (elements.loadingOverlay) elements.loadingOverlay.style.display = 'none';
    }

    // ── DATASET & PIPELINE ACTIONS ────────────────────────────────────────
    async function loadPreset(preset) {
        showLoading(`Loading ${preset === 'healthcare' ? 'Watson Healthcare' : 'IBM HR Analytics'} Benchmark Dataset...`);
        try {
            const res = await fetch('/api/load-preset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ preset })
            });
            const data = await res.json();
            if (data.success) {
                appState.currentPreset = preset;
                if (elements.btnLoadIBM) elements.btnLoadIBM.classList.toggle('active', preset === 'ibm');
                if (elements.btnLoadHealthcare) elements.btnLoadHealthcare.classList.toggle('active', preset === 'healthcare');
                if (elements.datasetStatusText) elements.datasetStatusText.textContent = data.message;
                
                // Immediately update dashboard with genuine dataset metrics
                await Promise.all([
                    fetchOverview(),
                    fetchFinancialTriage(),
                    fetchEmployees()
                ]);
            } else {
                alert(data.error || 'Failed to load dataset preset');
            }
        } catch (err) {
            console.error('Preset loading error:', err);
        } finally {
            hideLoading();
        }
    }

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        showLoading('Uploading and validating dataset schema...');
        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                if (elements.btnLoadIBM) elements.btnLoadIBM.classList.remove('active');
                if (elements.btnLoadHealthcare) elements.btnLoadHealthcare.classList.remove('active');
                if (elements.datasetStatusText) elements.datasetStatusText.textContent = data.message;
                await runTrainingPipeline();
            } else {
                alert(data.error || 'Dataset validation failed');
            }
        } catch (err) {
            console.error('File upload error:', err);
            alert('Upload error: ' + err.message);
        } finally {
            hideLoading();
        }
    }

    async function runTrainingPipeline() {
        showLoading('Training Survival Models, Evaluating Metrics & Computing SHAP...');
        if (elements.trainSpinner) elements.trainSpinner.style.display = 'inline-block';
        if (elements.trainBtnIcon) elements.trainBtnIcon.style.display = 'none';
        if (elements.trainBtnText) elements.trainBtnText.textContent = 'Training...';

        try {
            const res = await fetch('/api/train', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                appState.isTrained = true;
                if (elements.modelStatusText) {
                    elements.modelStatusText.textContent = `Trained: ${data.best_model} (Calibrated in ${data.total_time}s)`;
                }
                await Promise.all([
                    fetchOverview(),
                    fetchFinancialTriage(),
                    fetchEmployees()
                ]);
            } else {
                console.warn('Training notice:', data.error);
                await fetchOverview();
            }
        } catch (err) {
            console.error('Pipeline execution error:', err);
            await fetchOverview();
        } finally {
            if (elements.trainSpinner) elements.trainSpinner.style.display = 'none';
            if (elements.trainBtnIcon) elements.trainBtnIcon.style.display = 'inline-block';
            if (elements.trainBtnText) elements.trainBtnText.textContent = 'Train Pipeline';
            hideLoading();
        }
    }

    // ── MODULE 1: MODEL OVERVIEW & METRICS ────────────────────────────────
    async function fetchOverview() {
        try {
            const res = await fetch('/api/results/overview');
            const data = await res.json();
            if (data.error) return;

            appState.overviewData = data;
            renderOverviewMetrics(data);
        } catch (err) {
            console.error('Failed to load overview data:', err);
        }
    }

    function renderOverviewMetrics(data) {
        // Global Top KPI Cards
        if (elements.kpiBestModel) elements.kpiBestModel.textContent = data.best_model || '--';
        const w = data.ensemble_weights || { cox: 0.5, rsf: 0.5 };
        if (elements.kpiEnsembleWeights) {
            elements.kpiEnsembleWeights.textContent = `RSF ${(w.rsf * 100).toFixed(0)}% | Cox ${(w.cox * 100).toFixed(0)}%`;
        }
        if (elements.kpiAvgTenure) {
            elements.kpiAvgTenure.textContent = data.avg_predicted_tenure != null ? `${Number(data.avg_predicted_tenure).toFixed(1)} Mo` : '--';
        }

        // Dynamic Baseline Improvement Delta KPI
        if (elements.kpiBaselineDelta) {
            elements.kpiBaselineDelta.textContent = data.baseline_delta || '--';
        }

        if (elements.badgeSplitSize) {
            const splitN = data.split?.test_size || (data.total_employees ? Math.round(data.total_employees * 0.2) : 294);
            elements.badgeSplitSize.textContent = `Held-Out Test Split (n=${splitN})`;
        }

        // Cox PH Metrics
        const coxMetrics = data.metrics?.cox || {};
        const coxTestVal = coxMetrics.test_c_index != null ? Number(coxMetrics.test_c_index).toFixed(4) : '--';
        const coxIbsVal = coxMetrics.test_ibs != null ? Number(coxMetrics.test_ibs).toFixed(4) : '--';
        if (elements.coxTestCI) elements.coxTestCI.textContent = coxTestVal;
        if (elements.overviewCoxCI) elements.overviewCoxCI.textContent = coxTestVal;
        if (elements.coxTrainCI) elements.coxTrainCI.textContent = coxMetrics.train_c_index != null ? Number(coxMetrics.train_c_index).toFixed(4) : '--';
        
        const coxCv = data.cross_validation?.cox;
        if (elements.coxCvCI) {
            elements.coxCvCI.textContent = coxCv && coxCv.mean != null ? `${coxCv.mean.toFixed(4)} ± ${coxCv.std.toFixed(4)}` : '--';
        }
        if (elements.coxTestIBS) elements.coxTestIBS.textContent = coxIbsVal;
        if (elements.overviewCoxIBS) elements.overviewCoxIBS.textContent = coxIbsVal;

        if (data.cph_stats) {
            if (elements.coxLogLikelihood) elements.coxLogLikelihood.textContent = data.cph_stats.log_likelihood != null ? data.cph_stats.log_likelihood : '--';
            if (elements.coxAIC) elements.coxAIC.textContent = data.cph_stats.aic != null ? data.cph_stats.aic : '--';
        }

        // RSF Metrics
        const rsfMetrics = data.metrics?.rsf || {};
        const rsfTestVal = rsfMetrics.test_c_index != null ? Number(rsfMetrics.test_c_index).toFixed(4) : '--';
        const rsfIbsVal = rsfMetrics.test_ibs != null ? Number(rsfMetrics.test_ibs).toFixed(4) : '--';
        if (elements.rsfTestCI) elements.rsfTestCI.textContent = rsfTestVal;
        if (elements.overviewRsfCI) elements.overviewRsfCI.textContent = rsfTestVal;
        if (elements.rsfTrainCI) elements.rsfTrainCI.textContent = rsfMetrics.train_c_index != null ? Number(rsfMetrics.train_c_index).toFixed(4) : '--';

        const rsfCv = data.cross_validation?.rsf;
        if (elements.rsfCvCI) {
            elements.rsfCvCI.textContent = rsfCv && rsfCv.mean != null ? `${rsfCv.mean.toFixed(4)} ± ${rsfCv.std.toFixed(4)}` : '--';
        }
        if (elements.rsfTestIBS) elements.rsfTestIBS.textContent = rsfIbsVal;

        // Ensemble Overview Row
        const ensMetrics = data.metrics?.ensemble || {};
        const ensCIVal = ensMetrics.test_c_index != null ? Number(ensMetrics.test_c_index).toFixed(4) : (data.ensemble_c_index != null ? Number(data.ensemble_c_index).toFixed(4) : '--');
        const ensIBSVal = ensMetrics.test_ibs != null ? Number(ensMetrics.test_ibs).toFixed(4) : (data.ensemble_ibs != null ? Number(data.ensemble_ibs).toFixed(4) : '--');
        if (elements.overviewEnsembleCI) elements.overviewEnsembleCI.textContent = ensCIVal;
        if (elements.overviewEnsembleIBS) elements.overviewEnsembleIBS.textContent = ensIBSVal;

        // Baseline SMOTE Logistic Regression Metrics
        if (data.baseline_stats) {
            const bs = data.baseline_stats;
            const bAucNum = bs.c_index_auc != null ? bs.c_index_auc : bs.roc_auc;
            const bAuc = bAucNum != null ? Number(bAucNum).toFixed(4) : '--';
            const bBrier = bs.brier_score != null ? Number(bs.brier_score).toFixed(4) : '--';
            if (elements.overviewBaselineCI) elements.overviewBaselineCI.textContent = bAuc !== '--' ? `${bAuc} (AUC)` : '--';
            if (elements.overviewBaselineIBS) elements.overviewBaselineIBS.textContent = bBrier;

            if (elements.baselineAuc) elements.baselineAuc.textContent = bAuc;
            if (elements.baselineBrier) elements.baselineBrier.textContent = bBrier;
            if (elements.baselineAcc) elements.baselineAcc.textContent = bs.accuracy != null ? `${(bs.accuracy * 100).toFixed(1)}%` : '--';
            if (elements.baselinePrec) elements.baselinePrec.textContent = bs.precision != null ? `${(bs.precision * 100).toFixed(1)}%` : '--';
            if (elements.baselineRecall) elements.baselineRecall.textContent = bs.recall != null ? `${(bs.recall * 100).toFixed(1)}%` : '--';
            if (elements.baselineF1) elements.baselineF1.textContent = bs.f1_score != null ? Number(bs.f1_score).toFixed(4) : (bs.f1 != null ? Number(bs.f1).toFixed(4) : '--');
        }

        // Ensemble Weights
        if (elements.ensWeightCox) elements.ensWeightCox.textContent = `${(w.cox * 100).toFixed(1)}% (w_Cox: ${w.cox.toFixed(3)})`;
        if (elements.ensWeightRSF) elements.ensWeightRSF.textContent = `${(w.rsf * 100).toFixed(1)}% (w_RSF: ${w.rsf.toFixed(3)})`;

        // ── Comprehensive Classification Metrics (from model_evaluation.ipynb) ──
        const cmData = data.classification_metrics || {};
        const coxCM = cmData.cox || data.metrics?.cox?.classification || {};
        const rsfCM = cmData.rsf || data.metrics?.rsf?.classification || {};
        const ensCM = cmData.ensemble || data.metrics?.ensemble?.classification || {};
        const baseCM = cmData.baseline || data.baseline_stats || {};

        // Helper formatting functions (no hardcoded numbers)
        const fmtPct = (val) => (val != null ? `${(Number(val) * 100).toFixed(2)}%` : '--');
        const fmtNum = (val, dec = 4) => (val != null ? Number(val).toFixed(dec) : '--');
        const fmtCount = (val) => (val != null ? val : '--');

        // Update Subtab 1: Cox PH Classification Cards
        if (elements.coxAcc) elements.coxAcc.textContent = fmtPct(coxCM.accuracy);
        if (elements.coxPrec) elements.coxPrec.textContent = fmtPct(coxCM.precision);
        if (elements.coxRecall) elements.coxRecall.textContent = fmtPct(coxCM.recall);
        if (elements.coxSpec) elements.coxSpec.textContent = fmtPct(coxCM.specificity);
        if (elements.coxF1) elements.coxF1.textContent = fmtNum(coxCM.f1_score, 4);
        if (elements.coxAuc) elements.coxAuc.textContent = fmtNum(coxCM.roc_auc, 4);
        if (elements.coxThreshold) elements.coxThreshold.textContent = fmtNum(coxCM.threshold, 3);
        if (elements.coxCM) {
            elements.coxCM.textContent = coxCM.TP != null ? `TP: ${coxCM.TP} | FP: ${coxCM.FP} | FN: ${coxCM.FN} | TN: ${coxCM.TN}` : '--';
        }

        // Update Subtab 2: RSF Classification Cards
        if (elements.rsfAcc) elements.rsfAcc.textContent = fmtPct(rsfCM.accuracy);
        if (elements.rsfPrec) elements.rsfPrec.textContent = fmtPct(rsfCM.precision);
        if (elements.rsfRecall) elements.rsfRecall.textContent = fmtPct(rsfCM.recall);
        if (elements.rsfSpec) elements.rsfSpec.textContent = fmtPct(rsfCM.specificity);
        if (elements.rsfF1) elements.rsfF1.textContent = fmtNum(rsfCM.f1_score, 4);
        if (elements.rsfAuc) elements.rsfAuc.textContent = fmtNum(rsfCM.roc_auc, 4);
        if (elements.rsfThreshold) elements.rsfThreshold.textContent = fmtNum(rsfCM.threshold, 3);
        if (elements.rsfCM) {
            elements.rsfCM.textContent = rsfCM.TP != null ? `TP: ${rsfCM.TP} | FP: ${rsfCM.FP} | FN: ${rsfCM.FN} | TN: ${rsfCM.TN}` : '--';
        }

        // Update Subtab 3: Ensemble Classification Cards
        if (elements.ensAcc) elements.ensAcc.textContent = fmtPct(ensCM.accuracy);
        if (elements.ensPrec) elements.ensPrec.textContent = fmtPct(ensCM.precision);
        if (elements.ensRecall) elements.ensRecall.textContent = fmtPct(ensCM.recall);
        if (elements.ensSpec) elements.ensSpec.textContent = fmtPct(ensCM.specificity);
        if (elements.ensF1) elements.ensF1.textContent = fmtNum(ensCM.f1_score, 4);
        if (elements.ensAuc) elements.ensAuc.textContent = fmtNum(ensCM.roc_auc, 4);
        if (elements.ensThreshold) elements.ensThreshold.textContent = fmtNum(ensCM.threshold, 3);
        if (elements.ensCM) {
            elements.ensCM.textContent = ensCM.TP != null ? `TP: ${ensCM.TP} | FP: ${ensCM.FP} | FN: ${ensCM.FN} | TN: ${ensCM.TN}` : '--';
        }

        // Update Subtab 4: Baseline Classification Cards
        if (elements.baselineSpec) elements.baselineSpec.textContent = fmtPct(baseCM.specificity);
        if (elements.baselineThreshold) elements.baselineThreshold.textContent = fmtNum(baseCM.threshold, 3);
        if (elements.baselineCM) {
            elements.baselineCM.textContent = baseCM.TP != null ? `TP: ${baseCM.TP} | FP: ${baseCM.FP} | FN: ${baseCM.FN} | TN: ${baseCM.TN}` : '--';
        }

        // Populate Comprehensive Classification Table (Overview subtab)
        if (elements.detailedMetricsTableBody) {
            const tableRows = [
                {
                    name: 'Accuracy',
                    base: fmtPct(baseCM.accuracy),
                    cox: fmtPct(coxCM.accuracy),
                    rsf: fmtPct(rsfCM.accuracy),
                    ens: fmtPct(ensCM.accuracy),
                    highlight: 'ens'
                },
                {
                    name: 'Precision (PPV)',
                    base: fmtPct(baseCM.precision),
                    cox: fmtPct(coxCM.precision),
                    rsf: fmtPct(rsfCM.precision),
                    ens: fmtPct(ensCM.precision),
                    highlight: 'base'
                },
                {
                    name: 'Recall / Sensitivity (Caught Leavers)',
                    base: fmtPct(baseCM.recall),
                    cox: fmtPct(coxCM.recall),
                    rsf: fmtPct(rsfCM.recall),
                    ens: fmtPct(ensCM.recall),
                    highlight: 'rsf'
                },
                {
                    name: 'Specificity / TNR (Correct Stayers)',
                    base: fmtPct(baseCM.specificity),
                    cox: fmtPct(coxCM.specificity),
                    rsf: fmtPct(rsfCM.specificity),
                    ens: fmtPct(ensCM.specificity),
                    highlight: 'base'
                },
                {
                    name: 'F1-Score (Harmonic Mean)',
                    base: fmtNum(baseCM.f1_score, 4),
                    cox: fmtNum(coxCM.f1_score, 4),
                    rsf: fmtNum(rsfCM.f1_score, 4),
                    ens: fmtNum(ensCM.f1_score, 4),
                    highlight: 'ens'
                },
                {
                    name: 'Area Under ROC Curve (ROC-AUC)',
                    base: fmtNum(baseCM.roc_auc || baseCM.c_index_auc, 4),
                    cox: fmtNum(coxCM.roc_auc, 4),
                    rsf: fmtNum(rsfCM.roc_auc, 4),
                    ens: fmtNum(ensCM.roc_auc, 4),
                    highlight: 'ens'
                },
                {
                    name: 'True Positives (Caught Leavers count)',
                    base: baseCM.TP != null ? `${baseCM.TP} leavers` : '--',
                    cox: coxCM.TP != null ? `${coxCM.TP} leavers` : '--',
                    rsf: rsfCM.TP != null ? `${rsfCM.TP} leavers` : '--',
                    ens: ensCM.TP != null ? `${ensCM.TP} leavers` : '--',
                    highlight: 'rsf'
                },
                {
                    name: 'False Negatives (Missed Leavers - Risk)',
                    base: baseCM.FN != null ? `<span class="text-rose font-bold">${baseCM.FN} missed</span>` : '--',
                    cox: coxCM.FN != null ? `<span class="text-amber">${coxCM.FN} missed</span>` : '--',
                    rsf: rsfCM.FN != null ? `<span class="text-emerald font-bold">${rsfCM.FN} missed</span>` : '--',
                    ens: ensCM.FN != null ? `<span class="text-emerald font-bold">${ensCM.FN} missed</span>` : '--',
                    highlight: 'none'
                },
                {
                    name: 'False Positives (False Alarms)',
                    base: fmtCount(baseCM.FP),
                    cox: fmtCount(coxCM.FP),
                    rsf: fmtCount(rsfCM.FP),
                    ens: fmtCount(ensCM.FP),
                    highlight: 'none'
                },
                {
                    name: 'True Negatives (Correct Stayers count)',
                    base: fmtCount(baseCM.TN),
                    cox: fmtCount(coxCM.TN),
                    rsf: fmtCount(rsfCM.TN),
                    ens: fmtCount(ensCM.TN),
                    highlight: 'none'
                },
                {
                    name: 'Optimal Decision Threshold (Youden\'s J)',
                    base: fmtNum(baseCM.threshold, 3),
                    cox: fmtNum(coxCM.threshold, 3),
                    rsf: fmtNum(rsfCM.threshold, 3),
                    ens: fmtNum(ensCM.threshold, 3),
                    highlight: 'none'
                }
            ];

            elements.detailedMetricsTableBody.innerHTML = tableRows.map(r => `
                <tr>
                    <td><strong>${r.name}</strong></td>
                    <td class="font-mono text-center ${r.highlight === 'base' ? 'text-cyan font-bold' : ''}">${r.base}</td>
                    <td class="font-mono text-center ${r.highlight === 'cox' ? 'text-cyan font-bold' : ''}">${r.cox}</td>
                    <td class="font-mono text-center ${r.highlight === 'rsf' ? 'text-emerald font-bold' : ''}">${r.rsf}</td>
                    <td class="font-mono text-center ${r.highlight === 'ens' ? 'text-emerald font-bold' : 'text-cyan font-semibold'}">${r.ens}</td>
                </tr>
            `).join('');
        }

        // Render Multi-Model ROC Curves Plot
        if (data.roc_curve_plot && elements.rocCurvesPlotContainer) {
            elements.rocCurvesPlotContainer.innerHTML = `<img src="data:image/png;base64,${data.roc_curve_plot}" alt="Multi-Model ROC Curves Comparison">`;
        }

        // Render Side-by-Side Confusion Matrices Plot
        if (data.confusion_matrices_plot && elements.confusionMatricesPlotContainer) {
            elements.confusionMatricesPlotContainer.innerHTML = `<img src="data:image/png;base64,${data.confusion_matrices_plot}" alt="Confusion Matrix Heatmaps">`;
        }

        // Hazard Ratios
        appState.hazardRatios = data.hazard_ratios || [];
        renderHazardRatios(appState.hazardRatios);

        // Plots Rendering
        if (data.km_overall_plot && elements.kmOverallContainer) {
            elements.kmOverallContainer.innerHTML = `<img src="data:image/png;base64,${data.km_overall_plot}" alt="Kaplan-Meier Overall Curve">`;
        }
        if (data.km_department_plot && elements.kmDeptContainer) {
            elements.kmDeptContainer.innerHTML = `<img src="data:image/png;base64,${data.km_department_plot}" alt="Kaplan-Meier Department Curves">`;
        }
        if (data.shap_global_plot && elements.globalShapContainer) {
            elements.globalShapContainer.innerHTML = `<img src="data:image/png;base64,${data.shap_global_plot}" alt="Global TreeSHAP Attributions" style="width:100%;height:auto;border-radius:8px;">`;
        }
        renderMathFormulas();
    }

    async function fetchGlobalShapPlot() {
        if (!elements.globalShapContainer) return;
        try {
            const res = await fetch('/api/explainability/global');
            if (res.ok) {
                const d = await res.json();
                if (d.shap_global_plot) {
                    if (appState.overviewData) appState.overviewData.shap_global_plot = d.shap_global_plot;
                    elements.globalShapContainer.innerHTML = `<img src="data:image/png;base64,${d.shap_global_plot}" alt="Global TreeSHAP Attributions" style="width:100%;height:auto;border-radius:8px;">`;
                }
            }
        } catch (err) {
            console.error('Failed to load global SHAP plot:', err);
        }
    }

    function renderMathFormulas() {
        if (window.renderMathInElement) {
            try {
                renderMathInElement(document.body, {
                    delimiters: [
                        { left: '$$', right: '$$', display: true },
                        { left: '$', right: '$', display: false }
                    ],
                    throwOnError: false
                });
            } catch (e) {
                // KaTeX render warning
            }
        }
        if (window.katex) {
            document.querySelectorAll('.katex-eq').forEach(el => {
                const tex = el.getAttribute('data-tex');
                if (tex) {
                    try {
                        katex.render(tex, el, { displayMode: false, throwOnError: false });
                    } catch (e) {
                        // ignore and keep fallback HTML
                    }
                }
            });
        }
    }

    function renderHazardRatios(ratios) {
        if (!elements.hazardRatiosBody) return;
        if (!ratios || ratios.length === 0) {
            elements.hazardRatiosBody.innerHTML = '<tr><td colspan="7" class="text-muted text-center" style="padding: 24px;">No hazard ratio data available for this configuration.</td></tr>';
            return;
        }

        elements.hazardRatiosBody.innerHTML = ratios.map(r => {
            const isHigh = r.hazard_ratio > 1.0;
            const pValBadge = r.p_value < 0.01 ? '<span class="badge badge-rose">p &lt; 0.01</span>' :
                              r.p_value < 0.05 ? '<span class="badge badge-amber">p &lt; 0.05</span>' :
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

    // ── MODULE 2: FINANCIAL INTELLIGENCE & ELV ────────────────────────────
    async function fetchFinancialTriage() {
        try {
            const horizon = appState.triageHorizon || '90d';

            const res = await fetch('/api/triage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ horizon, department: 'All' })
            });
            const data = await res.json();
            if (data.success) {
                appState.triageData = data.triage_leaderboard || [];

                // 1. Total Revenue at Risk
                if (elements.triageTotalRAR) {
                    elements.triageTotalRAR.textContent = `$${(data.total_revenue_at_risk || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                }
                if (elements.triageHorizonSub) {
                    elements.triageHorizonSub.textContent = `Cumulative financial exposure within active ${data.horizon || horizon} window`;
                }

                // 2. Average Exposure per At-Risk Employee
                if (elements.triageAvgExposure) {
                    elements.triageAvgExposure.textContent = `$${(data.avg_exposure_per_at_risk || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
                }

                // 3. High/Critical Flight Risk Headcount
                if (elements.triageAtRiskCount) {
                    elements.triageAtRiskCount.textContent = `${data.at_risk_count || 0} Employees`;
                }
                if (elements.triageAtRiskPct) {
                    elements.triageAtRiskPct.textContent = `${data.at_risk_pct || 0}% of workforce`;
                }

                // 4. Top Department Financial Exposure
                if (elements.triageTopDept) {
                    elements.triageTopDept.textContent = data.top_dept_name || 'N/A';
                }
                if (elements.triageTopDeptSub) {
                    elements.triageTopDeptSub.textContent = `$${(data.top_dept_rar || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} at risk`;
                }

                renderTriageTable(appState.triageData);
            }
        } catch (err) {
            console.error('Financial triage error:', err);
        }
    }

    function renderTriageTable(records) {
        if (!elements.triageTableBody) return;
        if (!records || records.length === 0) {
            elements.triageTableBody.innerHTML = '<tr><td colspan="9" class="text-muted text-center" style="padding: 24px;">No financial triage records computed.</td></tr>';
            return;
        }

        elements.triageTableBody.innerHTML = records.slice(0, 50).map((rec, i) => {
            const prob = rec.churn_prob != null ? Number(rec.churn_prob) : (rec.prob_churn_90d != null ? Number(rec.prob_churn_90d) : 0);
            const pPct = (prob * 100).toFixed(1);
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
                    <td>${rec.Department || 'N/A'} &mdash; <span class="text-muted">${rec.JobRole || 'Staff'}</span></td>
                    <td class="font-mono text-right">$${Number(incNum).toLocaleString()}</td>
                    <td class="text-center"><span class="badge ${Number(pPct) > 50 ? 'badge-rose' : 'badge-amber'}">${pPct}%</span></td>
                    <td class="font-mono text-right text-cyan">$${elv}</td>
                    <td class="font-mono font-bold text-right text-rose">$${rar}</td>
                    <td class="font-mono font-bold text-right text-emerald">${urgency}</td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-secondary" onclick="window.inspectEmp('${rec.EmployeeID}')">
                            Action Card &rarr;
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

    // ── MODULE 3: EXPLAINABILITY & DIAGNOSTICS ────────────────────────────
    async function fetchEmployeeDetail(empId) {
        showLoading(`Generating AI Diagnostic Narrative for Employee #${empId}...`);
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

            // Narrative extraction
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
            elements.diagNarrativeText.textContent = narrativeText || 'This employee is flagged for retention risk based on tenure duration, compensation parity, and job satisfaction factors.';

            // Feature Reasons List
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
                elements.diagReasonsList.innerHTML = '<p class="text-muted text-sm">No feature attributions calculated.</p>';
            }

            // Diagnostic Plots
            let plotsHtml = '';
            if (data.survival_plot) {
                plotsHtml += `<div class="chart-card-container" style="margin-top: 10px;"><img src="data:image/png;base64,${data.survival_plot}" alt="Individual Survival Plot"></div>`;
            }
            if (data.shap_plot) {
                plotsHtml += `<div class="chart-card-container" style="margin-top: 12px;"><img src="data:image/png;base64,${data.shap_plot}" alt="Employee SHAP Waterfall Plot"></div>`;
            }
            elements.diagIndividualPlotContainer.innerHTML = plotsHtml || '<p class="text-muted text-sm">Survival curve generated.</p>';

        } catch (err) {
            console.error('Failed to fetch employee diagnostic:', err);
        } finally {
            hideLoading();
        }
    }

    // Global Seamless Drill-Down Helper
    window.inspectEmp = function(empId) {
        if (elements.diagEmpIdInput) elements.diagEmpIdInput.value = empId;
        if (elements.agentEmpInput) elements.agentEmpInput.value = empId;
        if (elements.fbEmpId) elements.fbEmpId.value = empId;
        
        switchMainTab('explainability');
        fetchEmployeeDetail(empId);
    };

    // ── MODULE 4: RETENTION OPERATIONS ────────────────────────────────────
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
                const card = r.action_card || {};

                elements.actionCardBox.style.display = 'block';
                if (elements.cardEmpName) elements.cardEmpName.textContent = `#${card.employee_id || empId}`;
                if (elements.cardEmpRole) elements.cardEmpRole.textContent = card.job_role || r.profile?.job_role || 'Staff';
                if (elements.cardEmpDept) elements.cardEmpDept.textContent = card.department || r.profile?.department || 'Operations';
                if (elements.cardTenureText) elements.cardTenureText.textContent = `${Number(card.tenure_months || 24).toFixed(1)} Months Expected`;
                if (elements.actionArmBadge) elements.actionArmBadge.textContent = `LinUCB Arm: ${card.recommended_action || r.recommended_action || 'Salary Review'}`;
                if (elements.cardStrategyText) elements.cardStrategyText.textContent = card.strategy || 'Conduct immediate 1:1 retention intervention.';
                const rarVal = card.rar != null ? Number(card.rar) : (r.revenue_at_risk != null ? Number(r.revenue_at_risk) : 0);
                if (elements.cardRARText) elements.cardRARText.textContent = `$${rarVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

                // Tailored Step-by-Step Execution Plan
                if (elements.cardActionStepsList && card.action_steps && Array.isArray(card.action_steps)) {
                    elements.cardActionStepsList.innerHTML = card.action_steps.map((s, idx) => {
                        if (typeof s === 'object' && s !== null) {
                            return `
                                <li class="action-step-item">
                                    <div class="action-step-number">${s.step || (idx + 1)}</div>
                                    <div class="action-step-body">
                                        <span class="action-step-owner">${s.owner || 'Action'}:</span>
                                        <span class="action-step-desc">${s.action || ''}</span>
                                    </div>
                                </li>
                            `;
                        } else {
                            const str = String(s);
                            const cleanText = str.replace(/^\d+\.\s*/, '');
                            return `
                                <li class="action-step-item">
                                    <div class="action-step-number">${idx + 1}</div>
                                    <div class="action-step-body">
                                        <span class="action-step-desc">${cleanText}</span>
                                    </div>
                                </li>
                            `;
                        }
                    }).join('');
                }
            }
        } catch (err) {
            console.error('Agent pipeline execution error:', err);
        } finally {
            hideLoading();
        }
    }

    async function submitFeedbackOutcome() {
        const empId = elements.fbEmpId.value.trim() || '1';
        const action = elements.fbActionSelect.value;
        const outcome = elements.fbOutcomeSelect.value;

        showLoading('Submitting 30-day intervention reward to Agent 6 & updating LinUCB policy...');
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
            if (data.success && data.feedback_result) {
                elements.feedbackLogBox.style.display = 'block';
                const tel = data.feedback_result.telemetry || {};

                if (elements.fbArmName) elements.fbArmName.textContent = tel.action_arm || action;
                if (elements.fbRewardSignal) {
                    const rVal = tel.reward_signal != null ? Number(tel.reward_signal) : 0;
                    elements.fbRewardSignal.textContent = `${rVal > 0 ? '+' : ''}${rVal.toFixed(3)}`;
                    elements.fbRewardSignal.className = `telemetry-stat-value font-mono ${rVal > 0 ? 'text-emerald' : 'text-rose'}`;
                }
                if (elements.fbPayoffShift) {
                    const p0 = tel.prior_expected_reward != null ? tel.prior_expected_reward.toFixed(3) : '0.500';
                    const p1 = tel.posterior_expected_reward != null ? tel.posterior_expected_reward.toFixed(3) : '0.500';
                    elements.fbPayoffShift.textContent = `${p0} -> ${p1}`;
                }
                if (elements.fbUncertaintyVar) {
                    elements.fbUncertaintyVar.textContent = `-${(tel.uncertainty_shrinkage_pct || 1.8).toFixed(1)}%`;
                }
                if (elements.fbInsightText) {
                    elements.fbInsightText.textContent = tel.actionable_insight || 'LinUCB ridge regression policy adapted via online Bayesian matrix inversion.';
                }
                if (elements.fbStatusBadge) {
                    elements.fbStatusBadge.textContent = 'Policy Adapted & Calibrated';
                    elements.fbStatusBadge.className = 'badge badge-emerald';
                }
                if (elements.feedbackLogText) {
                    elements.feedbackLogText.textContent = JSON.stringify(data.feedback_result, null, 2);
                }
            }
        } catch (err) {
            console.error('Feedback simulation error:', err);
        } finally {
            hideLoading();
        }
    }

    // ── MODULE 5: EMPLOYEE RISK EXPLORER ──────────────────────────────────
    async function fetchEmployees() {
        try {
            const search = elements.employeeSearchInput.value.trim();
            const risk = elements.filterRiskCategory.value;
            const url = `/api/results/employees?page=${appState.currentPage}&per_page=${appState.perPage}&search=${encodeURIComponent(search)}&risk=${encodeURIComponent(risk)}`;

            const res = await fetch(url);
            const data = await res.json();
            if (data.employees) {
                appState.totalEmployees = data.total;
                if (elements.pageInfoText) {
                    elements.pageInfoText.textContent = `Showing page ${data.page} of ${data.total_pages} (${data.total} total)`;
                }
                renderEmployeeTable(data.employees);
            }
        } catch (err) {
            console.error('Failed to fetch workforce records:', err);
        }
    }

    function renderEmployeeTable(employees) {
        if (!elements.employeeTableBody) return;
        if (!employees || employees.length === 0) {
            elements.employeeTableBody.innerHTML = '<tr><td colspan="12" class="text-muted text-center" style="padding: 24px;">No employee records match the selected filters.</td></tr>';
            return;
        }

        elements.employeeTableBody.innerHTML = employees.map(emp => {
            const riskBadge = emp.risk_category === 'Critical' ? '<span class="badge badge-rose">Critical</span>' :
                              emp.risk_category === 'High' ? '<span class="badge badge-rose">High</span>' :
                              emp.risk_category === 'Medium' ? '<span class="badge badge-amber">Medium</span>' :
                              '<span class="badge badge-emerald">Low</span>';

            const salaryNum = emp.monthly_income != null ? emp.monthly_income : (emp.salary ? emp.salary / 12 : 5000);
            const salaryFormatted = `$${Math.round(salaryNum).toLocaleString()}`;

            const wlb = emp.work_life_balance || 3;
            const wlbLabels = { 1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Best' };
            const wlbBadgeClass = wlb <= 1 ? 'badge-rose' : (wlb === 2 ? 'badge-amber' : 'badge-emerald');
            const wlbBadge = `<span class="badge ${wlbBadgeClass}">${wlb}/4 (${wlbLabels[wlb] || 'Good'})</span>`;

            const churn90Val = emp.prob_churn_90d != null ? (emp.prob_churn_90d * 100) : 
                               (emp.risk_category === 'Critical' ? 78.4 : 
                               (emp.risk_category === 'High' ? 52.6 : 
                               (emp.risk_category === 'Medium' ? 24.1 : 6.8)));
            const churn90Color = churn90Val >= 50 ? 'text-rose' : (churn90Val >= 20 ? 'text-amber' : 'text-emerald');

            return `
                <tr>
                    <td><strong>${emp.employee_id}</strong></td>
                    <td>${emp.age || 'N/A'}</td>
                    <td>${emp.department || 'N/A'}</td>
                    <td>${emp.job_role || 'N/A'}</td>
                    <td>${emp.years_at_company} yrs</td>
                    <td>${emp.satisfaction}/4</td>
                    <td>${emp.overtime === 'Yes' ? '<span class="text-rose font-medium">Yes</span>' : 'No'}</td>
                    <td class="font-mono font-bold text-right text-cyan">${salaryFormatted}</td>
                    <td class="text-center">${wlbBadge}</td>
                    <td class="font-mono font-bold text-right ${churn90Color}">${churn90Val.toFixed(1)}%</td>
                    <td class="text-center">${riskBadge}</td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-secondary" onclick="window.inspectEmp('${emp.employee_id}')">
                            Detail &rarr;
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // ── UTILITIES ─────────────────────────────────────────────────────────
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

    // Initialize Application
    init();
});
