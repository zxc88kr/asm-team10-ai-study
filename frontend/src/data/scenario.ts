import type { ScenarioStep, HardConstraints } from '../types'

const SCHOOL = '○○대'

export const GREETING = '안녕하세요, 첫 자취 준비를 도와드릴 RoomPilot이에요 🙂 어떤 집을 찾고 계세요? 편하게 말씀해 주세요.'

export const SCENARIO: ScenarioStep[] = [
  {
    userText: `${SCHOOL} 신입인데 자취가 처음이에요. 보증금 1000에 월세 50 정도 생각해요.`,
    hard: { deposit: 1000, rent: 50 } satisfies HardConstraints,
    cards: ['school_near'],
    aiText: '좋아요. 보증금 1,000·월세 50으로 잡고 학교 근처부터 볼게요. 본가가 멀어 자주 오가긴 어려우세요?',
  },
  {
    userText: '대구라서 한 학기에 두세 번밖에 못 내려가요.',
    cards: ['fulloption'],
    aiText: '그러면 짐을 자주 옮기기 어려우니 풀옵션·기본가전 갖춘 집이 부담이 적어요. 그 조건을 추가해둘게요. 혹시 저녁 알바도 생각하세요? 귀가 시간대가 중요해질 수 있어요.',
  },
  {
    userText: '네, 카페 알바라 밤 11시쯤 끝날 것 같아요.',
    cards: ['safe_route', 'night_transit'],
    aiText: '밤 11시 귀가라면 안전이 가장 중요하겠네요. \'귀가 안전동선\'과 \'심야 교통\'을 우선 조건으로 올렸어요. 마지막으로, 요리는 자주 하실 편이에요?',
  },
  {
    userText: '자취하면 거의 해먹으려고요.',
    cards: ['separated_vent'],
    aiText: '그럼 냄새·환기를 위해 분리형이나 환기 잘 되는 구조가 좋아요. 조건이 충분히 모였어요! 우선순위를 \'안전 › 비용 › 통학\'으로 두고 매물을 찾아볼게요 🔎',
    recommend: true,
  },
]

export const PRIORITY: string[] = ['안전', '비용', '통학']
