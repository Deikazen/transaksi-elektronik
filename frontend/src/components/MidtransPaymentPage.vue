<template>
  <div class="pay-page fade-in">
    <div class="pay-hero">
      <div class="pay-hero-content">
        <div class="pay-hero-icon"><History :size="28" /></div>
        <div>
          <h2>Monitoring Bayar</h2>
          <p class="muted">Log dan riwayat transaksi via Midtrans</p>
        </div>
      </div>
      <div class="pay-hero-badge" :class="configLoaded ? 'online' : 'checking'">
        <component :is="configLoaded ? CheckCircle : Loader" :size="14" :class="{spin:!configLoaded}" />
        {{ configLoaded ? (payConfig.is_production ? 'Production' : 'Sandbox') : 'Loading...' }}
      </div>
    </div>

    <div class="pay-layout">


      <!-- Right: Payment History -->
      <div class="pay-history-panel">
        <div class="pay-card">
          <div class="pay-card-header">
            <h3><History :size="18" /> Riwayat Pembayaran</h3>
            <button class="btn-refresh-sm" @click="fetchHistory" :disabled="historyLoading">
              <RefreshCw :size="14" :class="{spin:historyLoading}" />
            </button>
          </div>

          <div v-if="historyLoading" class="pay-loading"><Loader :size="20" class="spin" /> Memuat...</div>
          <div v-else-if="paymentHistory.length === 0" class="pay-empty">
            <Wallet :size="40" />
            <p>Belum ada riwayat pembayaran</p>
            <span class="muted">Buat pembayaran untuk memulai</span>
          </div>
          <div v-else class="pay-history-list">
            <div v-for="ph in paymentHistory" :key="ph.id" class="pay-history-item" :class="ph.payment_status">
              <div class="ph-top">
                <div class="ph-order">
                  <code>{{ ph.order_id }}</code>
                  <span class="muted">{{ ph.transaksi_kode }}</span>
                </div>
                <span class="badge sm" :class="ph.payment_status">{{ ph.payment_status }}</span>
              </div>
              <div class="ph-body">
                <span class="ph-client">{{ ph.nama_klien }}</span>
                <span class="ph-amount mono bold">{{ formatRp(ph.gross_amount) }}</span>
              </div>
              <div class="ph-bottom">
                <span class="muted">{{ ph.payment_type || 'snap' }}</span>
                <span class="muted">{{ formatDate(ph.created_at) }}</span>
              </div>
              <div class="ph-actions" v-if="ph.payment_status === 'pending'">
                <button class="btn-sim-sm" @click="simulateById(ph.order_id)">
                  <CheckCircle :size="12" /> Simulasi Bayar
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Payment Channel Info -->
        <div class="pay-card pay-channels">
          <h3><Shield :size="18" /> Channel Pembayaran</h3>
          <div class="channel-grid">
            <div class="channel-item" v-for="ch in channels" :key="ch.name">
              <div class="channel-icon" :style="{background:ch.bg}"><component :is="ch.icon" :size="16" :style="{color:ch.color}" /></div>
              <div class="channel-info">
                <strong>{{ ch.name }}</strong>
                <span class="muted">{{ ch.desc }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { transactionApi, paymentApi } from '../services/api.js'
import {
  CreditCard, CheckCircle, Loader, Zap, AlertTriangle, ExternalLink, History,
  RefreshCw, Wallet, Shield, Landmark, Smartphone, QrCode, Store, Globe, Building2
} from 'lucide-vue-next'

const configLoaded = ref(false)
const payConfig = ref({ is_production: false, client_key: '', snap_url: '' })
const paymentHistory = ref([])
const historyLoading = ref(false)

const channels = [
  { name:'Bank Transfer', desc:'BCA, BNI, BRI, Mandiri VA', icon:Landmark, bg:'rgba(99,102,241,0.12)', color:'#6366f1' },
  { name:'E-Wallet', desc:'GoPay, ShopeePay, DANA', icon:Smartphone, bg:'rgba(16,185,129,0.12)', color:'#10b981' },
  { name:'QRIS', desc:'Scan QR universal', icon:QrCode, bg:'rgba(139,92,246,0.12)', color:'#8b5cf6' },
  { name:'Retail', desc:'Indomaret, Alfamart', icon:Store, bg:'rgba(245,158,11,0.12)', color:'#f59e0b' },
]

function formatRp(v) { return 'Rp ' + Number(v).toLocaleString('id-ID') }
function formatDate(d) { if(!d) return '-'; return new Date(d).toLocaleDateString('id-ID',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}) }

async function fetchConfig() {
  try {
    const res = await paymentApi.getConfig()
    payConfig.value = res.data
    configLoaded.value = true
  } catch { configLoaded.value = true }
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    const res = await paymentApi.getHistory()
    paymentHistory.value = res.data || []
  } catch {} finally { historyLoading.value = false }
}

