<template>
  <div class="deteksi-page fade-in">
    <div class="det-hero">
      <div class="det-hero-content">
        <div class="det-hero-icon"><ScanLine :size="28" /></div>
        <div>
          <h2>Deteksi Keaslian Uang</h2>
          <p class="muted">Analisis visual menggunakan Computer Vision — OpenCV</p>
        </div>
      </div>
      <div class="det-hero-badge" :class="cvStatus">
        <component :is="cvStatus === 'online' ? CheckCircle : AlertTriangle" :size="14" />
        {{ cvStatus === 'online' ? 'Engine Ready' : cvStatus === 'demo' ? 'Demo Mode' : 'Checking...' }}
      </div>
    </div>

    <div class="det-layout">
      <div class="det-input-panel">
        <div class="det-card">
          <div class="det-card-header"><h3><Camera :size="18" /> Sumber Gambar</h3></div>
          <div class="det-tabs">
            <button :class="{ active: inputMode === 'camera' }" @click="inputMode = 'camera'"><Camera :size="14" /> Kamera</button>
            <button :class="{ active: inputMode === 'upload' }" @click="inputMode = 'upload'"><Upload :size="14" /> Upload</button>
          </div>

          <div v-if="inputMode === 'camera'" class="camera-section">
            <div class="camera-viewport" :class="{ active: cameraActive }">
              <video ref="videoEl" autoplay playsinline muted v-show="cameraActive"></video>
              <canvas ref="canvasEl" style="display:none"></canvas>
              <div v-if="!cameraActive && !capturedImage" class="camera-placeholder">
                <VideoOff :size="48" /><p>Kamera belum aktif</p>
              </div>
              <div v-if="capturedImage && !cameraActive" class="captured-overlay"><img :src="capturedImage" /></div>
            </div>
            <div class="camera-controls">
              <button v-if="!cameraActive" class="btn-action start" @click="startCamera"><Camera :size="16" /> Aktifkan Kamera</button>
              <template v-else>
                <button class="btn-action capture" @click="captureFrame"><Aperture :size="16" /> Ambil Foto</button>
                <button class="btn-action stop" @click="stopCamera"><VideoOff :size="16" /> Matikan</button>
              </template>
            </div>
          </div>

          <div v-if="inputMode === 'upload'" class="upload-section">
            <div class="upload-zone" :class="{ dragover: isDragOver }" @dragover.prevent="isDragOver=true" @dragleave="isDragOver=false" @drop.prevent="handleDrop" @click="$refs.fileInputEl.click()">
              <Upload :size="40" /><p>Drag & drop gambar uang</p><span class="muted">JPEG/PNG, maks 20MB</span>
              <input ref="fileInputEl" type="file" accept="image/*" @change="handleFileSelect" style="display:none" />
            </div>
            <div v-if="capturedImage" class="upload-preview">
              <img :src="capturedImage" />
              <button class="btn-remove" @click="clearCapture"><X :size="14" /> Hapus</button>
            </div>
          </div>

          <button class="btn-analyze" :disabled="!capturedImage || analyzing" @click="analyzeImage">
            <component :is="analyzing ? Loader : ScanLine" :size="16" :class="{ spin: analyzing }" />
            {{ analyzing ? 'Menganalisis...' : 'Mulai Analisis' }}
          </button>
        </div>
      </div>

      <div class="det-results-panel">
        <div v-if="!result" class="det-card result-empty">
          <ScanLine :size="48" /><h3>Belum Ada Hasil</h3>
          <p class="muted">Ambil foto atau upload gambar untuk memulai analisis</p>
        </div>
        <template v-else>
          <div class="det-card verdict-card" :class="result.verdict.level">
            <div class="verdict-header">
              <div class="verdict-emoji">{{ result.verdict.emoji }}</div>
              <div class="verdict-info">
                <h2>{{ result.verdict.verdict }}</h2>
                <p>{{ result.verdict.pesan }}</p>
              </div>
            </div>
            <div class="score-gauge-wrap">
              <svg class="score-gauge" viewBox="0 0 200 120">
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="12" stroke-linecap="round" />
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" :stroke="result.verdict.warna" stroke-width="12" stroke-linecap="round" :stroke-dasharray="gArc" :stroke-dashoffset="gOffset" class="gauge-fill" />
                <text x="100" y="80" text-anchor="middle" fill="white" font-size="36" font-weight="700" font-family="Outfit">{{ result.skor_keseluruhan }}</text>
                <text x="100" y="100" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="12">dari 100</text>
              </svg>
            </div>
            <div class="analysis-meta">
              <span><Clock :size="12" /> {{ result.waktu_analisis_ms }}ms</span>
              <span><Maximize :size="12" /> {{ result.resolusi.lebar }}×{{ result.resolusi.tinggi }}</span>
              <span v-if="result.status === 'demo'" class="demo-badge"><AlertTriangle :size="12" /> Demo</span>
            </div>
          </div>
          <div class="indicators-grid">
            <div v-for="(ind, key) in result.indikator" :key="key" class="indicator-card" :class="ind.skor >= 75 ? 'ind-good' : ind.skor >= 50 ? 'ind-warn' : 'ind-bad'">
              <div class="ind-header"><span class="ind-name">{{ key.replace(/_/g,' ') }}</span></div>
              <div class="ind-score">
                <div class="ind-bar-bg"><div class="ind-bar-fill" :style="{ width: ind.skor+'%', background: ind.skor>=75?'#10b981':ind.skor>=50?'#f59e0b':'#ef4444' }"></div></div>
                <span class="ind-score-val">{{ ind.skor }}</span>
              </div>
              <div class="ind-status">{{ ind.status }}</div>
              <div class="ind-detail muted">{{ ind.detail }}</div>
            </div>
          </div>
          <div class="det-card rekomendasi-card">
            <h3><Lightbulb :size="18" /> Rekomendasi</h3>
            <ul><li v-for="(r,i) in result.verdict.rekomendasi" :key="i"><CheckCircle :size="14" :style="{color:result.verdict.warna}" /> {{ r }}</li></ul>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'
