import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const FileUploader = ({ onUploadSuccess }) => {
  const [neo4jCredentials, setNeo4jCredentials] = useState({
    url: '',
    username: '',
    password: '',
    // url: 'bolt://localhost:7687',
    // username: 'neo4j',
    // password: 'password123',
  })
  const [errorMessage, setErrorMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [neo4jConnected, setNeo4jConnected] = useState(false)
  const [query, setQuery] = useState('')
  // User Study
  const [userStudyMode, setUserStudyMode] = useState(false)
  const [prolificId, setProlificId] = useState('')
  const [userStudyError, setUserStudyError] = useState('')
  const [userStudyLoading, setUserStudyLoading] = useState(false)

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0]
    const formData = new FormData()
    formData.append('file', file)

    setLoading(true)

    try {
      const res = await fetch(`${BACKEND_URL}/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await res.json()
      onUploadSuccess(data.session_id)
    } catch (error) {
      setErrorMessage('Failed to upload and process the file.')
    } finally {
      setLoading(false)
    }
  }, [onUploadSuccess])

  const handleNeo4jSubmit = async (e) => {
    e.preventDefault()
    setErrorMessage('')
    setConnecting(true)

    try {
      const res = await fetch(`${BACKEND_URL}/neo4j/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(neo4jCredentials),
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.message || 'Failed to connect to Neo4j.')

      setNeo4jConnected(true)
    } catch (error) {
      setErrorMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleNeo4jQuerySubmit = async (e) => {
    e.preventDefault()
    setErrorMessage('')
    setLoading(true)

    try {
      const res = await fetch(`${BACKEND_URL}/neo4j/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.message || 'Failed to query knowledge graph')

      onUploadSuccess(data.session_id)
    } catch (err) {
      setErrorMessage(err.message)
    } finally {
      setLoading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
    },
    multiple: false,
  })

  const handleBackToStart = () => {
    setNeo4jConnected(false)
    setConnecting(false)
    setLoading(false)
    setNeo4jCredentials({
      url: '',
      username: '',
      password: '',
    })
    setQuery('')
    setErrorMessage('')
  }

  return (
    <div className="flex flex-col items-center gap-8">
      {(loading && !neo4jConnected) ? (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center mb-100">
            <svg className="animate-spin w-15 text-blue-600 mx-auto" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-blue-600 font-semibold">Uploading and chunking your file...</p>
          </div>
        </div>
      ) : neo4jConnected ? (
        <div className="bg-white p-10 rounded-2xl shadow-xl border border-gray-300 w-full max-w-lg">
          <h2 className="text-xl font-semibold mb-4 text-center">Query Knowledge Graph</h2>
          <form onSubmit={handleNeo4jQuerySubmit}>
            <input
              type="text"
              placeholder="Enter your query"
              value={query}
              disabled={connecting && loading}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full p-2 border rounded-lg mb-4"
              required
            />
            <button
              type="submit"
              className="bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 font-semibold shadow-md w-full mb-4"
              disabled={connecting && loading}
            >
              {(connecting && loading) ? 'Searching...' : 'Search and Start Learning'}
            </button>
          </form>
          <button
            onClick={handleBackToStart}
            className="text-blue-600 hover:underline text-sm"
            disabled={connecting && loading}
          >
            ← Back to Start
          </button>
          {errorMessage && (
            <p className="text-red-500 text-sm mt-4">{errorMessage}</p>
          )}
        </div>
      ) : (
        <>
          {/* User Study Form Only */}
          {userStudyMode ? (
            <div className="bg-white p-10 rounded-2xl shadow-xl border border-gray-300 w-full max-w-lg mt-6">
              <h2 className="text-xl font-semibold mb-4 text-center">Enter your prolific ID</h2>
              <form
                onSubmit={async (e) => {
                  e.preventDefault()
                  setUserStudyError('')
                  setUserStudyLoading(true)
                  try {
                    // Call backend endpoint to load pre-chunked PDF session
                    const res = await fetch(`${BACKEND_URL}/user_study`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ prolific_id: prolificId }),
                    })
                    const data = await res.json()
                    if (!res.ok) throw new Error(data.message || 'Failed to start user study')
                    onUploadSuccess(data.session_id)
                  } catch (err) {
                    setUserStudyError(err.message)
                  } finally {
                    setUserStudyLoading(false)
                  }
                }}
                className="space-y-4"
              >
                <input
                  type="text"
                  placeholder="Enter your Prolific ID"
                  value={prolificId}
                  onChange={(e) => setProlificId(e.target.value)}
                  className="w-full p-2 border rounded-lg"
                  required
                />
                <button
                  type="submit"
                  className="bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 font-semibold shadow-md w-full"
                  disabled={userStudyLoading}
                >
                  {userStudyLoading ? 'Loading...' : 'Start User Study'}
                </button>
                <button
                  type="button"
                  className="text-blue-600 hover:underline text-sm"
                  onClick={() => setUserStudyMode(false)}
                  disabled={userStudyLoading}
                >
                  ← Back
                </button>
                {userStudyError && (
                  <p className="text-red-500 text-sm mt-4">{userStudyError}</p>
                )}
              </form>
            </div>
          ) : (
            <>
              {/* File Upload */}
              <div className="bg-white p-10 rounded-2xl shadow-xl border-3 border-dashed border-orange-300 text-center hover:border-blue-500 transition-all duration-300 w-full max-w-lg" {...getRootProps()}>
                <input {...getInputProps()} />
                <h2 className="text-xl font-semibold">Upload your PDF or TXT file</h2>
                <p className="text-gray-500">
                  {isDragActive
                    ? 'Drop the file here...'
                    : 'Drag and drop a PDF or TXT file, or click to select'}
                </p>
              </div>

              {/* OR Separator */}
              <div className="text-gray-500 font-semibold text-xl">OR</div>

              {/* Neo4j Connection */}
              <div className="bg-white p-10 rounded-2xl shadow-xl border border-gray-300 w-full max-w-lg">
                <div className="flex items-center justify-center mb-6">
                  <img
                    src="images/neo4j_icon.png"
                    alt="Neo4j Logo"
                    className="h-12"
                  />
                </div>
                <form onSubmit={handleNeo4jSubmit} className="space-y-4">
                  <h2 className="text-xl font-semibold mb-2 text-center">Connect to Neo4j</h2>
                  <input
                    type="text"
                    placeholder="Neo4j URL"
                    value={neo4jCredentials.url}
                    disabled={connecting}
                    onChange={(e) =>
                      setNeo4jCredentials({ ...neo4jCredentials, url: e.target.value })
                    }
                    className="w-full p-2 border rounded-lg"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Username"
                    value={neo4jCredentials.username}
                    disabled={connecting}
                    onChange={(e) =>
                      setNeo4jCredentials({ ...neo4jCredentials, username: e.target.value })
                    }
                    className="w-full p-2 border rounded-lg"
                    required
                  />
                  <input
                    type="password"
                    placeholder="Password"
                    value={neo4jCredentials.password}
                    disabled={connecting}
                    onChange={(e) =>
                      setNeo4jCredentials({ ...neo4jCredentials, password: e.target.value })
                    }
                    className="w-full p-2 border rounded-lg"
                    required
                  />
                  <button
                    type="submit"
                    className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 font-semibold shadow-md w-full"
                    disabled={connecting}
                  >
                    {connecting ? 'Connecting...' : 'Connect'}
                  </button>
                </form>
                {errorMessage && (
                  <p className="text-red-500 text-sm mt-4">{errorMessage}</p>
                )}
              </div>

              {/* OR Separator */}
              <div className="text-gray-500 font-semibold text-xl">OR</div>

              {/* User Study Button */}
              <button
                className="bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 font-semibold shadow-md w-full max-w-lg"
                onClick={() => setUserStudyMode(true)}
              >
                Complete the User Study
              </button>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default FileUploader
