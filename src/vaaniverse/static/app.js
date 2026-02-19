/* ═══════════════════════════════════════════════════════════
   Vaaniverse AI — Frontend JavaScript
   Tab switching, API calls, Web Audio instrumental engine,
   MediaRecorder voice recording, legendary voices
   ═══════════════════════════════════════════════════════════ */

/* ── Tab switching ── */
function switchTab(tab) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    document.querySelector('[data-tab="' + tab + '"]').classList.add('active');
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
async function doVoiceTranslate() {
    const btn = event.currentTarget; setLoading(btn, true);
    if (vtMode === 'audio') {
        const fileInput = document.getElementById('vt-file');
        if (!fileInput.files.length) { showStatus('vt-status', '⚠️ Upload a recording first.', 'error'); setLoading(btn, false); return; }
        showStatus('vt-status', '⏳ Transcribing, translating...', 'info');
        const body = new FormData();
        body.append('file', fileInput.files[0]);
        body.append('src_lang', document.getElementById('vt-src').value);
        body.append('tgt_lang', document.getElementById('vt-tgt').value);
        body.append('gender', document.getElementById('vt-gender').value);
        try {
            const res = await fetch('/voice-translate-audio', { method: 'POST', body });
            if (!res.ok) { const d = await res.json(); if (d.transcribed) { document.getElementById('vt-transcribed').textContent = d.transcribed; document.getElementById('vt-transcribed-result').style.display = 'block'; document.getElementById('vt-transcribed-result').classList.add('visible'); } if (d.translated) { document.getElementById('vt-translated').textContent = d.translated; document.getElementById('vt-result').classList.add('visible'); } throw new Error(d.error); }
            const transcribed = res.headers.get('X-Transcribed-Text') || '';
            const translated = res.headers.get('X-Translated-Text') || '';
            if (transcribed) { document.getElementById('vt-transcribed').textContent = transcribed; document.getElementById('vt-transcribed-result').style.display = 'block'; document.getElementById('vt-transcribed-result').classList.add('visible'); }
            document.getElementById('vt-translated').textContent = translated; document.getElementById('vt-result').classList.add('visible');
            const blob = await res.blob(); const url = URL.createObjectURL(blob);
            document.getElementById('vt-audio').src = url; document.getElementById('vt-player').style.display = 'block'; document.getElementById('vt-audio').play();
            showStatus('vt-status', '✅ Voice translation complete!', 'success');
        } catch (e) { showStatus('vt-status', '❌ ' + e.message, 'error'); }
    } else {
        showStatus('vt-status', '⏳ Translating...', 'info');
        const body = new FormData();
        body.append('text', document.getElementById('vt-text').value);
        body.append('src_lang', document.getElementById('vt-src').value);
        body.append('tgt_lang', document.getElementById('vt-tgt').value);
        body.append('gender', document.getElementById('vt-gender').value);
        try {
            const res = await fetch('/voice-translate', { method: 'POST', body });
            if (!res.ok) { const d = await res.json(); document.getElementById('vt-translated').textContent = d.translated || ''; document.getElementById('vt-result').classList.add('visible'); throw new Error(d.error); }
            const translatedText = res.headers.get('X-Translated-Text') || '';
            document.getElementById('vt-translated').textContent = translatedText; document.getElementById('vt-result').classList.add('visible'); document.getElementById('vt-transcribed-result').style.display = 'none';
            const blob = await res.blob(); const url = URL.createObjectURL(blob);
            document.getElementById('vt-audio').src = url; document.getElementById('vt-player').style.display = 'block'; document.getElementById('vt-audio').play();
            showStatus('vt-status', '✅ Voice translation complete!', 'success');
        } catch (e) { showStatus('vt-status', '❌ ' + e.message, 'error'); }
    }
    setLoading(btn, false);
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
        document.getElementById('song-lyrics').textContent = data.lyrics;
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
    } catch (e) { showStatus('song-status', '❌ ' + e.message, 'error'); stopInstrumental(); }
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
    if (!text || !selectedLegendaryId) { showStatus('legend-status', '⚠️ Select a voice and enter text.', 'error'); return; }
    setLoading(btn, true);
    showStatus('legend-status', '⏳ Generating legendary voice...', 'info');
    const body = new FormData(); body.append('voice_id', selectedLegendaryId); body.append('text', text);
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
    document.getElementById('auth-title').textContent = mode === 'login' ? 'Login' : 'Sign Up';
    document.getElementById('auth-email-group').style.display = mode === 'signup' ? 'block' : 'none';
    document.getElementById('auth-login-btn').classList.toggle('active', mode === 'login');
    document.getElementById('auth-signup-btn').classList.toggle('active', mode === 'signup');
    document.getElementById('auth-submit-btn').querySelector('.btn-text').textContent = mode === 'login' ? '🔐 Login' : '✨ Sign Up';
}
async function doAuth() {
    const btn = document.getElementById('auth-submit-btn'); setLoading(btn, true);
    const body = new FormData();
    body.append('username', document.getElementById('auth-username').value);
    body.append('password', document.getElementById('auth-password').value);
    if (authMode === 'signup') body.append('email', document.getElementById('auth-email').value);
    const endpoint = authMode === 'login' ? '/login' : '/register';
    try {
        const res = await fetch(endpoint, { method: 'POST', body });
        const data = await res.json();
        if (data.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('vaaniverse_token', authToken);
            showStatus('auth-status', '✅ Welcome, ' + data.user.username + '!', 'success');
            updateLoginUI();
            setTimeout(closeLoginModal, 1000);
        } else {
            showStatus('auth-status', '❌ ' + data.error, 'error');
        }
    } catch (e) { showStatus('auth-status', '❌ ' + e.message, 'error'); }
    setLoading(btn, false);
}
function updateLoginUI() {
    const btn = document.getElementById('login-tab-btn');
    if (currentUser) {
        btn.textContent = '👤 ' + currentUser.username;
        btn.onclick = doLogout;
        document.getElementById('library-login-msg').style.display = 'none';
        document.getElementById('library-content').style.display = 'block';
        loadHistory();
    } else {
        btn.textContent = '🔐 Login';
        btn.onclick = openLoginModal;
        document.getElementById('library-login-msg').style.display = 'block';
        document.getElementById('library-content').style.display = 'none';
    }
}
function doLogout() {
    authToken = ''; currentUser = null;
    localStorage.removeItem('vaaniverse_token');
    updateLoginUI();
}

