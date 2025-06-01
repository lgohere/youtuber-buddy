import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue') // Assuming you have a HomeView.vue
  },
  {
    path: '/upload',
    name: 'upload',
    component: () => import('@/views/UploadView.vue')
  },
  {
    path: '/transcription/:id',
    name: 'transcription',
    component: () => import('@/views/TranscriptionView.vue')
  },
  {
    path: '/content-generation',
    name: 'content-generation',
    component: () => import('@/views/ContentGenerationView.vue')
  },
  {
    path: '/transcription-management',
    name: 'transcription-management',
    component: () => import('@/views/TranscriptionManagementView.vue')
  },
  // Add other routes here as needed
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router 