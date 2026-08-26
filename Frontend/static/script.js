// ==========================================
// PharmTrack - Netlify Frontend
// MongoDB Atlas + Flask Backend
// ==========================================

const API_BASE_URL = "https://pharmtrack-2.onrender.com";


// ==========================================
// API REQUEST HELPER
// ==========================================

async function apiRequest(endpoint, options = {}) {

    const url = `${API_BASE_URL}${endpoint}`;

    console.log("➡️ API Request:", url);

    try {

        const response = await fetch(url, {
            method: options.method || "GET",
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            },
            body: options.body
        });

        console.log(
            "⬅️ API Status:",
            response.status,
            response.statusText
        );

        const contentType =
            response.headers.get("content-type") || "";

        let data;

        if (contentType.includes("application/json")) {
            data = await response.json();
        } else {
            const text = await response.text();

            data = {
                success: false,
                message: text || "Server returned non-JSON response"
            };
        }

        console.log("📦 API Response:", endpoint, data);

        if (!response.ok) {

            throw new Error(
                data.message ||
                `HTTP ${response.status}`
            );
        }

        return data;

    } catch (error) {

        console.error(
            `❌ API Error [${endpoint}]:`,
            error
        );

        throw error;
    }
}


// ==========================================
// SAFE TEXT
// ==========================================

function setText(id, value) {

    const element = document.getElementById(id);

    if (!element) {
        console.warn(`Element #${id} not found`);
        return;
    }

    element.textContent = value;
}


// ==========================================
// HTML SECURITY
// ==========================================

