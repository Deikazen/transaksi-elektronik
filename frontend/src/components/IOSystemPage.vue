<template>
  <div class="io-page fade-in">
    <div class="io-hero">
      <div class="io-hero-content">
        <div class="io-hero-icon"><Activity :size="28" /></div>
        <div>
          <h2>I/O System Transaction</h2>
          <p class="muted">Monitor alur Input/Output data transaksi secara real-time</p>
        </div>
      </div>
      <button class="btn-refresh" @click="fetchAll" :disabled="loading">
        <component :is="loading ? Loader : RefreshCw" :size="16" :class="{spin:loading}" /> Refresh
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="io-stats" v-if="overview">
      <div class="io-stat" v-for="s in statsCards" :key="s.label" :style="{'--c':s.color}">
        <div class="io-stat-icon"><component :is="s.icon" :size="20" /></div>
        <div class="io-stat-body">
          <span class="io-stat-val">{{ s.value }}</span>
          <span class="io-stat-label">{{ s.label }}</span>
        </div>
      </div>
    </div>

    <div class="io-grid">
      <!-- Log Table -->
      <div class="io-card io-logs-card">
        <div class="io-card-header">
          <h3><FileText :size="18" /> Log I/O Terbaru</h3>
          <div class="io-filter">
            <button v-for="f in filters" :key="f.val" :class="{active:logFilter===f.val}" @click="logFilter=f.val">{{ f.label }}</button>
          </div>
        </div>
        <div v-if="loading" class="io-loading"><Loader :size="24" class="spin" /> Memuat log...</div>
        <div v-else-if="filteredLogs.length===0" class="io-empty muted">Tidak ada log ditemukan.</div>
        <div v-else class="io-log-list">
          <div v-for="log in filteredLogs.slice(0,30)" :key="log.id" class="io-log-item">
            <div class="io-log-top">
              <div class="io-log-badge" :class="log.action.toLowerCase()">{{ log.action }}</div>
              <div class="io-log-flow">
                <span class="io-log-src">{{ log.source }}</span>
                <ArrowRight :size="12" class="muted" />
                <span class="io-log-tgt">{{ log.target }}</span>
              </div>
              <span class="io-log-status" :class="log.status">{{ log.status }}</span>
            </div>
            <div class="io-log-desc">{{ log.description }}</div>
            <div class="io-log-meta">
              <span v-if="log.transaction_kode" class="mono"><Database :size="10"/> {{ log.transaction_kode }}</span>
              <span v-if="log.data_size" class="muted"><Wifi :size="10"/> {{ log.data_size }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right side: Pipeline Detail -->
      <div class="io-right">
        <!-- Transaction Detail Lookup -->
        <div class="io-card detail-card">
          <div class="io-card-header"><h3><Search :size="18" /> Pipeline Transaksi</h3></div>
          <div class="io-lookup">
            <input v-model.number="lookupId" type="number" placeholder="Masukkan ID Transaksi (1, 2...)" @keyup.enter="lookupTransaction" />
            <button class="btn-lookup" @click="lookupTransaction" :disabled="!lookupId || lookupLoading">
              <component :is="lookupLoading ? Loader : Search" :size="14" :class="{spin:lookupLoading}" /> Cari
            </button>
          </div>
          
          <div v-if="txDetail" class="io-tx-detail fade-in">
            <div class="io-pipeline-header">
              <div class="tx-info">
                <strong>{{ txDetail.kode }}</strong>
                <span class="muted">{{ txDetail.nama_klien }}</span>
              </div>
              <span class="badge lg" :class="txDetail.io_status">{{ txDetail.io_status }}</span>
            </div>
            
            <div class="io-pipeline">
              <div v-for="(step, index) in txDetail.processing_steps" :key="step.step" class="io-step" :class="step.status">
                <div class="io-step-node">
                  <div class="node-dot" :class="step.status">
                    <component :is="step.status==='success'?CheckCircle:step.status==='error'?XCircle:Clock" :size="14" />
                  </div>
                  <div class="node-line" v-if="index < txDetail.processing_steps.length - 1"></div>
                </div>
                <div class="io-step-content">
                  <div class="step-title">
                    <strong>{{ step.name }}</strong>
                    <span v-if="step.duration_ms" class="io-step-time">{{ step.duration_ms }}ms</span>
                  </div>
                  <span class="step-desc muted">{{ step.description }}</span>
                </div>
              </div>
            </div>
            
            <div class="io-io-summary">
              <div class="io-sum-col">
                <h4 class="sum-title"><span class="sum-icon in">📥</span> Input Payload</h4>
                <div class="sum-box">
                  <div v-for="inp in txDetail.input_payload" :key="inp.field" class="io-sum-row">
                    <code>{{ inp.field }}</code>
                    <span>{{ inp.value }}</span>
                    <span class="badge sm" :class="inp.validation">{{ inp.validation }}</span>
                  </div>
                </div>
              </div>
              <div class="io-sum-col">
                <h4 class="sum-title"><span class="sum-icon out">📤</span> Output Result</h4>
                <div class="sum-box">
                  <div v-for="out in txDetail.output_results" :key="out.field" class="io-sum-row">
                    <code>{{ out.field }}</code>
                    <span>{{ out.value }}</span>
                    <span class="badge sm" :class="out.type">{{ out.type }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="!lookupLoading" class="empty-detail muted">
            Cari ID Transaksi untuk melihat alur detail I/O-nya.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ioSystemApi } from '../services/api.js'
import {
  Activity, RefreshCw, Loader, FileText, ArrowRight, Search, CheckCircle, XCircle,
  Clock, Database, Zap, BarChart3, Wifi
} from 'lucide-vue-next'

const loading = ref(false), overview = ref(null), logs = ref([]), logFilter = ref('all')
const lookupId = ref(null), lookupLoading = ref(false), txDetail = ref(null)

const filters = [
  { val:'all', label:'Semua' }, { val:'INPUT', label:'Input' },
  { val:'PROCESS', label:'Process' }, { val:'OUTPUT', label:'Output' }, { val:'ERROR', label:'Error' }
]

const filteredLogs = computed(() => {
  if (logFilter.value === 'all') return logs.value
  return logs.value.filter(l => l.action === logFilter.value)
})

const statsCards = computed(() => {
  if (!overview.value) return []
  const d = overview.value
  return [
    { label:'Total Transaksi', value:d.total_transactions, icon:Database, color:'var(--c-indigo)' },
    { label:'Total I/O Ops', value:d.total_io_operations, icon:Zap, color:'var(--c-emerald)' },
    { label:'Avg Response', value:d.avg_response_time_ms+'ms', icon:BarChart3, color:'var(--c-amber)' },
    { label:'Success Rate', value:d.success_rate+'%', icon:CheckCircle, color:'var(--c-purple)' },
  ]
})

async function fetchAll() {
  loading.value = true
  try {
    const [ovRes, logRes] = await Promise.all([
      ioSystemApi.getOverview(),
      ioSystemApi.getLogs(50)
    ])
    overview.value = ovRes.data
    logs.value = logRes.data || []
  } catch (e) {
    console.error('IO fetch error:', e)
  } finally { loading.value = false }
}

async function lookupTransaction() {
  if (!lookupId.value) return
  lookupLoading.value = true; txDetail.value = null
  try {
    const res = await ioSystemApi.getTransactionIO(lookupId.value)
    txDetail.value = res.data
  } catch (e) { alert(e.message) } finally { lookupLoading.value = false }
}

onMounted(fetchAll)
</script>

<style scoped>
.io-page { flex: 1; display: flex; flex-direction: column; gap: 20px; min-height: 0; overflow-y: auto; padding: 4px; }

/* Hero */
.io-hero {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px;
  background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(99,102,241,0.08));
  border: 1px solid rgba(16,185,129,0.2); border-radius: 16px; padding: 20px 24px;
}
.io-hero-content { display: flex; align-items: center; gap: 16px; }
.io-hero-icon { background: rgba(16,185,129,0.15); color: var(--c-emerald); padding: 12px; border-radius: 14px; display: flex; }
.io-hero h2 { font-family: 'Outfit', sans-serif; font-size: 20px; font-weight: 700; }
.btn-refresh {
  background: rgba(18,18,20,0.6); border: 1px solid var(--border); color: var(--text); backdrop-filter: blur(8px);
  padding: 10px 18px; border-radius: 12px; font-size: 13px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; gap: 8px; transition: 0.2s;
}
.btn-refresh:hover { background: var(--surface3); border-color: var(--border-hover); transform: translateY(-1px); }
.btn-refresh:disabled { opacity: 0.5; transform: none; cursor: not-allowed; }

