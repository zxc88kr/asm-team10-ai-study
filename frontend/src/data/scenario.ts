import type { ScenarioStep, HardConstraints } from '../types'

export const GREETING = '안녕하세요! AI 주거 코치입니다.\n대화로 조건을 파악하고 맞춤 매물을 추천해드립니다.\n\n자취를 준비 중이신가요? 회사나 학교 위치와 월 예산을 알려주시면 조건을 정리해드릴게요.'

export const SCENARIO: ScenarioStep[] = [
  {
    userText: '강남역 근처 회사에 다녀요.',
    hard: { deposit: 10000, rent: 75 } satisfies HardConstraints,
    cards: ['gangnam_commute'],
    aiText: '좋습니다. 강남역 접근성을 기준으로 찾아볼게요. 관리비 포함 월 고정비는 어느 정도 생각하세요?',
  },
  {
    userText: '관리비 포함 75만 원 이하이면 좋겠어요.',
    cards: ['budget_75'],
    aiText: '월 75만 원 이하로 잡겠습니다. 출퇴근 시간 기준은 어느 정도까지 괜찮으세요? 그리고 특별히 피하고 싶은 조건이 있으신가요?',
  },
  {
    userText: '출퇴근은 35분 이내면 좋겠고 반지하는 싫어요.',
    hard: { commuteMax: 35, noBasement: true } satisfies HardConstraints,
    cards: ['no_basement'],
    aiText: '출퇴근 35분 이내, 반지하 제외로 설정했어요. 혹시 밤늦게 귀가하시는 일이 많으신가요?',
  },
  {
    userText: '카페 알바라 밤 11시쯤 끝날 것 같아요.',
    cards: ['night_safe', 'night_transit'],
    aiText: '심야 귀가가 잦으시군요. 귀가 안전 동선과 심야 교통을 우선 조건에 추가했어요. 조건이 충분히 모였네요! 후보 매물을 찾아볼게요 🔎',
    recommend: true,
  },
]

export const PRIORITY: string[] = ['비용', '출퇴근', '안전']
