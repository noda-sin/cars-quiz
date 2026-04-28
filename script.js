const CARS = [
  { emoji: "🚗", name: "くるま" },
  { emoji: "🚕", name: "タクシー" },
  { emoji: "🚌", name: "バス" },
  { emoji: "🚎", name: "トロリーバス" },
  { emoji: "🏎️", name: "レーシングカー" },
  { emoji: "🚓", name: "パトカー" },
  { emoji: "🚑", name: "きゅうきゅうしゃ" },
  { emoji: "🚒", name: "しょうぼうしゃ" },
  { emoji: "🚐", name: "バン" },
  { emoji: "🛻", name: "ピックアップトラック" },
  { emoji: "🚚", name: "トラック" },
  { emoji: "🚛", name: "おおきなトラック" },
  { emoji: "🚜", name: "トラクター" },
  { emoji: "🚙", name: "ジープ" },
  { emoji: "🚲", name: "じてんしゃ" },
  { emoji: "🛵", name: "スクーター" },
  { emoji: "🏍️", name: "バイク" },
  { emoji: "🚂", name: "きかんしゃ" },
];

const PRAISES = ["せいかい！", "やったー！", "じょうずだね！", "すごい！", "おみごと！", "ぴんぽーん！"];
const TRY_AGAINS = ["もういちど！", "おしいー！", "もういっかい！", "うーん？"];
const CELEBRATE_EMOJIS = ["🎉", "✨", "🌟", "💯", "👏"];

const GRID_SIZE = 6;

let currentTarget = null;
let currentCars = [];
let score = 0;
let busy = false;
let jaVoice = null;

function loadVoices() {
  if (!("speechSynthesis" in window)) return;
  const voices = speechSynthesis.getVoices();
  jaVoice =
    voices.find((v) => v.lang === "ja-JP") ||
    voices.find((v) => v.lang.startsWith("ja")) ||
    null;
}

if ("speechSynthesis" in window) {
  loadVoices();
  speechSynthesis.onvoiceschanged = loadVoices;
}

function speak(text, opts = {}) {
  if (!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "ja-JP";
  u.rate = opts.rate ?? 0.95;
  u.pitch = opts.pitch ?? 1.2;
  u.volume = 1;
  if (jaVoice) u.voice = jaVoice;
  speechSynthesis.speak(u);
}

function pickRandom(arr, n) {
  const copy = arr.slice();
  const result = [];
  for (let i = 0; i < n && copy.length > 0; i++) {
    const idx = Math.floor(Math.random() * copy.length);
    result.push(copy.splice(idx, 1)[0]);
  }
  return result;
}

function questionText(car) {
  return `${car.name}は どれかな？`;
}

function newRound() {
  busy = false;
  hideFeedback();
  currentCars = pickRandom(CARS, GRID_SIZE);
  currentTarget = currentCars[Math.floor(Math.random() * currentCars.length)];

  document.getElementById("question").textContent = questionText(currentTarget);

  const grid = document.getElementById("grid");
  grid.innerHTML = "";
  for (const car of currentCars) {
    const btn = document.createElement("button");
    btn.className = "car-card";
    btn.textContent = car.emoji;
    btn.setAttribute("aria-label", car.name);
    btn.addEventListener("click", () => onPick(btn, car));
    grid.appendChild(btn);
  }

  setTimeout(() => speak(questionText(currentTarget)), 250);
}

function onPick(btn, car) {
  if (busy) return;
  if (car === currentTarget) {
    busy = true;
    btn.classList.add("correct");
    document.querySelectorAll(".car-card").forEach((el) => {
      if (el !== btn) el.classList.add("dim");
    });
    score++;
    document.getElementById("score").textContent = score;

    const emoji = CELEBRATE_EMOJIS[Math.floor(Math.random() * CELEBRATE_EMOJIS.length)];
    showFeedback(emoji);

    const praise = PRAISES[Math.floor(Math.random() * PRAISES.length)];
    speak(praise, { pitch: 1.5, rate: 1.0 });

    setTimeout(newRound, 1900);
  } else {
    btn.classList.add("wrong");
    setTimeout(() => btn.classList.remove("wrong"), 500);
    const t = TRY_AGAINS[Math.floor(Math.random() * TRY_AGAINS.length)];
    speak(t, { pitch: 1.1 });
  }
}

function showFeedback(emoji) {
  const f = document.getElementById("feedback");
  f.textContent = emoji;
  f.classList.add("show");
}

function hideFeedback() {
  document.getElementById("feedback").classList.remove("show");
}

document.getElementById("start-btn").addEventListener("click", () => {
  // Prime speech synthesis on first user gesture (required on iOS)
  speak("はじめるよ", { rate: 1.0 });
  document.getElementById("start-screen").classList.add("hidden");
  document.getElementById("game-screen").classList.remove("hidden");
  setTimeout(newRound, 500);
});

document.getElementById("replay-btn").addEventListener("click", () => {
  if (currentTarget && !busy) {
    speak(questionText(currentTarget));
  }
});

// Prevent iOS double-tap zoom on the game area
document.addEventListener("dblclick", (e) => e.preventDefault(), { passive: false });