/* Stats */
.io-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.io-stat {
  background: rgba(18,18,20,0.6); border: 1px solid var(--border); border-radius: 16px;
  padding: 20px; display: flex; align-items: center; gap: 16px; position: relative; overflow: hidden;
  backdrop-filter: blur(12px); transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.io-stat:hover { transform: translateY(-4px); border-color: color-mix(in srgb, var(--c) 40%, var(--border)); box-shadow: 0 12px 32px rgba(0,0,0,0.4); }
.io-stat::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--c); box-shadow: 0 0 12px var(--c); }
.io-stat-icon { color: var(--c); background: color-mix(in srgb, var(--c) 15%, transparent); padding: 12px; border-radius: 12px; display: flex; }
.io-stat-body { display: flex; flex-direction: column; gap: 2px; }
.io-stat-val { font-family: 'Outfit', sans-serif; font-size: 22px; font-weight: 700; }
.io-stat-label { font-size: 13px; color: var(--muted); font-weight: 500; }

/* Grid */
.io-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; flex: 1; min-height: 0; }
@media(max-width: 1024px) { .io-grid { grid-template-columns: 1fr; } }

.io-card { background: rgba(18,18,20,0.6); border: 1px solid var(--border); border-radius: 16px; padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); backdrop-filter: blur(12px); display: flex; flex-direction: column; }
.io-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.io-card-header h3 { font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }

