// ==========================================
// PharmTrack - Netlify Frontend
// ==========================================

// IMPORTANT:
// Deploy hone ke baad yahan apna Render backend URL daalna.
//
// Example:
// const API_BASE_URL = "https://pharmtrack-2.onrender.com";

const API_BASE_URL = "https://pharmtrack-2.onrender.com";


// ==========================================
// Load Dashboard
// ==========================================

async function loadDashboard() {

    try {

        const response = await fetch(`${API_BASE_URL}/api/dashboard`);

        if (!response.ok) {
            throw new Error("Backend response error");
        }

        const data = await response.json();

        console.log("Dashboard data:", data);

        // Statistics
        document.getElementById("total").textContent =
            data.stats.total;

        document.getElementById("expired").textContent =
            data.stats.expired;

        document.getElementById("critical").textContent =
            data.stats.critical;

        document.getElementById("warning").textContent =
            data.stats.warning;

        document.getElementById("safe").textContent =
            data.stats.safe;

        document.getElementById("inventoryCount").textContent =
            data.stats.total;


        // Progress bars
        updateBar("expiredBar", data.stats.expired, data.stats.total);
        updateBar("criticalBar", data.stats.critical, data.stats.total);
        updateBar("warningBar", data.stats.warning, data.stats.total);
        updateBar("safeBar", data.stats.safe, data.stats.total);


        // Tables
        loadMedicines(data.medicines || []);
        loadStates(data.states || []);
        loadTransfers(data.transfers || []);


    } catch (error) {

        console.error("Dashboard error:", error);

        document.getElementById("medicineTable").innerHTML = `
            <tr>
                <td colspan="11">
                    <div class="empty">
                        <div class="empty-icon">⚠️</div>
                        <p>
                            Unable to connect to backend.
                        </p>
                    </div>
                </td>
            </tr>
        `;

        document.getElementById("stateTable").innerHTML = `
            <tr>
                <td colspan="3">
                    <div class="empty">
                        <div class="empty-icon">⚠️</div>
                        <p>Unable to load states.</p>
                    </div>
                </td>
            </tr>
        `;

        document.getElementById("transferTable").innerHTML = `
            <tr>
                <td colspan="4">
                    <div class="empty">
                        <div class="empty-icon">⚠️</div>
                        <p>Unable to load transfers.</p>
                    </div>
                </td>
            </tr>
        `;
    }
}


// ==========================================
// Progress Bar
// ==========================================

function updateBar(id, value, total) {

    const bar = document.getElementById(id);

    if (!bar) return;

    if (!total || total <= 0) {
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
// Medicines Table
// ==========================================

function loadMedicines(medicines) {

    const table = document.getElementById("medicineTable");

    if (!table) return;

    if (medicines.length === 0) {

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

        const days = Number(m.days ?? 0);

        const daysText =
            days < 0
                ? `${Math.abs(days)}d ago`
                : `${days}d`;


        return `
            <tr>

                <td class="mono">
                    ${escapeHTML(m.id)}
                </td>

                <td>
                    <div class="name">
                        ${escapeHTML(m.name)}
                    </div>
                </td>

                <td style="font-size:12px;color:var(--muted);">
                    ${escapeHTML(m.manufacturer)}
                </td>

                <td class="mono">
                    ${escapeHTML(m.batch_number)}
                </td>

                <td style="font-size:12px;color:var(--text2);">
                    ${escapeHTML(m.category)}
                </td>

                <td class="mono">
                    ${escapeHTML(m.expiry_date)}
                </td>

                <td>
                    <span class="days ${escapeHTML(m.status)}">
                        ${daysText}
                    </span>
                </td>

                <td class="mono">
                    ${escapeHTML(m.quantity)}
                </td>

                <td class="mono">
                    ₹${escapeHTML(m.unit_price)}
                </td>

                <td>
                    <span class="badge ${escapeHTML(m.status)}">
                        ${escapeHTML(m.status)}
                    </span>
                </td>

                <td>
                    <div style="display:flex;gap:6px;">

                        <button
                            class="btn btn-ghost btn-sm"
                            onclick="editMedicine(${Number(m.id)})">
                            ✏️
                        </button>

                        <button
                            class="btn btn-danger btn-sm"
                            onclick="deleteMedicine(${Number(m.id)})">
                            🗑️
                        </button>

                    </div>
                </td>

            </tr>
        `;

    }).join("");
}


// ==========================================
// State Table
// ==========================================

function loadStates(states) {

    const table = document.getElementById("stateTable");

    if (!table) return;


    if (states.length === 0) {

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


    table.innerHTML = states.map(s => `

        <tr>

            <td>
                <div class="name">
                    ${escapeHTML(s.state_name)}
                </div>
            </td>

            <td class="mono">
                ${escapeHTML(s.medicine_count)}
            </td>

            <td class="mono">
                ${escapeHTML(s.total_qty)}
            </td>

        </tr>

    `).join("");
}


// ==========================================
// Transfers Table
// ==========================================

function loadTransfers(transfers) {

    const table = document.getElementById("transferTable");

    if (!table) return;


    if (transfers.length === 0) {

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


    table.innerHTML = transfers.map(t => `

        <tr>

            <td>
                <div class="name" style="font-size:12px;">
                    ${escapeHTML(t.medicine_name)}
                </div>
            </td>

            <td class="mono">
                ${escapeHTML(t.from_state)}
            </td>

            <td class="mono">
                ${escapeHTML(t.to_state)}
            </td>

            <td class="mono">
                ${escapeHTML(t.quantity)}
            </td>

        </tr>

    `).join("");
}


// ==========================================
// Search
// ==========================================

const searchInput = document.getElementById("search");

if (searchInput) {

    searchInput.addEventListener("input", function () {

        const query = this.value.toLowerCase().trim();

        document
            .querySelectorAll("#medicineTable tr")
            .forEach(row => {

                row.style.display =
                    row.textContent.toLowerCase().includes(query)
                        ? ""
                        : "none";

            });

    });

}


// ==========================================
// Edit Medicine
// ==========================================

function editMedicine(id) {

    window.location.href = `edit.html?id=${id}`;

}


// ==========================================
// Delete Medicine
// ==========================================

async function deleteMedicine(id) {

    const confirmed = confirm(
        "Delete this medicine? This cannot be undone."
    );

    if (!confirmed) return;


    try {

        const response = await fetch(
            `${API_BASE_URL}/api/medicines/${id}`,
            {
                method: "DELETE"
            }
        );


        if (!response.ok) {

            throw new Error(
                "Delete request failed"
            );

        }


        alert("Medicine deleted successfully.");

        loadDashboard();


    } catch (error) {

        console.error(error);

        alert(
            "Unable to delete medicine. Please try again."
        );

    }

}


// ==========================================
// HTML Security
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
// Count Animation
// ==========================================

function animateValue(element, target) {

    if (!element) return;

    target = Number(target) || 0;

    let current = 0;

    const step = Math.max(
        1,
        Math.ceil(target / 30)
    );

    const timer = setInterval(() => {

        current += step;

        if (current >= target) {
            current = target;
            clearInterval(timer);
        }

        element.textContent = current;

    }, 20);
}


// ==========================================
// Start Dashboard
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadDashboard();

    }
);