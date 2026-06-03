// ============================================
// System Developer — Pipeline SocketIO Client
// ============================================

const socket = io();
let currentSessionId = null;
let currentIteration = 1;

// --- Elements ---
const requirementInput = document.getElementById("requirement-input");
const btnBuild = document.getElementById("btn-build");
const btnClear = document.getElementById("btn-clear");
const pipelineSection = document.getElementById("pipeline-section");
const pipelineStages = document.getElementById("pipeline-stages");
const errorSection = document.getElementById("error-section");
const errorMessage = document.getElementById("error-message");
const completionSection = document.getElementById("completion-section");
const completionSummary = document.getElementById("completion-summary");
const samplesSection = document.getElementById("samples-section");
const pipelineStatusBadge = document.getElementById("pipeline-status-badge");

// Pipeline stage definitions
const STAGES = [
    { agent: "industry_sme", label: "Industry SME", icon: "bi-lightbulb", desc: "Elaborating requirements" },
    { agent: "business_analyst", label: "Business Analyst", icon: "bi-list-check", desc: "Creating product backlog" },
    { agent: "product_owner", label: "Product Owner", icon: "bi-bullseye", desc: "Scoping MVP" },
    { agent: "architect", label: "Architect", icon: "bi-diagram-3", desc: "Designing system" },
    { agent: "frontend_developer", label: "Frontend Developer", icon: "bi-palette", desc: "Generating UI code" },
    { agent: "backend_developer", label: "Backend Developer", icon: "bi-server", desc: "Generating backend code" },
    { agent: "execution_instructor", label: "Execution Instructor", icon: "bi-terminal", desc: "Writing run instructions" },
    { agent: "qa_tester", label: "QA Tester", icon: "bi-bug", desc: "Testing & validation" },
    { agent: "business_validator", label: "Business Validator", icon: "bi-shield-check", desc: "Reviewing alignment" },
    { agent: "technical_writer", label: "Technical Writer", icon: "bi-book", desc: "Producing documentation" },
];

// --- Socket Events ---

socket.on("connect", () => {
    console.log("[System Developer] Connected");
});

socket.on("pipeline_started", (data) => {
    console.log("[Pipeline] Started:", data);
    currentIteration = data.iteration || 1;
});

socket.on("stage_update", (data) => {
    updateStage(data.agent, data.status, data.desc);
});

socket.on("board_update", (data) => {
    // Show board section if hidden
    const boardSection = document.getElementById("board-section");
    if (boardSection) boardSection.classList.remove("d-none");
    // Render board
    if (typeof renderBoard === "function" && document.getElementById("project-board")) {
        renderBoard(data.board_state);
    }
});

socket.on("pipeline_complete", (data) => {
    console.log("[Pipeline] Complete:", data);
    setBuildState(false);

    if (pipelineStatusBadge) {
        pipelineStatusBadge.textContent = "Complete";
        pipelineStatusBadge.className = "badge bg-success-subtle text-success";
    }

    // Show completion section
    if (completionSection) {
        completionSection.classList.remove("d-none");
        const count = data.artifacts_count || 0;
        completionSummary.textContent = `${count} artifacts generated across all pipeline stages.`;

        const dashLink = document.getElementById("btn-view-dashboard");
        if (dashLink) {
            dashLink.href = `/session/${data.session_id}`;
        }
    }

    toast("Pipeline complete!", "success");
});

socket.on("pipeline_error", (data) => {
    console.error("[Pipeline] Error:", data);
    setBuildState(false);

    if (pipelineStatusBadge) {
        pipelineStatusBadge.textContent = "Error";
        pipelineStatusBadge.className = "badge bg-danger-subtle text-danger";
    }

    // Build a user-friendly hint based on the structured error_code
    const hints = {
        "token_limit":    "💡 Tip: Your requirement may be too long. Try breaking it into smaller pieces.",
        "empty_response": "💡 Tip: The model may have hit a context or iteration limit. Simplify your input.",
        "server_busy":    "💡 Tip: Neuro SAN is still processing a previous request. Wait 30 seconds and retry.",
        "rate_limit":     "💡 Tip: API rate limit hit. Wait 60 seconds before retrying.",
        "api_overloaded": "💡 Tip: The LLM API is overloaded. Wait a few minutes and retry.",
        "timeout":        "💡 Tip: Request timed out. For complex tasks, this can happen — try again.",
        "connection":     "💡 Tip: Cannot reach Neuro SAN. Make sure it is running on port 8080.",
    };
    const hint = hints[data.error_code] || "";
    const fullMsg = hint ? `${data.msg}\n\n${hint}` : data.msg;

    errorSection.classList.remove("d-none");
    errorMessage.textContent = fullMsg;
    toast(data.msg, "error");
});

