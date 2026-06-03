import type { Listing, ConditionCard, MatchResult } from '../types'

const SCHOOL = '○○대'

export const CONDITION_CARDS: Record<string, ConditionCard> = {
  school_near: {
    label: `${SCHOOL} 근처 (통학)`, category: '통학', weight: 2,
    source: 'said', reason: `"${SCHOOL} 신입이에요"`,
    match(L: Listing): MatchResult {
      if (L.walkMin <= 15) return { status: 'full', evidence: `학교 도보 ${L.walkMin}분` }
      if (L.walkMin <= 25) return { status: 'partial', evidence: `학교 도보 ${L.walkMin}분 (조금 멈)` }
      return { status: 'none', evidence: `학교 도보 ${L.walkMin}분` }
    },
  },
  fulloption: {
    label: '풀옵션·기본가전', category: '구조', weight: 2,
    source: 'inferred', reason: '본가가 멀어 세팅·왕복 부담을 줄여야 함',
    match(L: Listing): MatchResult {
      if (/풀옵션|옵션 완비|가전 포함/.test(L.desc) || L.options.includes('풀옵션'))
        return { status: 'full', evidence: "'풀옵션' 명시" }
      if (L.options.length >= 3)
        return { status: 'partial', evidence: `옵션 ${L.options.length}개 (${L.options.slice(0, 3).join('·')})` }
      return { status: 'none', evidence: '옵션 정보 부족' }
    },
  },
  safe_route: {
    label: '귀가 안전동선', category: '안전', weight: 3,
    source: 'inferred', reason: '밤 11시 알바 귀가 — 안전이 최우선',
    match(L: Listing): MatchResult {
      const n = L.night
      if (n.lit && n.mainRoad && n.alleyM <= 80)
        return { status: 'full', evidence: `큰길·가로등 양호, 골목 ${n.alleyM}m` }
      if (n.lit || n.mainRoad)
        return { status: 'partial', evidence: n.mainRoad ? `큰길이나 골목 ${n.alleyM}m 구간` : '가로등은 있으나 큰길 아님' }
      return { status: 'none', evidence: `어두운 골목 ${n.alleyM}m` }
    },
  },
  night_transit: {
    label: '심야 교통', category: '통학', weight: 1,
    source: 'inferred', reason: '밤 11시 귀가 — 막차·심야버스 필요',
    match(L: Listing): MatchResult {
      if (L.nightTransit === 'good') return { status: 'full', evidence: '심야버스/막차 늦음' }
      if (L.nightTransit === 'ok') return { status: 'partial', evidence: '막차 다소 이름' }
      return { status: 'none', evidence: '심야 교통 불편' }
    },
  },
  separated_vent: {
    label: '분리형·환기', category: '구조', weight: 2,
    source: 'inferred', reason: '요리를 자주 해 냄새·환기가 중요',
    match(L: Listing): MatchResult {
      const kws = ['분리형', '복층', '채광', '환기', '볕', '통풍', '남향']
      const hit = kws.filter(k => L.desc.includes(k))
      if (hit.includes('분리형') || hit.length >= 2)
        return { status: 'full', evidence: `설명에서 '${hit.slice(0, 2).join('·')}' 포착` }
      if (hit.length === 1) return { status: 'partial', evidence: `설명에서 '${hit[0]}' 포착` }
      return { status: 'none', evidence: '분리형·환기 단서 없음' }
    },
  },
}

export const CATEGORY_CLASS: Record<string, string> = {
  안전: 'cat-safe',
  비용: 'cat-cost',
  통학: 'cat-commute',
  구조: 'cat-struct',
  편의: 'cat-conv',
}
