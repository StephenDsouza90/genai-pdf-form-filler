import React, { useState } from 'react'
import { Upload, MessageSquare, Download, CheckCircle } from 'lucide-react'
import UploadStep from './components/UploadStep'
import ConversationStep from './components/ConversationStep'
import CompletionStep from './components/CompletionStep'
import ProgressBar from './components/ProgressBar'
import Header from './components/Header'

const STEPS = {
  UPLOAD: 'upload',
  CONVERSATION: 'conversation',
  COMPLETION: 'completion'
}

function App() {
  const [currentStep, setCurrentStep] = useState(STEPS.UPLOAD)
  const [sessionData, setSessionData] = useState(null)
  const [progress, setProgress] = useState({ filled: 0, total: 0 })

  const handleUploadSuccess = (data) => {
    setSessionData(data)
    setProgress({ filled: 0, total: data.total_fields })
    setCurrentStep(STEPS.CONVERSATION)
  }

  const handleFormComplete = () => {
    setCurrentStep(STEPS.COMPLETION)
  }

  const handleStartOver = () => {
    setCurrentStep(STEPS.UPLOAD)
    setSessionData(null)
    setProgress({ filled: 0, total: 0 })
  }

  const getStepIcon = (step) => {
    const baseClass = "w-8 h-8"
    switch (step) {
      case STEPS.UPLOAD:
        return <Upload className={baseClass} />
      case STEPS.CONVERSATION:
        return <MessageSquare className={baseClass} />
      case STEPS.COMPLETION:
        return <CheckCircle className={baseClass} />
      default:
        return null
    }
  }

  const getStepTitle = (step) => {
    switch (step) {
      case STEPS.UPLOAD:
        return "Upload PDF Form"
      case STEPS.CONVERSATION:
        return "Fill Form Fields"
      case STEPS.COMPLETION:
        return "Download Complete Form"
      default:
        return ""
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Step Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {Object.values(STEPS).map((step, index) => (
              <div
                key={step}
                className={`flex items-center ${
                  index < Object.values(STEPS).length - 1 ? 'flex-1' : ''
                }`}
              >
                <div
                  className={`flex items-center justify-center w-12 h-12 rounded-full transition-all duration-300 ${
                    currentStep === step
                      ? 'bg-primary-500 text-white shadow-lg scale-110'
                      : Object.values(STEPS).indexOf(currentStep) > index
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {getStepIcon(step)}
                </div>
                {index < Object.values(STEPS).length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-4 rounded transition-all duration-300 ${
                      Object.values(STEPS).indexOf(currentStep) > index
                        ? 'bg-green-500'
                        : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              {getStepTitle(currentStep)}
            </h2>
            {currentStep === STEPS.CONVERSATION && sessionData && (
              <p className="text-gray-600">
                Filling form: <span className="font-medium">{sessionData.filename}</span>
              </p>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {currentStep === STEPS.CONVERSATION && (
          <div className="mb-8">
            <ProgressBar 
              current={progress.filled} 
              total={progress.total}
            />
          </div>
        )}

        {/* Step Content */}
        <div className="animate-fade-in">
          {currentStep === STEPS.UPLOAD && (
            <UploadStep onUploadSuccess={handleUploadSuccess} />
          )}
          
          {currentStep === STEPS.CONVERSATION && sessionData && (
            <ConversationStep
              sessionId={sessionData.session_id}
              onFormComplete={handleFormComplete}
              onProgressUpdate={setProgress}
            />
          )}
          
          {currentStep === STEPS.COMPLETION && sessionData && (
            <CompletionStep
              sessionId={sessionData.session_id}
              filename={sessionData.filename}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </main>
    </div>
  )
}

export default App