// --- UI Functions ---

function renderStages() {
    pipelineStages.innerHTML = "";
    STAGES.forEach((stage) => {
        const div = document.createElement("div");
        div.className = "stage-item";
        div.id = `stage-${stage.agent}`;
        div.innerHTML = `
            <div class="stage-icon pending" id="icon-${stage.agent}">
                <i class="bi ${stage.icon}"></i>
            </div>
            <div class="stage-info">
                <span class="stage-label" id="label-${stage.agent}">${stage.label}</span>
                <span class="stage-desc text-muted" id="desc-${stage.agent}">Waiting...</span>
            </div>
        `;
        pipelineStages.appendChild(div);
    });
}

function updateStage(agent, status, desc) {
    const icon = document.getElementById(`icon-${agent}`);
    const descEl = document.getElementById(`desc-${agent}`);
    if (!icon) return;

    // Update icon class
    icon.className = `stage-icon ${status}`;

    // Update icon content
    if (status === "completed") {
        icon.innerHTML = '<i class="bi bi-check-lg"></i>';
    } else if (status === "active") {
        icon.innerHTML = '<i class="bi bi-arrow-repeat spin"></i>';
    } else if (status === "error") {
        icon.innerHTML = '<i class="bi bi-x-lg"></i>';
    }

    // Update description
    if (descEl && desc) {
        descEl.textContent = desc;
        if (status === "completed") descEl.classList.add("text-success");
        else if (status === "active") { descEl.classList.remove("text-muted"); descEl.classList.add("text-accent"); }
        else if (status === "error") descEl.classList.add("text-danger");
    }
}

function setBuildState(building) {
    if (!btnBuild) return;
    btnBuild.disabled = building;
    if (building) {
        btnBuild.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Building...';
        btnBuild.classList.add("disabled");
    } else {
        btnBuild.innerHTML = '<i class="bi bi-rocket me-1"></i> Build It';
        btnBuild.classList.remove("disabled");
    }
}

// --- Build Action ---

if (btnBuild) {
    btnBuild.addEventListener("click", async () => {
        const requirement = requirementInput.value.trim();
        if (!requirement) {
            requirementInput.focus();
            requirementInput.classList.add("is-invalid");
            setTimeout(() => requirementInput.classList.remove("is-invalid"), 2000);
            return;
        }

        // Reset UI
        errorSection.classList.add("d-none");
        if (completionSection) completionSection.classList.add("d-none");
        pipelineSection.classList.remove("d-none");
        if (samplesSection) samplesSection.classList.add("d-none");
        renderStages();
        setBuildState(true);

        if (pipelineStatusBadge) {
            pipelineStatusBadge.textContent = "Running";
            pipelineStatusBadge.className = "badge bg-accent-subtle text-accent";
        }

        // Create session via REST
        try {
            const resp = await fetch("/api/build", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ requirement }),
            });
            const data = await resp.json();

            if (!data.ok) {
                errorSection.classList.remove("d-none");
                errorMessage.textContent = data.msg;
                setBuildState(false);
                return;
            }

            currentSessionId = data.session_id;
            currentIteration = data.iteration || 1;

            // Start pipeline via SocketIO
            socket.emit("start_pipeline", {
                requirement: requirement,
                session_id: currentSessionId,
                iteration: currentIteration,
            });

            toast("Pipeline started! AI agents are working...", "success");

        } catch (err) {
            errorSection.classList.remove("d-none");
            errorMessage.textContent = "Connection failed: " + err.message;
            setBuildState(false);
        }
    });
}

// --- Clear Action ---

if (btnClear) {
    btnClear.addEventListener("click", () => {
        requirementInput.value = "";
        pipelineSection.classList.add("d-none");
        errorSection.classList.add("d-none");
        if (completionSection) completionSection.classList.add("d-none");
        if (samplesSection) samplesSection.classList.remove("d-none");
        requirementInput.focus();
    });
}

// --- Enter key to submit ---
if (requirementInput) {
    requirementInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            btnBuild.click();
        }
    });
}
