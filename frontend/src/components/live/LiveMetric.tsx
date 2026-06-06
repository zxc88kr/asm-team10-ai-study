import { Sparkles } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'

export default function LiveMetric() {
  const metric = useLiveStore(s => s.metric)

  return (
    <div className="kpi">
      <div className="kpi-label"><Sparkles size={14} /> 차별 지표 · 숨은 조건 발굴</div>
      <div className="kpi-ratio">
        {metric ? metric.ratio : <>0:0</>}
      </div>
      <div className="kpi-sub">
        {metric
          ? `직접 말한 ${metric.said}개에서 AI가 ${metric.derived}개의 숨은 조건을 함께 찾았어요.`
          : '생활 대화만으로 AI가 말로 못 한 주거 조건까지 발굴합니다.'}
      </div>
      {metric && (
        <div className="kpi-split">
          <div className="kpi-stat"><b>{metric.said}</b><span>직접 말한 조건</span></div>
          <div className="kpi-stat"><b>{metric.derived}</b><span>AI 발굴·추출</span></div>
        </div>
      )}
    </div>
  )
}
