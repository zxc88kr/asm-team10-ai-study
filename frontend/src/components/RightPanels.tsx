import ConditionSummary from './ConditionSummary'
import RecommendationList from './RecommendationList'
import AgentLogPanel from './AgentLogPanel'
// import LocationAnalysisSummary from './LocationAnalysis'

export default function RightPanels() {
  return (
    <div className="panels">
      <ConditionSummary />
      <AgentLogPanel />
      <RecommendationList />
      {/* <LocationAnalysisSummary /> */}
    </div>
  )
}
