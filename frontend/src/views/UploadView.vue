<template>
  <div class="upload-container">
    <!-- Header Section -->
    <section class="upload-hero-section">
      <div class="upload-hero-content">
        <h1 class="upload-title">
          UPLOAD DE ARQUIVO
        </h1>
        <p class="upload-subtitle">
          Faça upload de seus arquivos de áudio ou vídeo para gerar transcrições automáticas com IA
        </p>
      </div>
    </section>

    <!-- Upload Section -->
    <section class="upload-main-section">
      <div class="upload-content">
        <div class="upload-card">
          <!-- File Upload -->
          <div class="upload-area-section">
            <h2 class="section-title">
              📁 Upload de Arquivo
            </h2>
            
            <!-- Drag & Drop Area -->
            <div 
              @drop="handleDrop"
              @dragover.prevent
              @dragenter.prevent
              @dragleave="isDragOver = false"
              @dragover="isDragOver = true"
              :class="[
                'drop-zone',
                isDragOver ? 'drag-over' : '',
                isUploading ? 'uploading' : ''
              ]"
              @click="$refs.fileInput.click()"
            >
              <div class="drop-content">
                <div class="drop-icon">
                  {{ isDragOver ? '📥' : '📎' }}
                </div>
                <div class="drop-text-section">
                  <p class="drop-main-text">
                    {{ isDragOver ? 'Solte o arquivo aqui' : 'Clique ou arraste arquivos aqui' }}
                  </p>
                  <p class="drop-sub-text">
                    Formatos suportados para áudio e vídeo
                  </p>
                  
                  <!-- Supported Formats -->
                  <div class="formats-grid">
                    <div class="format-card">
                      <div class="format-title">🎵 Áudio (até 500MB)</div>
                      <div class="format-list">
                        <div>MP3, WAV, FLAC, AAC</div>
                        <div>OGG, M4A, AIFF, WMA</div>
                      </div>
                    </div>
                    <div class="format-card">
                      <div class="format-title">🎬 Vídeo (até 1GB)</div>
                      <div class="format-list">
                        <div>MP4, AVI, MOV, MKV</div>
                        <div>WMV, FLV, WebM, 3GP</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Hidden File Input -->
            <input
              ref="fileInput"
              type="file"
              :accept="acceptedFileTypes"
              @change="handleFileSelect"
              class="hidden-input"
            />
          </div>

          <!-- Selected File Info -->
          <div v-if="selectedFile" class="selected-file-section">
            <div class="file-info-card">
              <div class="file-info">
                <div class="file-icon">
                  {{ getFileIcon(selectedFile.type) }}
                </div>
                <div class="file-details">
                  <div class="file-name">{{ selectedFile.name }}</div>
                  <div class="file-meta">
                    {{ formatFileSize(selectedFile.size) }} • {{ getFileType(selectedFile.type) }}
                  </div>
                </div>
              </div>
              <button
                @click="clearFile"
                class="remove-file-btn"
              >
                ❌
              </button>
            </div>
          </div>

          <!-- Upload Options -->
          <div v-if="selectedFile" class="upload-options-section">
            <div class="options-grid">
              <!-- Include Timestamps -->
              <label class="option-item">
                <input
                  v-model="includeTimestamps"
                  type="checkbox"
                  class="option-checkbox"
                />
                <span class="option-text">Incluir timestamps na transcrição</span>
              </label>

              <!-- Model Selection -->
              <div class="option-item">
                <label class="option-label">Modelo Whisper</label>
                <select
                  v-model="selectedModel"
                  class="model-select"
                >
                  <option value="whisper-large-v3-turbo">Whisper Large V3 Turbo (Recomendado)</option>
                  <option value="whisper-large-v3">Whisper Large V3</option>
                  <option value="distil-whisper-large-v3-en">Distil Whisper Large V3 (Inglês)</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Upload Button -->
          <div v-if="selectedFile" class="upload-button-section">
            <button
              @click="uploadFile"
              :disabled="isUploading"
              :class="[
                'upload-btn',
                isUploading ? 'uploading' : ''
              ]"
            >
              {{ isUploading ? 'Enviando...' : '🚀 Iniciar Transcrição' }}
            </button>
          </div>

          <!-- Upload Progress -->
          <div v-if="uploadProgress > 0" class="progress-section">
            <div class="progress-header">
              <span class="progress-text">Progresso do Upload</span>
              <span class="progress-percent">{{ uploadProgress }}%</span>
            </div>
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: uploadProgress + '%' }"
              ></div>
            </div>
          </div>
        </div>

        <!-- Recent Transcriptions -->
        <div v-if="recentTranscriptions.length > 0" class="recent-section">
          <h2 class="section-title">
            📋 Transcrições Recentes
          </h2>
          
          <div class="transcriptions-grid">
            <div
              v-for="transcription in recentTranscriptions"
              :key="transcription.id"
              class="transcription-card"
              @click="viewTranscription(transcription.id)"
            >
              <div class="card-header">
                <div class="card-icon">
                  {{ getStatusIcon(transcription.status) }}
                </div>
                <div class="card-status" :class="transcription.status">
                  {{ getStatusText(transcription.status) }}
                </div>
              </div>
              
              <div class="card-content">
                <div class="card-title">{{ transcription.original_filename || transcription.title }}</div>
                <div class="card-meta">
                  {{ formatDate(transcription.created_at) }}
                </div>
              </div>

              <div class="card-actions"> 
                <button 
                  @click.stop="confirmDeleteTranscription(transcription.id)" 
                  class="delete-transcription-btn"
                  title="Deletar transcrição"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import api from '@/services/api'

