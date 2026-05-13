<template>
  <div class="admin-page fade-in">
    <div class="toolbar">
      <button class="btn-primary" @click="showAddUser = true">
        <UserPlus :size="16" /> Tambah User
      </button>
      <span class="muted">{{ users.length }} user terdaftar</span>
    </div>

    <div v-if="loading" class="loading-state">
      <Loader :size="24" class="spin" /> Memuat data user...
    </div>

    <div v-else class="card p-0">
      <table class="data-table full">
        <thead>
          <tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>Aksi</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td class="mono muted">#{{ u.id }}</td>
            <td><strong>{{ u.username }}</strong></td>
            <td class="muted">{{ u.email }}</td>
            <td><span class="badge" :class="roleBadge(u.role)">{{ u.role }}</span></td>
            <td><span class="badge" :class="u.is_active ? 'lunas' : 'warn'">{{ u.is_active ? 'Aktif' : 'Nonaktif' }}</span></td>
            <td class="actions">
              <button class="btn-icon" @click="openEdit(u)" title="Edit"><Edit2 :size="14"/></button>
              <button class="btn-icon danger" @click="confirmDelete(u)" title="Hapus"><Trash2 :size="14"/></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ADD USER MODAL -->
    <div class="modal-overlay" v-if="showAddUser" @click.self="showAddUser = false">
      <div class="modal fade-in">
        <div class="modal-header">
          <h3>Tambah User Baru</h3>
          <button class="btn-icon" @click="showAddUser = false"><X :size="20"/></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label>Username</label><input v-model="newUser.username" type="text" placeholder="username" /></div>
          <div class="form-group"><label>Email</label><input v-model="newUser.email" type="email" placeholder="email@example.com" /></div>
          <div class="form-group"><label>Password</label><input v-model="newUser.password" type="password" placeholder="Min 8 karakter" /></div>
          <div class="form-group">
            <label>Role</label>
            <select v-model="newUser.role" class="form-select">
              <option value="kasir">Kasir</option>
              <option value="manajer">Manajer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAddUser = false">Batal</button>
          <button class="btn-primary" @click="createUser" :disabled="saving">
            <component :is="saving ? Loader : UserPlus" :size="14" :class="{spin:saving}"/> {{ saving ? 'Menyimpan...' : 'Simpan' }}
          </button>
        </div>
      </div>
    </div>

    <!-- EDIT USER MODAL -->
    <div class="modal-overlay" v-if="showEditUser" @click.self="showEditUser = false">
      <div class="modal fade-in">
        <div class="modal-header">
          <h3>Edit User: {{ editUser.username }}</h3>
          <button class="btn-icon" @click="showEditUser = false"><X :size="20"/></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label>Username</label><input v-model="editUser.username" type="text" /></div>
          <div class="form-group"><label>Email</label><input v-model="editUser.email" type="email" /></div>
          <div class="form-group"><label>Password Baru (kosongkan jika tidak diubah)</label><input v-model="editUser.password" type="password" placeholder="••••••••" /></div>
          <div class="form-group">
            <label>Role</label>
            <select v-model="editUser.role" class="form-select">
              <option value="kasir">Kasir</option>
              <option value="manajer">Manajer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="editUser.is_active" class="form-select">
              <option :value="true">Aktif</option>
              <option :value="false">Nonaktif</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showEditUser = false">Batal</button>
          <button class="btn-primary" @click="updateUser" :disabled="saving">
            <component :is="saving ? Loader : CheckCircle" :size="14" :class="{spin:saving}"/> {{ saving ? 'Menyimpan...' : 'Update' }}
          </button>
        </div>
      </div>
    </div>

    <!-- DELETE CONFIRMATION MODAL -->
    <div class="modal-overlay" v-if="showDeleteConfirm" @click.self="showDeleteConfirm = false">
      <div class="modal fade-in" style="max-width:420px">
        <div class="modal-header">
          <h3>Konfirmasi Hapus</h3>
          <button class="btn-icon" @click="showDeleteConfirm = false"><X :size="20"/></button>
        </div>
        <div class="modal-body" style="text-align:center; padding:24px;">
          <AlertTriangle :size="40" style="color:var(--c-rose); margin-bottom:12px;"/>
          <p>Apakah Anda yakin ingin menghapus user <strong>{{ deleteTarget?.username }}</strong>?</p>
          <p class="muted" style="font-size:13px;">Tindakan ini tidak dapat dibatalkan.</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteConfirm = false">Batal</button>
          <button class="btn-danger" @click="doDelete">
            <Trash2 :size="14"/> Hapus Permanen
          </button>
        </div>
      </div>
    </div>

    <!-- TOAST -->
    <div class="admin-toast" :class="{ show: toastVisible, error: toastType === 'error', success: toastType === 'success' }">
      <component :is="toastType === 'error' ? AlertTriangle : CheckCircle" :size="16"/>
      {{ toastMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { authApi } from '../services/api.js'
import { UserPlus, Edit2, Trash2, X, Loader, CheckCircle, AlertTriangle } from 'lucide-vue-next'

const users = ref([])
const loading = ref(false)
const saving = ref(false)

const showAddUser = ref(false)
const showEditUser = ref(false)
const showDeleteConfirm = ref(false)
const deleteTarget = ref(null)

const newUser = ref({ username: '', email: '', password: '', role: 'kasir' })
const editUser = ref({ id: null, username: '', email: '', password: '', role: 'kasir', is_active: true })

const toastVisible = ref(false)
const toastMsg = ref('')
const toastType = ref('success')

function showToast(msg, type = 'success') {
  toastMsg.value = msg; toastType.value = type; toastVisible.value = true
  setTimeout(() => toastVisible.value = false, 3500)
}

function roleBadge(role) {
  if (role === 'admin') return 'admin-badge'
  if (role === 'manajer') return 'manajer-badge'
  return 'lunas'
}

async function fetchUsers() {
  loading.value = true
  try {
    const res = await authApi.getUsers()
    users.value = res.data || []
  } catch (e) { showToast(e.message, 'error') }
  finally { loading.value = false }
}

async function createUser() {
  if (!newUser.value.username || !newUser.value.email || !newUser.value.password) {
    showToast('Lengkapi semua field!', 'error'); return
  }
  saving.value = true
  try {
    await authApi.createUser(newUser.value)
    showToast('User berhasil ditambahkan!')
    showAddUser.value = false
    newUser.value = { username: '', email: '', password: '', role: 'kasir' }
    await fetchUsers()
  } catch (e) { showToast(e.message, 'error') }
  finally { saving.value = false }
}

function openEdit(u) {
  editUser.value = { id: u.id, username: u.username, email: u.email, password: '', role: u.role, is_active: u.is_active }
  showEditUser.value = true
}

async function updateUser() {
  saving.value = true
  try {
    const payload = {
      username: editUser.value.username,
      email: editUser.value.email,
      role: editUser.value.role,
      is_active: editUser.value.is_active,
    }
    if (editUser.value.password) payload.password = editUser.value.password
    await authApi.updateUser(editUser.value.id, payload)
    showToast('User berhasil diupdate!')
    showEditUser.value = false
    await fetchUsers()
  } catch (e) { showToast(e.message, 'error') }
  finally { saving.value = false }
}

function confirmDelete(u) {
  deleteTarget.value = u
  showDeleteConfirm.value = true
}

async function doDelete() {
  try {
    await authApi.deleteUser(deleteTarget.value.id)
    showToast('User berhasil dihapus!')
    showDeleteConfirm.value = false
    await fetchUsers()
  } catch (e) { showToast(e.message, 'error') }
}

onMounted(fetchUsers)
</script>

<style scoped>
.admin-page { padding: 0; }
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.btn-primary {
  background: var(--text); color: var(--bg); border: none; padding: 10px 20px;
  border-radius: 10px; font-size: 14px; font-weight: 600; display: inline-flex;
  align-items: center; gap: 8px; cursor: pointer; transition: 0.15s;
}
.btn-primary:hover { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-secondary {
  background: transparent; color: var(--text); border: 1px solid var(--border);
  padding: 10px 20px; border-radius: 10px; font-size: 14px; cursor: pointer;
}
.btn-secondary:hover { background: var(--surface2); }
.btn-danger {
  background: var(--c-rose); color: white; border: none; padding: 10px 20px;
  border-radius: 10px; font-size: 14px; font-weight: 600; display: inline-flex;
  align-items: center; gap: 8px; cursor: pointer; transition: 0.15s;
}
.btn-danger:hover { opacity: 0.85; }
.btn-icon {
  background: transparent; border: 1px solid var(--border); color: var(--text); width: 32px; height: 32px;
  border-radius: 8px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; transition: 0.2s;
}
.btn-icon:hover { background: var(--surface2); }
.btn-icon.danger { color: var(--c-rose); border-color: rgba(244,63,94,0.3); }
.btn-icon.danger:hover { background: rgba(244,63,94,0.1); }

.card { background: rgba(18,18,20,0.6); border: 1px solid var(--border); border-radius: 16px; padding: 24px; }
.card.p-0 { padding: 0; overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; padding: 14px 20px; color: var(--muted); font-size: 12px;
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border); background: var(--surface2);
}
.data-table td { padding: 14px 20px; border-bottom: 1px solid rgba(39,39,42,0.5); font-size: 14px; }
.actions { display: flex; gap: 8px; }

.badge {
  padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600;
}
.badge.lunas { background: rgba(16,185,129,0.1); color: var(--c-emerald); }
.badge.warn { background: rgba(244,63,94,0.1); color: var(--c-rose); }
.badge.admin-badge { background: rgba(168,85,247,0.15); color: #a855f7; }
.badge.manajer-badge { background: rgba(59,130,246,0.15); color: #3b82f6; }

.form-select {
  width: 100%; background: var(--surface2); border: 1px solid var(--border); color: var(--text);
  padding: 12px 16px; border-radius: 10px; outline: none; font-family: 'Inter', sans-serif; font-size: 14px;
}

/* Modals */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal {
  background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
  width: 500px; max-height: 90vh; overflow-y: auto; box-shadow: 0 24px 48px rgba(0,0,0,0.5);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid var(--border);
}
.modal-header h3 { font-family: 'Outfit', sans-serif; font-size: 18px; }
.modal-body { padding: 24px; }
.modal-footer {
  padding: 16px 24px; border-top: 1px solid var(--border);
  display: flex; justify-content: flex-end; gap: 12px;
}

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; color: var(--muted); font-weight: 500; margin-bottom: 6px; }
.form-group input {
  width: 100%; background: var(--surface2); border: 1px solid var(--border); color: var(--text);
  padding: 12px 16px; border-radius: 10px; outline: none; font-size: 14px; transition: 0.2s;
}
.form-group input:focus { border-color: var(--c-indigo); box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }

.loading-state { display: flex; align-items: center; gap: 12px; padding: 40px; color: var(--muted); justify-content: center; }
.muted { color: var(--muted); }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.fade-in { animation: fi 0.3s ease-out; }
@keyframes fi { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.admin-toast {
  position: fixed; bottom: 32px; right: 32px; background: var(--surface); border: 1px solid var(--border);
  padding: 14px 22px; border-radius: 12px; font-size: 14px; font-weight: 500;
  display: flex; align-items: center; gap: 10px; z-index: 2000;
  transform: translateY(100px); opacity: 0; transition: all 0.4s cubic-bezier(0.68,-0.55,0.27,1.55);
}
.admin-toast.show { transform: translateY(0); opacity: 1; }
.admin-toast.error { border-color: var(--c-rose); color: var(--c-rose); }
.admin-toast.success { border-color: var(--c-emerald); color: var(--c-emerald); }
</style>
