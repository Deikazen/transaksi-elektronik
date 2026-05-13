<template>
  <div class="login-root">
    <!-- Animated background -->
    <div class="bg-layer">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-orb orb-3"></div>
      <div class="bg-grid"></div>
    </div>

    <div class="login-wrap">
      <!-- Left panel - branding -->
      <div class="login-brand">
        <div class="brand-content">
          <div class="brand-logo">
            <component :is="ShieldCheck" :size="36" stroke-width="2" />
          </div>
          <h1 class="brand-name">Secure<span class="accent">Transact</span></h1>
          <p class="brand-desc">
            Sistem Transaksi Elektronik Terintegrasi dengan keamanan <em>Secure by Design</em>.
          </p>
          <div class="brand-pills">
            <span class="pill"><component :is="Lock" :size="12" /> JWT Auth</span>
            <span class="pill"><component :is="Users" :size="12" /> RBAC</span>
            <span class="pill"><component :is="FileCheck" :size="12" /> Kontrak Digital</span>
            <span class="pill"><component :is="ShieldCheck" :size="12" /> Enkripsi</span>
          </div>
          <div class="brand-stats">
            <div class="stat-item">
              <span class="stat-num">256-bit</span>
              <span class="stat-label">Enkripsi AES</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-num">3 Role</span>
              <span class="stat-label">Access Control</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-num">JWT</span>
              <span class="stat-label">Auth Tokens</span>
            </div>
          </div>
          <div class="brand-footer">
            <span>Grup C10 · Tugas IFB-352 · ITENAS 2026</span>
          </div>
        </div>
      </div>

      <!-- Right panel - form -->
      <div class="login-form-panel">
        <div class="form-box">
          <!-- Tab switch -->
          <div class="tab-switch">
            <button :class="['tab', { active: mode === 'login' }]" @click="mode = 'login'; clearErr()">
              <component :is="LogIn" :size="15" /> Masuk
            </button>
            <button :class="['tab', { active: mode === 'register' }]" @click="mode = 'register'; clearErr()">
              <component :is="UserPlus" :size="15" /> Daftar
            </button>
          </div>

          <!-- ── LOGIN ── -->
          <transition name="slide-fade" mode="out-in">
            <form v-if="mode === 'login'" key="login" class="form-section" @submit.prevent="doLogin">
              <div class="form-header">
                <h2 class="form-title">Selamat datang kembali</h2>
                <p class="form-sub">Masuk ke dashboard SecureTransact</p>
              </div>

              <div class="form-group">
                <label>Username</label>
                <div class="input-wrap">
                  <component :is="UserIcon" :size="16" class="input-icon" />
                  <input
                    v-model="loginForm.username"
                    type="text"
                    placeholder="Masukkan username"
                    autocomplete="username"
                    id="login-username"
                  />
                </div>
              </div>

              <div class="form-group">
                <label>Password</label>
                <div class="input-wrap">
                  <component :is="KeyRound" :size="16" class="input-icon" />
                  <input
                    v-model="loginForm.password"
                    :type="showPw ? 'text' : 'password'"
                    placeholder="••••••••"
                    autocomplete="current-password"
                    id="login-password"
                  />
                  <button class="toggle-pw" @click="showPw = !showPw" type="button" :aria-label="showPw ? 'Sembunyikan' : 'Tampilkan'">
                    <component :is="showPw ? EyeOff : Eye" :size="16" />
                  </button>
                </div>
              </div>

              <transition name="fade">
                <div class="error-box" v-if="errMsg">
                  <component :is="AlertCircle" :size="14" /> {{ errMsg }}
                </div>
              </transition>

              <button class="btn-submit" type="submit" :disabled="loading" id="btn-login">
                <component v-if="loading" :is="Loader" :size="16" class="spin" />
                <template v-else>
                  <component :is="LogIn" :size="16" /> Masuk ke Dashboard
                </template>
              </button>
            </form>
          </transition>

          <!-- ── REGISTER ── -->
          <transition name="slide-fade" mode="out-in">
            <form v-if="mode === 'register'" key="register" class="form-section" @submit.prevent="doRegister">
              <div class="form-header">
                <h2 class="form-title">Buat Akun Baru</h2>
                <p class="form-sub">Daftarkan pengguna ke sistem SecureTransact</p>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>Username</label>
                  <div class="input-wrap">
                    <component :is="UserIcon" :size="16" class="input-icon" />
                    <input v-model="regForm.username" type="text" placeholder="huruf kecil, tanpa spasi" id="reg-username" />
                  </div>
                </div>
                <div class="form-group">
                  <label>Email</label>
                  <div class="input-wrap">
                    <component :is="Mail" :size="16" class="input-icon" />
                    <input v-model="regForm.email" type="email" placeholder="user@email.com" id="reg-email" />
                  </div>
                </div>
              </div>

              <div class="form-group">
                <label>Password <span class="hint">(min. 8 karakter)</span></label>
                <div class="input-wrap">
                  <component :is="KeyRound" :size="16" class="input-icon" />
                  <input
                    v-model="regForm.password"
                    :type="showPw ? 'text' : 'password'"
                    placeholder="••••••••"
                    id="reg-password"
                  />
                  <button class="toggle-pw" @click="showPw = !showPw" type="button">
                    <component :is="showPw ? EyeOff : Eye" :size="16" />
                  </button>
                </div>
                <div class="pw-strength" v-if="regForm.password">
                  <div class="pw-track">
                    <div class="pw-bar" :class="pwStrengthClass" :style="{ width: pwStrengthWidth }"></div>
                  </div>
                  <span class="pw-label" :class="pwStrengthClass">{{ pwStrengthLabel }}</span>
                </div>
              </div>

              <div class="form-group">
                <label>Role Pengguna</label>
                <div class="input-wrap select-input">
                  <component :is="Shield" :size="16" class="input-icon" />
                  <select v-model="regForm.role" id="reg-role">
                    <option value="kasir">Kasir — akses POS & inventory</option>
                    <option value="manajer">Manajer — akses lihat semua</option>
                    <option value="admin">Admin — akses penuh sistem</option>
                  </select>
                </div>
              </div>

              <transition name="fade">
                <div class="error-box" v-if="errMsg">
                  <component :is="AlertCircle" :size="14" /> {{ errMsg }}
                </div>
              </transition>
              <transition name="fade">
                <div class="success-box" v-if="successMsg">
                  <component :is="CheckCircle2" :size="14" /> {{ successMsg }}
                </div>
              </transition>

              <button class="btn-submit" type="submit" :disabled="loading" id="btn-register">
                <component v-if="loading" :is="Loader" :size="16" class="spin" />
                <template v-else>
                  <component :is="UserPlus" :size="16" /> Buat Akun Sekarang
                </template>
              </button>

              <div class="register-note">
                <component :is="Info" :size="12" />
                Akun baru memerlukan persetujuan admin sebelum dapat login.
              </div>
            </form>
          </transition>

          <div class="form-footnote">
            SecureTransact · Sistem Transaksi Elektronik · IFB-352 ITENAS
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { authApi, saveTokens, saveUser } from './services/api.js'
import {
  ShieldCheck, Lock, FileCheck, LogIn, UserPlus, User as UserIcon, KeyRound,
  Eye, EyeOff, AlertCircle, Loader, Info, Mail, Shield, CheckCircle2, Users
} from 'lucide-vue-next'

