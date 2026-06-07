import useAppStore from '../store/useAppStore'

export default function AgentLogPanel() {
  const { agentLogs } = useAppStore()

  return (
    <div className="card agent-log-card">
      <div className="card-head">
        <h2>AI 처리 로그</h2>
        <span className="agent-log-badge">live</span>
      </div>
      <ol className="agent-log-list">
        {agentLogs.map((log, idx) => (
          <li key={`${log}-${idx}`} className="agent-log-item">
            <span className="agent-log-dot" />
            <span>{log}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}
