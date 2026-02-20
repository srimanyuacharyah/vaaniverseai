/* ═══════════════════════════════════════════════════════════
   Vaaniverse AI — Frontend JavaScript (Premium Edition)
   ═══════════════════════════════════════════════════════════ */

/* ── Sidebar & Navigation ── */
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebar-overlay').classList.toggle('active');
}

function showDashboard() {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('main-dashboard').style.display = 'block';
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector('[data-tab="dashboard"]').classList.add('active');
    if (window.innerWidth < 769) toggleSidebar();
}

function showFeature(name) {
    document.getElementById('main-dashboard').style.display = 'none';
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById('tab-' + name);
    if (panel) panel.classList.add('active');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const nav = document.querySelector('[data-tab="' + name + '"]');
    if (nav) nav.classList.add('active');
    if (window.innerWidth < 769) toggleSidebar();
}

/* ── Helpers ── */
function showStatus(id, msg, type) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = msg;
    el.className = 'status visible ' + type;
}
function setLoading(btn, loading) {
    if (!btn) return;
    if (loading) { btn.classList.add('loading'); btn.disabled = true; }
    else { btn.classList.remove('loading'); btn.disabled = false; }
}
function getAuthHeaders() {
    return { 'Authorization': 'Bearer ' + authToken };
}

function getAudioUrl(path) {
    if (!path) return '';
    const connector = path.includes('?') ? '&' : '?';
    return `${path}${connector}token=${authToken}&t=${Date.now()}`;
}

/* ═══════════ AUTH ═══════════ */
let authMode = 'login';
let authToken = localStorage.getItem('vaaniverse_token') || '';
let currentUser = null;

function openLoginModal() { document.getElementById('login-modal').style.display = 'flex'; }
function closeLoginModal() { document.getElementById('login-modal').style.display = 'none'; }

function setAuthMode(mode) {
    authMode = mode;
    const isLanding = !!document.getElementById('auth-landing-overlay')?.style.display !== 'none';
    document.getElementById('auth-title').textContent = mode === 'login' ? 'Login' : 'Sign Up';
    const lEmail = document.getElementById('landing-email-group');
    const mEmail = document.getElementById('auth-email-group');
    if (lEmail) lEmail.style.display = mode === 'signup' ? 'block' : 'none';
    if (mEmail) mEmail.style.display = mode === 'signup' ? 'block' : 'none';
    const lt = document.getElementById('landing-login-tab');
    const st = document.getElementById('landing-signup-tab');
    if (lt) lt.classList.toggle('active', mode === 'login');
    if (st) st.classList.toggle('active', mode === 'signup');
    const lb = document.getElementById('auth-login-btn');
    const sb = document.getElementById('auth-signup-btn');
    if (lb) lb.classList.toggle('active', mode === 'login');
    if (sb) sb.classList.toggle('active', mode === 'signup');
    const landBtn = document.getElementById('landing-auth-btn');
    const modalBtn = document.getElementById('auth-submit-btn');
    if (landBtn) landBtn.querySelector('.btn-text').textContent = mode === 'login' ? '🔐 Login' : '✨ Sign Up';
    if (modalBtn) modalBtn.querySelector('.btn-text').textContent = mode === 'login' ? '🔐 Login' : '✨ Sign Up';
}

async function doAuth() {
    const btn = document.getElementById('auth-submit-btn'), statusId = 'auth-status';
    const endpoint = authMode === 'login' ? '/login' : '/register';
    await performAuth(endpoint, statusId, btn, false);
}
async function doLandingAuth() {
    const btn = document.getElementById('landing-auth-btn'), statusId = 'landing-auth-status';
    const endpoint = authMode === 'login' ? '/login' : '/register';
    await performAuth(endpoint, statusId, btn, true);
}

async function performAuth(endpoint, statusId, btn, isLanding) {
    setLoading(btn, true);
    const prefix = isLanding ? 'landing-' : 'auth-';
    const body = new FormData();
    body.append('username', document.getElementById(prefix + 'username').value);
    body.append('password', document.getElementById(prefix + 'password').value);
    if (authMode === 'signup') body.append('email', document.getElementById(prefix + 'email')?.value || '');
    try {
        const res = await fetch(endpoint, { method: 'POST', body });
        const data = await res.json();
        if (data.ok) {
            authToken = data.token; currentUser = data.user;
            localStorage.setItem('vaaniverse_token', authToken);
            showStatus(statusId, '✅ Welcome, ' + (data.user?.username || 'User') + '!', 'success');
            updateLoginUI();
            if (isLanding) {
                setTimeout(() => {
                    document.getElementById('auth-landing-overlay').style.opacity = '0';
                    setTimeout(() => document.getElementById('auth-landing-overlay').style.display = 'none', 500);
                }, 600);
            } else { setTimeout(closeLoginModal, 800); }
        } else { showStatus(statusId, '❌ ' + (data.error || 'Authentication failed'), 'error'); }
    } catch (e) { showStatus(statusId, '❌ ' + (e.message || 'Server error'), 'error'); }
    setLoading(btn, false);
}

function updateLoginUI() {
    if (currentUser) {
        document.body.classList.add('authenticated');
        document.getElementById('main-app').style.display = 'flex';
        document.getElementById('auth-landing-overlay').style.display = 'none';
        const uname = document.getElementById('sidebar-username');
        const uavatar = document.getElementById('user-avatar-letter');
        if (uname) uname.textContent = currentUser.username;
        if (uavatar) uavatar.textContent = currentUser.username.charAt(0).toUpperCase();
        loadHistory();
    } else {
        document.body.classList.remove('authenticated');
        document.getElementById('main-app').style.display = 'none';
        document.getElementById('auth-landing-overlay').style.display = 'flex';
    }
}

function doLogout() {
    authToken = ''; currentUser = null;
    localStorage.removeItem('vaaniverse_token');
    updateLoginUI();
}

