import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail)
    } else if (error.response?.status === 413) {
      throw new Error('File too large. Please select a smaller PDF file.')
    } else if (error.response?.status >= 500) {
      throw new Error('Server error. Please try again later.')
    } else {
      throw new Error(error.message || 'An unexpected error occurred')
    }
  }
)

// API Functions
export const uploadPDF = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export const getSessionFields = async (sessionId) => {
  return api.get(`/session/${sessionId}/fields`)
}

export const getNextQuestion = async (sessionId) => {
  return api.get(`/session/${sessionId}/question`)
}

export const submitAnswer = async (sessionId, fieldName, answer) => {
  return api.post(`/session/${sessionId}/answer`, {
    field_name: fieldName,
    answer: answer
  })
}

export const completeForm = async (sessionId) => {
  return api.get(`/session/${sessionId}/complete`)
}

export const downloadForm = async (sessionId, filename) => {
  try {
    const apiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || '';
    const url = `${apiUrl}/download/${sessionId}`;
    const response = await axios.get(url, {
      responseType: 'blob',
    });
    // Create blob link to download
    const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', filename || 'completed_form.pdf');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    console.error('Download error:', error);
    throw new Error('Failed to download file');
  }
}

export const getSessionStatus = async (sessionId) => {
  return api.get(`/session/${sessionId}/status`)
}

export const healthCheck = async () => {
  return api.get('/health')
}
