import ConditionSummary from './ConditionSummary'
import RecommendationList from './RecommendationList'
// import LocationAnalysisSummary from './LocationAnalysis'

export default function RightPanels() {
  return (
    <div className="panels">
      <ConditionSummary />
      <RecommendationList />
      {/* <LocationAnalysisSummary /> */}
    </div>
  )
}
