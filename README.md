# Salus Transcriptor

Um aplicativo Streamlit para extração de transcrições de vídeos do YouTube e transcrição de áudios/vídeos usando Whisper via API Groq.

## Funcionalidades

### 1. Extrator de Legendas do YouTube
- Extrai legendas/transcrições de vídeos do YouTube
- Salva as transcrições como arquivos de texto
- Suporta principalmente legendas em português, com fallback para outros idiomas

### 2. Transcrição com Whisper/Groq
- Transcreve arquivos de áudio MP3 usando o modelo Whisper via API Groq
- Transcreve arquivos de vídeo (MP4, AVI, MOV, etc.), extraindo automaticamente o áudio
- Processamento automático em segmentos para arquivos grandes
- Sistema de retry automático para maior confiabilidade

## Requisitos

- Python 3.7+
- Bibliotecas listadas no arquivo `requirements.txt`
- Chave de API do Groq (para a funcionalidade de transcrição Whisper)
- FFmpeg instalado no sistema (para processamento de áudio/vídeo)

## Instalação

### Instalação Automática (macOS)

1. Execute o script de setup:
```bash
chmod +x setup_macos.command
./setup_macos.command
```

### Instalação Manual

1. Clone este repositório ou baixe os arquivos
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Instale o FFmpeg (necessário para processamento de áudio/vídeo):
   - **Windows**: Baixe do site oficial e adicione ao PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` ou equivalente para sua distribuição

4. Para usar a transcrição via Groq, crie um arquivo `.env` na raiz do projeto com:

```
GROQ_API_KEY=sua-chave-api-aqui
```

## Como executar o aplicativo

### Método 1: Script de execução (macOS)
```bash
chmod +x run_salus.command
./run_salus.command
```

### Método 2: Comando direto
```bash
streamlit run app.py
```

### Método 3: Script bash
```bash
bash run_app.sh
```

Isso iniciará o servidor Streamlit e abrirá automaticamente o aplicativo no seu navegador padrão. Se não abrir automaticamente, acesse `http://localhost:8501` no seu navegador.

## Resolução de Problemas

### Problemas com Processamento de Vídeo no macOS

Se você está tendo problemas para transcrever arquivos MP4, siga estes passos:

1. **Verifique o status do sistema**: Na aba "Transcrição com Whisper/Groq", expanda "Status do Sistema" para ver se há problemas.

2. **Execute o teste de configuração**:
```bash
python test_video.py
```

3. **Problemas comuns e soluções**:

   - **FFmpeg não encontrado**: 
     ```bash
     brew install ffmpeg
     ```
   
   - **Erro de codec**: Alguns vídeos podem usar codecs não suportados. Tente converter o vídeo primeiro:
     ```bash
     ffmpeg -i seu_video.mp4 -c:v libx264 -c:a aac video_convertido.mp4
     ```
   
   - **Arquivo muito grande**: O sistema automaticamente divide arquivos grandes em segmentos menores.
   
   - **Vídeo sem áudio**: Verifique se o arquivo de vídeo realmente contém áudio.

4. **Alternativa**: Se o processamento de vídeo não funcionar, extraia o áudio manualmente:
```bash
ffmpeg -i seu_video.mp4 -vn -acodec libmp3lame audio.mp3
```
Depois use o arquivo MP3 na opção "Áudio (MP3)".

### Outros Problemas

- **API Groq indisponível**: Verifique sua chave API e conexão com internet
- **Erro de dependências**: Reinstale as dependências com `pip install -r requirements.txt`
- **Problemas de permissão**: No macOS, pode ser necessário dar permissão para executar scripts

## Diretórios de Saída

- As transcrições do YouTube são salvas na pasta `texts/`
- As transcrições Whisper são salvas na pasta `transcriptions/`

## Como usar

### Extração de Legendas do YouTube
1. Cole a URL de um vídeo do YouTube no campo de entrada
2. Clique no botão "Extrair Transcrição"
3. Após o processamento, você poderá visualizar a transcrição e baixá-la como arquivo .txt

### Transcrição de Áudio/Vídeo
1. Selecione o tipo de arquivo (áudio ou vídeo)
2. Escolha o modelo Whisper desejado
3. Faça upload do arquivo
4. Clique em "Iniciar Transcrição"
5. Após o processamento, você poderá visualizar e baixar a transcrição

## Observações

- O aplicativo extrai preferencialmente legendas em português (pt ou pt-BR)
- Caso não encontre legendas em português, usará o primeiro idioma disponível
- As transcrições são salvas automaticamente além de estarem disponíveis para download
- Arquivos grandes são processados automaticamente em segmentos menores
- O sistema inclui retry automático para maior confiabilidade 