/* =====================================================================
 * RoomPilot 프로토타입 — 시드 데이터 / 시나리오 / 조건 카드 정의
 *
 * 주의: 이 프로토타입은 GitHub Pages용 정적 데모입니다.
 * 실제 구현은 기획서대로 LangGraph 오케스트레이션 + Claude API로
 * 조건 추출/발굴/의미매칭을 수행합니다. 여기서는 그 흐름을
 * 시드 데이터와 규칙 기반 매칭으로 "재현"해 보여줍니다.
 * ===================================================================== */

const SCHOOL = "○○대";

/* ── 조건 카드 정의 ─────────────────────────────────────────────────
 * 각 카드: 라벨, 카테고리, 가중치, 출처(말함|AI추론), 근거,
 *          그리고 매물 L을 평가하는 match(L) → {status, evidence}
 * status: 'full'(충족) | 'partial'(부분) | 'none'(미충족)
 * ─────────────────────────────────────────────────────────────────── */
const CONDITION_CARDS = {
  school_near: {
    label: `${SCHOOL} 근처 (통학)`, category: "통학", weight: 2,
    source: "said", reason: `"${SCHOOL} 신입이에요"`,
    match(L) {
      if (L.walkMin <= 15) return { status: "full", evidence: `학교 도보 ${L.walkMin}분` };
      if (L.walkMin <= 25) return { status: "partial", evidence: `학교 도보 ${L.walkMin}분 (조금 멈)` };
      return { status: "none", evidence: `학교 도보 ${L.walkMin}분` };
    },
  },
  fulloption: {
    label: "풀옵션·기본가전", category: "구조", weight: 2,
    source: "inferred", reason: "본가가 멀어 세팅·왕복 부담을 줄여야 함",
    match(L) {
      if (/풀옵션|옵션 완비|가전 포함/.test(L.desc) || L.options.includes("풀옵션"))
        return { status: "full", evidence: "‘풀옵션’ 명시" };
      if (L.options.length >= 3)
        return { status: "partial", evidence: `옵션 ${L.options.length}개 (${L.options.slice(0, 3).join("·")})` };
      return { status: "none", evidence: "옵션 정보 부족" };
    },
  },
  safe_route: {
    label: "귀가 안전동선", category: "안전", weight: 3,
    source: "inferred", reason: "밤 11시 알바 귀가 — 안전이 최우선",
    match(L) {
      const n = L.night;
      if (n.lit && n.mainRoad && n.alleyM <= 80)
        return { status: "full", evidence: `큰길·가로등 양호, 골목 ${n.alleyM}m` };
      if (n.lit || n.mainRoad)
        return { status: "partial", evidence: n.mainRoad ? `큰길이나 골목 ${n.alleyM}m 구간` : "가로등은 있으나 큰길 아님" };
      return { status: "none", evidence: `어두운 골목 ${n.alleyM}m` };
    },
  },
  night_transit: {
    label: "심야 교통", category: "통학", weight: 1,
    source: "inferred", reason: "밤 11시 귀가 — 막차·심야버스 필요",
    match(L) {
      if (L.nightTransit === "good") return { status: "full", evidence: "심야버스/막차 늦음" };
      if (L.nightTransit === "ok") return { status: "partial", evidence: "막차 다소 이름" };
      return { status: "none", evidence: "심야 교통 불편" };
    },
  },
  separated_vent: {
    label: "분리형·환기", category: "구조", weight: 2,
    source: "inferred", reason: "요리를 자주 해 냄새·환기가 중요",
    match(L) {
      const kws = ["분리형", "복층", "채광", "환기", "볕", "통풍", "남향"];
      const hit = kws.filter((k) => L.desc.includes(k));
      if (hit.includes("분리형") || hit.length >= 2)
        return { status: "full", evidence: `설명에서 ‘${hit.slice(0, 2).join("·")}’ 포착` };
      if (hit.length === 1) return { status: "partial", evidence: `설명에서 ‘${hit[0]}’ 포착` };
      return { status: "none", evidence: "분리형·환기 단서 없음" };
    },
  },
};

/* ── 카테고리 색상 키 (CSS와 매핑) ─────────────────────────────────── */
const CATEGORY_CLASS = { 안전: "cat-safe", 비용: "cat-cost", 통학: "cat-commute", 구조: "cat-struct", 편의: "cat-conv" };

/* ── 매물 시드 데이터 (LLM 생성+검수 가정) ───────────────────────────
 * 설명(desc)을 사람 글처럼 풍부하게 둬 의미 매칭이 드러나게 함.
 * ─────────────────────────────────────────────────────────────────── */
