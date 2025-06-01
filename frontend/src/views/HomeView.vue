<template>
  <div class="home-container">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          YOUTUBER BUDDY
        </h1>
        <p class="hero-subtitle">
          Transforme seus vídeos em conteúdo otimizado com IA avançada
        </p>
        <div class="cta-section">
          <button @click="navigateToUpload" class="cta-button">
            <span class="button-text">COMEÇAR AGORA</span>
            <span class="button-arrow">→</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Features Grid -->
    <section class="features-section">
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">🎯</div>
          <h3 class="feature-title">TÍTULOS INTELIGENTES</h3>
          <p class="feature-description">
            Gere títulos otimizados para SEO que aumentam visualizações e engajamento
          </p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">📝</div>
          <h3 class="feature-title">DESCRIÇÕES AUTOMÁTICAS</h3>
          <p class="feature-description">
            Descrições completas e envolventes geradas automaticamente do seu conteúdo
          </p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">⏱️</div>
          <h3 class="feature-title">CAPÍTULOS PRECISOS</h3>
          <p class="feature-description">
            Timestamps automáticos para melhorar a navegação e retenção de audiência
          </p>
        </div>
        
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'HomeView',
  mounted() {
    console.log('HomeView mounted')
  },
  methods: {
    navigateToUpload() {
      console.log('Navigating to upload...')
      this.$router.push('/upload')
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #000000 0%, #0a0a0a 25%, #1a1a2e 50%, #16213e 75%, #0f0f0f 100%);
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
  overflow-x: hidden;
}

.hero-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
  padding: 80px 2rem 4rem;
  text-align: center;
  position: relative;
}

.hero-section::before {
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

.hero-content {
  max-width: 800px;
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: clamp(2.5rem, 8vw, 4.5rem);
  font-weight: 800;
  margin-bottom: 1.5rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background: linear-gradient(45deg, #ffffff, #0080ff, #00aaff);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 3s ease-in-out infinite;
  text-shadow: 0 0 30px rgba(0, 128, 255, 0.3);
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.hero-subtitle {
  font-size: clamp(1rem, 3vw, 1.3rem);
  font-weight: 500;
  margin-bottom: 3rem;
  opacity: 0.9;
  letter-spacing: 0.05em;
  line-height: 1.6;
}

.cta-section {
  margin-top: 3rem;
}

.cta-button {
  background: linear-gradient(45deg, #0080ff, #0066cc);
  border: 2px solid transparent;
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  box-shadow: 
    0 0 20px rgba(0, 128, 255, 0.3),
    inset 0 0 20px rgba(255, 255, 255, 0.1);
}

.cta-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.cta-button:hover::before {
  left: 100%;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 0 30px rgba(0, 128, 255, 0.5),
    0 10px 30px rgba(0, 128, 255, 0.2),
    inset 0 0 20px rgba(255, 255, 255, 0.2);
}

.button-text {
  position: relative;
  z-index: 2;
}

.button-arrow {
  position: relative;
  z-index: 2;
  font-size: 1.2rem;
  transition: transform 0.3s ease;
}

.cta-button:hover .button-arrow {
  transform: translateX(4px);
}

.features-section {
  padding: 4rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 128, 255, 0.2);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #0080ff, #00aaff);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.feature-card:hover {
  transform: translateY(-8px);
  border-color: rgba(0, 128, 255, 0.4);
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.3),
    0 0 20px rgba(0, 128, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1.5rem;
  filter: grayscale(1) brightness(1.5);
  transition: filter 0.3s ease;
}

.feature-card:hover .feature-icon {
  filter: grayscale(0) brightness(1);
}

.feature-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 1rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #0080ff;
}

.feature-description {
  font-size: 0.9rem;
  font-weight: 400;
  line-height: 1.6;
  opacity: 0.8;
  letter-spacing: 0.02em;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .hero-section {
    padding: 60px 1rem 3rem;
    min-height: 60vh;
  }
  
  .features-section {
    padding: 3rem 1rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .feature-card {
    padding: 1.5rem;
  }
  
  .cta-button {
    min-width: 240px;
    padding: 0.9rem 2rem;
    font-size: 0.9rem;
  }
}
</style> 