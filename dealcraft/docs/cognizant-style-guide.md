# DealCraft — Consolidated Cognizant Style Guide
> Sources: Wells Fargo API Migration RFP + Response | Scotiabank PEGA Smart Dispute RFP + Response
> Version: v0.3.0 | Last Updated: 2026-03-26
> Purpose: Complete agent tailoring baseline — the full "Cognizant DNA"

---

## 1. NEW FINDINGS FROM SCOTIABANK PROPOSAL (Additions to v0.2.0)

### 1.1 New Section — "Your Ask, Our Take" (Enhanced Executive Summary)
The Scotiabank proposal uses a **4-row table format** for the Executive Summary — different from Wells Fargo's 5-box layout:

| Row | Label | Content |
|-----|-------|---------|
| Row 1 | Our Understanding of [Client]'s Objectives | 3–4 bullets — client goals in their language |
| Row 2 | Solution Highlights | 4–5 bullets — what Cognizant proposes to build/deliver |
| Row 3 | Our Approach | 5–6 bullets — how Cognizant will execute |
| Row 4 | Cognizant Differentiators | 5 icon cards — short, bold differentiators in visual tile format |

**Bottom banner** (full width, dark background): A commitment statement — always ends with a relationship/partnership message.
Example: *"Cognizant is committed to establish a best-in-class Team to augment strategic nature of this engagement and look forward to further strengthening this relationship through delivery, innovation, transformation and Investments"*

**Rule**: Use the 4-row table when the client is an existing account. Use the 5-box layout for new prospects.

---

### 1.2 New Section — Relationship / Account History Slide
For existing accounts, always include a **"Trusted Partner" timeline slide** showing:
- Year-by-year delivery history with the client
- Specific programs/upgrades delivered each year
- Visual timeline format
- Headline: *"A Trusted Partner delivering value to [Client] across a Decade of Delivery"* (adapt years as needed)

**Why it matters**: Shows continuity, reduces risk perception, proves the relationship is real — not a new vendor pitch.

---

### 1.3 New Section — Clear Delivery Ownership & Shared Responsibilities
A 3-panel slide clearly showing:
- **Activities** (Cognizant-owned): Planning, Architecture, Development, Testing, DevOps, Go-Live
- **Out of Scope** (explicit list): Infrastructure, Business User Testing, End-user training, etc.
- **Expectation from [Client]**: What Cognizant needs from the client — SMEs, test data, APIs, infra access

**Rule**: Always be explicit about what the client owns. This prevents scope disputes and builds trust.

---

### 1.4 New Section — Quality Gates & Definition of Done
Present a 6-gate quality framework aligned to client's standards:
1. Test Planning (test plan, traceability to user stories)
2. Test Case Readiness (scenarios for all functional/non-functional requirements)
3. System Testing & QAT (IST/QAT execution, defect thresholds)
4. Non-Functional Testing (performance, scalability, reliability)
5. DSAT & SAST Security Scan (specific tools: Web Inspect, Black Duck, Checkmarx)
6. Test Completion & Documentation (exit report, audit evidence)

**Rule**: Always align definition of done to the **client's own gating criteria** — use their templates and terminology.

---

### 1.5 New Section — Organizational Change Management (OCM)
For large transformation programs, include an OCM section with a Gantt showing:
- Assessment & Planning (discovery, change impact assessment, stakeholder analysis)
- Training (needs assessment, curriculum development, content development, training sessions)
- Communications & Engagement (planning, execution, office hours, change agent engagement)
- Adoption measurement and reporting

---

### 1.6 New Section — Risk Register (Formal Table)
Present risks as a formal table:
| Area | Possible Risk Scenario | Impact | Mitigation Planning |
- Always include 5–6 rows minimum
- Impact levels: High / Medium / Low
- Mitigation must be specific — not generic "we will monitor"

---

### 1.7 New Section — Dependencies on Client (Numbered Table)
| Sl. No | Activity | Details |
- Numbered list, not bullets
- Specific to the engagement
- Includes SLA expectations (e.g., "24-hour response SLA")

---

### 1.8 New Case Study Format — 3-Section Vertical Layout
The Scotiabank proposal uses a different case study format:
```
Case Study Title (left panel, large text)
Client description (italics below)

| Business Goal | (section)
[3–4 bullet points]

| Solution | (section)
[4–6 bullet points]

| Outcomes | (section)
[4–5 bullet points with specific metrics]
```
This is used for **detailed case studies** (appendix). The 3-column horizontal format is used for **quick case study summaries** (main body).

---

### 1.9 "Future-Ready" / Technology Roadmap Slide
For platform/product implementations, include a forward-looking slide showing:
- 5 future themes aligned to the vendor's roadmap (e.g., PEGA Infinity Agentic Vision)
- For each theme: Future Components + How it helps [Client]
- **Purpose**: Shows you're not just solving today's problem — you're building for tomorrow

---

### 1.10 New Headline Positioning Language
From Scotiabank proposal, the "Why Cognizant" headline uses:
*"The Lowest-Risk, Highest-Confidence Partner for [Client]'s [Program Name]"*

This is more powerful than generic "Why Cognizant" — use it when Cognizant has a long account relationship.

---

## 2. NEW DIFFERENTIATORS (from Scotiabank proposal)

