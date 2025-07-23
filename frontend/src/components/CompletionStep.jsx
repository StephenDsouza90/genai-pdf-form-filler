import React, { useState, useEffect } from 'react'
import { Download, CheckCircle, RefreshCw } from 'lucide-react'
import { completeForm, downloadForm } from '../services/api'

const CompletionStep = ({ sessionId, filename, onStartOver }) => {
  const [isGenerating, setIsGenerating] = useState(true)
  const [isReady, setIsReady] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    generateCompletedForm()
  }, [sessionId])

  const generateCompletedForm = async () => {
    setIsGenerating(true)
    setError('')
    
    try {
      const result = await completeForm(sessionId)
      setDownloadUrl(result.download_url)
      setIsReady(true)
    } catch (err) {
      setError(err.message || 'Failed to generate completed form')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = async () => {
    try {
      await downloadForm(sessionId, `completed_${filename}`)
    } catch (err) {
      setError('Failed to download file')
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card text-center animate-slide-up">
        {isGenerating ? (
          <div className="py-8">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-500 mx-auto mb-6"></div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              Generating Your Completed Form
            </h3>
            <p className="text-gray-600">
              Please wait while we fill your PDF with all the provided information...
            </p>
          </div>
        ) : error ? (
          <div className="py-8">
            <div className="bg-red-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
              <RefreshCw className="w-8 h-8 text-red-500" />
            </div>
            <h3 className="text-xl font-semibold text-red-800 mb-2">
              Something went wrong
            </h3>
            <p className="text-red-600 mb-6">{error}</p>
            <div className="space-y-3">
              <button
                onClick={generateCompletedForm}
                className="btn-primary"
              >
                Try Again
              </button>
              <button
                onClick={onStartOver}
                className="btn-secondary ml-3"
              >
                Start Over
              </button>
            </div>
          </div>
        ) : (
          <div className="py-8">
            <div className="bg-green-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-2xl font-bold text-gray-800 mb-2">
              Form Completed Successfully! 🎉
            </h3>
            <p className="text-gray-600 mb-8">
              Your PDF form has been filled with all the information you provided. 
              You can now download the completed form.
            </p>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-8">
              <p className="text-sm text-gray-600 mb-1">Completed file:</p>
              <p className="font-medium text-gray-800">completed_{filename}</p>
            </div>

            <div className="space-y-3">
              <button
                onClick={handleDownload}
                className="btn-primary text-lg px-8 py-3 flex items-center mx-auto"
              >
                <Download className="w-5 h-5 mr-2" />
                Download Completed Form
              </button>
              
              <button
                onClick={onStartOver}
                className="btn-secondary"
              >
                Fill Another Form
              </button>
            </div>
          </div>
        )}
      </div>

      {isReady && (
        <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-medium text-green-800 mb-2">What's next?</h4>
          <ul className="text-sm text-green-700 space-y-1">
            <li>• Review the completed form for accuracy</li>
            <li>• Print or submit as required</li>
            <li>• Keep a copy for your records</li>
          </ul>
        </div>
      )}
    </div>
  )
}

export default CompletionStep