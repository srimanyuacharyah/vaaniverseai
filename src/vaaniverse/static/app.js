/* ═══════════════════════════════════════════════════════════
   Vaaniverse AI — Frontend JavaScript
   Tab switching, API calls, Web Audio instrumental engine,
   MediaRecorder voice recording, legendary voices
   ═══════════════════════════════════════════════════════════ */

/* ── Tab switching ── */
function switchTab(tab) {
    document.body.classList.add('in-feature');
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    const btn = document.querySelector('[data-tab="' + tab + '"]');
    if (btn) btn.classList.add('active');
}

function showFeature(name) {
    switchTab(name);
}

function exitToDashboard() {
    document.body.classList.remove('in-feature');
}

/* ── Helpers ── */
function showStatus(id, msg, type) {
    const el = document.getElementById(id);
    el.textContent = msg;
    el.className = 'status visible ' + type;
}
function setLoading(btn, loading) {
    if (loading) { btn.classList.add('loading'); btn.disabled = true; }
    else { btn.classList.remove('loading'); btn.disabled = false; }
}

/* ── Voice Translate mode ── */
let vtMode = 'text';
function setVTMode(mode) {
    vtMode = mode;
    document.getElementById('vt-text-mode').style.display = mode === 'text' ? 'block' : 'none';
    document.getElementById('vt-audio-mode').style.display = mode === 'audio' ? 'block' : 'none';
    document.getElementById('vt-mode-text').classList.toggle('active', mode === 'text');
    document.getElementById('vt-mode-audio').classList.toggle('active', mode === 'audio');
}
function onVTFileSelect() {
    const f = document.getElementById('vt-file').files[0];
    if (f) document.getElementById('vt-upload-label').innerHTML = '🎙️ <strong>' + f.name + '</strong><br><small>' + (f.size / 1024).toFixed(1) + ' KB</small>';
}

/* ── Song mode ── */
let songMode = 'generate';
let selectedGenre = 'bollywood';
function setSongMode(mode) {
    songMode = mode;
    const isInstrumental = mode === 'instrumental';
    document.getElementById('song-generate-mode').style.display = mode === 'generate' ? 'block' : 'none';
    document.getElementById('song-custom-mode').style.display = mode === 'custom' ? 'block' : 'none';
    document.getElementById('song-mode-generate').classList.toggle('active', mode === 'generate');
    document.getElementById('song-mode-custom').classList.toggle('active', mode === 'custom');
    document.getElementById('song-mode-instrumental').classList.toggle('active', isInstrumental);
    document.getElementById('vocal-check-group').style.display = isInstrumental ? 'none' : 'block';
    document.getElementById('instrumental-info').style.display = isInstrumental ? 'block' : 'none';
}
function selectGenre(gid) {
    selectedGenre = gid;
    document.querySelectorAll('#genre-grid .genre-card').forEach(c => c.classList.toggle('active', c.dataset.genre === gid));
    const bpmMap = { bollywood: 120, pop: 110, rock: 130, lofi: 75, classical: 90, devotional: 80, hiphop: 140, indian_classical: 70, refreshing: 115, romantic: 85, mass: 150 };
    if (bpmMap[gid]) { document.getElementById('song-bpm').value = bpmMap[gid]; document.getElementById('bpm-val').textContent = bpmMap[gid]; }
}

/* ── Clone input mode ── */
let cloneInputMode = 'upload';
function setCloneInputMode(mode) {
    cloneInputMode = mode;
    document.getElementById('clone-upload-mode').style.display = mode === 'upload' ? 'block' : 'none';
    document.getElementById('clone-record-mode').style.display = mode === 'record' ? 'block' : 'none';
    document.getElementById('clone-mode-upload').classList.toggle('active', mode === 'upload');
    document.getElementById('clone-mode-record').classList.toggle('active', mode === 'record');
}

/* ══════════════════════════════════════════════════════════
   TRANSLATE
   ══════════════════════════════════════════════════════════ */
async function doTranslate() {
    const btn = event.currentTarget; setLoading(btn, true);
    const body = new FormData();
    body.append('text', document.getElementById('translate-text').value);
    body.append('src', document.getElementById('translate-src').value);
    body.append('tgt', document.getElementById('translate-tgt').value);
    try {
        const res = await fetch('/translate', { method: 'POST', body });
        const data = await res.json();
        document.getElementById('translate-output').textContent = data.translated || data.error;
        document.getElementById('translate-result').classList.add('visible');
        document.getElementById('batch-result').classList.remove('visible');
    } catch (e) { document.getElementById('translate-output').textContent = 'Error: ' + e.message; document.getElementById('translate-result').classList.add('visible'); }
    setLoading(btn, false);
}
async function doBatchTranslate() {
    const btn = event.currentTarget; setLoading(btn, true);
    const body = new FormData(); body.append('text', document.getElementById('translate-text').value);
    try {
        const res = await fetch('/batch-translate', { method: 'POST', body });
        const data = await res.json();
        let html = ''; for (const [lang, translated] of Object.entries(data.translations || {})) html += '<span class="lang-tag">' + lang + '</span> ' + translated + '\n\n';
        document.getElementById('batch-output').innerHTML = html;
        document.getElementById('batch-result').classList.add('visible');
        document.getElementById('translate-result').classList.remove('visible');
    } catch (e) { document.getElementById('batch-output').textContent = 'Error: ' + e.message; document.getElementById('batch-result').classList.add('visible'); }
    setLoading(btn, false);
}

