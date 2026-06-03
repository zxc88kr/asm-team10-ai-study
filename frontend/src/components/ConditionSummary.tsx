import { Building2, Wallet, Clock, Ban, Star, Pencil } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import useAppStore from '../store/useAppStore'
import { PRIORITY } from '../data/scenario'

interface ConditionConfig {
  key: string
  icon: LucideIcon
  iconBg: string
  label: string
  valBg: string
  valColor: string
}

const CONDITION_DISPLAY: ConditionConfig[] = [
  { key: 'company',  icon: Building2, iconBg: '#EEF3FF', label: '회사/학교',  valBg: '#EEF3FF', valColor: '#4B7BF5' },
  { key: 'rent',     icon: Wallet,    iconBg: '#DCFCE7', label: '월 고정비',  valBg: '#DCFCE7', valColor: '#16A34A' },
  { key: 'commute',  icon: Clock,     iconBg: '#DCFCE7', label: '출퇴근',     valBg: '#DCFCE7', valColor: '#16A34A' },
  { key: 'exclude',  icon: Ban,       iconBg: '#FEE2E2', label: '제외 조건',  valBg: '#FEE2E2', valColor: '#DC2626' },
  { key: 'priority', icon: Star,      iconBg: '#FEF3C7', label: '우선순위',   valBg: '#FEF3C7', valColor: '#D97706' },
]

export default function ConditionSummary({ showEdit = false }: { showEdit?: boolean }) {
  const { hard, cards } = useAppStore()

  const companyVal = cards.includes('gangnam_commute') ? '강남역' : null
  const rentVal = hard.rent ? `${hard.rent}만 원 이하` : null
  const commuteVal = hard.commuteMax ? `${hard.commuteMax}분 이내` : null
  const excludeVal = hard.noBasement ? '반지하' : null
  const priorityVal = PRIORITY.join(' / ')

  const displayValues: Record<string, string | null> = {
    company: companyVal,
    rent: rentVal,
    commute: commuteVal,
    exclude: excludeVal,
    priority: cards.length > 0 ? priorityVal : null,
  }

  const activeRows = CONDITION_DISPLAY.filter(c => displayValues[c.key] !== null)

  if (activeRows.length === 0) {
    return (
      <div className="card cond-summary">
        <div className="card-head">
          <h2>내 조건 요약</h2>
          {showEdit && (
            <button className="card-link" type="button">
              <Pencil size={12} style={{ marginRight: 3 }} /> 편집
            </button>
          )}
        </div>
        <p style={{ fontSize: 12, color: 'var(--muted)', padding: '4px 0' }}>
          대화를 통해 조건을 설정해주세요.
        </p>
      </div>
    )
  }

  return (
    <div className="card cond-summary">
      <div className="card-head">
        <h2>내 조건 요약</h2>
        {showEdit ? (
          <button className="card-link" type="button">
            <Pencil size={12} style={{ marginRight: 3 }} /> 수정
          </button>
        ) : (
          <span style={{ fontSize: 11, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 3 }}>
            <Pencil size={11} /> 편집
          </span>
        )}
      </div>
      <div className="cond-rows">
        {activeRows.map(row => {
          const Icon = row.icon
          return (
            <div key={row.key} className="cond-row">
              <div className="cond-row-icon" style={{ background: row.iconBg }}>
                <Icon size={15} />
              </div>
              <span className="cond-row-key">{row.label}</span>
              <span
                className="cond-row-val"
                style={{ background: row.valBg, color: row.valColor }}
              >
                {displayValues[row.key]}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
