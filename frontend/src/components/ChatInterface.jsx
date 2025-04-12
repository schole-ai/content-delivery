import { useEffect, useState, useRef } from 'react'

const ChatInterface = ({ sessionId }) => {
  const [chunk, setChunk] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [lastAnswer, setLastAnswer] = useState('')
  const [messages, setMessages] = useState([])
  const [completed, setCompleted] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMessage, setLoadingMessage] = useState('Chunking and generating the first question...')
  const [feedback, setFeedback] = useState('')
  const [showFeedback, setShowFeedback] = useState(false)
  const hasFetched = useRef(false)

  // Fetch the first chunk and question
  const fetchNext = async () => {
    const res = await fetch(`http://localhost:8000/chunk/${sessionId}`)
    const data = await res.json()
    setChunk(data.chunk)
    setQuestion(data.question)
    setLoading(false)
  }

  // Make sure to fetch the first chunk and question only once
  useEffect(() => {
    if (!sessionId || hasFetched.current) return
    hasFetched.current = true
    fetchNext()
  }, [sessionId])


  // Get the answer from the user and generate feedback
  const handleSubmit = async (e) => {
    e.preventDefault()

    setLoadingMessage('Submitting answer...')
    setLoading(true)
  
    const res = await fetch(`http://localhost:8000/answer/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ answer }),
    })
  
    const data = await res.json()
  
    setFeedback(data.feedback || '')
    setShowFeedback(true)
    setAnswer('')
    setLastAnswer(answer)
    setLoading(false)
    
    // Check if the course is completed
    if (data.is_last) {
      setCompleted('pending')
    } else {
      setCompleted(false)
    }
  }

  // When the user clicks "Continue" after feedback, fetch the next chunk and question
  const handleContinue = async () => {
    setMessages((prev) => [
      ...prev,
      { chunk, question, lastAnswer, answer, feedback },
    ])
  
    setLoadingMessage('Loading next chunk...')
    setLoading(true)
  
    const res = await fetch(`http://localhost:8000/chunk/${sessionId}`)
    const data = await res.json()
  
    setChunk(data.chunk)
    setQuestion(data.question)
    setFeedback('')
    setShowFeedback(false)
    setLoading(false)
  }
  

  // If the course is completed, show a completion message
  if (completed === true) {
    return (
      <div className="bg-white p-10 rounded-xl shadow-xl text-center">
        <h2 className="text-3xl font-bold text-green-600 mb-2">🎉 Course Completed!</h2>
        <p className="text-gray-600">Great job answering all the questions!</p>
      </div>
    )
  }

  return (
    <div className="bg-white p-8 rounded-xl shadow-xl space-y-6">
      {messages.map((msg, idx) => (
        <div key={idx} className="border-b pb-4 mb-4 space-y-2">
          <p className="text-sm text-gray-400">Chunk {idx + 1}</p>
          <p className="text-justify">{msg.chunk}</p>
          <p className="mt-2 text-blue-700 font-semibold">Q: {msg.question}</p>
          <p className="text-gray-700"><span className="font-medium">You:</span> {msg.lastAnswer}</p>
          {msg.feedback && (
            <p className="text-sm text-green-700 mt-1">
              <span className="font-medium">Feedback:</span> {msg.feedback}
            </p>
          )}
        </div>
      ))}

{loading ? (
  <div className="flex items-center justify-center py-12 text-blue-600">
    <svg className="animate-spin h-6 w-6 mr-3" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10"
              stroke="currentColor" strokeWidth="4" fill="none" />
      <path className="opacity-75" fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <span>{loadingMessage}</span>
  </div>
) : showFeedback ? (
  <div className="space-y-4">
    <p className="text-green-700 text-lg font-medium">
      <span className="font-bold">Feedback:</span> {feedback}
    </p>
    {completed === 'pending' ? (
      <button
        onClick={() => setCompleted(true)}
        className="bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 font-semibold shadow-md"
      >
        Finish
      </button>
    ) : (
      <button
        onClick={handleContinue}
        className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 font-semibold shadow-md"
      >
        Continue
      </button>
    )}
  </div>
) : (
  <div className="space-y-4">
    <div>
      <p className="text-sm text-gray-400">Current Chunk</p>
      <p className="text-justify text-gray-800">{chunk}</p>
    </div>

    <p className="text-lg font-medium text-blue-700">{question}</p>

    <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
      <textarea
        className="border p-3 rounded-lg resize-none shadow-sm focus:ring-2 focus:ring-blue-500"
        rows={4}
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        placeholder="Write your answer here..."
        required
      />
      <button
        type="submit"
        className="bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 font-semibold shadow-md"
      >
        Submit Answer
      </button>
    </form>
  </div>
)}

    </div>
  )
}

export default ChatInterface
