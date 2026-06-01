import useAppStore from '../store/useAppStore'
import { CONDITION_CARDS } from '../data/conditions'

const STEPS = [
  { n: 1, label: '니즈 파악' },
  { n: 2, label: '매물 추천' },
  { n: 3, label: '입지 분석' },
]

export default function Sidebar() {
  const currentStep = useAppStore(s => s.currentStep)
  const cards = useAppStore(s => s.cards)
  const hard = useAppStore(s => s.hard)

  const said = Object.keys(hard).length + cards.filter(c => CONDITION_CARDS[c].source === 'said').length
  const inferred = cards.filter(c => CONDITION_CARDS[c].source === 'inferred').length

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" />
        <span className="brand-name">RoomPilot</span>
      </div>

      <nav className="nav">
        <a className="nav-item active"><span className="nav-ic">💬</span> 대화</a>
        <a className="nav-item"><span className="nav-ic">🏠</span> 추천 매물</a>
        <a className="nav-item"><span className="nav-ic">📍</span> 입지 분석</a>
        <a className="nav-item"><span className="nav-ic">🔖</span> 저장한 매물</a>
      </nav>

      <div className="steps">
        <div className="steps-title">진행 단계</div>
        <ol className="step-list">
          {STEPS.map(({ n, label }) => (
            <li
              key={n}
              className={`step${currentStep === n ? ' active' : ''}${currentStep > n ? ' done' : ''}`}
            >
              <span className="step-dot">{n}</span>
              <span className="step-label">{label}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="sidebar-foot">
        <div className="kpi-card">
          <div className="kpi-title">차별점 지표</div>
          <div className="kpi-line">내가 말한 조건 <b>{said}</b></div>
          <div className="kpi-line accent">AI가 발굴한 조건 <b>{inferred}</b></div>
          <div className="kpi-hint">태그 검색은 '말한 것'만, RoomPilot은 '몰랐던 것'까지 찾아줍니다.</div>
        </div>
      </div>
    </aside>
  )
}
