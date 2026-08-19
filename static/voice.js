/* FitPulse voice helpers - MediaRecorder + Groq Whisper STT, with Web Speech fallback */
var synth = window.speechSynthesis;
var cachedVoices = [];
if (synth && typeof synth.getVoices === 'function') {
  cachedVoices = synth.getVoices() || [];
  synth.addEventListener('voiceschanged', function () { cachedVoices = synth.getVoices() || []; });
}

function pickNaturalVoice() {
  if (!cachedVoices.length) return null;
  var prefer = function (v) { return /en/i.test(v.lang); };
  var namePrefer = ['Google UK English Female', 'Google US English', 'Google UK English Male',
                    'Samantha', 'Microsoft Aria', 'Microsoft Jenny', 'Microsoft Zira', 'Google español de Estados Unidos'];
  for (var i = 0; i < namePrefer.length; i++) {
    var hit = cachedVoices.find(function (v) { return v.name.indexOf(namePrefer[i]) !== -1; });
    if (hit) return hit;
  }
  return cachedVoices.find(function (v) { return /female/i.test(v.name) && prefer(v); }) ||
         cachedVoices.find(prefer) || cachedVoices[0];
}

function speak(text) {
  if (!synth || !text) return;
  synth.cancel();
  var u = new SpeechSynthesisUtterance(text);
  u.rate = 0.95;
  u.pitch = 1.05;
  var v = pickNaturalVoice();
  if (v) u.voice = v;
  synth.speak(u);
}

/* ---------- MediaRecorder voice (works in Chrome, Edge AND the Android WebView app) ---------- */
var recorder = null;
var recStream = null;
var recChunks = [];
var recTimer = null;
var recSeconds = 0;
var holdTimer = null;
var holdMode = false;
var recording = false;
var pendingSend = false;
var recCapMs = 60000;
var canRecord = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);

function stopTracks(stream) {
  if (stream && stream.getTracks) stream.getTracks().forEach(function (t) { t.stop(); });
}

function voiceStatus(msg) {
  var el = document.getElementById('voice-status');
  if (el) el.textContent = msg || '';
}

function updateRecTimer() {
  var el = document.getElementById('voice-timer');
  if (!el) return;
  var m = Math.floor(recSeconds / 60);
  var s = recSeconds % 60;
  el.textContent = m + ':' + (s < 10 ? '0' + s : s);
}

function recUI(on) {
  var bar = document.getElementById('voice-rec');
  var input = document.getElementById('chat-input');
  var btn = document.getElementById('voice-btn');
  if (bar) bar.hidden = !on;
  if (input) input.classList.toggle('recording', on);
  if (btn) {
    btn.classList.toggle('rec-on', on);
    var ic = btn.querySelector('.material-symbols-outlined');
    if (ic) ic.textContent = on ? 'graphic_eq' : 'mic';
  }
  if (on) updateRecTimer();
}

function startRecTimer() {
  recSeconds = 0;
  updateRecTimer();
  if (recTimer) clearInterval(recTimer);
  recTimer = setInterval(function () {
    recSeconds++;
    updateRecTimer();
    if (recSeconds * 1000 >= recCapMs) {
      clearInterval(recTimer);
      recTimer = null;
      finishRecording(true);
    }
  }, 1000);
}

function beginRecording() {
  if (recording) return;
  recording = true;
  recChunks = [];
  holdMode = false;
  pendingSend = false;
  voiceStatus('Requesting microphone...');
  navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
    if (!recording) { stopTracks(stream); return; }
    recStream = stream;
    try {
      recorder = new MediaRecorder(stream);
      recorder.ondataavailable = function (e) { if (e.data && e.data.size) recChunks.push(e.data); };
      recorder.onstop = function () { handleRecStop(); };
      recorder.start();
      voiceStatus('Recording... tap the send button to finish');
      recUI(true);
      startRecTimer();
    } catch (err) {
      stopTracks(stream);
      recording = false;
      recUI(false);
      voiceStatus('');
      startSpeechFallback();
    }
  }).catch(function () {
    recording = false;
    recUI(false);
    voiceStatus('');
    startSpeechFallback();
  });
}

function finishRecording(sendIt) {
  if (!recording) return;
  recording = false;
  if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
  holdMode = false;
  if (recTimer) { clearInterval(recTimer); recTimer = null; }
  pendingSend = sendIt;
  if (recorder && recorder.state !== 'inactive') {
    try { recorder.stop(); } catch (e) {}
  } else {
    handleRecStop();
  }
}