export default {
  name: 'UploadView',
  setup() {
    const router = useRouter()
    const toast = useToast()

    // Reactive data
    const selectedFile = ref(null)
    const isDragOver = ref(false)
    const isUploading = ref(false)
    const uploadProgress = ref(0)
    const includeTimestamps = ref(true)
    const selectedModel = ref('whisper-large-v3-turbo')
    const recentTranscriptions = ref([])
    let pollingInterval = null; // Variable to hold the interval ID
    const activePollIds = ref(new Set()); // Set to keep track of IDs being polled

    // Accepted file types - expanded to include all supported formats
    const acceptedFileTypes = ref([
      // Audio formats
      '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.aiff', '.wma',
      'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg', 'audio/m4a', 'audio/aiff', 'audio/x-ms-wma',
      // Video formats  
      '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg',
      'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/x-ms-wmv', 
      'video/x-flv', 'video/webm', 'video/3gpp', 'video/x-m4v', 'video/mpeg'
    ].join(','))

    // File handling methods
    const handleDrop = (e) => {
      e.preventDefault()
      isDragOver.value = false
      
      const files = e.dataTransfer.files
      if (files.length > 0) {
        handleFileSelection(files[0])
      }
    }

    const handleFileSelect = (e) => {
      const files = e.target.files
      if (files.length > 0) {
        handleFileSelection(files[0])
      }
    }

    const handleFileSelection = (file) => {
      // Validate file type
      if (!isValidFileType(file)) {
        toast.error('Formato de arquivo não suportado. Verifique os formatos aceitos.')
        return
      }

      // Validate file size
      const maxSize = isVideoFile(file) ? 1024 * 1024 * 1024 : 500 * 1024 * 1024 // 1GB for video, 500MB for audio
      if (file.size > maxSize) {
        const maxSizeText = isVideoFile(file) ? '1GB' : '500MB'
        toast.error(`Arquivo muito grande. Tamanho máximo: ${maxSizeText}`)
        return
      }

      selectedFile.value = file
      toast.success('Arquivo selecionado com sucesso!')
    }

    const clearFile = () => {
      selectedFile.value = null
      uploadProgress.value = 0
    }

    // File validation methods
    const isValidFileType = (file) => {
      const audioTypes = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg', 'audio/m4a', 'audio/aiff', 'audio/x-ms-wma']
      const videoTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/x-ms-wmv', 'video/x-flv', 'video/webm', 'video/3gpp', 'video/x-m4v', 'video/mpeg']
      
      return audioTypes.includes(file.type) || videoTypes.includes(file.type) || 
             file.name.match(/\.(mp3|wav|flac|aac|ogg|m4a|aiff|wma|mp4|avi|mov|mkv|wmv|flv|webm|3gp|m4v|mpg|mpeg)$/i)
    }

    const isVideoFile = (file) => {
      const videoTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/x-ms-wmv', 'video/x-flv', 'video/webm', 'video/3gpp', 'video/x-m4v', 'video/mpeg']
      return videoTypes.includes(file.type) || file.name.match(/\.(mp4|avi|mov|mkv|wmv|flv|webm|3gp|m4v|mpg|mpeg)$/i)
    }

    // Upload method
    const uploadFile = async () => {
      if (!selectedFile.value) return

      isUploading.value = true
      uploadProgress.value = 0

      try {
        const formData = new FormData()
        
        // Determine source type and add file
        if (isVideoFile(selectedFile.value)) {
          formData.append('source_type', 'video_upload')
          formData.append('video_file', selectedFile.value)
        } else {
          formData.append('source_type', 'audio_upload')
          formData.append('audio_file', selectedFile.value)
        }
        
        formData.append('include_timestamps', includeTimestamps.value)
        formData.append('model_used', selectedModel.value)

        await api.post('/transcriptions/create/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          }
        })

        toast.success('Upload realizado com sucesso! Processamento iniciado.')
        
        // Clear the selected file and reset progress
        clearFile();
        // Refresh the list of recent transcriptions
        await loadRecentTranscriptions(); 
        
        // No longer redirecting, user stays on UploadView
        // router.push(`/transcription/${response.data.transcription.id}`)
        
      } catch (error) {
        console.error('Upload error:', error)
        const errorMessage = error.response?.data?.error || 'Erro no upload do arquivo'
        toast.error(errorMessage)
      } finally {
        isUploading.value = false
      }
    }

    // Utility methods
    const getFileIcon = (type) => {
      if (type.startsWith('video/')) return '🎬'
      if (type.startsWith('audio/')) return '🎵'
      return '📎'
    }

    const getFileType = (type) => {
      if (type.startsWith('video/')) return 'Vídeo'
      if (type.startsWith('audio/')) return 'Áudio'
      return 'Arquivo'
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const getStatusIcon = (status) => {
      const icons = {
        pending: '⏳',
        processing: '⚙️',
        completed: '✅',
        failed: '❌'
      }
      return icons[status] || '❓'
    }

    const getStatusText = (status) => {
      const texts = {
        pending: 'Pendente',
        processing: 'Processando',
        completed: 'Concluído',
        failed: 'Falhou'
      }
      return texts[status] || 'Desconhecido'
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('pt-BR')
    }

    const viewTranscription = (id) => {
      router.push(`/transcription/${id}`)
    }

    const confirmDeleteTranscription = (id) => {
      if (confirm("Tem certeza que deseja deletar esta transcrição? Esta ação não pode ser desfeita.")) {
        deleteTranscription(id);
      }
    };

    const deleteTranscription = async (id) => {
      try {
        await api.delete(`/transcriptions/${id}/delete/`);
        recentTranscriptions.value = recentTranscriptions.value.filter(t => t.id !== id);
        toast.success("Transcrição deletada com sucesso!");
      } catch (error) {
        console.error("Error deleting transcription:", error);
        toast.error(error.response?.data?.message || error.response?.data?.error || "Erro ao deletar transcrição.");
      }
    };

    // Load recent transcriptions
    const loadRecentTranscriptions = async () => {
      try {
        const response = await api.get('/transcriptions/')
        recentTranscriptions.value = response.data.results.slice(0, 5) // Show last 5
        checkAndStartPolling(); // Check if polling needs to start/continue
      } catch (error) {
        console.error('Error loading transcriptions:', error)
      }
    }

    const fetchTranscriptionStatus = async (transcriptionId) => {
      try {
        console.log(`[Polling] Fetching status for ${transcriptionId}`);
        const response = await api.get(`/transcriptions/${transcriptionId}/status/`);
        const updatedTx = response.data;
        const index = recentTranscriptions.value.findIndex(tx => tx.id === transcriptionId);

        if (index !== -1) {
          // Only update if status has changed to avoid unnecessary re-renders
          if (recentTranscriptions.value[index].status !== updatedTx.status) {
            recentTranscriptions.value[index].status = updatedTx.status;
            recentTranscriptions.value[index].completed_at = updatedTx.completed_at; // Update completion time too
             toast.info(`Status da transcrição '${updatedTx.original_filename || updatedTx.title}' atualizado para: ${getStatusText(updatedTx.status)}`);
          }

          // If status is now completed or failed, remove from active polling
          if (updatedTx.status === 'completed' || updatedTx.status === 'failed') {
            activePollIds.value.delete(transcriptionId);
            console.log(`[Polling] Stopped polling for ${transcriptionId} (Status: ${updatedTx.status})`);
          }
        }
      } catch (error) {
        console.error(`Error fetching status for transcription ${transcriptionId}:`, error);
        activePollIds.value.delete(transcriptionId); // Stop polling on error for this ID
      }
    };

    const checkAndStartPolling = () => {
      // Clear existing interval if any to avoid multiple pollers
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
      }
      activePollIds.value.clear(); // Reset active poll IDs for current list

      recentTranscriptions.value.forEach(tx => {
        if (tx.status === 'pending' || tx.status === 'processing') {
          activePollIds.value.add(tx.id);
        }
      });

      if (activePollIds.value.size > 0) {
        console.log('[Polling] Starting polling for active transcriptions:', Array.from(activePollIds.value));
        pollingInterval = setInterval(() => {
          if (activePollIds.value.size === 0) {
            console.log('[Polling] No active transcriptions to poll. Stopping interval.');
            clearInterval(pollingInterval);
            pollingInterval = null;
            return;
          }
          console.log('[Polling] Interval tick. Checking status for:', Array.from(activePollIds.value));
          activePollIds.value.forEach(id => fetchTranscriptionStatus(id));
        }, 10000); // Poll every 10 seconds
      } else {
        console.log('[Polling] No transcriptions in pending/processing state. Polling not started.');
      }
    };

    // Lifecycle
    onMounted(() => {
      loadRecentTranscriptions()
    })

    // Clear interval when component is unmounted
    onUnmounted(() => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
        console.log('[Polling] UploadView unmounted. Polling stopped.');
      }
    });

    return {
      selectedFile,
      isDragOver,
      isUploading,
      uploadProgress,
      includeTimestamps,
      selectedModel,
      recentTranscriptions,
      acceptedFileTypes,
      handleDrop,
      handleFileSelect,
      clearFile,
      uploadFile,
      getFileIcon,
      getFileType,
      formatFileSize,
      getStatusIcon,
      getStatusText,
      formatDate,
      viewTranscription,
      confirmDeleteTranscription,
      deleteTranscription
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

.upload-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #000000 0%, #0a0a0a 25%, #1a1a2e 50%, #16213e 75%, #0f0f0f 100%);
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
  overflow-x: hidden;
}

