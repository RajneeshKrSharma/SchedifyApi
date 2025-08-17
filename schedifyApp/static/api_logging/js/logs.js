let allLogs = [];

function showLoader() {
  document.getElementById("loader").classList.remove("hidden");
}

function hideLoader() {
  //document.getElementById("loader").classList.add("hidden");
}

async function fetchLogs() {
  try {
    showLoader();
    const res = await fetch("/logging/logs/data?n=200");
    const data = await res.json();
    allLogs = (data.lines || [])
      .map(line => { try { return JSON.parse(line) } catch { return null } })
      .filter(Boolean)
      .reverse();
    renderLogs();
  } catch (err) {
    console.error("Error clearing logs:", err);
  } finally {
    hideLoader();
  }
}

function renderLogs() {
  const container = document.getElementById("logs");
  container.innerHTML = "";

  const searchText = document.getElementById("search").value.toLowerCase();
  const methodFilter = document.getElementById("filter-method").value;
  const statusFilter = document.getElementById("filter-status").value;
  const timeFilter = document.getElementById("filter-time").value;
  const dateFilter = document.getElementById("clear-date")?.value;

  let filtered = allLogs.filter(log => {
    if (searchText && !JSON.stringify(log).toLowerCase().includes(searchText)) return false;
    if (methodFilter !== "all" && log.method !== methodFilter) return false;
    if (statusFilter === "2xx" && !(log.status >= 200 && log.status < 300)) return false;
    if (statusFilter === "4xx" && !(log.status >= 400 && log.status < 500)) return false;
    if (statusFilter === "5xx" && !(log.status >= 500)) return false;
    if (timeFilter === "<100" && !(log.time_ms < 100)) return false;
    if (timeFilter === "100-500" && !(log.time_ms >= 100 && log.time_ms <= 500)) return false;
    if (timeFilter === ">500" && !(log.time_ms > 500)) return false;
    if (dateFilter && !log.ts.startsWith(dateFilter)) return false;
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="text-center py-10 text-gray-500 text-sm">
        🚫 No logs found for current filters.
      </div>`;
    return;
  }

  filtered.forEach(log => {
    const statusColor =
      log.status >= 200 && log.status < 300 ? "bg-green-100 text-green-700" :
      log.status >= 400 && log.status < 500 ? "bg-yellow-100 text-yellow-700" :
      "bg-red-100 text-red-700";

    const methodColor = {
      GET: "bg-blue-100 text-blue-700",
      POST: "bg-purple-100 text-purple-700",
      PUT: "bg-orange-100 text-orange-700",
      DELETE: "bg-red-100 text-red-700",
    }[log.method] || "bg-gray-100 text-gray-700";

    const card = `
      <div class="bg-white shadow-sm rounded-2xl border p-5 hover:shadow-md transition">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="px-2 py-1 text-xs font-semibold rounded ${methodColor}">
              ${log.method}
            </span>
            <span class="font-medium text-gray-800">${log.path}</span>
          </div>
          <span class="px-2 py-1 text-xs font-semibold rounded ${statusColor}">
            ${log.status}
          </span>
        </div>
        <div class="mt-1 text-xs text-gray-500">
          <span>ID: ${log.id}</span> •
          <span>${log.time_ms} ms</span> •
          <span>${log.ts}</span>
        </div>
        <div class="mt-3 space-y-2">
          ${makeDetails("📩 Request Body", log.body)}
          ${makeDetails("📤 Response", log.response)}
          ${makeDetails("🛠 Headers", log.headers)}
        </div>
      </div>`;
    container.innerHTML += card;
  });
}

function makeDetails(title, obj) {
  return `
    <details class="border rounded-lg">
      <summary class="cursor-pointer px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
        ${title}
      </summary>
      <pre class="bg-gray-50 text-xs p-3 overflow-x-auto">${JSON.stringify(obj, null, 2)}</pre>
    </details>`;
}

async function clearLogs() {
  const date = document.getElementById("clear-date").value;
  if (!date) {
    alert("Please select a date to clear logs.");
    return;
  }
  if (!confirm(`Are you sure you want to clear logs for ${date}?`)) {
    return;
  }

  try {
    showLoader();
    const res = await fetch(`/logging/logs/data/clear?date=${date}`);
    const result = await res.json();
    alert(result.message || result.error || "Action completed.");
    await fetchLogs();
  } catch (err) {
    console.error("Error clearing logs:", err);
  } finally {
    hideLoader();
  }
}

function toggleClearButton() {
  const dateInput = document.getElementById("clear-date");
  const clearBtn = document.getElementById("clear-btn");
  if (dateInput.value) {
    clearBtn.disabled = false;
    renderLogs();
  } else {
    clearBtn.disabled = true;
    renderLogs();
  }
}

function clearFilters() {
  document.getElementById("search").value = "";
  document.getElementById("filter-method").value = "all";
  document.getElementById("filter-status").value = "all";
  document.getElementById("filter-time").value = "all";
  const dateInput = document.getElementById("clear-date");
  if (dateInput) dateInput.value = "";
  renderLogs();
}

window.onload = fetchLogs;