const emit = defineEmits(['logged-in'])

const mode    = ref('login')
const loading = ref(false)
const errMsg  = ref('')
const successMsg = ref('')
const showPw  = ref(false)

const loginForm = reactive({ username: '', password: '' })
const regForm   = reactive({ username: '', email: '', password: '', role: 'kasir' })

const pwStrengthScore = computed(() => {
  const pw = regForm.password;
  if (!pw) return 0;
  let score = 0;
  if (pw.length > 7) score += 1;
  if (pw.length > 10) score += 1;
  if (/[A-Z]/.test(pw)) score += 1;
  if (/[0-9]/.test(pw)) score += 1;
  if (/[^A-Za-z0-9]/.test(pw)) score += 1;
  return Math.min(score, 4);
});

const pwStrengthClass = computed(() => {
  const score = pwStrengthScore.value;
  if (score === 0) return '';
  if (score === 1) return 'weak';
  if (score === 2) return 'medium';
  if (score === 3) return 'strong';
  return 'very-strong';
});

const pwStrengthLabel = computed(() => {
  const score = pwStrengthScore.value;
  if (score === 0) return '';
  if (score === 1) return 'Lemah';
  if (score === 2) return 'Sedang';
  if (score === 3) return 'Kuat';
  return 'Sangat Kuat';
});

