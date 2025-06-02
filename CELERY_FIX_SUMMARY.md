# 🔧 Correção do Problema de Variáveis de Ambiente no Celery

## 🎯 Problema Identificado

O **Celery** não estava conseguindo acessar as variáveis de ambiente do Coolify, especificamente a `GROQ_API_KEY`, causando erros de autenticação "Invalid API Key" mesmo com a chave correta.

## 🔍 Root Cause

- O Celery roda em um processo separado do Django
- Em ambientes containerizados (Docker/Coolify), o Celery pode não herdar as variáveis de ambiente corretamente
- As variáveis estavam disponíveis no processo principal do Django, mas não nos workers do Celery

## 🛠️ Soluções Implementadas

### 1. **Configuração Melhorada do Celery** (`backend/your_social_media/celery.py`)
- ✅ Adicionado `django.setup()` para garantir carregamento das configurações
- ✅ Adicionado logging de variáveis de ambiente no startup do Celery
- ✅ Criado task de debug `debug_env_vars` para testar ambiente do worker

### 2. **Loader de Ambiente para Celery** (`backend/celery_env_loader.py`)
- ✅ Módulo que força o carregamento das variáveis de ambiente
- ✅ Verificação e logging de todas as variáveis necessárias
- ✅ Importado automaticamente pelo Celery

### 3. **Script de Verificação** (`backend/load_env_for_celery.py`)
- ✅ Script standalone para verificar e exportar variáveis
- ✅ Executado antes de iniciar workers do Celery
- ✅ Falha explicitamente se variáveis estão faltando

### 4. **Docker Entrypoint Melhorado** (`backend/docker-entrypoint.sh`)
- ✅ Exportação explícita de todas as variáveis de ambiente
- ✅ Uso do comando `env` para garantir que variáveis sejam passadas
- ✅ Verificação de ambiente antes de iniciar Celery
- ✅ Logging detalhado do status das variáveis

### 5. **Comandos de Teste** 
- ✅ `test_env_vars` - Testa variáveis no Django
- ✅ `test_groq_direct` - Testa API Groq diretamente
- ✅ `test_groq_library` - Testa usando biblioteca oficial
- ✅ `test_celery_env` - Testa variáveis no Celery worker

## 🚀 Como Testar

### 1. **Deploy no Coolify**
```bash
# As mudanças serão aplicadas automaticamente no próximo deploy
# Verifique os logs do container backend para ver os testes
```

### 2. **Verificar Logs**
```bash
# Procure por estas mensagens nos logs:
# ✅ GROQ_API_KEY exported (length: 56)
# ✅ Environment loader passed!
# ✅ All environment variables are available in Celery worker!
```

### 3. **Testar Transcrição**
```bash
# Faça upload de um arquivo de áudio
# Verifique se a transcrição funciona sem erro de API key
```

## 🔧 Variáveis de Ambiente Necessárias

Certifique-se de que estas variáveis estão configuradas no Coolify:

```env
GROQ_API_KEY=sua-chave-groq-aqui
GOOGLE_API_KEY=sua-chave-google-aqui
OPENAI_API_KEY=sua-chave-openai-aqui
SECRET_KEY=sua-chave-secreta-django
POSTGRES_DB=nome-do-banco
POSTGRES_USER=usuario-postgres
POSTGRES_PASSWORD=senha-postgres
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
```

## 🎯 Resultado Esperado

Após essas mudanças:
- ✅ Celery workers terão acesso a todas as variáveis de ambiente
- ✅ API do Groq funcionará corretamente nas transcrições
- ✅ Logs mostrarão claramente o status das variáveis
- ✅ Erros de "Invalid API Key" serão eliminados

## 🔍 Troubleshooting

Se ainda houver problemas:

1. **Verifique os logs do container backend**
2. **Procure por mensagens de erro do environment loader**
3. **Execute o comando de teste**: `python manage.py test_celery_env`
4. **Verifique se todas as variáveis estão configuradas no Coolify**

## 📝 Próximos Passos

1. **Deploy das mudanças**
2. **Verificar logs de startup**
3. **Testar upload e transcrição de arquivo**
4. **Confirmar que Groq API funciona** 