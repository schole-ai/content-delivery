import { useState } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const EmojiFeedback = ({ sessionId, onSubmitted, isFinal = false }) => {
    const [submitted, setSubmitted] = useState(false)
  
    const handleFeedback = async (rating) => {
      setSubmitted(true)
      setTimeout(() => {
        onSubmitted()
      }, 2000)

      await fetch(`${BACKEND_URL}/feedback/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, rating }),
      })
    }
  
    return (
      <div className="flex flex-col items-center bg-yellow-50 border border-yellow-300 p-4 rounded-xl shadow-md my-6">
        {!submitted ? (
          <>
            <p className="text-lg font-medium mb-2 text-yellow-800">
              {isFinal
                ? 'How did you enjoy the course overall?'
                : 'How are you enjoying the course so far?'}
            </p>
            <div className="flex space-x-3 text-3xl">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  onClick={() => handleFeedback(rating)}
                  className="hover:scale-110 transition-transform"
                >
                  {['😡', '😕', '😐', '🙂', '😍'][rating - 1]}
                </button>
              ))}
            </div>
          </>
        ) : (
          <p className="text-green-700 text-lg mt-2 font-semibold">Thanks for your feedback! 🙏</p>
        )}
      </div>
    )
  }
  
export default EmojiFeedback
