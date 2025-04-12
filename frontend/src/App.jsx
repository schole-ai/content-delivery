import { useState } from 'react'
import FileUploader from './components/FileUploader'
import ChatInterface from './components/ChatInterface'

function App() {
  const [sessionId, setSessionId] = useState(null)

  return (
    <div className="min-h-screen w-full flex items-center justify-center px-4 bg-gray-100">
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
