/**
 * services/api.js
 * Semua HTTP call ke backend FastAPI dipusatin di sini.
 * Token otomatis disisipin ke header, refresh otomatis kalau expired.
 */

const BASE_URL = "http://localhost:8000"

// ── Token management ──────────────────────────────────────────
export function saveTokens(access, refresh) {
  localStorage.setItem("access_token", access)
  localStorage.setItem("refresh_token", refresh)
}

export function getAccessToken() {
  return localStorage.getItem("access_token")
}

export function getRefreshToken() {
  return localStorage.getItem("refresh_token")
}

export function clearTokens() {
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
  localStorage.removeItem("user")
}

export function saveUser(user) {
  localStorage.setItem("user", JSON.stringify(user))
}

export function getSavedUser() {
  const u = localStorage.getItem("user")
  return u ? JSON.parse(u) : null
}

// ── Base fetch wrapper dengan auto-attach token ───────────────
let isRefreshing = false
let refreshSubscribers = []

function onRefreshed(token) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

async function apiFetch(path, options = {}, retry = true) {
  const token = getAccessToken()
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  // Auto-refresh kalau 401
  if (res.status === 401 && retry) {
    if (!isRefreshing) {
      isRefreshing = true
      const refreshed = await tryRefresh()
      isRefreshing = false
      if (refreshed) {
        onRefreshed(getAccessToken())
      } else {
        refreshSubscribers = []
        clearTokens()
        window.location.reload() // paksa ke halaman login
        return
      }
    }
    
    // Antrikan request ini menunggu refresh selesai
    return new Promise(resolve => {
      refreshSubscribers.push(() => {
        resolve(apiFetch(path, options, false))
      })
    })
  }

  return res
}

async function tryRefresh() {
  const rt = getRefreshToken()
  if (!rt) return false
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    })
    if (!res.ok) return false
    const data = await res.json()
    saveTokens(data.access_token, data.refresh_token)
    return true
  } catch {
    return false
  }
}

