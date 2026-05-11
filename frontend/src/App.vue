<template>
  <div id="app">
    <div class="app-background"></div>

    <!-- AUTHENTICATION UI -->
    <div v-if="!authState.isAuthenticated" class="auth-container fade-in">
      <div class="auth-card">
        <div class="auth-header" style="text-align:center; margin-bottom:24px;">
          <div class="logo" style="justify-content:center; margin-bottom:16px;">
            <span class="logo-icon"><component :is="icons.ShieldCheck" size="24" stroke-width="2.5" /></span>
            <span class="logo-text" style="font-size:20px">SecureTransact</span>
          </div>
          <h2 v-if="authView === 'login'">Masuk ke Akun</h2>
          <h2 v-else-if="authView === 'register'">Daftar Akun Baru</h2>
          <h2 v-else>Lupa Password</h2>
        </div>
        
        <div v-if="authView === 'login'" class="auth-form">
          <div class="form-group">
            <label>Username</label>
            <input type="text" v-model="loginForm.username" placeholder="Masukkan username" @keyup.enter="handleLogin" />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" v-model="loginForm.password" placeholder="Masukkan password" @keyup.enter="handleLogin" />
          </div>
          <div style="display:flex; justify-content:flex-end; margin-bottom:16px;">
            <button class="btn-link" @click="authView = 'forgot'">Lupa password?</button>
          </div>
          <button class="btn-primary full-w" @click="handleLogin" :disabled="loginForm.loading">
            <component :is="loginForm.loading ? icons.Loader : icons.CheckCircle" size="16" :class="{spin:loginForm.loading}"/>
            {{ loginForm.loading ? 'Memproses...' : 'Masuk' }}
          </button>
          <div style="text-align:center; margin-top:16px; font-size:13px" class="muted">
            Belum punya akun? <button class="btn-link" style="display:inline; color:var(--c-indigo)" @click="authView = 'register'">Daftar</button>
          </div>
        </div>

        <div v-if="authView === 'register'" class="auth-form">
          <div class="form-group">
            <label>Username</label>
            <input type="text" v-model="registerForm.username" placeholder="Buat username tanpa spasi" />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" v-model="registerForm.email" placeholder="nama@email.com" />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" v-model="registerForm.password" placeholder="Minimal 8 karakter" />
          </div>
          <div class="form-group">
            <label>Role</label>
            <select v-model="registerForm.role" style="background:var(--surface2); border:1px solid var(--border); color:var(--text); padding:12px 16px; border-radius:10px; outline:none; font-family:'Inter',sans-serif;">
              <option value="kasir">Kasir</option>
              <option value="manajer">Manajer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button class="btn-primary full-w mt-2" @click="handleRegister" :disabled="registerForm.loading">
            <component :is="registerForm.loading ? icons.Loader : icons.Plus" size="16" :class="{spin:registerForm.loading}"/>
            {{ registerForm.loading ? 'Memproses...' : 'Daftar' }}
          </button>
          <div style="text-align:center; margin-top:16px; font-size:13px" class="muted">
            Sudah punya akun? <button class="btn-link" style="display:inline; color:var(--c-indigo)" @click="authView = 'login'">Masuk</button>
          </div>
        </div>

        <div v-if="authView === 'forgot'" class="auth-form">
          <div class="form-group">
            <label>Username</label>
            <input type="text" v-model="forgotForm.username" placeholder="Username akun Anda" />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" v-model="forgotForm.email" placeholder="Email yang terdaftar" />
          </div>
          <div class="form-group">
            <label>Password Baru</label>
            <input type="password" v-model="forgotForm.new_password" placeholder="Password baru" />
          </div>
          <button class="btn-primary full-w mt-2" @click="handleForgot" :disabled="forgotForm.loading">
            <component :is="forgotForm.loading ? icons.Loader : icons.CheckCircle" size="16" :class="{spin:forgotForm.loading}"/>
            {{ forgotForm.loading ? 'Memproses...' : 'Reset Password' }}
          </button>
          <div style="text-align:center; margin-top:16px; font-size:13px" class="muted">
            Kembali ke <button class="btn-link" style="display:inline; color:var(--c-indigo)" @click="authView = 'login'">Login</button>
          </div>
        </div>
      </div>
    </div>

    <!-- MAIN APP UI -->
    <template v-else>
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }" aria-label="Navigasi samping">
      <div class="sidebar-header">
        <div class="logo">
          <span class="logo-icon"><component :is="icons.ShieldCheck" size="18" stroke-width="2.5" /></span>
          <span class="logo-text" v-show="!sidebarCollapsed">SecureTransact</span>
        </div>
        <button
          class="collapse-btn"
          type="button"
          :aria-label="sidebarCollapsed ? 'Perluas sidebar' : 'Ciutkan sidebar'"
          @click="sidebarCollapsed = !sidebarCollapsed"
        >
          <component :is="sidebarCollapsed ? icons.ChevronRight : icons.ChevronLeft" size="18" />
        </button>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-group">
          <span class="nav-label" v-show="!sidebarCollapsed">Utama</span>
          <button
            v-for="item in permittedNavMain"
            :key="item.id"
            class="nav-item"
            :class="{ active: currentPage === item.id }"
            @click="currentPage = item.id"
          >
            <span class="nav-icon"><component :is="item.icon" size="18" /></span>
            <span class="nav-text" v-show="!sidebarCollapsed">{{ item.label }}</span>
          </button>
        </div>
        <div class="nav-group" v-if="permittedNavAdvanced.length > 0">
          <span class="nav-label" v-show="!sidebarCollapsed">Fitur Lanjutan</span>
          <button
            v-for="item in permittedNavAdvanced"
            :key="item.id"
            class="nav-item"
            :class="{ active: currentPage === item.id }"
            @click="currentPage = item.id"
          >
            <span class="nav-icon"><component :is="item.icon" size="18" /></span>
            <span class="nav-text" v-show="!sidebarCollapsed">{{ item.label }}</span>
          </button>
        </div>
      </nav>
      <div class="sidebar-footer" v-show="!sidebarCollapsed">
        <div class="user-info">
          <div class="user-avatar">{{ authState.user ? authState.user.username.substring(0,2).toUpperCase() : 'U' }}</div>
          <div class="user-details">
            <span class="user-name">{{ authState.user ? authState.user.username : 'User' }}</span>
            <span class="user-role">{{ authState.user ? authState.user.role.toUpperCase() : 'GUEST' }}</span>
          </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
          <div class="status-dot" :class="backendStatus">
            <component :is="backendStatus === 'online' ? icons.Server : icons.ServerOff" size="14" />
            {{ backendStatus === 'online' ? 'Online' : 'Offline' }}
          </div>
          <button class="btn-link danger" @click="handleLogout" style="font-size:12px">Logout</button>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">{{ currentPageMeta.title }}</h1>
          <span class="page-subtitle">{{ currentPageMeta.subtitle }}</span>
        </div>
        <div class="topbar-right">
          <div class="search-bar">
            <component :is="icons.Search" size="16" class="search-icon" />
            <input
              type="search"
              placeholder="Cari produk, transaksi..."
              v-model="searchQuery"
            />
          </div>
          <button class="notif-btn" type="button" aria-label="Notifikasi">
            <component :is="icons.Bell" size="18" />
            <span class="notif-dot"></span>
          </button>
        </div>
      </header>

      <div class="page-content">
        <!-- DASHBOARD -->
        <div v-if="currentPage === 'dashboard'" class="fade-in">
          <div class="stats-grid">
            <div class="stat-card" v-for="stat in dashboardStats" :key="stat.label" :style="{'--c': stat.color}">
              <div class="stat-top">
                <div class="stat-icon"><component :is="stat.icon" size="22" stroke-width="2" /></div>
                <div class="stat-trend up"><component :is="icons.TrendingUp" size="14" /> {{ stat.trend }}%</div>
              </div>
              <div class="stat-body">
                <span class="stat-value">{{ stat.value }}</span>
                <span class="stat-label">{{ stat.label }}</span>
              </div>
            </div>
          </div>
          <div class="dashboard-grid">
            <div class="card">
              <div class="card-header">
                <h3>Transaksi Terbaru</h3>
                <button class="btn-link" @click="currentPage = 'transaksi'">Lihat Semua <component :is="icons.ArrowRight" size="14" /></button>
              </div>
              <table class="data-table">
                <thead><tr><th>ID</th><th>Klien</th><th>Total</th><th>Status</th><th>Tanggal</th></tr></thead>
                <tbody>
                  <tr v-for="tx in transactions.slice(0,5)" :key="tx.id">
                    <td class="mono">#{{ tx.id }}</td>
                    <td>{{ tx.client }}</td>
                    <td class="mono bold">{{ formatRp(tx.total) }}</td>
                    <td><span class="badge" :class="tx.status">{{ tx.status }}</span></td>
                    <td class="muted">{{ tx.date }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="card">
              <div class="card-header"><h3>Status Sistem</h3></div>
              <div class="system-status">
                <div class="status-item" v-for="s in systemStatus" :key="s.name">
                  <div class="status-name">
                    <span class="dot" :class="s.status"></span> {{ s.name }}
                  </div>
                  <div class="bar-wrap"><div class="bar" :class="s.status" :style="{width: s.up+'%'}"></div></div>
                  <span class="muted">{{ s.up }}%</span>
                </div>
              </div>
              <div class="card-header" style="margin-top:24px"><h3>Checklist Keamanan</h3></div>
              <div class="sec-checks">
                <div class="check-item" v-for="c in secChecks" :key="c.name">
                  <span class="chk" :class="c.ok ? 'ok':'warn'">
                    <component :is="c.ok ? icons.CheckCircle : icons.AlertOctagon" size="14" />
                  </span>
                  <span>{{ c.name }}</span>
                  <span class="chk-status" :class="c.ok?'ok':'warn'">{{ c.ok ? 'Aktif':'Pending' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- INVENTORY -->
        <div v-if="currentPage === 'inventory'" class="fade-in">
          <div class="toolbar">
            <button class="btn-primary" @click="showAddProduct = true">
              <component :is="icons.Plus" size="16" /> Tambah Produk
            </button>
            <span class="muted">{{ filteredInventory.length }} produk</span>
          </div>
          <div v-if="inventoryLoading" class="loading-state"><component :is="icons.Loader" size="24" class="spin" /> Memuat dari backend...</div>
          <div v-else-if="inventoryError" class="error-state">
            <component :is="icons.AlertTriangle" size="24" class="text-warn" /> {{ inventoryError }}
            <button class="btn-secondary" @click="fetchInventory">Coba Lagi</button>
          </div>
          <div v-else class="card p-0">
            <table class="data-table full">
              <thead><tr><th>ID</th><th>Barcode</th><th>Nama Produk</th><th>Harga</th><th>Stok</th><th>Status</th><th>Aksi</th></tr></thead>
              <tbody>
                <tr v-for="item in filteredInventory" :key="item.id">
                  <td class="mono muted">#{{ item.id }}</td>
                  <td class="mono">{{ item.barcode || '-' }}</td>
                  <td><strong>{{ item.nama_produk }}</strong></td>
                  <td class="mono">{{ formatRp(item.harga) }}</td>
                  <td><span class="badge" :class="item.stok < 5 ? 'warn':'lunas'">{{ item.stok }} unit</span></td>
                  <td><span class="badge lunas">Aktif</span></td>
                  <td class="actions">
                    <button class="btn-icon" @click="openEditProduct(item)" title="Edit produk"><component :is="icons.Edit2" size="14"/></button>
                    <button class="btn-icon" @click="addToCart(item)" title="Tambah ke keranjang"><component :is="icons.ShoppingCart" size="14"/></button>
                    <button class="btn-icon danger" @click="deleteProduct(item.id)" title="Hapus"><component :is="icons.Trash2" size="14"/></button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- POS -->
        <div v-if="currentPage === 'pos'" class="fade-in h-full-flex">
          <div class="pos-layout">
            <div class="pos-catalog">
              <div class="card h-full">
                <div class="card-header">
                  <h3>Katalog Produk</h3>
                  <span class="muted">Klik untuk tambah</span>
                </div>
                <div class="product-grid">
                  <div v-for="item in inventoryData" :key="item.id" class="product-card"
                    :class="{'out-of-stock': item.stok === 0}" @click="addToCart(item)">
                    <div class="product-icon"><component :is="icons.Package" size="24" /></div>
                    <div class="product-name">{{ item.nama_produk }}</div>
                    <div class="product-price">{{ formatRp(item.harga) }}</div>
                    <div class="product-stock" :class="item.stok < 5 ? 'text-warn':''">Stok: {{ item.stok }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="pos-cart">
              <div class="card h-full">
                <div class="card-header">
                  <h3 class="flex items-center gap-2"><component :is="icons.ShoppingCart" size="18"/> Keranjang</h3>
                  <button v-if="cart.length > 0" class="btn-link danger" @click="cart = []">Kosongkan</button>
                </div>
                <div v-if="cart.length === 0" class="empty-cart flex-1 flex flex-col justify-center items-center">
                  <component :is="icons.ShoppingBag" size="32" />
                  <p>Klik produk untuk menambahkan</p>
                </div>
                <div v-else class="cart-content-wrapper">
                  <div class="cart-items-wrapper">
                    <div class="cart-item" v-for="(item, idx) in cart" :key="idx">
                      <div class="cart-info">
                        <strong>{{ item.nama_produk }}</strong>
                        <span class="muted">{{ formatRp(item.harga) }} /unit</span>
                      </div>
                      <div class="qty-ctrl">
                        <button @click="decQty(idx)"><component :is="icons.Minus" size="14"/></button>
                        <span>{{ item.qty }}</span>
                        <button @click="incQty(idx)"><component :is="icons.Plus" size="14"/></button>
                      </div>
                    </div>
                  </div>
                  <div class="cart-footer">
                    <div class="cart-summary">
                      <div class="sum-row"><span>Subtotal</span><span>{{ formatRp(subtotal) }}</span></div>
                      <div class="sum-row" v-if="diskonPersen > 0" style="color:var(--c-emerald)"><span>Diskon ({{ diskonPersen }}%)</span><span>-{{ formatRp(diskonNominal) }}</span></div>
                      <div class="sum-row"><span>PPN (11%)</span><span>{{ formatRp(tax) }}</span></div>
                      <div class="sum-row total"><span>TOTAL</span><span>{{ formatRp(grandTotal) }}</span></div>
                    </div>
                    <div class="form-group mt-4">
                      <label>Nama Klien / Perusahaan</label>
                      <input v-model="clientName" type="text" placeholder="PT Maju Jaya..." />
                    </div>
                    <div style="display:flex; gap:12px; margin-bottom:12px">
                      <div class="form-group" style="flex:1; margin-bottom:0">
                        <label>Metode Bayar</label>
                        <select v-model="paymentMethod" style="width:100%; background:var(--surface2); border:1px solid var(--border); color:var(--text); padding:10px 14px; border-radius:10px; font-size:14px; outline:none">
                          <option value="tunai">Tunai</option>
                          <option value="debit">Debit</option>
                          <option value="e-wallet">E-Wallet</option>
                          <option value="qris">QRIS</option>
                        </select>
                      </div>
                      <div class="form-group" style="flex:1; margin-bottom:0">
                        <label>Diskon (%)</label>
                        <input v-model.number="diskonPersen" type="number" min="0" max="100" placeholder="0" style="width:100%" />
                      </div>
                    </div>
                    <div v-if="paymentMethod === 'tunai'" class="form-group" style="margin-bottom:12px">
                      <label>Jumlah Bayar (Rp)</label>
                      <input v-model.number="jumlahBayar" type="number" min="0" placeholder="Masukkan nominal" />
                      <div v-if="jumlahBayar >= grandTotal && grandTotal > 0" style="font-size:12px; color:var(--c-emerald); margin-top:4px">
                        Kembalian: {{ formatRp(jumlahBayar - grandTotal) }}
                      </div>
                    </div>
                    
                    <button class="btn-primary full-w mt-2" @click="checkout" :disabled="!clientName.trim() || processing || (paymentMethod === 'tunai' && jumlahBayar < grandTotal)">
                      <component :is="processing ? icons.Loader : icons.CheckCircle" size="16" :class="{spin:processing}"/>
                      {{ processing ? 'Memproses...' : (paymentMethod === 'tunai' ? 'Checkout & Generate Kontrak' : 'Bayar via Midtrans') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TRANSAKSI -->
        <div v-if="currentPage === 'transaksi'" class="fade-in">
          <div class="toolbar">
            <span class="muted">{{ filteredTx.length }} transaksi ditemukan</span>
            <div class="custom-select">
              <div class="custom-select-overlay" v-if="txFilterOpen" @click="txFilterOpen = false"></div>
              <div class="select-trigger" @click="txFilterOpen = !txFilterOpen" :class="{ open: txFilterOpen }">
                <span>{{ getTxFilterLabel }}</span>
                <component :is="icons.ChevronDown" size="16" class="select-icon" />
              </div>
              <div class="select-dropdown fade-in" v-if="txFilterOpen">
                <div 
                  v-for="opt in txFilterOptions" 
                  :key="opt.value"
                  class="select-option"
                  :class="{ selected: txFilter === opt.value }"
                  @click="txFilter = opt.value; txFilterOpen = false"
                >
                  {{ opt.label }}
                  <component :is="icons.CheckCircle" size="14" v-if="txFilter === opt.value" class="check-icon" />
                </div>
              </div>
            </div>
          </div>
          <div class="card p-0">
            <div v-if="filteredTx.length === 0" class="empty-state text-center p-4 muted" style="padding:40px;">
              Tidak ada transaksi ditemukan.
            </div>
            <table class="data-table full" v-else>
              <thead><tr><th>ID</th><th>Klien</th><th>Total</th><th>Kontrak</th><th>Status</th><th>Tanggal</th></tr></thead>
              <tbody>
                <tr v-for="tx in filteredTx" :key="tx.id">
                  <td class="mono">#{{ tx.id }}</td>
                  <td><strong>{{ tx.client }}</strong></td>
                  <td class="mono bold">{{ formatRp(tx.total) }}</td>
                  <td>
                    <div v-if="tx.contract" class="flex items-center gap-2">
                      <button class="btn-link flex items-center gap-1" @click="previewContract(tx)" title="Lihat">
                        <component :is="icons.FileText" size="14"/> Lihat
                      </button>
                      <button class="btn-link flex items-center gap-1" @click="downloadContract(tx)" title="Unduh">
                        <component :is="icons.Download" size="14"/> Unduh
                      </button>
                    </div>
                    <span v-else class="muted">—</span>
                  </td>
                  <td><span class="badge" :class="tx.status">{{ tx.status }}</span></td>
                  <td class="muted">{{ tx.date }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- KONTRAK -->
        <div v-if="currentPage === 'kontrak'" class="fade-in">
          <div class="toolbar">
            <div class="muted">{{ filteredContracts.length }} dokumen terverifikasi</div>
          </div>
          <div class="card" style="padding-top:20px;">
            <div v-if="filteredContracts.length === 0" class="empty-state text-center p-4 muted" style="padding:40px;">
              Tidak ada dokumen kontrak ditemukan.
            </div>
            <div class="contract-list" v-else>
              <div class="contract-row" v-for="c in filteredContracts" :key="c.id">
                <div class="c-icon-wrap" @click="previewContract(c)" style="cursor:pointer"><component :is="icons.ShieldCheck" size="20" class="text-green" /></div>
                <div class="c-info" @click="previewContract(c)" style="cursor:pointer">
                  <strong>{{ c.title }}</strong>
                  <span class="muted">{{ c.client }}</span>
                </div>
                <div class="c-hash" @click="previewContract(c)" style="cursor:pointer">
                  <span class="muted">SHA-256</span>
                  <code>{{ c.hash }}</code>
                </div>
                <div class="c-meta" @click="previewContract(c)" style="cursor:pointer">
                  <span class="badge lunas">Terverifikasi</span>
                  <span class="muted">{{ c.date }}</span>
                </div>
                <div class="c-actions">
                   <button class="btn-icon" @click.stop="previewContract(c)" title="Lihat PDF"><component :is="icons.FileText" size="16"/></button>
                   <button class="btn-icon" @click.stop="downloadContract(c)" title="Unduh PDF"><component :is="icons.Download" size="16"/></button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- DETEKSI UANG PALSU -->
        <DeteksiUangPage v-if="currentPage === 'deteksi-uang'" />

        <!-- I/O SYSTEM -->
        <IOSystemPage v-if="currentPage === 'io-system'" />

        <!-- PAYMENT GATEWAY -->
        <MidtransPaymentPage v-if="currentPage === 'payment'" />

        <!-- LAPORAN -->
        <LaporanPage v-if="currentPage === 'laporan'" />

        <!-- ADMIN PANEL -->
        <AdminPanelPage v-if="currentPage === 'admin-panel'" />
      </div>
    </main>

    <!-- TOAST -->
    <div class="toast" :class="[{show: toast.show}, toast.type]">
      <component :is="toast.type==='error'?icons.AlertCircle:icons.CheckCircle" size="16"/>
      {{ toast.message }}
    </div>

    <!-- CONFIRM MODAL -->
    <div class="modal-overlay" v-if="confirmModal.show" @click.self="closeConfirm">
      <div class="modal fade-in" style="max-width:400px">
        <div class="modal-header">
          <h3>Konfirmasi</h3>
          <button class="btn-icon" style="margin:0" @click="closeConfirm" aria-label="Tutup"><component :is="icons.X" size="20"/></button>
        </div>
        <div class="modal-body" style="padding:24px 20px">
          <div style="display:flex; align-items:flex-start; gap:16px">
            <div style="background:rgba(244,63,94,0.1); color:var(--c-rose); padding:12px; border-radius:12px; display:flex">
              <component :is="icons.AlertTriangle" size="24"/>
            </div>
            <div>
              <strong style="display:block; font-size:16px; margin-bottom:8px; color:var(--text)">{{ confirmModal.title }}</strong>
              <p class="muted" style="font-size:14px; line-height:1.5">{{ confirmModal.message }}</p>
            </div>
          </div>
        </div>
        <div class="modal-footer" style="background:var(--surface2)">
          <button class="btn-secondary" @click="closeConfirm">Batal</button>
          <button class="btn-primary" style="background:var(--c-rose); box-shadow:0 4px 12px rgba(244,63,94,0.3)" @click="confirmAction">
            <component :is="icons.Trash2" size="14" style="margin-right:6px" /> Ya, Hapus
          </button>
        </div>
      </div>
    </div>

    <!-- MODALS -->
    <div class="modal-overlay" v-if="showAddProduct" @click.self="showAddProduct = false">
      <div class="modal fade-in">
        <div class="modal-header">
          <h3>Tambah Produk Baru</h3>
          <button class="btn-icon" style="margin:0" @click="showAddProduct = false" aria-label="Tutup"><component :is="icons.X" size="20"/></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Nama Produk</label>
            <input v-model="newProd.nama_produk" type="text" placeholder="Contoh: Laptop Gaming ASUS..." />
          </div>
          <div class="form-row">
            <div class="form-group"><label>Harga (Rp)</label><input v-model.number="newProd.harga" type="number" /></div>
            <div class="form-group"><label>Stok</label><input v-model.number="newProd.stok" type="number" /></div>
          </div>
          <div class="form-group">
            <label>Barcode</label>
            <div style="position:relative; display:flex; align-items:center;">
              <component :is="icons.ScanLine" size="16" style="position:absolute; left:12px; color:var(--muted)" />
              <input v-model="newProd.barcode" type="text" placeholder="Scan atau ketik barcode..." style="padding-left:36px; width:100%" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAddProduct = false">Batal</button>
          <button class="btn-primary" @click="submitProduct" :disabled="addingProduct">Simpan Produk</button>
        </div>
      </div>
    </div>

    <!-- EDIT PRODUCT MODAL -->
    <div class="modal-overlay" v-if="showEditProduct" @click.self="showEditProduct = false">
      <div class="modal fade-in">
        <div class="modal-header">
          <h3>Edit Produk</h3>
          <button class="btn-icon" style="margin:0" @click="showEditProduct = false" aria-label="Tutup"><component :is="icons.X" size="20"/></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Nama Produk</label>
            <input v-model="editProd.nama_produk" type="text" />
          </div>
          <div class="form-row">
            <div class="form-group"><label>Harga (Rp)</label><input v-model.number="editProd.harga" type="number" /></div>
            <div class="form-group"><label>Stok</label><input v-model.number="editProd.stok" type="number" /></div>
          </div>
          <div class="form-group">
            <label>Barcode</label>
            <div style="position:relative; display:flex; align-items:center;">
              <component :is="icons.ScanLine" size="16" style="position:absolute; left:12px; color:var(--muted)" />
              <input v-model="editProd.barcode" type="text" placeholder="Scan atau ketik barcode..." style="padding-left:36px; width:100%" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showEditProduct = false">Batal</button>
          <button class="btn-primary" @click="submitEditProduct">Simpan Perubahan</button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="showInvoice" @click.self="showInvoice = false">
      <div class="modal inv-modal fade-in">
        <div class="inv-head">
          <div><h2>INVOICE</h2><span class="mono muted">#{{ inv.id }}</span></div>
          <div class="inv-brand"><component :is="icons.ShieldCheck" size="16"/> SecureTransact</div>
        </div>
        <div class="inv-meta">
          <div><span class="muted">Kepada: </span><strong>{{ inv.client }}</strong></div>
          <div><span class="muted">Tanggal: </span>{{ inv.date }}</div>
        </div>
        <table class="data-table full inv-table">
          <thead>
            <tr>
              <th class="text-left">Produk</th>
              <th class="text-center">Qty</th>
              <th class="text-right">Harga</th>
              <th class="text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in inv.items" :key="it.nama_produk">
              <td class="text-left">{{ it.nama_produk }}</td>
              <td class="text-center">{{ it.qty }}</td>
              <td class="text-right mono">{{ formatRp(it.harga) }}</td>
              <td class="text-right mono bold" style="color:var(--text)">{{ formatRp(it.harga * it.qty) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="inv-totals">
          <div class="sum-row total"><span>TOTAL</span><span>{{ formatRp(inv.total) }}</span></div>
        </div>
        <div class="inv-hash">
          <component :is="icons.Lock" size="14"/>
          <span class="muted">Hash:</span><code>{{ inv.hash }}</code>
        </div>
        <div class="modal-footer">
          <button class="btn-primary" @click="currentPage='kontrak'; showInvoice=false">Lihat Kontrak</button>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, markRaw } from 'vue'
import {
  LayoutDashboard, Box, ShoppingCart, ArrowRightLeft, FileCheck, Search, Bell,
  ChevronLeft, ChevronRight, Server, ServerOff, TrendingUp, ArrowRight,
  CheckCircle, AlertOctagon, Plus, Loader, AlertTriangle, Trash2, Package,
  ShoppingBag, Minus, FileText, ShieldCheck, X, Code, AlertCircle, Lock, ChevronDown,
  ScanLine, Activity, CreditCard, LogOut, Users, BarChart3, Edit2, Tag, Download
} from 'lucide-vue-next'
import DeteksiUangPage from './components/DeteksiUangPage.vue'
import IOSystemPage from './components/IOSystemPage.vue'
import MidtransPaymentPage from './components/MidtransPaymentPage.vue'
import AdminPanelPage from './components/AdminPanelPage.vue'
import LaporanPage from './components/LaporanPage.vue'
import { inventoryApi, transactionApi, kontrakApi, paymentApi } from './services/api.js'

const icons = {
  LayoutDashboard: markRaw(LayoutDashboard), Box: markRaw(Box), ShoppingCart: markRaw(ShoppingCart),
  ArrowRightLeft: markRaw(ArrowRightLeft), FileCheck: markRaw(FileCheck), Search: markRaw(Search),
  Bell: markRaw(Bell), ChevronLeft: markRaw(ChevronLeft), ChevronRight: markRaw(ChevronRight),
  Server: markRaw(Server), ServerOff: markRaw(ServerOff), TrendingUp: markRaw(TrendingUp),
  ArrowRight: markRaw(ArrowRight), CheckCircle: markRaw(CheckCircle), AlertOctagon: markRaw(AlertOctagon),
  Plus: markRaw(Plus), Loader: markRaw(Loader), AlertTriangle: markRaw(AlertTriangle),
  Trash2: markRaw(Trash2), Package: markRaw(Package), ShoppingBag: markRaw(ShoppingBag),
  Minus: markRaw(Minus), FileText: markRaw(FileText), ShieldCheck: markRaw(ShieldCheck),
  X: markRaw(X), Code: markRaw(Code), AlertCircle: markRaw(AlertCircle), Lock: markRaw(Lock), ChevronDown: markRaw(ChevronDown),
  ScanLine: markRaw(ScanLine), Activity: markRaw(Activity), CreditCard: markRaw(CreditCard),
  Users: markRaw(Users), BarChart3: markRaw(BarChart3), Edit2: markRaw(Edit2), Tag: markRaw(Tag), Download: markRaw(Download)
}

const navItemsMain = [
  { id: 'dashboard', label: 'Dashboard', icon: icons.LayoutDashboard },
  { id: 'inventory', label: 'Inventaris', icon: icons.Box },
  { id: 'pos', label: 'Point of Sale', icon: icons.ShoppingCart },
  { id: 'transaksi', label: 'Transaksi', icon: icons.ArrowRightLeft },
  { id: 'kontrak', label: 'Kontrak Digital', icon: icons.FileCheck },
]

const navItemsAdvanced = [
  { id: 'deteksi-uang', label: 'Deteksi Uang', icon: icons.ScanLine },
  { id: 'io-system', label: 'I/O System', icon: icons.Activity },
  { id: 'payment', label: 'Monitoring Bayar', icon: icons.CreditCard },
  { id: 'laporan', label: 'Laporan', icon: icons.BarChart3 },
  { id: 'admin-panel', label: 'Admin Panel', icon: icons.Users },
]

const authState = reactive({
  isAuthenticated: false,
  user: null,
  token: null
})

const authView = ref('login')
const loginForm = reactive({ username: '', password: '', loading: false })
const registerForm = reactive({ username: '', email: '', password: '', role: 'kasir', loading: false })
const forgotForm = reactive({ username: '', email: '', new_password: '', loading: false })

const permittedNavMain = computed(() => {
  if (!authState.user) return []
  const role = authState.user.role
  return navItemsMain.filter(item => {
    if (role === 'admin') return true
    if (role === 'kasir') return ['pos', 'inventory', 'transaksi'].includes(item.id)
    if (role === 'manajer') return ['dashboard', 'transaksi', 'kontrak'].includes(item.id)
    return false
  })
})

const permittedNavAdvanced = computed(() => {
  if (!authState.user) return []
  const role = authState.user.role
  if (role === 'admin') return navItemsAdvanced
  if (role === 'manajer') return navItemsAdvanced.filter(i => ['payment','io-system','laporan'].includes(i.id))
  return []
})

const currentPage = ref('pos')
const sidebarCollapsed = ref(false)
const searchQuery = ref('')
const backendStatus = ref('offline')

const inventoryData = ref([])
const inventoryLoading = ref(false)
const inventoryError = ref(null)
const showAddProduct = ref(false)
const addingProduct = ref(false)
const newProd = reactive({ nama_produk: '', harga: 0, stok: 0, barcode: '' })
const showEditProduct = ref(false)
const editProd = reactive({ id: null, nama_produk: '', harga: 0, stok: 0, barcode: '' })
const paymentMethod = ref('tunai')
const diskonPersen = ref(0)
const jumlahBayar = ref(0)

const confirmModal = reactive({ show: false, title: '', message: '', onConfirm: null })

function showConfirm(title, message, onConfirm) {
  confirmModal.title = title
  confirmModal.message = message
  confirmModal.onConfirm = onConfirm
  confirmModal.show = true
}

function closeConfirm() {
  confirmModal.show = false
  confirmModal.onConfirm = null
}

function confirmAction() {
  if (confirmModal.onConfirm) confirmModal.onConfirm()
  closeConfirm()
}

const cart = ref([])
const clientName = ref('')
const processing = ref(false)
const scannedBarcode = ref('')
const barcodeInputRef = ref(null)

const txFilter = ref('all')
const txFilterOpen = ref(false)
const txFilterOptions = [
  { value: 'all', label: 'Semua Status' },
  { value: 'lunas', label: 'Lunas' },
  { value: 'pending', label: 'Pending' }
]
const getTxFilterLabel = computed(() => {
  const f = txFilterOptions.find(o => o.value === txFilter.value)
  return f ? f.label : 'Semua Status'
})

const transactions = ref([])
const contracts = ref([])

const toast = reactive({ show: false, message: '', type: 'success' })
const showInvoice = ref(false)
const inv = reactive({ id:'', client:'', date:'', items:[], subtotal:0, tax:0, total:0, hash:'' })

const pagesMeta = {
  dashboard: { title: 'Dashboard', subtitle: 'Ringkasan sistem & aktivitas terbaru' },
  inventory: { title: 'Inventaris', subtitle: 'Kelola produk & stok barang' },
  pos: { title: 'Point of Sale', subtitle: 'Proses transaksi & checkout' },
  transaksi: { title: 'Riwayat Transaksi', subtitle: 'Log semua transaksi tercatat' },
  kontrak: { title: 'Kontrak Digital', subtitle: 'Dokumen kontrak terverifikasi kriptografi' },
  'deteksi-uang': { title: 'Deteksi Uang Palsu', subtitle: 'Analisis keaslian uang via kamera — Computer Vision' },
  'io-system': { title: 'I/O System Transaction', subtitle: 'Monitor alur input/output data transaksi' },
  payment: { title: 'Payment Gateway', subtitle: 'Pembayaran multi-channel via Midtrans' },
  laporan: { title: 'Laporan & Export', subtitle: 'Ringkasan penjualan dan export data' },
  'admin-panel': { title: 'Admin Panel', subtitle: 'Manajemen user & role akses' },
}

const currentPageMeta = computed(() => pagesMeta[currentPage.value])

const dashboardStats = computed(() => [
  { label: 'Total Transaksi', value: transactions.value.length, icon: icons.ArrowRightLeft, trend: 12, color: 'var(--c-indigo)' },
  { label: 'Pendapatan', value: formatRp(transactions.value.reduce((a,b)=>a+b.total,0)), icon: icons.ShoppingCart, trend: 8, color: 'var(--c-emerald)' },
  { label: 'Produk Aktif', value: inventoryData.value.length, icon: icons.Package, trend: 3, color: 'var(--c-amber)' },
  { label: 'Kontrak Dibuat', value: contracts.value.length, icon: icons.ShieldCheck, trend: 5, color: 'var(--c-purple)' },
])

const systemStatus = ref([])
const secChecks = ref([])
const payConfig = ref({ is_production: false, client_key: '', snap_url: '' })

async function fetchSystemStatus() {
  try {
    const res = await fetch('http://localhost:8000/system-status')
    if (res.ok) {
      const data = await res.json()
      systemStatus.value = data.data.system_status
      secChecks.value = data.data.sec_checks
      backendStatus.value = 'online'
    } else {
      backendStatus.value = 'offline'
    }
  } catch(e) {
    console.error('Fetch system status error', e)
    backendStatus.value = 'offline'
  }
}

async function loadPayConfig() {
  try {
    const res = await paymentApi.getConfig()
    payConfig.value = res.data
    if(payConfig.value.snap_url && !document.querySelector(`script[src="${payConfig.value.snap_url}"]`)) {
      const s = document.createElement('script')
      s.src = payConfig.value.snap_url
      s.setAttribute('data-client-key', payConfig.value.client_key)
      document.head.appendChild(s)
    }
  } catch(e) { console.error('Failed to load pay config', e) }
}

const filteredInventory = computed(() => {
  if (!searchQuery.value) return inventoryData.value
  const q = searchQuery.value.toLowerCase()
  return inventoryData.value.filter(i => 
    i.nama_produk.toLowerCase().includes(q) || 
    (i.barcode && i.barcode.toLowerCase().includes(q))
  )
})

const filteredTx = computed(() => {
  let result = transactions.value
  if (txFilter.value !== 'all') {
    result = result.filter(t => t.status === txFilter.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.id.toLowerCase().includes(q) || 
      t.client.toLowerCase().includes(q) || 
      String(t.total).includes(q)
    )
  }
  return result
})

const filteredContracts = computed(() => {
  if (!searchQuery.value) return contracts.value
  const q = searchQuery.value.toLowerCase()
  return contracts.value.filter(c => 
    c.id.toLowerCase().includes(q) || 
    c.client.toLowerCase().includes(q) || 
    c.hash.toLowerCase().includes(q)
  )
})

const subtotal = computed(() => cart.value.reduce((s,i) => s + i.harga * i.qty, 0))
const diskonNominal = computed(() => Math.round(subtotal.value * diskonPersen.value / 100))
const setelahDiskon = computed(() => subtotal.value - diskonNominal.value)
const tax = computed(() => Math.round(setelahDiskon.value * 0.11))
const grandTotal = computed(() => setelahDiskon.value + tax.value)

function formatRp(v) { return typeof v === 'number' ? 'Rp ' + v.toLocaleString('id-ID') : v }

function showToast(msg, type='success') {
  toast.message = msg; toast.type = type; toast.show = true
  setTimeout(() => toast.show = false, 3000)
}

async function fetchInventory() {
  inventoryLoading.value = true; inventoryError.value = null
  try {
    const res = await inventoryApi.getAll()
    inventoryData.value = res.data || []
    backendStatus.value = 'online'
  } catch (err) {
    inventoryError.value = err.message || 'Tidak dapat terhubung ke backend.'
    inventoryData.value = []
  } finally { inventoryLoading.value = false }
}

async function submitProduct() {
  if (!newProd.nama_produk.trim() || newProd.harga <= 0) { showToast('Isi semua field yang valid!', 'error'); return }
  addingProduct.value = true;
  try {
    const res = await inventoryApi.create(newProd)
    inventoryData.value.push(res.data)
    showToast(`Produk "${newProd.nama_produk}" ditambah.`);
    showAddProduct.value = false;
    newProd.nama_produk = ''; newProd.harga = 0; newProd.stok = 0; newProd.barcode = '';
  } catch (err) {
    showToast(err.message, 'error')
  } finally {
    addingProduct.value = false
  }
}

function deleteProduct(id) { 
  showConfirm(
    'Hapus Produk',
    'Apakah Anda yakin ingin menghapus produk ini dari inventaris? Tindakan ini tidak dapat dibatalkan.',
    async () => {
      try {
        await inventoryApi.delete(id)
        inventoryData.value = inventoryData.value.filter(i => i.id !== id)
        showToast('Produk dihapus!', 'success')
      } catch (err) {
        showToast(err.message, 'error')
      }
    }
  )
}
function openEditProduct(item) {
  Object.assign(editProd, { id: item.id, nama_produk: item.nama_produk, harga: item.harga, stok: item.stok, barcode: item.barcode || '' })
  showEditProduct.value = true
}
async function submitEditProduct() {
  try {
    const res = await inventoryApi.update(editProd.id, { nama_produk: editProd.nama_produk, harga: editProd.harga, stok: editProd.stok, barcode: editProd.barcode })
    const idx = inventoryData.value.findIndex(i => i.id === editProd.id)
    if (idx >= 0) inventoryData.value[idx] = res.data
    showEditProduct.value = false
    showToast('Produk berhasil diperbarui!')
  } catch (err) { showToast(err.message, 'error') }
}
function handleBarcodeScan() {
  if (!scannedBarcode.value.trim()) return
  const code = scannedBarcode.value.trim()
  const item = inventoryData.value.find(i => i.barcode === code)
  if (item) {
    addToCart(item)
    showToast(`Produk ditambahkan via Barcode`, 'success')
  } else {
    showToast(`Barcode ${code} tidak dikenali!`, 'error')
  }
  scannedBarcode.value = ''
  if (barcodeInputRef.value) barcodeInputRef.value.focus()
}
function addToCart(item) {
  if (item.stok === 0) { showToast('Stok habis!', 'error'); return }
  const ex = cart.value.find(c => c.id === item.id)
  if (ex) { if (ex.qty >= item.stok) return; ex.qty++ } else { cart.value.push({ ...item, qty: 1 }) }
  if (currentPage.value !== 'pos') showToast(`${item.nama_produk} → keranjang`)
}
function incQty(i) { cart.value[i].qty++ }
function decQty(i) { if (cart.value[i].qty === 1) cart.value.splice(i,1); else cart.value[i].qty-- }
async function fetchTransactions() {
  try {
    const res = await transactionApi.getAll()
    transactions.value = res.data.map(t => ({
      id: t.kode,
      client: t.nama_klien,
      items: t.items.length + ' jenis',
      total: t.grand_total,
      status: t.status,
      contract: true,
      date: new Date(t.created_at).toLocaleDateString('id-ID', {day:'2-digit',month:'short',year:'numeric'}),
      _rawId: t.id
    }))
  } catch (e) { console.error('Fetch tx error', e) }
}

async function fetchContracts() {
  try {
    const res = await kontrakApi.getAll()
    contracts.value = res.data.map(c => ({
      id: c.kode,
      title: `Kontrak Pembelian #${c.kode}`,
      client: c.nama_klien,
      hash: c.hash_doc && c.hash_doc !== '__pending__' ? c.hash_doc.substring(0, 16) + '...' : 'pending...',
      date: new Date(c.created_at).toLocaleDateString('id-ID', {day:'2-digit',month:'short',year:'numeric'}),
      _rawId: c.id
    }))
  } catch (e) { console.error('Fetch kontrak error', e) }
}

async function finalizeCheckout(tx) {
  await fetchTransactions()
  await fetchContracts()
  await fetchInventory()

  const d = new Date(tx.created_at).toLocaleDateString('id-ID', {day:'2-digit',month:'short',year:'numeric'})
  Object.assign(inv, { id:tx.kode, client:tx.nama_klien, date:d, items:[...cart.value], subtotal:tx.total, tax:tx.ppn, total:tx.grand_total, hash:'(lihat di kontrak)' })
  
  cart.value = []; clientName.value = ''; showInvoice.value = true
  diskonPersen.value = 0; paymentMethod.value = 'tunai'; jumlahBayar.value = 0
  showToast(`Transaksi ${tx.kode} berhasil!`, 'success')
  processing.value = false
}

async function checkout() {
  if (!clientName.value.trim()) { showToast('Nama Klien belum diisi!', 'error'); return }
  if (paymentMethod.value === 'tunai' && jumlahBayar.value < grandTotal.value) {
    showToast('Jumlah bayar kurang dari total!', 'error'); return
  }
  processing.value = true;
  try {
    const payload = {
      nama_klien: clientName.value,
      metode_pembayaran: paymentMethod.value,
      jumlah_bayar: paymentMethod.value === 'tunai' ? jumlahBayar.value : grandTotal.value,
      diskon_persen: diskonPersen.value,
      items: cart.value.map(i => ({ produk_id: i.id, qty: i.qty }))
    }
    const res = await transactionApi.create(payload)
    const tx = res.data
    
    if (paymentMethod.value !== 'tunai') {
      try {
        const snapRes = await paymentApi.createSnapToken(tx.id)
        
        if (snapRes.data.is_demo) {
          // Jika mode demo (karena keys belum diisi di .env), tampilkan prompt simulasi
          if (confirm("MODE DEMO: Midtrans belum dikonfigurasi di .env.\n\nSimulasikan pembayaran BERHASIL untuk transaksi ini?")) {
            await finalizeCheckout(tx)
          } else {
            processing.value = false
            showToast('Pembayaran dibatalkan (Mode Demo)', 'error')
          }
          return
        }

        if (window.snap) {
          window.snap.pay(snapRes.data.snap_token, {
            onSuccess: async () => await finalizeCheckout(tx),
            onPending: async () => { showToast('Pembayaran pending.'); await finalizeCheckout(tx) },
            onError: () => { showToast('Pembayaran gagal!', 'error'); processing.value = false },
            onClose: async () => { showToast('Popup ditutup.'); await finalizeCheckout(tx) }
          })
          return 
        } else if (snapRes.data.redirect_url) {
          window.open(snapRes.data.redirect_url, '_blank')
        }
      } catch (err) {
        showToast('Gagal memanggil Midtrans: ' + err.message, 'error')
      }
    }
    
    await finalizeCheckout(tx)
  } catch (err) {
    showToast(err.message, 'error')
    processing.value = false
  }
}

function previewContract(item) {
  let kontrakId = item._rawId;
  if (item.id && item.id.startsWith('TRX')) {
    showToast('Membuka dokumen...', 'success');
    fetch(`http://localhost:8000/transaction/${item._rawId}/receipt`, {
      headers: { 'Authorization': `Bearer ${authState.token}` }
    }).then(r => r.json()).then(res => {
      if (res.data && res.data.kontrak) {
        window.open(`http://localhost:8000/kontrak/${res.data.kontrak.id}/pdf?token=${authState.token}`, '_blank');
      } else {
        showToast('Kontrak belum tersedia', 'error');
      }
    }).catch(() => showToast('Gagal memuat kontrak', 'error'));
    return;
  }
  window.open(`http://localhost:8000/kontrak/${kontrakId}/pdf?token=${authState.token}`, '_blank');
}

function downloadContract(item) {
  let kontrakId = item._rawId;
  if (item.id && item.id.startsWith('TRX')) {
    showToast('Mengunduh dokumen...', 'success');
    fetch(`http://localhost:8000/transaction/${item._rawId}/receipt`, {
      headers: { 'Authorization': `Bearer ${authState.token}` }
    }).then(r => r.json()).then(res => {
      if (res.data && res.data.kontrak) {
        window.open(`http://localhost:8000/kontrak/${res.data.kontrak.id}/pdf?download=1&token=${authState.token}`, '_blank');
      } else {
        showToast('Kontrak belum tersedia', 'error');
      }
    }).catch(() => showToast('Gagal memuat kontrak', 'error'));
    return;
  }
  window.open(`http://localhost:8000/kontrak/${kontrakId}/pdf?download=1&token=${authState.token}`, '_blank');
}

async function handleLogin() {
  if(!loginForm.username || !loginForm.password) { showToast('Isi username dan password', 'error'); return }
  loginForm.loading = true
  try {
    const res = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginForm)
    })
    const data = await res.json()
    if(!res.ok) throw new Error(data.detail || 'Login gagal')
    
    authState.token = data.access_token
    authState.user = data.user
    authState.isAuthenticated = true
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_info', JSON.stringify(data.user))
    
    showToast(`Selamat datang, ${data.user.username}!`, 'success')
    
    // Set default page based on role
    if(data.user.role === 'admin' || data.user.role === 'manajer') currentPage.value = 'dashboard'
    else currentPage.value = 'pos'
    
    fetchInventory()
    fetchTransactions()
    fetchContracts()
    fetchSystemStatus()
  } catch (err) {
    showToast(err.message, 'error')
  } finally {
    loginForm.loading = false
  }
}

async function handleRegister() {
  if(!registerForm.username || !registerForm.password || !registerForm.email) { showToast('Lengkapi form pendaftaran!', 'error'); return }
  registerForm.loading = true
  try {
    const res = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(registerForm)
    })
    const data = await res.json()
    if(!res.ok) throw new Error(data.detail || 'Gagal mendaftar')
    showToast('Registrasi berhasil! Silakan login.', 'success')
    authView.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = registerForm.password
  } catch (err) {
    showToast(err.message, 'error')
  } finally {
    registerForm.loading = false
  }
}

async function handleForgot() {
  if(!forgotForm.username || !forgotForm.email || !forgotForm.new_password) { showToast('Lengkapi semua data!', 'error'); return }
  forgotForm.loading = true
  try {
    const res = await fetch('http://localhost:8000/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(forgotForm)
    })
    const data = await res.json()
    if(!res.ok) throw new Error(data.detail || 'Gagal mereset password')
    showToast(data.message, 'success')
    authView.value = 'login'
  } catch (err) {
    showToast(err.message, 'error')
  } finally {
    forgotForm.loading = false
  }
}

function handleLogout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_info')
  authState.isAuthenticated = false
  authState.user = null
  authState.token = null
  authView.value = 'login'
  showToast('Berhasil logout', 'success')
}

onMounted(() => {
  const token = localStorage.getItem('access_token')
  const userStr = localStorage.getItem('user_info')
  if (token && userStr) {
    try {
      authState.user = JSON.parse(userStr)
      authState.token = token
      authState.isAuthenticated = true
      
      if(authState.user.role === 'admin' || authState.user.role === 'manajer') {
        if(currentPage.value === 'pos' && authState.user.role === 'manajer') currentPage.value = 'dashboard'
      } else {
        currentPage.value = 'pos'
      }
      
      fetchInventory()
      fetchTransactions()
      fetchContracts()
      fetchSystemStatus()
      loadPayConfig()
    } catch {
      handleLogout()
    }
  }
})
</script>

<style>
/* Modern Reset & Base Variables */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#09090b; --surface:#121214; --surface2:#18181b; --surface3:#27272a;
  --border:#27272a; --border-hover:#3f3f46;
  --text:#f4f4f5; --muted:#a1a1aa;
  --c-indigo:#6366f1; --c-emerald:#10b981; --c-rose:#f43f5e; --c-amber:#f59e0b; --c-purple:#8b5cf6;
  --sw:260px; --r-card:16px; --r-btn:10px;
}
html,body{width:100%;height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-weight:400;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;line-height:1.5}
#app{display:flex;width:100%;height:100%;overflow:hidden;position:relative}