async function simulateById(orderId) {
  try {
    await paymentApi.simulateSuccess(orderId)
    alert('Pembayaran berhasil disimulasikan!')
    await fetchHistory()
  } catch(e) { alert(e.message) }
}

onMounted(async () => {
  await Promise.all([fetchConfig(), fetchHistory()])
  // Load Midtrans Snap JS
  if(payConfig.value.snap_url) {
    const s = document.createElement('script')
    s.src = payConfig.value.snap_url
    s.setAttribute('data-client-key', payConfig.value.client_key)
    document.head.appendChild(s)
  }
})
</script>

<style scoped>
.pay-page{flex:1;display:flex;flex-direction:column;gap:20px;min-height:0;overflow-y:auto}
.pay-hero{display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,rgba(139,92,246,0.1),rgba(99,102,241,0.08));border:1px solid rgba(139,92,246,0.2);border-radius:16px;padding:20px 24px}
.pay-hero-content{display:flex;align-items:center;gap:16px}
.pay-hero-icon{background:rgba(139,92,246,0.15);color:var(--c-purple);padding:12px;border-radius:14px;display:flex}
.pay-hero h2{font-family:'Outfit',sans-serif;font-size:20px;font-weight:700}
.pay-hero-badge{display:flex;align-items:center;gap:6px;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600}
.pay-hero-badge.online{background:rgba(16,185,129,0.12);color:var(--c-emerald);border:1px solid rgba(16,185,129,0.2)}
.pay-hero-badge.checking{background:rgba(99,102,241,0.12);color:var(--c-indigo);border:1px solid rgba(99,102,241,0.2)}

.pay-layout{display:flex;flex-direction:column;gap:20px;flex:1;min-height:0}
.pay-card{background:rgba(18,18,20,0.6);border:1px solid var(--border);border-radius:16px;padding:24px;box-shadow:0 8px 32px rgba(0,0,0,0.3);backdrop-filter:blur(12px);margin-bottom:20px}
.pay-card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.pay-card-header h3{font-family:'Outfit',sans-serif;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}


.pay-loading{display:flex;align-items:center;gap:12px;padding:40px;color:var(--muted);justify-content:center;font-size:13px}
.pay-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:40px 20px;color:var(--muted);gap:8px;border:1px dashed var(--border);border-radius:12px}
.pay-history-list{display:flex;flex-direction:column;gap:8px;max-height:400px;overflow-y:auto}
.pay-history-item{background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:14px;transition:0.2s}
.pay-history-item:hover{border-color:var(--border-hover)}
.pay-history-item.settlement{border-left:3px solid var(--c-emerald)}
.pay-history-item.pending{border-left:3px solid var(--c-amber)}
.pay-history-item.deny,.pay-history-item.cancel,.pay-history-item.expire{border-left:3px solid var(--c-rose)}
.ph-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.ph-order{display:flex;flex-direction:column;gap:2px}
.ph-order code{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--c-indigo)}
.ph-body{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.ph-client{font-size:14px;font-weight:600}
.ph-amount{font-size:15px}
.ph-bottom{display:flex;justify-content:space-between;font-size:11px}
.ph-actions{margin-top:8px;display:flex;gap:6px}
.btn-sim-sm{background:rgba(16,185,129,0.12);color:var(--c-emerald);border:1px solid rgba(16,185,129,0.2);padding:5px 10px;border-radius:6px;font-size:11px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:4px}
.btn-refresh-sm{background:transparent;border:none;color:var(--muted);cursor:pointer;padding:4px;display:flex}
.btn-refresh-sm:hover{color:var(--text)}

.pay-channels{padding:20px}
.pay-channels h3{font-family:'Outfit',sans-serif;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px;margin-bottom:16px}
.channel-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.channel-item{display:flex;align-items:center;gap:12px;padding:12px;background:var(--surface2);border-radius:10px}
.channel-icon{padding:8px;border-radius:8px;display:flex}
.channel-info{display:flex;flex-direction:column;gap:2px}
.channel-info strong{font-size:13px}
.channel-info .muted{font-size:11px}

.badge{display:inline-flex;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:600}
.badge.lunas,.badge.settlement{background:rgba(16,185,129,0.15);color:var(--c-emerald)}
.badge.pending{background:rgba(245,158,11,0.15);color:var(--c-amber)}
.badge.deny,.badge.cancel,.badge.expire{background:rgba(244,63,94,0.15);color:var(--c-rose)}
.badge.sm{font-size:10px;padding:2px 6px}
.mono{font-family:'JetBrains Mono',monospace;font-size:13px}
.bold{font-weight:600}
.muted{color:var(--muted)}
.spin{animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.fade-in{animation:fi 0.3s ease-out}
@keyframes fi{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:1024px){.pay-layout{grid-template-columns:1fr}.channel-grid{grid-template-columns:1fr}}
</style>
