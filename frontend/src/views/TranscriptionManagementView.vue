<template>
  <div class="transcription-management-view">
    <div class="container mx-auto px-4 py-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">
          <i class="fas fa-cogs mr-3"></i>
          Gerenciamento de Transcrições
        </h1>
        <p class="text-gray-600">
          Gerencie suas transcrições, visualize estatísticas e limpe dados antigos
        </p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
        <div class="card">
          <div class="card-body text-center">
            <i class="fas fa-list-alt text-blue-500 text-2xl mb-2"></i>
            <div class="text-2xl font-bold text-gray-800">{{ stats.total_transcriptions || 0 }}</div>
            <div class="text-sm text-gray-600">Total</div>
          </div>
        </div>

        <div class="card">
          <div class="card-body text-center">
            <i class="fas fa-check-circle text-green-500 text-2xl mb-2"></i>
            <div class="text-2xl font-bold text-gray-800">{{ stats.completed_transcriptions || 0 }}</div>
            <div class="text-sm text-gray-600">Concluídas</div>
          </div>
        </div>

        <div class="card">
          <div class="card-body text-center">
            <i class="fas fa-spinner text-blue-500 text-2xl mb-2"></i>
            <div class="text-2xl font-bold text-gray-800">{{ stats.processing_transcriptions || 0 }}</div>
            <div class="text-sm text-gray-600">Processando</div>
          </div>
        </div>

        <div class="card">
          <div class="card-body text-center">
            <i class="fas fa-clock text-yellow-500 text-2xl mb-2"></i>
            <div class="text-2xl font-bold text-gray-800">{{ stats.pending_transcriptions || 0 }}</div>
            <div class="text-sm text-gray-600">Pendentes</div>
          </div>
        </div>

        <div class="card">
          <div class="card-body text-center">
            <i class="fas fa-exclamation-triangle text-red-500 text-2xl mb-2"></i>
            <div class="text-2xl font-bold text-gray-800">{{ stats.failed_transcriptions || 0 }}</div>
            <div class="text-sm text-gray-600">Falharam</div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="mb-6">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex space-x-8">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'py-2 px-1 border-b-2 font-medium text-sm',
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              <i :class="tab.icon + ' mr-2'"></i>
              {{ tab.name }}
            </button>
          </nav>
        </div>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Pending Transcriptions Tab -->
        <div v-if="activeTab === 'pending'">
          <PendingTranscriptionsManager @deleted="refreshStats" />
        </div>

        <!-- All Transcriptions Tab -->
        <div v-if="activeTab === 'all'">
          <div class="card">
            <div class="card-header">
              <h3 class="text-lg font-semibold text-gray-800">
                <i class="fas fa-list mr-2"></i>
                Todas as Transcrições
              </h3>
            </div>
            <div class="card-body">
              <TranscriptionsList />
            </div>
          </div>
        </div>

        <!-- System Status Tab -->
        <div v-if="activeTab === 'system'">
          <div class="card">
            <div class="card-header">
              <h3 class="text-lg font-semibold text-gray-800">
                <i class="fas fa-server mr-2"></i>
                Status do Sistema
              </h3>
            </div>
            <div class="card-body">
              <SystemStatus />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useToast } from 'vue-toastification'
import PendingTranscriptionsManager from '@/components/PendingTranscriptionsManager.vue'

export default {
  name: 'TranscriptionManagementView',
  components: {
    PendingTranscriptionsManager
  },
  setup() {
    const toast = useToast()
    const activeTab = ref('pending')
    const stats = ref({})
    const loading = ref(false)

    const tabs = [
      {
        id: 'pending',
        name: 'Transcrições Pendentes',
        icon: 'fas fa-clock'
      },
      {
        id: 'all',
        name: 'Todas as Transcrições',
        icon: 'fas fa-list'
      },
      {
        id: 'system',
        name: 'Status do Sistema',
        icon: 'fas fa-server'
      }
    ]

    const loadStats = async () => {
      try {
        const response = await api.get('/transcriptions/stats/')
        stats.value = response.data
      } catch (error) {
        console.error('Erro ao carregar estatísticas:', error)
        toast.error('Erro ao carregar estatísticas')
      }
    }

    const refreshStats = () => {
      loadStats()
    }

    onMounted(() => {
      loadStats()
    })

    return {
      activeTab,
      tabs,
      stats,
      loading,
      refreshStats
    }
  }
}
</script>

<style scoped>
.container {
  max-width: 1200px;
}
</style> 