import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import RightPanels from './components/RightPanels'
import ListingModal from './components/ListingModal'
import Toast from './components/Toast'

export default function App() {
  return (
    <>
      <div className="app">
        <Sidebar />
        <ChatPanel />
        <RightPanels />
      </div>
      <ListingModal />
      <Toast />
    </>
  )
}
