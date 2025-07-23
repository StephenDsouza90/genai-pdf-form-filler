import React, { useState, useRef } from 'react'
import { Upload, FileText, AlertCircle } from 'lucide-react'
import { uploadPDF } from '../services/api'

const UploadStep = ({ onUploadSuccess }) => {
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const handleFileSelect = async (file) => {
    if (!file) return
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please select a valid PDF file')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB')
      return
    }

    setError('')
    setIsUploading(true)

    try {
      const result = await uploadPDF(file)
      onUploadSuccess(result)
    } catch (err) {
      setError(err.message || 'Failed to upload file. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files[0]
    handleFileSelect(file)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    handleFileSelect(file)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card animate-slide-up">
        <div className="text-center mb-6">
          <div className="bg-primary-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-primary-500" />
          </div>
          <p className="text-gray-600 text-lg">
            Upload your PDF form to get started. Our AI will guide you through filling it out step by step.
          </p>
        </div>

        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ${
            isDragOver
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={handleClick}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
          />

          {isUploading ? (
            <div className="flex flex-col items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
              <p className="text-gray-600">Processing your PDF...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <Upload className={`w-12 h-12 mb-4 ${isDragOver ? 'text-primary-500' : 'text-gray-400'}`} />
              <p className="text-lg font-medium text-gray-700 mb-2">
                Drop your PDF here or click to browse
              </p>
              <p className="text-sm text-gray-500">
                Supports PDF files up to 10MB
              </p>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center text-red-700">
            <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-800 mb-2">How it works:</h3>
          <ol className="text-sm text-blue-700 space-y-1">
            <li>1. Upload your fillable PDF form</li>
            <li>2. Answer simple questions about each field</li>
            <li>3. Download your completed form</li>
          </ol>
        </div>
      </div>
    </div>
  )
}

export default UploadStep