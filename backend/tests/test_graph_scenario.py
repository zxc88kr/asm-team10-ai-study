"""민지 시나리오 E2E (오케스트레이션 §9 트레이스). mock provider로 결정적 검증."""


from app.runtime import drive, new_session

T1 = "부산대 신입인데 자취 처음이에요. 보증금 1000에 월세 50 정도로 보고 있어요. 관리비는 5~7만까지 괜찮아요."
T2 = "밤 11시쯤 집에 들어가요. 본가가 서울이라 자주 못 와요. 요리도 자주 하는 편이에요."


def _events(result, etype):
    return [e for e in result["events"] if e.get("type") == etype]


def _run_needs_phase(sid):
    """T1 → T2 → 역질문 3회 응답 → 우선순위 편집까지 진행, 최종 결과 반환."""
    drive(sid, T1)
    drive(sid, T2)
    drive(sid, resume="어두운 골목은 무서울 것 같아요.")
    drive(sid, resume="택배도 챙겨주세요.")
    drive(sid, resume="곰팡이나 습기는 싫어요.")
    return drive(sid, resume={"order": ["safety", "budget", "commute"]})


def test_scene1_hard_cards_only_then_lifestyle_prompt():
    sid = new_session()
    r = drive(sid, T1)
    cards = _events(r, "card")
    assert {c["card"]["label"] for c in cards} == {"지역", "예산"}
    assert all(c["card"]["source"] == "said" for c in cards)
    assert not r["pending"]
    assert "생활" in _events(r, "message")[0]["text"]


def test_scene2_first_blind_spot_is_safety():
    sid = new_session()
    drive(sid, T1)
    r = drive(sid, T2)
    assert r["pending"] and r["next"] == ("discover",)
    q = _events(r, "question")[0]
    assert q["category"] == "safety"  # 우선순위 1순위 사각지대


def test_needs_phase_produces_top3_and_ratio():
    sid = new_session()
    r = _run_needs_phase(sid)
    ranked = _events(r, "ranked")[-1]["ranked"]
    assert [x["listingId"] for x in ranked] == ["A", "B", "C"]
    assert ranked[0]["score"] > ranked[1]["score"] > ranked[2]["score"]
    # 차별 지표: 직접 2 : 발굴/추출 6 → 1:6 (스펙 메트릭 계약)
    assert "1:6" in _events(r, "message")[0]["text"]


def test_differentiation_metric_streamed():
    sid = new_session()
    drive(sid, T1)
    r = drive(sid, T2)  # 소프트 카드 추가되며 비율 갱신
    metric = _events(r, "metric")[-1]
    assert metric["said"] == 2 and metric["derived"] >= 3


def test_groundedness_refuses_unknown_attribute():
    sid = new_session()
    _run_needs_phase(sid)
    r = drive(sid, "C는 방음 어때요?")
    text = _events(r, "message")[0]["text"]
    assert "지어내" in text and "방음" in text  # 설명에 없는 정보 → 환각 회피


def test_location_explained_in_card_terms():
    sid = new_session()
    _run_needs_phase(sid)
    r = drive(sid, "입지 설명해줘")
    locs = _events(r, "location")
    assert locs and locs[0]["listingId"] == "A"  # TOP-1 기본 선택
    assert "카드" in _events(r, "message")[0]["text"]


def test_loopback_reranks_and_promotes_new_listing():
    sid = new_session()
    _run_needs_phase(sid)
    drive(sid, "입지 설명해줘")
    r = drive(sid, "월세 5만 더 올리면 뭐가 달라져요?")
    ranked = _events(r, "ranked")[-1]["ranked"]
    assert ranked[0]["listingId"] == "D"  # 예산 +5 → D신축빌라 신규 1위
    assert [x["listingId"] for x in ranked][:3] == ["D", "A", "B"]
    assert "D신축빌라" in _events(r, "message")[0]["text"]


def test_discovered_cards_are_marked_inferred():
    sid = new_session()
    drive(sid, T1)
    drive(sid, T2)
    r = drive(sid, resume="어두운 골목은 무서울 것 같아요.")
    card = _events(r, "card")[0]["card"]
    assert card["source"] == "discovered"
    assert card["reason"].startswith("(추론)")
