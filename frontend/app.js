// ================================================
// KANPUR POTHOLE TRACKER — Core Utilities
// ================================================

const API_BASE = "https://kanpur-pothole-backend.onrender.com";

// ---- AUTH ----
const getToken = () => localStorage.getItem("token");
const getUser  = () => { const u = localStorage.getItem("user"); return u ? JSON.parse(u) : null; };

function saveAuth(data) {
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify({
    id: data.user_id, role: data.role, name: data.full_name
  }));
}

function logout() {
  localStorage.clear();
  window.location.href = "index.html";
}

function requireAuth(roles) {
  const token = getToken(), user = getUser();
  if (!token || !user) { window.location.href = "index.html"; return false; }
  if (roles && !roles.includes(user.role)) {
    window.location.href = "index.html"; return false;
  }
  return true;
}

// ---- API ----
async function apiCall(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  const token   = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const config  = { method, headers };
  if (body) config.body = JSON.stringify(body);
  try {
    const res  = await fetch(`${API_BASE}${endpoint}`, config);
    if (res.status === 401) { logout(); return null; }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed.");
    return data;
  } catch (err) { throw err; }
}

async function downloadCSV() {
  const res = await fetch(`${API_BASE}/analytics/export-csv`, {
    headers: { "Authorization": `Bearer ${getToken()}` }
  });
  if (!res.ok) { showAlert("Export failed.", "error"); return; }
  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url; a.download = `kanpur_complaints_${Date.now()}.csv`; a.click();
  URL.revokeObjectURL(url);
}

// ---- UI HELPERS ----
function showAlert(msg, type = "success", id = "alert-box") {
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const box   = document.getElementById(id);
  if (!box) return;
  box.innerHTML = `<div class="alert alert-${type}">${icons[type]} ${msg}</div>`;
  setTimeout(() => { if (box) box.innerHTML = ""; }, 5000);
}

function showLoading(show) {
  const el = document.getElementById("loading-overlay");
  if (el) el.classList.toggle("active", show);
}

function openModal(id)  { document.getElementById(id).classList.add("active");    }
function closeModal(id) { document.getElementById(id).classList.remove("active"); }

function statusBadge(s) {
  return `<span class="badge badge-${s.toLowerCase()}">${s}</span>`;
}
function severityBadge(s) {
  return `<span class="badge badge-${s.toLowerCase()}">${s}</span>`;
}
function formatDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric"
  });
}

function setNavUser() {
  const user = getUser();
  if (!user) return;
  const n = document.getElementById("nav-name");
  const r = document.getElementById("nav-role");
  if (n) n.textContent = user.name;
  if (r) {
    r.textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);
    r.className   = `role-badge role-${user.role}`;
  }
}

// ---- LIGHTBOX ----
function initLightbox() {
  const lb = document.createElement("div");
  lb.id        = "lightbox";
  lb.innerHTML = `
    <div id="lightbox-overlay" onclick="closeLightbox()"
         style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.92);
                z-index:9999; align-items:center; justify-content:center;
                flex-direction:column; gap:16px;">
      <button onclick="closeLightbox()"
              style="position:absolute; top:20px; right:24px; background:rgba(255,255,255,0.15);
                     border:none; color:white; font-size:28px; cursor:pointer;
                     width:44px; height:44px; border-radius:50%; display:flex;
                     align-items:center; justify-content:center;">✕</button>
      <img id="lightbox-img" src="" alt="Photo"
           style="max-width:90vw; max-height:80vh; border-radius:12px;
                  box-shadow:0 24px 64px rgba(0,0,0,0.5); object-fit:contain;"/>
      <p id="lightbox-caption"
         style="color:rgba(255,255,255,0.7); font-size:13px; margin:0;"></p>
    </div>`;
  document.body.appendChild(lb);
}

function openLightbox(url, caption = "") {
  if (!url) return;
  document.getElementById("lightbox-img").src         = url;
  document.getElementById("lightbox-caption").textContent = caption;
  const overlay = document.getElementById("lightbox-overlay");
  overlay.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeLightbox() {
  document.getElementById("lightbox-overlay").style.display = "none";
  document.body.style.overflow = "";
}

// ESC key to close lightbox
document.addEventListener("keydown", e => {
  if (e.key === "Escape") closeLightbox();
});

// ---- PHOTO PREVIEW ----
function setupPhotoPreview(inputId, previewId) {
  const input   = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  if (!input || !preview) return;

  input.addEventListener("input", () => {
    const url = input.value.trim();
    if (!url) { preview.style.display = "none"; return; }
    preview.style.display = "block";
    preview.querySelector("img").src = url;
    preview.querySelector("img").onerror = () => {
      preview.style.display = "none";
    };
  });
}

// ---- KANPUR AREAS ----
const KANPUR_AREAS = [
  "GT Road", "Vijay Nagar", "Rawatpur", "Kalyanpur", "Kidwai Nagar",
  "Govind Nagar", "Kakadeo", "Harsh Nagar", "Civil Lines", "Swaroop Nagar",
  "Armapur", "Jajmau", "Gwaltoli", "Naubasta", "Panki",
  "Fazalganj", "Barra", "Shyam Nagar", "Dabauli", "Chakeri",
  "Juhi", "Benajhabar", "Ratan Lal Nagar", "Tilak Nagar", "Ashok Nagar",
  "Cantt Area", "Colonelganj", "Birhana Road", "Parade", "Naramau"
];

function getAreaOptions(selected = "") {
  return KANPUR_AREAS.map(a =>
    `<option value="${a}" ${a === selected ? "selected" : ""}>${a}</option>`
  ).join("");
}

// Init lightbox on load
document.addEventListener("DOMContentLoaded", initLightbox);


// ---- FILE UPLOAD TO CLOUDINARY (via backend) ----
async function uploadImage(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);

  const token = getToken();

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Progress tracking
    xhr.upload.addEventListener("progress", e => {
      if (e.lengthComputable && onProgress) {
        const percent = Math.round((e.loaded / e.total) * 100);
        onProgress(percent);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 200) {
        const data = JSON.parse(xhr.responseText);
        resolve(data.url);
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || "Upload failed"));
        } catch {
          reject(new Error("Upload failed"));
        }
      }
    });

    xhr.addEventListener("error", () => reject(new Error("Network error during upload")));

    xhr.open("POST", `${API_BASE}/upload/image`);
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.send(formData);
  });
}

