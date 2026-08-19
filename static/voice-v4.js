/* FitPulse voice-v4 - MediaRecorder primary, SpeechRecognition fallback.
   getUserMedia retries on transient permission errors (fixes WebView race),
   shows the real error name so issues are easy to diagnose. */
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

var REC = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
var SPEECH = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
var engine = REC ? 'rec' : (SPEECH ? 'sr' : 'none');

var recorder = null;
var recStream = null;
var recChunks = [];
var recTimer = null;
var recSeconds = 0;
var holdTimer = null;
var holdMode = false;
var recording = false;
var pendingSend = false;
var gumTimer = null;
var recCapMs = 60000;
var sr = null;
var srCancel = false;

function voiceStatus(msg, isErr) {
  var el = document.getElementById('voice-status');
  if (!el) return;
  el.textContent = msg || '';
  el.classList.toggle('err', !!isErr);
  el.style.display = msg ? 'block' : 'none';
}

function stopTracks(stream) {
  if (stream && stream.getTracks) stream.getTracks().forEach(function (t) { t.stop(); });
}

function updateRecTimer() {
  var el = document.getElementById('voice-timer');
  if (!el) return;
  var m = Math.floor(recSeconds / 60);
  var s = recSeconds % 60;
  el.textContent = m + ':' + (s < 10 ? '0' + s : s);
}

function recUI(on, hint) {
  var bar = document.getElementById('voice-rec');
  var input = document.getElementById('chat-input');
  var btn = document.getElementById('voice-btn');
  var hintEl = document.getElementById('voice-rec-hint');
  if (bar) bar.hidden = !on;
  if (input) input.classList.toggle('recording', on);
  if (hintEl) hintEl.textContent = hint || 'Recording…';
  if (btn) {
    btn.classList.toggle('rec-on', on);
    var ic = btn.querySelector('.material-symbols-outlined');
    if (ic) ic.textContent = on ? 'graphic_eq' : 'mic';
  }
  if (on) updateRecTimer();
}

function resetRecordingState() {
  if (gumTimer) { clearTimeout(gumTimer); gumTimer = null; }
  if (recTimer) { clearInterval(recTimer); recTimer = null; }
  if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
  holdMode = false;
  recording = false;
  pendingSend = false;
  recChunks = [];
  if (recStream) { stopTracks(recStream); recStream = null; }
  recorder = null;
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

/* ---------- MediaRecorder engine (PRIMARY) ---------- */
function beginRecording() {
  if (recording) return;
  recording = true;
  recChunks = [];
  holdMode = false;
  pendingSend = false;
  voiceStatus('Requesting microphone…');
  if (gumTimer) clearTimeout(gumTimer);
  gumTimer = setTimeout(function () {
    if (!recording) return;
    resetRecordingState();
    recUI(false);
    voiceStatus('Voice: the microphone did not respond. Make sure the mic permission for this app is ON, then tap again.', true);
  }, 12000);

  gumAttempt(0);
}

function gumAttempt(attempt) {
  if (!recording) return;
  navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
    if (gumTimer) { clearTimeout(gumTimer); gumTimer = null; }
    if (!recording) { stopTracks(stream); return; }
    recStream = stream;
    try {
      recorder = new MediaRecorder(stream);
      recorder.ondataavailable = function (e) { if (e.data && e.data.size) recChunks.push(e.data); };
      recorder.onstop = function () { handleRecStop(); };
      recorder.start();
      voiceStatus('');
      recUI(true, holdMode ? 'Release to send' : 'Tap to send, or press & hold to talk');
      startRecTimer();
    } catch (err) {
      resetRecordingState();
      stopTracks(stream);
      recUI(false);
      voiceStatus('Voice: recording could not start on this device.', true);
    }
  }).catch(function (e) {
    if (!recording) return;
    var name = (e && e.name) || 'error';
    var retryable = name === 'NotAllowedError' || name === 'PermissionDeniedError' ||
                    name === 'AbortError' || name === 'SecurityError' || name === 'NotReadableError';
    if (attempt < 2 && retryable) {
      voiceStatus('Requesting microphone… (retry ' + (attempt + 1) + ')');
      setTimeout(function () { gumAttempt(attempt + 1); }, 900);
      return;
    }
    if (gumTimer) { clearTimeout(gumTimer); gumTimer = null; }
    recording = false;
    recUI(false);
    voiceStatus('Voice: mic blocked (' + name + '). In the app: Settings → Apps → FitPulse → Permissions → Microphone = Allow, then tap the mic again.', true);
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
    try { recorder.stop(); } catch (e) { handleRecStop(); }
  } else {
    handleRecStop();
  }
}