async function checkAuth() {
    if (!authToken) { authToken = localStorage.getItem('vaaniverse_token') || ''; if (!authToken) return; }
    try {
        const res = await fetch('/me', { headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok) { currentUser = data.user; updateLoginUI(); }
        else { authToken = ''; localStorage.removeItem('vaaniverse_token'); }
    } catch (e) { /* not logged in */ }
}

/* ═══════════ TRANSLATE ═══════════ */
async function doTranslate(e) {
    const btn = (e && e.currentTarget) || document.getElementById('translate-btn'); setLoading(btn, true);
    const body = new FormData();
    body.append('text', document.getElementById('translate-text').value);
    body.append('src', document.getElementById('translate-src').value);
    body.append('tgt', document.getElementById('translate-tgt').value);
    try {
        const res = await fetch('/translate', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        document.getElementById('translate-output').textContent = data.translated || data.error || 'Translation failed';
        document.getElementById('translate-result').classList.add('visible');
        document.getElementById('batch-result').classList.remove('visible');
    } catch (e) { document.getElementById('translate-output').textContent = 'Error: ' + (e.message || 'Unknown error'); document.getElementById('translate-result').classList.add('visible'); }
    setLoading(btn, false);
}
async function doBatchTranslate(e) {
    const btn = (e && e.currentTarget) || document.getElementById('batch-translate-btn'); setLoading(btn, true);
    const body = new FormData(); body.append('text', document.getElementById('translate-text').value);
    try {
        const res = await fetch('/batch-translate', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        let html = ''; for (const [lang, translated] of Object.entries(data.translations || {})) html += '<span class="lang-tag">' + lang + '</span> ' + translated + '\n\n';
        document.getElementById('batch-output').innerHTML = html || 'No translations found';
        document.getElementById('batch-result').classList.add('visible');
        document.getElementById('translate-result').classList.remove('visible');
    } catch (e) { document.getElementById('batch-output').textContent = 'Error: ' + (e.message || 'Batch translate failed'); document.getElementById('batch-result').classList.add('visible'); }
    setLoading(btn, false);
}

/* ═══════════ TTS ═══════════ */
async function doSpeak(e) {
    const btn = (e && e.currentTarget) || document.getElementById('tts-btn'); setLoading(btn, true);
    showStatus('tts-status', '⏳ Generating speech...', 'info');
    const body = new FormData();
    body.append('text', document.getElementById('tts-text').value);
    body.append('lang', document.getElementById('tts-lang').value);
    body.append('gender', document.getElementById('tts-gender').value);
    body.append('backend', document.getElementById('tts-backend').value);
    try {
        const res = await fetch('/speak', { method: 'POST', body, headers: getAuthHeaders() });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error || 'TTS failed'); }
        const blob = await res.blob(); const url = URL.createObjectURL(blob);
        document.getElementById('tts-audio').src = url;
        document.getElementById('tts-player').style.display = 'block';
        document.getElementById('tts-audio').play();
        showStatus('tts-status', '✅ Speech generated!', 'success');
    } catch (e) { showStatus('tts-status', '❌ ' + (e.message || 'Synthesis failed'), 'error'); }
    setLoading(btn, false);
}

/* ═══════════ VOICE TRANSLATOR ═══════════ */
let transMode = 'text';
function setTranslatorMode(mode) {
    transMode = mode;
    document.getElementById('translator-text-ui').style.display = mode === 'text' ? 'block' : 'none';
    document.getElementById('translator-record-ui').style.display = mode === 'record' ? 'block' : 'none';
    document.getElementById('translator-upload-ui').style.display = mode === 'upload' ? 'block' : 'none';
    document.getElementById('trans-mode-text').classList.toggle('active', mode === 'text');
    document.getElementById('trans-mode-record').classList.toggle('active', mode === 'record');
    document.getElementById('trans-mode-upload').classList.toggle('active', mode === 'upload');
}

async function doTranslateText(e) {
    const btn = (e && e.currentTarget) || document.getElementById('trans-text-btn');
    const text = document.getElementById('trans-text-input').value;
    if (!text) { showStatus('trans-status', '⚠️ Enter text first', 'error'); return; }
    setLoading(btn, true); showStatus('trans-status', '⏳ Translating...', 'info');
    const body = new FormData();
    body.append('text', text); body.append('src_lang', 'auto');
    body.append('tgt_lang', document.getElementById('trans-tgt-lang').value);
    body.append('gender', 'female');
    try {
        const res = await fetch('/voice-translate', { method: 'POST', body, headers: getAuthHeaders() });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error || 'Translation failed'); }
        const translated = decodeURIComponent(res.headers.get('X-Translated-Text') || '');
        document.getElementById('trans-original').textContent = text;
        document.getElementById('trans-translated').textContent = translated || '(No translation)';
        const blob = await res.blob(); const url = URL.createObjectURL(blob);
        document.getElementById('trans-audio').src = url;
        document.getElementById('trans-player').style.display = 'block';
        document.getElementById('trans-result').style.display = 'block';
        document.getElementById('trans-audio').play();
        showStatus('trans-status', '✅ Success!', 'success');
    } catch (e) { showStatus('trans-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

function onTranslatorFileSelect() {
    const f = document.getElementById('trans-file').files[0];
    if (f) document.getElementById('trans-file-label').innerHTML = '📁 <strong>' + f.name + '</strong><br><small>' + (f.size / 1024).toFixed(1) + ' KB</small>';
}

let transRecorder = null, transChunks = [], transBlob = null, isTransRecording = false, transStream = null, transAnimFrame = null;

async function toggleTranslatorRecording() {
    if (isTransRecording) { stopTranslatorRecording(); return; }
    try {
        transStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        transRecorder = new MediaRecorder(transStream);
        transChunks = [];
        transRecorder.ondataavailable = e => { if (e.data.size > 0) transChunks.push(e.data); };
        transRecorder.onstop = () => { transBlob = new Blob(transChunks, { type: 'audio/webm' }); transStream.getTracks().forEach(t => t.stop()); doTranslateRecorded(); };
        transRecorder.start(); isTransRecording = true;
        document.getElementById('trans-status-text').textContent = 'Recording... Tap to stop.';
        document.getElementById('trans-record-btn').classList.add('recording');
    } catch (e) { showStatus('trans-status', '❌ Mic error: ' + (e.message || 'Permission denied'), 'error'); }
}
function stopTranslatorRecording() {
    if (transRecorder && transRecorder.state !== 'inactive') transRecorder.stop();
    isTransRecording = false;
    document.getElementById('trans-status-text').textContent = 'Processing...';
    document.getElementById('trans-record-btn').classList.remove('recording');
}

async function doTranslateRecorded() {
    if (!transBlob) return;
    showStatus('trans-status', '⏳ Transcribing & Translating...', 'info');
    const body = new FormData();
    body.append('file', new File([transBlob], 'recording.webm', { type: 'audio/webm' }));
    body.append('tgt_lang', document.getElementById('trans-tgt-lang').value);
    body.append('src_lang', 'auto');
    await sendTranslateRequest(body);
}
async function doTranslateUpload(e) {
    const btn = (e && e.currentTarget) || document.getElementById('trans-upload-btn');
    const f = document.getElementById('trans-file').files[0];
    if (!f) { showStatus('trans-status', '⚠️ Select a file first', 'error'); return; }
    setLoading(btn, true);
    showStatus('trans-status', '⏳ Transcribing & Translating...', 'info');
    const body = new FormData(); body.append('file', f);
    body.append('tgt_lang', document.getElementById('trans-tgt-lang').value);
    body.append('src_lang', 'auto');
    await sendTranslateRequest(body);
    setLoading(btn, false);
}
async function sendTranslateRequest(body) {
    try {
        const res = await fetch('/voice-translate-audio', { method: 'POST', body, headers: getAuthHeaders() });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error || 'Server error'); }
        const transcribed = decodeURIComponent(res.headers.get('X-Transcribed-Text') || '');
        const translated = decodeURIComponent(res.headers.get('X-Translated-Text') || '');
        document.getElementById('trans-original').textContent = transcribed || '(No speech detected)';
        document.getElementById('trans-translated').textContent = translated || '...';
        const blob = await res.blob(); const url = URL.createObjectURL(blob);
        document.getElementById('trans-audio').src = url;
        document.getElementById('trans-player').style.display = 'block';
        document.getElementById('trans-result').style.display = 'block';
        document.getElementById('trans-audio').play();
        showStatus('trans-status', '✅ Success!', 'success');
    } catch (e) { showStatus('trans-status', '❌ ' + e.message, 'error'); }
}

