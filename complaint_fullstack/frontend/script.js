const API_BASE = "http://127.0.0.1:5000";
const API = API_BASE + "/api/complaints";

/* =========================
   LOGIN (USER / ADMIN)
   ========================= */
function protectPage(requiredRole) {
    const role = localStorage.getItem("role");
    if (!role || role !== requiredRole) {
        window.location.href = "index.html";
    }
}

function login(username, password, role) {
    fetch(API_BASE + "/api/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.token) {
            localStorage.setItem("token", data.token);
            localStorage.setItem("role", data.role);

            if (role === "admin") {
                window.location.href = "admin.html";
            } else {
                window.location.href = "user.html";
            }
        } else {
            alert("Login failed");
        }
    })
    .catch(err => console.error("Login error:", err));
}

/* =========================
   USER: Submit Complaint
   ========================= */
function submitComplaint() {
    fetch(API, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": localStorage.getItem("token")
        },
        body: JSON.stringify({
            name: document.getElementById("name").value,
            email: document.getElementById("email").value,
            phone: document.getElementById("phone").value,
            category: document.getElementById("category").value,
            title: document.getElementById("title").value,
            description: document.getElementById("description").value
        })
    })
    .then(response => response.json())
    .then(() => {
        alert("Complaint submitted successfully");

        // clear fields
        document.getElementById("name").value = "";
        document.getElementById("email").value = "";
        document.getElementById("phone").value = "";
        document.getElementById("category").value = "";
        document.getElementById("title").value = "";
        document.getElementById("description").value = "";

        loadComplaints();
    })
    .catch(error => {
        console.error("Error submitting complaint:", error);
    });
}

/* =========================
   LOAD COMPLAINTS
   (User + Admin)
   ========================= */
function loadComplaints() {
    fetch(API, {
        headers: {
            "Authorization": localStorage.getItem("token")
        }
    })
    .then(response => response.json())
    .then(data => {

        /* ---------- USER VIEW ---------- */
        if (document.getElementById("complaintList")) {
            let html = "";
            data.forEach(c => {
                html += `
                    <div class="complaint-item">
                        <b>${c.id}</b> – ${c.title}
                        <span class="status ${c.status.toLowerCase()}">
                            ${c.status}
                        </span>
                    </div>
                `;
            });
            document.getElementById("complaintList").innerHTML = html;
        }

        /* ---------- ADMIN VIEW ---------- */
        if (document.getElementById("adminList")) {
            let html = "";
            data.forEach(c => {
                html += `
                    <tr>
                        <td>${c.id}</td>
                        <td>${c.title}</td>
                        <td>${c.name}</td>
                        <td>${c.category}</td>
                        <td>
                            <span class="status ${c.status.toLowerCase()}">
                                ${c.status}
                            </span>
                        </td>
                        <td>
                            <button class="small-btn"
                                onclick="resolveComplaint('${c.id}')">
                                Resolve
                            </button>
                            <button class="small-btn danger"
                                onclick="deleteComplaint('${c.id}')">
                                Delete
                            </button>
                        </td>
                    </tr>
                `;
            });
            document.getElementById("adminList").innerHTML = html;
        }
    })
    .catch(error => {
        console.error("Error loading complaints:", error);
    });
}

/* =========================
   ADMIN: Resolve Complaint
   ========================= */
function resolveComplaint(id) {
    fetch(`${API}/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": localStorage.getItem("token")
        },
        body: JSON.stringify({ status: "Resolved" })
    })
    .then(() => loadComplaints())
    .catch(error => {
        console.error("Error resolving complaint:", error);
    });
}

/* =========================
   ADMIN: Delete Complaint
   ========================= */
function deleteComplaint(id) {
    fetch(`${API}/${id}`, {
        method: "DELETE",
        headers: {
            "Authorization": localStorage.getItem("token")
        }
    })
    .then(() => loadComplaints())
    .catch(error => {
        console.error("Error deleting complaint:", error);
    });
}

/* =========================
   LOGOUT (OPTIONAL)
   ========================= */
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    window.location.href = "index.html";
}

/* =========================
   AUTO LOAD
   ========================= */
window.onload = function () {
    if (localStorage.getItem("token")) {
        loadComplaints();
    }
};
function doLogin() {
    const params = new URLSearchParams(window.location.search);
    const role = params.get("role");

    fetch("http://127.0.0.1:5000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.token) {
            alert("Invalid credentials");
            return;
        }

        if (data.role !== role) {
            alert("Access denied for this role");
            return;
        }

        localStorage.setItem("token", data.token);
        localStorage.setItem("role", data.role);

        window.location.href = role === "admin" ? "admin.html" : "user.html";
    });
}
