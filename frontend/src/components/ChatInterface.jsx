import { useEffect, useState, useRef } from 'react'
import ProgressBar from './ProgressBar' // Import the ProgressBar component
import EmojiFeedback from './EmojiFeedback'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const ChatInterface = ({ sessionId }) => {
  const [chunk, setChunk] = useState('') // State to hold the current chunk of text
  const [isImage, setIsImage] = useState(false) // State to track if the chunk is an image or text
  const [question, setQuestion] = useState('') // State to hold the question related to the current chunk
  const [questionType, setQuestionType] = useState('SAQ') // State to hold the type of question (SAQ or MCQ)
  const [bloomLevel, setBloomLevel] = useState('') // State to hold the Bloom's taxonomy level
  const [answer, setAnswer] = useState('')  // State to hold the user's answer
  const [lastAnswer, setLastAnswer] = useState('')  // State to hold the last answer submitted by the user
  const [messages, setMessages] = useState([]) // State to hold the conversation history
  const [completed, setCompleted] = useState(false) // State to track if the course is completed
  const [loading, setLoading] = useState(true)  // State to track if the app is loading or generating content
  const [loadingMessage, setLoadingMessage] = useState('Chunking and generating the first question...') 
  const [feedback, setFeedback] = useState('') // State to hold the feedback from the server
  const [showFeedback, setShowFeedback] = useState(false) // State to control the visibility of feedback
  const [progress, setProgress] = useState({ current: 0, total: 1, percent: 0 }) // State to track the progress of the course
  const [fileLoaded, setFileLoaded] = useState(false);  // Track if the file is ready
  const [questionStartTime, setQuestionStartTime] = useState(null); // State to track the amount of time spent on the question
  const [midFeedbackShown, setMidFeedbackShown] = useState(false)
  const [endFeedbackShown, setEndFeedbackShown] = useState(false)
  const hasFetched = useRef(false) // Ref to track if the first chunk has been fetched
  const currentChunkRef = useRef(null) // Ref to hold the current chunk of text

  // Fetch the first chunk and question
  const fetchNext = async () => {
    const res = await fetch(`${BACKEND_URL}/chunk/${sessionId}`);
    const data = await res.json()
    setChunk(data.chunk)
    setQuestion(data.question)
    setIsImage(data.is_img)
    setProgress(data.progress)
    setQuestion(data.question)
    setQuestionType(data.question_type)
    setBloomLevel(data.bloom_level)
    setQuestionStartTime(Date.now())
    setLoading(false)
    setFileLoaded(true) 
    
  }

  // Make sure to fetch the first chunk and question only once
  useEffect(() => {
    const load = async () => {
      setLoadingMessage('Chunking...')
      setLoading(true)
  
      // // Wait until backend finished processing
      // await fetch(`${BACKEND_URL}/upload`, { method: 'POST' })
  
      setLoadingMessage('Generating first chunk and question...')
      await fetchNext()
    }
  
    if (!sessionId || hasFetched.current) return
    hasFetched.current = true
    load()
  }, [sessionId])


  // Get the answer from the user and generate feedback
  const handleSubmit = async (e) => {
    e.preventDefault()

    const elapsedTime = Date.now() - questionStartTime;

    setLoadingMessage('Submitting answer...')
    setLoading(true)
  
    const res = await fetch(`${BACKEND_URL}/answer/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ answer, elapsed_time: elapsedTime }),
    })
  
    const data = await res.json()
  
    setFeedback(data.feedback || '')
    setShowFeedback(true)
    setAnswer('')
    setLastAnswer(answer)
    setLoading(false)
    
    // Check if the course is completed
    if (data.is_last) {
      setProgress(data.progress)
      setCompleted('pending')
    } else {
      setProgress(data.progress)
      setCompleted(false)
      setTimeout(() => {
        currentChunkRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);      
    }
  }

  // When the user clicks "Continue" after feedback, fetch the next chunk and question
  const handleContinue = async () => {
    setMessages((prev) => [
      ...prev,
      { chunk, question, lastAnswer, answer, feedback, isImage, bloomLevel },
    ])
  
    setLoadingMessage('Loading next chunk...')
    setLoading(true)
  
    const res = await fetch(`${BACKEND_URL}/chunk/${sessionId}`)
    const data = await res.json()
  
    setChunk(data.chunk)
    setQuestion(data.question)
    setQuestion(data.question)
    setQuestionType(data.question_type)
    setBloomLevel(data.bloom_level)
    setProgress(data.progress)
    setFeedback('')
    setQuestionStartTime(Date.now())
    setShowFeedback(false)
    setLoading(false)
    setTimeout(() => {
      currentChunkRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);    
  }
  

  // If the course is completed, show a completion message
  if (completed === true && !endFeedbackShown) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-10 rounded-xl shadow-xl text-center space-y-6">
          <h2 className="text-3xl font-bold text-green-600">🎉 Course Completed!</h2>
          <p className="text-gray-600">Great job answering all the questions!</p>
          <EmojiFeedback sessionId={sessionId} onSubmitted={() => setEndFeedbackShown(true)} isFinal={true} />
        </div>
      </div>
    )
  }
  
  if (completed === true && endFeedbackShown) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-10 rounded-xl shadow-xl text-center">
          <h2 className="text-3xl font-bold text-green-600 mb-2">🎉 Course Completed!</h2>
          <p className="text-gray-600">Thanks for your feedback. See you next time!</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 font-semibold shadow-md mt-4"
          >
            Start New Session
          </button>
        </div>
      </div>
    )
  }
  

  return (
    <div className="bg-white p-8 rounded-xl shadow-xl space-y-6 mt-20">
      {fileLoaded && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-white shadow px-4">
          <div className="max-w-3xl mx-auto">
            <ProgressBar {...progress} />
          </div>
        </div>
      )}
      {messages.map((msg, idx) => (
        <div key={idx} className="border-b pb-4 mb-4 space-y-2">
          <p className="text-sm text-gray-400">Chunk {idx + 1}</p>
          {msg.isImage ? (
            <img
              src={`data:image/png;base64,${msg.chunk}`}
              alt={`PDF chunk ${idx + 1}`}
              className="w-full rounded-lg shadow-md"
            />
          ) : (
            <p className="text-justify">{msg.chunk}</p>
          )}

          <p className="text-sm italic text-purple-600">
            Bloom Level: <span className="font-semibold">{msg.bloomLevel}</span>
          </p>

          <div className="mt-2 text-blue-700 font-semibold">
            <p>Q: {typeof msg.question === 'string' ? msg.question : msg.question.question}</p>
            {msg.question.choices && (
              <ul className="ml-4 mt-1 text-sm text-gray-800 space-y-1">
                {Object.entries(msg.question.choices).map(([letter, choice]) => (
                  <li key={letter}>
                    <span className="font-medium">{letter}.</span> {choice}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <p className="text-gray-700"><span className="font-medium">You:</span> {msg.lastAnswer}</p>
          {msg.feedback && (
            <p className="text-sm text-green-700 mt-1">
              <span className="font-medium">Feedback:</span> {msg.feedback}
            </p>
          )}
        </div>
      ))}

      {progress.total > 2 &&
      progress.current === Math.floor(progress.total / 2) &&
      !midFeedbackShown && (
        <EmojiFeedback sessionId={sessionId} onSubmitted={() => setMidFeedbackShown(true)} />
      )}


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
          <div ref={currentChunkRef}>
            <p className="text-sm text-gray-400">Current Chunk</p>
            {isImage ? (
              <img
                src={`data:image/png;base64,${chunk}`}
                alt="Current PDF chunk"
                className="w-full rounded-lg shadow-md"
              />
            ) : (
              <p className="text-justify text-gray-800">{chunk}</p>
            )}
          </div>

          <p className="text-sm text-purple-600 italic">
            Bloom Level: <span className="font-semibold">{bloomLevel}</span>
          </p>

          <p className="text-lg font-medium text-blue-700">
            {questionType === 'MCQ' ? question.question : question}
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
            {questionType === 'MCQ' && (
              <div className="space-y-2">
                {Object.entries(question.choices).map(([key, val]) => (
                  <label key={key} className="block">
                    <input
                      type="radio"
                      name="mcq"
                      value={key}
                      checked={answer === key}
                      onChange={() => setAnswer(key)}
                      className="mr-2"
                    />
                    {key}. {val}
                  </label>
                ))}
              </div>
            )}

            {questionType === 'SAQ' && (
              <textarea
                className="border p-3 rounded-lg resize-none shadow-sm focus:ring-2 focus:ring-blue-500"
                rows={4}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Write your answer here..."
                required
              />
            )}

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
