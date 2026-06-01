export const LISTINGS = [
  {
    id: 'A', name: '햇살빌라 301호', type: '빌라', area: '신촌', deposit: 1000, rent: 48, pyeong: 7, floor: 3,
    options: ['풀옵션', '에어컨', '세탁기', '냉장고', '인덕션'], walkMin: 12,
    night: { lit: true, mainRoad: true, alleyM: 40 }, nightTransit: 'ok', thumb: '🏠',
    desc: '남향이라 채광이 좋고 환기가 잘 됩니다. 정류장에서 큰길만 따라오면 되는 위치라 밤에도 안심이에요. 풀옵션으로 바로 입주 가능.',
  },
  {
    id: 'B', name: '역세권 오피스텔 1107', type: '오피스텔', area: '△△역', deposit: 1000, rent: 53, pyeong: 8, floor: 11,
    options: ['풀옵션', '에어컨', '세탁기', '냉장고', '전자레인지', '붙박이장'], walkMin: 8,
    night: { lit: true, mainRoad: true, alleyM: 20 }, nightTransit: 'good', thumb: '🏢',
    desc: '역에서 도보 5분, 심야버스 정류장 바로 앞이라 늦은 귀가도 편합니다. 보안 출입에 CCTV 완비. 원룸 일체형 구조이며 채광 양호.',
  },
  {
    id: 'C', name: '조용한 원룸 B102', type: '원룸', area: '회기', deposit: 500, rent: 45, pyeong: 6, floor: 1,
    options: ['에어컨', '냉장고'], walkMin: 20,
    night: { lit: false, mainRoad: false, alleyM: 180 }, nightTransit: 'poor', thumb: '🏚️',
    desc: '복층 구조에 채광과 통풍이 좋아 요리하기 좋습니다. 다만 골목 안쪽이라 밤길은 다소 어두운 편이에요. 보증금이 저렴.',
  },
  {
    id: 'D', name: '신축 분리형 룸 502', type: '빌라', area: '안암', deposit: 1500, rent: 55, pyeong: 9, floor: 5,
    options: ['풀옵션', '에어컨', '세탁기', '냉장고', '인덕션', '식기세척기'], walkMin: 10,
    night: { lit: true, mainRoad: true, alleyM: 30 }, nightTransit: 'good', thumb: '✨',
    desc: '신축 분리형 구조로 방과 주방이 나뉘어 환기가 뛰어납니다. 풀옵션에 보안도 우수. (보증금이 다소 높음)',
  },
  {
    id: 'E', name: '큰길 풀옵 원룸 204', type: '원룸', area: '노원', deposit: 900, rent: 50, pyeong: 6, floor: 2,
    options: ['풀옵션', '에어컨', '세탁기', '냉장고'], walkMin: 25,
    night: { lit: true, mainRoad: true, alleyM: 50 }, nightTransit: 'ok', thumb: '🏠',
    desc: '대로변에 접해 밤에도 환하고 안전합니다. 풀옵션 완비. 다만 학교까지는 버스를 타야 하는 거리예요.',
  },
  {
    id: 'F', name: '복층 원룸 401', type: '원룸', area: '신촌', deposit: 1000, rent: 49, pyeong: 7, floor: 4,
    options: ['에어컨', '세탁기', '냉장고'], walkMin: 15,
    night: { lit: false, mainRoad: false, alleyM: 120 }, nightTransit: 'ok', thumb: '🏠',
    desc: '복층이라 공간이 넉넉하고 채광·환기가 좋아 자취 요리에 제격입니다. 학교도 가깝지만, 막다른 골목이라 밤길은 신경 쓰여요.',
  },
]
