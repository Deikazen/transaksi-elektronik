<template>
  <div class="pos-page fade-in">
    <div class="pos-layout">
      <!-- ═══ PRODUCT CATALOG ═══ -->
      <div class="pos-catalog">
        <div class="catalog-card">
          <div class="catalog-header">
            <h3><ShoppingCart :size="18"/> Katalog Produk</h3>
            <span class="muted">{{ products.length }} produk tersedia</span>
          </div>
          <div class="catalog-search">
            <Search :size="16" class="search-ico"/>
            <input type="search" v-model="productSearch" placeholder="Cari produk..." />
          </div>
          <div v-if="loading" class="loading-state">
            <Loader :size="24" class="spin"/> Memuat produk...
          </div>
          <div v-else-if="filteredProducts.length === 0" class="empty-catalog">
            <PackageX :size="32"/>
            <p>Tidak ada produk ditemukan.</p>
          </div>
          <div v-else class="product-grid">
            <div
              v-for="p in filteredProducts" :key="p.id"
              class="product-card"
              :class="{ 'out-of-stock': p.stok === 0 }"
              @click="addToCart(p)"
            >
              <div class="p-icon"><Package :size="24"/></div>
              <div class="p-name">{{ p.nama_produk }}</div>
              <div class="p-price">{{ formatRp(p.harga) }}</div>
              <div class="p-stock" :class="{ 'low': p.stok > 0 && p.stok < 5, 'out': p.stok === 0 }">
                {{ p.stok === 0 ? 'Habis' : `Stok: ${p.stok}` }}
              </div>
              <button class="add-btn" :disabled="p.stok === 0" @click.stop="addToCart(p)">
                <Plus :size="14"/> Tambah
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ CART SIDEBAR ═══ -->
      <div class="pos-cart">
        <div class="cart-card">
          <div class="cart-header">
            <h3><ShoppingBag :size="18"/> Keranjang</h3>
            <button v-if="cart.length > 0" class="clear-btn" @click="cart = []">
              <Trash2 :size="14"/> Kosongkan
            </button>
          </div>

          <!-- Empty cart -->
          <div v-if="cart.length === 0" class="empty-cart">
            <ShoppingBag :size="40"/>
            <p>Keranjang kosong</p>
            <span class="muted">Klik produk untuk menambahkan</span>
          </div>

          <!-- Cart items -->
          <div v-else class="cart-body">
            <div class="cart-items">
              <div
                v-for="(item, idx) in cart" :key="item.id"
                class="cart-item"
                :class="{ 'over-stock': isOverStock(item) }"
              >
                <div class="ci-info">
                  <strong>{{ item.nama_produk }}</strong>
                  <span class="muted">{{ formatRp(item.harga) }} /unit</span>
                  <span v-if="isOverStock(item)" class="stock-warn">
                    <AlertTriangle :size="12"/> Melebihi stok (maks: {{ getMaxStock(item) }})
                  </span>
                </div>
                <div class="ci-right">
                  <div class="qty-ctrl">
                    <button @click="decQty(idx)"><Minus :size="14"/></button>
                    <span>{{ item.qty }}</span>
                    <button @click="incQty(idx)"><Plus :size="14"/></button>
                  </div>
                  <span class="ci-sub">{{ formatRp(item.harga * item.qty) }}</span>
                  <button class="remove-btn" @click="cart.splice(idx, 1)"><X :size="14"/></button>
                </div>
              </div>
            </div>

            <!-- Summary -->
            <div class="cart-footer">
              <div class="summary">
                <div class="sum-row"><span>Subtotal</span><span>{{ formatRp(subtotal) }}</span></div>
                <div class="sum-row"><span>PPN (11%)</span><span>{{ formatRp(ppn) }}</span></div>
                <div class="sum-row total"><span>GRAND TOTAL</span><span>{{ formatRp(grandTotal) }}</span></div>
              </div>
              <div class="checkout-form">
                <label>Nama Klien / Perusahaan <span class="req">*</span></label>
                <input v-model="clientName" type="text" placeholder="PT Maju Jaya..." />
              </div>
              <button
                class="checkout-btn"
                :disabled="!canCheckout"
                @click="doCheckout"
              >
                <component :is="processing ? Loader : CheckCircle" :size="16" :class="{ spin: processing }"/>
                {{ processing ? 'Memproses...' : 'Checkout & Generate Kontrak' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ RECEIPT MODAL ═══ -->
    <div class="modal-overlay" v-if="showReceipt" @click.self="showReceipt = false">
      <div class="receipt-modal fade-in">
        <div class="receipt-head">
          <div>
            <h2>INVOICE</h2>
            <span class="mono muted">#{{ receipt.kode }}</span>
          </div>
          <div class="receipt-brand"><ShieldCheck :size="16"/> SecureTransact</div>
        </div>
        <div class="receipt-meta">
          <div><span class="muted">Kepada: </span><strong>{{ receipt.nama_klien }}</strong></div>
          <div><span class="muted">Tanggal: </span>{{ receipt.dateStr }}</div>
        </div>
        <table class="receipt-table">
          <thead><tr><th>Produk</th><th class="tc">Qty</th><th class="tr">Harga</th><th class="tr">Subtotal</th></tr></thead>
          <tbody>
            <tr v-for="it in receipt.items" :key="it.id">
              <td>{{ it.nama_produk }}</td>
              <td class="tc">{{ it.qty }}</td>
              <td class="tr mono">{{ formatRp(it.harga) }}</td>
              <td class="tr mono bold">{{ formatRp(it.harga * it.qty) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="receipt-totals">
          <div class="sum-row"><span>Subtotal</span><span>{{ formatRp(receipt.total) }}</span></div>
          <div class="sum-row"><span>PPN (11%)</span><span>{{ formatRp(receipt.ppn) }}</span></div>
          <div class="sum-row total"><span>GRAND TOTAL</span><span>{{ formatRp(receipt.grand_total) }}</span></div>
        </div>
        <div class="receipt-status">
          <CheckCircle :size="16" class="text-green"/> Transaksi berhasil — Kontrak digital sedang di-generate
        </div>
        <div class="receipt-footer">
          <button class="btn-secondary" @click="showReceipt = false">Tutup</button>
          <button class="btn-primary" @click="showReceipt = false">
            <CheckCircle :size="14"/> Selesai
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ ERROR TOAST ═══ -->
    <div class="pos-toast" :class="{ show: toastVisible, error: toastType === 'error', success: toastType === 'success' }">
      <component :is="toastType === 'error' ? AlertTriangle : CheckCircle" :size="16"/>
      {{ toastMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { inventoryApi, transactionApi } from '../services/api.js'
import {
  ShoppingCart, ShoppingBag, Search, Package, PackageX, Plus, Minus,
  Trash2, X, Loader, CheckCircle, ShieldCheck, AlertTriangle
} from 'lucide-vue-next'

// ── Props & Emits ──
const emit = defineEmits(['checkout-success'])

// ── State ──
const products = ref([])
const loading = ref(false)
const productSearch = ref('')
const cart = ref([])
const clientName = ref('')
const processing = ref(false)
const showReceipt = ref(false)
const receipt = ref({ kode: '', nama_klien: '', total: 0, ppn: 0, grand_total: 0, items: [], dateStr: '' })

// Toast
const toastVisible = ref(false)
const toastMsg = ref('')
const toastType = ref('success')

function showToast(msg, type = 'success') {
  toastMsg.value = msg
  toastType.value = type
  toastVisible.value = true
  setTimeout(() => toastVisible.value = false, 3500)
}

// ── Computed ──
const filteredProducts = computed(() => {
  if (!productSearch.value) return products.value
  const q = productSearch.value.toLowerCase()
  return products.value.filter(p => p.nama_produk.toLowerCase().includes(q))
})

const subtotal = computed(() => cart.value.reduce((s, i) => s + i.harga * i.qty, 0))
const ppn = computed(() => Math.round(subtotal.value * 0.11))
const grandTotal = computed(() => subtotal.value + ppn.value)

const hasOverStock = computed(() => cart.value.some(item => isOverStock(item)))

const canCheckout = computed(() =>
  cart.value.length > 0 &&
  clientName.value.trim() !== '' &&
  !hasOverStock.value &&
  !processing.value
)

// ── Helpers ──
function formatRp(v) {
  return 'Rp ' + Number(v).toLocaleString('id-ID')
}

function getMaxStock(item) {
  const prod = products.value.find(p => p.id === item.id)
  return prod ? prod.stok : 0
}

function isOverStock(item) {
  return item.qty > getMaxStock(item)
}

// ── Cart ops ──
function addToCart(p) {
  if (p.stok === 0) { showToast('Stok habis!', 'error'); return }
  const existing = cart.value.find(c => c.id === p.id)
  if (existing) {
    if (existing.qty >= p.stok) { showToast(`Stok ${p.nama_produk} tidak cukup!`, 'error'); return }
    existing.qty++
  } else {
    cart.value.push({ id: p.id, nama_produk: p.nama_produk, harga: p.harga, qty: 1 })
  }
}

function incQty(idx) {
  const item = cart.value[idx]
  const max = getMaxStock(item)
  if (item.qty >= max) { showToast('Stok tidak cukup!', 'error'); return }
  item.qty++
}

function decQty(idx) {
  if (cart.value[idx].qty <= 1) cart.value.splice(idx, 1)
  else cart.value[idx].qty--
}

// ── Checkout ──
async function doCheckout() {
  if (!canCheckout.value) return
  processing.value = true
  try {
    const payload = {
      nama_klien: clientName.value,
      items: cart.value.map(i => ({ produk_id: i.id, qty: i.qty }))
    }
    const res = await transactionApi.create(payload)
    const data = res.data

    receipt.value = {
      kode: data.kode,
      nama_klien: data.nama_klien,
      total: data.total,
      ppn: data.ppn,
      grand_total: data.grand_total,
      items: data.items || [],
      dateStr: new Date(data.created_at).toLocaleDateString('id-ID', {
        day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
      })
    }

    showReceipt.value = true
    cart.value = []
    clientName.value = ''
    showToast(`Transaksi ${data.kode} berhasil!`)

    // Refresh product list (stok updated)
    await fetchProducts()
    emit('checkout-success')
  } catch (err) {
    showToast(err.message || 'Gagal memproses checkout', 'error')
  } finally {
    processing.value = false
  }
}

// ── Fetch ──
async function fetchProducts() {
  loading.value = true
  try {
    const data = await inventoryApi.getAll()
    products.value = data.data || []
  } catch {
    products.value = []
    showToast('Gagal memuat produk dari server', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchProducts)
</script>

<style scoped>
/* ═══ Layout ═══ */
.pos-page { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.pos-layout { display: grid; grid-template-columns: 1.6fr 1fr; gap: 20px; flex: 1; min-height: 0; }

/* ═══ Catalog Card ═══ */
.catalog-card, .cart-card {
  background: rgba(18,18,20,0.6); border: 1px solid var(--border); border-radius: 16px;
  padding: 24px; display: flex; flex-direction: column; height: 100%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3); backdrop-filter: blur(12px);
}
.catalog-header, .cart-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
}
.catalog-header h3, .cart-header h3 {
  font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 600;
  display: flex; align-items: center; gap: 8px; letter-spacing: -0.02em;
}
.catalog-search { position: relative; margin-bottom: 16px; }
.catalog-search .search-ico { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--muted); }
.catalog-search input {
  width: 100%; background: var(--surface2); border: 1px solid var(--border); color: var(--text);
  padding: 10px 16px 10px 36px; border-radius: 10px; font-size: 14px; outline: none;
  font-family: 'Inter', sans-serif; transition: 0.2s;
}
.catalog-search input:focus { border-color: var(--c-indigo); box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }

/* ═══ Product Grid ═══ */
.product-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px;
  overflow-y: auto; flex: 1; align-content: start; padding-right: 4px;
}
.product-card {
  background: var(--surface2); border: 1px solid var(--border); border-radius: 14px;
  padding: 18px 14px 14px; cursor: pointer; transition: all 0.2s; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.product-card:hover { border-color: var(--c-indigo); background: rgba(99,102,241,0.05); transform: translateY(-2px); }
.product-card.out-of-stock { opacity: 0.35; pointer-events: none; }
.p-icon { color: var(--muted); background: var(--surface3); padding: 12px; border-radius: 12px; }
.p-name { font-size: 13px; font-weight: 500; line-height: 1.4; min-height: 36px; display: flex; align-items: center; }
.p-price { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--c-indigo); font-weight: 600; }
.p-stock { font-size: 11px; color: var(--muted); }
.p-stock.low { color: var(--c-amber); }
.p-stock.out { color: var(--c-rose); font-weight: 600; }
.add-btn {
  background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2); color: var(--c-indigo);
  padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; gap: 4px; transition: 0.2s; width: 100%; justify-content: center;
}
.add-btn:hover { background: rgba(99,102,241,0.2); }
.add-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* ═══ Cart ═══ */
.clear-btn {
  background: none; border: none; color: var(--c-rose); font-size: 13px; font-weight: 500;
  cursor: pointer; display: flex; align-items: center; gap: 4px; transition: 0.2s;
}
.clear-btn:hover { opacity: 0.7; }
.empty-cart {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 40px 20px; color: var(--muted); border: 1px dashed var(--border);
  border-radius: 12px; gap: 8px;
}
.cart-body { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
.cart-items { flex: 1; overflow-y: auto; padding-right: 4px; }
.cart-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 0; border-bottom: 1px solid var(--border); gap: 10px;
}
.cart-item.over-stock { background: rgba(244,63,94,0.06); border-radius: 8px; padding: 14px 10px; border-color: rgba(244,63,94,0.2); }
.ci-info { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.ci-info strong { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ci-right { display: flex; align-items: center; gap: 10px; }
.stock-warn { color: var(--c-rose); font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.ci-sub {
  font-family: 'JetBrains Mono', monospace; font-size: 12px; min-width: 80px;
  text-align: right; color: var(--text); font-weight: 500;
}
.qty-ctrl {
  display: flex; align-items: center; gap: 8px; background: var(--surface2);
  padding: 4px; border-radius: 8px; border: 1px solid var(--border);
}
.qty-ctrl button {
  background: transparent; border: none; color: var(--text); width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center; cursor: pointer; border-radius: 4px;
}
.qty-ctrl button:hover { background: var(--surface3); }
.qty-ctrl span { font-size: 13px; font-family: 'JetBrains Mono', monospace; min-width: 20px; text-align: center; }
.remove-btn {
  background: transparent; border: none; color: var(--c-rose); width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center; cursor: pointer; border-radius: 4px; opacity: 0.6;
}
.remove-btn:hover { opacity: 1; background: rgba(244,63,94,0.1); }

/* ═══ Cart Footer ═══ */
.cart-footer { margin-top: auto; padding-top: 16px; border-top: 1px solid var(--border); }
.summary { background: var(--surface2); padding: 16px; border-radius: 12px; margin-bottom: 14px; }
.sum-row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; color: var(--muted); }
.sum-row.total {
  margin-bottom: 0; padding-top: 10px; border-top: 1px solid var(--border);
  color: var(--text); font-size: 18px; font-weight: 700; font-family: 'Outfit', sans-serif;
}
.checkout-form { margin-bottom: 12px; }
.checkout-form label { font-size: 13px; color: var(--muted); font-weight: 500; display: block; margin-bottom: 6px; }
.checkout-form .req { color: var(--c-rose); }
.checkout-form input {
  width: 100%; background: var(--surface2); border: 1px solid var(--border); color: var(--text);
  padding: 10px 14px; border-radius: 10px; font-size: 14px; outline: none; transition: 0.2s;
}
.checkout-form input:focus { border-color: var(--c-indigo); box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }
.checkout-btn {
  width: 100%; background: var(--text); color: var(--bg); border: none; padding: 14px;
  border-radius: 10px; font-size: 14px; font-weight: 600; display: flex; align-items: center;
  justify-content: center; gap: 8px; cursor: pointer; transition: 0.15s;
  box-shadow: 0 4px 12px rgba(255,255,255,0.1);
}
.checkout-btn:hover { opacity: 0.9; transform: translateY(-1px); }
.checkout-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

/* ═══ Receipt Modal ═══ */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.receipt-modal {
  background: var(--surface); border: 1px solid var(--border); border-radius: 20px;
  width: 560px; max-height: 90vh; overflow-y: auto; box-shadow: 0 24px 48px rgba(0,0,0,0.5);
}
.receipt-head { padding: 28px 28px 20px; display: flex; justify-content: space-between; align-items: flex-start; }
.receipt-head h2 { font-family: 'Outfit', sans-serif; font-size: 26px; letter-spacing: 3px; }
.receipt-brand { font-family: 'Outfit', sans-serif; font-weight: 600; display: flex; align-items: center; gap: 6px; font-size: 14px; }
.receipt-meta { padding: 0 28px 20px; display: flex; justify-content: space-between; font-size: 14px; }
.receipt-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.receipt-table th {
  text-align: left; padding: 12px 28px; color: var(--muted); font-size: 12px;
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
  border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
}
.receipt-table td { padding: 12px 28px; border-bottom: 1px solid rgba(39,39,42,0.5); }
.receipt-table .tc { text-align: center; } .receipt-table .tr { text-align: right; }
.receipt-totals { padding: 16px 28px 20px; display: flex; flex-direction: column; align-items: flex-end; }
.receipt-totals .sum-row { min-width: 280px; }
.receipt-status {
  margin: 0 28px 20px; background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2);
  padding: 12px 16px; border-radius: 10px; font-size: 13px; font-weight: 500;
  display: flex; align-items: center; gap: 8px; color: var(--c-emerald);
}
.receipt-footer {
  padding: 18px 28px; border-top: 1px solid var(--border); display: flex;
  justify-content: flex-end; gap: 12px; background: var(--surface2); border-radius: 0 0 20px 20px;
}

/* ═══ Shared button styles ═══ */
.btn-primary {
  background: var(--text); color: var(--bg); border: none; padding: 10px 20px;
  border-radius: 10px; font-size: 14px; font-weight: 600; display: inline-flex;
  align-items: center; gap: 8px; cursor: pointer; transition: 0.15s;
}
.btn-primary:hover { opacity: 0.9; }
.btn-secondary {
  background: transparent; color: var(--text); border: 1px solid var(--border);
  padding: 10px 20px; border-radius: 10px; font-size: 14px; font-weight: 500;
  cursor: pointer; transition: 0.2s; display: inline-flex; align-items: center; gap: 8px;
}
.btn-secondary:hover { background: var(--surface2); }

/* ═══ Toast ═══ */
.pos-toast {
  position: fixed; bottom: 32px; right: 32px; background: var(--surface); border: 1px solid var(--border);
  padding: 14px 22px; border-radius: 12px; font-size: 14px; font-weight: 500;
  display: flex; align-items: center; gap: 10px; z-index: 2000;
  transform: translateY(100px); opacity: 0; transition: all 0.4s cubic-bezier(0.68,-0.55,0.27,1.55);
  box-shadow: 0 12px 24px rgba(0,0,0,0.3);
}
.pos-toast.show { transform: translateY(0); opacity: 1; }
.pos-toast.error { border-color: var(--c-rose); color: var(--c-rose); }
.pos-toast.success { border-color: var(--c-emerald); color: var(--c-emerald); }

/* ═══ Utilities ═══ */
.muted { color: var(--muted); }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.bold { font-weight: 600; }
.text-green { color: var(--c-emerald); }
.loading-state { display: flex; align-items: center; gap: 12px; padding: 40px; color: var(--muted); justify-content: center; }
.empty-catalog { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 60px; color: var(--muted); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.fade-in { animation: fi 0.3s ease-out; }
@keyframes fi { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* ═══ Responsive ═══ */
@media (max-width: 1024px) {
  .pos-layout { grid-template-columns: 1fr; }
}
</style>
