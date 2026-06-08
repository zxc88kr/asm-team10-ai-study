import useAppStore from '../store/useAppStore'
import ConditionSummary from './ConditionSummary'
import RecommendationList from './RecommendationList'

export default function AnalysisRightPanel() {
  const { selectedListingId } = useAppStore()

  return (
    <div className="analysis-panels">
      <ConditionSummary />

      <RecommendationList selectedId={selectedListingId} />
    </div>
  )
}
