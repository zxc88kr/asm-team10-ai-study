import { Home, MessageCircle, Building2, MapPin, Bookmark, Check } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import useAppStore from '../store/useAppStore'

interface NavItem {
  icon: LucideIcon
  label: string
  id: string
}

const NAV_ITEMS: NavItem[] = [
  { icon: Home, label: '홈', id: 'home' },
  { icon: MessageCircle, label: '대화', id: 'chat' },
  { icon: Building2, label: '추천 매물', id: 'listings' },
  { icon: MapPin, label: '입지 분석', id: 'analysis' },
  { icon: Bookmark, label: '저장한 매물', id: 'saved' },
]

interface StepConfig {
  label: string
  statusMap: Record<number, string>
}

const STEPS: StepConfig[] = [
  { label: '니즈 파악', statusMap: { 1: '진행 중', 2: '완료', 3: '완료' } },
  { label: '매물 추천', statusMap: { 1: '대기 중', 2: '진행 중', 3: '완료' } },
  { label: '입지 분석', statusMap: { 1: '대기 중', 2: '대기 중', 3: '진행 중' } },
]

function getStepState(stepIdx: number, currentStep: number): 'done' | 'active' | 'waiting' {
  if (currentStep > stepIdx + 1) return 'done'
  if (currentStep === stepIdx + 1) return 'active'
  return 'waiting'
}

export default function Sidebar() {
  const { currentStep, activeView, openAnalysis, closeAnalysis, lastTop } = useAppStore()

  const handleNavClick = (id: string) => {
    if (id === 'chat') closeAnalysis()
    if (id === 'analysis' && lastTop && lastTop.length > 0) {
      openAnalysis(lastTop[0].L.id)
    }
  }

  const activeNavId = activeView === 'analysis' ? 'analysis' : 'chat'
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Home size={20} strokeWidth={2.5} /></div>
        <span className="brand-name">RoomPilot</span>
      </div>

      <nav className="nav">
        {NAV_ITEMS.map(item => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              className={`nav-item${activeNavId === item.id ? ' active' : ''}`}
              onClick={() => handleNavClick(item.id)}
              type="button"
            >
              <span className="nav-ic"><Icon size={18} /></span>
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="steps-section">
        <div className="steps-title">에이전트 진행</div>
        <ul className="step-list">
          {STEPS.map((step, i) => {
            const state = getStepState(i, currentStep)
            return (
              <li key={step.label} className={`step ${state === 'done' ? 'done' : state === 'active' ? 'active' : ''}`}>
                <div className="step-dot">
                  {state === 'done' ? <Check size={14} strokeWidth={3} /> : i + 1}
                </div>
                <div className="step-text">
                  <span className="step-label">{step.label}</span>
                  <span className="step-status">{step.statusMap[currentStep]}</span>
                </div>
              </li>
            )
          })}
        </ul>
      </div>

    </aside>
  )
}