import { deteksiUangApi } from '../services/api.js'
import { ScanLine, Camera, Upload, VideoOff, Aperture, Loader, X, CheckCircle, AlertTriangle, Lightbulb, Clock, Maximize } from 'lucide-vue-next'

const inputMode = ref('camera'), cameraActive = ref(false), capturedImage = ref(null), capturedBlob = ref(null)
const analyzing = ref(false), result = ref(null), isDragOver = ref(false), cvStatus = ref('checking')
const videoEl = ref(null), canvasEl = ref(null)
let mediaStream = null

const gArc = computed(() => `${Math.PI * 80}`)
const gOffset = computed(() => { if (!result.value) return Math.PI*80; return Math.PI*80 - (Math.PI*80 * result.value.skor_keseluruhan/100) })

onMounted(async () => {
  try {
    const d = await deteksiUangApi.getStatus()
    cvStatus.value = d.cv2_available ? 'online' : 'demo'
  } catch {
    cvStatus.value = 'demo'
  }
})

async function startCamera() {
  try { mediaStream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:'environment', width:{ideal:1280}, height:{ideal:720} } }); if(videoEl.value) videoEl.value.srcObject=mediaStream; cameraActive.value=true; capturedImage.value=null; capturedBlob.value=null } catch(e) { alert('Gagal akses kamera: '+e.message) }
}
function stopCamera() { if(mediaStream){mediaStream.getTracks().forEach(t=>t.stop()); mediaStream=null} cameraActive.value=false }
function captureFrame() { if(!videoEl.value||!canvasEl.value) return; const v=videoEl.value, c=canvasEl.value; c.width=v.videoWidth; c.height=v.videoHeight; c.getContext('2d').drawImage(v,0,0); capturedImage.value=c.toDataURL('image/jpeg',0.92); c.toBlob(b=>{capturedBlob.value=b},'image/jpeg',0.92); stopCamera() }
function handleFileSelect(e) { const f=e.target.files?.[0]; if(f) processFile(f) }
function handleDrop(e) { isDragOver.value=false; const f=e.dataTransfer.files?.[0]; if(f) processFile(f) }
function processFile(f) { if(!f.type.startsWith('image/')){alert('File harus gambar');return} capturedBlob.value=f; const r=new FileReader(); r.onload=e=>{capturedImage.value=e.target.result}; r.readAsDataURL(f) }
function clearCapture() { capturedImage.value=null; capturedBlob.value=null; result.value=null }
async function analyzeImage() {
  if (!capturedBlob.value) return
  analyzing.value = true
  result.value = null
  try {
    const res = await deteksiUangApi.analyze(capturedBlob.value)
    result.value = res
  } catch (e) {
    alert(e.message)
  } finally {
    analyzing.value = false
  }
}
onBeforeUnmount(()=>stopCamera())
</script>