/* ═══════════ WEB AUDIO INSTRUMENTAL ENGINE ═══════════ */
const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx = null, instrumentalPlaying = false, instrumentalNodes = [];
function getAudioCtx() { if (!audioCtx) audioCtx = new AudioCtx(); return audioCtx; }
const NOTE_FREQ = { C: 261.63, D: 293.66, E: 329.63, F: 349.23, G: 392.00, A: 440.00, B: 493.88 };
function noteFreq(note, octave) { const base = NOTE_FREQ[note[0]] || 261.63; let freq = base * Math.pow(2, octave - 4); if (note.includes('m')) freq *= 0.9438; return freq; }

function createDrumPattern(ctx, dest, bpm, pattern, duration) {
    const beatDur = 60 / bpm, totalBeats = Math.floor(duration / beatDur);
    for (let i = 0; i < totalBeats; i++) {
        const time = i * beatDur;
        if (i % 4 === 0 || i % 4 === 2) {
            const osc = ctx.createOscillator(), gain = ctx.createGain();
            osc.type = 'sine'; osc.frequency.setValueAtTime(150, ctx.currentTime + time);
            osc.frequency.exponentialRampToValueAtTime(50, ctx.currentTime + time + 0.1);
            gain.gain.setValueAtTime(0.5, ctx.currentTime + time);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + 0.15);
            osc.connect(gain); gain.connect(dest);
            osc.start(ctx.currentTime + time); osc.stop(ctx.currentTime + time + 0.15);
            instrumentalNodes.push(osc);
        }
        if (i % 4 === 1 || i % 4 === 3) {
            const noise = ctx.createBufferSource(), buf = ctx.createBuffer(1, ctx.sampleRate * 0.1, ctx.sampleRate);
            const data = buf.getChannelData(0); for (let j = 0; j < data.length; j++) data[j] = Math.random() * 2 - 1;
            noise.buffer = buf; const gain = ctx.createGain();
            gain.gain.setValueAtTime(0.3, ctx.currentTime + time);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + 0.08);
            const filter = ctx.createBiquadFilter(); filter.type = 'highpass'; filter.frequency.value = 5000;
            noise.connect(filter); filter.connect(gain); gain.connect(dest);
            noise.start(ctx.currentTime + time); noise.stop(ctx.currentTime + time + 0.1);
            instrumentalNodes.push(noise);
        }
    }
}
function createBassLine(ctx, dest, bpm, chords, duration, vol) {
    const beatDur = 60 / bpm, barDur = beatDur * 4, totalBars = Math.floor(duration / barDur);
    for (let bar = 0; bar < totalBars; bar++) {
        const chord = chords[bar % chords.length], freq = noteFreq(chord, 2), time = bar * barDur;
        for (let beat = 0; beat < 4; beat++) {
            const osc = ctx.createOscillator(), gain = ctx.createGain();
            osc.type = 'sawtooth'; const f = beat % 2 === 0 ? freq : freq * 1.5;
            osc.frequency.setValueAtTime(f, ctx.currentTime + time + beat * beatDur);
            gain.gain.setValueAtTime(vol * 0.4, ctx.currentTime + time + beat * beatDur);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + beat * beatDur + beatDur * 0.8);
            const filter = ctx.createBiquadFilter(); filter.type = 'lowpass'; filter.frequency.value = 300;
            osc.connect(filter); filter.connect(gain); gain.connect(dest);
            osc.start(ctx.currentTime + time + beat * beatDur); osc.stop(ctx.currentTime + time + beat * beatDur + beatDur * 0.8);
            instrumentalNodes.push(osc);
        }
    }
}
function createChordPad(ctx, dest, bpm, chords, duration, vol, type) {
    const barDur = (60 / bpm) * 4, totalBars = Math.floor(duration / barDur);
    for (let bar = 0; bar < totalBars; bar++) {
        const chord = chords[bar % chords.length], baseFreq = noteFreq(chord, 4), time = bar * barDur;
        [1, 1.25, 1.5].forEach(mult => {
            const osc = ctx.createOscillator(), gain = ctx.createGain();
            osc.type = type === 'piano' ? 'triangle' : 'sine';
            osc.frequency.setValueAtTime(baseFreq * mult, ctx.currentTime + time);
            gain.gain.setValueAtTime(vol * 0.15, ctx.currentTime + time);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + barDur * 0.95);
            osc.connect(gain); gain.connect(dest);
            osc.start(ctx.currentTime + time); osc.stop(ctx.currentTime + time + barDur);
            instrumentalNodes.push(osc);
        });
    }
}
function playInstrumental(config) {
    stopInstrumental();
    const ctx = getAudioCtx(), master = ctx.createGain(); master.gain.value = 0.6; master.connect(ctx.destination);
    const chords = config.chord_progression || ['C', 'G', 'Am', 'F'];
    const dur = Math.min(config.duration || 120, 180), inst = config.instruments || {};
    if (inst.drums?.enabled) createDrumPattern(ctx, master, config.bpm, inst.drums.pattern, dur);
    if (inst.bass?.enabled) createBassLine(ctx, master, config.bpm, chords, dur, inst.bass.volume);
    if (inst.piano?.enabled) createChordPad(ctx, master, config.bpm, chords, dur, inst.piano.volume, 'piano');
    if (inst.guitar?.enabled) createChordPad(ctx, master, config.bpm, chords, dur, inst.guitar.volume, 'guitar');
    instrumentalPlaying = true;
}
function stopInstrumental() { instrumentalNodes.forEach(n => { try { n.stop(); } catch (e) { } }); instrumentalNodes = []; instrumentalPlaying = false; }

