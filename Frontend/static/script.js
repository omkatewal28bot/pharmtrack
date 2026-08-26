// ==========================================
// PharmTrack - Netlify Frontend
// MongoDB Atlas + Flask Backend
// ==========================================

// ==========================================
// BACKEND URL
// ==========================================

const API_BASE_URL = "https://pharmtrack-2.onrender.com";


// ==========================================
// API HELPER
// ==========================================

async function apiRequest(endpoint, options = {}) {

    const url = `${API_BASE_URL}${endpoint}`;

    console.log("API Request:", url);

    try {

        const response = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        });

        const contentType =
            response.headers.get("content-type") || "";

        let data;

        if (contentType.includes("application/json")) {

            data = await response.json();

        } else {

            const text = await response.text();

            data = {
                success: false,
                message: text || "Server returned a non-JSON response"
            };
        }


        console.log("API Response:", endpoint, data);


        if (!response.ok) {

            throw new Error(
                data.message ||
                `Request failed with status ${response.status}`
            );
        }


        return data;

    } catch (error) {

        console.error(
            `API Error [${endpoint}]:`,
            error
        );

        throw error;
    }
}


// ==========================================
// DASHBOARD
// ==========================================

async function loadDashboard() {

    const medicineTable =
        document.getElementById("medicineTable");

    const stateTable =
        document.getElementById("stateTable");

    const transferTable =
        document.getElementById("transferTable");


    try {

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


        const data =
            await apiRequest("/api/dashboard");


        console.log(
            "Dashboard loaded successfully:",
            data
        );


        // ======================================
        // CHECK RESPONSE
        // ======================================

        if (!data.success) {

            throw new Error(
                data.message ||
                "Dashboard request failed"
            );
        }


        // ======================================
        // STATS
        // ======================================

        const stats = data.stats || {};

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
        // TABLES
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


    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );


        showTableError(
            "medicineTable",
            11,
            "Unable to connect to backend.",
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
// SAFE TEXT
// ==========================================

function setText(id, value) {

    const element =
        document.getElementById(id);

    if (!element) return;

    element.textContent = value;
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

    const table =
        document.getElementById(tableId);

    if (!table) return;


    table.innerHTML = `
        <tr>
            <td colspan="${colspan}">
                <div class="empty">
                    <div class="empty-icon">⚠️</div>
                    <p>${escapeHTML(title)}</p>

                    <small style="
                        display:block;
                        margin-top:6px;
                        color:var(--muted);
                    ">
                        ${escapeHTML(message)}
                    </small>
                </div>
            </td>
        </tr>
    `;
}


// ==========================================
// PROGRESS BAR
// ==========================================

function updateBar(
    id,
    value,
    total
) {

    const bar =
        document.getElementById(id);

    if (!bar) return;


    if (!total || total <= 0) {

        bar.style.width = "0%";

        return;
    }


    const percentage =
        Math.min(
            100,
            Math.round(
                (Number(value) / Number(total)) * 100
            )
        );


    bar.style.width =
        `${percentage}%`;
}


// ==========================================
// MEDICINES TABLE
// ==========================================

function loadMedicines(medicines) {

    const table =
        document.getElementById("medicineTable");

    if (!table) return;


    if (!Array.isArray(medicines) ||
        medicines.length === 0) {

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


    table.innerHTML =
        medicines.map(m => {

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
                            ${escapeHTML(
                                m.name || ""
                            )}
                        </div>
                    </td>


                    <td style="
                        font-size:12px;
                        color:var(--muted);
                    ">
                        ${escapeHTML(
                            m.manufacturer || ""
                        )}
                    </td>


                    <td class="mono">
                        ${escapeHTML(
                            m.batch_number || ""
                        )}
                    </td>


                    <td style="
                        font-size:12px;
                        color:var(--text2);
                    ">
                        ${escapeHTML(
                            m.category || ""
                        )}
                    </td>


                    <td class="mono">
                        ${escapeHTML(
                            formatDate(
                                m.expiry_date
                            )
                        )}
                    </td>


                    <td>

                        <span class="
                            days
                            ${escapeHTML(status)}
                        ">
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

                        <span class="
                            badge
                            ${escapeHTML(status)}
                        ">
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
                                onclick="
                                    editMedicine(
                                        '${escapeJS(id)}'
                                    )
                                "
                                title="Edit"
                            >
                                ✏️
                            </button>


                            <button
                                class="btn btn-danger btn-sm"
                                onclick="
                                    deleteMedicine(
                                        '${escapeJS(id)}'
                                    )
                                "
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

    if (!table) return;


    if (!Array.isArray(states) ||
        states.length === 0) {

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


    table.innerHTML =
        states.map(s => `

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

        `).join("");
}


// ==========================================
// TRANSFERS TABLE
// ==========================================

function loadTransfers(transfers) {

    const table =
        document.getElementById(
            "transferTable"
        );

    if (!table) return;


    if (!Array.isArray(transfers) ||
        transfers.length === 0) {

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


    table.innerHTML =
        transfers.map(t => `

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

        `).join("");
}


// ==========================================
// SEARCH
// ==========================================

function setupSearch() {

    const searchInput =
        document.getElementById(
            "search"
        );

    if (!searchInput) return;


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

        alert(
            "Invalid medicine ID."
        );

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

        alert(
            "Invalid medicine ID."
        );

        return;
    }


    const confirmed =
        confirm(
            "Delete this medicine? This cannot be undone."
        );


    if (!confirmed) return;


    try {

        const data =
            await apiRequest(
                `/api/medicines/${encodeURIComponent(id)}`,
                {
                    method: "DELETE"
                }
            );


        if (!data.success) {

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
            "Delete error:",
            error
        );


        alert(
            `Unable to delete medicine.\n\n${error.message}`
        );
    }
}


// ==========================================
// HTML SECURITY
// ==========================================

function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );
}


// ==========================================
// JAVASCRIPT STRING SECURITY
// ==========================================

function escapeJS(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)
        .replace(
            /\\/g,
            "\\\\"
        )
        .replace(
            /'/g,
            "\\'"
        )
        .replace(
            /\r/g,
            "\\r"
        )
        .replace(
            /\n/g,
            "\\n"
        );
}


// ==========================================
// DATE FORMAT
// ==========================================

function formatDate(value) {

    if (!value) return "";


    // MongoDB date object support
    if (
        typeof value === "object" &&
        value.$date
    ) {

        value = value.$date;
    }


    const date =
        new Date(value);


    if (
        isNaN(
            date.getTime()
        )
    ) {

        return String(value);
    }


    // Keep YYYY-MM-DD format
    return date
        .toISOString()
        .split("T")[0];
}


// ==========================================
// COUNT ANIMATION
// ==========================================

function animateValue(
    element,
    target
) {

    if (!element) return;


    target =
        Number(target) || 0;


    let current = 0;


    const step =
        Math.max(
            1,
            Math.ceil(
                target / 30
            )
        );


    const timer =
        setInterval(() => {

            current += step;


            if (
                current >= target
            ) {

                current = target;

                clearInterval(
                    timer
                );
            }


            element.textContent =
                current;

        }, 20);
}


// ==========================================
// BACKEND HEALTH CHECK
// ==========================================

async function checkBackend() {

    try {

        const data =
            await apiRequest(
                "/api/health"
            );


        console.log(
            "Backend health:",
            data
        );


        if (data.success) {

            console.log(
                "✅ Backend + MongoDB connected"
            );

        } else {

            console.warn(
                "⚠️ Backend reachable but database error:",
                data.message
            );
        }


    } catch (error) {

        console.error(
            "❌ Backend health check failed:",
            error
        );
    }
}


// ==========================================
// START APPLICATION
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        console.log(
            "================================="
        );

        console.log(
            "PharmTrack Frontend Started"
        );

        console.log(
            "Backend:",
            API_BASE_URL
        );

        console.log(
            "================================="
        );


        setupSearch();


        await checkBackend();


        await loadDashboard();

    }
);