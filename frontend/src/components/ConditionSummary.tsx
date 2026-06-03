import { useState, useEffect } from 'react'
import useAppStore from '../store/useAppStore'
import { CONDITION_CARDS, CATEGORY_CLASS } from '../data/conditions'
import { PRIORITY } from '../data/scenario'
import type { CardSource } from '../types'

export default function ConditionSummary() {
  const hard = useAppStore(s => s.hard)
  const cards = useAppStore(s => s.cards)
  const recommended = useAppStore(s => s.recommended)
  const lastTop = useAppStore(s => s.lastTop)
  const updateRent = useAppStore(s => s.updateRent)
  const showToast = useAppStore(s => s.showToast)

  const [showEditor, setShowEditor] = useState(false)
  const [tempRent, setTempRent] = useState(50)

  useEffect(() => {
    if (hard.rent) {
      setTempRent(hard.rent)
    } else {
      setShowEditor(false)
    }
  }, [hard.rent])

  const hasConditions = cards.length > 0 || Object.keys(hard).length > 0

  function handleEditClick() {
    if (!hard.rent) {
      showToast('아직 예산 조건이 없어요. 대화를 먼저 진행해 주세요.')
      return
    }
    setShowEditor(v => !v)
  }

  function handleApply() {
    updateRent(tempRent)
    setShowEditor(false)
    if (recommended || lastTop) {
      showToast(`월세 상한을 ${tempRent}만원으로 반영해 추천을 갱신했어요.`)
    }
  }

  return (
    <div className="card">
      <div className="card-head">
        <h2>내 조건 요약</h2>
        <button className="link" onClick={handleEditClick}>조건 편집</button>
      </div>

      {!hasConditions && (
        <div className="empty">대화를 시작하면 조건이 여기에 쌓여요.</div>
      )}

      <ul className="cond-list">
        {hard.deposit && (
          <CondItem category="비용" label="보증금" value={`${hard.deposit.toLocaleString()}만원 이하`} source="said" reason="직접 입력" />
        )}
        {hard.rent && (
          <CondItem category="비용" label="월세" value={`${hard.rent}만원 이하`} source="said" reason="직접 입력" />
        )}
        {cards.map(cid => {
          const c = CONDITION_CARDS[cid]
          return (
            <CondItem key={cid} category={c.category} label={c.label} value="" source={c.source} reason={c.reason} />
          )
        })}
      </ul>

      {hasConditions && (
        <div className="priority">
          <span className="pri-label">우선순위</span>
          <span className="pri-chips">
            {PRIORITY.map((p, i) => (
              <span key={p} className="pri-chip">{i + 1}. {p}</span>
            ))}
          </span>
        </div>
      )}

      {showEditor && (
        <div className="editor">
          <div className="ed-title">월세 상한 조정 (루프백 데모)</div>
          <div className="ed-row">
            <button className="ed-btn" onClick={() => setTempRent(t => Math.max(20, t - 5))}>−5</button>
            <span className="ed-val"><b>{tempRent}</b> 만원</span>
            <button className="ed-btn" onClick={() => setTempRent(t => Math.min(120, t + 5))}>＋5</button>
          </div>
          <button className="ed-apply" onClick={handleApply}>이 조건으로 다시 추천</button>
          <div className="ed-hint">조건을 바꾸면 Agent 2·3가 다시 돌아 추천이 갱신돼요.</div>
        </div>
      )}
    </div>
  )
}

interface CondItemProps {
  category: string
  label: string
  value: string
  source: CardSource
  reason: string
}

function CondItem({ category, label, value, source, reason }: CondItemProps) {
  return (
    <li className="cond-item">
      <div className="cond-top">
        <span className={`cat-dot ${CATEGORY_CLASS[category] || ''}`} />
        <span className="cond-label">{label}</span>
        <span className={`src ${source}`}>{source === 'said' ? '말함' : 'AI 발굴'}</span>
      </div>
      {value && <div className="cond-val">{value}</div>}
      {reason && <div className="cond-reason">↳ {reason}</div>}
    </li>
  )
}