// ---- PHOTO UPLOAD BOX COMPONENT ----
// Creates a drag-drop + click upload box
// containerId: where to render, onUpload: callback with URL
function createUploadBox(containerId, onUpload, label = "Upload Photo") {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = `
    <div id="${containerId}-box"
         style="border:2px dashed #d1fae5; border-radius:12px; padding:24px;
                text-align:center; cursor:pointer; transition:all 0.2s;
                background:#f9fafb; position:relative;"
         onclick="document.getElementById('${containerId}-input').click()"
         ondragover="event.preventDefault();this.style.borderColor='#057a55';this.style.background='#ecfdf5';"
         ondragleave="this.style.borderColor='#d1fae5';this.style.background='#f9fafb';"
         ondrop="handleDrop(event,'${containerId}')">

      <input type="file" id="${containerId}-input" accept="image/*"
             style="display:none;" onchange="handleFileSelect(event,'${containerId}')"/>

      <div id="${containerId}-idle">
        <div style="font-size:36px;margin-bottom:8px;">📸</div>
        <div style="font-weight:600;color:#374151;margin-bottom:4px;">${label}</div>
        <div style="font-size:12px;color:#9ca3af;">
          Click to browse or drag & drop<br>JPG, PNG, GIF, WEBP · Max 5MB
        </div>
      </div>

      <div id="${containerId}-progress" style="display:none;">
        <div style="font-size:24px;margin-bottom:8px;">⏳</div>
        <div style="font-weight:600;color:#1a56db;">Uploading...</div>
        <div style="margin-top:10px;background:#e5e7eb;border-radius:99px;height:8px;overflow:hidden;">
          <div id="${containerId}-bar"
               style="height:100%;background:#1a56db;border-radius:99px;
                      width:0%;transition:width 0.3s;"></div>
        </div>
        <div id="${containerId}-pct" style="font-size:12px;color:#6b7280;margin-top:4px;">0%</div>
      </div>

      <div id="${containerId}-preview" style="display:none;">
        <img id="${containerId}-img" src="" alt="Preview"
             style="max-height:160px;border-radius:8px;object-fit:cover;
                    max-width:100%;margin-bottom:8px;"/>
        <div style="font-size:12px;color:#057a55;font-weight:600;">✅ Uploaded</div>
        <button onclick="event.stopPropagation();resetUploadBox('${containerId}')"
                style="margin-top:6px;background:none;border:1px solid #e5e7eb;
                       border-radius:6px;padding:4px 10px;font-size:11px;
                       cursor:pointer;color:#6b7280;">
          Change Photo
        </button>
      </div>
    </div>
  `;

  // Store callback
  window[`${containerId}_callback`] = onUpload;
}

function handleDrop(event, containerId) {
  event.preventDefault();
  const box = document.getElementById(`${containerId}-box`);
  box.style.borderColor = "#d1fae5";
  box.style.background  = "#f9fafb";
  const file = event.dataTransfer.files[0];
  if (file) processUpload(file, containerId);
}

function handleFileSelect(event, containerId) {
  const file = event.target.files[0];
  if (file) processUpload(file, containerId);
}

async function processUpload(file, containerId) {
  // Validate type
  const allowed = ["image/jpeg","image/png","image/gif","image/webp"];
  if (!allowed.includes(file.type)) {
    alert("Invalid file type. Please upload JPG, PNG, GIF, or WEBP.");
    return;
  }
  // Validate size
  if (file.size > 5 * 1024 * 1024) {
    alert("File too large. Maximum size is 5MB.");
    return;
  }

  // Show progress
  document.getElementById(`${containerId}-idle`).style.display     = "none";
  document.getElementById(`${containerId}-progress`).style.display = "block";
  document.getElementById(`${containerId}-preview`).style.display  = "none";

  try {
    const url = await uploadImage(file, (pct) => {
      document.getElementById(`${containerId}-bar`).style.width = pct + "%";
      document.getElementById(`${containerId}-pct`).textContent  = pct + "%";
    });

    // Show preview
    document.getElementById(`${containerId}-progress`).style.display = "none";
    document.getElementById(`${containerId}-preview`).style.display  = "block";
    document.getElementById(`${containerId}-img`).src = url;

    // Call callback with URL
    if (window[`${containerId}_callback`]) {
      window[`${containerId}_callback`](url);
    }

  } catch(e) {
    // Reset on error
    resetUploadBox(containerId);
    alert("Upload failed: " + e.message);
  }
}

function resetUploadBox(containerId) {
  document.getElementById(`${containerId}-idle`).style.display     = "block";
  document.getElementById(`${containerId}-progress`).style.display = "none";
  document.getElementById(`${containerId}-preview`).style.display  = "none";
  document.getElementById(`${containerId}-input`).value            = "";
  document.getElementById(`${containerId}-bar`).style.width        = "0%";
  if (window[`${containerId}_callback`]) {
    window[`${containerId}_callback`](null);
  }
}
