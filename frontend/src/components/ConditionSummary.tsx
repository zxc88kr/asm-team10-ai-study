import { Building2, Wallet, Clock, Ban, Star, ShoppingBag } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import useAppStore from '../store/useAppStore'

interface DisplayRow {
  key: string
  icon: LucideIcon
  label: string
  value: string
  valBg: string
  valColor: string
}

function buildRows(agentConditions: NonNullable<ReturnType<typeof useAppStore.getState>['agentConditions']>): DisplayRow[] {
  const rows: DisplayRow[] = []
  const loc = agentConditions.hard_conditions.location_transport
  const rent = agentConditions.hard_conditions.monthly_rent
  const soft = agentConditions.soft_conditions

  const locationLabel = [...loc.landmarks, ...loc.areas].filter(Boolean).join(', ')
  if (locationLabel) {
    rows.push({
      key: 'location',
      icon: Building2,
      label: '위치/교통',
      value: locationLabel,
      valBg: 'var(--primary-soft)',
      valColor: 'var(--primary)',
    })
  }

  if (loc.commute_time_max_minutes !== null) {
    rows.push({
      key: 'commute',
      icon: Clock,
      label: '출퇴근',
      value: `${loc.commute_time_max_minutes}분 이내`,
      valBg: 'var(--primary-soft)',
      valColor: 'var(--primary)',
    })
  }

  if (rent.max_manwon !== null) {
    const rentLabel = `${rent.max_manwon}만 원 이하${rent.includes_management_fee ? ' (관리비 포함)' : ''}`
    rows.push({
      key: 'rent',
      icon: Wallet,
      label: '월 고정비',
      value: rentLabel,
      valBg: 'var(--primary-soft)',
      valColor: 'var(--primary)',
    })
  }

  const excludeItems: string[] = []
  if (soft.basement.avoid) excludeItems.push('반지하')
  if (soft.pests.avoid) excludeItems.push('벌레')
  if (soft.mold.avoid) excludeItems.push('곰팡이')
  if (excludeItems.length > 0) {
    rows.push({
      key: 'exclude',
      icon: Ban,
      label: '제외 조건',
      value: excludeItems.join(', '),
      valBg: '#f1f5f9',
      valColor: 'var(--ink-2)',
    })
  }

  const facilityItems = [...soft.convenience_facilities.required, ...soft.convenience_facilities.preferred]
  if (facilityItems.length > 0) {
    rows.push({
      key: 'facility',
      icon: Star,
      label: '편의시설',
      value: facilityItems.join(', '),
      valBg: 'var(--primary-soft)',
      valColor: 'var(--primary)',
    })
  }

  const optionItems = [...soft.default_options.required, ...soft.default_options.preferred]
  if (optionItems.length > 0) {
    rows.push({
      key: 'options',
      icon: ShoppingBag,
      label: '기본 옵션',
      value: optionItems.join(', '),
      valBg: '#f1f5f9',
      valColor: 'var(--ink-2)',
    })
  }

  return rows
}

export default function ConditionSummary() {
  const { agentConditions } = useAppStore()

  const rows = agentConditions ? buildRows(agentConditions) : []

  if (rows.length === 0) {
    return (
      <div className="card cond-summary">
        <div className="card-head">
          <h2>내 조건 요약</h2>
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
      </div>
      <div className="cond-rows">
        {rows.map(row => {
          const Icon = row.icon
          return (
            <div key={row.key} className="cond-row">
              <div className="cond-row-icon">
                <Icon size={18} />
              </div>
              <span className="cond-row-key">{row.label}</span>
              <span className="cond-row-val" style={{ background: row.valBg, color: row.valColor }}>
                {row.value}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
