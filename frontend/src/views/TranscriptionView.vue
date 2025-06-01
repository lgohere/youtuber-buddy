<template>
  <div class="transcription-view">
    <!-- Header -->
    <div class="header">
      <div class="container">
        <button @click="goBack" class="back-btn">
          ← Voltar
        </button>
        <h1 class="title">Transcrição</h1>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Carregando transcrição...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-card">
        <h2>Erro ao carregar transcrição</h2>
        <p>{{ error }}</p>
        <button @click="loadTranscription" class="retry-btn">Tentar novamente</button>
      </div>
    </div>

    <!-- Transcription Content -->
    <div v-else-if="transcription" class="content">
      <div class="container">
        <!-- Transcription Info -->
        <div class="transcription-info">
          <div class="info-header">
            <h2>{{ transcription.title || transcription.original_filename || 'Transcrição' }}</h2>
            <div class="status-badge" :class="transcription.status">
              {{ getStatusText(transcription.status) }}
            </div>
          </div>
          
          <div class="info-details">
            <span v-if="transcription.duration_display">⏱️ {{ transcription.duration_display }}</span>
            <span v-if="transcription.file_size_display">📁 {{ transcription.file_size_display }}</span>
            <span v-if="transcription.language_detected">🌐 {{ transcription.language_detected }}</span>
            <span>📅 {{ formatDate(transcription.created_at) }}</span>
          </div>
        </div>

        <!-- Processing State -->
        <div v-if="transcription.status === 'processing'" class="processing-card">
          <div class="processing-content">
            <div class="spinner"></div>
            <h3>Processando transcrição...</h3>
            <p>Aguarde enquanto processamos seu arquivo. Isso pode levar alguns minutos.</p>
            <button @click="loadTranscription" class="refresh-btn">Atualizar status</button>
          </div>
        </div>

        <!-- Failed State -->
        <div v-else-if="transcription.status === 'failed'" class="failed-card">
          <div class="failed-content">
            <h3>Falha no processamento</h3>
            <p v-if="transcription.error_message">{{ transcription.error_message }}</p>
            <p v-else>Ocorreu um erro durante o processamento da transcrição.</p>
            <button @click="retryTranscription" class="retry-btn">Tentar novamente</button>
          </div>
        </div>

        <!-- Completed Transcription -->
        <div v-else-if="transcription.status === 'completed' && transcription.transcription_text" class="transcription-content">
          <!-- Transcription Text -->
          <div class="transcription-card">
            <div class="card-header">
              <h3>Texto da Transcrição</h3>
              <button @click="copyTranscription" class="copy-btn">
                📋 Copiar
              </button>
            </div>
            <div class="transcription-text">
              {{ transcription.transcription_text }}
            </div>
          </div>

          <!-- AI Content Generation -->
          <div class="ai-section">
            <h3>Gerar Conteúdo com IA</h3>
            <p>Use inteligência artificial para criar títulos, descrições e capítulos baseados na sua transcrição.</p>
            
            <div class="ai-options">
              <button @click="generateTitles" class="ai-btn" :disabled="generatingContent">
                <span class="icon">🎯</span>
                <div class="btn-content">
                  <strong>Gerar Títulos</strong>
                  <small>Títulos otimizados para YouTube</small>
                </div>
              </button>

              <button @click="generateDescription" class="ai-btn" :disabled="generatingContent">
                <span class="icon">📝</span>
                <div class="btn-content">
                  <strong>Gerar Descrição</strong>
                  <small>Descrição completa e otimizada</small>
                </div>
              </button>

              <button @click="generateChapters" class="ai-btn" :disabled="generatingContent">
                <span class="icon">📚</span>
                <div class="btn-content">
                  <strong>Gerar Capítulos</strong>
                  <small>Timestamps e títulos dos capítulos</small>
                </div>
              </button>

              <button @click="generateComplete" class="ai-btn complete" :disabled="generatingContent">
                <span class="icon">✨</span>
                <div class="btn-content">
                  <strong>Pacote Completo</strong>
                  <small>Títulos + Descrição + Capítulos</small>
                </div>
              </button>
            </div>

            <!-- Generation Loading -->
            <div v-if="generatingContent" class="generation-loading">
              <div class="spinner"></div>
              <p>Gerando conteúdo com IA...</p>
            </div>
          </div>

          <!-- Generated Content Results -->
          <div v-if="generatedContent" class="generated-content">
            <h3>Conteúdo Gerado</h3>
            <div class="generated-card">
              <div class="card-header">
                <h4>{{ generatedContent.content_type }}</h4>
                <button @click="copyGenerated" class="copy-btn">
                  📋 Copiar
                </button>
              </div>
              <div class="generated-text">
                <pre>{{ generatedContent.generated_content }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()

// Reactive data
const loading = ref(true)
const error = ref(null)
const transcription = ref(null)
const generatingContent = ref(false)
const generatedContent = ref(null)

// Methods
const loadTranscription = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await api.get(`/transcriptions/${route.params.id}/`)
    transcription.value = response.data
    
    // If still processing, set up polling
    if (transcription.value.status === 'processing') {
      setTimeout(loadTranscription, 5000) // Poll every 5 seconds
    }
  } catch (err) {
    console.error('Error loading transcription:', err)
    error.value = err.response?.data?.error || 'Erro ao carregar transcrição'
  } finally {
    loading.value = false
  }
}

const retryTranscription = async () => {
  try {
    await api.post(`/transcriptions/${route.params.id}/retry/`)
    await loadTranscription()
  } catch (err) {
    console.error('Error retrying transcription:', err)
    error.value = 'Erro ao tentar reprocessar transcrição'
  }
}

