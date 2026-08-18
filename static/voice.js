/* FitPulse voice helpers - Web Speech API (free, no key) */
var voiceActive = false;
var activeRec = null;
var speechRecognitionSupported = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
var synth = window.speechSynthesis;
var cachedVoices = [];
if (synth && typeof synth.getVoices === 'function') {
  cachedVoices = synth.getVoices() || [];
  synth.addEventListener('voiceschanged', function(){ cachedVoices = synth.getVoices() || []; });
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

function stopVoice() {
  if (activeRec) { activeRec.stop(); }
  activeRec = null;
  voiceActive = false;
}

function setListening(btn, statusEl, sub, on, err) {
  voiceActive = on;
  if (btn) btn.classList.toggle('listening', on);
  if (statusEl) statusEl.textContent = err ? ('Voice: ' + err) : (on ? 'Listening... speak now' : '');
  if (sub) sub.textContent = on ? '🎙️ Listening...' : 'Type, or tap the mic to speak';
}

function startVoice(callback, btn, statusEl, sub) {
  if (!speechRecognitionSupported) {
    setListening(btn, statusEl, sub, false, 'not supported in this browser. Use Chrome/Edge.');
    return;
  }
  if (voiceActive) { stopVoice(); setListening(btn, statusEl, sub, false); return; }
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var rec = new SR();
  activeRec = rec;
  rec.lang = 'en-US';
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  setListening(btn, statusEl, sub, true);
  rec.onresult = function (e) {
    var transcript = e.results[0][0].transcript;
    setListening(btn, statusEl, sub, false);
    activeRec = null;
    if (callback) callback(transcript);
  };
  rec.onerror = function (e) {
    setListening(btn, statusEl, sub, false, e.error || 'unknown error');
    activeRec = null;
  };
  rec.onend = function () {
    setListening(btn, statusEl, sub, false);
    activeRec = null;
  };
  rec.start();
}