/* ══════════════════ TTS ══════════════════ */
async function doSpeak() {
    const btn = event.currentTarget; setLoading(btn, true);
    showStatus('tts-status', '⏳ Generating speech...', 'info');
    const body = new FormData();
    body.append('text', document.getElementById('tts-text').value);
    body.append('lang', document.getElementById('tts-lang').value);
    body.append('gender', document.getElementById('tts-gender').value);
    body.append('backend', document.getElementById('tts-backend').value);
    try {
        const res = await fetch('/speak', { method: 'POST', body });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error); }
        const blob = await res.blob(); const url = URL.createObjectURL(blob);
        document.getElementById('tts-audio').src = url;
        document.getElementById('tts-player').style.display = 'block';
        document.getElementById('tts-audio').play();
        showStatus('tts-status', '✅ Speech generated!', 'success');
    } catch (e) { showStatus('tts-status', '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}

/* ══════════════════ VOICE TRANSLATE ══════════════════ */
/* ══════════════════ VOICE TRANSLATE (Consolidated into Translator Tab) ══════════════════ */
// Old function removed. Use doTranslateText / doTranslateRecorded / doTranslateUpload instead.

/* ══════════════════ NEW TRANSLATOR TAB (S2S) ══════════════════ */
let transMode = 'text'; // Default to text
function setTranslatorMode(mode) {
    transMode = mode;
    document.getElementById('translator-text-ui').style.display = mode === 'text' ? 'block' : 'none';
    document.getElementById('translator-record-ui').style.display = mode === 'record' ? 'block' : 'none';
    document.getElementById('translator-upload-ui').style.display = mode === 'upload' ? 'block' : 'none';

    document.getElementById('trans-mode-text').classList.toggle('active', mode === 'text');
    document.getElementById('trans-mode-record').classList.toggle('active', mode === 'record');
    document.getElementById('trans-mode-upload').classList.toggle('active', mode === 'upload');
}

async function doTranslateText() {
    const text = document.getElementById('trans-text-input').value;
    if (!text) { showStatus('trans-status', '⚠️ Enter text first', 'error'); return; }

    const btn = event.currentTarget; setLoading(btn, true);
    showStatus('trans-status', '⏳ Translating...', 'info');

    const body = new FormData();
    body.append('text', text);
    body.append('src_lang', 'auto');
    body.append('tgt_lang', document.getElementById('trans-tgt-lang').value);
    body.append('gender', 'female'); // Default

    try {
        const res = await fetch('/voice-translate', { method: 'POST', body });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error); }

        const translated = decodeURIComponent(res.headers.get('X-Translated-Text') || '');
        document.getElementById('trans-original').textContent = text;
        document.getElementById('trans-translated').textContent = translated || '(No translation)';

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = document.getElementById('trans-audio');
        audio.src = url;
        document.getElementById('trans-player').style.display = 'block';
        document.getElementById('trans-result').style.display = 'block';
        audio.play();
        showStatus('trans-status', '✅ Success!', 'success');
    } catch (e) { showStatus('trans-status', '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}

function onTranslatorFileSelect() {
    const f = document.getElementById('trans-file').files[0];
    if (f) document.getElementById('trans-file-label').innerHTML = '📁 <strong>' + f.name + '</strong><br><small>' + (f.size / 1024).toFixed(1) + ' KB</small>';
}

// MediaRecorder for Translator
let transRecorder = null;
let transChunks = [];
let transBlob = null;
let isTransRecording = false;
let transStream = null;
let transVizCtx = null, transVizCanvas = null, transVizAnalyser = null;
let transAnimFrame = null;

async function toggleTranslatorRecording() {
    if (isTransRecording) { stopTranslatorRecording(); return; }
    try {
        transStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        transRecorder = new MediaRecorder(transStream);
        transChunks = [];
        transRecorder.ondataavailable = e => { if (e.data.size > 0) transChunks.push(e.data); };
        transRecorder.onstop = async () => {
            transBlob = new Blob(transChunks, { type: 'audio/webm' });
            transStream.getTracks().forEach(t => t.stop());
            // Auto submit
            doTranslateRecorded();
        };
        transRecorder.start();
        isTransRecording = true;
        document.getElementById('trans-status-text').textContent = 'Recording... Tap to stop.';
        document.getElementById('trans-record-btn').classList.add('recording');
        setupTransViz(transStream);
    } catch (e) { showStatus('trans-status', '❌ Mic error: ' + e.message, 'error'); }
}

function stopTranslatorRecording() {
    if (transRecorder && transRecorder.state !== 'inactive') transRecorder.stop();
    isTransRecording = false;
    document.getElementById('trans-status-text').textContent = 'Processing...';
    document.getElementById('trans-record-btn').classList.remove('recording');
    if (transAnimFrame) cancelAnimationFrame(transAnimFrame);
}

function setupTransViz(stream) {
    const actx = getAudioCtx();
    const source = actx.createMediaStreamSource(stream);
    transVizAnalyser = actx.createAnalyser();
    transVizAnalyser.fftSize = 64;
    source.connect(transVizAnalyser);
    transVizCanvas = document.getElementById('trans-viz');
    // Simple mock viz since canvas might not be initialized properly in hidden tab
    if (!transVizCanvas.clientWidth) return;
    transVizCanvas.innerHTML = '<canvas width="' + transVizCanvas.clientWidth + '" height="60"></canvas>';
    const cvs = transVizCanvas.querySelector('canvas');
    const ctx = cvs.getContext('2d');
    const bufLen = transVizAnalyser.frequencyBinCount;
    const data = new Uint8Array(bufLen);
    function draw() {
        if (!isTransRecording) return;
        transAnimFrame = requestAnimationFrame(draw);
        transVizAnalyser.getByteFrequencyData(data);
        ctx.clearRect(0, 0, cvs.width, cvs.height);
        ctx.fillStyle = '#ec4899';
        const barW = cvs.width / bufLen;
        for (let i = 0; i < bufLen; i++) {
            const h = (data[i] / 255) * cvs.height;
            ctx.fillRect(i * barW, (cvs.height - h) / 2, barW - 1, h);
        }
    }
    draw();
}

async function doTranslateRecorded() {
    if (!transBlob) return;
    showStatus('trans-status', '⏳ Transcribing & Translating...', 'info');
    const body = new FormData();
    body.append('file', new File([transBlob], 'recording.webm', { type: 'audio/webm' }));
    body.append('tgt_lang', document.getElementById('trans-tgt-lang').value);
    body.append('src_lang', 'auto'); // Auto detect
    await sendTranslateRequest(body);
}

async function doTranslateUpload() {
    const f = document.getElementById('trans-file').files[0];
    if (!f) { showStatus('trans-status', '⚠️ Select a file first', 'error'); return; }
    const btn = event.currentTarget; setLoading(btn, true);
    showStatus('trans-status', '⏳ Transcribing & Translating...', 'info');
    const body = new FormData();
    body.append('file', f);
    body.append('tgt_lang', document.getElementById('trans-tgt-lang').value);
    body.append('src_lang', 'auto');
    await sendTranslateRequest(body);
    setLoading(btn, false);
}

async function sendTranslateRequest(body) {
    try {
        const res = await fetch('/voice-translate-audio', { method: 'POST', body });
        if (!res.ok) {
            const d = await res.json();
            throw new Error(d.error || 'Server error');
        }

        // Headers for text
        const transcribed = decodeURIComponent(res.headers.get('X-Transcribed-Text') || '');
        const translated = decodeURIComponent(res.headers.get('X-Translated-Text') || '');

        document.getElementById('trans-original').textContent = transcribed || '(No speech detected)';
        document.getElementById('trans-translated').textContent = translated || '...';

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = document.getElementById('trans-audio');
        audio.src = url;
        document.getElementById('trans-player').style.display = 'block';
        document.getElementById('trans-result').style.display = 'block';
        audio.play();
        showStatus('trans-status', '✅ Success!', 'success');
    } catch (e) {
        showStatus('trans-status', '❌ ' + e.message, 'error');
    }
}

/* ══════════════════════════════════════════════════════════
   WEB AUDIO INSTRUMENTAL ENGINE
   ══════════════════════════════════════════════════════════ */
const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;
let instrumentalPlaying = false;
let instrumentalNodes = [];

function getAudioCtx() { if (!audioCtx) audioCtx = new AudioCtx(); return audioCtx; }

// Note frequencies (C4=261.63)
const NOTE_FREQ = { C: 261.63, D: 293.66, E: 329.63, F: 349.23, G: 392.00, A: 440.00, B: 493.88 };
function noteFreq(note, octave) {
    const base = NOTE_FREQ[note[0]] || 261.63;
    const shift = octave - 4;
    let freq = base * Math.pow(2, shift);
    if (note.includes('m')) freq *= 0.9438; // minor approximation
    return freq;
}

function createDrumPattern(ctx, dest, bpm, pattern, duration) {
    const beatDur = 60 / bpm;
    const totalBeats = Math.floor(duration / beatDur);
    for (let i = 0; i < totalBeats; i++) {
        const time = i * beatDur;
        // Kick on 1,3 — snare on 2,4
        if (i % 4 === 0 || i % 4 === 2) {
            const osc = ctx.createOscillator(); const gain = ctx.createGain();
            osc.type = 'sine'; osc.frequency.setValueAtTime(150, ctx.currentTime + time);
            osc.frequency.exponentialRampToValueAtTime(50, ctx.currentTime + time + 0.1);
            gain.gain.setValueAtTime(0.5, ctx.currentTime + time);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + 0.15);
            osc.connect(gain); gain.connect(dest);
            osc.start(ctx.currentTime + time); osc.stop(ctx.currentTime + time + 0.15);
            instrumentalNodes.push(osc);
        }
        if (i % 4 === 1 || i % 4 === 3) {
            const noise = ctx.createBufferSource();
            const buf = ctx.createBuffer(1, ctx.sampleRate * 0.1, ctx.sampleRate);
            const data = buf.getChannelData(0);
            for (let j = 0; j < data.length; j++) data[j] = Math.random() * 2 - 1;
            noise.buffer = buf;
            const gain = ctx.createGain();
            gain.gain.setValueAtTime(0.3, ctx.currentTime + time);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + 0.08);
            const filter = ctx.createBiquadFilter(); filter.type = 'highpass'; filter.frequency.value = 5000;
            noise.connect(filter); filter.connect(gain); gain.connect(dest);
            noise.start(ctx.currentTime + time); noise.stop(ctx.currentTime + time + 0.1);
            instrumentalNodes.push(noise);
        }
        // Hi-hat on every beat
        if (pattern !== 'lofi' || i % 2 === 0) {
            const hh = ctx.createBufferSource();
            const hhBuf = ctx.createBuffer(1, ctx.sampleRate * 0.03, ctx.sampleRate);
            const hhData = hhBuf.getChannelData(0);
            for (let j = 0; j < hhData.length; j++) hhData[j] = Math.random() * 2 - 1;
            hh.buffer = hhBuf;
            const hhGain = ctx.createGain();
            hhGain.gain.setValueAtTime(0.15, ctx.currentTime + time);
            hhGain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + 0.03);
            const hhFilter = ctx.createBiquadFilter(); hhFilter.type = 'highpass'; hhFilter.frequency.value = 8000;
            hh.connect(hhFilter); hhFilter.connect(hhGain); hhGain.connect(dest);
            hh.start(ctx.currentTime + time); hh.stop(ctx.currentTime + time + 0.03);
            instrumentalNodes.push(hh);
        }
    }
}

