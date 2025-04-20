import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const FileUploader = ({ onUploadSuccess }) => {
  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0]
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(`${BACKEND_URL}/prepare`, {
      method: 'POST',
      body: formData,
    })

    const data = await res.json()
    onUploadSuccess(data.session_id)

    await fetch(`${BACKEND_URL}/process/${sessionId}`, {
      method: 'POST',
    })
    
  }, [onUploadSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
    },
    multiple: false,
  })

  return (
    <div
      {...getRootProps()}
      className="bg-white p-10 rounded-2xl shadow-xl border-2 border-dashed border-gray-300 text-center text-gray-600 hover:border-blue-400 transition-all duration-300"
    >
      <input {...getInputProps()} />
      <h2 className="text-xl font-semibold mb-2">Upload your PDF or TXT file</h2>
      <p className="text-gray-500">
        {isDragActive
          ? 'Drop the file here...'
          : 'Drag and drop a PDF or TXT file, or click to select'}
      </p>
    </div>
  )
}

export default FileUploader