/* Custom Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* Ambient Glow */
.app-background {
  position:absolute; inset:0; z-index:0; pointer-events:none;
  background: radial-gradient(circle at 15% 50%, rgba(99,102,241,0.06), transparent 25%),
              radial-gradient(circle at 85% 30%, rgba(16,185,129,0.04), transparent 25%);
}

/* Common Classes */
.flex{display:flex} .items-center{align-items:center} .gap-1{gap:4px} .gap-2{gap:8px}
.mt-2{margin-top:8px} .mt-4{margin-top:16px} .h-full{height:100%} .p-0{padding:0!important} .p-4{padding:16px!important}
.border-b{border-bottom:1px solid var(--border)}
.text-green{color:var(--c-emerald)} .text-warn{color:var(--c-amber)} .text-danger{color:var(--c-rose)}
h1,h2,h3{font-family:'Outfit',sans-serif;letter-spacing:-0.02em}

/* SIDEBAR */
.sidebar{width:var(--sw);background:rgba(18,18,20,0.6);backdrop-filter:blur(12px);border-right:1px solid var(--border);display:flex;flex-direction:column;transition:width 0.3s cubic-bezier(0.4, 0, 0.2, 1);z-index:10;flex-shrink:0}
.sidebar.collapsed{width:76px}
.sidebar-header{padding:24px 20px;display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:12px;overflow:hidden;white-space:nowrap}
.logo-icon{color:var(--bg);background:var(--text);padding:6px;border-radius:10px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 16px rgba(255,255,255,0.1)}
.logo-text{font-family:'Outfit',sans-serif;font-weight:700;font-size:18px}
.collapse-btn{background:var(--surface3);border:1px solid var(--border);color:var(--muted);width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:0.2s}
.collapse-btn:hover{color:var(--text);border-color:var(--text)}