const generateTitles = async () => {
  await generateContent('titles')
}

const generateDescription = async () => {
  await generateContent('description')
}

const generateChapters = async () => {
  await generateContent('chapters')
}

const generateComplete = async () => {
  await generateContent('complete')
}

const generateContent = async (contentType) => {
  try {
    generatingContent.value = true
    
    const response = await api.post('/content/create/', {
      transcription_id: transcription.value.id,
      content_type: contentType
    })
    
    // Get the content generation ID from the response
    const contentGenerationId = response.data.content_generation.id
    
    // Poll for completion
    const pollForCompletion = async () => {
      try {
        const contentResponse = await api.get(`/content/${contentGenerationId}/`)
        const contentData = contentResponse.data
        
        if (contentData.status === 'completed') {
          generatedContent.value = contentData
          generatingContent.value = false
        } else if (contentData.status === 'failed') {
          error.value = contentData.error_message || 'Erro ao gerar conteúdo'
          generatingContent.value = false
        } else {
          // Still processing, poll again in 3 seconds
          setTimeout(pollForCompletion, 3000)
        }
      } catch (err) {
        console.error('Error polling for content:', err)
        error.value = 'Erro ao verificar status do conteúdo'
        generatingContent.value = false
      }
    }
    
    // Start polling
    setTimeout(pollForCompletion, 2000) // Wait 2 seconds before first poll
    
  } catch (err) {
    console.error('Error generating content:', err)
    error.value = 'Erro ao gerar conteúdo com IA'
    generatingContent.value = false
  }
}

const copyTranscription = async () => {
  try {
    await navigator.clipboard.writeText(transcription.value.transcription_text)
    // You could add a toast notification here
  } catch (err) {
    console.error('Error copying text:', err)
  }
}

const copyGenerated = async () => {
  try {
    await navigator.clipboard.writeText(generatedContent.value.generated_content)
    // You could add a toast notification here
  } catch (err) {
    console.error('Error copying text:', err)
  }
}

const goBack = () => {
  router.push('/upload')
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': 'Pendente',
    'processing': 'Processando',
    'completed': 'Concluído',
    'failed': 'Falhou'
  }
  return statusMap[status] || status
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('pt-BR')
}

// Lifecycle
onMounted(() => {
  loadTranscription()
})
</script>

<style scoped>
.transcription-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
}

.header {
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #333;
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.header .container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-btn {
  background: transparent;
  border: 1px solid #00bcd4;
  color: #00bcd4;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #00bcd4;
  color: #000;
  box-shadow: 0 0 20px rgba(0, 188, 212, 0.3);
}

.title {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0;
}

.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.error-card {
  background: rgba(255, 0, 0, 0.1);
  border: 1px solid #ff4444;
  border-radius: 12px;
  padding: 2rem;
  max-width: 500px;
}

.content {
  padding: 2rem 0;
}

.transcription-info {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #333;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.info-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
}

.status-badge.completed {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  border: 1px solid #4caf50;
}

.status-badge.processing {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  border: 1px solid #ffc107;
}

.status-badge.failed {
  background: rgba(244, 67, 54, 0.2);
  color: #f44336;
  border: 1px solid #f44336;
}

.info-details {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.875rem;
  color: #ccc;
}

.processing-card, .failed-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #333;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  margin-bottom: 2rem;
}

.transcription-card, .generated-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #333;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #333;
}

.card-header h3, .card-header h4 {
  margin: 0;
}

.copy-btn {
  background: transparent;
  border: 1px solid #00bcd4;
  color: #00bcd4;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.copy-btn:hover {
  background: #00bcd4;
  color: #000;
}

.transcription-text, .generated-text {
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 500px;
  overflow-y: auto;
}

.transcription-text pre {
  margin: 0;
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.generated-text pre {
  margin: 0;
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.ai-section {
  margin: 2rem 0;
}

.ai-section h3 {
  margin-bottom: 0.5rem;
}

.ai-section p {
  color: #ccc;
  margin-bottom: 1.5rem;
}

.ai-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.ai-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #333;
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
  color: #fff;
}

.ai-btn:hover:not(:disabled) {
  background: rgba(0, 188, 212, 0.1);
  border-color: #00bcd4;
  box-shadow: 0 0 20px rgba(0, 188, 212, 0.2);
}

.ai-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-btn.complete {
  border-color: #ff6b35;
}

.ai-btn.complete:hover:not(:disabled) {
  background: rgba(255, 107, 53, 0.1);
  border-color: #ff6b35;
  box-shadow: 0 0 20px rgba(255, 107, 53, 0.2);
}

.ai-btn .icon {
  font-size: 1.5rem;
}

.btn-content strong {
  display: block;
  margin-bottom: 0.25rem;
}

.btn-content small {
  color: #ccc;
  font-size: 0.875rem;
}

.generation-loading {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: center;
  padding: 2rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #333;
  border-top: 2px solid #00bcd4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn, .refresh-btn {
  background: #00bcd4;
  border: none;
  color: #000;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  font-weight: bold;
  transition: all 0.3s ease;
}

.retry-btn:hover, .refresh-btn:hover {
  background: #00acc1;
  box-shadow: 0 0 20px rgba(0, 188, 212, 0.3);
}

@media (max-width: 768px) {
  .container {
    padding: 0 1rem;
  }
  
  .ai-options {
    grid-template-columns: 1fr;
  }
  
  .info-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .info-details {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style> 