/* Filter Tabs */
.io-filter { display: flex; gap: 4px; background: rgba(0,0,0,0.2); padding: 4px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); }
.io-filter button { background: transparent; border: none; color: var(--muted); padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; transition: 0.2s; text-transform: uppercase; letter-spacing: 0.05em; }
.io-filter button:hover { color: var(--text); }
.io-filter button.active { background: rgba(255,255,255,0.1); color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }

/* Logs Table */
.io-loading { display: flex; align-items: center; gap: 12px; padding: 60px; color: var(--muted); justify-content: center; }
.io-empty { padding: 60px; text-align: center; border: 1px dashed var(--border); border-radius: 12px; }
.io-log-list { overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 4px; }
.io-log-item { display: flex; flex-direction: column; gap: 8px; padding: 14px 16px; background: var(--surface2); border: 1px solid transparent; border-radius: 12px; transition: 0.2s; }
.io-log-item:hover { background: rgba(255,255,255,0.03); border-color: var(--border-hover); transform: translateX(2px); }

.io-log-top { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.io-log-badge { padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; flex-shrink: 0; }
.io-log-badge.input { background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(99,102,241,0.1)); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); }
.io-log-badge.process { background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.1)); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }
.io-log-badge.output { background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.1)); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }
.io-log-badge.error { background: linear-gradient(135deg, rgba(244,63,94,0.2), rgba(244,63,94,0.1)); color: #fda4af; border: 1px solid rgba(244,63,94,0.3); }

.io-log-flow { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted); flex: 1; }
.io-log-src, .io-log-tgt { background: rgba(0,0,0,0.2); padding: 2px 8px; border-radius: 4px; }
.io-log-status { padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 600; margin-left: auto; }
.io-log-status.success { background: rgba(16,185,129,0.1); color: var(--c-emerald); }
.io-log-status.error { background: rgba(244,63,94,0.1); color: var(--c-rose); }

.io-log-desc { font-size: 13px; line-height: 1.5; color: var(--text); }
.io-log-meta { display: flex; align-items: center; gap: 12px; font-size: 11px; margin-top: 4px; }
.io-log-meta .mono, .io-log-meta .muted { display: flex; align-items: center; gap: 4px; background: var(--surface); padding: 4px 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }

/* Right Column */
.io-right { display: flex; flex-direction: column; gap: 20px; }
.detail-card { flex: 1; }
.empty-detail { padding: 60px; text-align: center; border: 1px dashed var(--border); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 14px; margin-top: 20px; }