.sidebar-nav{flex:1;padding:12px 16px;overflow-y:auto}
.nav-group{margin-bottom:16px}
.nav-label{font-size:11px;font-weight:600;letter-spacing:0.08em;color:var(--muted);text-transform:uppercase;padding:0 12px 12px;display:block}
.nav-item{width:100%;display:flex;align-items:center;gap:12px;padding:12px;margin-bottom:4px;background:transparent;border:none;border-radius:12px;color:var(--muted);cursor:pointer;transition:all 0.2s;white-space:nowrap;overflow:hidden;font-family:'Inter',sans-serif;font-size:14px;font-weight:500;text-align:left}
.nav-item:hover{background:var(--surface2);color:var(--text)}
.nav-item.active{background:rgba(99,102,241,0.1);color:var(--c-indigo);font-weight:600}
.nav-icon{display:flex;align-items:center;justify-content:center;flex-shrink:0}

.sidebar-footer{padding:20px;border-top:1px solid var(--border);background:rgba(18,18,20,0.8)}
.user-info{display:flex;align-items:center;gap:12px;margin-bottom:12px}
.user-avatar{width:36px;height:36px;border-radius:12px;background:linear-gradient(135deg,var(--c-indigo),var(--c-purple));display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;font-family:'Outfit',sans-serif;}
.user-details{display:flex;flex-direction:column}
.user-name{font-size:14px;font-weight:600}
.user-role{font-size:12px;color:var(--muted)}
.status-dot{display:flex;align-items:center;gap:6px;font-size:12px;font-weight:500}
.status-dot.online{color:var(--c-emerald)}
.status-dot.offline{color:var(--c-amber)}

