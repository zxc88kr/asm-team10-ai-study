import useAppStore from '../store/useAppStore'

export default function LocationAnalysisSummary() {
  const lastTop = useAppStore(s => s.lastTop)

  if (!lastTop || lastTop.length === 0) return null

  const top = lastTop[0].L
  const analysis = top.locationAnalysis

  const safetyScore = analysis.scoreBreakdown.find(b => b.label === '안전')?.score ?? 0
  const commuteScore = analysis.scoreBreakdown.find(b => b.label === '통학/출근')?.score ?? 0
  const convScore = analysis.scoreBreakdown.find(b => b.label === '생활 편의성')?.score ?? 0

  const getQuality = (score: number): 'good' | 'ok' | 'poor' => {
    if (score >= 80) return 'good'
    if (score >= 60) return 'ok'
    return 'poor'
  }
  const getLabel = (quality: 'good' | 'ok' | 'poor') =>
    quality === 'good' ? '매우 좋음' : quality === 'ok' ? '좋음' : '보통 이상'

  const bars = [
    { key: '출퇴근', score: commuteScore, quality: getQuality(commuteScore) },
    { key: '편의시설', score: convScore, quality: getQuality(convScore) },
    { key: '안전성', score: safetyScore, quality: getQuality(safetyScore) },
  ]

  return (
    <div className="card">
      <div className="card-head">
        <h2>입지 분석 요약</h2>
        <button className="card-link" type="button">자세히 보기</button>
      </div>
      <div className="loc-summary-bars">
        {bars.map(bar => (
          <div key={bar.key} className="loc-bar-row">
            <span className="loc-bar-key">{bar.key}</span>
            <div className="bar-track">
              <span
                className={`bar-fill ${bar.quality}`}
                style={{ width: `${bar.score}%` }}
              />
            </div>
            <span className="loc-bar-val">
              {getLabel(bar.quality)}
            </span>
          </div>
        ))}
      </div>
      <p className="loc-note">
        ⓘ 분석 정보는 참고용이며, 실제와 다를 수 있습니다.
      </p>
    </div>
  )
}
