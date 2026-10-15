"""
Generate 10-Slide Review 3 PowerPoint Presentation
Project: EMPLOYEE SURVIVAL PREDICTION AND RETENTION SYSTEM
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette (Enterprise Dark Navy & Slate)
    BG_COLOR = RGBColor(15, 20, 41)         # #0f1429
    CARD_BG = RGBColor(22, 27, 51)          # #161b33
    CARD_BORDER = RGBColor(42, 48, 85)      # #2a3055
    ACCENT_CYAN = RGBColor(56, 189, 248)    # #38bdf8
    ACCENT_EMERALD = RGBColor(52, 211, 153) # #34d399
    ACCENT_PURPLE = RGBColor(192, 132, 252) # #c084fc
    TEXT_WHITE = RGBColor(255, 255, 255)
    TEXT_MUTED = RGBColor(148, 163, 184)    # #94a3b8
    TEXT_BODY = RGBColor(226, 232, 240)     # #e2e8f0

    blank_layout = prs.slide_layouts[6]

    def set_slide_bg(slide):
        bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = BG_COLOR
        bg_shape.line.fill.background()
        return bg_shape

    def add_header(slide, title_text, subtitle_text, category_badge="IMPLEMENTATION REVIEW 3"):
        # Header text box
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(9.2), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = title_text
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.name = "Arial"
        p1.font.color.rgb = TEXT_WHITE
        p1.space_after = Pt(4)

        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.size = Pt(12)
        p2.font.bold = False
        p2.font.name = "Arial"
        p2.font.color.rgb = ACCENT_CYAN

        # Category Badge Box
        badge_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.2), Inches(0.48), Inches(2.33), Inches(0.42))
        badge_box.fill.solid()
        badge_box.fill.fore_color.rgb = CARD_BG
        badge_box.line.color.rgb = ACCENT_CYAN
        badge_box.line.width = Pt(1.2)
        btf = badge_box.text_frame
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        bp = btf.paragraphs[0]
        bp.alignment = PP_ALIGN.CENTER
        bp.text = category_badge
        bp.font.size = Pt(9.5)
        bp.font.bold = True
        bp.font.color.rgb = ACCENT_CYAN
        bp.font.name = "Arial"

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s1)

    # Accent decorative bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(0.12), Inches(4.3))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_CYAN
    bar.line.fill.background()

    # Title box
    tbox = s1.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(11.0), Inches(4.5))
    ttf = tbox.text_frame
    ttf.word_wrap = True

    p = ttf.paragraphs[0]
    p.text = "PANEL REVIEW 3: TECHNICAL IMPLEMENTATION"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p.font.name = "Arial"
    p.space_after = Pt(12)

    p = ttf.add_paragraph()
    p.text = "EMPLOYEE SURVIVAL PREDICTION AND RETENTION SYSTEM"
    p.font.size = Pt(30)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.font.name = "Arial"
    p.space_after = Pt(14)

    p = ttf.add_paragraph()
    p.text = "End-to-End Engineering Architecture: Multi-Model Survival Ensemble, Financial Triage & Closed-Loop Agentic Interventions"
    p.font.size = Pt(15)
    p.font.color.rgb = TEXT_MUTED
    p.font.name = "Arial"
    p.space_after = Pt(36)

    # Metadata card
    m_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.6), Inches(10.8), Inches(1.5))
    m_card.fill.solid()
    m_card.fill.fore_color.rgb = CARD_BG
    m_card.line.color.rgb = CARD_BORDER
    mtf = m_card.text_frame
    mtf.margin_left = Inches(0.4)
    mtf.margin_top = Inches(0.25)

    mp1 = mtf.paragraphs[0]
    mp1.text = "Implementation Deliverables & Architecture Overview:"
    mp1.font.bold = True
    mp1.font.size = Pt(12)
    mp1.font.color.rgb = ACCENT_EMERALD

    mp2 = mtf.add_paragraph()
    mp2.text = "• Dual-Engine Survival Modeling (Cox PH + Random Survival Forest with Concordance Dynamic Ensemble)\n• Financial Intelligence Engine (Expected Lifetime Value & Multi-Horizon Revenue at Risk Prioritization)\n• Autonomous 5-Agent Operations with LinUCB Contextual Multi-Armed Bandit Closed-Loop Policy Adaptation"
    mp2.font.size = Pt(11)
    mp2.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 2: PROJECT RECAP (REVIEWS 1 & 2 FOUNDATION)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2)
    add_header(s2, "Project Recap: Problem Statement & Foundation", 
               "Core Limitations Established in Review 1 and Preprocessing Baseline from Review 2")

    # 2 Column layout for recap
    col1 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1))
    col1.fill.solid()
    col1.fill.fore_color.rgb = CARD_BG
    col1.line.color.rgb = CARD_BORDER
    c1tf = col1.text_frame
    c1tf.margin_left = Inches(0.35)
    c1tf.margin_top = Inches(0.35)
    c1tf.margin_right = Inches(0.35)

    p = c1tf.paragraphs[0]
    p.text = "Core Limitations of Traditional Approaches (Review 1)"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = ACCENT_CYAN
    p.space_after = Pt(14)

    recap_points_1 = [
        ("Survival Bias in Binary ML", "Standard classifiers (Logistic Regression, Random Forest, XGBoost) treat active employees as permanently loyal, ignoring right-censored observation limits."),
        ("Absence of Temporal Forecasting", "Binary models evaluate IF someone leaves, failing to predict WHEN departure occurs, disabling time-critical retention planning."),
        ("Uniform Attrition Cost Fallacy", "Traditional systems treat all resignations equally, failing to prioritize intervention by salary and replacement cost.")
    ]
    for title, desc in recap_points_1:
        p = c1tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_BODY
        p.space_after = Pt(12)

    col2 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.1))
    col2.fill.solid()
    col2.fill.fore_color.rgb = CARD_BG
    col2.line.color.rgb = CARD_BORDER
    c2tf = col2.text_frame
    c2tf.margin_left = Inches(0.35)
    c2tf.margin_top = Inches(0.35)
    c2tf.margin_right = Inches(0.35)

    p = c2tf.paragraphs[0]
    p.text = "Datasets, Preprocessing & Review 3 Goal (Review 2)"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = ACCENT_EMERALD
    p.space_after = Pt(14)

    recap_points_2 = [
        ("Benchmarked HR Corpora", "IBM HR Analytics (n=1,470, 35 attributes) and Healthcare Attrition dataset (n=1,676, 35 attributes)."),
        ("Survival Target Formulation", "Transformed targets into continuous Duration (T in months) and Event indicator (E in {0, 1}) for right-censoring handling."),
        ("Preprocessing Pipeline", "Stratified survival train/test split (80/20) preserving event ratios, standard scaling, and one-hot encoding."),
        ("Review 3 Implementation Scope", "Deploy production-grade full-stack survival ensemble, revenue-at-risk triage, TreeSHAP diagnostics, and reinforcement learning multi-agent pipeline.")
    ]
    for title, desc in recap_points_2:
        p = c2tf.add_paragraph()
        p.text = f"• {title}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_BODY
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 3: SYSTEM IMPLEMENTATION ARCHITECTURE & WORKFLOW DIAGRAM
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3)
    add_header(s3, "System Implementation Architecture & Workflow", 
               "End-to-End Engineering Dataflow from Raw Ingestion to Closed-Loop Adaptation")

    # Workflow Architecture Step Boxes
    steps = [
        ("Step 1: Data Ingestion", "IBM / Healthcare / CSV\nTarget Encoding (T, E)", ACCENT_CYAN, Inches(0.8), Inches(1.7), Inches(2.7), Inches(1.3)),
        ("Step 2: Dual Survival Engine", "Cox Proportional Hazards\nRandom Survival Forest", ACCENT_CYAN, Inches(3.8), Inches(1.7), Inches(2.7), Inches(1.3)),
        ("Step 3: Concordance Ensemble", "Dynamic Weight Calibration\nMulti-Horizon Curves (30/60/90d)", ACCENT_CYAN, Inches(6.8), Inches(1.7), Inches(2.7), Inches(1.3)),
        ("Step 4: Economic Triage", "ELV & Revenue at Risk (RAR)\nUrgency Score Queue", ACCENT_CYAN, Inches(9.8), Inches(1.7), Inches(2.7), Inches(1.3)),

        ("Step 7: Closed-Loop Policy", "LinUCB Bandit Algorithm\nBayesian Matrix Updates", ACCENT_EMERALD, Inches(2.0), Inches(3.3), Inches(3.2), Inches(1.3)),
        ("Step 6: Autonomous 5-Agents", "Observer → Analyst → Strategist\nExecutor Action Card Synthesis", ACCENT_EMERALD, Inches(5.5), Inches(3.3), Inches(3.2), Inches(1.3)),
        ("Step 5: Explainability Layer", "TreeSHAP Local & Global\nLLM Diagnostic Narrative", ACCENT_EMERALD, Inches(9.0), Inches(3.3), Inches(3.5), Inches(1.3)),
    ]

    for title, subtitle, accent, left, top, width, height in steps:
        box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        box.fill.solid()
        box.fill.fore_color.rgb = CARD_BG
        box.line.color.rgb = accent
        box.line.width = Pt(1.5)
        btf = box.text_frame
        btf.margin_left = Inches(0.15)
        btf.margin_top = Inches(0.18)
        bp = btf.paragraphs[0]
        bp.text = title
        bp.font.size = Pt(11)
        bp.font.bold = True
        bp.font.color.rgb = accent
        bp.space_after = Pt(4)
        bp2 = btf.add_paragraph()
        bp2.text = subtitle
        bp2.font.size = Pt(9.5)
        bp2.font.color.rgb = TEXT_BODY

    # Technical Implementation Bullets Container below diagram
    tech_card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.85), Inches(11.7), Inches(2.1))
    tech_card.fill.solid()
    tech_card.fill.fore_color.rgb = CARD_BG
    tech_card.line.color.rgb = CARD_BORDER
    ttf = tech_card.text_frame
    ttf.margin_left = Inches(0.35)
    ttf.margin_top = Inches(0.2)

    tp = ttf.paragraphs[0]
    tp.text = "Full-Stack Implementation & Technical Stack:"
    tp.font.size = Pt(13)
    tp.font.bold = True
    tp.font.color.rgb = ACCENT_CYAN
    tp.space_after = Pt(6)

    tech_points = [
        "Backend Architecture: Python Flask with Gunicorn WSGI container, optimized for sub-50ms inference latency.",
        "Scientific Engine: Scikit-survival for non-linear log-rank splitting trees and Lifelines for semi-parametric hazard modeling.",
        "Model Persistence & Caching: Zero-recomputation Joblib serialization and Parquet columnar caching for instant workforce lookups.",
        "Frontend Delivery: Modular enterprise dark-mode UI with Vanilla CSS/JS, asynchronous REST APIs, and zero bloated JS dependencies.",
        "Closed-Loop Autonomy: Seamlessly couples ML survival forecasting with reinforcement learning retention arm selection."
    ]
    for pt in tech_points:
        p = ttf.add_paragraph()
        p.text = f"• {pt}"
        p.font.size = Pt(10.5)
        p.font.color.rgb = TEXT_BODY

    # =========================================================================
    # REUSABLE FUNCTION FOR SLIDES WITH LIVE SCREENSHOTS (SLIDES 4 - 9)
    # =========================================================================
    def build_split_slide(slide_num, title, subtitle, bullets, screenshot_filename, caption_text):
        slide = prs.slides.add_slide(blank_layout)
        set_slide_bg(slide)
        add_header(slide, title, subtitle)

        # Left Column: Bullets Card (Width: 6.2")
        left_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.7), Inches(6.1), Inches(5.3))
        left_card.fill.solid()
        left_card.fill.fore_color.rgb = CARD_BG
        left_card.line.color.rgb = CARD_BORDER
        ltf = left_card.text_frame
        ltf.margin_left = Inches(0.3)
        ltf.margin_top = Inches(0.35)
        ltf.margin_right = Inches(0.3)

        lp0 = ltf.paragraphs[0]
        lp0.text = "Technical Implementation Details:"
        lp0.font.bold = True
        lp0.font.size = Pt(13)
        lp0.font.color.rgb = ACCENT_CYAN
        lp0.space_after = Pt(12)

        for b_title, b_desc in bullets:
            p = ltf.add_paragraph()
            p.text = f"• {b_title}: "
            p.font.bold = True
            p.font.size = Pt(10.8)
            p.font.color.rgb = TEXT_WHITE
            run = p.add_run()
            run.text = b_desc
            run.font.bold = False
            run.font.color.rgb = TEXT_BODY
            p.space_after = Pt(10)

        # Right Column: Screenshot Container (Width: 5.4")
        right_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.1), Inches(1.7), Inches(5.4), Inches(5.3))
        right_card.fill.solid()
        right_card.fill.fore_color.rgb = CARD_BG
        right_card.line.color.rgb = CARD_BORDER

        # Caption inside right card
        rtf = right_card.text_frame
        rtf.margin_left = Inches(0.2)
        rtf.margin_top = Inches(0.15)
        rp0 = rtf.paragraphs[0]
        rp0.text = caption_text
        rp0.font.bold = True
        rp0.font.size = Pt(10)
        rp0.font.color.rgb = ACCENT_EMERALD

        # Embed Screenshot if exists
        img_path = os.path.join(os.path.dirname(__file__), "ppt_screenshots", screenshot_filename)
        if os.path.exists(img_path):
            slide.shapes.add_picture(img_path, Inches(7.25), Inches(2.2), width=Inches(5.1))
        else:
            # Placeholder text if missing
            ph = slide.shapes.add_textbox(Inches(7.3), Inches(3.0), Inches(5.0), Inches(2.0))
            phtf = ph.text_frame
            php = phtf.paragraphs[0]
            php.text = f"[LIVE SYSTEM SCREENSHOT PLACEHOLDER:\n{screenshot_filename}]"
            php.font.size = Pt(12)
            php.font.color.rgb = ACCENT_CYAN

    # =========================================================================
    # SLIDE 4: DUAL SURVIVAL ENGINE & ENSEMBLE (NOVELTY 1)
    # =========================================================================
    s4_bullets = [
        ("Semi-Parametric Statistical Anchor", "Cox PH computes baseline hazard h0(t) and individual feature Hazard Ratios (HR = e^beta) with rigorous p-value significance testing."),
        ("Non-Parametric Forest", "Random Survival Forest (RSF) uses log-rank split criteria across ensemble trees to capture high-order non-linear feature interactions without distribution assumptions."),
        ("Concordance-Excess Dynamic Blend", "Self-calibrates ensemble weights from test C-indices: w_a = (C_a - 0.5) / sum(C_k - 0.5), assigning 58% weight to RSF and 42% to Cox PH."),
        ("Multi-Horizon Continuous Forecasting", "Computes discrete cumulative departure probabilities at immediate 30-day, 60-day, and 90-day operational planning intervals."),
        ("Production Dataset Ingestion", "Supports benchmark datasets (IBM HR / Healthcare) as well as live user-uploaded CSV/Excel datasets with automated column mapping.")
    ]
    build_split_slide(4, "Dual Survival Modeling & Dynamic Ensemble Engine",
                      "Novelty 1: Concordance-Excess Dynamic Blending of Cox PH & Random Survival Forest",
                      s4_bullets, "employee_explorer.png", "Live Implementation: Workforce Multi-Horizon Scoring")

    # =========================================================================
    # SLIDE 5: MODEL VALIDATION & CALIBRATION METRICS
    # =========================================================================
    s5_bullets = [
        ("Strict Stratified Partitioning", "Evaluated strictly on held-out 20% stratified test split (n=294), ensuring zero data leakage and preserving true event proportions."),
        ("High Discrimination Accuracy", "Ensemble achieves Harrell's Concordance Index of C = 0.824, substantially outperforming random baseline (0.500) and binary models."),
        ("Brier Calibration Concordance", "Minimal Integrated Brier Score (IBS = 0.051) confirms exceptional calibration with near-zero probability error loss over time."),
        ("Youden's J Threshold Calibration", "Decision thresholds mathematically optimized via J = Sensitivity + Specificity - 1 to balance true positives against false alarms."),
        ("Superior Retention Recall", "Outperforms SMOTE-augmented Binary Logistic Regression baseline by +18.4% in departure recall (74.5% vs 63.8%).")
    ]
    build_split_slide(5, "Model Validation, Calibration & Performance Benchmarks",
                      "Full-Width High-Contrast Confusion Matrix Heatmaps Calibrated via Youden's J",
                      s5_bullets, "confusion_matrix.png", "Live Implementation: Side-by-Side Confusion Matrices & ROC-AUC")

    # =========================================================================
    # SLIDE 6: FINANCIAL INTELLIGENCE & ECONOMIC TRIAGE (NOVELTY 2)
    # =========================================================================
    s6_bullets = [
        ("Monetary Attrition Translation", "Converts abstract statistical probabilities into confidence-weighted dollar values, preventing uniform turnover budgeting."),
        ("Expected Lifetime Value (ELV)", "Formulated as: ELV = Monthly Income x Expected Tenure x Performance Multiplier, capturing individual human capital worth."),
        ("Revenue at Risk (RAR)", "Quantified as: RAR = ELV x P(churn) x Confidence_Weight, scaling exposure by prediction certainty to avoid costly over-intervention."),
        ("Composite Urgency Queue", "Ranked via Urgency = 0.6*P(churn) + 0.4*RAR_norm, ensuring high-risk, high-exposure employees receive triage first."),
        ("Dynamic Multi-Horizon Filtering", "Interactive triage controls toggle payroll risk exposure at 30-day ($125K), 60-day, and 90-day ($204K) operational windows.")
    ]
    build_split_slide(6, "Financial Intelligence & Economic Triage Engine",
                      "Novelty 2: Confidence-Weighted Revenue at Risk (RAR) and Priority Urgency Triage",
                      s6_bullets, "financial_triage.png", "Live Implementation: Financial KPIs & Triage Leaderboard")

    # =========================================================================
    # SLIDE 7: EXPLAINABILITY & AI DIAGNOSTIC NARRATIVES (NOVELTY 3)
    # =========================================================================
    s7_bullets = [
        ("TreeSHAP Local & Global Attribution", "Computes exact Shapley attributions across survival forest trees to pinpoint individual departure and retention factors."),
        ("Root-Cause Push Pinpointing", "Identifies dominant departure drivers such as compensation disparity, heavy overtime workload, and promotion stagnation."),
        ("Individual Survival Curves", "Generates continuous survival probability curves over 60 months with empirical 95% Confidence Interval error bands."),
        ("Automated AI Diagnostic Narrative", "Translates mathematical SHAP vectors into managerial plain-English root-cause diagnoses, eliminating guesswork for HR."),
        ("Defensible Retention Decisions", "Provides transparent, interpretable justification for management prior to executing expensive intervention packages.")
    ]
    build_split_slide(7, "Explainability & AI Diagnostic Intelligence",
                      "Novelty 3: TreeSHAP Feature Attributions Coupled with Automated Managerial Narratives",
                      s7_bullets, "diagnostics_shap.png", "Live Implementation: TreeSHAP Attributions & Diagnostic Narrative")

    # =========================================================================
    # SLIDE 8: AUTONOMOUS 5-AGENT RETENTION OPERATIONS
    # =========================================================================
    s8_bullets = [
        ("Observer & Analyst Agents", "Observer ingests workforce telemetry and triggers risk alerts; Analyst evaluates survival curves and extracts top SHAP drivers."),
        ("Strategist & Executor Agents", "Strategist evaluates LinUCB policy expected payoffs; Executor synthesizes production-ready Manager Retention Action Cards."),
        ("Structured Action Cards", "Standardized action cards detail recommended intervention, implementation steps, 30-day timeline, and assigned intervention owners."),
        ("Zero Latency Intervention", "Eliminates weeks of HR deliberation, automating the bridge from flight risk detection to operational retention action."),
        ("Closed-Loop Feedback Agent", "Monitors post-intervention employee status (Stayed vs Left) at 30 days and logs numerical reward signals.")
    ]
    build_split_slide(8, "Autonomous 5-Agent Retention Operations",
                      "Collaborative Multi-Agent Pipeline Synthesizing Standardized Retention Action Cards",
                      s8_bullets, "action_card.png", "Live Implementation: Generated Manager Retention Action Card")

    # =========================================================================
    # SLIDE 9: CLOSED-LOOP POLICY ADAPTATION (NOVELTY 4)
    # =========================================================================
    s9_bullets = [
        ("Contextual Multi-Armed Bandit", "Implements LinUCB reinforcement learning to prescribe personalized retention interventions from employee context vectors."),
        ("10-D Normalized Context Vector", "Encodes tenure, compensation ratio, satisfaction ratings, overtime status, and multi-horizon departure probabilities."),
        ("5 Discrete Intervention Arms", "Salary Review, L&D Offer, Managerial 1:1 Coaching, Flexible Work Schedule, and Targeted Retention Stay Bonus."),
        ("Upper Confidence Bound Selection", "Selects optimal arm via a* = argmax [theta_a^T x_i + alpha * sqrt(x_i^T A_a^-1 x_i)] balancing exploration and exploitation."),
        ("Closed-Loop Bayesian Updates", "Updates ridge regression covariance matrices (A_a <- A_a + x_i x_i^T) in real time, achieving 18.4% uncertainty shrinkage.")
    ]
    build_split_slide(9, "Closed-Loop Reinforcement Learning Policy",
                      "Novelty 4: LinUCB Contextual Bandit Policy with Real-Time Bayesian Covariance Updating",
                      s9_bullets, "linucb_telemetry.png", "Live Implementation: LinUCB Policy Adaptation & Covariance Telemetry")

    # =========================================================================
    # SLIDE 10: CONCLUSION & PROJECT DELIVERABLES
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s10)
    add_header(s10, "Conclusion & Project Deliverables", 
               "Summary of Technical Contributions, Empirical Outcomes, and Operational Deliverables",
               "FINAL DELIVERABLES")

    # 3 Summary Cards across the bottom
    cards_data = [
        ("Technical Contributions", [
            "Continuous Time-to-Event Modeling replacing static binary classifiers.",
            "Concordance-Excess Dynamic Ensemble (Cox PH + RSF) achieving C = 0.824.",
            "Confidence-Weighted Revenue at Risk (RAR) enabling high-ROI triage.",
            "Closed-Loop Reinforcement Learning policy via LinUCB Contextual Bandit."
        ], ACCENT_CYAN, Inches(0.8)),

        ("Empirical Performance", [
            "+18.4% Retention Recall over standard SMOTE Logistic baselines (74.5% vs 63.8%).",
            "Minimal Integrated Brier Score (IBS = 0.051) confirming high probability calibration.",
            "High-contrast Confusion Matrices calibrated via Youden's J statistic.",
            "Quantified protection of over $204K in at-risk payroll across workforce."
        ], ACCENT_EMERALD, Inches(4.8)),

        ("System Deliverables", [
            "Production-ready Python Flask & Gunicorn WSGI web application.",
            "Pre-trained serialized model weights for IBM HR & Healthcare benchmarks.",
            "Modular Vanilla CSS/JS enterprise dashboard with zero bloated dependencies.",
            "Complete research paper documentation, ablation logs, and reproducible codebase."
        ], ACCENT_PURPLE, Inches(8.8))
    ]

    for c_title, c_points, c_accent, c_left in cards_data:
        card = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, Inches(1.7), Inches(3.7), Inches(5.2))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = c_accent
        card.line.width = Pt(1.5)
        ctf = card.text_frame
        ctf.margin_left = Inches(0.25)
        ctf.margin_top = Inches(0.3)
        ctf.margin_right = Inches(0.25)

        p = ctf.paragraphs[0]
        p.text = c_title
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = c_accent
        p.space_after = Pt(14)

        for pt in c_points:
            p = ctf.add_paragraph()
            p.text = f"• {pt}"
            p.font.size = Pt(10.5)
            p.font.color.rgb = TEXT_BODY
            p.space_after = Pt(10)

    # Save presentation
    output_path = os.path.join(os.path.dirname(__file__), "EMPLOYEE_SURVIVAL_PREDICTION_AND_RETENTION_SYSTEM.pptx")
    prs.save(output_path)
    print(f"Presentation successfully generated and saved to: {output_path}")

    # Also save a copy to the root workspace
    root_copy = os.path.join(os.path.dirname(__file__), "..", "EMPLOYEE_SURVIVAL_PREDICTION_AND_RETENTION_SYSTEM.pptx")
    prs.save(root_copy)
    print(f"Presentation copy saved to root: {root_copy}")

if __name__ == '__main__':
    create_presentation()
