<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">🎯 Geração de Conteúdo IA</h1>
        <p class="mt-2 text-gray-600">
          Transforme suas transcrições em conteúdo otimizado para YouTube
        </p>
      </div>

      <!-- Transcription Selection -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">
          📝 Selecionar Transcrição
        </h2>
        
        <div v-if="loading.transcriptions" class="text-center py-8">
          <div class="spinner mx-auto"></div>
          <p class="mt-2 text-gray-600">Carregando transcrições...</p>
        </div>

        <div v-else-if="availableTranscriptions.length === 0" class="text-center py-8">
          <p class="text-gray-500">Nenhuma transcrição concluída encontrada.</p>
          <router-link 
            to="/upload" 
            class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Fazer Upload
          </router-link>
        </div>

        <div v-else class="space-y-3">
          <div 
            v-for="transcription in availableTranscriptions" 
            :key="transcription.id"
            class="border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors"
            :class="{ 'ring-2 ring-blue-500 bg-blue-50': selectedTranscription?.id === transcription.id }"
            @click="selectTranscription(transcription)"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <h3 class="font-medium text-gray-900">
                  {{ transcription.title || transcription.original_filename || 'Sem título' }}
                </h3>
                <div class="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                  <span class="flex items-center">
                    <span class="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                    {{ transcription.source_type }}
                  </span>
                  <span>{{ formatDate(transcription.created_at) }}</span>
                  <span v-if="transcription.duration_display">{{ transcription.duration_display }}</span>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span 
                  v-if="transcription.language_detected"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                >
                  {{ transcription.language_detected }}
                </span>
                <button
                  v-if="selectedTranscription?.id === transcription.id"
                  class="text-blue-600 hover:text-blue-800"
                >
                  ✓ Selecionada
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Content Generation Options -->
      <div v-if="selectedTranscription" class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <!-- Titles -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-900">🎯 Títulos</h3>
          </div>
          <p class="text-gray-600 text-sm mb-4">
            Gere títulos otimizados para aumentar o CTR
          </p>
          
          <div class="space-y-3 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Tipos de Título
              </label>
              <div class="space-y-2">
                <label v-for="type in titleTypes" :key="type.value" class="flex items-center">
                  <input 
                    type="checkbox" 
                    :value="type.value"
                    v-model="selectedTitleTypes"
                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  >
                  <span class="ml-2 text-sm text-gray-700">{{ type.label }}</span>
                </label>
              </div>
            </div>
            
            <div>
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  v-model="useMarkdownTitles"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                >
                <span class="ml-2 text-sm text-gray-700">Usar formatação Markdown</span>
              </label>
            </div>
          </div>

          <button
            @click="generateContent('titles')"
            :disabled="loading.titles || selectedTitleTypes.length === 0"
            class="w-full btn-primary"
          >
            <span v-if="loading.titles" class="flex items-center justify-center">
              <div class="spinner-sm mr-2"></div>
              Gerando...
            </span>
            <span v-else>Gerar Títulos</span>
          </button>
        </div>

        <!-- Description -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-900">📄 Descrição</h3>
          </div>
          <p class="text-gray-600 text-sm mb-4">
            Crie descrições que melhoram o SEO
          </p>
          
          <div class="space-y-3 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Descrição
              </label>
              <select 
                v-model="selectedDescriptionType"
                class="w-full input-field"
              >
                <option value="analítica">Analítica</option>
                <option value="curiosidade">Curiosidade</option>
                <option value="hashtags">Com Hashtags</option>
                <option value="tópicos">Tópicos</option>
                <option value="gatilhos">Gatilhos Emocionais</option>
                <option value="engajamento">Engajamento</option>
              </select>
            </div>
            
            <div>
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  v-model="useMarkdownDescription"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                >
                <span class="ml-2 text-sm text-gray-700">Usar formatação Markdown</span>
              </label>
            </div>
          </div>

          <button
            @click="generateContent('description')"
            :disabled="loading.description"
            class="w-full btn-primary"
          >
            <span v-if="loading.description" class="flex items-center justify-center">
              <div class="spinner-sm mr-2"></div>
              Gerando...
            </span>
            <span v-else>Gerar Descrição</span>
          </button>
        </div>

        <!-- Chapters -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-900">📚 Capítulos</h3>
          </div>
          <p class="text-gray-600 text-sm mb-4">
            Organize o conteúdo em capítulos com timestamps
          </p>
          
          <div class="space-y-3 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Máximo de Capítulos
              </label>
              <select 
                v-model="maxChapters"
                class="w-full input-field"
              >
                <option value="4">4 capítulos</option>
                <option value="6">6 capítulos</option>
                <option value="8">8 capítulos</option>
                <option value="10">10 capítulos</option>
                <option value="12">12 capítulos</option>
              </select>
            </div>
            
            <div>
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  v-model="useMarkdownChapters"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                >
                <span class="ml-2 text-sm text-gray-700">Usar formatação Markdown</span>
              </label>
            </div>
          </div>

          <button
            @click="generateContent('chapters')"
            :disabled="loading.chapters"
            class="w-full btn-primary"
          >
            <span v-if="loading.chapters" class="flex items-center justify-center">
              <div class="spinner-sm mr-2"></div>
              Gerando...
            </span>
            <span v-else>Gerar Capítulos</span>
          </button>
        </div>
      </div>

      <!-- Complete Package Section -->
      <div v-if="selectedTranscription" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <div class="flex items-center mb-4">
          <h2 class="text-xl font-semibold text-gray-900">📦 Pacote Completo</h2>
        </div>
        <p class="text-gray-600 text-sm mb-6">
          Gere todos os tipos de conteúdo de uma vez com suas configurações personalizadas
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <!-- Content Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-3">
              Conteúdo a Gerar
            </label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  v-model="completePackage.generateTitles"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                >
                <span class="ml-2 text-sm text-gray-700">Gerar Títulos</span>
              </label>
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  v-model="completePackage.generateDescription"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                >
                <span class="ml-2 text-sm text-gray-700">Gerar Descrição</span>
              </label>
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  v-model="completePackage.generateChapters"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                >
                <span class="ml-2 text-sm text-gray-700">Gerar Capítulos</span>
              </label>
            </div>
          </div>

          <!-- Output Format -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-3">
              Formato de Saída
            </label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input 
                  type="radio" 
                  value="false"
                  v-model="completePackage.useMarkdown"
                  name="outputFormat"
                  class="text-blue-600 focus:ring-blue-500"
                >
                <span class="ml-2 text-sm text-gray-700">Texto simples (sem formatação)</span>
              </label>
              <label class="flex items-center">
                <input 
                  type="radio" 
                  value="true"
                  v-model="completePackage.useMarkdown"
                  name="outputFormat"
                  class="text-blue-600 focus:ring-blue-500"
                >
                <span class="ml-2 text-sm text-gray-700">Markdown (com formatação)</span>
              </label>
            </div>
          </div>

          <!-- Description Type -->
          <div v-if="completePackage.generateDescription">
            <label class="block text-sm font-medium text-gray-700 mb-3">
              Tipo de Descrição
            </label>
            <select 
              v-model="completePackage.descriptionType"
              class="w-full input-field"
            >
              <option value="analítica">Analítica</option>
              <option value="curiosidade">Curiosidade</option>
              <option value="hashtags">Com Hashtags</option>
              <option value="tópicos">Tópicos</option>
              <option value="gatilhos">Gatilhos Emocionais</option>
              <option value="engajamento">Engajamento</option>
            </select>
          </div>

          <!-- Number of Chapters -->
          <div v-if="completePackage.generateChapters">
            <label class="block text-sm font-medium text-gray-700 mb-3">
              Número de Capítulos
            </label>
            <div class="flex items-center space-x-3">
              <input 
                type="range" 
                v-model="completePackage.maxChapters"
                min="3" 
                max="20" 
                step="1"
                class="flex-1"
              >
              <span class="text-sm font-medium text-gray-700 min-w-0">
                {{ completePackage.maxChapters }}
              </span>
            </div>
          </div>
        </div>

        <button
          @click="generateCompletePackage()"
          :disabled="loading.complete || !hasSelectedContent"
          class="w-full btn-primary bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
        >
          <span v-if="loading.complete" class="flex items-center justify-center">
            <div class="spinner-sm mr-2"></div>
            Gerando Pacote Completo...
          </span>
          <span v-else>🚀 Gerar Pacote Completo</span>
        </button>
      </div>

      <!-- Generated Content Results -->
      <div v-if="generatedContent.length > 0" class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900">📋 Conteúdo Gerado</h2>
        
        <div 
          v-for="content in generatedContent" 
          :key="content.id"
          class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center space-x-3">
              <span class="text-lg">
                {{ getContentIcon(content.content_type) }}
              </span>
              <h3 class="text-lg font-semibold text-gray-900">
                {{ getContentTitle(content.content_type) }}
              </h3>
              <span 
                :class="getStatusClass(content.status)"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
              >
                {{ getStatusText(content.status) }}
              </span>
            </div>
            
            <div class="flex items-center space-x-2">
              <button
                v-if="content.status === 'completed'"
                @click="copyToClipboard(content.generated_content)"
                class="text-gray-400 hover:text-gray-600"
                title="Copiar"
              >
                📋
              </button>
              <button
                @click="deleteContent(content.id)"
                class="text-red-400 hover:text-red-600"
                title="Excluir"
              >
                🗑️
              </button>
            </div>
          </div>

          <div v-if="content.status === 'completed'" class="prose max-w-none">
            <div 
              v-if="content.use_markdown"
              v-html="renderMarkdown(content.generated_content)"
              class="markdown-content"
            ></div>
            <pre v-else class="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-lg">{{ content.generated_content }}</pre>
          </div>

          <div v-else-if="content.status === 'processing'" class="text-center py-8">
            <div class="spinner mx-auto"></div>
            <p class="mt-2 text-gray-600">Gerando conteúdo...</p>
          </div>

          <div v-else-if="content.status === 'failed'" class="text-center py-8">
            <p class="text-red-600">❌ Erro na geração</p>
            <p class="text-sm text-gray-500 mt-1">{{ content.error_message }}</p>
            <button
              @click="retryContentGeneration(content.id)"
              class="mt-3 btn-outline"
            >
              Tentar Novamente
            </button>
          </div>

          <div class="mt-4 text-xs text-gray-500">
            Gerado em {{ formatDate(content.created_at) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'vue-toastification'
import api from '@/services/api'

export default {
  name: 'ContentGenerationView',
  setup() {
    const toast = useToast()
    
    // State
    const availableTranscriptions = ref([])
    const selectedTranscription = ref(null)
    const generatedContent = ref([])
    
    const loading = ref({
      transcriptions: false,
      titles: false,
      description: false,
      chapters: false,
      complete: false
    })

    // Form data
    const selectedTitleTypes = ref(['impactante', 'analítico'])
    const useMarkdownTitles = ref(false)
    const selectedDescriptionType = ref('analítica')
    const useMarkdownDescription = ref(false)
    const maxChapters = ref(6)
    const useMarkdownChapters = ref(false)
    const completePackage = ref({
      generateTitles: true,
      generateDescription: true,
      generateChapters: true,
      useMarkdown: false,
      descriptionType: 'analítica',
      maxChapters: 6
    })

    // Options
    const titleTypes = [
      { value: 'impactante', label: 'Impactante' },
      { value: 'analítico', label: 'Analítico' },
      { value: 'agressivo', label: 'Agressivo' },
      { value: 'nicho', label: 'Nicho' },
      { value: 'engajamento', label: 'Engajamento' },
      { value: 'curiosidade', label: 'Curiosidade' },
      { value: 'seo_classico', label: 'SEO Clássico' },
      { value: 'storytelling', label: 'Storytelling' },
      { value: 'shorts', label: 'Shorts' },
      { value: 'live_podcast', label: 'Live/Podcast' }
    ]

    // Methods
    const loadAvailableTranscriptions = async () => {
      loading.value.transcriptions = true
      try {
        const response = await api.get('/content/available-transcriptions/')
        availableTranscriptions.value = response.data
      } catch (error) {
        toast.error('Erro ao carregar transcrições')
        console.error(error)
      } finally {
        loading.value.transcriptions = false
      }
    }

    const selectTranscription = (transcription) => {
      selectedTranscription.value = transcription
      loadGeneratedContent()
    }

    const loadGeneratedContent = async () => {
      if (!selectedTranscription.value) return
      
      try {
        const response = await api.get('/content/', {
          params: { transcription: selectedTranscription.value.id }
        })
        generatedContent.value = response.data.results || []
      } catch (error) {
        console.error('Erro ao carregar conteúdo gerado:', error)
      }
    }

    const generateContent = async (contentType) => {
      if (!selectedTranscription.value) {
        toast.error('Selecione uma transcrição primeiro')
        return
      }

      loading.value[contentType] = true

      try {
        const payload = {
          transcription_id: selectedTranscription.value.id,
          content_type: contentType
        }

        if (contentType === 'titles') {
          payload.title_types = selectedTitleTypes.value
          payload.use_markdown = useMarkdownTitles.value
        } else if (contentType === 'description') {
          payload.description_type = selectedDescriptionType.value
          payload.use_markdown = useMarkdownDescription.value
        } else if (contentType === 'chapters') {
          payload.max_chapters = parseInt(maxChapters.value)
          payload.use_markdown = useMarkdownChapters.value
        }

        const response = await api.post('content/create/', payload)
        
        toast.success('Geração de conteúdo iniciada!')
        
        // Add to generated content list
        generatedContent.value.unshift(response.data.content_generation)
        
        // Poll for updates
        pollContentStatus(response.data.content_generation.id)
        
      } catch (error) {
        toast.error('Erro ao gerar conteúdo. Por favor, tente novamente.')
        console.error(error)
      } finally {
        loading.value[contentType] = false
      }
    }

    const pollContentStatus = async (contentId) => {
      const maxAttempts = 30 // 5 minutes max
      let attempts = 0
      
      const poll = async () => {
        try {
          const response = await api.get(`/content/${contentId}/`)
          const content = response.data
          
          // Update in list
          const index = generatedContent.value.findIndex(c => c.id === contentId)
          if (index !== -1) {
            generatedContent.value[index] = content
          }
          
          if (content.status === 'completed') {
            toast.success('Conteúdo gerado com sucesso!')
            return
          } else if (content.status === 'failed') {
            toast.error('Falha na geração de conteúdo')
            return
          } else if (attempts < maxAttempts) {
            attempts++
            setTimeout(poll, 10000) // Poll every 10 seconds
          } else {
            toast.warning('Tempo limite excedido. Verifique o status manualmente.')
          }
        } catch (error) {
          console.error('Erro ao verificar status:', error)
        }
      }
      
      setTimeout(poll, 5000) // Start polling after 5 seconds
    }

    const retryContentGeneration = async (contentId) => {
      try {
        await api.post(`/content/${contentId}/retry/`)
        toast.success('Reprocessamento iniciado!')
        pollContentStatus(contentId)
      } catch (error) {
        toast.error('Erro ao tentar reprocessar')
        console.error(error)
      }
    }

    const deleteContent = async (contentId) => {
      if (!confirm('Tem certeza que deseja excluir este conteúdo?')) return
      
      try {
        await api.delete(`/content/${contentId}/delete/`)
        generatedContent.value = generatedContent.value.filter(c => c.id !== contentId)
        toast.success('Conteúdo excluído')
      } catch (error) {
        toast.error('Erro ao excluir conteúdo')
        console.error(error)
      }
    }

    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        toast.success('Copiado para a área de transferência!')
      } catch (error) {
        toast.error('Erro ao copiar')
      }
    }

    const generateCompletePackage = async () => {
      if (!selectedTranscription.value) {
        toast.error('Selecione uma transcrição primeiro')
        return
      }

      loading.value.complete = true

      try {
        const payload = {
          transcription_id: selectedTranscription.value.id,
          content_type: 'complete',
          use_markdown: completePackage.value.useMarkdown === 'true' || completePackage.value.useMarkdown === true
        }

        // Only add options for selected content types
        if (completePackage.value.generateTitles) {
          payload.title_types = selectedTitleTypes.value.length > 0 ? selectedTitleTypes.value : ['impactante', 'analítico']
        }

        if (completePackage.value.generateDescription) {
          payload.description_type = completePackage.value.descriptionType
        }

        if (completePackage.value.generateChapters) {
          payload.max_chapters = parseInt(completePackage.value.maxChapters)
        }

        const response = await api.post('content/create/', payload)
        
        toast.success('Geração de pacote completo iniciada!')
        
        // Add to generated content list
        generatedContent.value.unshift(response.data.content_generation)
        
        // Poll for updates
        pollContentStatus(response.data.content_generation.id)
        
      } catch (error) {
        toast.error('Erro ao gerar pacote completo')
        console.error(error)
      } finally {
        loading.value.complete = false
      }
    }

    // Computed properties
    const hasSelectedContent = computed(() => {
      return completePackage.value.generateTitles || 
             completePackage.value.generateDescription || 
             completePackage.value.generateChapters
    })

    // Utility functions
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('pt-BR')
    }

    const getContentIcon = (contentType) => {
      const icons = {
        titles: '🎯',
        description: '📄',
        chapters: '📚',
        complete: '📦'
      }
      return icons[contentType] || '📄'
    }

    const getContentTitle = (contentType) => {
      const titles = {
        titles: 'Títulos',
        description: 'Descrição',
        chapters: 'Capítulos',
        complete: 'Pacote Completo'
      }
      return titles[contentType] || contentType
    }

    const getStatusClass = (status) => {
      const classes = {
        pending: 'bg-yellow-100 text-yellow-800',
        processing: 'bg-blue-100 text-blue-800',
        completed: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const getStatusText = (status) => {
      const texts = {
        pending: 'Pendente',
        processing: 'Processando',
        completed: 'Concluído',
        failed: 'Falhou'
      }
      return texts[status] || status
    }

    const renderMarkdown = (text) => {
      // Simple markdown rendering (you might want to use a proper markdown library)
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>')
    }

    // Lifecycle
    onMounted(() => {
      loadAvailableTranscriptions()
    })

    return {
      // State
      availableTranscriptions,
      selectedTranscription,
      generatedContent,
      loading,
      
      // Form data
      selectedTitleTypes,
      useMarkdownTitles,
      selectedDescriptionType,
      useMarkdownDescription,
      maxChapters,
      useMarkdownChapters,
      completePackage,
      
      // Options
      titleTypes,
      
      // Methods
      selectTranscription,
      generateContent,
      retryContentGeneration,
      deleteContent,
      copyToClipboard,
      generateCompletePackage,
      
      // Utilities
      formatDate,
      getContentIcon,
      getContentTitle,
      getStatusClass,
      getStatusText,
      renderMarkdown,
      
      // Computed properties
      hasSelectedContent
    }
  }
}
</script>

<style scoped>
.spinner {
  @apply w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin;
}

.spinner-sm {
  @apply w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin;
}

.markdown-content {
  @apply text-sm text-gray-700;
}

.markdown-content strong {
  @apply font-semibold text-gray-900;
}

.markdown-content em {
  @apply italic;
}

.markdown-content code {
  @apply bg-gray-100 px-1 py-0.5 rounded text-xs font-mono;
}
</style> 