function createBassLine(ctx, dest, bpm, chords, duration, vol) {
    const beatDur = 60 / bpm;
    const barDur = beatDur * 4;
    const totalBars = Math.floor(duration / barDur);
    for (let bar = 0; bar < totalBars; bar++) {
        const chord = chords[bar % chords.length];
        const freq = noteFreq(chord, 2);
        const time = bar * barDur;
        for (let beat = 0; beat < 4; beat++) {
            const osc = ctx.createOscillator(); const gain = ctx.createGain();
            osc.type = 'sawtooth';
            const f = beat % 2 === 0 ? freq : freq * 1.5;
            osc.frequency.setValueAtTime(f, ctx.currentTime + time + beat * beatDur);
            gain.gain.setValueAtTime(vol * 0.4, ctx.currentTime + time + beat * beatDur);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + beat * beatDur + beatDur * 0.8);
            const filter = ctx.createBiquadFilter(); filter.type = 'lowpass'; filter.frequency.value = 300;
            osc.connect(filter); filter.connect(gain); gain.connect(dest);
            osc.start(ctx.currentTime + time + beat * beatDur);
            osc.stop(ctx.currentTime + time + beat * beatDur + beatDur * 0.8);
            instrumentalNodes.push(osc);
        }
    }
}

function createChordPad(ctx, dest, bpm, chords, duration, vol, type) {
    const barDur = (60 / bpm) * 4;
    const totalBars = Math.floor(duration / barDur);
    for (let bar = 0; bar < totalBars; bar++) {
        const chord = chords[bar % chords.length];
        const baseFreq = noteFreq(chord, 4);
        const time = bar * barDur;
        [1, 1.25, 1.5].forEach(mult => {
            const osc = ctx.createOscillator(); const gain = ctx.createGain();
            osc.type = type === 'piano' ? 'triangle' : 'sine';
            osc.frequency.setValueAtTime(baseFreq * mult, ctx.currentTime + time);
            gain.gain.setValueAtTime(vol * 0.15, ctx.currentTime + time);
            gain.gain.setValueAtTime(vol * 0.15, ctx.currentTime + time + barDur * 0.7);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + time + barDur * 0.95);
            osc.connect(gain); gain.connect(dest);
            osc.start(ctx.currentTime + time); osc.stop(ctx.currentTime + time + barDur);
            instrumentalNodes.push(osc);
        });
    }
}

