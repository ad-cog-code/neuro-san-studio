// ============================================
// System Developer — Project Board (Kanban)
// ============================================

const BOARD_COLUMNS = ["Backlog", "Scoped", "Designed", "Developed", "Tested", "Validated", "Documented"];

const COLUMN_COLORS = {
    "Backlog": "#6b7280",
    "Scoped": "#818cf8",
    "Designed": "#c084fc",
    "Developed": "#34d399",
    "Tested": "#fbbf24",
    "Validated": "#22c55e",
    "Documented": "#60a5fa",
};

const PRIORITY_CLASSES = {
    "Must-Have": "priority-must",
    "Should-Have": "priority-should",
    "Nice-to-Have": "priority-nice",
};

let previousPositions = {};

function renderBoard(boardState) {
    const container = document.getElementById("project-board");
    if (!container) return;

    if (!boardState || !boardState.columns) {
        container.innerHTML = `
            <div class="board-empty">
                <i class="bi bi-kanban fs-2 d-block mb-2"></i>
                <span>Stories will appear here as agents complete their work</span>
            </div>`;
        return;
    }

    // Track which stories moved
    const newPositions = {};
    if (boardState.stories) {
        Object.entries(boardState.stories).forEach(([id, s]) => {
            newPositions[id] = s.column;
        });
    }

    container.innerHTML = "";

    BOARD_COLUMNS.forEach((colName) => {
        const stories = boardState.columns[colName] || [];
        const col = document.createElement("div");
        col.className = "board-column";

        const color = COLUMN_COLORS[colName] || "#6b7280";
        col.innerHTML = `
            <div class="board-column-header" style="border-top: 3px solid ${color}">
                <span class="board-column-name">${colName}</span>
                <span class="board-column-count" style="background: ${color}20; color: ${color}">${stories.length}</span>
            </div>
            <div class="board-column-body"></div>
        `;

        const body = col.querySelector(".board-column-body");
        stories.forEach((story) => {
            const card = createBoardCard(story);
            // Animate if story just moved to this column
            if (previousPositions[story.id] && previousPositions[story.id] !== colName) {
                card.classList.add("entering");
            }
            body.appendChild(card);
        });

        container.appendChild(col);
    });

    previousPositions = newPositions;
}

function createBoardCard(story) {
    const card = document.createElement("div");
    const priorityCls = PRIORITY_CLASSES[story.priority] || "";
    card.className = `board-card ${priorityCls}`;

    const pointsBadge = story.points ? `<span class="board-card-points">${story.points}pt</span>` : "";
    const epicBadge = story.epic ? `<span class="board-card-epic">${story.epic_id || ""}</span>` : "";

    card.innerHTML = `
        <div class="board-card-header">
            <span class="board-card-id">${story.id}</span>
            ${pointsBadge}
        </div>
        <div class="board-card-title">${truncate(story.title, 50)}</div>
        <div class="board-card-footer">
            ${epicBadge}
            <span class="board-card-priority">${story.priority || ""}</span>
        </div>
    `;

    return card;
}

function truncate(str, len) {
    if (!str) return "";
    return str.length > len ? str.substring(0, len) + "..." : str;
}
