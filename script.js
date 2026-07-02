// くるまクイズ — 実写写真とナレーション音声で「〇〇はどーれだ？」
// 写真: images/cars/<slug>.jpg (Wikipedia/Wikimedia Commons)
// 音声: audio/*.mp3 (自然な日本語ナレーション)

const CARS = [
  { slug: "police_car",    name: "パトカー" },
  { slug: "fire_truck",    name: "しょうぼうしゃ" },
  { slug: "ambulance",     name: "きゅうきゅうしゃ" },
  { slug: "dump_truck",    name: "ダンプカー" },
  { slug: "bulldozer",     name: "ブルドーザー" },
  { slug: "excavator",     name: "ショベルカー" },
  { slug: "crane_truck",   name: "クレーンしゃ" },
  { slug: "mixer_truck",   name: "ミキサーしゃ" },
  { slug: "garbage_truck", name: "ごみしゅうしゅうしゃ" },
  { slug: "forklift",      name: "フォークリフト" },
  { slug: "tow_truck",     name: "レッカーしゃ" },
  { slug: "truck",         name: "トラック" },
  { slug: "tractor",       name: "トラクター" },
  { slug: "bus",           name: "バス" },
  { slug: "taxi",          name: "タクシー" },
  { slug: "car",           name: "じどうしゃ" },
  { slug: "motorcycle",    name: "バイク" },
  { slug: "road_roller",   name: "ロードローラー" },
  { slug: "train",         name: "でんしゃ" },
  { slug: "shinkansen",    name: "しんかんせん" },
];

const GRID_SIZE = 6;
const PRAISE_COUNT = 4;
const CELEBRATE_EMOJIS = ["🎉", "✨", "🌟", "💮", "👏"];
const CONFETTI_EMOJIS = ["🎉", "⭐", "✨", "🎈", "💛", "🧡"];

let currentTarget = null;
let currentCars = [];
let stars = 0;
let busy = false;

// ---- audio ----------------------------------------------------------------
// 単一の Audio 要素を使い回す (iOS はユーザー操作で unlock した要素しか鳴らせない)
const player = new Audio();
let onPlayerEnded = null;

player.addEventListener("ended", () => {
  const cb = onPlayerEnded;
  onPlayerEnded = null;
  if (cb) cb();
});

function playClip(key, onEnd) {
  onPlayerEnded = onEnd || null;
  player.src = `audio/${key}.mp3`;
  const p = player.play();
  if (p) p.catch(() => speakFallback(key));
}

// 音声ファイルが再生できない環境向けフォールバック
function speakFallback(key) {
  if (!("speechSynthesis" in window)) return;
  let text = null;
  if (key.startsWith("q_")) {
    const car = CARS.find((c) => c.slug === key.slice(2));
    if (car) text = `${car.name}は、どーれだ？`;
  } else if (key.startsWith("praise_")) {
    text = "せいかい！";
  } else if (key.startsWith("retry_") || key.startsWith("n_")) {
    text = "ちがうよ、もういっかい！";
  } else if (key === "start") {
    text = "はじめるよ！";
  }
  if (!text) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "ja-JP";
  u.rate = 0.95;
  speechSynthesis.speak(u);
  const cb = onPlayerEnded;
  onPlayerEnded = null;
  if (cb) u.onend = cb;
}

// ---- game -----------------------------------------------------------------
function pickRandom(arr, n) {
  const copy = arr.slice();
  const result = [];
  for (let i = 0; i < n && copy.length > 0; i++) {
    const idx = Math.floor(Math.random() * copy.length);
    result.push(copy.splice(idx, 1)[0]);
  }
  return result;
}

function askQuestion() {
  playClip(`q_${currentTarget.slug}`);
}

function newRound() {
  busy = false;
  hideFeedback();
  currentCars = pickRandom(CARS, GRID_SIZE);
  currentTarget = currentCars[Math.floor(Math.random() * currentCars.length)];

  document.getElementById("question").textContent = `${currentTarget.name}は どーれだ？`;

  const grid = document.getElementById("grid");
  grid.innerHTML = "";
  for (const car of currentCars) {
    const btn = document.createElement("button");
    btn.className = "car-card";
    btn.setAttribute("aria-label", car.name);

    const img = document.createElement("img");
    img.src = `images/cars/${car.slug}.jpg`;
    img.alt = car.name;
    img.draggable = false;
    btn.appendChild(img);

    btn.addEventListener("pointerdown", () => onPick(btn, car));
    grid.appendChild(btn);
  }

  setTimeout(askQuestion, 400);
}

function onPick(btn, car) {
  if (busy) return;
  if (car === currentTarget) {
    busy = true;
    btn.classList.add("correct");
    document.querySelectorAll(".car-card").forEach((el) => {
      if (el !== btn) el.classList.add("dim");
    });
    stars++;
    renderStars();
    showFeedback(CELEBRATE_EMOJIS[Math.floor(Math.random() * CELEBRATE_EMOJIS.length)]);
    burstConfetti(btn);

    const n = 1 + Math.floor(Math.random() * PRAISE_COUNT);
    playClip(`praise_${n}`);

    setTimeout(newRound, 2300);
  } else {
    btn.classList.add("wrong");
    setTimeout(() => btn.classList.remove("wrong"), 600);
    // 「それは、〇〇だね。」→ もう一度質問
    playClip(`n_${car.slug}`, () => {
      if (!busy) setTimeout(askQuestion, 350);
    });
  }
}

// ---- ui -------------------------------------------------------------------
function renderStars() {
  const el = document.getElementById("stars");
  if (stars <= 5) {
    el.textContent = "⭐".repeat(stars);
  } else {
    el.textContent = `⭐×${stars}`;
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

function burstConfetti(fromEl) {
  const box = document.getElementById("confetti");
  const rect = fromEl.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  for (let i = 0; i < 14; i++) {
    const s = document.createElement("span");
    s.className = "confetti-piece";
    s.textContent = CONFETTI_EMOJIS[Math.floor(Math.random() * CONFETTI_EMOJIS.length)];
    const angle = Math.random() * Math.PI * 2;
    const dist = 90 + Math.random() * 160;
    s.style.left = `${cx}px`;
    s.style.top = `${cy}px`;
    s.style.setProperty("--dx", `${Math.cos(angle) * dist}px`);
    s.style.setProperty("--dy", `${Math.sin(angle) * dist - 60}px`);
    s.style.setProperty("--rot", `${(Math.random() - 0.5) * 540}deg`);
    box.appendChild(s);
    setTimeout(() => s.remove(), 1300);
  }
}

// ---- boot -----------------------------------------------------------------
document.getElementById("start-btn").addEventListener("click", () => {
  // ユーザー操作の中で一度 play して iOS の audio を unlock する
  playClip("start");
  document.getElementById("start-screen").classList.add("hidden");
  document.getElementById("game-screen").classList.remove("hidden");
  setTimeout(newRound, 1600);
});

document.getElementById("replay-btn").addEventListener("click", () => {
  if (currentTarget && !busy) askQuestion();
});

// 画像の先読み
for (const car of CARS) {
  const img = new Image();
  img.src = `images/cars/${car.slug}.jpg`;
}

document.addEventListener("dblclick", (e) => e.preventDefault(), { passive: false });
