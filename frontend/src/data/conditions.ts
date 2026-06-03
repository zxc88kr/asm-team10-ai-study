import type { Listing, ConditionCard, MatchResult } from '../types'

export const CONDITION_CARDS: Record<string, ConditionCard> = {
  gangnam_commute: {
    label: '강남역 출퇴근 35분 이내',
    category: '출퇴근',
    weight: 3,
    source: 'said',
    reason: '"강남역 근처 회사에 다녀요"',
    match(L: Listing): MatchResult {
      if (L.commuteMin <= 20) return { status: 'full', evidence: `출퇴근 ${L.commuteMin}분` }
      if (L.commuteMin <= 35) return { status: 'partial', evidence: `출퇴근 ${L.commuteMin}분 (조건 내)` }
      return { status: 'none', evidence: `출퇴근 ${L.commuteMin}분 (초과)` }
    },
  },
  budget_75: {
    label: '월 고정비 75만 원 이하',
    category: '비용',
    weight: 3,
    source: 'said',
    reason: '"관리비 포함 75만 원 이하"',
    match(L: Listing): MatchResult {
      if (L.rent <= 70) return { status: 'full', evidence: `월세 ${L.rent}만 원` }
      if (L.rent <= 75) return { status: 'full', evidence: `월세 ${L.rent}만 원 (예산 내)` }
      if (L.rent <= 80) return { status: 'partial', evidence: `월세 ${L.rent}만 원 (5만 원 초과)` }
      return { status: 'none', evidence: `월세 ${L.rent}만 원 (예산 초과)` }
    },
  },
  no_basement: {
    label: '반지하 제외',
    category: '구조',
    weight: 2,
    source: 'said',
    reason: '"반지하는 싫어요"',
    match(L: Listing): MatchResult {
      if (L.floor >= 1) return { status: 'full', evidence: `${L.floor}층` }
      return { status: 'none', evidence: '반지하 또는 지하' }
    },
  },
  night_safe: {
    label: '심야 귀가 안전',
    category: '안전',
    weight: 3,
    source: 'inferred',
    reason: '"밤 11시쯤 끝날 것 같아요" — 귀가 안전 최우선',
    match(L: Listing): MatchResult {
      const n = L.night
      if (n.lit && n.mainRoad && n.alleyM <= 100)
        return { status: 'full', evidence: `큰길·가로등 양호, 골목 ${n.alleyM}m` }
      if (n.lit || n.mainRoad)
        return { status: 'partial', evidence: n.mainRoad ? `큰길이나 골목 ${n.alleyM}m 구간` : '가로등은 있으나 큰길 아님' }
      return { status: 'none', evidence: `어두운 골목 ${n.alleyM}m` }
    },
  },
  night_transit: {
    label: '심야 교통',
    category: '출퇴근',
    weight: 1,
    source: 'inferred',
    reason: '밤 11시 귀가 — 막차·심야버스 필요',
    match(L: Listing): MatchResult {
      if (L.nightTransit === 'good') return { status: 'full', evidence: '심야버스/막차 늦음' }
      if (L.nightTransit === 'ok') return { status: 'partial', evidence: '막차 다소 이름' }
      return { status: 'none', evidence: '심야 교통 불편' }
    },
  },
}

export const CATEGORY_CLASS: Record<string, string> = {
  안전: 'cat-safe',
  비용: 'cat-cost',
  출퇴근: 'cat-commute',
  구조: 'cat-struct',
  편의: 'cat-conv',
}