### PEGA-Specific (use when relevant)
- **World's largest PEGA partner of choice** — 3200+ PEGA consultants, 3000+ certified, 125+ CLSAs
- **26+ years** strong PEGA partnership — Global Elite PEGA Partner
- **1800+ successful PEGA projects**, 200+ clients globally
- **21 consecutive PEGAWorld Awards** including 2025 PEGA Partner of the Year
- **120+ Smart Dispute certified consultants**, 1200+ person-years experience
- **25+ PEGA Smart Dispute successful deliveries**
- Recognized by Everest Group (Leader, PEGA Services PEAK Matrix 2024), HFS (Podium Winner), Forrester (Leader, Digital Process Automation Q3 2020)

### PEGA Accelerators with specific metrics:
| Accelerator | What it does | Benefit |
|-------------|-------------|---------|
| XRACT GPT | GenAI user story grooming | 40–50%+ improvement |
| Automatic Code Review Tool | Scans rules against best practices | 30–40% review effort reduction |
| PEGA GenAI Auto Fixer | Auto-fixes 30+ categories in 15K+ rules in <2 min | 15–25% defect resolution time reduction |
| PEGA GenAI Audit Abstractor | Identifies performance/guardrail issues | 25–35% RCA time reduction |
| AI-Based Automation Script Accelerator | Creates/regenerates test assets for PEGA Infinity | 20–30% QA cycle time reduction |

### General differentiators reinforced:
- **LATAM Presence**: 4500+ associates, 9 countries, 12 cities, 150+ clients, 18+ years
- **Bilingual delivery**: Spanish-speaking PEGA capability across Mexico, LATAM, and Spain (Valladolid)
- **Day 1 Ready team**: Pre-identified profiles, no ramp-up delay
- **Handbook of lessons learned**: Codified learnings from 25+ similar implementations

---

## 3. PROPOSAL STRUCTURE — COMPLETE TEMPLATE (v0.3.0)

### Table of Contents (Standard Cognizant Order)
1. Your Ask, Our Take (Executive Summary)
2. Our Understanding of Scope
3. Our Solution Approach
4. Our Execution Approach
5. Timeline & Estimates
6. Team Structure
7. Assumptions and Dependencies
8. Appendix (Practice overview + Case Studies)

---

## 4. EXECUTIVE SUMMARY VARIATIONS

### Variation A — Existing Account (use Scotiabank format)
- 4-row table: Objectives | Solution Highlights | Our Approach | Differentiators
- Include relationship timeline slide immediately after
- Lead differentiator: "Proven in [existing engagement], Reusable for [new scope]"
- Headline: "The Lowest-Risk, Highest-Confidence Partner for [Program]"

### Variation B — New Prospect (use Wells Fargo format)
- 5-box layout: Your Ask | Cognizant's Solution | Key Differentiators | Key Outcomes | Engagement Details
- Lead with domain credentials and similar client references
- Headline: "Why Cognizant Is Confident in Delivering This Transformation"

---

## 5. COMPLETE DIFFERENTIATOR ARSENAL (Consolidated)

### Tier 1 — Always use (universal)
- GenAI-powered delivery with proprietary accelerators (20–30% effort savings)
- Factory-based execution model (parallel pods, predictable throughput)
- Foundation-first approach (build tools before scale)
- Evidence-driven quality engineering (CI-integrated, automated evidence)
- Transparent assumptions and dependency management

### Tier 2 — Use when relevant
- Google Cloud: Diamond Partner, 8200+ certified, 2025 Data Analytics Partner of Year
- IBM: Platinum Partner, 200+ DataPower experts, IBM Beacon Award winner
- PEGA: World's largest partner, 3000+ certified, 21 consecutive PEGAWorld Awards
- Cognizant financial investment ($200K–$300K) in tools built in client ecosystem

### Tier 3 — Account-specific
- Existing account: Years of delivery history, embedded ecosystem knowledge, zero ramp-up
- LATAM/multilingual: 4500+ associates, bilingual capability, 9 countries
- Industry-specific CoE credentials

---

## 6. TONE & STYLE — REINFORCED RULES (from both proposals)

| Rule | Example |
|------|---------|
| **Show-n-tell sessions** as governance | Not just "status meetings" — "continuous show-n-tell sessions to Scotiabank SMEs" |
| **OOTB-first philosophy** | Always state OOTB preference before customization — reduces risk, eases upgrades |
| **Reuse language** | "Proven in Canada, Reusable Across LATAM" — shows efficiency, not re-invention |
| **Guardrail score** specificity | Don't say "high quality" — say "Guard Rail score of 90%+" |
| **Hypercare** in timeline | Always include post-go-live stabilization as a named phase |
| **Anchor + extend** pattern | First deployment is anchor ("Mexico as anchor implementation"), then extend to others |

---

## 7. PRICING FORMATS (both formats observed)

### Format A (Wells Fargo style) — Track-by-track fixed bid:
| Track | Duration | Cost |
| Cognizant Investment | — | -$300K |
| **Net Cost** | | **$X** |

### Format B (Scotiabank style) — MVP-by-MVP with Dev/Testing split:
| Sl.# | Release | Description | Peak Team | Dev | Testing | Total |
| Change Management & Training | | | | | | $X |
| **TOTAL** | | | | | | **$X** |

---

## 8. RED LINES — WHAT COGNIZANT NEVER DOES (reinforced)
- Never presents a generic proposal — always mirrors the client's exact release/MVP/track structure
- Never omits the assumptions section — always numbered, always specific
- Never ignores existing relationship context — always leverages delivery history
- Never presents risk without mitigation — every risk has a specific counter-strategy
- Never uses generic quality statements — always ties to specific tools, metrics, or thresholds