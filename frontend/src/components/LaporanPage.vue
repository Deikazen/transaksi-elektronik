<template>
  <div class="laporan-page fade-in">
    <!-- Hero Section -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="hero-icon"><BarChart3 :size="28" /></div>
        <div>
          <h2>Laporan & Analitik</h2>
          <p class="muted">Ringkasan penjualan dan performa transaksi</p>
        </div>
      </div>
      <div class="hero-actions">
        <div class="periode-tabs">
          <button v-for="p in periodeOptions" :key="p.value" class="tab-btn" :class="{ active: periode === p.value }" @click="periode = p.value; fetchData()">
            {{ p.label }}
          </button>
        </div>
        <button class="btn-export" @click="exportCsv">
          <Download :size="16" /> Export CSV
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state"><Loader :size="24" class="spin" /> Memuat laporan...</div>

    <template v-else-if="data">
      <!-- Summary Cards -->
      <div class="stats-grid">
        <div class="stat-card" style="--c: var(--c-indigo)">
          <div class="stat-icon"><ShoppingCart :size="22" /></div>
          <div class="stat-value">{{ data.total_transaksi }}</div>
          <div class="stat-label">Total Transaksi</div>
        </div>
        <div class="stat-card" style="--c: var(--c-emerald)">
          <div class="stat-icon"><TrendingUp :size="22" /></div>
          <div class="stat-value">{{ formatRp(data.total_pendapatan) }}</div>
          <div class="stat-label">Total Pendapatan</div>
        </div>
        <div class="stat-card" style="--c: var(--c-amber)">
          <div class="stat-icon"><Tag :size="22" /></div>
          <div class="stat-value">{{ formatRp(data.total_diskon) }}</div>
          <div class="stat-label">Total Diskon</div>
        </div>
        <div class="stat-card" style="--c: var(--c-purple)">
          <div class="stat-icon"><Receipt :size="22" /></div>
          <div class="stat-value">{{ formatRp(data.rata_rata_per_tx) }}</div>
          <div class="stat-label">Rata-rata / Transaksi</div>
        </div>
      </div>

      <div class="report-grid">
        <!-- Chart -->
        <div class="card chart-card">
          <div class="card-header"><h3>Grafik Penjualan</h3></div>
          <div class="chart-container">
            <div class="chart-bars">
              <div v-for="(bar, i) in chartBars" :key="i" class="chart-col">
                <div class="bar-wrapper">
                  <div class="bar" :style="{ height: bar.height + '%' }" :title="formatRp(bar.value)">
                    <div class="bar-glow"></div>
                    <span class="bar-tooltip">{{ bar.shortValue }}</span>
                  </div>
                </div>
                <span class="bar-label">{{ bar.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Produk Terlaris -->
        <div class="card ranking-card">
          <div class="card-header"><h3>Produk Terlaris</h3></div>
          <div v-if="data.produk_terlaris.length === 0" class="empty-state muted">
            Belum ada data penjualan.
          </div>
          <div v-else class="ranking-list">
            <div v-for="(p, idx) in data.produk_terlaris" :key="idx" class="ranking-item">
              <div class="rank-num">#{{ idx + 1 }}</div>
              <div class="rank-info">
                <strong>{{ p.nama }}</strong>
                <span class="muted">{{ p.qty }} unit terjual</span>
              </div>
              <div class="rank-revenue mono">{{ formatRp(p.revenue) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Metode Pembayaran Breakdown -->
      <div class="card metode-container">
        <div class="card-header"><h3>Metode Pembayaran</h3></div>
        <div class="metode-grid">
          <div v-for="(count, metode) in data.metode_pembayaran" :key="metode" class="metode-card">
            <div class="metode-top">
              <div class="metode-label">{{ metode.toUpperCase() }}</div>
              <div class="metode-count">{{ count }} tx</div>
            </div>
            <div class="metode-bar">
              <div class="metode-fill" :style="{ width: (count / data.total_transaksi * 100) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- TOAST -->
    <div class="laporan-toast" :class="{ show: toastVisible, error: toastType === 'error' }">
      <component :is="toastType === 'error' ? AlertTriangle : CheckCircle" :size="16"/>
      {{ toastMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { laporanApi } from '../services/api.js'
import { ShoppingCart, TrendingUp, Tag, Receipt, Download, Loader, CheckCircle, AlertTriangle, BarChart3 } from 'lucide-vue-next'

const periode = ref('bulan')
const loading = ref(false)
const data = ref(null)

const periodeOptions = [
  { value: 'hari', label: 'Hari Ini' },
  { value: 'minggu', label: 'Minggu Ini' },
  { value: 'bulan', label: 'Bulan Ini' },
  { value: 'semua', label: 'Semua' },
]

const toastVisible = ref(false)
const toastMsg = ref('')
const toastType = ref('success')

function showToast(msg, type = 'success') {
  toastMsg.value = msg; toastType.value = type; toastVisible.value = true
  setTimeout(() => toastVisible.value = false, 3500)
}

function formatRp(v) {
  return 'Rp ' + Number(v || 0).toLocaleString('id-ID')
}

const chartBars = computed(() => {
  if (!data.value || !data.value.chart) return []
  const max = Math.max(...data.value.chart.map(c => c.pendapatan), 1)
  return data.value.chart.map(c => ({
    label: c.label,
    value: c.pendapatan,
    height: Math.max(2, (c.pendapatan / max) * 100),
    shortValue: c.pendapatan >= 1000000 ? (c.pendapatan / 1000000).toFixed(1) + 'jt' : c.pendapatan >= 1000 ? (c.pendapatan / 1000).toFixed(0) + 'k' : c.pendapatan.toString()
  }))
})

async function fetchData() {
  loading.value = true
  try {
    const res = await laporanApi.getRingkasan(periode.value)
    data.value = res.data
  } catch (e) { showToast(e.message, 'error') }
  finally { loading.value = false }
}

function exportCsv() {
  const url = laporanApi.getExportCsvUrl(periode.value)
  window.open(url, '_blank')
  showToast('Mengunduh laporan CSV...')
}

onMounted(fetchData)
</script>

<style scoped>
.laporan-page { display: flex; flex-direction: column; gap: 20px; flex: 1; min-height: 0; overflow-y: auto; padding: 4px; }

/* Hero Section */
.hero-section {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px;
  background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.08));
  border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 20px 24px;
}
.hero-content { display: flex; align-items: center; gap: 16px; }
.hero-icon { background: rgba(99,102,241,0.15); color: var(--c-indigo); padding: 12px; border-radius: 14px; display: flex; }
.hero-section h2 { font-family: 'Outfit', sans-serif; font-size: 20px; font-weight: 700; }
.hero-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

.periode-tabs { display: flex; gap: 4px; background: rgba(18,18,20,0.6); padding: 4px; border-radius: 12px; border: 1px solid var(--border); backdrop-filter: blur(8px); }
.tab-btn {
  padding: 8px 16px; border: none; background: transparent; color: var(--muted);
  font-size: 13px; font-weight: 600; border-radius: 8px; cursor: pointer; transition: 0.2s;
}
.tab-btn.active { background: rgba(255,255,255,0.1); color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
.tab-btn:hover:not(.active) { color: var(--text); }

.btn-export {
  background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.2); color: var(--c-emerald);
  padding: 10px 18px; border-radius: 12px; font-size: 13px; font-weight: 600;
  display: flex; align-items: center; gap: 8px; cursor: pointer; transition: 0.2s;
}
.btn-export:hover { background: rgba(16,185,129,0.25); transform: translateY(-1px); }

/* Stats Grid */
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.stat-card {
  background: rgba(18,18,20,0.6); border: 1px solid var(--border); border-radius: 16px;
  padding: 20px; backdrop-filter: blur(12px); position: relative; overflow: hidden; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.stat-card:hover { transform: translateY(-4px); border-color: color-mix(in srgb, var(--c) 40%, var(--border)); box-shadow: 0 12px 32px rgba(0,0,0,0.4); }
.stat-card::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: var(--c); border-radius: 16px 16px 0 0; box-shadow: 0 0 12px var(--c);
}
.stat-icon { color: var(--c); margin-bottom: 12px; background: color-mix(in srgb, var(--c) 15%, transparent); padding: 10px; border-radius: 10px; display: inline-flex; }
.stat-value { font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2; word-break: break-word; }
.stat-label { font-size: 13px; color: var(--muted); margin-top: 4px; font-weight: 500; }

/* Report Grid */
.report-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }

.card { background: rgba(18,18,20,0.6); border: 1px solid var(--border); border-radius: 16px; padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); backdrop-filter: blur(12px); }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.card-header h3 { font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }

/* Chart */
.chart-container { padding: 0 4px; }
.chart-bars { display: flex; gap: 8px; align-items: flex-end; height: 220px; }
.chart-col { flex: 1; display: flex; flex-direction: column; align-items: center; min-width: 0; }
.bar-wrapper { width: 100%; height: 190px; display: flex; align-items: flex-end; justify-content: center; padding-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.bar {
  width: 100%; max-width: 48px; background: linear-gradient(180deg, var(--c-indigo), rgba(99,102,241,0.1));
  border-radius: 8px; transition: height 0.6s cubic-bezier(0.34, 1.56, 0.64, 1); position: relative;
  min-height: 4px; cursor: pointer;
}
.bar:hover { background: linear-gradient(180deg, var(--c-purple), rgba(139,92,246,0.2)); }
.bar-glow { position: absolute; inset: 0; background: var(--c-indigo); filter: blur(8px); opacity: 0; transition: 0.3s; border-radius: 8px; z-index: -1; }
.bar:hover .bar-glow { opacity: 0.6; }
.bar-tooltip {
  position: absolute; top: -8px; left: 50%; transform: translate(-50%, -100%);
  font-size: 11px; color: var(--text); font-weight: 600; white-space: nowrap; background: var(--surface); padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border); box-shadow: 0 4px 12px rgba(0,0,0,0.3); opacity: 0; transition: 0.2s; pointer-events: none;
}
.bar:hover .bar-tooltip { opacity: 1; top: -12px; }
.bar-label { font-size: 11px; color: var(--muted); margin-top: 8px; text-align: center; font-weight: 500; }

/* Ranking */
.ranking-list { display: flex; flex-direction: column; gap: 10px; }
.ranking-item {
  display: flex; align-items: center; gap: 14px; padding: 12px 16px;
  background: var(--surface2); border: 1px solid transparent; border-radius: 12px; transition: 0.2s; cursor: default;
}
.ranking-item:hover { background: rgba(255,255,255,0.03); border-color: var(--border-hover); transform: translateX(4px); }
.rank-num {
  width: 32px; height: 32px; background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2)); color: #a5b4fc;
  border-radius: 10px; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0; box-shadow: inset 0 0 0 1px rgba(99,102,241,0.3);
}
.rank-info { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.rank-info strong { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-info .muted { font-size: 12px; }
.rank-revenue { font-size: 14px; font-weight: 600; color: var(--c-emerald); flex-shrink: 0; }
.empty-state { padding: 40px; text-align: center; display: flex; flex-direction: column; gap: 12px; align-items: center; border: 1px dashed var(--border); border-radius: 12px; }

/* Metode */
.metode-container { margin-bottom: 20px; }
.metode-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
.metode-card { background: var(--surface2); border-radius: 12px; padding: 16px; border: 1px solid var(--border); transition: 0.2s; }
.metode-card:hover { border-color: var(--border-hover); background: var(--surface3); }
.metode-top { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 12px; }
.metode-label { font-size: 13px; font-weight: 700; letter-spacing: 0.05em; color: var(--muted); }
.metode-count { font-size: 20px; font-weight: 700; font-family: 'Outfit', sans-serif; }
.metode-bar { height: 6px; background: rgba(0,0,0,0.4); border-radius: 3px; overflow: hidden; box-shadow: inset 0 1px 2px rgba(0,0,0,0.5); }
.metode-fill { height: 100%; background: linear-gradient(90deg, var(--c-indigo), var(--c-purple)); border-radius: 3px; transition: width 1s cubic-bezier(0.34, 1.56, 0.64, 1); box-shadow: 0 0 8px rgba(139,92,246,0.6); }

/* Utils */
.loading-state { display: flex; align-items: center; gap: 12px; padding: 60px; color: var(--muted); justify-content: center; font-size: 15px; }
.muted { color: var(--muted); }
.mono { font-family: 'JetBrains Mono', monospace; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.fade-in { animation: fi 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
@keyframes fi { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.laporan-toast {
  position: fixed; bottom: 32px; right: 32px; background: var(--surface); border: 1px solid var(--c-emerald);
  padding: 14px 22px; border-radius: 12px; font-size: 14px; font-weight: 500; color: var(--c-emerald);
  display: flex; align-items: center; gap: 10px; z-index: 2000; box-shadow: 0 12px 32px rgba(0,0,0,0.5);
  transform: translateY(100px); opacity: 0; transition: all 0.4s cubic-bezier(0.68,-0.55,0.27,1.55);
}
.laporan-toast.show { transform: translateY(0); opacity: 1; }
.laporan-toast.error { border-color: var(--c-rose); color: var(--c-rose); }

@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .report-grid { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .stats-grid { grid-template-columns: 1fr; }
  .hero-section { flex-direction: column; align-items: flex-start; }
}
</style>