.upload-hero-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40vh;
  padding: 80px 2rem 2rem;
  text-align: center;
  position: relative;
}

.upload-hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(0, 100, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(0, 150, 255, 0.08) 0%, transparent 50%);
  pointer-events: none;
}

.upload-hero-content {
  max-width: 800px;
  position: relative;
  z-index: 1;
}

.upload-title {
  font-size: clamp(2rem, 6vw, 3rem);
  font-weight: 800;
  margin-bottom: 1rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background: linear-gradient(45deg, #ffffff, #0080ff, #00aaff);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 3s ease-in-out infinite;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.upload-subtitle {
  font-size: clamp(1rem, 3vw, 1.2rem);
  font-weight: 500;
  opacity: 0.9;
  letter-spacing: 0.05em;
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto;
}

.upload-main-section {
  padding: 2rem;
}

.upload-content {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.upload-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 128, 255, 0.2);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  letter-spacing: 0.1em;
  color: #0080ff;
  text-transform: uppercase;
}

.upload-area-section {
  margin-bottom: 2rem;
}

.drop-zone {
  border: 2px dashed rgba(0, 128, 255, 0.3);
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-zone:hover {
  border-color: rgba(0, 128, 255, 0.5);
  background: rgba(0, 128, 255, 0.05);
}

.drop-zone.drag-over {
  border-color: #0080ff;
  background: rgba(0, 128, 255, 0.1);
  transform: scale(1.02);
}

.drop-zone.uploading {
  pointer-events: none;
  opacity: 0.7;
}

.drop-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  width: 100%;
}