/* ═══════════ SONG GENERATOR ═══════════ */
let songMode = 'generate', selectedGenre = 'bollywood', lastLyrics = '';
function setSongMode(mode) {
    songMode = mode;
    document.getElementById('song-generate-mode').style.display = mode === 'generate' ? 'block' : 'none';
    document.getElementById('song-custom-mode').style.display = mode === 'custom' ? 'block' : 'none';
    document.getElementById('song-mode-generate').classList.toggle('active', mode === 'generate');
    document.getElementById('song-mode-custom').classList.toggle('active', mode === 'custom');
    document.getElementById('song-mode-instrumental').classList.toggle('active', mode === 'instrumental');
    document.getElementById('vocal-check-group').style.display = mode === 'instrumental' ? 'none' : 'block';
    document.getElementById('instrumental-info').style.display = mode === 'instrumental' ? 'block' : 'none';
}
function selectGenre(gid) {
    selectedGenre = gid;
    document.querySelectorAll('#genre-grid .genre-card').forEach(c => c.classList.toggle('active', c.dataset.genre === gid));
    const bpmMap = { bollywood: 120, pop: 110, rock: 130, lofi: 75, classical: 90, devotional: 80, hiphop: 140, romantic: 85 };
    if (bpmMap[gid]) { document.getElementById('song-bpm').value = bpmMap[gid]; document.getElementById('bpm-val').textContent = bpmMap[gid]; }
}

async function doGenerateSong(e) {
    const btn = (e && e.currentTarget) || document.getElementById('song-gen-btn'); setLoading(btn, true);
    showStatus('song-status', '⏳ Creating your song with instrumentals...', 'info');
    const body = new FormData();
    body.append('gender', document.getElementById('song-gender').value);
    body.append('with_audio', document.getElementById('song-audio-check').checked ? 'on' : 'off');
    body.append('full_length', 'on'); body.append('genre', selectedGenre);
    body.append('bpm', document.getElementById('song-bpm').value);
    body.append('instruments_drums', document.getElementById('inst-drums').checked ? 'on' : 'off');
    body.append('instruments_bass', document.getElementById('inst-bass').checked ? 'on' : 'off');
    body.append('instruments_guitar', document.getElementById('inst-guitar').checked ? 'on' : 'off');
    body.append('instruments_piano', document.getElementById('inst-piano').checked ? 'on' : 'off');
    body.append('instruments_synth', document.getElementById('inst-synth').checked ? 'on' : 'off');
    body.append('duration', '120');
    if (songMode === 'instrumental') { body.append('instrumental_only', 'on'); body.append('theme', 'love'); body.append('lang', 'hi'); }
    else if (songMode === 'custom') { body.append('custom_lyrics', document.getElementById('song-custom-lyrics').value); body.append('lang', document.getElementById('song-custom-lang').value); body.append('theme', 'love'); }
    else { body.append('theme', document.getElementById('song-theme').value); body.append('lang', document.getElementById('song-lang').value); body.append('genre_description', document.getElementById('song-genre-desc').value); }
    try {
        const res = await fetch('/generate-song', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok) {
            lastLyrics = data.lyrics;
            document.getElementById('song-lyrics').textContent = data.lyrics;
            document.getElementById('translate-lyrics-btn').style.display = 'inline-flex';
            document.getElementById('karaoke-lyrics-btn').style.display = 'inline-flex';
            if (data.has_audio) {
                const audio = document.getElementById('song-audio');
                audio.src = getAudioUrl(data.audio_path || '/song-audio?lang=' + (songMode === 'custom' ? document.getElementById('song-custom-lang').value : document.getElementById('song-lang').value));
                document.getElementById('song-player').style.display = 'block';
                audio.play();
            } else if (data.instrumental_config) { playInstrumental(data.instrumental_config); }
            const viz = document.getElementById('melody-viz'); viz.innerHTML = '';
            (data.melody || []).forEach(note => {
                const bar = document.createElement('div'); bar.className = 'melody-bar';
                bar.style.height = Math.max(8, Math.min(100, ((note - 55) / 20) * 100)) + '%';
                viz.appendChild(bar);
            });
            document.getElementById('song-result').classList.add('visible');
            showStatus('song-status', '✅ Song created!', 'success');
        } else { showStatus('song-status', '❌ ' + (data.error || 'Failed'), 'error'); }
    } catch (e) { showStatus('song-status', '❌ ' + (e.message || 'Error occurred'), 'error'); stopInstrumental(); }
    setLoading(btn, false);
}