function createSynthLead(ctx, dest, bpm, chords, duration, vol) {
    const beatDur = 60 / bpm;
    const totalBeats = Math.floor(duration / beatDur);
    const scale = [1, 1.125, 1.25, 1.333, 1.5, 1.667, 1.875];
    for (let i = 0; i < totalBeats; i++) {
        if (Math.random() > 0.4) continue;
        const bar = Math.floor(i / 4);
        const chord = chords[bar % chords.length];
        const baseFreq = noteFreq(chord, 5);
        const f = baseFreq * scale[Math.floor(Math.random() * scale.length)];
        const time = i * beatDur;
        const osc = ctx.createOscillator(); const gain = ctx.createGain();
        osc.type = 'square'; osc.frequency.setValueAtTime(f, ctx.currentTime + time);
        gain.gain.setValueAtTime(vol * 0.08, ctx.currentTime + time);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + time + beatDur * 0.6);
        osc.connect(gain); gain.connect(dest);
        osc.start(ctx.currentTime + time); osc.stop(ctx.currentTime + time + beatDur * 0.6);
        instrumentalNodes.push(osc);
    }
}

function playInstrumental(config) {
    stopInstrumental();
    const ctx = getAudioCtx();
    const master = ctx.createGain(); master.gain.value = 0.6;
    const reverb = ctx.createGain(); reverb.gain.value = config.effects?.reverb || 0.3;
    master.connect(ctx.destination); reverb.connect(master);
    const chords = config.chord_progression || ['C', 'G', 'Am', 'F'];
    const dur = Math.min(config.duration || 120, 180);
    const inst = config.instruments || {};

    if (inst.drums?.enabled) createDrumPattern(ctx, master, config.bpm, inst.drums.pattern, dur);
    if (inst.bass?.enabled) createBassLine(ctx, master, config.bpm, chords, dur, inst.bass.volume);
    if (inst.piano?.enabled) createChordPad(ctx, master, config.bpm, chords, dur, inst.piano.volume, 'piano');
    if (inst.synth?.enabled) createSynthLead(ctx, master, config.bpm, chords, dur, inst.synth.volume);
    if (inst.guitar?.enabled) createChordPad(ctx, master, config.bpm, chords, dur, inst.guitar.volume, 'guitar');

    instrumentalPlaying = true;
}

function stopInstrumental() {
    instrumentalNodes.forEach(n => { try { n.stop(); } catch (e) { } });
    instrumentalNodes = [];
    instrumentalPlaying = false;
}

/* ══════════════════ SONG GENERATOR ══════════════════ */
async function doGenerateSong() {
    const btn = event.currentTarget; setLoading(btn, true);
    showStatus('song-status', '⏳ Creating your song with instrumentals...', 'info');
    const body = new FormData();
    body.append('gender', document.getElementById('song-gender').value);
    body.append('with_audio', document.getElementById('song-audio-check').checked ? 'on' : 'off');
    body.append('full_length', 'on');
    body.append('genre', selectedGenre);
    body.append('bpm', document.getElementById('song-bpm').value);
    body.append('instruments_drums', document.getElementById('inst-drums').checked ? 'on' : 'off');
    body.append('instruments_bass', document.getElementById('inst-bass').checked ? 'on' : 'off');
    body.append('instruments_guitar', document.getElementById('inst-guitar').checked ? 'on' : 'off');
    body.append('instruments_piano', document.getElementById('inst-piano').checked ? 'on' : 'off');
    body.append('instruments_synth', document.getElementById('inst-synth').checked ? 'on' : 'off');
    body.append('duration', '120');
    if (songMode === 'instrumental') {
        body.append('instrumental_only', 'on');
        body.append('theme', 'love'); body.append('lang', 'hi');
    } else if (songMode === 'custom') {
        body.append('custom_lyrics', document.getElementById('song-custom-lyrics').value);
        body.append('lang', document.getElementById('song-custom-lang').value);
        body.append('theme', 'love');
    } else {
        body.append('theme', document.getElementById('song-theme').value);
        body.append('lang', document.getElementById('song-lang').value);
        body.append('genre_description', document.getElementById('song-genre-desc').value);
    }
    try {
        const res = await fetch('/generate-song', { method: 'POST', body });
        const data = await res.json();
        if (data.ok) {
            lastLyrics = data.lyrics;
            document.getElementById('song-lyrics').textContent = data.lyrics;
            document.getElementById('translate-lyrics-btn').style.display = 'inline-flex';

            // ENHANCED: Unified Audio + Lyrics
            if (data.has_audio) {
                document.getElementById('song-player').style.display = 'block';
                document.getElementById('song-audio').src = data.audio_path;
                document.getElementById('song-audio').play();
                setupSpectrumViz(document.getElementById('song-audio'));
            } else if (data.instrumental_config) {
                playInstrumental(data.instrumental_config);
                showStatus('song-status', '🎵 Instrumentals playing!', 'info');
            }

            const viz = document.getElementById('melody-viz'); viz.innerHTML = '';
            (data.melody || []).forEach(note => {
                const bar = document.createElement('div'); bar.className = 'melody-bar';
                bar.style.height = Math.max(8, Math.min(100, ((note - 55) / 20) * 100)) + '%';
                viz.appendChild(bar);
            });
            document.getElementById('song-result').classList.add('visible');

            // Play instrumental backing (Web Audio API live preview)
            if (data.instrumental_config && !data.has_audio) {
                playInstrumental(data.instrumental_config);
                showStatus('song-status', '🎵 Instrumentals playing!', 'info');
            }

            // Vocal audio
            if (data.has_audio) {
                const lang = songMode === 'custom' ? document.getElementById('song-custom-lang').value : document.getElementById('song-lang').value;
                const audioRes = await fetch('/song-audio?lang=' + lang);
                if (audioRes.ok) {
                    const blob = await audioRes.blob(); const url = URL.createObjectURL(blob);
                    const audioEl = document.getElementById('song-audio');
                    audioEl.src = url;
                    document.getElementById('song-player').style.display = 'block';
                    audioEl.play();
                    // Spectrum visualizer
                    setupSpectrumViz(audioEl);
                }
            }
            showStatus('song-status', '✅ Song created with instrumentals!', 'success');
        } else {
            showStatus('song-status', '❌ ' + data.error, 'error');
        }
    } catch (e) {
        showStatus('song-status', '❌ ' + e.message, 'error');
        stopInstrumental();
    }
    setLoading(btn, false);
}

