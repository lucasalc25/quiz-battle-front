// === Config ===
const API = "https://lucasalc25-quiz-battle-api.hf.space";

// Firebase minimal config (substitua pelos seus dados do Console)
const firebaseConfig = {
  apiKey: "SUA_API_KEY",
  authDomain: "SEU_PROJETO.firebaseapp.com",
  projectId: "SEU_PROJETO",
};
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// === Helpers ===
const qs = (s) => document.querySelector(s);
const authBox = qs("#auth");
const gameBox = qs("#game");
const finalBox = qs("#final");
const msg = qs("#msg");

let username = "";
let score = 0;
let totalQuestions = 10;
let current = 0;
let timer = null;
let timeLeft = 15;

function show(box) {
  [authBox, gameBox, finalBox].forEach((b) => b.classList.add("hidden"));
  box.classList.remove("hidden");
}

async function idToken() {
  const user = auth.currentUser;
  if (!user) return "";
  return await user.getIdToken();
}

async function authedFetch(path, opts = {}) {
  const token = await idToken();
  return fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  });
}

// === Auth UI ===
qs("#loginBtn").onclick = async () => {
  const email = qs("#email").value.trim();
  const password = qs("#password").value;
  try {
    await auth.signInWithEmailAndPassword(email, password);
    msg.textContent = "Logado!";
  } catch (e) {
    if (e.code === "auth/user-not-found") {
      await auth.createUserWithEmailAndPassword(email, password);
      msg.textContent = "Conta criada e logada!";
    } else {
      msg.textContent = e.message;
    }
  }
};
qs("#logoutBtn").onclick = async () => {
  await auth.signOut();
  msg.textContent = "Saiu.";
};

auth.onAuthStateChanged((user) => {
  if (user) {
    // logged in
  } else {
    // logged out
  }
});

// === Game Flow ===
qs("#startBtn").onclick = () => {
  username = (qs("#username").value || "").trim();
  if (!username) {
    msg.textContent = "Defina um apelido para o ranking.";
    return;
  }
  startGame();
};

qs("#giveupBtn").onclick = () => endGame();

qs("#againBtn").onclick = () => {
  show(authBox);
  score = 0;
  current = 0;
  qs("#score").textContent = String(score);
};

async function startGame() {
  score = 0;
  current = 0;
  qs("#score").textContent = "0";
  qs("#playerName").textContent = username;
  qs("#total").textContent = totalQuestions;
  show(gameBox);
  await nextQuestion();
}

async function nextQuestion() {
  current += 1;
  if (current > totalQuestions) return endGame();
  qs("#current").textContent = current;

  // fetch question
  const res = await authedFetch("/question");
  if (!res.ok) {
    const t = await res.text();
    alert("Erro ao buscar pergunta: " + t);
    return endGame();
  }
  const q = await res.json();
  renderQuestion(q);
}

function renderQuestion(q) {
  // Reset card
  qs("#qtext").textContent = q.question;
  const ops = qs("#options");
  ops.innerHTML = "";
  q.options.forEach((text, idx) => {
    const btn = document.createElement("button");
    btn.className = "option";
    btn.textContent = text;
    btn.onclick = () => answer(q.id, idx, btn);
    ops.appendChild(btn);
  });
  // Timer
  stopTimer();
  timeLeft = 15;
  qs("#timer").textContent = timeLeft;
  timer = setInterval(() => {
    timeLeft -= 1;
    qs("#timer").textContent = timeLeft;
    if (timeLeft <= 0) {
      stopTimer();
      lockOptions();
      setTimeout(nextQuestion, 800);
    }
  }, 1000);
}

function stopTimer() {
  if (timer) clearInterval(timer);
  timer = null;
}

function lockOptions() {
  document.querySelectorAll(".option").forEach((b) => (b.disabled = true));
}

async function answer(question_id, choice_index, el) {
  lockOptions();
  stopTimer();
  const res = await authedFetch("/answer", {
    method: "POST",
    body: JSON.stringify({ question_id, choice_index }),
  });
  const data = await res.json();
  // Feedback
  const options = Array.from(document.querySelectorAll(".option"));
  options[data.correct_index]?.classList.add("correct");
  if (!data.correct) {
    el.classList.add("wrong");
  } else {
    score += 10;
    qs("#score").textContent = String(score);
  }
  setTimeout(nextQuestion, 600);
}

async function endGame() {
  show(finalBox);
  qs("#finalScore").textContent = String(score);
  try {
    await authedFetch("/score", {
      method: "POST",
      body: JSON.stringify({ username, points: score }),
    });
  } catch (e) {}
  const res = await fetch(`${API}/ranking`);
  const list = await res.json();
  const ol = qs("#ranking");
  ol.innerHTML = "";
  list.forEach((r, i) => {
    const li = document.createElement("li");
    li.textContent = `${i + 1}. ${r.username} — ${r.points} pts`;
    ol.appendChild(li);
  });
}
