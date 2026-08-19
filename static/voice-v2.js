/* FitPulse voice-v2 - works on Chrome, Edge, Safari AND the Android WebView app */
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

var SPEECH = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
var REC = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);

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
var sr = null;

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

/* ---------- Speech Recognition engine (best on mobile Chrome / desktop) ---------- */
function startSR(onDone) {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var r = new SR();
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
    voiceStatus('Voice: ' + err + '. Allow microphone permission in your browser settings, then try again.', true);
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
    voiceStatus('Listening... speak now');
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

/* ---------- MediaRecorder engine (Android WebView app / Firefox) ---------- */
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
      voiceStatus('Voice: could not start recording. Check microphone permission.', true);
    }
  }).catch(function () {
    recording = false;
    recUI(false);
    voiceStatus('Voice: microphone permission needed. Enable it in your browser/app settings, then try again.', true);
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
        voiceStatus('Voice: could not understand the audio. Please speak clearly and try again.', true);
      }
    })
    .catch(function () {
      voiceStatus('Voice: transcription failed. Check your internet connection.', true);
    });
}

/* ---------- button wiring ---------- */
document.addEventListener('DOMContentLoaded', function () {
  var voiceBtn = document.getElementById('voice-btn');
  var vSend = document.getElementById('voice-send');
  var vCancel = document.getElementById('voice-cancel');
  if (!voiceBtn) return;
  var srCancel = false;

  function sendFromSR(t) {
    srCancel = false;
    if (window.ask && t) window.ask(t);
  }

  function useRecorder() {
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
    if (vSend) vSend.addEventListener('click', function () { finishRecording(true); });
    if (vCancel) vCancel.addEventListener('click', function () { cancelRecording(); });
  }

  function useSpeech() {
    voiceBtn.addEventListener('click', function () {
      if (sr) { stopSR(); return; }
      srCancel = false;
      if (startSR(sendFromSR)) {
        voiceStatus('Listening... speak now');
      } else {
        voiceStatus('Voice: could not start speech recognition. Trying the recorder...', true);
        useRecorder();
      }
    });
    if (vSend) vSend.addEventListener('click', function () { srCancel = false; stopSR(); });
    if (vCancel) vCancel.addEventListener('click', function () { srCancel = true; stopSR(); });
  }

  if (SPEECH) {
    useSpeech();
  } else if (REC) {
    useRecorder();
  } else {
    voiceBtn.addEventListener('click', function () {
      voiceStatus('Voice input is not supported in this browser. Please use Chrome, Edge, or the app.', true);
    });
  }
});