// ── Auth API ──────────────────────────────────────────────────
export const authApi = {
  async login(username, password) {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Login gagal.")
    return data
  },

  async register(payload) {
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Register gagal.")
    return data
  },

  async me() {
    const res = await apiFetch("/auth/me")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail)
    return data
  },

  async getUsers() {
    const res = await apiFetch("/auth/users")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil daftar user.")
    return data
  },

  async createUser(payload) {
    const res = await apiFetch("/auth/users", {
      method: "POST",
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal tambah user.")
    return data
  },

  async updateUser(userId, payload) {
    const res = await apiFetch(`/auth/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal update user.")
    return data
  },

  async deleteUser(userId) {
    const res = await apiFetch(`/auth/users/${userId}`, {
      method: "DELETE"
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal hapus user.")
    return data
  }
}

// ── Inventory API ─────────────────────────────────────────────
export const inventoryApi = {
  async getAll() {
    const res = await apiFetch("/inventory/")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil inventory.")
    return data
  },

  async create(payload) {
    const res = await apiFetch("/inventory/", {
      method: "POST",
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal tambah produk.")
    return data
  },

  async delete(id) {
    const res = await apiFetch(`/inventory/${id}`, { method: "DELETE" })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal hapus produk.")
    return data
  },

  async update(id, payload) {
    const res = await apiFetch(`/inventory/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal update produk.")
    return data
  },
}

// ── Transaction API ─────────────────────────────────────────────
export const transactionApi = {
  async getAll() {
    const res = await apiFetch("/transaction/")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil transaksi.")
    return data
  },

  async getById(id) {
    const res = await apiFetch(`/transaction/${id}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil detail transaksi.")
    return data
  },

  async create(payload) {
    const res = await apiFetch("/transaction/", {
      method: "POST",
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal buat transaksi.")
    return data
  }
}

// ── Kontrak API ───────────────────────────────────────────
export const kontrakApi = {
  async getAll() {
    const res = await apiFetch("/kontrak/")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil kontrak.")
    return data
  },

  async getById(id) {
    const res = await apiFetch(`/kontrak/${id}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil detail kontrak.")
    return data
  },

  async create(payload) {
    const res = await apiFetch("/kontrak/", {
      method: "POST",
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal buat kontrak.")
    return data
  },

  async verify(id) {
    const res = await apiFetch(`/kontrak/${id}/verify`, { method: "POST" })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal verifikasi kontrak.")
    return data
  },

  async getPdfBlob(id) {
    const res = await apiFetch(`/kontrak/${id}/pdf`)
    if (!res.ok) {
      let msg = "Gagal mengunduh PDF."
      try { const errData = await res.json(); if(errData.detail) msg = errData.detail } catch(e){}
      throw new Error(msg)
    }
    return await res.blob()
  },

  async generatePdf(id) {
    const res = await apiFetch(`/kontrak/${id}/generate-pdf`, { method: "POST" })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal generate PDF kontrak.")
    return data
  },

  async generateForTransaction(transaksiId) {
    const res = await apiFetch(`/kontrak/generate-for-transaction/${transaksiId}`, { method: "POST" })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal generate kontrak untuk transaksi.")
    return data
  },
}

// ── I/O System API ────────────────────────────────────────────
export const ioSystemApi = {
  async getOverview() {
    const res = await apiFetch("/io/overview")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil overview I/O.")
    return data
  },

  async getLogs(limit = 50, action = null) {
    let path = `/io/logs?limit=${limit}`
    if (action) path += `&action=${action}`
    const res = await apiFetch(path)
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil log I/O.")
    return data
  },

  async getTransactionIO(id) {
    const res = await apiFetch(`/io/transaction/${id}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil detail I/O transaksi.")
    return data
  },

  async simulate(payload) {
    const res = await apiFetch("/io/simulate", {
      method: "POST",
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal simulasi I/O pipeline.")
    return data
  },

  async getThroughput() {
    const res = await apiFetch("/io/throughput")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil throughput data.")
    return data
  },

  async getManualLogs() {
    const res = await apiFetch("/io/logs/manual")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil manual log.")
    return data
  },

  async createManualLog(payload) {
    const res = await apiFetch("/io/logs/manual", {
      method: "POST",
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal tambah manual log.")
    return data
  },

  async deleteManualLog(id) {
    const res = await apiFetch(`/io/logs/manual/${id}`, { method: "DELETE" })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal hapus manual log.")
    return data
  },

  async clearManualLogs() {
    const res = await apiFetch("/io/logs/manual", { method: "DELETE" })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal hapus semua manual log.")
    return data
  }
}

// ── Deteksi Uang API ──────────────────────────────────────────
export const deteksiUangApi = {
  async analyze(file) {
    const token = getAccessToken()
    const formData = new FormData()
    formData.append("file", file)
    const res = await fetch(`${BASE_URL}/deteksi-uang/analisis`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal menganalisis gambar.")
    return data
  },

  async getStatus() {
    const res = await fetch(`${BASE_URL}/deteksi-uang/status`)
    const data = await res.json()
    return data
  },
}

// ── Payment Gateway (Midtrans) API ────────────────────────────
export const paymentApi = {
  async getConfig() {
    const res = await apiFetch("/payment/config")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil konfigurasi payment.")
    return data
  },

  async createSnapToken(transaksiId) {
    const res = await apiFetch("/payment/create-snap-token", {
      method: "POST",
      body: JSON.stringify({ transaksi_id: transaksiId }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal buat snap token.")
    return data
  },

  async getStatus(orderId) {
    const res = await apiFetch(`/payment/status/${orderId}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal cek status pembayaran.")
    return data
  },

  async getHistory() {
    const res = await apiFetch("/payment/history")
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil riwayat pembayaran.")
    return data
  },

  async simulateSuccess(orderId) {
    const res = await apiFetch("/payment/simulate-success", {
      method: "POST",
      body: JSON.stringify({ order_id: orderId }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal simulasi pembayaran.")
    return data
  },
}

// ── Laporan API ────────────────────────────────────────────────
export const laporanApi = {
  async getRingkasan(periode = 'bulan') {
    const res = await apiFetch(`/laporan/ringkasan?periode=${periode}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Gagal ambil ringkasan.")
    return data
  },

  getExportCsvUrl(periode = 'bulan') {
    const token = getAccessToken()
    return `${BASE_URL}/laporan/export/csv?periode=${periode}`
  },
}