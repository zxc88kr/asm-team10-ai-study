import useAppStore from '../store/useAppStore'

export default function LocationAnalysis() {
  const lastTop = useAppStore(s => s.lastTop)

  if (!lastTop?.[0]) {
    return (
      <div className="card">
        <div className="card-head"><h2>입지 분석 요약</h2></div>
        <div className="empty">추천 매물의 입지를 당신의 생활 기준으로 해석해요.</div>
      </div>
    )
  }

  const { L } = lastTop[0]
  const safe = L.night.lit && L.night.mainRoad
    ? (L.night.alleyM <= 80 ? 0.88 : 0.62)
    : 0.4
  const commute = Math.max(0.2, 1 - (L.walkMin - 8) / 30)
  const conv = Math.min(1, L.options.length / 6)

  const bars = [
    ['귀가 안전동선', safe],
    ['통학 시간', commute],
    ['편의시설', conv],
  ]

  const safetyTxt = safe >= 0.85
    ? `정류장에서 큰길을 따라 도보 약 ${Math.round(L.night.alleyM / 70 + 3)}분, 가로등도 밝아 밤 11시 귀가도 안심이에요.`
    : safe >= 0.6
    ? `큰길과 가까우나 골목 ${L.night.alleyM}m 구간이 있어 늦은 귀가 시 약간 신경 쓰일 수 있어요.`
    : `골목이 어두운 편이라 밤 11시 알바 귀가에는 주의가 필요해요.`

  return (
    <div className="card">
      <div className="card-head"><h2>입지 분석 요약</h2></div>

      <div className="loc-target">
        <b>1위 · {L.name}</b> 를 당신의 생활 기준으로 해석했어요
      </div>

      <ul className="loc-bars">
        {bars.map(([k, v]) => {
          const cls = v >= 0.75 ? 'good' : v >= 0.5 ? 'ok' : 'poor'
          return (
            <li key={k}>
              <span className="loc-k">{k}</span>
              <span className="bar">
                <span className={`fill ${cls}`} style={{ width: `${Math.round(v * 100)}%` }} />
              </span>
            </li>
          )
        })}
      </ul>

      <p className="loc-comment">
        밤 11시 알바 귀가 기준 — {safetyTxt} 학교까지는 도보 {L.walkMin}분.
      </p>
    </div>
  )
}
