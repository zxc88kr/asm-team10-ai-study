import ConditionSummary from './ConditionSummary'
import RecommendationList from './RecommendationList'
import LocationAnalysis from './LocationAnalysis'

export default function RightPanels() {
  return (
    <section className="panels">
      <ConditionSummary />
      <RecommendationList />
      <LocationAnalysis />
    </section>
  )
}
