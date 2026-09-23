/**
 * ShortPulse URL Shortener & Analytics System - Master Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const BASE_URL = window.location.origin;

    // DOM References - Workbench & Form
    const shortenForm = document.getElementById("shorten-form");
    const longUrlInput = document.getElementById("long-url");
    const pasteBtn = document.getElementById("paste-btn");
    const clearBtn = document.getElementById("clear-btn");
    const submitBtn = document.getElementById("submit-btn");
    const urlValidationHint = document.getElementById("url-validation-hint");
    const hintText = document.getElementById("hint-text");

    const aliasDomainPrefix = document.getElementById("alias-domain-prefix");
    const customAliasInput = document.getElementById("custom-alias");
    const customExpiresInInput = document.getElementById("custom-expires-in");
    const tabChips = document.querySelectorAll(".tab-chip");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const presetBtns = document.querySelectorAll(".preset-btn");

    // Result Card References
    const resultCard = document.getElementById("result-card");
    const resultShortUrl = document.getElementById("result-short-url");
    const resultCreatedTime = document.getElementById("result-created-time");
    const copyResultBtn = document.getElementById("copy-result-btn");
    const testRedirectLink = document.getElementById("test-redirect-link");
    const openQrModalBtn = document.getElementById("open-qr-modal-btn");
    const inspectResultBtn = document.getElementById("inspect-result-btn");

    // Analytics Panel References
    const analyticsInput = document.getElementById("analytics-input");
    const analyticsSubmitBtn = document.getElementById("analytics-submit-btn");
    const analyticsCanvas = document.getElementById("analytics-canvas");

    // Table & Pagination References
    const linksTbody = document.getElementById("links-tbody");
    const refreshTableBtn = document.getElementById("refresh-table-btn");
    const tableSearchInput = document.getElementById("table-search-input");
    const filterChips = document.querySelectorAll(".filter-chip");
    const prevPageBtn = document.getElementById("prev-page");
    const nextPageBtn = document.getElementById("next-page");
    const pageIndicator = document.getElementById("page-indicator");
    const paginationInfo = document.getElementById("pagination-info");

    // Modal References
    const qrModal = document.getElementById("qr-modal");
    const closeQrModal = document.getElementById("close-qr-modal");
    const qrcodeWrapper = document.getElementById("qrcode-wrapper");
    const qrTargetUrl = document.getElementById("qr-target-url");
    const copyQrLinkBtn = document.getElementById("copy-qr-link-btn");
    const downloadQrBtn = document.getElementById("download-qr-btn");

    // State Variables
    let currentPage = 1;
    const pageLimit = 5;
    let selectedExpiryMinutes = null;
    let activeFilter = "all";
    let allLinksData = [];

    // Initialize Domain Prefix & Table
    if (aliasDomainPrefix) {
        aliasDomainPrefix.textContent = `${BASE_URL.replace(/^https?:\/\//, '')}/`;
    }
    fetchLinks(currentPage);

    // Clipboard Paste Helper
    pasteBtn.addEventListener("click", async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                longUrlInput.value = text;
                toggleInputState();
                showToast("Pasted link from clipboard", "info");
            }
        } catch (e) {
            showToast("Clipboard permission required to paste", "error");
        }
    });

    // Clear Button Helper
    clearBtn.addEventListener("click", () => {
        longUrlInput.value = "";
        toggleInputState();
    });

    longUrlInput.addEventListener("input", toggleInputState);

    function toggleInputState() {
        const val = longUrlInput.value.trim();
        clearBtn.classList.toggle("hidden", val.length === 0);

        if (val.length > 0 && !val.startsWith("http://") && !val.startsWith("https://")) {
            urlValidationHint.classList.remove("hidden");
            hintText.textContent = "Note: 'https://' protocol will be automatically prepended.";
        } else {
            urlValidationHint.classList.add("hidden");
        }
    }

    // Tab Switcher
    tabChips.forEach(chip => {
        chip.addEventListener("click", () => {
            tabChips.forEach(c => c.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));
            chip.classList.add("active");
            const target = document.getElementById(chip.dataset.tab);
            if (target) target.classList.add("active");
        });
    });

    // Expiry Presets Switcher
    presetBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            presetBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const mins = parseInt(btn.dataset.minutes, 10);
            selectedExpiryMinutes = mins > 0 ? mins : null;
            if (customExpiresInInput) {
                customExpiresInInput.value = selectedExpiryMinutes ? selectedExpiryMinutes : "";
            }
        });
    });

    if (customExpiresInInput) {
        customExpiresInInput.addEventListener("input", () => {
            const val = parseInt(customExpiresInInput.value, 10);
            selectedExpiryMinutes = val > 0 ? val : null;
            presetBtns.forEach(b => b.classList.remove("active"));
        });
    }

    // Submit Shorten Form
    shortenForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const url = longUrlInput.value.trim();
        const custom_alias = customAliasInput.value.trim() || null;
        const expires_in_minutes = selectedExpiryMinutes;

        if (!url) {
            showToast("Please enter a valid target URL", "error");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Creating...</span>`;

        try {
            const response = await fetch(`${BASE_URL}/api/shorten`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, custom_alias, expires_in_minutes })
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 409) {
                    showToast(`Alias taken: ${data.detail}`, "error");
                } else if (response.status === 429) {
                    showToast(`Rate limit: ${data.detail}`, "error");
                } else {
                    showToast(data.detail || "Failed to create short link", "error");
                }
                return;
            }

            // Success Display
            resultShortUrl.value = data.short_url;
            testRedirectLink.href = data.short_url;
            resultCreatedTime.innerHTML = `<i class="fa-regular fa-clock"></i> Created ${new Date(data.created_at).toLocaleTimeString()}`;
            resultCard.classList.remove("hidden");

            showToast("Short link generated successfully!", "success");

            // Attach inspect button trigger for new link
            inspectResultBtn.onclick = () => {
                analyticsInput.value = data.short_code;
                fetchAnalytics(data.short_code);
                analyticsCanvas.scrollIntoView({ behavior: "smooth", block: "center" });
            };

            // Attach QR modal trigger for new link
            openQrModalBtn.onclick = () => {
                openQRCodeModal(data.short_url);
            };

            // Refresh History Table
            fetchLinks(1);
        } catch (err) {
            showToast("Network error. Unable to reach server.", "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<span class="btn-text">Shorten URL</span> <i class="fa-solid fa-wand-magic-sparkles btn-icon"></i>`;
        }
    });

    // Copy Result Short Link
    copyResultBtn.addEventListener("click", () => {
        if (!resultShortUrl.value) return;
        navigator.clipboard.writeText(resultShortUrl.value);
        copyResultBtn.innerHTML = `<i class="fa-solid fa-check"></i> <span>Copied!</span>`;
        showToast("Short link copied to clipboard", "success");
        setTimeout(() => {
            copyResultBtn.innerHTML = `<i class="fa-solid fa-copy"></i> <span>Copy Link</span>`;
        }, 2000);
    });

    // Analytics Search
    analyticsSubmitBtn.addEventListener("click", () => {
        const code = analyticsInput.value.trim();
        if (code) fetchAnalytics(code);
    });

    analyticsInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            const code = analyticsInput.value.trim();
            if (code) fetchAnalytics(code);
        }
    });

    async function fetchAnalytics(code) {
        analyticsCanvas.classList.remove("empty-canvas");
        analyticsCanvas.innerHTML = `<div class="text-center py-4"><i class="fa-solid fa-spinner fa-spin fa-2x text-indigo"></i><p class="mt-2">Fetching link insights...</p></div>`;

        try {
            const response = await fetch(`${BASE_URL}/api/analytics/${code}`);
            const data = await response.json();

            if (!response.ok) {
                analyticsCanvas.classList.add("empty-canvas");
                analyticsCanvas.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon-ring text-rose"><i class="fa-solid fa-circle-xmark"></i></div>
                        <h4>Link Not Found</h4>
                        <p>${data.detail || "No analytics record exists for this short code."}</p>
                    </div>
                `;
                return;
            }

            const statusBadge = data.is_expired
                ? `<span class="badge-status badge-expired"><i class="fa-solid fa-circle-exclamation"></i> Expired</span>`
                : `<span class="badge-status badge-active"><i class="fa-solid fa-circle-check"></i> Active</span>`;

            analyticsCanvas.innerHTML = `
                <div class="analytics-metrics-grid">
                    <div class="metric-card-box">
                        <div class="metric-big-num">${data.clicks}</div>
                        <div class="metric-card-label">Total Redirect Clicks</div>
                    </div>
                    <div class="metric-card-box">
                        <div style="margin-top:0.35rem;">${statusBadge}</div>
                        <div class="metric-card-label" style="margin-top:0.75rem;">Link Status</div>
                    </div>
                </div>
                <div class="analytics-detail-list">
                    <div class="detail-item-row">
                        <span>Short Code:</span>
                        <strong class="code-pill">${data.short_code}</strong>
                    </div>
                    <div class="detail-item-row">
                        <span>Target Destination:</span>
                        <a href="${data.original_url}" target="_blank" class="truncate-link" title="${data.original_url}">${data.original_url}</a>
                    </div>
                    <div class="detail-item-row">
                        <span>Created Date:</span>
                        <span>${new Date(data.created_at).toLocaleString()}</span>
                    </div>
                    <div class="detail-item-row">
                        <span>Last Accessed:</span>
                        <span>${data.last_accessed_at ? new Date(data.last_accessed_at).toLocaleString() : 'Never'}</span>
                    </div>
                    <div class="detail-item-row">
                        <span>Expiration:</span>
                        <span>${data.expires_at ? new Date(data.expires_at).toLocaleString() : 'No expiration set'}</span>
                    </div>
                </div>
            `;
        } catch (err) {
            analyticsCanvas.classList.add("empty-canvas");
            analyticsCanvas.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon-ring text-rose"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <h4>Network Error</h4>
                    <p>Failed to load analytics metrics from server.</p>
                </div>
            `;
        }
    }

    // Fetch Paginated Links Directory
    async function fetchLinks(page = 1) {
        refreshTableBtn.disabled = true;
        try {
            const response = await fetch(`${BASE_URL}/api/links?page=${page}&limit=${pageLimit}`);
            const data = await response.json();

            if (!response.ok) return;

            currentPage = data.page;
            allLinksData = data.items;
            const totalPages = Math.ceil(data.total / pageLimit) || 1;

            pageIndicator.textContent = data.page;
            paginationInfo.textContent = `Showing page ${data.page} of ${totalPages} (${data.total} total links)`;

            prevPageBtn.disabled = data.page <= 1;
            nextPageBtn.disabled = data.page >= totalPages;

            renderTableRows(allLinksData);
        } catch (err) {
            linksTbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-rose">Failed to load links list.</td></tr>`;
        } finally {
            refreshTableBtn.disabled = false;
        }
    }

    // Render Table Rows with Filters
    function renderTableRows(items) {
        let filtered = items;

        if (activeFilter === "active") {
            filtered = items.filter(i => !i.is_expired);
        } else if (activeFilter === "expired") {
            filtered = items.filter(i => i.is_expired);
        }

        const query = tableSearchInput.value.trim().toLowerCase();
        if (query) {
            filtered = filtered.filter(i => 
                i.short_code.toLowerCase().includes(query) || 
                i.original_url.toLowerCase().includes(query)
            );
        }

        if (filtered.length === 0) {
            linksTbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No short links match your criteria.</td></tr>`;
            return;
        }

        linksTbody.innerHTML = filtered.map(item => {
            const statusBadge = item.is_expired
                ? `<span class="badge-status badge-expired">Expired</span>`
                : `<span class="badge-status badge-active">Active</span>`;

            return `
                <tr>
                    <td><span class="code-pill">${item.short_code}</span></td>
                    <td><a href="${item.original_url}" target="_blank" class="truncate-link" title="${item.original_url}">${item.original_url}</a></td>
                    <td class="text-center"><strong>${item.clicks}</strong></td>
                    <td>${statusBadge}</td>
                    <td class="text-right">
                        <div class="table-row-actions">
                            <button class="tbl-action-btn copy-link-btn" data-url="${item.short_url}" title="Copy Link"><i class="fa-solid fa-copy"></i></button>
                            <button class="tbl-action-btn inspect-link-btn" data-code="${item.short_code}" title="Inspect Analytics"><i class="fa-solid fa-chart-pie"></i></button>
                            <button class="tbl-action-btn qr-link-btn" data-url="${item.short_url}" title="Get QR Code"><i class="fa-solid fa-qrcode"></i></button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        // Attach action delegates
        document.querySelectorAll(".copy-link-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                navigator.clipboard.writeText(btn.dataset.url);
                showToast("Short link copied to clipboard", "success");
            });
        });

        document.querySelectorAll(".inspect-link-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                analyticsInput.value = btn.dataset.code;
                fetchAnalytics(btn.dataset.code);
                analyticsCanvas.scrollIntoView({ behavior: "smooth", block: "center" });
            });
        });

        document.querySelectorAll(".qr-link-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                openQRCodeModal(btn.dataset.url);
            });
        });
    }

    // Filter Chips Event Listeners
    filterChips.forEach(chip => {
        chip.addEventListener("click", () => {
            filterChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            activeFilter = chip.dataset.filter;
            renderTableRows(allLinksData);
        });
    });

    tableSearchInput.addEventListener("input", () => {
        renderTableRows(allLinksData);
    });

    refreshTableBtn.addEventListener("click", () => fetchLinks(currentPage));
    prevPageBtn.addEventListener("click", () => { if (currentPage > 1) fetchLinks(currentPage - 1); });
    nextPageBtn.addEventListener("click", () => { fetchLinks(currentPage + 1); });

    // QR Code Modal Setup
    function openQRCodeModal(url) {
        qrcodeWrapper.innerHTML = "";
        qrTargetUrl.textContent = url;
        qrModal.classList.remove("hidden");

        const qrcode = new QRCode(qrcodeWrapper, {
            text: url,
            width: 180,
            height: 180,
            colorDark: "#080c14",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });

        // Set download canvas link after small render delay
        setTimeout(() => {
            const img = qrcodeWrapper.querySelector("img") || qrcodeWrapper.querySelector("canvas");
            if (img) {
                downloadQrBtn.href = img.src || img.toDataURL("image/png");
            }
        }, 200);
    }

    closeQrModal.addEventListener("click", () => qrModal.classList.add("hidden"));
    qrModal.addEventListener("click", (e) => {
        if (e.target === qrModal) qrModal.classList.add("hidden");
    });

    copyQrLinkBtn.addEventListener("click", () => {
        if (qrTargetUrl.textContent) {
            navigator.clipboard.writeText(qrTargetUrl.textContent);
            showToast("Copied link to clipboard", "success");
        }
    });

    // Toast Notification System
    function showToast(message, type = "info") {
        const toastContainer = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;

        const iconMap = {
            success: "fa-circle-check text-emerald",
            error: "fa-circle-exclamation text-rose",
            info: "fa-circle-info text-indigo"
        };

        toast.innerHTML = `<i class="fa-solid ${iconMap[type] || 'fa-info-circle'}"></i> <span>${message}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(100%)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }
});