const LISTINGS = [
  {
    id: "A", name: "햇살빌라 301호", type: "빌라", area: "신촌", deposit: 1000, rent: 48, pyeong: 7, floor: 3,
    options: ["풀옵션", "에어컨", "세탁기", "냉장고", "인덕션"], walkMin: 12,
    night: { lit: true, mainRoad: true, alleyM: 40 }, nightTransit: "ok", thumb: "🏠",
    desc: "남향이라 채광이 좋고 환기가 잘 됩니다. 정류장에서 큰길만 따라오면 되는 위치라 밤에도 안심이에요. 풀옵션으로 바로 입주 가능.",
  },
  {
    id: "B", name: "역세권 오피스텔 1107", type: "오피스텔", area: "△△역", deposit: 1000, rent: 53, pyeong: 8, floor: 11,
    options: ["풀옵션", "에어컨", "세탁기", "냉장고", "전자레인지", "붙박이장"], walkMin: 8,
    night: { lit: true, mainRoad: true, alleyM: 20 }, nightTransit: "good", thumb: "🏢",
    desc: "역에서 도보 5분, 심야버스 정류장 바로 앞이라 늦은 귀가도 편합니다. 보안 출입에 CCTV 완비. 원룸 일체형 구조이며 채광 양호.",
  },
  {
    id: "C", name: "조용한 원룸 B102", type: "원룸", area: "회기", deposit: 500, rent: 45, pyeong: 6, floor: 1,
    options: ["에어컨", "냉장고"], walkMin: 20,
    night: { lit: false, mainRoad: false, alleyM: 180 }, nightTransit: "poor", thumb: "🏚️",
    desc: "복층 구조에 채광과 통풍이 좋아 요리하기 좋습니다. 다만 골목 안쪽이라 밤길은 다소 어두운 편이에요. 보증금이 저렴.",
  },
  {
    id: "D", name: "신축 분리형 룸 502", type: "빌라", area: "안암", deposit: 1500, rent: 55, pyeong: 9, floor: 5,
    options: ["풀옵션", "에어컨", "세탁기", "냉장고", "인덕션", "식기세척기"], walkMin: 10,
    night: { lit: true, mainRoad: true, alleyM: 30 }, nightTransit: "good", thumb: "✨",
    desc: "신축 분리형 구조로 방과 주방이 나뉘어 환기가 뛰어납니다. 풀옵션에 보안도 우수. (보증금이 다소 높음)",
  },
  {
    id: "E", name: "큰길 풀옵 원룸 204", type: "원룸", area: "노원", deposit: 900, rent: 50, pyeong: 6, floor: 2,
    options: ["풀옵션", "에어컨", "세탁기", "냉장고"], walkMin: 25,
    night: { lit: true, mainRoad: true, alleyM: 50 }, nightTransit: "ok", thumb: "🏠",
    desc: "대로변에 접해 밤에도 환하고 안전합니다. 풀옵션 완비. 다만 학교까지는 버스를 타야 하는 거리예요.",
  },
  {
    id: "F", name: "복층 원룸 401", type: "원룸", area: "신촌", deposit: 1000, rent: 49, pyeong: 7, floor: 4,
    options: ["에어컨", "세탁기", "냉장고"], walkMin: 15,
    night: { lit: false, mainRoad: false, alleyM: 120 }, nightTransit: "ok", thumb: "🏠",
    desc: "복층이라 공간이 넉넉하고 채광·환기가 좋아 자취 요리에 제격입니다. 학교도 가깝지만, 막다른 골목이라 밤길은 신경 쓰여요.",
  },
];

/* ── 인터뷰 시나리오 (민지: 상경 대학 신입생) ───────────────────────
 * 각 단계: 사용자 발화 → 하드 제약/조건 카드 추가 → AI 응답
 * recommend:true 인 단계 이후 매물 추천이 실행됨
 * ─────────────────────────────────────────────────────────────────── */
const GREETING = "안녕하세요, 첫 자취 준비를 도와드릴 RoomPilot이에요 🙂 어떤 집을 찾고 계세요? 편하게 말씀해 주세요.";

const SCENARIO = [
  {
    userText: `${SCHOOL} 신입인데 자취가 처음이에요. 보증금 1000에 월세 50 정도 생각해요.`,
    hard: { deposit: 1000, rent: 50 },
    cards: ["school_near"],
    aiText: "좋아요. 보증금 1,000·월세 50으로 잡고 학교 근처부터 볼게요. 본가가 멀어 자주 오가긴 어려우세요?",
  },
  {
    userText: "대구라서 한 학기에 두세 번밖에 못 내려가요.",
    cards: ["fulloption"],
    aiText: "그러면 짐을 자주 옮기기 어려우니 풀옵션·기본가전 갖춘 집이 부담이 적어요. 그 조건을 추가해둘게요. 혹시 저녁 알바도 생각하세요? 귀가 시간대가 중요해질 수 있어요.",
  },
  {
    userText: "네, 카페 알바라 밤 11시쯤 끝날 것 같아요.",
    cards: ["safe_route", "night_transit"],
    aiText: "밤 11시 귀가라면 안전이 가장 중요하겠네요. ‘귀가 안전동선’과 ‘심야 교통’을 우선 조건으로 올렸어요. 마지막으로, 요리는 자주 하실 편이에요?",
  },
  {
    userText: "자취하면 거의 해먹으려고요.",
    cards: ["separated_vent"],
    aiText: "그럼 냄새·환기를 위해 분리형이나 환기 잘 되는 구조가 좋아요. 조건이 충분히 모였어요! 우선순위를 ‘안전 › 비용 › 통학’으로 두고 매물을 찾아볼게요 🔎",
    recommend: true,
  },
];

/* 우선순위(데모 고정) — 실제로는 사용자가 편집 */
const PRIORITY = ["안전", "비용", "통학"];
