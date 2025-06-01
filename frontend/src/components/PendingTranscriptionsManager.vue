<template>
  <div class="pending-transcriptions-manager">
    <div class="card">
      <div class="card-header">
        <h3 class="text-lg font-semibold text-gray-800">
          <i class="fas fa-clock mr-2"></i>
          Gerenciar Transcrições Pendentes
        </h3>
        <p class="text-sm text-gray-600 mt-1">
          Visualize e delete transcrições que estão pendentes há muito tempo
        </p>
      </div>

      <div class="card-body">
        <!-- Filters -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Fonte
            </label>
            <select v-model="filters.source_type" class="input-field">
              <option value="">Todos</option>
              <option value="youtube">YouTube</option>
              <option value="audio_upload">Upload de Áudio</option>
              <option value="video_upload">Upload de Vídeo</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Mais antigas que (horas)
            </label>
            <input 
              v-model.number="filters.older_than_hours" 
              type="number" 
              min="1" 
              class="input-field"
              placeholder="Ex: 24"
            >
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Limite
            </label>
            <input 
              v-model.number="filters.limit" 
              type="number" 
              min="1" 
              max="100" 
              class="input-field"
              placeholder="Ex: 10"
            >
          </div>

          <div class="flex items-end">
            <button 
              @click="loadPendingTranscriptions"
              :disabled="loading"
              class="btn-primary w-full"
            >
              <i class="fas fa-search mr-2"></i>
              {{ loading ? 'Carregando...' : 'Buscar' }}
            </button>
          </div>
        </div>

        <!-- Results -->
        <div v-if="pendingData">
          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <div class="flex items-center">
              <i class="fas fa-exclamation-triangle text-yellow-600 mr-2"></i>
              <span class="font-medium text-yellow-800">
                {{ pendingData.message }}
              </span>
            </div>
            <p class="text-sm text-yellow-700 mt-1">
              Total encontrado: {{ pendingData.total_count }} transcrições
            </p>
          </div>

          <!-- Preview List -->
          <div v-if="pendingData.preview && pendingData.preview.length > 0" class="mb-4">
            <h4 class="font-medium text-gray-800 mb-3">Preview das transcrições:</h4>
            <div class="space-y-2">
              <div 
                v-for="item in pendingData.preview" 
                :key="item.id"
                class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div class="flex-1">
                  <div class="flex items-center space-x-3">
                    <span class="badge badge-warning">{{ item.source_type }}</span>
                    <span class="text-sm font-medium text-gray-800">
                      {{ item.filename || 'Sem nome' }}
                    </span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    ID: {{ item.id }} • Idade: {{ item.age_hours }}h • 
                    Criado: {{ formatDate(item.created_at) }}
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="pendingData.total_count > pendingData.preview.length" class="text-sm text-gray-500 mt-2">
              ... e mais {{ pendingData.total_count - pendingData.preview.length }} transcrições
            </div>
          </div>

          <!-- Delete Actions -->
          <div class="flex items-center justify-between pt-4 border-t">
            <div class="text-sm text-gray-600">
              <i class="fas fa-info-circle mr-1"></i>
              Esta operação é irreversível
            </div>
            
            <div class="space-x-3">
              <button 
                @click="clearResults"
                class="btn-outline"
              >
                Cancelar
              </button>
              
              <button 
                @click="confirmDelete"
                :disabled="deleting"
                class="btn-danger"
              >
                <i class="fas fa-trash mr-2"></i>
                {{ deleting ? 'Deletando...' : `Deletar ${pendingData.total_count} Transcrições` }}
              </button>
            </div>
          </div>
        </div>

        <!-- No Results -->
        <div v-else-if="searched && !pendingData" class="text-center py-8">
          <i class="fas fa-check-circle text-green-500 text-4xl mb-3"></i>
          <h3 class="text-lg font-medium text-gray-800 mb-2">
            Nenhuma transcrição pendente encontrada
          </h3>
          <p class="text-gray-600">
            Não há transcrições pendentes com os critérios especificados.
          </p>
        </div>

        <!-- Initial State -->
        <div v-else class="text-center py-8">
          <i class="fas fa-search text-gray-400 text-4xl mb-3"></i>
          <h3 class="text-lg font-medium text-gray-800 mb-2">
            Buscar Transcrições Pendentes
          </h3>
          <p class="text-gray-600">
            Configure os filtros acima e clique em "Buscar" para encontrar transcrições pendentes.
          </p>
        </div>
      </div>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="showConfirmModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div class="text-center">
          <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-4"></i>
          <h3 class="text-lg font-bold text-gray-800 mb-2">
            Confirmar Deleção
          </h3>
          <p class="text-gray-600 mb-6">
            Tem certeza que deseja deletar {{ pendingData?.total_count }} transcrições pendentes?
            <br><br>
            <strong class="text-red-600">Esta ação é irreversível!</strong>
          </p>
          
          <div class="flex space-x-3">
            <button 
              @click="showConfirmModal = false"
              class="btn-outline flex-1"
            >
              Cancelar
            </button>
            <button 
              @click="deletePendingTranscriptions"
              :disabled="deleting"
              class="btn-danger flex-1"
            >
              {{ deleting ? 'Deletando...' : 'Confirmar Deleção' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import api from '@/services/api'
import { useToast } from 'vue-toastification'

export default {
  name: 'PendingTranscriptionsManager',
  setup() {
    const toast = useToast()
    
    const loading = ref(false)
    const deleting = ref(false)
    const searched = ref(false)
    const pendingData = ref(null)
    const showConfirmModal = ref(false)
    
    const filters = reactive({
      source_type: '',
      older_than_hours: null,
      limit: null
    })

    const loadPendingTranscriptions = async () => {
      loading.value = true
      searched.value = true
      pendingData.value = null
      
      try {
        const payload = {}
        
        if (filters.source_type) payload.source_type = filters.source_type
        if (filters.older_than_hours) payload.older_than_hours = filters.older_than_hours
        if (filters.limit) payload.limit = filters.limit
        
        const response = await api.post('/transcriptions/delete-pending/', payload)
        pendingData.value = response.data
        
        if (response.data.total_count === 0) {
          toast.info('Nenhuma transcrição pendente encontrada com os critérios especificados')
        }
        
      } catch (error) {
        console.error('Erro ao buscar transcrições pendentes:', error)
        toast.error('Erro ao buscar transcrições pendentes')
      } finally {
        loading.value = false
      }
    }

    const confirmDelete = () => {
      showConfirmModal.value = true
    }

    const deletePendingTranscriptions = async () => {
      deleting.value = true
      
      try {
        const payload = { force: true }
        
        if (filters.source_type) payload.source_type = filters.source_type
        if (filters.older_than_hours) payload.older_than_hours = filters.older_than_hours
        if (filters.limit) payload.limit = filters.limit
        
        const response = await api.post('/transcriptions/delete-pending/', payload)
        
        toast.success(response.data.message)
        
        if (response.data.failed_count > 0) {
          toast.warning(`${response.data.failed_count} transcrições falharam ao ser deletadas`)
        }
        
        // Clear results
        clearResults()
        showConfirmModal.value = false
        
      } catch (error) {
        console.error('Erro ao deletar transcrições pendentes:', error)
        toast.error('Erro ao deletar transcrições pendentes')
      } finally {
        deleting.value = false
      }
    }

    const clearResults = () => {
      pendingData.value = null
      searched.value = false
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('pt-BR')
    }

    return {
      loading,
      deleting,
      searched,
      pendingData,
      showConfirmModal,
      filters,
      loadPendingTranscriptions,
      confirmDelete,
      deletePendingTranscriptions,
      clearResults,
      formatDate
    }
  }
}
</script>

<style scoped>
.btn-danger {
  @apply bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200;
}

.btn-danger:disabled {
  @apply bg-red-400 cursor-not-allowed;
}
</style> 