/* MAIN CONTENT */
.main-content{flex:1;display:flex;flex-direction:column;z-index:1;min-width:0;height:100%;background:var(--bg)}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:24px;background:rgba(9,9,11,0.7);backdrop-filter:blur(16px);border-bottom:1px solid var(--border);z-index:20}
.page-title{font-size:24px;font-weight:700}
.page-subtitle{font-size:14px;color:var(--muted);margin-top:2px;display:block}
.topbar-right{display:flex;align-items:center;gap:16px}
.search-bar{position:relative;display:flex;align-items:center}
.search-icon{position:absolute;left:12px;color:var(--muted)}
.search-bar input{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:10px 16px 10px 36px;border-radius:var(--r-btn);font-size:14px;width:260px;font-family:'Inter',sans-serif;outline:none;transition:all 0.2s cubic-bezier(0.4, 0, 0.2, 1);box-shadow:inset 0 2px 4px rgba(0,0,0,0.2)}
.search-bar input:focus{border-color:var(--c-indigo);box-shadow:0 0 0 3px rgba(99,102,241,0.15);width:300px}
.notif-btn{background:var(--surface2);border:1px solid var(--border);color:var(--text);width:40px;height:40px;border-radius:var(--r-btn);display:flex;align-items:center;justify-content:center;cursor:pointer;position:relative;transition:0.2s}
.notif-btn:hover{background:var(--surface3);border-color:var(--border-hover)}
.notif-dot{width:8px;height:8px;background:var(--c-rose);border-radius:50%;position:absolute;top:10px;right:10px;box-shadow:0 0 8px rgba(244,63,94,0.6)}