let lastLyrics = '';
async function translateCurrentLyrics() {
    const lang = prompt("Enter target language code (e.g., hi, ta, te, bn, fr):", "hi");
    if (!lang) return;
    const btn = document.getElementById('translate-lyrics-btn');
    setLoading(btn, true);
    try {
        const res = await fetch('/translate', {
            method: 'POST',
            body: new URLSearchParams({ text: lastLyrics, target: lang })
        });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('song-lyrics').innerHTML = data.translated.replace(/\n/g, '<br>');
            showStatus('song-status', '✅ Lyrics translated to ' + lang, 'success');
        }
    } catch (e) { showStatus('song-status', '❌ Translation failed', 'error'); }
    setLoading(btn, false);
}

/* ── Spectrum Visualizer ── */
function setupSpectrumViz(audioEl) {
    const container = document.getElementById('viz-container');
    const canvas = document.getElementById('spectrum-canvas');
    container.style.display = 'block';
    canvas.width = canvas.parentElement.offsetWidth;
    const ctx2d = canvas.getContext('2d');
    try {
        const actx = getAudioCtx();
        const source = actx.createMediaElementSource(audioEl);
        const analyser = actx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser); analyser.connect(actx.destination);
        const bufLen = analyser.frequencyBinCount;
        const dataArr = new Uint8Array(bufLen);
        function draw() {
            requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArr);
            ctx2d.fillStyle = 'rgba(10,10,26,0.85)'; ctx2d.fillRect(0, 0, canvas.width, canvas.height);
            const barW = (canvas.width / bufLen) * 2.5;
            let x = 0;
            for (let i = 0; i < bufLen; i++) {
                const h = (dataArr[i] / 255) * canvas.height;
                const hue = (i / bufLen) * 270 + 220;
                ctx2d.fillStyle = 'hsl(' + hue + ', 80%, 60%)';
                ctx2d.fillRect(x, canvas.height - h, barW - 1, h);
                x += barW;
            }
        }
        draw();
    } catch (e) { /* spectrum viz optional */ }
}

/* ══════════════════ VOICE CLONE ══════════════════ */
function onCloneFileSelect() {
    const f = document.getElementById('clone-file').files[0];
    if (f) document.getElementById('clone-upload-label').innerHTML = '🎤 <strong>' + f.name + '</strong><br><small>' + (f.size / 1024).toFixed(1) + ' KB</small>';
}

