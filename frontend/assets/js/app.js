/* =====================================================================
 * RoomPilot 프로토타입 — 앱 로직
 * 인터뷰(추출 A + 발굴 C) → 조건 카드 → 의미 매칭 점수 → 입지 해석 → 루프백
 * ===================================================================== */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const RENT_ALLOWANCE = 5; // 월세 상한 초과 허용폭(만원): 초과해도 탈락 아닌 감점
  const STATUS_VAL = { full: 1, partial: 0.5, none: 0 };
  const STATUS_KO = { full: "충족", partial: "부분", none: "미흡" };

  /* ── 상태 ─────────────────────────────────────────────── */
  const state = {
    turn: 0,            // 진행된 시나리오 단계 수
    hard: {},           // 하드 제약 (deposit, rent)
    cards: [],          // 추가된 조건 카드 id (순서대로)
    recommended: false, // 추천 1회 이상 실행됨
  };

  /* ── 채팅 ─────────────────────────────────────────────── */
  function bubble(role, text) {
    const wrap = document.createElement("div");
    wrap.className = `msg ${role}`;
    if (role === "ai") {
      const av = document.createElement("div");
      av.className = "avatar";
      av.textContent = "🤖";
      wrap.appendChild(av);
    }
    const b = document.createElement("div");
    b.className = "bubble";
    b.textContent = text;
    wrap.appendChild(b);
    $("chatScroll").appendChild(wrap);
    scrollChat();
    return wrap;
  }

  function typing() {
    const wrap = document.createElement("div");
    wrap.className = "msg ai typing";
    wrap.innerHTML =
      '<div class="avatar">🤖</div><div class="bubble"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
    $("chatScroll").appendChild(wrap);
    scrollChat();
    return wrap;
  }

  function scrollChat() {
    const s = $("chatScroll");
    s.scrollTop = s.scrollHeight;
  }

  function aiSay(text, after) {
    const t = typing();
    setTimeout(() => {
      t.remove();
      bubble("ai", text);
      if (after) after();
    }, 650);
  }

  /* ── 진행: 사용자 발화 → 카드 처리 → AI 응답 ───────────── */
  function advance(displayText) {
    const step = SCENARIO[state.turn];
    if (!step) return;
    bubble("user", displayText || step.userText);
    setQuick(null); // 처리 중에는 잠금

    // 하드 제약 병합
    if (step.hard) Object.assign(state.hard, step.hard);
    // 조건 카드 추가 (약간의 시차로 "발굴되는" 느낌)
    (step.cards || []).forEach((cid, i) => {
      setTimeout(() => addCard(cid), 300 + i * 260);
    });

    state.turn += 1;

    aiSay(step.aiText, () => {
      if (step.recommend) {
        runRecommendation(true);
      }
      // 다음 추천 답변 노출
      const next = SCENARIO[state.turn];
      if (next) setQuick(next.userText);
      else setQuick(null);
    });
  }

  /* ── 조건 카드 ─────────────────────────────────────────── */
  function addCard(cid) {
    if (state.cards.includes(cid)) return;
    state.cards.push(cid);
    renderProfile();
    updateKpi();
  }

  function renderProfile() {
    const list = $("condList");
    list.innerHTML = "";
    $("profileEmpty").hidden = state.cards.length > 0 || Object.keys(state.hard).length > 0;

    // 하드 제약을 먼저 (말한 조건)
    if (state.hard.deposit)
      list.appendChild(condItem("비용", "보증금", `${state.hard.deposit.toLocaleString()}만원 이하`, "said", "직접 입력"));
    if (state.hard.rent)
      list.appendChild(condItem("비용", "월세", `${state.hard.rent}만원 이하`, "said", "직접 입력"));

    // 소프트 카드
    state.cards.forEach((cid) => {
      const c = CONDITION_CARDS[cid];
      list.appendChild(condItem(c.category, c.label, "", c.source, c.reason));
    });

    // 우선순위
    if (state.cards.length || Object.keys(state.hard).length) {
      $("priorityBox").hidden = false;
      $("priChips").innerHTML = PRIORITY.map((p, i) => `<span class="pri-chip">${i + 1}. ${p}</span>`).join("");
    }
  }

  function condItem(category, label, value, source, reason) {
    const li = document.createElement("li");
    li.className = "cond-item enter";
    const dot = `<span class="cat-dot ${CATEGORY_CLASS[category] || ""}"></span>`;
    const tag =
      source === "said"
        ? '<span class="src said">말함</span>'
        : '<span class="src inferred">AI 발굴</span>';
    li.innerHTML = `
      <div class="cond-top">${dot}<span class="cond-label">${label}</span>${tag}</div>
      ${value ? `<div class="cond-val">${value}</div>` : ""}
      ${reason ? `<div class="cond-reason">↳ ${reason}</div>` : ""}`;
    setTimeout(() => li.classList.remove("enter"), 20);
    return li;
  }

  function updateKpi() {
    const said =
      Object.keys(state.hard).length + state.cards.filter((c) => CONDITION_CARDS[c].source === "said").length;
    const inferred = state.cards.filter((c) => CONDITION_CARDS[c].source === "inferred").length;
    $("kpiSaid").textContent = said;
    $("kpiInferred").textContent = inferred;
  }

  /* ── 의미 매칭 / 추천 (Agent 2) ────────────────────────── */
  function scoreListing(L) {
    // 하드 필터
    if (L.deposit > state.hard.deposit) return { excluded: true, reason: "보증금 초과" };
    if (L.rent > state.hard.rent + RENT_ALLOWANCE) return { excluded: true, reason: "월세 초과" };

    let sum = 0,
      wsum = 0;
    const breakdown = state.cards.map((cid) => {
      const c = CONDITION_CARDS[cid];
      const r = c.match(L);
      sum += c.weight * STATUS_VAL[r.status];
      wsum += c.weight;
      return { cid, label: c.label, category: c.category, weight: c.weight, ...r };
    });
    let score = wsum ? (sum / wsum) * 100 : 0;

    // 월세 초과분 감점 (트레이드오프: 탈락 대신 감점)
    let penalty = 0;
    if (L.rent > state.hard.rent) penalty = Math.round((L.rent - state.hard.rent) * 1.6);
    score = Math.max(0, Math.round(score - penalty));

    return { excluded: false, score, breakdown, penalty };
  }

  function runRecommendation(advanceSteps) {
    const scored = LISTINGS.map((L) => ({ L, ...scoreListing(L) }));
    const ok = scored.filter((s) => !s.excluded).sort((a, b) => b.score - a.score);
    const top = ok.slice(0, 3);
    state.lastTop = top;

    if (advanceSteps) setStep(2);

    $("recEmpty").hidden = true;
    const meta = $("recMeta");
    meta.hidden = false;
    const excluded = scored.length - ok.length;
    meta.textContent = `${LISTINGS.length}개 중 ${excluded}개 제외 · 의미 매칭 랭킹`;

    const list = $("recList");
    list.innerHTML = "";
    top.forEach((s, idx) => list.appendChild(recItem(s, idx)));

    // 입지 분석 (Agent 3) — 1위 기준
    if (top[0]) {
      if (advanceSteps) setTimeout(() => setStep(3), 500);
      renderLocation(top[0]);
    }
  }

  function scoreClass(score) {
    if (score >= 85) return "sc-high";
    if (score >= 75) return "sc-mid";
    return "sc-low";
  }

  function recItem(s, idx) {
    const li = document.createElement("li");
    li.className = "rec-item enter";
    const fulls = s.breakdown.filter((b) => b.status === "full").length;
    const chips = s.breakdown
      .map((b) => `<span class="mini ${b.status}">${b.label.split(/[ ·(]/)[0]} ${STATUS_KO[b.status]}</span>`)
      .join("");
    li.innerHTML = `
      <div class="rank">${idx + 1}</div>
      <div class="thumb">${s.L.thumb}</div>
      <div class="rec-body">
        <div class="rec-name">${s.L.name}</div>
        <div class="rec-sub">${s.L.area} · ${s.L.type} · 보증금 ${s.L.deposit.toLocaleString()} / 월세 ${s.L.rent}</div>
        <div class="rec-chips">${chips}</div>
      </div>
      <div class="score ${scoreClass(s.score)}">${s.score}<span>점</span></div>`;
    setTimeout(() => li.classList.remove("enter"), 20);
    li.addEventListener("click", () => openModal(s));
    return li;
  }

  /* ── 입지 해석 (Agent 3) ───────────────────────────────── */
  function renderLocation(s) {
    const L = s.L;
    $("locEmpty").hidden = true;
    $("locBox").hidden = false;
    $("locTarget").innerHTML = `<b>1위 · ${L.name}</b> 를 당신의 생활 기준으로 해석했어요`;

    const safe = L.night.lit && L.night.mainRoad ? (L.night.alleyM <= 80 ? 0.88 : 0.62) : 0.4;
    const commute = Math.max(0.2, 1 - (L.walkMin - 8) / 30);
    const conv = Math.min(1, L.options.length / 6);
    const bars = [
      ["귀가 안전동선", safe],
      ["통학 시간", commute],
      ["편의시설", conv],
    ];
    $("locBars").innerHTML = bars
      .map(([k, v]) => {
        const cls = v >= 0.75 ? "good" : v >= 0.5 ? "ok" : "poor";
        return `<li><span class="loc-k">${k}</span><span class="bar"><span class="fill ${cls}" style="width:${Math.round(
          v * 100
        )}%"></span></span></li>`;
      })
      .join("");

    const safetyTxt = safe >= 0.85
      ? `정류장에서 큰길을 따라 도보 약 ${Math.round(L.night.alleyM / 70 + 3)}분, 가로등도 밝아 밤 11시 귀가도 안심이에요.`
      : safe >= 0.6
      ? `큰길과 가까우나 골목 ${L.night.alleyM}m 구간이 있어 늦은 귀가 시 약간 신경 쓰일 수 있어요.`
      : `골목이 어두운 편이라 밤 11시 알바 귀가에는 주의가 필요해요.`;
    $("locComment").textContent = `밤 11시 알바 귀가 기준 — ${safetyTxt} 학교까지는 도보 ${L.walkMin}분.`;
  }

  /* ── 매물 상세 모달 ────────────────────────────────────── */
  function openModal(s) {
    const L = s.L;
    const goods = s.breakdown.filter((b) => b.status === "full");
    const weaks = s.breakdown.filter((b) => b.status !== "full");
    const rows = s.breakdown
      .map(
        (b) => `<li class="bd ${b.status}">
          <span class="bd-status">${STATUS_KO[b.status]}</span>
          <span class="bd-label">${b.label}</span>
          <span class="bd-ev">${b.evidence}</span></li>`
      )
      .join("");
    const narrative = `민지님은 <b>밤 11시 알바 귀가</b>와 <b>첫 자취</b>가 핵심이었어요. 이 집은 ${
      goods.map((g) => `‘${g.label}’`).join(", ") || "기본 조건"
    }을(를) 충족해요.${weaks.length ? ` 다만 ${weaks.map((w) => `‘${w.label}’`).join(", ")}은(는) 아쉬운 점이에요.` : ""}`;

    $("modalBody").innerHTML = `
      <div class="m-head">
        <div class="m-thumb">${L.thumb}</div>
        <div>
          <h3>${L.name} <span class="score ${scoreClass(s.score)} inline">${s.score}점</span></h3>
          <p>${L.area} · ${L.type} · ${L.pyeong}평 · ${L.floor}층 · 보증금 ${L.deposit.toLocaleString()} / 월세 ${L.rent}${
      s.penalty ? ` <span class="pen">(월세 초과 −${s.penalty})</span>` : ""
    }</p>
        </div>
      </div>
      <p class="m-desc">“${L.desc}”</p>
      <div class="m-why"><b>왜 이 집인가</b><p>${narrative}</p></div>
      <div class="m-bd-title">조건별 매칭 (의미 매칭 근거)</div>
      <ul class="m-bd">${rows}</ul>`;
    $("modal").hidden = false;
  }

  /* ── 조건 편집 / 루프백 ────────────────────────────────── */
  function toggleEditor() {
    const box = $("condList");
    let editor = $("inlineEditor");
    if (editor) {
      editor.remove();
      return;
    }
    if (!state.hard.rent) {
      toast("아직 예산 조건이 없어요. 대화를 먼저 진행해 주세요.");
      return;
    }
    editor = document.createElement("div");
    editor.id = "inlineEditor";
    editor.className = "editor";
    editor.innerHTML = `
      <div class="ed-title">월세 상한 조정 (루프백 데모)</div>
      <div class="ed-row">
        <button class="ed-btn" data-d="-5">−5</button>
        <span class="ed-val"><b id="edRent">${state.hard.rent}</b> 만원</span>
        <button class="ed-btn" data-d="5">＋5</button>
      </div>
      <button class="ed-apply" id="edApply">이 조건으로 다시 추천</button>
      <div class="ed-hint">조건을 바꾸면 Agent 2·3가 다시 돌아 추천이 갱신돼요.</div>`;
    $("condList").after(editor);

    let temp = state.hard.rent;
    editor.querySelectorAll(".ed-btn").forEach((btn) =>
      btn.addEventListener("click", () => {
        temp = Math.max(20, Math.min(120, temp + Number(btn.dataset.d)));
        $("edRent").textContent = temp;
      })
    );
    $("edApply").addEventListener("click", () => {
      state.hard.rent = temp;
      renderProfile();
      editor.remove();
      if (state.recommended || state.lastTop) {
        runRecommendation(false);
        toast(`월세 상한을 ${temp}만원으로 반영해 추천을 갱신했어요.`);
      }
    });
  }

  /* ── 단계 표시 ─────────────────────────────────────────── */
  function setStep(n) {
    state.recommended = state.recommended || n >= 2;
    document.querySelectorAll("#stepList .step").forEach((li) => {
      const d = Number(li.dataset.step);
      li.classList.toggle("active", d === n);
      li.classList.toggle("done", d < n);
    });
  }

  /* ── 추천 답변 칩 ──────────────────────────────────────── */
  function setQuick(text) {
    const q = $("quickReplies");
    q.innerHTML = "";
    if (!text) return;
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.textContent = text;
    chip.addEventListener("click", () => advance(text));
    q.appendChild(chip);
  }

  /* ── 토스트 ────────────────────────────────────────────── */
  let toastTimer;
  function toast(msg) {
    const t = $("toast");
    t.textContent = msg;
    t.hidden = false;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      t.classList.remove("show");
      setTimeout(() => (t.hidden = true), 300);
    }, 2600);
  }

  /* ── 입력 처리 ─────────────────────────────────────────── */
  function onSend() {
    const inp = $("chatInput");
    const v = inp.value.trim();
    if (state.turn >= SCENARIO.length) {
      if (v) {
        bubble("user", v);
        inp.value = "";
        aiSay("이 프로토타입의 시나리오는 여기까지예요. 오른쪽 추천과 ‘조건 편집’으로 루프백을 체험해 보세요 🙂");
      }
      return;
    }
    advance(v || undefined);
    inp.value = "";
  }

  /* ── 초기화 / 리셋 ─────────────────────────────────────── */
  function reset() {
    state.turn = 0;
    state.hard = {};
    state.cards = [];
    state.recommended = false;
    state.lastTop = null;
    $("chatScroll").innerHTML = "";
    $("condList").innerHTML = "";
    $("recList").innerHTML = "";
    $("recEmpty").hidden = false;
    $("recMeta").hidden = true;
    $("locBox").hidden = true;
    $("locEmpty").hidden = false;
    $("priorityBox").hidden = true;
    $("profileEmpty").hidden = false;
    updateKpi();
    setStep(1);
    bubble("ai", GREETING);
    setQuick(SCENARIO[0].userText);
  }

  function init() {
    $("sendBtn").addEventListener("click", onSend);
    $("chatInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter") onSend();
    });
    $("restartBtn").addEventListener("click", reset);
    $("editBtn").addEventListener("click", toggleEditor);
    $("modalClose").addEventListener("click", () => ($("modal").hidden = true));
    $("modal").addEventListener("click", (e) => {
      if (e.target.id === "modal") $("modal").hidden = true;
    });
    reset();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