.page-content{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column}
/* Full size flex wrapper for specific pages */
.fade-in.h-full-flex{flex:1;display:flex;flex-direction:column;min-height:0}

/* CARDS */
.card{background:rgba(18,18,20,0.6);border:1px solid var(--border);border-radius:var(--r-card);padding:24px;margin-bottom:20px;box-shadow:0 8px 32px rgba(0,0,0,0.3);backdrop-filter:blur(12px)}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.card-header h3{font-size:18px;font-weight:600;display:flex;align-items:center;gap:8px}

/* DASHBOARD STATS */
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:24px}
.stat-card{background:linear-gradient(145deg, rgba(24,24,27,0.8), rgba(18,18,20,0.9));border:1px solid var(--border);border-radius:var(--r-card);padding:20px;display:flex;flex-direction:column;gap:16px;position:relative;overflow:hidden;transition:transform 0.2s}
.stat-card:hover{transform:translateY(-2px);border-color:var(--border-hover)}
.stat-card::after{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--c);box-shadow:0 0 12px var(--c)}
.stat-top{display:flex;justify-content:space-between;align-items:flex-start;width:100%}
.stat-icon{color:var(--c);background:color-mix(in srgb, var(--c) 15%, transparent);padding:12px;border-radius:12px;display:inline-flex}
.stat-body{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px}
.stat-value{font-family:'Outfit',sans-serif;font-size:24px;font-weight:700;line-height:1.2;word-break:break-word}
.stat-label{font-size:13px;color:var(--muted);font-weight:500}
.stat-trend{display:flex;align-items:center;gap:4px;font-size:12px;font-weight:600;padding:4px 8px;border-radius:8px;background:rgba(16,185,129,0.1);color:var(--c-emerald)}

