import React, { useState, useEffect } from 'react'
import { MessageSquare, Send, Loader } from 'lucide-react'
import { getNextQuestion, submitAnswer, getSessionStatus } from '../services/api'

const ConversationStep = ({ sessionId, onFormComplete, onProgressUpdate }) => {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [currentField, setCurrentField] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [conversation, setConversation] = useState([])

  useEffect(() => {
    loadNextQuestion()
    updateProgress()
  }, [sessionId])

  const loadNextQuestion = async () => {
    setIsLoading(true)
    try {
      const response = await getNextQuestion(sessionId)
      
      if (response.is_complete) {
        onFormComplete()
        return
      }

      setQuestion(response.question)
      setCurrentField({
        name: response.field_name,
        type: response.field_type
      })
    } catch (error) {
      console.error('Error loading question:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const updateProgress = async () => {
    try {
      const status = await getSessionStatus(sessionId)
      onProgressUpdate({
        filled: status.filled_fields,
        total: status.total_fields
      })
    } catch (error) {
      console.error('Error updating progress:', error)
    }
  }

  const handleSubmitAnswer = async (e) => {
    e.preventDefault()
    if (!answer.trim() || !currentField) return

    setIsSubmitting(true)
    try {
      // Add to conversation history
      setConversation(prev => [...prev, {
        type: 'question',
        text: question,
        fieldName: currentField.name
      }, {
        type: 'answer',
        text: answer
      }])

      await submitAnswer(sessionId, currentField.name, answer)
      setAnswer('')
      
      // Update progress
      await updateProgress()
      
      // Load next question
      await loadNextQuestion()
    } catch (error) {
      console.error('Error submitting answer:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading && conversation.length === 0) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="card text-center">
          <Loader className="w-8 h-8 animate-spin mx-auto mb-4 text-primary-500" />
          <p className="text-gray-600">Analyzing your PDF form...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card">
        {/* Conversation History */}
        {conversation.length > 0 && (
          <div className="mb-6 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center">
              <MessageSquare className="w-5 h-5 mr-2" />
              Conversation History
            </h3>
            <div className="space-y-3">
              {conversation.map((entry, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg ${
                    entry.type === 'question'
                      ? 'bg-gray-50 border-l-4 border-primary-500'
                      : 'bg-primary-50 border-l-4 border-green-500 ml-4'
                  }`}
                >
                  <p className={`text-sm ${
                    entry.type === 'question' ? 'text-gray-700' : 'text-primary-700'
                  }`}>
                    {entry.type === 'question' ? '🤖 AI Assistant:' : '👤 You:'}
                  </p>
                  <p className="mt-1">{entry.text}</p>
                  {entry.fieldName && (
                    <p className="text-xs text-gray-500 mt-1">
                      Field: {entry.fieldName}
                    </p>
                  )}
                </div>
              ))}
            </div>
            <hr className="my-6" />
          </div>
        )}

        {/* Current Question */}
        <div className="mb-6">
          <div className="bg-gray-50 border-l-4 border-primary-500 p-4 rounded-r-lg mb-4">
            <div className="flex items-start">
              <div className="bg-primary-500 rounded-full p-1 mr-3 mt-1">
                <MessageSquare className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-600 mb-1">AI Assistant asks:</p>
                <p className="text-gray-800 text-lg">{question}</p>
                {currentField && (
                  <p className="text-xs text-gray-500 mt-2">
                    Field: {currentField.name} ({currentField.type})
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Answer Form */}
        <form onSubmit={handleSubmitAnswer} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Answer:
            </label>
            {currentField?.type === 'checkbox' ? (
              <select
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="input"
                required
              >
                <option value="">Select an option...</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            ) : (
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type your answer here..."
                className="input resize-none"
                rows="3"
                required
                disabled={isSubmitting}
              />
            )}
          </div>
          
          <button
            type="submit"
            disabled={!answer.trim() || isSubmitting}
            className="btn-primary w-full flex items-center justify-center"
          >
            {isSubmitting ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Submit Answer
              </>
            )}
          </button>
        </form>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-700">
            💡 <strong>Tip:</strong> Be as specific as possible in your answers. 
            The AI will help format them appropriately for the form.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ConversationStep