function cancelRecording() {
  if (!recording && !recorder) return;
  pendingSend = false;
  recording = false;
  if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
  holdMode = false;
  if (recTimer) { clearInterval(recTimer); recTimer = null; }
  if (recorder && recorder.state !== 'inactive') {
    try { recorder.stop(); } catch (e) {}
  } else {
    resetRecordingState();
    recUI(false);
    voiceStatus('');
  }
}

function handleRecStop() {
  var mime = recorder ? recorder.mimeType : 'audio/webm';
  var chunks = recChunks.slice();
  var shouldSend = pendingSend;
  resetRecordingState();
  recUI(false);
  if (shouldSend && chunks.length) {
    sendAudio(chunks, mime);
  } else {
    voiceStatus('');
  }
}

function sendAudio(chunks, mime) {
  var blob = new Blob(chunks, { type: mime || 'audio/webm' });
  var fd = new FormData();
  fd.append('audio', blob, 'voice.webm');
  voiceStatus('Transcribing…');
  fetch('/api/stt', { method: 'POST', body: fd })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d && d.text) {
        voiceStatus('');
        if (window.ask) window.ask(d.text);
        else voiceStatus('Voice: got "' + d.text + '" but the chat could not be updated.', true);
      } else {
        voiceStatus('Voice: I couldn\'t hear clearly. Please speak closer to the mic and try again.', true);
      }
    })
    .catch(function () {
      voiceStatus('Voice: transcription failed. Check your internet connection and try again.', true);
    });
}

/* ---------- SpeechRecognition engine (fallback only) ---------- */
function startSR(onDone) {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var r;
  try { r = new SR(); } catch (e) { return false; }
  sr = r;
  r.lang = 'en-US';
  r.interimResults = false;
  r.continuous = false;
  r.maxAlternatives = 1;
  r.onresult = function (e) {
    var t = '';
    for (var i = 0; i < e.results.length; i++) t += e.results[i][0].transcript;
    var cancel = srCancel;
    r.onend = null;
    sr = null;
    srCancel = false;
    voiceStatus('');
    recUI(false);
    if (!cancel && onDone) onDone(t);
  };
  r.onerror = function (e) {
    var err = (e && e.error) || 'unknown';
    sr = null;
    srCancel = false;
    voiceStatus('Voice: ' + err + '. Allow microphone permission for this app/site, then try again.', true);
  };
  r.onend = function () {
    sr = null;
    srCancel = false;
    voiceStatus('');
    recUI(false);
  };
  try {
    r.start();
    recUI(true);
    voiceStatus('Listening… speak now');
    return true;
  } catch (err) {
    sr = null;
    return false;
  }
}

function stopSR() {
  if (sr) { try { sr.stop(); } catch (e) {} sr = null; }
  voiceStatus('');
  recUI(false);
}

/* ---------- button wiring ---------- */
document.addEventListener('DOMContentLoaded', function () {
  var voiceBtn = document.getElementById('voice-btn');
  var vSend = document.getElementById('voice-send');
  var vCancel = document.getElementById('voice-cancel');
  if (!voiceBtn) return;

  function micDown(e) {
    if (e.cancelable) e.preventDefault();
    if (recording) { cancelRecording(); return; }
    holdMode = false;
    if (holdTimer) clearTimeout(holdTimer);
    holdTimer = setTimeout(function () { holdMode = true; recUI(true, 'Release to send'); }, 400);
    beginRecording();
  }
  function micUp() {
    if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
    if (recording && holdMode) finishRecording(true);
  }
  function micCancel() {
    if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }
    if (recording && holdMode) finishRecording(true);
    else if (recording) cancelRecording();
  }

  function bindHold(el, down, up, cancel) {
    if (window.PointerEvent) {
      el.addEventListener('pointerdown', down);
      el.addEventListener('pointerup', up);
      el.addEventListener('pointercancel', cancel);
    } else {
      el.addEventListener('touchstart', down, { passive: false });
      el.addEventListener('touchend', up);
      el.addEventListener('touchcancel', cancel);
    }
  }

  if (engine === 'rec') {
    bindHold(voiceBtn, micDown, micUp, micCancel);
    if (vSend) vSend.addEventListener('click', function () { finishRecording(true); });
    if (vCancel) vCancel.addEventListener('click', function () { cancelRecording(); });
  } else if (engine === 'sr') {
    voiceBtn.addEventListener('click', function () {
      if (sr) { stopSR(); return; }
      srCancel = false;
      if (!startSR(function (t) { srCancel = false; if (window.ask && t) window.ask(t); })) {
        voiceStatus('Voice: could not start speech recognition. Check microphone permission.', true);
      }
    });
    if (vSend) vSend.addEventListener('click', function () { srCancel = false; stopSR(); });
    if (vCancel) vCancel.addEventListener('click', function () { srCancel = true; stopSR(); });
  } else {
    voiceBtn.addEventListener('click', function () {
      voiceStatus('Voice input is not supported on this device. Please use Chrome or the app.', true);
    });
  }
});