function cancelRecording() {
  recording = false;
  if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
  holdMode = false;
  if (recTimer) { clearInterval(recTimer); recTimer = null; }
  pendingSend = false;
  if (recorder && recorder.state !== 'inactive') {
    try { recorder.stop(); } catch (e) {}
  }
  if (recStream) { stopTracks(recStream); recStream = null; }
  recChunks = [];
  recorder = null;
  recUI(false);
  voiceStatus('');
}

function handleRecStop() {
  if (recStream) { stopTracks(recStream); recStream = null; }
  recUI(false);
  var mime = recorder ? recorder.mimeType : 'audio/webm';
  var chunks = recChunks.slice();
  recChunks = [];
  recorder = null;
  var shouldSend = pendingSend;
  pendingSend = false;
  if (shouldSend && chunks.length) {
    sendAudio(chunks, mime);
  } else if (!shouldSend) {
    voiceStatus('');
  }
}

function sendAudio(chunks, mime) {
  var blob = new Blob(chunks, { type: mime || 'audio/webm' });
  var fd = new FormData();
  fd.append('audio', blob, 'voice.webm');
  voiceStatus('Transcribing...');
  fetch('/api/stt', { method: 'POST', body: fd })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d && d.text) {
        voiceStatus('');
        if (window.ask) window.ask(d.text);
      } else {
        voiceStatus('Voice: could not understand audio. Try again.');
      }
    })
    .catch(function () {
      voiceStatus('Voice: transcription failed. Check your connection.');
    });
}

/* ---------- Web Speech API fallback (desktop browsers) ---------- */
var speechRecognitionSupported = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
var voiceActive = false;
var activeRec = null;

function setListening(btn, statusEl, on, err) {
  voiceActive = on;
  if (btn) btn.classList.toggle('listening', on);
  if (statusEl) statusEl.textContent = err ? ('Voice: ' + err) : (on ? 'Listening... speak now' : '');
}

function startVoice(callback, btn, statusEl, sub) {
  if (!speechRecognitionSupported) {
    setListening(btn, statusEl, false, 'not supported. Use Chrome, Edge, or the app.');
    return;
  }
  if (voiceActive) { stopVoice(); setListening(btn, statusEl, false); return; }
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var rec = new SR();
  activeRec = rec;
  rec.lang = 'en-US';
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  setListening(btn, statusEl, true);
  rec.onresult = function (e) {
    var transcript = e.results[0][0].transcript;
    setListening(btn, statusEl, false);
    activeRec = null;
    if (callback) callback(transcript);
  };
  rec.onerror = function (e) {
    setListening(btn, statusEl, false, e.error || 'unknown error');
    activeRec = null;
  };
  rec.onend = function () {
    setListening(btn, statusEl, false);
    activeRec = null;
  };
  rec.start();
}

function stopVoice() {
  if (activeRec) { try { activeRec.stop(); } catch (e) {} }
  activeRec = null;
  voiceActive = false;
}

function startSpeechFallback() {
  if (!speechRecognitionSupported) {
    voiceStatus('Voice input needs microphone permission or the app.');
    return;
  }
  var btn = document.getElementById('voice-btn');
  var statusEl = document.getElementById('voice-status');
  var sub = document.getElementById('chat-sub');
  startVoice(function (t) { if (window.ask) window.ask(t); }, btn, statusEl, sub);
}

/* ---------- button wiring ---------- */
document.addEventListener('DOMContentLoaded', function () {
  var voiceBtn = document.getElementById('voice-btn');
  var vSend = document.getElementById('voice-send');
  var vCancel = document.getElementById('voice-cancel');

  if (voiceBtn && canRecord) {
    voiceBtn.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      if (recording) { cancelRecording(); return; }
      holdMode = false;
      holdTimer = setTimeout(function () { holdMode = true; }, 400);
      beginRecording();
    });
    voiceBtn.addEventListener('pointerup', function () {
      if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
      if (recording && holdMode) finishRecording(true);
    });
    voiceBtn.addEventListener('pointercancel', function () {
      if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
      if (recording) cancelRecording();
    });
  } else if (voiceBtn) {
    voiceBtn.addEventListener('click', function () {
      var statusEl = document.getElementById('voice-status');
      var sub = document.getElementById('chat-sub');
      startVoice(function (t) { if (window.ask) window.ask(t); }, voiceBtn, statusEl, sub);
    });
  }

  if (vSend) vSend.addEventListener('click', function () { finishRecording(true); });
  if (vCancel) vCancel.addEventListener('click', function () { cancelRecording(); });
});