.dashboard-grid{display:grid;grid-template-columns:2fr 1fr;gap:20px}

/* TABLES & BADGES */
.data-table{width:100%;border-collapse:collapse;font-size:14px}
.data-table th{text-align:left;padding:16px;color:var(--muted);font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;border-bottom:1px solid var(--border)}
.data-table td{padding:16px;border-bottom:1px solid rgba(39,39,42,0.6);vertical-align:middle}
.data-table tr:hover td{background:rgba(255,255,255,0.02)}
.badge{display:inline-flex;align-items:center;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;text-transform:capitalize}
.badge.lunas{background:rgba(16,185,129,0.15);color:var(--c-emerald);border:1px solid rgba(16,185,129,0.2)}
.badge.pending{background:rgba(245,158,11,0.15);color:var(--c-amber);border:1px solid rgba(245,158,11,0.2)}
.badge.warn{background:rgba(244,63,94,0.15);color:var(--c-rose);border:1px solid rgba(244,63,94,0.2)}

/* UTILS */
.mono{font-family:'JetBrains Mono',monospace;font-size:13px}
.muted{color:var(--muted)} .bold{font-weight:600}
.text-left{text-align:left!important} .text-center{text-align:center!important} .text-right{text-align:right!important}
.spin{animation:spin 1s linear infinite} @keyframes spin{to{transform:rotate(360deg)}}
.fade-in{animation:fi 0.3s cubic-bezier(0.4, 0, 0.2, 1)}
@keyframes fi{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

/* STATES */
.loading-state, .error-state{display:flex;align-items:center;gap:12px;padding:16px 24px;border-radius:12px;margin-bottom:20px;font-size:14px;border:1px solid var(--border);background:rgba(18,18,20,0.6);backdrop-filter:blur(8px)}
.error-state{background:rgba(245,158,11,0.05);border-color:rgba(245,158,11,0.2)}
.error-state .btn-secondary{margin-left:auto;border-color:rgba(245,158,11,0.3);color:var(--text);padding:8px 16px;font-size:13px}
.error-state .btn-secondary:hover{background:rgba(245,158,11,0.15);border-color:rgba(245,158,11,0.5)}

/* SYSTEM STATUS */
.system-status, .sec-checks{display:flex;flex-direction:column;gap:16px}
.status-item, .check-item{display:flex;align-items:center;font-size:14px;background:var(--surface2);padding:12px 16px;border-radius:12px}
.status-name{display:flex;align-items:center;gap:8px;width:160px;font-weight:500}
.dot{width:8px;height:8px;border-radius:50%}
.dot.online{background:var(--c-emerald);box-shadow:0 0 8px var(--c-emerald)}
.dot.offline{background:var(--c-rose)}
.bar-wrap{flex:1;height:6px;background:var(--surface3);border-radius:6px;overflow:hidden;margin:0 16px}
.bar{height:100%;border-radius:6px}
.bar.online{background:var(--c-emerald)} .bar.offline{background:var(--c-rose)}
.chk{display:flex;align-items:center;margin-right:12px}
.chk.ok{color:var(--c-emerald)} .chk.warn{color:var(--c-amber)}

/* BUTTONS & FORMS */
.toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.btn-primary{background:var(--text);color:var(--bg);border:none;padding:10px 20px;border-radius:var(--r-btn);font-size:14px;font-weight:600;display:inline-flex;align-items:center;gap:8px;cursor:pointer;transition:transform 0.1s, opacity 0.2s;box-shadow:0 4px 12px rgba(255,255,255,0.1)}
.btn-primary:hover{opacity:0.9;transform:translateY(-1px)}
.btn-primary:active{transform:translateY(1px)}
.btn-primary:disabled{opacity:0.5;cursor:not-allowed}
.btn-primary.full-w{width:100%;justify-content:center;padding:14px}
.btn-secondary{background:transparent;color:var(--text);border:1px solid var(--border);padding:10px 20px;border-radius:var(--r-btn);font-size:14px;font-weight:500;cursor:pointer;transition:0.2s}
.btn-secondary:hover{background:var(--surface2);border-color:var(--border-hover)}
.btn-link{background:none;border:none;color:var(--muted);font-size:14px;font-weight:500;cursor:pointer;transition:0.2s;display:flex;align-items:center;gap:4px}
.btn-link:hover{color:var(--text)}
.btn-link.danger:hover{color:var(--c-rose)}
.btn-icon{background:var(--surface3);border:none;color:var(--text);width:32px;height:32px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;transition:0.2s;margin-right:8px}
.btn-icon:hover{background:var(--border-hover)}
.btn-icon.danger{color:var(--c-rose)} .btn-icon.danger:hover{background:rgba(244,63,94,0.15)}

.form-group{display:flex;flex-direction:column;gap:8px;margin-bottom:16px}
.form-group label{font-size:13px;color:var(--muted);font-weight:500}
.form-group input{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:12px 16px;border-radius:var(--r-btn);font-size:14px;outline:none;transition:0.2s;box-shadow:inset 0 2px 4px rgba(0,0,0,0.1)}
.form-group input:focus{border-color:var(--c-indigo);box-shadow:0 0 0 3px rgba(99,102,241,0.15)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
input[type=number]::-webkit-outer-spin-button,
input[type=number]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
  appearance: textfield;
}

/* CUSTOM SELECT */
.custom-select { position: relative; }
.custom-select-overlay { position: fixed; inset: 0; z-index: 40; }
.select-trigger { position: relative; z-index: 41; display: flex; align-items: center; justify-content: space-between; gap: 12px; min-width: 170px; padding: 10px 14px; background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; font-size: 13px; font-weight: 500; color: var(--text); cursor: pointer; transition: 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.select-trigger:hover { border-color: var(--border-hover); background: var(--surface3); }
.select-trigger.open { border-color: var(--c-indigo); box-shadow: 0 0 0 3px rgba(99,102,241,0.15); background: var(--surface3); }
.select-icon { color: var(--muted); transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.select-trigger.open .select-icon { transform: rotate(180deg); }
.select-dropdown { position: absolute; z-index: 41; top: calc(100% + 8px); right: 0; min-width: 100%; background: var(--surface); border: 1px solid var(--border-hover); border-radius: 12px; padding: 6px; box-shadow: 0 16px 32px rgba(0,0,0,0.4); display: flex; flex-direction: column; gap: 4px; }
.select-option { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border-radius: 8px; font-size: 13px; font-weight: 500; color: var(--muted); cursor: pointer; transition: 0.2s; }
.select-option:hover { background: var(--surface2); color: var(--text); }
.select-option.selected { background: rgba(99,102,241,0.1); color: var(--text); font-weight: 600; }
.select-option .check-icon { color: var(--c-indigo); }

/* POS LAYOUT */
.pos-layout{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;flex:1;min-height:0}
.pos-catalog, .pos-cart{height:100%; display:flex; flex-direction:column}
.pos-catalog .card { display: flex; flex-direction: column; height: 100%; }
.pos-cart .card { display: flex; flex-direction: column; height: 100%; }
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:16px; overflow-y:auto; padding-right:8px; flex:1; align-content: start; margin-top:16px}
.product-card{background:var(--surface2);border:1px solid var(--border);border-radius:14px;padding:20px 16px;cursor:pointer;transition:0.2s;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:space-between;gap:12px}
.product-card:hover{border-color:var(--c-indigo);background:rgba(99,102,241,0.05);transform:translateY(-2px)}
.product-card.out-of-stock{opacity:0.4;pointer-events:none}
.product-icon{color:var(--muted);background:var(--surface3);padding:12px;border-radius:12px}
.product-name{font-size:14px;font-weight:500;line-height:1.4}
.product-price{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--c-indigo);font-weight:600}

/* AUTHENTICATION UI */
.auth-container { position:fixed; inset:0; z-index:999; display:flex; align-items:center; justify-content:center; background:var(--bg); }
.auth-card { width:100%; max-width:400px; background:rgba(18,18,20,0.8); backdrop-filter:blur(16px); border:1px solid var(--border); border-radius:24px; padding:32px; box-shadow:0 16px 64px rgba(0,0,0,0.5); }
.auth-header h2 { font-size:24px; font-weight:700; margin-bottom:8px; }
.auth-form { display:flex; flex-direction:column; gap:4px; }
.text-indigo { color:var(--c-indigo); }
.cart-content-wrapper { display:flex; flex-direction:column; flex:1; overflow:hidden; }
.cart-items-wrapper { flex:1; overflow-y:auto; padding-right:8px; margin-bottom:16px }
.cart-item{display:flex;align-items:center;justify-content:space-between;padding:16px 0;border-bottom:1px solid var(--border)}
.cart-info{display:flex;flex-direction:column;gap:4px;flex:1;padding-right:16px}
.qty-ctrl{display:flex;align-items:center;gap:12px;background:var(--surface2);padding:4px;border-radius:8px;border:1px solid var(--border)}
.qty-ctrl button{background:transparent;border:none;color:var(--text);width:24px;height:24px;display:flex;align-items:center;justify-content:center;cursor:pointer;border-radius:4px}
.qty-ctrl button:hover{background:var(--surface3)}
.cart-footer { margin-top: auto; padding-top: 16px; border-top: 1px solid var(--border); }
.cart-summary{background:var(--surface2);padding:20px;border-radius:12px}
.sum-row{display:flex;justify-content:space-between;margin-bottom:12px;font-size:14px;color:var(--muted)}
.sum-row.total{margin-bottom:0;padding-top:12px;border-top:1px solid var(--border);color:var(--text);font-size:18px;font-weight:700;font-family:'Outfit'}
.empty-cart{display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:60px 20px; color:var(--muted); border:1px dashed var(--border); border-radius:12px; margin-top:20px; height: 100%;}

/* CONTRACTS */
.contract-list{display:flex;flex-direction:column;gap:12px}
.contract-row{display:flex;align-items:center;padding:16px 20px;background:var(--surface2);border:1px solid var(--border);border-radius:12px;cursor:pointer;transition:all 0.2s}
.contract-row:hover{border-color:var(--c-indigo);background:rgba(99,102,241,0.05)}
.c-icon-wrap{background:rgba(16,185,129,0.1);padding:10px;border-radius:10px;margin-right:16px}
.c-info{flex:1;display:flex;flex-direction:column;gap:4px;font-size:14px}
.c-hash{display:flex;flex-direction:column;align-items:flex-end;font-size:12px;gap:4px;margin-right:24px}
.c-hash code{color:var(--c-emerald);background:rgba(16,185,129,0.1);padding:2px 6px;border-radius:4px}
.c-meta{display:flex;flex-direction:column;align-items:flex-end;gap:6px;font-size:13px}
.c-actions{display:flex;align-items:center;gap:8px;margin-left:16px}

/* MODALS */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;z-index:1000}
.modal{background:var(--surface);border:1px solid var(--border);border-radius:20px;width:480px;box-shadow:0 24px 48px rgba(0,0,0,0.5)}
.modal-header{padding:24px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.modal-body{padding:24px}
.modal-footer{padding:20px 24px;border-top:1px solid var(--border);display:flex;justify-content:flex-end;gap:12px;background:var(--surface2);border-radius:0 0 20px 20px}

/* INVOICE MODAL */
.inv-modal{width:600px}
.inv-head{padding:32px 32px 24px;display:flex;justify-content:space-between}
.inv-head h2{font-size:28px;letter-spacing:4px;color:var(--text)}
.inv-brand{font-family:'Outfit';font-weight:600;display:flex;align-items:center;gap:6px}
.inv-meta{padding:0 32px 24px;display:flex;justify-content:space-between;font-size:14px}
.modal .data-table.inv-table{margin-bottom:16px;border-top:1px solid var(--border)}
.inv-table th:first-child, .inv-table td:first-child{padding-left:32px}
.inv-table th:last-child, .inv-table td:last-child{padding-right:32px}
.inv-totals{padding:0 32px 24px;display:flex;justify-content:flex-end}
.inv-totals .sum-row{min-width:320px;justify-content:space-between;gap:20px}
.inv-hash{margin:0 32px 32px;background:var(--surface2);padding:16px;border-radius:12px;display:flex;align-items:center;gap:12px;font-size:13px}
.inv-hash code{color:var(--c-emerald);font-family:'JetBrains Mono'}

/* TOAST */
.toast{position:fixed;bottom:32px;right:32px;background:var(--surface);border:1px solid var(--border);padding:16px 24px;border-radius:12px;font-size:14px;font-weight:500;display:flex;align-items:center;gap:12px;z-index:2000;transform:translateY(100px);opacity:0;transition:all 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.55);box-shadow:0 12px 24px rgba(0,0,0,0.3)}
.toast.show{transform:translateY(0);opacity:1}
.toast.error{border-color:var(--c-rose);color:var(--c-rose)}