async function doCloneVoice() {
    const btn = event.currentTarget;
    const consent = document.getElementById('clone-consent').checked;
    if (!consent) { showStatus('clone-status', '⚠️ You must provide consent.', 'error'); return; }

    let file = null;
    if (cloneInputMode === 'upload') {
        const fi = document.getElementById('clone-file');
        if (!fi.files.length) { showStatus('clone-status', '⚠️ Upload a voice sample.', 'error'); return; }
        file = fi.files[0];
    } else {
        if (!recordedBlob) { showStatus('clone-status', '⚠️ Record your voice first.', 'error'); return; }
        file = new File([recordedBlob], 'recording.webm', { type: 'audio/webm' });
    }

    setLoading(btn, true);
    showStatus('clone-status', '⏳ Analyzing voice & creating profile...', 'info');
    const body = new FormData();
    body.append('file', file);
    body.append('name', document.getElementById('clone-name').value);
    body.append('consent', 'on');
    body.append('lang', document.getElementById('clone-lang').value);
    body.append('gender', document.getElementById('clone-gender').value);
    try {
        const res = await fetch('/clone-voice', { method: 'POST', body });
        const data = await res.json();
        if (data.success) {
            const p = data.profile || {};
            let info = 'Profile: ' + (p.name || '') + '\nVoice: ' + (p.edge_voice || '') + '\nLanguage: ' + (p.language || '') + '\nGender: ' + (p.gender || '');
            if (p.voice_analysis) info += '\nPitch: ' + (p.voice_analysis.pitch_hz || 'N/A') + ' Hz\nDuration: ' + (p.voice_analysis.duration_seconds || 'N/A') + 's';
            document.getElementById('clone-profile-info').textContent = info;
            document.getElementById('clone-profile-result').classList.add('visible');
            document.getElementById('test-profile-name').value = p.name || 'myvoice';
            showStatus('clone-status', '✅ Voice profile created! Test it below.', 'success');
        } else { showStatus('clone-status', '❌ ' + data.error, 'error'); }
    } catch (e) { showStatus('clone-status', '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}

async function doTestProfile() {
    const btn = event.currentTarget;
    const name = document.getElementById('test-profile-name').value;
    const text = document.getElementById('test-profile-text').value;
    if (!name || !text) { showStatus('test-profile-status', '⚠️ Enter name and text.', 'error'); return; }
    setLoading(btn, true);
    showStatus('test-profile-status', '⏳ Speaking...', 'info');
    const body = new FormData(); body.append('name', name); body.append('text', text);
    try {
        const res = await fetch('/speak-with-profile', { method: 'POST', body });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error); }
        const blob = await res.blob(); const url = URL.createObjectURL(blob);
        document.getElementById('test-profile-audio').src = url;
        document.getElementById('test-profile-player').style.display = 'block';
        document.getElementById('test-profile-audio').play();
        showStatus('test-profile-status', '✅ Playing!', 'success');
    } catch (e) { showStatus('test-profile-status', '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}

/* ══════════════════ RECORDING (MediaRecorder) ══════════════════ */
let mediaRecorder = null;
let recordedChunks = [];
let recordedBlob = null;
let isRecording = false;
let recStartTime = 0;
let recTimerInterval = null;
let recAnimFrame = null;
let recAnalyser = null;
let recStream = null;

async function toggleRecording() {
    if (isRecording) { stopRecording(); return; }
    try {
        recStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(recStream);
        recordedChunks = [];
        mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data); };
        mediaRecorder.onstop = () => {
            recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' });
            const url = URL.createObjectURL(recordedBlob);
            document.getElementById('rec-audio-preview').src = url;
            document.getElementById('rec-preview').style.display = 'block';
            recStream.getTracks().forEach(t => t.stop());
        };
        mediaRecorder.start();
        isRecording = true;
        recStartTime = Date.now();
        document.getElementById('rec-btn-icon').textContent = '⏹️';
        document.getElementById('rec-btn-text').textContent = 'Stop Recording';
        document.getElementById('rec-start-btn').classList.add('recording');
        recTimerInterval = setInterval(updateRecTimer, 100);
        setupRecWaveform(recStream);
    } catch (e) { showStatus('clone-status', '❌ Microphone access denied: ' + e.message, 'error'); }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
    isRecording = false;
    clearInterval(recTimerInterval);
    cancelAnimationFrame(recAnimFrame);
    document.getElementById('rec-btn-icon').textContent = '⏺️';
    document.getElementById('rec-btn-text').textContent = 'Start Recording';
    document.getElementById('rec-start-btn').classList.remove('recording');
}

function updateRecTimer() {
    const elapsed = Math.floor((Date.now() - recStartTime) / 1000);
    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const s = String(elapsed % 60).padStart(2, '0');
    document.getElementById('rec-timer').textContent = m + ':' + s;
}

function setupRecWaveform(stream) {
    const actx = getAudioCtx();
    const source = actx.createMediaStreamSource(stream);
    recAnalyser = actx.createAnalyser();
    recAnalyser.fftSize = 256;
    source.connect(recAnalyser);
    const canvas = document.getElementById('rec-waveform');
    canvas.width = canvas.parentElement.offsetWidth;
    const ctx2d = canvas.getContext('2d');
    const bufLen = recAnalyser.frequencyBinCount;
    const dataArr = new Uint8Array(bufLen);
    function drawWave() {
        if (!isRecording) return;
        recAnimFrame = requestAnimationFrame(drawWave);
        recAnalyser.getByteTimeDomainData(dataArr);
        ctx2d.fillStyle = 'rgba(10,10,26,0.9)'; ctx2d.fillRect(0, 0, canvas.width, canvas.height);
        ctx2d.lineWidth = 2; ctx2d.strokeStyle = '#ec4899';
        ctx2d.beginPath();
        const sliceW = canvas.width / bufLen;
        let x = 0;
        for (let i = 0; i < bufLen; i++) {
            const v = dataArr[i] / 128.0; const y = (v * canvas.height) / 2;
            if (i === 0) ctx2d.moveTo(x, y); else ctx2d.lineTo(x, y);
            x += sliceW;
        }
        ctx2d.lineTo(canvas.width, canvas.height / 2);
        ctx2d.stroke();
    }
    drawWave();
}

/* ══════════════════ LEGENDARY VOICES ══════════════════ */
let selectedLegendaryId = '';
function selectLegendary(vid) {
    selectedLegendaryId = vid;
    document.getElementById('legendary-panel').style.display = 'block';
    document.querySelectorAll('.legendary-card').forEach(c => c.classList.toggle('active', c.dataset.vid === vid));
    const card = document.querySelector('[data-vid="' + vid + '"]');
    const name = card ? card.querySelector('.legendary-name').textContent : vid;
    document.getElementById('legend-name-display').textContent = name;
}
async function doSpeakLegendary() {
    const btn = event.currentTarget;
    const text = document.getElementById('legend-text').value;
    const autoTrans = document.getElementById('legend-auto-translate').checked ? 'on' : 'off';
    if (!text || !selectedLegendaryId) { showStatus('legend-status', '⚠️ Select a voice and enter text.', 'error'); return; }
    setLoading(btn, true);
    showStatus('legend-status', '⏳ Generating legendary voice...', 'info');
    const body = new FormData();
    body.append('voice_id', selectedLegendaryId);
    body.append('text', text);
    body.append('auto_translate', autoTrans);
    try {
        const res = await fetch('/speak-legendary', { method: 'POST', body });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error); }
        const blob = await res.blob(); const url = URL.createObjectURL(blob);
        document.getElementById('legend-audio').src = url;
        document.getElementById('legend-player').style.display = 'block';
        document.getElementById('legend-audio').play();
        showStatus('legend-status', '✅ Legendary voice generated!', 'success');
    } catch (e) { showStatus('legend-status', '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}

/* ══════════════════ VOICE AGE SIMULATOR ══════════════════ */
let selectedAge = 'adult';
function selectAge(aid) {
    selectedAge = aid;
    document.querySelectorAll('#age-grid .genre-card').forEach(c => c.classList.toggle('active', c.dataset.age === aid));
}
async function doSpeakAge() {
    const btn = event.currentTarget; setLoading(btn, true);
    showStatus('age-status', '⏳ Generating age-styled voice...', 'info');
    const body = new FormData();
    body.append('text', document.getElementById('age-text').value);
    body.append('lang', document.getElementById('age-lang').value);
    body.append('gender', document.getElementById('age-gender').value);
    body.append('age_preset', selectedAge);
    body.append('auto_translate', document.getElementById('age-auto-translate').checked ? 'on' : 'off');
    try {
        const res = await fetch('/speak-age', { method: 'POST', body });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error); }
        const blob = await res.blob(); const url = URL.createObjectURL(blob);
        document.getElementById('age-audio').src = url;
        document.getElementById('age-player').style.display = 'block';
        document.getElementById('age-audio').play();
        showStatus('age-status', '✅ Age voice generated!', 'success');
    } catch (e) { showStatus('age-status', '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}

/* ══════════════════ AUDIO STUDIO ══════════════════ */
let selectedEffect = 'enhance';
const effectDescs = {
    pitch_up: '🐿️ Raise pitch to make voice sound higher or child-like',
    pitch_down: '🗿 Lower pitch for a deeper, bass-like voice',
    speed_up: '⏩ Make the audio play faster',
    slow_down: '🐌 Make the audio play slower',
    enhance: '✨ Boost audio levels and normalize volume',
    echo: '🏔️ Add an echo / reverb trail to the audio',
    reverse: '🔄 Play the audio backwards',
    robot: '🤖 Robotic / metallic voice effect with modulation',
};
function selectEffect(eid) {
    selectedEffect = eid;
    document.querySelectorAll('#effects-grid .genre-card').forEach(c => c.classList.toggle('active', c.dataset.effect === eid));
    document.getElementById('effect-desc').textContent = effectDescs[eid] || '';
}
function onStudioFileSelect() {
    const f = document.getElementById('studio-file').files[0];
    if (f) {
        document.getElementById('studio-upload-label').innerHTML = '🎧 <strong>' + f.name + '</strong><br><small>' + (f.size / 1024).toFixed(1) + ' KB</small>';
        const url = URL.createObjectURL(f);
        document.getElementById('studio-original-audio').src = url;
        document.getElementById('studio-original-player').style.display = 'block';
    }
}
async function doEditAudio() {
    const btn = event.currentTarget;
    const fi = document.getElementById('studio-file');
    if (!fi.files.length) { showStatus('studio-status', '⚠️ Upload an audio file first.', 'error'); return; }
    setLoading(btn, true);
    showStatus('studio-status', '⏳ Applying ' + selectedEffect + ' effect...', 'info');
    const body = new FormData();
    body.append('file', fi.files[0]);
    body.append('effect', selectedEffect);
    try {
        const res = await fetch('/edit-audio', { method: 'POST', body });
        if (!res.ok) { const d = await res.json(); throw new Error(d.error); }
        const blob = await res.blob(); const url = URL.createObjectURL(blob);
        document.getElementById('studio-processed-audio').src = url;
        document.getElementById('studio-processed-player').style.display = 'block';
        document.getElementById('studio-processed-audio').play();
        showStatus('studio-status', '✅ Effect applied!', 'success');
    } catch (e) { showStatus('studio-status', '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}

/* ══════════════════ AUTH & LOGIN ══════════════════ */
let authMode = 'login';
let authToken = localStorage.getItem('vaaniverse_token') || '';
let currentUser = null;

function openLoginModal() {
    document.getElementById('login-modal').style.display = 'flex';
}
function closeLoginModal() {
    document.getElementById('login-modal').style.display = 'none';
}
function setAuthMode(mode) {
    authMode = mode;
    const isLanding = document.body.classList.contains('auth-landing');
    const prefix = isLanding ? 'landing-' : 'auth-';

    document.getElementById('auth-title').textContent = mode === 'login' ? 'Login' : 'Sign Up';
    document.getElementById(prefix + 'email-group').style.display = mode === 'signup' ? 'block' : 'none';

    // Switch tabs in landing if needed
    if (isLanding) {
        document.getElementById('landing-login-tab').classList.toggle('active', mode === 'login');
        document.getElementById('landing-signup-tab').classList.toggle('active', mode === 'signup');
    } else {
        document.getElementById('auth-login-btn').classList.toggle('active', mode === 'login');
        document.getElementById('auth-signup-btn').classList.toggle('active', mode === 'signup');
    }

    const submitBtn = document.getElementById(isLanding ? 'landing-auth-btn' : 'auth-submit-btn');
    submitBtn.querySelector('.btn-text').textContent = mode === 'login' ? '🔐 Login' : '✨ Sign Up';
}
async function doAuth() {
    const btn = document.getElementById('auth-submit-btn'); setLoading(btn, true);
    await performAuth('/login', 'auth-status', btn);
}

async function doLandingAuth() {
    const btn = document.getElementById('landing-auth-btn'); setLoading(btn, true);
    const endpoint = authMode === 'login' ? '/login' : '/register';
    await performAuth(endpoint, 'landing-auth-status', btn, true);
}

async function performAuth(endpoint, statusId, btn, isLanding = false) {
    const prefix = isLanding ? 'landing-' : 'auth-';
    const body = new FormData();
    body.append('username', document.getElementById(prefix + 'username').value);
    body.append('password', document.getElementById(prefix + 'password').value);
    if (authMode === 'signup') body.append('email', document.getElementById(prefix + 'email')?.value || '');

    try {
        const res = await fetch(endpoint, { method: 'POST', body });
        const data = await res.json();
        if (data.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('vaaniverse_token', authToken);
            showStatus(statusId, '✅ Welcome, ' + data.user.username + '!', 'success');
            updateLoginUI();
            if (isLanding) {
                setTimeout(() => {
                    document.body.classList.remove('auth-landing');
                    document.getElementById('auth-landing-overlay').style.opacity = '0';
                    setTimeout(() => document.getElementById('auth-landing-overlay').style.display = 'none', 500);
                }, 800);
            } else {
                setTimeout(closeLoginModal, 1000);
            }
        } else {
            showStatus(statusId, '❌ ' + data.error, 'error');
        }
    } catch (e) { showStatus(statusId, '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}
function updateLoginUI() {
    const btn = document.getElementById('login-tab-btn');

    if (currentUser) {
        document.body.classList.remove('auth-landing');
        document.getElementById('auth-landing-overlay').style.display = 'none';
        document.getElementById('user-guide-overlay').style.display = 'none';

        // STRICT LOCK: Enable the app
        document.getElementById('main-app').style.display = 'block';

        if (btn) {
            btn.textContent = '👤 ' + currentUser.username;
            btn.onclick = doLogout;
        }
        document.getElementById('library-content').style.display = 'block';
        loadHistory();
    } else {
        document.body.classList.add('auth-landing');
        document.getElementById('main-app').style.display = 'none'; // Lock app
        if (btn) {
            btn.textContent = '🔐 Login';
            btn.onclick = openLoginModal;
        }
        document.getElementById('library-content').style.display = 'none';
    }
}

async function doGenerateStory() {
    const theme = document.getElementById('story-theme').value;
    const lang = document.getElementById('story-lang').value;
    if (!theme) return alert("Please enter a theme!");

    const btn = document.getElementById('story-btn');
    setLoading(btn, true);
    showStatus('story-status', '⏳ Crafting your magical story...', 'info');

    const body = new FormData();
    body.append('theme', theme);
    body.append('lang', lang);

    try {
        const res = await fetch('/generate-story', { method: 'POST', body });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('story-result').style.display = 'block';
            document.getElementById('story-text').textContent = data.text;

            // Auto narrate story
            const ttsBody = new URLSearchParams({ text: data.text, voice_id: 'en-US-AriaNeural' });
            const narRes = await fetch('/tts', { method: 'POST', body: ttsBody });
            if (narRes.ok) {
                const blob = await narRes.blob();
                document.getElementById('story-audio').src = URL.createObjectURL(blob);
                document.getElementById('story-player').style.display = 'block';
            }
            showStatus('story-status', '📖 Story generated!', 'success');
        }
    } catch (e) { showStatus('story-status', '❌ Failed to generate story', 'error'); }
    setLoading(btn, false);
}

async function doAnalyzeSentiment() {
    const text = document.getElementById('sentiment-text').value;
    if (!text) return alert("Enter text to analyze!");

    const btn = document.getElementById('sentiment-btn');
    setLoading(btn, true);
    showStatus('sentiment-status', '🔍 Analyzing emotional frequencies...', 'info');

    const body = new FormData();
    body.append('text', text);

    try {
        const res = await fetch('/analyze-sentiment', { method: 'POST', body });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('sentiment-result').style.display = 'block';
            document.getElementById('sentiment-label').textContent = data.sentiment;
            document.getElementById('sentiment-score').textContent = (data.score * 100).toFixed(0) + '% Confidence';
            document.getElementById('sentiment-bar').style.width = (data.score * 100) + '%';
            showStatus('sentiment-status', '🌈 Analysis complete!', 'success');
        }
    } catch (e) { showStatus('sentiment-status', '❌ Analysis failed', 'error'); }
    setLoading(btn, false);
}
function doLogout() {
    authToken = ''; currentUser = null;
    localStorage.removeItem('vaaniverse_token');
    updateLoginUI();
}

/* ══════════════════ HISTORY / LIBRARY ══════════════════ */
let allHistory = [];
async function loadHistory() {
    if (!authToken) return;
    try {
        const res = await fetch('/history', { headers: { 'Authorization': 'Bearer ' + authToken } });
        const data = await res.json();
        if (data.ok && data.history) {
            allHistory = data.history;
            renderHistory(allHistory);
        }
    } catch (e) { console.error('History load failed', e); }
}

function renderHistory(items) {
    const list = document.getElementById('history-list');
    if (items.length === 0) {
        document.getElementById('history-empty').style.display = 'block';
        list.innerHTML = '';
        return;
    }
    document.getElementById('history-empty').style.display = 'none';
    const icons = { translate: '🌐', tts: '🔊', song: '🎵', clone: '🎤', clone_speak: '🗣️', voice_translate: '🌐', voice_translate_audio: '🎙️', studio: '🎚️' };

    list.innerHTML = items.map(h => `
        <div class="history-card">
            <div class="history-type-icon">${icons[h.type] || '✨'}</div>
            <div class="history-info">
                <span class="history-title">${h.title || 'Untitled Creation'}</span>
                <span class="history-meta">${h.type.replace(/_/g, ' ').toUpperCase()} • ${h.created_at}</span>
            </div>
            ${h.audio_path ? `
                <button class="btn btn-secondary btn-sm" onclick="playHistoryAudio(${h.id})">▶️ Play</button>
            ` : ''}
        </div>
    `).join('');
}

function filterHistory(query) {
    const q = query.toLowerCase();
    const filtered = allHistory.filter(h =>
        h.title.toLowerCase().includes(q) ||
        h.type.toLowerCase().includes(q)
    );
    renderHistory(filtered);
}

function playHistoryAudio(hid) {
    const audio = new Audio(`/history-audio/${hid}?token=${authToken}`);
    audio.play().catch(e => alert("Playback failed: " + e.message));
}

// Auto-init and transitions
window.onload = () => {
    // Stage 1: Splash Screen
    setTimeout(() => {
        const splash = document.getElementById('splash-screen');
        if (splash) {
            splash.style.opacity = '0';
            setTimeout(() => {
                splash.style.display = 'none';
                // Stage 2: User Guide (only if not logged in)
                if (!localStorage.getItem('vaaniverse_token')) {
                    document.getElementById('user-guide-overlay').style.display = 'flex';
                } else {
                    checkAuth();
                }
            }, 800);
        }
    }, 2000);
};

async function checkAuth() {
    if (!authToken) {
        const stored = localStorage.getItem('vaaniverse_token');
        if (stored) authToken = stored;
        else return;
    }
    try {
        const res = await fetch('/me', { headers: { 'Authorization': 'Bearer ' + authToken } });
        const data = await res.json();
        if (data.ok) { currentUser = data.user; updateLoginUI(); }
        else { authToken = ''; localStorage.removeItem('vaaniverse_token'); }
    } catch (e) { /* not logged in */ }
}

function proceedToAuth() {
    const guide = document.getElementById('user-guide-overlay');
    guide.style.opacity = '0';
    setTimeout(() => {
        guide.style.display = 'none';
        document.getElementById('auth-landing-overlay').style.display = 'flex';
    }, 500);
}

async function translateGuide(lang) {
    if (lang === 'en') {
        renderGuideContent("en");
        return;
    }
    const content = document.getElementById('guide-content').innerText;
    try {
        const res = await fetch('/translate', {
            method: 'POST',
            body: new URLSearchParams({ text: content, target: lang })
        });
        const data = await res.json();
        if (data.ok) {
            document.getElementById('guide-title').innerText = await translateText("Welcome to Vaaniverse AI", lang);
            document.getElementById('guide-content').innerHTML = data.translated.split('\n').map(p => `<p>${p}</p>`).join('');
        }
    } catch (e) { console.error("Guide translation failed", e); }
}

async function translateText(text, lang) {
    try {
        const res = await fetch('/translate', {
            method: 'POST',
            body: new URLSearchParams({ text, target: lang })
        });
        const data = await res.json();
        return data.ok ? data.translated : text;
    } catch (e) { return text; }
}

function renderGuideContent(lang) {
    if (lang === 'en') {
        document.getElementById('guide-title').innerText = "Welcome to Vaaniverse AI";
        document.getElementById('guide-content').innerHTML = `
            <p>Vaaniverse AI is your all-in-one platform for voice intelligence:</p>
            <ul>
              <li><strong>🌐 Translate:</strong> Break language barriers instantly.</li>
              <li><strong>🔊 TTS:</strong> Convert text to 300+ life-like voices.</li>
              <li><strong>🎤 Clone:</strong> Create digital versions of any voice.</li>
              <li><strong>✍️ Lyrics:</strong> Generate and translate lyrics for any genre.</li>
            </ul>
        `;
    }
}