.drop-icon {
  font-size: 4rem;
  opacity: 0.7;
}

.drop-text-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.drop-main-text {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
}

.drop-sub-text {
  font-size: 1rem;
  opacity: 0.7;
  margin: 0;
}

.formats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
  max-width: 500px;
}

.format-card {
  background: rgba(0, 128, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.format-title {
  font-weight: 600;
  color: #0080ff;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.format-list {
  font-size: 0.8rem;
  opacity: 0.8;
  line-height: 1.4;
}

.hidden-input {
  display: none;
}

.selected-file-section {
  margin-bottom: 2rem;
}

.file-info-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(0, 128, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid rgba(0, 128, 255, 0.3);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  font-size: 2rem;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-name {
  font-weight: 600;
  font-size: 1rem;
}

.file-meta {
  font-size: 0.9rem;
  opacity: 0.7;
}

.remove-file-btn {
  background: rgba(255, 0, 0, 0.2);
  border: 1px solid rgba(255, 0, 0, 0.3);
  border-radius: 50%;
  color: #ff4444;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.remove-file-btn:hover {
  background: rgba(255, 0, 0, 0.3);
  border-color: #ff4444;
}

.upload-options-section {
  margin-bottom: 2rem;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.option-checkbox {
  width: 18px;
  height: 18px;
  accent-color: #0080ff;
}

.option-text {
  font-size: 0.9rem;
}

.option-label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #0080ff;
}

.model-select {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 128, 255, 0.3);
  border-radius: 8px;
  padding: 0.75rem;
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.model-select:focus {
  outline: none;
  border-color: #0080ff;
  box-shadow: 0 0 10px rgba(0, 128, 255, 0.3);
}

.upload-button-section {
  text-align: center;
  margin-bottom: 2rem;
}

.upload-btn {
  background: linear-gradient(45deg, #0080ff, #0066cc);
  border: none;
  border-radius: 8px;
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 1rem 3rem;
  min-width: 280px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 
    0 0 20px rgba(0, 128, 255, 0.3),
    inset 0 0 20px rgba(255, 255, 255, 0.1);
}

.upload-btn:hover:not(.uploading) {
  transform: translateY(-2px);
  box-shadow: 
    0 0 30px rgba(0, 128, 255, 0.5),
    0 10px 30px rgba(0, 128, 255, 0.2),
    inset 0 0 20px rgba(255, 255, 255, 0.2);
}

.upload-btn.uploading {
  opacity: 0.7;
  cursor: not-allowed;
}

.progress-section {
  margin-top: 2rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.progress-text {
  font-weight: 600;
}

.progress-percent {
  color: #0080ff;
  font-weight: 700;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0080ff, #00aaff);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.recent-section {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 128, 255, 0.2);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
}

.transcriptions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.transcription-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 128, 255, 0.2);
  border-radius: 8px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.transcription-card:hover {
  border-color: rgba(0, 128, 255, 0.4);
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card-icon {
  font-size: 1.5rem;
}

.card-status {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.card-status.completed {
  background: rgba(0, 255, 0, 0.2);
  color: #00ff00;
}

.card-status.processing {
  background: rgba(255, 165, 0, 0.2);
  color: #ffa500;
}

.card-status.pending {
  background: rgba(128, 128, 128, 0.2);
  color: #808080;
}

.card-status.failed {
  background: rgba(255, 0, 0, 0.2);
  color: #ff4444;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.3;
  max-height: 2.6em;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  font-size: 0.9rem;
  opacity: 0.7;
  margin: 0;
}

.card-actions {
  margin-top: 1rem; 
  display: flex;
  justify-content: flex-end; 
}

.delete-transcription-btn {
  background: rgba(255, 68, 68, 0.1); 
  border: 1px solid rgba(255, 68, 68, 0.4); 
  color: #ff4444; 
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
  border-radius: 6px; 
  line-height: 1;
  transition: all 0.2s ease-in-out;
}

.delete-transcription-btn:hover {
  background: rgba(255, 68, 68, 0.2);
  color: #ff0000; 
  transform: scale(1.05); 
  border-color: #ff0000;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .upload-container {
    padding: 0;
  }
  
  .upload-hero-section {
    padding: 60px 1rem 1rem;
    min-height: 30vh;
  }
  
  .upload-main-section {
    padding: 1rem;
  }
  
  .upload-card {
    padding: 1.5rem;
  }
  
  .drop-zone {
    padding: 2rem 1rem;
    min-height: 200px;
  }
  
  .formats-grid {
    grid-template-columns: 1fr;
  }
  
  .options-grid {
    grid-template-columns: 1fr;
  }
  
  .transcriptions-grid {
    grid-template-columns: 1fr;
  }
}
</style>