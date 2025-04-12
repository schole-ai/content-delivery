import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

const FileUploader = ({ onUploadSuccess }) => {
  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0]
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch('http://localhost:8000/upload', {
      method: 'POST',
      body: formData,
    })

    const data = await res.json()
    onUploadSuccess(data.session_id)
  }, [onUploadSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
  })

  return (
    <div
      {...getRootProps()}
      className="bg-white p-10 rounded-2xl shadow-xl border-2 border-dashed border-gray-300 text-center text-gray-600 hover:border-blue-400 transition-all duration-300"
    >
      <input {...getInputProps()} />
      <h2 className="text-xl font-semibold mb-2">Upload your PDF</h2>
      <p className="text-gray-500">
        {isDragActive ? 'Drop the PDF here...' : 'Drag and drop a PDF file, or click to select'}
      </p>
    </div>
  )
}


export default FileUploader
