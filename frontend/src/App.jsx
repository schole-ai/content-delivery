import { useState } from 'react'
import FileUploader from './components/FileUploader'
import ChatInterface from './components/ChatInterface'
import Header from './components/Header'

function App() {
  const [sessionId, setSessionId] = useState(null)

  return (
    <div className="min-h-screen w-full flex flex-col items-center px-4 bg-gray-100">
      {!sessionId && <Header />}
      <div className="max-w-4xl w-full">
        {!sessionId ? (
          <FileUploader onUploadSuccess={setSessionId} />
        ) : (
          <ChatInterface sessionId={sessionId} />
        )}
      </div>
    </div>
  )
}


export default App
