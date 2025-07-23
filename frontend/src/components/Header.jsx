import React from 'react'
import { FileText, Sparkles } from 'lucide-react'

const Header = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center">
          <div className="flex items-center space-x-3">
            <div className="bg-primary-500 p-2 rounded-lg">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                AI PDF Form Filler
              </h1>
              <p className="text-sm text-gray-600 flex items-center">
                <Sparkles className="w-4 h-4 mr-1" />
                Smart form filling made simple
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header