<style scoped>
.deteksi-page{flex:1;display:flex;flex-direction:column;gap:20px;min-height:0}
.det-layout{display:grid;grid-template-columns:1fr 1.2fr;gap:20px;flex:1;min-height:0;overflow-y:auto}
.det-hero{display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(139,92,246,0.08));border:1px solid rgba(99,102,241,0.2);border-radius:16px;padding:20px 24px}
.det-hero-content{display:flex;align-items:center;gap:16px}
.det-hero-icon{background:rgba(99,102,241,0.15);color:var(--c-indigo);padding:12px;border-radius:14px;display:flex}
.det-hero h2{font-family:'Outfit',sans-serif;font-size:20px;font-weight:700}
.det-hero-badge{display:flex;align-items:center;gap:6px;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600}
.det-hero-badge.online{background:rgba(16,185,129,0.12);color:var(--c-emerald);border:1px solid rgba(16,185,129,0.2)}
.det-hero-badge.demo{background:rgba(245,158,11,0.12);color:var(--c-amber);border:1px solid rgba(245,158,11,0.2)}
.det-hero-badge.checking{background:rgba(99,102,241,0.12);color:var(--c-indigo);border:1px solid rgba(99,102,241,0.2)}
.det-card{background:rgba(18,18,20,0.6);border:1px solid var(--border);border-radius:16px;padding:24px;box-shadow:0 8px 32px rgba(0,0,0,0.3);backdrop-filter:blur(12px)}
.det-card-header{display:flex;align-items:center;margin-bottom:16px}
.det-card-header h3{font-family:'Outfit',sans-serif;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}
.det-tabs{display:flex;gap:4px;background:var(--surface2);padding:4px;border-radius:10px;margin-bottom:16px}
.det-tabs button{flex:1;background:transparent;border:none;color:var(--muted);padding:8px 16px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;transition:0.2s}
.det-tabs button.active{background:var(--surface3);color:var(--text);font-weight:600}
.camera-viewport{position:relative;aspect-ratio:16/10;background:#000;border-radius:12px;overflow:hidden;border:2px solid var(--border);margin-bottom:12px}
.camera-viewport.active{border-color:var(--c-emerald)}
.camera-viewport video{width:100%;height:100%;object-fit:cover}
.camera-placeholder{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;color:var(--muted)}
.captured-overlay{position:absolute;inset:0}
.captured-overlay img{width:100%;height:100%;object-fit:cover}
.camera-controls{display:flex;gap:10px}
.btn-action{flex:1;padding:10px;border:none;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;transition:0.2s}
.btn-action.start{background:rgba(16,185,129,0.15);color:var(--c-emerald);border:1px solid rgba(16,185,129,0.2)}
.btn-action.start:hover{background:rgba(16,185,129,0.25)}
.btn-action.capture{background:rgba(99,102,241,0.15);color:var(--c-indigo);border:1px solid rgba(99,102,241,0.2)}
.btn-action.stop{background:rgba(244,63,94,0.15);color:var(--c-rose);border:1px solid rgba(244,63,94,0.2)}
.upload-zone{border:2px dashed var(--border);border-radius:12px;padding:40px 20px;text-align:center;color:var(--muted);cursor:pointer;transition:0.2s;display:flex;flex-direction:column;align-items:center;gap:8px}
.upload-zone:hover,.upload-zone.dragover{border-color:var(--c-indigo);background:rgba(99,102,241,0.05)}
.upload-preview{position:relative;margin-top:12px;border-radius:12px;overflow:hidden;border:1px solid var(--border)}
.upload-preview img{width:100%;max-height:300px;object-fit:contain;background:#000}
.btn-remove{position:absolute;top:8px;right:8px;background:rgba(0,0,0,0.7);color:var(--c-rose);border:none;padding:6px 10px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:4px}
.btn-analyze{width:100%;margin-top:16px;padding:14px;background:linear-gradient(135deg,var(--c-indigo),var(--c-purple));color:white;border:none;border-radius:12px;font-size:14px;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;transition:0.2s;box-shadow:0 4px 16px rgba(99,102,241,0.3)}
.btn-analyze:hover:not(:disabled){transform:translateY(-1px)}
.btn-analyze:disabled{opacity:0.4;cursor:not-allowed;transform:none}
.result-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:60px 24px;color:var(--muted);min-height:400px;gap:12px}
.result-empty h3{font-family:'Outfit',sans-serif;font-size:18px;color:var(--text)}
.verdict-card{margin-bottom:16px;position:relative;overflow:hidden}
.verdict-card.aman{border-color:rgba(16,185,129,0.3);background:linear-gradient(135deg,rgba(16,185,129,0.08),rgba(18,18,20,0.6))}
.verdict-card.waspada{border-color:rgba(245,158,11,0.3);background:linear-gradient(135deg,rgba(245,158,11,0.08),rgba(18,18,20,0.6))}
.verdict-card.bahaya{border-color:rgba(239,68,68,0.3);background:linear-gradient(135deg,rgba(239,68,68,0.08),rgba(18,18,20,0.6))}
.verdict-header{display:flex;align-items:flex-start;gap:16px;margin-bottom:16px}
.verdict-emoji{font-size:40px;line-height:1}
.verdict-info h2{font-family:'Outfit',sans-serif;font-size:20px;font-weight:700;margin-bottom:4px}
.verdict-info p{font-size:13px;color:var(--muted);line-height:1.5}
.score-gauge-wrap{display:flex;justify-content:center;margin:8px 0}
.score-gauge{width:180px;height:110px}
.gauge-fill{transition:stroke-dashoffset 1.5s cubic-bezier(0.4,0,0.2,1)}
.analysis-meta{display:flex;justify-content:center;gap:16px;font-size:12px;color:var(--muted)}
.analysis-meta span{display:flex;align-items:center;gap:4px}
.demo-badge{color:var(--c-amber)!important;font-weight:600}
.indicators-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px}
.indicator-card{background:rgba(18,18,20,0.6);border:1px solid var(--border);border-radius:12px;padding:16px;transition:0.2s}
.indicator-card:hover{border-color:var(--border-hover);transform:translateY(-1px)}
.indicator-card.ind-good{border-left:3px solid var(--c-emerald)}
.indicator-card.ind-warn{border-left:3px solid var(--c-amber)}
.indicator-card.ind-bad{border-left:3px solid var(--c-rose)}
.ind-header{display:flex;align-items:center;gap:8px;margin-bottom:10px;color:var(--muted)}
.ind-name{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.04em}
.ind-score{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.ind-bar-bg{flex:1;height:6px;background:var(--surface3);border-radius:6px;overflow:hidden}
.ind-bar-fill{height:100%;border-radius:6px;transition:width 1s ease}
.ind-score-val{font-family:'Outfit',sans-serif;font-size:18px;font-weight:700;min-width:28px;text-align:right}
.ind-status{font-size:13px;font-weight:600;margin-bottom:4px}
.ind-detail{font-size:11px;line-height:1.4}
.rekomendasi-card h3{font-family:'Outfit',sans-serif;font-size:16px;display:flex;align-items:center;gap:8px;margin-bottom:14px}
.rekomendasi-card ul{list-style:none;display:flex;flex-direction:column;gap:10px}
.rekomendasi-card li{display:flex;align-items:flex-start;gap:10px;font-size:13px;line-height:1.5;background:var(--surface2);padding:12px 14px;border-radius:10px}
.muted{color:var(--muted)}
.spin{animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.fade-in{animation:fi 0.3s ease-out}
@keyframes fi{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:1024px){.det-layout{grid-template-columns:1fr}}
</style>