/* QRIS DISPLAY */
.qris-container{display:flex;justify-content:center;margin:16px 0}
.qris-box{background:var(--surface2);border:1px solid var(--border);border-radius:16px;padding:16px;display:flex;flex-direction:column;align-items:center;gap:12px;width:100%;max-width:240px;box-shadow:0 8px 24px rgba(0,0,0,0.2)}
.qris-header{text-align:center;display:flex;flex-direction:column;gap:4px}
.qris-qr{background:#fff;padding:8px;border-radius:12px;box-shadow:inset 0 2px 4px rgba(0,0,0,0.1)}
.qris-qr img{display:block;width:150px;height:150px;mix-blend-mode:multiply}
.qris-footer{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:12px}

/* RESPONSIVENESS */
@media(max-width:1024px), (max-height: 700px){
  html,body{height:auto;min-height:100vh;overflow-y:auto}
  #app{height:auto;min-height:100vh;overflow-y:visible}
  .main-content{min-height:100vh;overflow:visible}
  .page-content{overflow:visible}
  .stats-grid{grid-template-columns:repeat(2,1fr)}
  .dashboard-grid{grid-template-columns:1fr}
  .pos-layout{grid-template-columns:1fr;height:auto;overflow:visible}
  .pos-cart{margin-top:24px}
}
@media(max-width:768px){
  #app{flex-direction:column}
  .sidebar{width:100%;height:auto;border-right:none;border-bottom:1px solid var(--border)}
  .sidebar.collapsed{height:72px;overflow:hidden}
  .topbar{flex-direction:column;gap:16px;align-items:flex-start}
  .search-bar input{width:100%}
  .page-content{padding:16px}
}
</style>