const pwStrengthWidth = computed(() => {
  const score = pwStrengthScore.value;
  if (score === 0) return '0%';
  if (score === 1) return '25%';
  if (score === 2) return '50%';
  if (score === 3) return '75%';
  return '100%';
});

function clearErr() { errMsg.value = ''; successMsg.value = '' }


async function doLogin() {
  if (!loginForm.username || !loginForm.password) {
    errMsg.value = 'Username dan password wajib diisi.'; return
  }
  loading.value = true; errMsg.value = ''
  try {
    const data = await authApi.login(loginForm.username, loginForm.password)
    saveTokens(data.access_token, data.refresh_token)
    saveUser(data.user)
    emit('logged-in', data.user)
  } catch (e) {
    if (e.name === 'TypeError' || e.message.includes('fetch') || e.message.includes('NetworkError')) {
      errMsg.value = 'Tidak dapat terhubung ke server. Pastikan backend berjalan di port 8000.'
    } else {
      errMsg.value = e.message
    }
  } finally {
    loading.value = false
  }
}


async function doRegister() {
  if (!regForm.username || !regForm.email || !regForm.password) {
    errMsg.value = 'Semua field wajib diisi.'; return
  }
  loading.value = true; errMsg.value = ''; successMsg.value = ''
  try {
    await authApi.register({ ...regForm })
    successMsg.value = `Akun "${regForm.username}" berhasil dibuat! Tunggu persetujuan admin.`
    regForm.username = ''; regForm.email = ''; regForm.password = ''
    setTimeout(() => { mode.value = 'login'; successMsg.value = '' }, 2000)
  } catch (e) {
    errMsg.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@700;800;900&display=swap');

/* ── ROOT & BACKGROUND ── */
.login-root {
  min-height: 100vh;
  background: #07070a;
  font-family: 'Inter', sans-serif;
  color: #f4f4f5;
  position: relative;
  overflow: hidden;
}

.bg-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  animation: orbFloat 12s ease-in-out infinite;
}
.orb-1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
  top: -100px; left: -100px;
  animation-delay: 0s;
}
.orb-2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 70%);
  bottom: -80px; right: 20%;
  animation-delay: -4s;
}
.orb-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%);
  top: 40%; right: -50px;
  animation-delay: -8s;
}
@keyframes orbFloat {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-30px) scale(1.05); }
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* ── LAYOUT WRAP ── */
.login-wrap {
  display: flex;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* ── LEFT BRAND ── */
.login-brand {
  width: 42%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
  background: linear-gradient(160deg,
    rgba(99,102,241,0.08) 0%,
    rgba(15,15,20,0.6) 40%,
    rgba(139,92,246,0.06) 100%
  );
  border-right: 1px solid rgba(255,255,255,0.06);
  backdrop-filter: blur(4px);
  position: relative;
  overflow-y: auto;
}

.brand-content {
  max-width: 360px;
  width: 100%;
}

.brand-logo {
  width: 56px; height: 56px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 24px;
  color: #fff;
  box-shadow:
    0 0 0 1px rgba(99,102,241,0.3),
    0 8px 32px rgba(99,102,241,0.25),
    0 0 60px rgba(99,102,241,0.1);
}

.brand-name {
  font-family: 'Outfit', sans-serif;
  font-size: 30px; font-weight: 900;
  color: #f4f4f5;
  margin-bottom: 10px;
  letter-spacing: -0.04em;
  line-height: 1.1;
}
.brand-name .accent {
  background: linear-gradient(135deg, #a5b4fc, #c4b5fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-desc {
  font-size: 13px; color: #71717a; line-height: 1.7;
  margin-bottom: 24px;
}
.brand-desc em { color: #a5b4fc; font-style: normal; font-weight: 500; }

.brand-pills {
  display: flex; flex-wrap: wrap; gap: 7px;
  margin-bottom: 28px;
}
.pill {
  background: rgba(99,102,241,0.08);
  border: 1px solid rgba(99,102,241,0.18);
  color: #a5b4fc;
  padding: 6px 14px; border-radius: 100px;
  font-size: 12px; font-weight: 500;
  display: inline-flex; align-items: center; gap: 6px;
  transition: all 0.2s;
}
.pill:hover {
  background: rgba(99,102,241,0.15);
  border-color: rgba(99,102,241,0.35);
}

.brand-stats {
  display: flex; align-items: center; gap: 0;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 24px;
}
.stat-item {
  flex: 1;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.stat-num {
  font-size: 15px; font-weight: 700;
  color: #a5b4fc;
  font-family: 'Outfit', sans-serif;
}
.stat-label {
  font-size: 11px; color: #52525b;
  font-weight: 500;
}
.stat-divider {
  width: 1px; height: 32px;
  background: rgba(255,255,255,0.06);
}

.brand-footer {
  font-size: 12px; color: #3f3f46;
  padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.04);
}

/* ── RIGHT FORM PANEL ── */
.login-form-panel {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 32px 48px;
  overflow-y: auto;
}

.form-box {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: auto 0;
}

/* ── TABS ── */
.tab-switch {
  display: flex;
  background: rgba(24,24,27,0.8);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 24px;
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}
.tab {
  flex: 1; padding: 11px;
  background: none; border: none;
  color: #71717a; cursor: pointer;
  border-radius: 10px;
  font-family: 'Inter', sans-serif;
  font-size: 14px; font-weight: 500;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex; align-items: center; justify-content: center; gap: 7px;
}
.tab:hover:not(.active) { color: #a1a1aa; background: rgba(255,255,255,0.04); }
.tab.active {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff; font-weight: 600;
  box-shadow: 0 4px 16px rgba(99,102,241,0.35);
}

/* ── FORM SECTIONS ── */
.form-section {
  display: flex;
  flex-direction: column;
}

.form-header {
  margin-bottom: 20px;
}
.form-title {
  font-family: 'Outfit', sans-serif;
  font-size: 22px; font-weight: 800;
  color: #f4f4f5; margin-bottom: 4px;
  letter-spacing: -0.03em;
}
.form-sub {
  font-size: 14px; color: #71717a;
}

.form-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
}

/* ── INPUTS ── */
.form-group { margin-bottom: 14px; }
.form-group label {
  display: block; font-size: 12px;
  font-weight: 500; color: #a1a1aa;
  margin-bottom: 6px; letter-spacing: 0.01em;
}
.hint { font-weight: 400; color: #52525b; }

.input-wrap {
  position: relative;
  display: flex; align-items: center;
}
.input-icon {
  position: absolute; left: 14px;
  color: #52525b;
  pointer-events: none;
  z-index: 1;
  transition: color 0.2s;
}
.input-wrap:focus-within .input-icon { color: #a5b4fc; }

.input-wrap input,
.input-wrap select {
  width: 100%;
  background: rgba(24,24,27,0.9);
  border: 1px solid rgba(255,255,255,0.08);
  color: #f4f4f5;
  padding: 11px 16px 11px 40px;
  border-radius: 10px;
  font-size: 13px;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: all 0.25s;
  backdrop-filter: blur(4px);
}
.input-wrap input::placeholder { color: #3f3f46; }
.input-wrap input:focus,
.input-wrap select:focus {
  border-color: rgba(99,102,241,0.5);
  background: rgba(30,30,38,0.95);
  box-shadow:
    0 0 0 3px rgba(99,102,241,0.12),
    inset 0 1px 2px rgba(0,0,0,0.2);
}

.input-wrap select {
  appearance: none;
  cursor: pointer;
  padding-right: 40px;
}
.select-input::after {
  content: '▾';
  position: absolute; right: 14px;
  color: #52525b; pointer-events: none;
  font-size: 12px;
}

.toggle-pw {
  position: absolute; right: 12px;
  background: none; border: none;
  cursor: pointer; color: #52525b;
  padding: 6px;
  display: flex; align-items: center;
  transition: color 0.2s; border-radius: 6px;
}
.toggle-pw:hover { color: #a1a1aa; background: rgba(255,255,255,0.05); }

/* ── PASSWORD STRENGTH ── */
.pw-strength {
  display: flex; align-items: center; gap: 10px; margin-top: 8px;
}
.pw-track {
  flex: 1; height: 3px;
  background: rgba(255,255,255,0.06);
  border-radius: 99px; overflow: hidden;
}
.pw-bar {
  height: 100%; border-radius: 99px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.pw-bar.weak      { background: #f43f5e; }
.pw-bar.medium    { background: #f59e0b; }
.pw-bar.strong    { background: #10b981; }
.pw-bar.very-strong { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.pw-label {
  font-size: 11px; font-weight: 600;
  white-space: nowrap; text-transform: uppercase; letter-spacing: 0.05em;
}
.pw-label.weak      { color: #f43f5e; }
.pw-label.medium    { color: #f59e0b; }
.pw-label.strong    { color: #10b981; }
.pw-label.very-strong { color: #a5b4fc; }

/* ── ALERTS ── */
.error-box {
  background: rgba(244,63,94,0.07);
  border: 1px solid rgba(244,63,94,0.2);
  color: #fb7185;
  padding: 12px 16px; border-radius: 10px;
  font-size: 13px; margin-bottom: 16px;
  display: flex; align-items: center; gap: 8px;
}
.success-box {
  background: rgba(16,185,129,0.07);
  border: 1px solid rgba(16,185,129,0.2);
  color: #34d399;
  padding: 12px 16px; border-radius: 10px;
  font-size: 13px; margin-bottom: 16px;
  display: flex; align-items: center; gap: 8px;
}

/* ── SUBMIT BUTTON ── */
.btn-submit {
  width: 100%; padding: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  border: none; border-radius: 10px;
  font-family: 'Inter', sans-serif;
  font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.25s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 20px rgba(99,102,241,0.3);
  letter-spacing: 0.01em;
}
.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(99,102,241,0.42);
}
.btn-submit:active:not(:disabled) { transform: translateY(0); }
.btn-submit:disabled { opacity: 0.45; cursor: not-allowed; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.role-badge {
  padding: 3px 8px; border-radius: 6px;
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.06em;
  flex-shrink: 0;
}
.role-badge.admin   { background: rgba(244,63,94,0.12);  color: #fb7185; border: 1px solid rgba(244,63,94,0.2); }
.role-badge.kasir   { background: rgba(99,102,241,0.12); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.2); }
.role-badge.manajer { background: rgba(139,92,246,0.12); color: #c4b5fd; border: 1px solid rgba(139,92,246,0.2); }

/* ── REGISTER NOTE ── */
.register-note {
  display: flex; align-items: flex-start; gap: 7px;
  font-size: 12px; color: #52525b;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 9px; padding: 11px 13px;
  margin-bottom: 20px; line-height: 1.5;
}

/* ── FOOTNOTE ── */
.form-footnote {
  text-align: center; font-size: 11px;
  color: #27272a; letter-spacing: 0.03em;
  padding-top: 4px;
}

/* ── TRANSITIONS ── */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-fade-enter-from {
  opacity: 0; transform: translateY(10px);
}
.slide-fade-leave-to {
  opacity: 0; transform: translateY(-10px);
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
  .login-wrap { flex-direction: column; }
  .login-brand {
    width: 100%; padding: 40px 32px;
    border-right: none;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  .brand-content { max-width: 100%; }
  .brand-name { font-size: 28px; }
  .brand-stats { display: none; }
  .login-form-panel { padding: 32px 24px; }
}
@media (max-width: 480px) {
  .login-brand { display: none; }
  .form-row { grid-template-columns: 1fr; }
  .login-form-panel { padding: 24px 20px; }
}
</style>