async function translateCurrentLyrics() {
    const lang = prompt("Enter target language code (e.g., hi, ta, te, bn, fr):", "hi");
    if (!lang) return;
    const btn = document.getElementById('translate-lyrics-btn'); setLoading(btn, true);
    try {
        const body = new FormData();
        body.append('text', lastLyrics);
        body.append('tgt', lang);
        const res = await fetch('/translate', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.translated) {
            lastLyrics = data.translated;
            document.getElementById('song-lyrics').innerHTML = data.translated.replace(/\n/g, '<br>');
            showStatus('song-status', '✅ Lyrics translated to ' + lang, 'success');
            // Show a "Re-Sing" button after translation
            if (!document.getElementById('resing-lyrics-btn')) {
                const resingBtn = document.createElement('button');
                resingBtn.id = 'resing-lyrics-btn';
                resingBtn.className = 'btn btn-secondary';
                resingBtn.innerHTML = '<span class="btn-text">🎤 AI Sing This</span>';
                resingBtn.onclick = doSingLyrics;
                document.getElementById('translate-lyrics-btn').parentNode.appendChild(resingBtn);
            }
        }
    } catch (e) { showStatus('song-status', '❌ Translation failed: ' + e.message, 'error'); }
    setLoading(btn, false);
}

async function doSingLyrics(e) {
    const btn = (e && e.currentTarget) || document.getElementById('sing-lyrics-btn'); setLoading(btn, true);
    showStatus('song-status', '⏳ AI is singing your translated lyrics...', 'info');
    const body = new FormData();
    body.append('lyrics', lastLyrics);
    body.append('lang', 'hi'); // Default or detection could be better
    body.append('gender', document.getElementById('song-gender').value);
    body.append('genre', selectedGenre);
    body.append('bpm', document.getElementById('song-bpm').value);

    try {
        const res = await fetch('/sing-lyrics', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok && data.audio_path) {
            const audio = document.getElementById('song-audio');
            audio.src = getAudioUrl(data.audio_path);
            document.getElementById('song-player').style.display = 'block';
            audio.play();
            showStatus('song-status', '✅ AI Singing complete!', 'success');
        } else { showStatus('song-status', '❌ ' + (data.error || 'Failed to sing'), 'error'); }
    } catch (e) { showStatus('song-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

function startKaraokeFromSong() {
    document.getElementById('karaoke-lyrics-input').value = lastLyrics;
    showFeature('karaoke');
}

/* ═══════════ VOICE CLONE ═══════════ */
let cloneInputMode = 'upload';
function setCloneInputMode(mode) {
    cloneInputMode = mode;
    document.getElementById('clone-upload-mode').style.display = mode === 'upload' ? 'block' : 'none';
    document.getElementById('clone-record-mode').style.display = mode === 'record' ? 'block' : 'none';
    document.getElementById('clone-mode-upload').classList.toggle('active', mode === 'upload');
    document.getElementById('clone-mode-record').classList.toggle('active', mode === 'record');
}
function onCloneFileSelect() {
    const f = document.getElementById('clone-file').files[0];
    if (f) document.getElementById('clone-upload-label').innerHTML = '🎤 <strong>' + f.name + '</strong><br><small>' + (f.size / 1024).toFixed(1) + ' KB</small>';
}
async function doCloneVoice(e) {
    const btn = (e && e.currentTarget) || document.getElementById('clone-voice-btn');
    if (!document.getElementById('clone-consent').checked) { showStatus('clone-status', '⚠️ You must provide consent.', 'error'); return; }
    let file = null;
    if (cloneInputMode === 'upload') { const fi = document.getElementById('clone-file'); if (!fi.files.length) { showStatus('clone-status', '⚠️ Upload a voice sample.', 'error'); return; } file = fi.files[0]; }
    else { if (!recordedBlob) { showStatus('clone-status', '⚠️ Record your voice first.', 'error'); return; } file = new File([recordedBlob], 'recording.webm', { type: 'audio/webm' }); }
    setLoading(btn, true); showStatus('clone-status', '⏳ Analyzing voice...', 'info');
    const body = new FormData();
    body.append('file', file); body.append('name', document.getElementById('clone-name').value);
    body.append('consent', 'on'); body.append('lang', document.getElementById('clone-lang').value);
    body.append('gender', document.getElementById('clone-gender').value);
    try {
        const res = await fetch('/clone-voice', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.success) {
            const p = data.profile || {};
            let info = 'Profile: ' + (p.name || '') + '\nVoice: ' + (p.edge_voice || '') + '\nLanguage: ' + (p.language || '') + '\nGender: ' + (p.gender || '');
            if (p.voice_analysis) info += '\nPitch: ' + (p.voice_analysis.pitch_hz || 'N/A') + ' Hz';
            document.getElementById('clone-profile-info').textContent = info;
            document.getElementById('clone-profile-result').classList.add('visible');
            document.getElementById('test-profile-name').value = p.name || 'myvoice';
            showStatus('clone-status', '✅ Voice profile created!', 'success');
        } else { showStatus('clone-status', '❌ ' + (data.error || 'Cloning failed'), 'error'); }
    } catch (e) { showStatus('clone-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}
async function doTestProfile(e) {
    const btn = (e && e.currentTarget) || document.getElementById('test-profile-btn');
    const name = document.getElementById('test-profile-name').value, text = document.getElementById('test-profile-text').value;
    if (!name || !text) { showStatus('test-profile-status', '⚠️ Enter name and text.', 'error'); return; }
    setLoading(btn, true); showStatus('test-profile-status', '⏳ Speaking...', 'info');
    const body = new FormData(); body.append('name', name); body.append('text', text);
    try {
        const res = await fetch('/speak-with-profile', { method: 'POST', body, headers: getAuthHeaders() });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error || 'Profile TTS failed'); }
        const blob = await res.blob(); document.getElementById('test-profile-audio').src = URL.createObjectURL(blob);
        document.getElementById('test-profile-player').style.display = 'block'; document.getElementById('test-profile-audio').play();
        showStatus('test-profile-status', '✅ Playing!', 'success');
    } catch (e) { showStatus('test-profile-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

/* ═══════════ RECORDING ═══════════ */
let mediaRecorder = null, recordedChunks = [], recordedBlob = null, isRecording = false, recStartTime = 0, recTimerInterval = null, recStream = null;
async function toggleRecording() {
    if (isRecording) { stopRecording(); return; }
    try {
        recStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(recStream); recordedChunks = [];
        mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data); };
        mediaRecorder.onstop = () => { recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' }); document.getElementById('rec-audio-preview').src = URL.createObjectURL(recordedBlob); document.getElementById('rec-preview').style.display = 'block'; recStream.getTracks().forEach(t => t.stop()); };
        mediaRecorder.start(); isRecording = true; recStartTime = Date.now();
        document.getElementById('rec-btn-icon').textContent = '⏹️'; document.getElementById('rec-btn-text').textContent = 'Stop Recording';
        document.getElementById('rec-start-btn').classList.add('recording');
        recTimerInterval = setInterval(() => { const s = Math.floor((Date.now() - recStartTime) / 1000); document.getElementById('rec-timer').textContent = String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }, 100);
    } catch (e) { showStatus('clone-status', '❌ Mic denied: ' + (e.message || 'Permission denied'), 'error'); }
}
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
    isRecording = false; clearInterval(recTimerInterval);
    document.getElementById('rec-btn-icon').textContent = '⏺️'; document.getElementById('rec-btn-text').textContent = 'Start Recording';
    document.getElementById('rec-start-btn').classList.remove('recording');
}

/* ═══════════ LEGENDARY VOICES ═══════════ */
let selectedLegendaryId = '';
function selectLegendary(vid) {
    selectedLegendaryId = vid; document.getElementById('legendary-panel').style.display = 'block';
    document.querySelectorAll('.legendary-card').forEach(c => c.classList.toggle('active', c.dataset.vid === vid));
    const card = document.querySelector('[data-vid="' + vid + '"]');
    document.getElementById('legend-name-display').textContent = card ? card.querySelector('.legendary-name').textContent : vid;
}
async function doSpeakLegendary(e) {
    const btn = (e && e.currentTarget) || document.getElementById('legendary-gen-btn');
    const text = document.getElementById('legend-text').value;
    if (!text || !selectedLegendaryId) { showStatus('legend-status', '⚠️ Select a voice and enter text.', 'error'); return; }
    setLoading(btn, true); showStatus('legend-status', '⏳ Generating legendary voice...', 'info');
    const body = new FormData(); body.append('voice_id', selectedLegendaryId); body.append('text', text);
    body.append('auto_translate', document.getElementById('legend-auto-translate').checked ? 'on' : 'off');
    try {
        const res = await fetch('/speak-legendary', { method: 'POST', body, headers: getAuthHeaders() });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error || 'Synthesis failed'); }
        const blob = await res.blob(); document.getElementById('legend-audio').src = URL.createObjectURL(blob);
        document.getElementById('legend-player').style.display = 'block'; document.getElementById('legend-audio').play();
        showStatus('legend-status', '✅ Legendary voice generated!', 'success');
    } catch (e) { showStatus('legend-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

/* ═══════════ AUDIO STUDIO ═══════════ */
let selectedEffect = 'enhance';
const effectDescs = { pitch_up: '🐿️ Raise pitch higher', pitch_down: '🗿 Lower pitch deeper', speed_up: '⏩ Speed up audio', slow_down: '🐌 Slow down audio', enhance: '✨ Boost & normalize volume', echo: '🏔️ Add echo/reverb', reverse: '🔄 Play backwards', robot: '🤖 Robotic voice effect' };
function selectEffect(eid) { selectedEffect = eid; document.querySelectorAll('#effects-grid .genre-card').forEach(c => c.classList.toggle('active', c.dataset.effect === eid)); document.getElementById('effect-desc').textContent = effectDescs[eid] || ''; }
function onStudioFileSelect() {
    const f = document.getElementById('studio-file').files[0];
    if (f) { document.getElementById('studio-upload-label').innerHTML = '🎧 <strong>' + f.name + '</strong><br><small>' + (f.size / 1024).toFixed(1) + ' KB</small>'; document.getElementById('studio-original-audio').src = URL.createObjectURL(f); document.getElementById('studio-original-player').style.display = 'block'; }
}
async function doEditAudio(e) {
    const btn = (e && e.currentTarget) || document.getElementById('studio-gen-btn'), fi = document.getElementById('studio-file');
    if (!fi.files.length) { showStatus('studio-status', '⚠️ Upload audio first.', 'error'); return; }
    setLoading(btn, true); showStatus('studio-status', '⏳ Applying ' + selectedEffect + '...', 'info');
    const body = new FormData(); body.append('file', fi.files[0]); body.append('effect', selectedEffect);
    try {
        const res = await fetch('/edit-audio', { method: 'POST', body, headers: getAuthHeaders() });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error || 'Editing failed'); }
        const blob = await res.blob(); document.getElementById('studio-processed-audio').src = URL.createObjectURL(blob);
        document.getElementById('studio-processed-player').style.display = 'block'; document.getElementById('studio-processed-audio').play();
        showStatus('studio-status', '✅ Effect applied!', 'success');
    } catch (e) { showStatus('studio-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

async function doGenerateStory(e) {
    const btn = (e && e.currentTarget) || document.getElementById('story-gen-btn'); setLoading(btn, true);
    const theme = document.getElementById('story-theme').value;
    if (!theme) { showStatus('story-status', '⚠️ Enter a story theme', 'error'); setLoading(btn, false); return; }
    showStatus('story-status', '⏳ Crafting your story...', 'info');
    const body = new FormData(); body.append('theme', theme); body.append('lang', document.getElementById('story-lang').value);
    try {
        const res = await fetch('/generate-story', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('story-text').textContent = data.text;
            document.getElementById('story-result').style.display = 'block';
            const speakBody = new FormData(); speakBody.append('text', data.text); speakBody.append('lang', document.getElementById('story-lang').value);
            const speakRes = await fetch('/speak', { method: 'POST', body: speakBody, headers: getAuthHeaders() });
            if (speakRes.ok) {
                const b = await speakRes.blob();
                document.getElementById('story-audio').src = URL.createObjectURL(b);
                document.getElementById('story-player').style.display = 'block';
                document.getElementById('story-audio').play();
            }
            showStatus('story-status', '✅ Story ready!', 'success');
        } else { showStatus('story-status', '❌ ' + (data.error || 'Failed'), 'error'); }
    } catch (e) { showStatus('story-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

/* ═══════════ SENTIMENT ═══════════ */
async function doAnalyzeSentiment(e) {
    const btn = (e && e.currentTarget) || document.getElementById('sentiment-btn'); setLoading(btn, true);
    const text = document.getElementById('sentiment-text').value;
    if (!text) { showStatus('sentiment-status', '⚠️ Enter text', 'error'); setLoading(btn, false); return; }
    showStatus('sentiment-status', '🔍 Analyzing sentiment...', 'info');
    const body = new FormData(); body.append('text', text);
    try {
        const res = await fetch('/analyze-sentiment', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('sentiment-label').textContent = data.sentiment || 'Neutral';
            document.getElementById('sentiment-emoji').textContent = data.emoji || '🤔';
            document.getElementById('sentiment-score').textContent = 'Confidence: ' + (data.confidence || '0%');
            document.getElementById('sentiment-bar').style.width = (data.score * 100) + '%';
            document.getElementById('sentiment-result').style.display = 'block';
            showStatus('sentiment-status', '✅ Analysis complete!', 'success');
        } else { showStatus('sentiment-status', '❌ ' + (data.error || 'Failed'), 'error'); }
    } catch (e) { showStatus('sentiment-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

/* ═══════════ NEW: AI PODCAST ═══════════ */
async function doGeneratePodcast(e) {
    const btn = (e && e.currentTarget) || document.getElementById('podcast-gen-btn'); setLoading(btn, true);
    const topic = document.getElementById('podcast-topic').value;
    if (!topic) { showStatus('podcast-status', '⚠️ Enter a topic', 'error'); setLoading(btn, false); return; }
    showStatus('podcast-status', '⏳ Generating podcast...', 'info');
    const body = new FormData();
    body.append('topic', topic);
    body.append('lang', document.getElementById('podcast-lang').value);
    body.append('duration', document.getElementById('podcast-duration').value);
    try {
        const res = await fetch('/generate-podcast', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('podcast-script').textContent = data.script;
            document.getElementById('podcast-result').classList.add('visible');
            if (data.audio_path) {
                const audio = document.getElementById('podcast-audio');
                audio.src = getAudioUrl(data.audio_path);
                document.getElementById('podcast-player').style.display = 'block';
                audio.play();
            }
            showStatus('podcast-status', '✅ Podcast generated!', 'success');
        } else { showStatus('podcast-status', '❌ ' + (data.error || 'Failed'), 'error'); }
    } catch (e) { showStatus('podcast-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

/* ═══════════ NEW: KARAOKE MODE ═══════════ */
let karaokeTimer = null, karaokeLines = [], karaokeCurrent = 0;
function onKaraokeFileSelect() { const f = document.getElementById('karaoke-audio-file').files[0]; if (f) document.querySelector('[for="karaoke-audio-file"]').textContent = '🎵 ' + f.name; }

function startKaraoke(e) {
    const btn = (e && e.currentTarget) || document.getElementById('karaoke-start-btn');
    const lyrics = document.getElementById('karaoke-lyrics-input').value.trim();
    if (!lyrics) { showStatus('karaoke-status', '⚠️ Enter lyrics', 'error'); return; }
    karaokeLines = lyrics.split('\n').filter(l => l.trim());
    karaokeCurrent = 0;
    const speed = parseFloat(document.getElementById('karaoke-speed').value) || 4;
    const display = document.getElementById('karaoke-display');
    display.innerHTML = karaokeLines.map((line, i) => '<div class="karaoke-line" id="kl-' + i + '">' + line + '</div>').join('');
    document.getElementById('karaoke-display-area').style.display = 'block';
    // Play audio if uploaded
    const audioFile = document.getElementById('karaoke-audio-file').files[0];
    if (audioFile) {
        const audio = document.getElementById('karaoke-audio');
        audio.src = URL.createObjectURL(audioFile);
        document.getElementById('karaoke-audio-player').style.display = 'block';
        audio.play();
    }
    // Start highlighting
    highlightKaraokeLine();
    karaokeTimer = setInterval(() => {
        karaokeCurrent++;
        if (karaokeCurrent >= karaokeLines.length) { stopKaraoke(); return; }
        highlightKaraokeLine();
    }, speed * 1000);
}
function highlightKaraokeLine() {
    karaokeLines.forEach((_, i) => {
        const el = document.getElementById('kl-' + i);
        if (!el) return;
        el.classList.remove('active', 'done');
        if (i < karaokeCurrent) el.classList.add('done');
        else if (i === karaokeCurrent) { el.classList.add('active'); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    });
}
function stopKaraoke() {
    clearInterval(karaokeTimer); karaokeTimer = null;
    const audio = document.getElementById('karaoke-audio');
    if (audio) audio.pause();
    showStatus('karaoke-status', '⏹️ Karaoke stopped', 'info');
}

/* ═══════════ NEW: RINGTONE CREATOR ═══════════ */
let selectedRingtoneGenre = 'bollywood';
function selectRingtoneGenre(gid) {
    selectedRingtoneGenre = gid;
    document.querySelectorAll('#ringtone-genre-grid .genre-card').forEach(c => c.classList.toggle('active', c.dataset.genre === gid));
}
async function doGenerateRingtone(e) {
    const btn = (e && e.currentTarget) || document.getElementById('ringtone-gen-btn'); setLoading(btn, true);
    showStatus('ringtone-status', '⏳ Creating ringtone...', 'info');
    const body = new FormData();
    body.append('genre', selectedRingtoneGenre);
    body.append('duration', document.getElementById('ringtone-duration').value);
    body.append('bpm', document.getElementById('ringtone-bpm').value);
    try {
        const res = await fetch('/generate-ringtone', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok && data.audio_path) {
            const audio = document.getElementById('ringtone-audio');
            audio.src = getAudioUrl(data.audio_path);
            document.getElementById('ringtone-result').classList.add('visible');
            audio.play();
            showStatus('ringtone-status', '✅ Ringtone ready!', 'success');
        } else { showStatus('ringtone-status', '❌ ' + (data.error || 'Failed'), 'error'); }
    } catch (e) { showStatus('ringtone-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

/* ═══════════ NEW: AUDIO MASHUP ═══════════ */
function onMashupFileSelect(track) {
    const f = document.getElementById('mashup-file-' + track).files[0];
    if (f) document.getElementById('mashup-file-' + track + '-name').textContent = '✅ ' + f.name;
}
async function doMashup(e) {
    const btn = (e && e.currentTarget) || document.getElementById('mashup-gen-btn');
    const fa = document.getElementById('mashup-file-a').files[0], fb = document.getElementById('mashup-file-b').files[0];
    if (!fa || !fb) { showStatus('mashup-status', '⚠️ Upload both tracks', 'error'); return; }
    setLoading(btn, true); showStatus('mashup-status', '⏳ Mixing tracks...', 'info');
    const body = new FormData(); body.append('file_a', fa); body.append('file_b', fb);
    body.append('mix', document.getElementById('mashup-mix').value);
    try {
        const res = await fetch('/mashup', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.audio_path) {
            const audio = document.getElementById('mashup-audio');
            audio.src = getAudioUrl(data.audio_path);
            document.getElementById('mashup-result').classList.add('visible');
            audio.play();
            showStatus('mashup-status', '✅ Mashup created!', 'success');
        } else { showStatus('mashup-status', '❌ ' + (data.error || 'Failed to mix'), 'error'); }
    } catch (e) { showStatus('mashup-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}

/* ═══════════ NEW: VOICE MOOD BOARD ═══════════ */
async function doDetectMood(e) {
    const btn = (e && e.currentTarget) || document.getElementById('mood-gen-btn'); setLoading(btn, true);
    const text = document.getElementById('mood-text').value;
    if (!text) { showStatus('mood-status', '⚠️ Enter text', 'error'); setLoading(btn, false); return; }
    showStatus('mood-status', '🔍 Analyzing mood...', 'info');
    const body = new FormData(); body.append('text', text);
    try {
        const res = await fetch('/detect-mood', { method: 'POST', body, headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('mood-result-emoji').textContent = data.emoji || '🎭';
            document.getElementById('mood-result-label').textContent = data.mood || 'Unknown';
            document.getElementById('mood-result-desc').textContent = data.description || '';
            const tags = document.getElementById('mood-tags'); tags.innerHTML = '';
            (data.tags || []).forEach(t => { const span = document.createElement('span'); span.className = 'mood-tag'; span.textContent = t; tags.appendChild(span); });
            document.getElementById('mood-result').classList.add('visible');
            showStatus('mood-status', '✅ Mood detected!', 'success');
        } else { showStatus('mood-status', '❌ ' + (data.error || 'Detection failed'), 'error'); }
    } catch (e) { showStatus('mood-status', '❌ ' + (e.message || 'Error occurred'), 'error'); }
    setLoading(btn, false);
}
async function doSpeakMood(e) {
    const btn = (e && e.currentTarget) || document.getElementById('mood-speak-btn');
    const text = document.getElementById('mood-text').value;
    if (!text) return;
    showStatus('mood-status', '⏳ Generating voice...', 'info');
    const body = new FormData(); body.append('text', text); body.append('lang', 'en'); body.append('gender', 'female'); body.append('backend', 'edge');
    try {
        const res = await fetch('/speak', { method: 'POST', body, headers: getAuthHeaders() });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error || 'TTS failed'); }
        const blob = await res.blob();
        document.getElementById('mood-audio').src = URL.createObjectURL(blob);
        document.getElementById('mood-player').style.display = 'block';
        document.getElementById('mood-audio').play();
        showStatus('mood-status', '✅ Playing!', 'success');
    } catch (e) { showStatus('mood-status', '❌ ' + (e.message || 'Synthesis failed'), 'error'); }
}

/* ═══════════ HISTORY / LIBRARY ═══════════ */
let allHistory = [];
async function loadHistory() {
    if (!authToken) return;
    try {
        const res = await fetch('/history', { headers: getAuthHeaders() });
        const data = await res.json();
        if (data.ok && data.history) { allHistory = data.history; renderHistory(allHistory); }
    } catch (e) { console.error('History load failed', e); }
}
function renderHistory(items) {
    const list = document.getElementById('history-list');
    if (items.length === 0) { document.getElementById('history-empty').style.display = 'block'; list.innerHTML = ''; return; }
    document.getElementById('history-empty').style.display = 'none';
    const icons = { translate: '🌐', tts: '🔊', song: '🎵', clone: '🎤', voice_translate: '🌐', studio: '🎚️' };
    list.innerHTML = items.map(h => `<div class="history-card"><div class="history-type-icon">${icons[h.type] || '✨'}</div><div class="history-info"><span class="history-title">${h.title || 'Untitled'}</span><span class="history-meta">${h.type.replace(/_/g, ' ').toUpperCase()} • ${h.created_at}</span></div>${h.audio_path ? `<button class="btn btn-secondary btn-sm" onclick="playHistoryAudio(${h.id})">▶️</button>` : ''}</div>`).join('');
}
function filterHistory(query) { renderHistory(allHistory.filter(h => h.title.toLowerCase().includes(query.toLowerCase()) || h.type.toLowerCase().includes(query.toLowerCase()))); }
function playHistoryAudio(hid) { new Audio(getAudioUrl('/history-audio/' + hid)).play().catch(e => alert("Playback failed: " + e.message)); }

/* ═══════════ GUIDE & INIT ═══════════ */
function proceedToAuth() {
    const guide = document.getElementById('user-guide-overlay');
    guide.style.opacity = '0';
    setTimeout(() => { guide.style.display = 'none'; document.getElementById('auth-landing-overlay').style.display = 'flex'; }, 500);
}
async function translateGuide(lang) {
    if (lang === 'en') { renderGuideContent('en'); return; }
    const content = document.getElementById('guide-content').innerText;
    try { const res = await fetch('/translate', { method: 'POST', body: new URLSearchParams({ text: content, target: lang }) }); const data = await res.json(); if (data.ok) document.getElementById('guide-content').innerHTML = data.translated.split('\n').map(p => '<p>' + p + '</p>').join(''); } catch (e) { }
}
function renderGuideContent(lang) {
    if (lang === 'en') {
        document.getElementById('guide-title').innerText = "Welcome to Vaaniverse AI";
        document.getElementById('guide-content').innerHTML = '<p>Your all-in-one platform for voice intelligence:</p><ul><li><strong>🌐 Translate:</strong> Break language barriers</li><li><strong>🔊 TTS:</strong> 300+ lifelike voices</li><li><strong>🎤 Clone:</strong> Digital voice replicas</li><li><strong>🎵 Songs:</strong> AI singing & lyrics</li></ul>';
    }
}

window.onload = () => {
    setTimeout(() => {
        const splash = document.getElementById('splash-screen');
        if (splash) { splash.style.opacity = '0'; setTimeout(() => { splash.style.display = 'none'; if (!localStorage.getItem('vaaniverse_token')) { document.getElementById('user-guide-overlay').style.display = 'flex'; } else { checkAuth(); } }, 800); }
    }, 2000);
};
