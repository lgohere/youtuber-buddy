import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import router from './router/index.js'
import App from './App.vue'

// Styles
import './style.css'
import 'vue-toastification/dist/index.css'

console.log('Starting app initialization...')

// Create app
const app = createApp(App)

// Use plugins
app.use(createPinia())
app.use(router)
app.use(Toast, {
  position: 'top-right',
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false,
})

console.log('Mounting app...')

// Mount app
app.mount('#app')

console.log('App mounted successfully!')

// Auth store initialization removed - no authentication required 