/* ══════════════════ HISTORY / LIBRARY ══════════════════ */
async function loadHistory() {
    if (!authToken) return;
    try {
        const res = await fetch('/history', { headers: { 'Authorization': 'Bearer ' + authToken } });
        const data = await res.json();
        if (data.ok && data.history) {
            const list = document.getElementById('history-list');
            if (data.history.length === 0) {
                document.getElementById('history-empty').style.display = 'block';
                list.innerHTML = '';
                return;
            }
            document.getElementById('history-empty').style.display = 'none';
            list.innerHTML = data.history.map(h => `
                <div class="card" style="margin-bottom:12px;padding:12px">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <span class="lang-tag">${h.type}</span>
                            <strong>${h.title || 'Untitled'}</strong>
                            <small style="color:var(--text-muted);margin-left:8px">${h.created_at}</small>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) { /* silent */ }
}

// Auto-check login on page load
(async function checkAuth() {
    if (!authToken) return;
    try {
        const res = await fetch('/me', { headers: { 'Authorization': 'Bearer ' + authToken } });
        const data = await res.json();
        if (data.ok) { currentUser = data.user; updateLoginUI(); }
        else { authToken = ''; localStorage.removeItem('vaaniverse_token'); }
    } catch (e) { /* not logged in */ }
})();