.io-lookup { display: flex; gap: 8px; margin-bottom: 24px; }
.io-lookup input { flex: 1; background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 12px 16px; border-radius: 12px; font-size: 14px; outline: none; transition: 0.2s; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1); }
.io-lookup input:focus { border-color: var(--c-indigo); box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }
.btn-lookup { background: linear-gradient(135deg, var(--c-indigo), var(--c-purple)); color: white; border: none; padding: 12px 20px; border-radius: 12px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: 0.2s; box-shadow: 0 4px 12px rgba(99,102,241,0.2); }
.btn-lookup:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(99,102,241,0.3); }

/* Pipeline Detail */
.io-tx-detail { display: flex; flex-direction: column; gap: 24px; }
.io-pipeline-header { display: flex; align-items: center; justify-content: space-between; padding: 16px; background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.15); border-radius: 12px; }
.tx-info { display: flex; flex-direction: column; gap: 4px; }
.tx-info strong { font-size: 16px; font-family: 'Outfit', sans-serif; letter-spacing: 1px; }
.tx-info .muted { font-size: 13px; }

/* Timeline Format */
.io-pipeline { display: flex; flex-direction: column; padding: 10px 0; }
.io-step { display: flex; gap: 16px; position: relative; }
.io-step-node { display: flex; flex-direction: column; align-items: center; width: 24px; }
.node-dot { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: var(--surface2); z-index: 2; border: 2px solid var(--surface); }
.node-dot.success { color: var(--c-emerald); background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); }
.node-dot.error { color: var(--c-rose); background: rgba(244,63,94,0.1); border-color: rgba(244,63,94,0.3); }
.node-dot.pending { color: var(--c-amber); background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.3); }
.node-line { width: 2px; flex: 1; background: rgba(255,255,255,0.1); margin: 4px 0; min-height: 30px; }

.io-step-content { flex: 1; padding-bottom: 24px; display: flex; flex-direction: column; gap: 4px; padding-top: 2px; }
.step-title { display: flex; align-items: center; gap: 10px; }
.step-title strong { font-size: 14px; }
.io-step-time { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--c-indigo); background: rgba(99,102,241,0.1); padding: 2px 6px; border-radius: 4px; }
.step-desc { font-size: 13px; line-height: 1.5; color: var(--muted); }

/* Summary Boxes */
.io-io-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 10px; }
@media(max-width: 600px) { .io-io-summary { grid-template-columns: 1fr; } }
.sum-title { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-bottom: 12px; font-family: 'Outfit', sans-serif; }
.sum-icon { display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 8px; font-size: 14px; }
.sum-icon.in { background: rgba(99,102,241,0.15); }
.sum-icon.out { background: rgba(16,185,129,0.15); }

.sum-box { background: rgba(0,0,0,0.2); border: 1px solid var(--border); border-radius: 12px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.io-sum-row { display: flex; align-items: center; gap: 8px; font-size: 12px; padding-bottom: 8px; border-bottom: 1px dashed rgba(255,255,255,0.05); }
.io-sum-row:last-child { border-bottom: none; padding-bottom: 0; }
.io-sum-row code { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #a5b4fc; background: rgba(99,102,241,0.1); padding: 2px 6px; border-radius: 4px; }
.io-sum-row span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text); }

/* Badges */
.badge { display: inline-flex; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
.badge.lg { padding: 6px 14px; font-size: 12px; }
.badge.sm { font-size: 9px; padding: 2px 6px; border-radius: 6px; flex-shrink: 0; }
.badge.complete,.badge.valid,.badge.success,.badge.response { background: rgba(16,185,129,0.15); color: var(--c-emerald); border: 1px solid rgba(16,185,129,0.2); }
.badge.partial,.badge.warning,.badge.pending,.badge.side_effect { background: rgba(245,158,11,0.15); color: var(--c-amber); border: 1px solid rgba(245,158,11,0.2); }
.badge.failed,.badge.invalid,.badge.error { background: rgba(244,63,94,0.15); color: var(--c-rose); border: 1px solid rgba(244,63,94,0.2); }
.badge.event { background: rgba(139,92,246,0.15); color: var(--c-purple); border: 1px solid rgba(139,92,246,0.2); }

/* Utils */
.mono { font-family: 'JetBrains Mono', monospace; }
.muted { color: var(--muted); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.fade-in { animation: fi 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
@keyframes fi { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

@media(max-width: 1024px) {
  .io-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