function escapeHTML(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ==========================================
// DATE FORMAT
// ==========================================

function formatDate(value) {

    if (!value) {
        return "";
    }

    // MongoDB date object
    if (
        typeof value === "object" &&
        value.$date
    ) {
        value = value.$date;
    }

    const parsed = new Date(value);

    if (isNaN(parsed.getTime())) {
        return String(value);
    }

    return parsed
        .toISOString()
        .split("T")[0];
}


// ==========================================
// PROGRESS BAR
// ==========================================

function updateBar(id, value, total) {

    const bar = document.getElementById(id);

    if (!bar) {
        return;
    }

    value = Number(value) || 0;
    total = Number(total) || 0;

    if (total <= 0) {
        bar.style.width = "0%";
        return;
    }

    const percentage = Math.min(
        100,
        Math.round((value / total) * 100)
    );

    bar.style.width = `${percentage}%`;
}


// ==========================================
// TABLE ERROR
// ==========================================

function showTableError(
    tableId,
    colspan,
    title,
    message
) {

    const table = document.getElementById(tableId);

    if (!table) {
        return;
    }

    table.innerHTML = `
        <tr>
            <td colspan="${colspan}">
                <div class="empty">
                    <div class="empty-icon">⚠️</div>

                    <p>${escapeHTML(title)}</p>

                    <small
                        style="
                            display:block;
                            margin-top:6px;
                            color:var(--muted);
                        "
                    >
                        ${escapeHTML(message)}
                    </small>
                </div>
            </td>
        </tr>
    `;
}


// ==========================================
// MEDICINES TABLE
// ==========================================

function loadMedicines(medicines) {

    const table =
        document.getElementById("medicineTable");

    if (!table) {
        console.warn("#medicineTable not found");
        return;
    }

    if (
        !Array.isArray(medicines) ||
        medicines.length === 0
    ) {

        table.innerHTML = `
            <tr>
                <td colspan="11">
                    <div class="empty">
                        <div class="empty-icon">💊</div>
                        <p>No medicines found.</p>
                    </div>
                </td>
            </tr>
        `;

        return;
    }

    table.innerHTML = medicines.map(m => {

        const id =
            m.id ??
            m._id ??
            "";

        const days =
            Number(m.days ?? 0);

        const daysText =
            days < 0
                ? `${Math.abs(days)}d ago`
                : `${days}d`;

        const status =
            String(
                m.status || "safe"
            ).toLowerCase();

        const quantity =
            m.quantity ?? 0;

        const price =
            m.unit_price ??
            m.price ??
            0;

        return `
            <tr>

                <td class="mono">
                    ${escapeHTML(id)}
                </td>

                <td>
                    <div class="name">
                        ${escapeHTML(m.name || "")}
                    </div>
                </td>

                <td style="
                    font-size:12px;
                    color:var(--muted);
                ">
                    ${escapeHTML(m.manufacturer || "")}
                </td>

                <td class="mono">
                    ${escapeHTML(m.batch_number || "")}
                </td>

                <td style="
                    font-size:12px;
                    color:var(--text2);
                ">
                    ${escapeHTML(m.category || "")}
                </td>

                <td class="mono">
                    ${escapeHTML(
                        formatDate(m.expiry_date)
                    )}
                </td>

                <td>
                    <span class="days ${escapeHTML(status)}">
                        ${escapeHTML(daysText)}
                    </span>
                </td>

                <td class="mono">
                    ${escapeHTML(quantity)}
                </td>

                <td class="mono">
                    ₹${escapeHTML(price)}
                </td>

                <td>
                    <span class="badge ${escapeHTML(status)}">
                        ${escapeHTML(status)}
                    </span>
                </td>

                <td>
                    <div style="
                        display:flex;
                        gap:6px;
                    ">

                        <button
                            class="btn btn-ghost btn-sm"
                            onclick="editMedicine('${escapeHTML(id)}')"
                            title="Edit"
                        >
                            ✏️
                        </button>

                        <button
                            class="btn btn-danger btn-sm"
                            onclick="deleteMedicine('${escapeHTML(id)}')"
                            title="Delete"
                        >
                            🗑️
                        </button>

                    </div>
                </td>

            </tr>
        `;

    }).join("");
}


// ==========================================
// STATES TABLE
// ==========================================

function loadStates(states) {

    const table =
        document.getElementById("stateTable");

    if (!table) {
        return;
    }

    if (
        !Array.isArray(states) ||
        states.length === 0
    ) {

        table.innerHTML = `
            <tr>
                <td colspan="3">
                    <div class="empty">
                        <div class="empty-icon">🗺️</div>
                        <p>No distributions yet.</p>
                    </div>
                </td>
            </tr>
        `;

        return;
    }

    table.innerHTML = states.map(s => {

        return `
            <tr>

                <td>
                    <div class="name">
                        ${escapeHTML(
                            s.state_name || ""
                        )}
                    </div>
                </td>

                <td class="mono">
                    ${escapeHTML(
                        s.medicine_count ?? 0
                    )}
                </td>

                <td class="mono">
                    ${escapeHTML(
                        s.total_qty ?? 0
                    )}
                </td>

            </tr>
        `;

    }).join("");
}


// ==========================================
// TRANSFERS TABLE
// ==========================================

function loadTransfers(transfers) {

    const table =
        document.getElementById("transferTable");

    if (!table) {
        return;
    }

    if (
        !Array.isArray(transfers) ||
        transfers.length === 0
    ) {

        table.innerHTML = `
            <tr>
                <td colspan="4">
                    <div class="empty">
                        <div class="empty-icon">🔄</div>
                        <p>No transfers yet.</p>
                    </div>
                </td>
            </tr>
        `;

        return;
    }

    table.innerHTML = transfers.map(t => {

        return `
            <tr>

                <td>
                    <div
                        class="name"
                        style="font-size:12px;"
                    >
                        ${escapeHTML(
                            t.medicine_name || ""
                        )}
                    </div>
                </td>

                <td class="mono">
                    ${escapeHTML(
                        t.from_state || ""
                    )}
                </td>

                <td class="mono">
                    ${escapeHTML(
                        t.to_state || ""
                    )}
                </td>

                <td class="mono">
                    ${escapeHTML(
                        t.quantity ?? 0
                    )}
                </td>

            </tr>
        `;

    }).join("");
}


// ==========================================
// DASHBOARD
// ==========================================

async function loadDashboard() {

    console.log("📊 Loading dashboard...");

    const medicineTable =
        document.getElementById("medicineTable");

    if (medicineTable) {

        medicineTable.innerHTML = `
            <tr>
                <td colspan="11">
                    <div class="empty">
                        <div class="empty-icon">⏳</div>
                        <p>Loading medicines...</p>
                    </div>
                </td>
            </tr>
        `;
    }

    try {

        const data =
            await apiRequest("/api/dashboard");

        console.log(
            "✅ Dashboard response:",
            data
        );

        if (!data) {
            throw new Error(
                "Empty response from backend"
            );
        }

        if (data.success !== true) {
            throw new Error(
                data.message ||
                "Dashboard API returned an error"
            );
        }

        // ======================================
        // STATS
        // ======================================

        const stats =
            data.stats || {};

        const total =
            Number(stats.total) || 0;

        const expired =
            Number(stats.expired) || 0;

        const critical =
            Number(stats.critical) || 0;

        const warning =
            Number(stats.warning) || 0;

        const safe =
            Number(stats.safe) || 0;

        setText("total", total);
        setText("expired", expired);
        setText("critical", critical);
        setText("warning", warning);
        setText("safe", safe);
        setText("inventoryCount", total);

        // ======================================
        // PROGRESS BARS
        // ======================================

        updateBar(
            "expiredBar",
            expired,
            total
        );

        updateBar(
            "criticalBar",
            critical,
            total
        );

        updateBar(
            "warningBar",
            warning,
            total
        );

        updateBar(
            "safeBar",
            safe,
            total
        );

        // ======================================
        // TABLE DATA
        // ======================================

        loadMedicines(
            Array.isArray(data.medicines)
                ? data.medicines
                : []
        );

        loadStates(
            Array.isArray(data.states)
                ? data.states
                : []
        );

        loadTransfers(
            Array.isArray(data.transfers)
                ? data.transfers
                : []
        );

        console.log(
            "✅ Dashboard loaded successfully"
        );

    } catch (error) {

        console.error(
            "❌ Dashboard error:",
            error
        );

        showTableError(
            "medicineTable",
            11,
            "Unable to load medicines.",
            error.message
        );

        showTableError(
            "stateTable",
            3,
            "Unable to load states.",
            error.message
        );

        showTableError(
            "transferTable",
            4,
            "Unable to load transfers.",
            error.message
        );
    }
}


// ==========================================
// SEARCH
// ==========================================

function setupSearch() {

    const searchInput =
        document.getElementById("search");

    if (!searchInput) {
        console.log("Search input not found");
        return;
    }

    searchInput.addEventListener(
        "input",
        function () {

            const query =
                this.value
                    .toLowerCase()
                    .trim();

            document
                .querySelectorAll(
                    "#medicineTable tr"
                )
                .forEach(row => {

                    const text =
                        row.textContent
                            .toLowerCase();

                    row.style.display =
                        text.includes(query)
                            ? ""
                            : "none";
                });
        }
    );
}


// ==========================================
// EDIT MEDICINE
// ==========================================

function editMedicine(id) {

    if (
        id === null ||
        id === undefined ||
        id === ""
    ) {

        alert("Invalid medicine ID.");

        return;
    }

    window.location.href =
        `edit.html?id=${encodeURIComponent(id)}`;
}


// ==========================================
// DELETE MEDICINE
// ==========================================

async function deleteMedicine(id) {

    if (
        id === null ||
        id === undefined ||
        id === ""
    ) {

        alert("Invalid medicine ID.");

        return;
    }

    const confirmed =
        confirm(
            "Delete this medicine? This cannot be undone."
        );

    if (!confirmed) {
        return;
    }

    try {

        const data =
            await apiRequest(
                `/api/medicines/${encodeURIComponent(id)}`,
                {
                    method: "DELETE"
                }
            );

        if (data.success !== true) {

            throw new Error(
                data.message ||
                "Delete failed"
            );
        }

        alert(
            data.message ||
            "Medicine deleted successfully."
        );

        await loadDashboard();

    } catch (error) {

        console.error(
            "❌ Delete error:",
            error
        );

        alert(
            `Unable to delete medicine.\n\n${error.message}`
        );
    }
}


// ==========================================
// BACKEND HEALTH CHECK
// ==========================================

async function checkBackend() {

    console.log(
        "🔍 Checking backend..."
    );

    try {

        const data =
            await apiRequest(
                "/api/health"
            );

        console.log(
            "🏥 Backend health:",
            data
        );

        if (
            data.success === true &&
            data.database === "connected"
        ) {

            console.log(
                "✅ Render + MongoDB Atlas connected"
            );

            return true;
        }

        console.warn(
            "⚠️ Backend connected but database status is:",
            data.database
        );

        return false;

    } catch (error) {

        console.error(
            "❌ Backend health check failed:",
            error
        );

        return false;
    }
}


// ==========================================
// START APPLICATION
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    async function () {

        console.log(
            "===================================="
        );

        console.log(
            "🚀 PharmTrack Frontend Started"
        );

        console.log(
            "Backend:",
            API_BASE_URL
        );

        console.log(
            "===================================="
        );

        setupSearch();

        await checkBackend();

        await loadDashboard();
    }
);