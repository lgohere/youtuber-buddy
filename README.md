# 🎬 Your Social Media - Plataforma de Geração de Conteúdo para YouTube

Uma aplicação web moderna para extração de transcrições de vídeos do YouTube, transcrição de áudios/vídeos usando Whisper via API Groq, e **geração inteligente de conteúdo para YouTube usando IA**.

## 🏗️ Arquitetura

- **Backend**: Django REST Framework + PostgreSQL + Redis + Celery
- **Frontend**: Vue.js 3 + TypeScript + Tailwind CSS
- **IA**: Google Generative AI + Groq Whisper API
- **Deploy**: Docker + Coolify

## ✨ Funcionalidades

### 🎯 Extração de Conteúdo YouTube
- ✅ Extração automática de legendas em múltiplos idiomas
- ✅ Detecção inteligente do melhor idioma disponível
- ✅ Fallback para transcrição via Whisper se necessário

### 🎤 Transcrição de Áudio/Vídeo
- ✅ Upload de arquivos de áudio/vídeo (MP3, MP4, WAV, etc.)
- ✅ Transcrição via Groq Whisper API
- ✅ Segmentação automática para arquivos grandes
- ✅ Timestamps precisos

### 🤖 Geração de Conteúdo IA
- ✅ **10 tipos de títulos**: Viral, SEO, Educativo, Questionador, etc.
- ✅ **6 tipos de descrições**: Analítica, Promocional, Educativa, etc.
- ✅ **Capítulos automáticos** com timestamps
- ✅ **Suporte multilíngue**: PT, EN, ES, FR, IT, DE

### 👥 Sistema de Usuários
- ✅ Autenticação JWT
- ✅ Planos Free/Premium
- ✅ Controle de uso e limites
- ✅ Histórico de transcrições

## 🚀 Deploy com Coolify

### Pré-requisitos
- Servidor VPS com Docker
- Coolify instalado
- Domínio configurado (`texts.com.br`)
- API Keys (Groq + Google AI)

### Configuração Rápida

1. **No Coolify Dashboard**:
   - New Resource → Docker Compose
   - Cole o conteúdo do `docker-compose.yml`

2. **Variáveis de Ambiente**:
```env
   SECRET_KEY=sua-chave-secreta-aqui
GROQ_API_KEY=sua-chave-groq-aqui
GOOGLE_API_KEY=sua-chave-google-ai-aqui
   DB_PASSWORD=senha-do-banco-aqui
   ```

3. **Configurar Domínio**: `texts.com.br`

4. **Deploy!**

📖 **Guia completo**: [COOLIFY-DEPLOY.md](COOLIFY-DEPLOY.md)

## 🛠️ Desenvolvimento Local

### 1. Clonar o Repositório
```bash
git clone <repository-url>
cd your-social-media
```

### 2. Configurar Variáveis de Ambiente
```bash
cp env.example .env
# Edite o .env com suas API keys
```

### 3. Executar com Docker
```bash
docker-compose up --build
```

### 4. Acessar a Aplicação
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Admin Django**: http://localhost:8000/api/admin

## 📁 Estrutura do Projeto

```
your-social-media/
├── backend/                    # Django REST API
│   ├── apps/
│   │   ├── users/             # Autenticação e usuários
│   │   ├── transcriptions/    # Transcrições e uploads
│   │   ├── content_generation/# Geração de conteúdo IA
│   │   └── youtube_extractor/ # Extração YouTube
│   ├── your_social_media/     # Configurações Django
│   ├── requirements.txt       # Dependências Python
│   └── Dockerfile            # Container Django
├── frontend/                  # Vue.js SPA
│   ├── src/
│   │   ├── components/       # Componentes Vue
│   │   ├── views/           # Páginas
│   │   ├── stores/          # Pinia stores
│   │   └── services/        # API services
│   ├── package.json         # Dependências Node.js
│   ├── Dockerfile          # Container Vue.js
│   └── nginx.conf          # Configuração Nginx
├── docker-compose.yml      # Orquestração containers
├── env.example            # Exemplo variáveis ambiente
└── COOLIFY-DEPLOY.md     # Guia deploy produção
```

## 🔑 API Keys Necessárias

### Groq API (Transcrição Whisper)
1. Acesse: https://console.groq.com
2. Crie uma conta e gere uma API key
3. Adicione em `GROQ_API_KEY`

### Google AI (Geração de Conteúdo)
1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma API key para Generative AI
3. Adicione em `GOOGLE_API_KEY`

## 🎯 Tipos de Conteúdo Gerado

### 📝 Títulos (10 tipos)
- **Viral**: Títulos chamativos para máximo engajamento
- **SEO**: Otimizados para busca no YouTube
- **Educativo**: Focados em aprendizado
- **Questionador**: Que despertam curiosidade
- **Numérico**: Com listas e números
- **Urgente**: Com senso de urgência
- **Benefício**: Destacando vantagens
- **Problema/Solução**: Identificando dores
- **Comparativo**: Comparações e vs.
- **Tutorial**: Para conteúdo educativo

### 📄 Descrições (6 tipos)
- **Analítica**: Análise detalhada do conteúdo
- **Promocional**: Focada em conversão
- **Educativa**: Para ensino e aprendizado
- **Storytelling**: Narrativa envolvente
- **Técnica**: Detalhes técnicos
- **Casual**: Tom descontraído

### 📚 Capítulos
- Divisão automática em seções lógicas
- Timestamps precisos
- Títulos descritivos
- Máximo configurável (padrão: 6)

## 🌍 Suporte Multilíngue

A aplicação detecta automaticamente o idioma e gera conteúdo em:
- 🇧🇷 Português (PT)
- 🇺🇸 Inglês (EN)
- 🇪🇸 Espanhol (ES)
- 🇫🇷 Francês (FR)
- 🇮🇹 Italiano (IT)
- 🇩🇪 Alemão (DE)

## 💎 Planos de Uso

### 🆓 Free
- 5 transcrições/mês
- Geração básica de conteúdo
- Suporte a arquivos até 25MB

### 💰 Premium
- Transcrições ilimitadas
- Todos os tipos de conteúdo
- Arquivos até 200MB
- Suporte prioritário

## 🔧 Tecnologias

### Backend
- **Django 4.2** - Framework web
- **Django REST Framework** - API REST
- **PostgreSQL** - Banco de dados
- **Redis** - Cache e filas
- **Celery** - Processamento assíncrono
- **Gunicorn** - Servidor WSGI

### Frontend
- **Vue.js 3** - Framework reativo
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização
- **Pinia** - Gerenciamento de estado
- **Vite** - Build tool

### IA & APIs
- **Google Generative AI** - Geração de conteúdo
- **Groq Whisper** - Transcrição de áudio
- **YouTube Data API** - Extração de legendas

### DevOps
- **Docker** - Containerização
- **Nginx** - Proxy reverso
- **Coolify** - Deploy e gerenciamento

## 📊 Monitoramento

### Health Checks
- Frontend: `/health`
- Backend: `/api/health/`

### Logs
- Acesse via Coolify Dashboard
- Logs por serviço individual
- Monitoramento em tempo real

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- 📧 Email: suporte@texts.com.br
- 📖 Documentação: [COOLIFY-DEPLOY.md](COOLIFY-DEPLOY.md)
- 🐛 Issues: GitHub Issues

---

🚀 **Transforme suas transcrições em conteúdo viral para YouTube!** 