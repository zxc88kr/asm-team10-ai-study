import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import RightPanels from './components/RightPanels'
import LocationAnalysisView from './components/LocationAnalysisView'
import AnalysisRightPanel from './components/AnalysisRightPanel'
import Toast from './components/Toast'
import useAppStore from './store/useAppStore'

export default function App() {
  const activeView = useAppStore(s => s.activeView)

  return (
    <>
      <div className="app">
        <Sidebar />
        {activeView === 'chat' ? (
          <>
            <ChatPanel />
            <RightPanels />
          </>
        ) : (
          <>
            <LocationAnalysisView />
            <AnalysisRightPanel />
          </>
        )}
      </div>
      <Toast />
    </>
  )
}
