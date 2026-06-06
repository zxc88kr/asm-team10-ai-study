import { Building2, Wallet, Clock, Ban, Star, ShoppingBag, Pencil } from 'lucide-react'
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
      valBg: '#EEF3FF',
      valColor: '#4B7BF5',
    })
  }

  if (loc.commute_time_max_minutes !== null) {
    rows.push({
      key: 'commute',
      icon: Clock,
      label: '출퇴근',
      value: `${loc.commute_time_max_minutes}분 이내`,
      valBg: '#EEF3FF',
      valColor: '#4B7BF5',
    })
  }

  if (rent.max_manwon !== null) {
    const rentLabel = `${rent.max_manwon}만 원 이하${rent.includes_management_fee ? ' (관리비 포함)' : ''}`
    rows.push({
      key: 'rent',
      icon: Wallet,
      label: '월 고정비',
      value: rentLabel,
      valBg: '#EEF3FF',
      valColor: '#4B7BF5',
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
      valBg: '#F1F5F9',
      valColor: '#64748B',
    })
  }

  const facilityItems = [...soft.convenience_facilities.required, ...soft.convenience_facilities.preferred]
  if (facilityItems.length > 0) {
    rows.push({
      key: 'facility',
      icon: Star,
      label: '편의시설',
      value: facilityItems.join(', '),
      valBg: '#EEF3FF',
      valColor: '#4B7BF5',
    })
  }

  const optionItems = [...soft.default_options.required, ...soft.default_options.preferred]
  if (optionItems.length > 0) {
    rows.push({
      key: 'options',
      icon: ShoppingBag,
      label: '기본 옵션',
      value: optionItems.join(', '),
      valBg: '#F1F5F9',
      valColor: '#64748B',
    })
  }

  return rows
}

export default function ConditionSummary({ showEdit = false }: { showEdit?: boolean }) {
  const { agentConditions } = useAppStore()

  const rows = agentConditions ? buildRows(agentConditions) : []

  if (rows.length === 0) {
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
