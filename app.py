import re
import requests
import logging
import streamlit as st
from bs4 import BeautifulSoup
from datetime import datetime
import yt_dlp as youtube_dl
import os
import time
import json
import random
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import tempfile
from moviepy.editor import VideoFileClip

# Configuração específica para macOS
import sys
if sys.platform == "darwin":  # macOS
    # Configurar o caminho do FFmpeg para o MoviePy
    import moviepy.config as config
    
    # Primeiro, deixar o MoviePy detectar automaticamente
    # Se não funcionar, tentar caminhos específicos
    try:
        from moviepy.config import get_setting
        current_ffmpeg = get_setting("FFMPEG_BINARY")
        if not current_ffmpeg or not os.path.exists(current_ffmpeg):
            # Tentar caminhos comuns no macOS
            possible_paths = [
                "/opt/homebrew/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "/usr/bin/ffmpeg"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config.FFMPEG_BINARY = path
                    break
    except Exception as e:
        # Se houver erro, continuar com a configuração padrão
        pass

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Limite de tamanho de arquivo para a API Groq (em bytes)
GROQ_API_MAX_FILE_SIZE = 24 * 1024 * 1024  # 24 MB (para margem de segurança)
FALLBACK_SEGMENT_MAX_FILE_SIZE = 20 * 1024 * 1024 # 20MB para segmentos muito grandes que precisam de mais processamento

# Configurações para retry
MAX_RETRIES = 5
INITIAL_BACKOFF = 2  # segundos
MAX_BACKOFF = 60  # segundos máximo de espera

# Função para formatação de timestamps para extração do YouTube
def format_timestamp(timestamp_float):
    """Format the timestamp float into HH:MM:SS"""
    try:
        total_seconds = float(timestamp_float)
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    except Exception as e:
        logger.error(f"Erro ao formatar timestamp '{timestamp_float}': {e}")
        return "00:00"

def sanitize_filename(filename):
    """Remove caracteres inválidos do nome do arquivo."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_youtube_transcript_and_title(video_url):
    """Extrai a transcrição, título e data de upload de um vídeo do YouTube usando yt_dlp."""
    try:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['pt', 'en'],
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'compat_opts': {'ffmpeg': 'false'},
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            title = info_dict.get('title', 'sem_titulo')
            upload_date_str = info_dict.get('upload_date', None)
            upload_date = None

            if upload_date_str:
                try:
                    upload_date = datetime.strptime(upload_date_str, "%Y%m%d").strftime("%d/%m/%Y")
                except ValueError:
                    upload_date = upload_date_str

            # Primeiro tenta legendas manuais
            subtitles = info_dict.get('subtitles', {})
            # Depois tenta legendas automáticas
            automatic_captions = info_dict.get('automatic_captions', {})

            logger.info(f"Legendas disponíveis: {list(subtitles.keys())}")
            logger.info(f"Legendas automáticas disponíveis: {list(automatic_captions.keys())}")

            selected_subs = None
            lang = None
            # Prioridade de idiomas
            for lang_priority in ['pt', 'pt-BR',]:
                # Tenta primeiro legendas manuais
                if lang_priority in subtitles:
                    selected_subs = subtitles[lang_priority]
                    lang = lang_priority
                    logger.info(f"Usando legenda manual em {lang_priority}")
                    break
                # Depois tenta legendas automáticas
                elif lang_priority in automatic_captions:
                    selected_subs = automatic_captions[lang_priority]
                    lang = lang_priority
                    logger.info(f"Usando legenda automática em {lang_priority}")
                    break
            else:
                # Se não encontrou nas prioridades, pega a primeira disponível
                if subtitles:
                    lang, selected_subs = next(iter(subtitles.items()))
                    logger.info(f"Usando primeira legenda manual disponível: {lang}")
                elif automatic_captions:
                    lang, selected_subs = next(iter(automatic_captions.items()))
                    logger.info(f"Usando primeira legenda automática disponível: {lang}")
                else:
                    logger.error("Nenhuma legenda disponível")
                    return None, title, upload_date

            # Tenta diferentes formatos de legenda
            for sub_format in selected_subs:
                try:
                    transcript_url = sub_format.get('url')
                    if not transcript_url:
                        continue

                    transcript_response = requests.get(transcript_url)
                    if transcript_response.status_code == 200:
                        transcript_xml = transcript_response.content
                        transcript_soup = BeautifulSoup(transcript_xml, 'xml')
                        transcript_segments = transcript_soup.find_all('text') or transcript_soup.find_all('p')

                        if transcript_segments:
                            full_transcript = []
                            for segment in transcript_segments:
                                timestamp = segment.get('start', '0')
                                text = segment.get_text().strip()
                                if text:
                                    formatted_timestamp = format_timestamp(timestamp)
                                    full_transcript.append(f"{formatted_timestamp} {text}")

                            if full_transcript:
                                return '\n'.join(full_transcript), title, upload_date

                except Exception as e:
                    logger.error(f"Erro ao processar formato de legenda: {e}")
                    continue

            logger.error("Não foi possível extrair a transcrição em nenhum formato")
            return None, title, upload_date

    except Exception as e:
        logger.error(f"Erro geral ao extrair transcrição: {e}")
        logger.exception("Detalhes do erro:")
        return None, None, None

def validate_youtube_url(url):
    """Valida se a URL fornecida é válida para o YouTube."""
    youtube_regex = (
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/live/)'
        r'[A-Za-z0-9_-]+'  # Video ID
        r'(&\S*)?$'  # Optional parameters
    )
    return re.match(youtube_regex, url) is not None

def create_download_link(text, filename):
    """Cria um link para download do texto como arquivo"""
    text_encoded = text.encode('utf-8')
    b64_text = text_encoded.decode('utf-8')
    return f'<a href="data:file/txt;charset=utf-8,{b64_text}" download="{filename}">Clique aqui para baixar</a>'

def extract_audio_from_video(video_path, output_audio_path):
    """Extrai o áudio de um arquivo de vídeo"""
    try:
        logger.info(f"Iniciando extração de áudio de: {video_path}")
        video = VideoFileClip(video_path)
        
        # Verificar se o vídeo tem áudio
        if video.audio is None:
            logger.error("O arquivo de vídeo não contém áudio")
            video.close()
            return None
            
        logger.info(f"Extraindo áudio para: {output_audio_path}")
        # Usar parâmetros mais específicos para melhor compatibilidade no macOS
        video.audio.write_audiofile(
            output_audio_path, 
            codec='libmp3lame',  # Codec específico para MP3
            verbose=False,       # Reduzir verbosidade
            logger=None         # Desabilitar logger do moviepy
        )
        
        # Fechar o vídeo para liberar recursos
        video.close()
        
        # Verificar se o arquivo foi criado com sucesso
        if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 0:
            logger.info(f"Áudio extraído com sucesso: {output_audio_path}")
            return output_audio_path
        else:
            logger.error("Arquivo de áudio não foi criado ou está vazio")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao extrair áudio do vídeo: {e}")
        logger.exception("Detalhes do erro:")
        # Tentar fechar o vídeo mesmo em caso de erro
        try:
            if 'video' in locals():
                video.close()
        except:
            pass
        return None

def check_groq_file_size(filepath):
    """Verifica o tamanho do arquivo e retorna se está dentro do limite da API Groq"""
    file_size = os.path.getsize(filepath)
    return file_size, file_size <= GROQ_API_MAX_FILE_SIZE

def reduce_audio_segment_size(input_audio_path, output_audio_path):
    """Reduz o tamanho de um segmento de áudio para ficar abaixo do limite da API Groq"""
    try:
        audio = AudioSegment.from_file(input_audio_path)
        target_bitrate = "64k"
        
        # Tentar primeiro com 64k
        audio.export(output_audio_path, format="mp3", bitrate=target_bitrate)
        file_size, is_within_limit = check_groq_file_size(output_audio_path)
        
        # Se ainda estiver grande, tentar 32k
        if not is_within_limit:
            target_bitrate = "32k"
            audio.export(output_audio_path, format="mp3", bitrate=target_bitrate)
            file_size, is_within_limit = check_groq_file_size(output_audio_path)
            
        # Se ainda estiver muito grande (improvável para segmentos curtos, mas por segurança)
        # Esta parte pode ser expandida para cortar o segmento se a compressão não for suficiente
        if not is_within_limit:
            logger.warning(f"Segmento {input_audio_path} ainda muito grande ({file_size/(1024*1024):.2f}MB) após compressão para {target_bitrate}.")
            # Aqui, poderia-se implementar uma lógica para cortar o segmento em pedaços menores ainda.
            # Por ora, retornamos None indicando falha em reduzir o suficiente.
            return None, 0
            
        return output_audio_path, file_size
        
    except Exception as e:
        print(f"Erro ao reduzir tamanho do segmento de áudio: {e}")
        return None, 0

def api_call_with_retry(endpoint, headers, files, data, max_retries=MAX_RETRIES, status_text=None, progress_bar=None):
    """
    Fazer chamada à API com sistema de retry e backoff exponencial
    """
    global MAX_RETRIES # Permitir que MAX_RETRIES seja atualizado pelas opções avançadas
    retry_count = 0
    backoff = INITIAL_BACKOFF
    
    while retry_count <= max_retries:
        try:
            # Atualizar status se fornecido
            if status_text and retry_count > 0:
                status_text.write(f"Tentativa {retry_count+1} de {max_retries+1}...")
                
            # Fazer a requisição
            response = requests.post(endpoint, headers=headers, files=files, data=data)
            
            # Se sucesso, retornar imediatamente
            if response.status_code == 200:
                return response
                
            # Se erro 5xx do servidor, tentar novamente
            if 500 <= response.status_code < 600:
                error_details = ""
                try:
                    if "text/html" in response.headers.get("Content-Type", ""):
                        error_details = f"Erro HTML do servidor: código {response.status_code}"
                    else:
                        error_json = response.json()
                        error_details = f"Erro do servidor: {json.dumps(error_json)}"
                except:
                    error_details = f"Erro do servidor: {response.text[:100]}..."
                
                if status_text:
                    status_text.write(f"Erro na API Groq (código {response.status_code}). {error_details}")
                    status_text.write(f"Aguardando {backoff:.1f} segundos antes de tentar novamente...")
                    
                if progress_bar:
                    progress_bar.progress(0.3, text=f"Aguardando retry ({retry_count+1}/{max_retries+1})...")
                    
                time.sleep(backoff)
                
                # Aumentar backoff exponencialmente com jitter (aleatoriedade)
                backoff = min(MAX_BACKOFF, backoff * 2 * (1 + random.random() * 0.1))
                retry_count += 1
                continue
                
            # Para outros erros (ex: 4xx), retornar a resposta para processamento
            return response
            
        except requests.exceptions.RequestException as e:
            if status_text:
                status_text.write(f"Erro de conexão: {str(e)}")
                status_text.write(f"Aguardando {backoff:.1f} segundos antes de tentar novamente...")
                
            if progress_bar:
                progress_bar.progress(0.3, text=f"Erro de conexão. Retry {retry_count+1}/{max_retries+1}...")
                
            time.sleep(backoff)
            
            # Aumentar backoff exponencialmente com jitter
            backoff = min(MAX_BACKOFF, backoff * 2 * (1 + random.random() * 0.1))
            retry_count += 1
            
    # Se chegou aqui, todas as tentativas falharam
    if status_text:
        status_text.write(f"Falha após {max_retries+1} tentativas. O servidor parece estar indisponível ou o arquivo é inválido.")
        
    return None

def processar_segmento_individual(segment_path, api_key, status_text, progress_bar, segment_index, total_segments, model_id):
    """Processa um único segmento de áudio"""
    progress_value = 0.1 + (0.8 * (segment_index / total_segments))
    progress_bar.progress(progress_value, text=f"Transcrevendo segmento {segment_index+1}/{total_segments}...")
    status_text.write(f"Transcrevendo segmento {segment_index+1} de {total_segments}...")

    headers = {"Authorization": f"Bearer {api_key}"}
    endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"

    with open(segment_path, "rb") as file:
        files = {"file": (os.path.basename(segment_path), file, "audio/mpeg")}
        data = {"model": model_id, "temperature": 0.0}

        response = api_call_with_retry(
            endpoint=endpoint,
            headers=headers,
            files=files,
            data=data,
            status_text=status_text,
            progress_bar=progress_bar
        )

        if response and response.status_code == 200:
            result = response.json()
            return result.get("text", "")
        else:
            error_code = response.status_code if response else "N/A"
            status_text.write(f"Falha ao transcrever segmento {segment_index+1} (Erro: {error_code})")
            return f"[ERRO NO SEGMENTO {segment_index+1} - Código {error_code}]"


def processar_arquivo_em_segmentos(arquivo_audio_original, nome_saida, model_id, progress_bar=None):
    """
    Processa o arquivo de áudio em segmentos, garantindo que cada um respeite o GROQ_API_MAX_FILE_SIZE.
    """
    status_text = st.empty()
    status_text.write("Iniciando processamento em segmentos...")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        status_text.write("Erro: GROQ_API_KEY não encontrada no arquivo .env")
        return None
    
    temp_dir = os.path.join(os.path.dirname(nome_saida), f"temp_segments_{int(time.time())}")
    os.makedirs(temp_dir, exist_ok=True)
    
    all_transcriptions = []
    
    try:
        audio = AudioSegment.from_file(arquivo_audio_original)
        total_duration_ms = len(audio)
        
        # Tentar uma duração inicial para os segmentos (ex: 5 minutos)
        # Esta duração será ajustada dinamicamente se os segmentos ficarem muito grandes
        initial_segment_duration_ms = 5 * 60 * 1000 
        
        segment_paths_para_transcrever = []
        current_pos_ms = 0
        segment_idx = 0

        status_text.write("Preparando e segmentando áudio...")
        progress_bar.progress(0.05, text="Segmentando áudio...")

        while current_pos_ms < total_duration_ms:
            segment_duration_ms = initial_segment_duration_ms
            segment_audio = None
            segment_path = os.path.join(temp_dir, f"segment_raw_{segment_idx:04d}.mp3")
            processed_segment_path = os.path.join(temp_dir, f"segment_processed_{segment_idx:04d}.mp3")
            
            # Loop para ajustar a duração do segmento se ele for muito grande após compressão
            while True:
                start_ms = current_pos_ms
                end_ms = min(current_pos_ms + segment_duration_ms, total_duration_ms)
                segment_audio = audio[start_ms:end_ms]
                
                # Exportar com compressão leve primeiro
                segment_audio.export(segment_path, format="mp3", bitrate="128k") 
                
                # Tentar reduzir se necessário
                reduced_path, file_size = reduce_audio_segment_size(segment_path, processed_segment_path)
                
                if reduced_path and file_size <= GROQ_API_MAX_FILE_SIZE:
                    segment_paths_para_transcrever.append(reduced_path)
                    current_pos_ms = end_ms
                    segment_idx += 1
                    if os.path.exists(segment_path) and segment_path != reduced_path:
                         os.unlink(segment_path) # Limpa o raw se o reduced foi diferente
                    break # Segmento OK, próximo
                elif segment_duration_ms <= 15 * 1000: # Se o segmento já é muito curto (15s) e ainda falha
                    status_text.write(f"Segmento em {start_ms/1000:.1f}s muito denso ou erro ao reduzir. Pulando.")
                    current_pos_ms = end_ms # Pula este trecho problemático
                    if os.path.exists(segment_path): os.unlink(segment_path)
                    if os.path.exists(processed_segment_path): os.unlink(processed_segment_path)
                    all_transcriptions.append(f"[ERRO/PULO: Segmento em {start_ms/1000:.1f}s muito problemático para reduzir/processar]")
                    break # Pula para o próximo ponto de início
                else:
                    # Reduz a duração do segmento e tenta novamente
                    segment_duration_ms = max(15 * 1000, int(segment_duration_ms * 0.75)) # Reduz em 25% ou mínimo de 15s
                    status_text.write(f"Reduzindo duração do segmento para {segment_duration_ms/1000:.1f}s e tentando novamente...")
                    if os.path.exists(segment_path): os.unlink(segment_path)
                    if os.path.exists(processed_segment_path): os.unlink(processed_segment_path)
            
            if current_pos_ms >= total_duration_ms:
                break
        
        total_segments_to_transcribe = len(segment_paths_para_transcrever)
        status_text.write(f"Total de {total_segments_to_transcribe} segmentos preparados para transcrição.")
        
        for i, seg_path in enumerate(segment_paths_para_transcrever):
            transcript_part = processar_segmento_individual(seg_path, api_key, status_text, progress_bar, i, total_segments_to_transcribe, model_id)
            all_transcriptions.append(transcript_part)
            time.sleep(1) # Pausa para não sobrecarregar a API
            
        complete_transcript = "\n\n".join(filter(None, all_transcriptions))
        
        with open(nome_saida, "w", encoding="utf-8") as f:
            f.write(complete_transcript)
            
        progress_bar.progress(1.0, text="Transcrição concluída!")
        status_text.write(f"Transcrição completa concluída! Arquivo salvo em: {nome_saida}")
        return nome_saida
        
    except Exception as e:
        status_text.write(f"Erro crítico durante processamento em segmentos: {str(e)}")
        logger.error(f"Erro crítico em processar_arquivo_em_segmentos: {e}", exc_info=True)
        return None
    finally:
        # Limpar diretório temporário de segmentos
        if os.path.exists(temp_dir):
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as e_clean:
                logger.error(f"Erro ao limpar diretório temporário {temp_dir}: {e_clean}")

def transcrever_audio_groq(arquivo_audio, nome_saida, model_id, progress_bar=None):
    """
    Ponto de entrada para transcrição com Groq. Decide entre envio direto ou segmentado.
    """
    status_text = st.empty()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        status_text.write("Erro: GROQ_API_KEY não encontrada no arquivo .env")
        return None

    file_size, is_within_groq_limit = check_groq_file_size(arquivo_audio)
    file_size_mb = file_size / (1024 * 1024)

    if is_within_groq_limit:
        status_text.write(f"Arquivo ({file_size_mb:.2f} MB) dentro do limite da API. Processando diretamente...")
        progress_bar.progress(0.2, text="Enviando para API Groq...")
        
        endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        try:
            with open(arquivo_audio, "rb") as file:
                files = {"file": (os.path.basename(arquivo_audio), file, "audio/mpeg")}
                data = {"model": model_id, "temperature": 0.0}
                
                response = api_call_with_retry(
                    endpoint=endpoint, headers=headers, files=files, data=data, 
                    status_text=status_text, progress_bar=progress_bar
                )
                
                if response and response.status_code == 200:
                    result = response.json()
                    transcript_text = result.get("text", "")
                    with open(nome_saida, "w", encoding="utf-8") as f:
                        f.write(transcript_text)
                    status_text.write(f"Transcrição direta concluída! Salvo em: {nome_saida}")
                    progress_bar.progress(1.0, text="Concluído!")
                    return nome_saida
                else:
                    error_code = response.status_code if response else "N/A"
                    status_text.write(f"Falha na transcrição direta (Erro: {error_code})")
                    return None
        except Exception as e:
            status_text.write(f"Erro na transcrição direta: {e}")
            logger.error(f"Erro em transcrever_audio_groq (direto): {e}", exc_info=True)
            return None
    else:
        status_text.write(f"Arquivo ({file_size_mb:.2f} MB) excede o limite da API. Iniciando processamento em segmentos...")
        return processar_arquivo_em_segmentos(arquivo_audio, nome_saida, model_id, progress_bar)

def test_video_processing():
    """Testa se o processamento de vídeo está funcionando corretamente"""
    try:
        # Verificar se FFmpeg está disponível
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False, "FFmpeg não está funcionando corretamente"
            
        # Verificar se MoviePy pode importar VideoFileClip
        from moviepy.editor import VideoFileClip
        
        # Verificar configuração do MoviePy
        from moviepy.config import get_setting
        ffmpeg_binary = get_setting("FFMPEG_BINARY")
        if not ffmpeg_binary or not os.path.exists(ffmpeg_binary):
            return False, f"MoviePy não encontrou FFmpeg: {ffmpeg_binary}"
            
        return True, "Sistema configurado corretamente"
        
    except Exception as e:
        return False, f"Erro na verificação: {str(e)}"

# Interface Streamlit
st.set_page_config(page_title="Salus Transcriptor", page_icon="🎞️", layout="wide")

# Criar abas
tab1, tab2 = st.tabs(["Extrator de Legendas do YouTube", "Transcrição com Whisper/Groq"])

# Configuração por aba
with tab1:
    st.title("Extrator de Transcrição do YouTube")
    st.write("Este aplicativo extrai a transcrição de vídeos do YouTube e permite salvá-la como arquivo de texto.")

    # Campo de entrada para a URL
    video_url = st.text_input("Insira a URL do vídeo do YouTube:", "", key="youtube_url")

    # Diretório para salvar as transcrições
    output_dir = "texts/"
    os.makedirs(output_dir, exist_ok=True)

    if st.button("Extrair Transcrição", key="extract_youtube"):
        if not video_url:
            st.error("Por favor, insira uma URL válida.")
        elif not validate_youtube_url(video_url):
            st.error("A URL fornecida não é válida para o YouTube. Por favor, insira uma URL válida.")
        else:
            with st.spinner("Extraindo transcrição..."):
                transcript, title, upload_date = get_youtube_transcript_and_title(video_url)
                
                if transcript and title:
                    st.success(f"Transcrição extraída com sucesso: {title}")
                    
                    # Exibir informações
                    st.subheader("Informações do Vídeo")
                    st.write(f"**Título:** {title}")
                    st.write(f"**Data de Upload:** {upload_date}")
                    
                    # Exibir transcrição
                    st.subheader("Transcrição")
                    st.text_area("", transcript, height=300, key="youtube_transcript")
                    
                    # Criar arquivo de download
                    safe_title = sanitize_filename(title)
                    output_filename = f"{safe_title}.txt"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    full_text = f"Título: {title}\nData de Upload: {upload_date}\n\nTranscrição:\n{transcript}"
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(full_text)
                    
                    # Botão de download
                    st.download_button(
                        label="Baixar Transcrição",
                        data=full_text,
                        file_name=output_filename,
                        mime="text/plain",
                        key="download_youtube"
                    )
                    
                    st.success(f"Transcrição também salva em: {output_path}")
                else:
                    st.error("Não foi possível extrair a transcrição deste vídeo. Verifique se ele possui legendas.")

    st.markdown("---")
    st.markdown("### Como usar:")
    st.markdown("""
    1. Cole a URL de um vídeo do YouTube no campo acima
    2. Clique em 'Extrair Transcrição'
    3. Após o processamento, você poderá visualizar e baixar a transcrição
    """)

with tab2:
    st.title("Transcrição com Whisper/Groq")
    st.write("Este aplicativo transcreve arquivos de áudio e vídeo usando o modelo Whisper via API Groq.")
    st.info("Nota: Arquivos grandes serão processados automaticamente, dividindo-os em segmentos menores (<25MB) se necessário.")
    
    # Estado do sistema Groq
    with st.expander("Status do Sistema"):
        # Verificar API Groq
        try:
            status_response = requests.get("https://api.groq.com/openai/v1/models", 
                                       headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"})
            if status_response.status_code == 200:
                st.success("✅ API Groq está online e respondendo")
            else:
                st.error(f"⚠️ API Groq está com problemas (código {status_response.status_code})")
        except:
            st.error("⚠️ Não foi possível verificar o status da API Groq")
            
        # Verificar processamento de vídeo
        video_ok, video_msg = test_video_processing()
        if video_ok:
            st.success(f"✅ Processamento de vídeo: {video_msg}")
        else:
            st.error(f"❌ Processamento de vídeo: {video_msg}")
            st.warning("O processamento de vídeos pode não funcionar corretamente. Tente apenas arquivos de áudio MP3.")
    
    # Verificar se a API key está configurada
    if not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY não encontrada. Adicione a chave em um arquivo .env na raiz do projeto.")
        st.markdown("""
        Crie um arquivo .env na raiz do projeto com o seguinte conteúdo:
        ```
        GROQ_API_KEY=sua-chave-api-aqui
        ```
        """)
    else:
        # Diretório para salvar as transcrições
        transcriptions_dir = "transcriptions/"
        os.makedirs(transcriptions_dir, exist_ok=True)
        
        # Tipo de arquivo
        file_type = st.radio(
            "Selecione o tipo de arquivo:",
            ["Áudio (MP3)", "Vídeo (MP4, AVI, MOV, etc.)"],
            key="file_type"
        )
        
        # Selecionar modelo Whisper
        model_options = {
            "Whisper Large v3 Turbo (Multilíngue, Rápido)": "whisper-large-v3-turbo",
            "Whisper Large v3 (Multilíngue, Mais Preciso)": "whisper-large-v3",
            "Distil Whisper Large v3 (Inglês, Mais Rápido)": "distil-whisper-large-v3-en"
        }
        selected_model_name = st.selectbox("Selecione o modelo Whisper:", list(model_options.keys()))
        model_id_to_use = model_options[selected_model_name]
        
        # Upload do arquivo
        if file_type == "Áudio (MP3)":
            uploaded_file = st.file_uploader("Faça upload de um arquivo de áudio", type=["mp3"], key="audio_upload")
            needs_conversion = False
        else:  # Vídeo
            uploaded_file = st.file_uploader("Faça upload de um arquivo de vídeo", 
                                           type=["mp4", "avi", "mov", "mkv", "wmv"], 
                                           key="video_upload")
            needs_conversion = True
        
        if uploaded_file is not None:
            # Calcular e mostrar tamanho do arquivo
            file_size_bytes = len(uploaded_file.getbuffer())
            file_size_mb = file_size_bytes / (1024 * 1024)
            st.info(f"Arquivo carregado: {uploaded_file.name} ({file_size_mb:.2f} MB)")
            
            # Opções avançadas
            with st.expander("Opções avançadas"):
                user_max_retries = st.slider("Número máximo de tentativas (API)", 1, 10, MAX_RETRIES, key="max_retries_slider")
                st.info("Caso ocorram erros na API Groq, o sistema tentará novamente automaticamente.")
            
            # Salvar arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_file_path = temp_file.name
            
            # Botão para iniciar a transcrição
            if st.button("Iniciar Transcrição", key="start_whisper"):
                progress_bar = st.progress(0, text="Iniciando...")
                
                # Atualizar MAX_RETRIES globalmente antes de chamar a função de transcrição
                MAX_RETRIES = user_max_retries
                
                try:
                    # Se for um vídeo, converter para MP3 primeiro
                    if needs_conversion:
                        progress_bar.progress(0.05, text="Extraindo áudio do vídeo...")
                        
                        # Criar um status text para mostrar progresso detalhado
                        status_container = st.empty()
                        status_container.info("Iniciando extração de áudio do vídeo...")
                        
                        temp_audio_path_for_conversion = os.path.join(transcriptions_dir, f"temp_audio_conv_{int(time.time())}.mp3")
                        
                        # Verificar se o arquivo de vídeo é válido
                        if not os.path.exists(temp_file_path):
                            st.error("Arquivo de vídeo temporário não encontrado.")
                            st.stop()
                            
                        file_size_check = os.path.getsize(temp_file_path)
                        if file_size_check == 0:
                            st.error("Arquivo de vídeo está vazio.")
                            st.stop()
                            
                        status_container.info(f"Processando arquivo de vídeo ({file_size_check / (1024*1024):.2f} MB)...")
                        
                        audio_path_to_transcribe = extract_audio_from_video(temp_file_path, temp_audio_path_for_conversion)
                        
                        if not audio_path_to_transcribe:
                            st.error("❌ Falha ao extrair áudio do vídeo.")
                            st.error("Possíveis causas:")
                            st.error("• O arquivo de vídeo pode estar corrompido")
                            st.error("• O vídeo pode não conter áudio")
                            st.error("• Problema com FFmpeg ou codecs")
                            st.error("• Formato de vídeo não suportado")
                            
                            # Limpar arquivos temporários
                            if os.path.exists(temp_file_path): 
                                os.unlink(temp_file_path)
                            if os.path.exists(temp_audio_path_for_conversion): 
                                os.unlink(temp_audio_path_for_conversion)
                            st.stop()
                        else:
                            # Verificar se o arquivo de áudio foi criado corretamente
                            audio_size = os.path.getsize(audio_path_to_transcribe)
                            status_container.success(f"✅ Áudio extraído com sucesso! ({audio_size / (1024*1024):.2f} MB)")
                    else:
                        audio_path_to_transcribe = temp_file_path # Usar o arquivo de áudio diretamente
                    
                    progress_bar.progress(0.1, text="Preparando para transcrição...")
                    
                    # Nome do arquivo de saída
                    nome_base = os.path.splitext(os.path.basename(uploaded_file.name))[0]
                    output_filename = f"{nome_base}_transcript.txt"
                    output_path = os.path.join(transcriptions_dir, output_filename)
                    
                    # Usar a função de transcrição Groq
                    result_path = transcrever_audio_groq(audio_path_to_transcribe, output_path, model_id_to_use, progress_bar)
                    
                    # Mostrar resultado se tudo correu bem
                    if result_path:
                        progress_bar.progress(1.0, text="Concluído!")
                        
                        # Ler o conteúdo do arquivo de transcrição
                        with open(output_path, 'r', encoding='utf-8') as f:
                            transcript_content = f.read()
                        
                        # Exibir transcrição
                        st.subheader("Transcrição")
                        st.text_area("", transcript_content, height=400, key="whisper_transcript")
                        
                        # Botão de download
                        st.download_button(
                            label="Baixar Transcrição",
                            data=transcript_content,
                            file_name=output_filename,
                            mime="text/plain",
                            key="download_whisper"
                        )
                        
                        st.success(f"Transcrição concluída e salva em: {output_path}")
                    else:
                        st.error("Erro durante a transcrição. Verifique os logs para mais detalhes ou tente novamente.")
                
                except Exception as e:
                    st.error(f"Erro ao transcrever o arquivo: {str(e)}")
                    logger.error(f"Erro principal ao transcrever: {e}", exc_info=True)
                
                finally:
                    # Remover arquivos temporários
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    if needs_conversion and 'temp_audio_path_for_conversion' in locals() and os.path.exists(temp_audio_path_for_conversion):
                        os.unlink(temp_audio_path_for_conversion)
        
        st.markdown("---")
        st.markdown("### Como usar:")
        st.markdown("""
        1. Selecione o tipo de arquivo (áudio ou vídeo)
        2. Faça upload do arquivo
        3. Clique em "Iniciar Transcrição"
        4. Após o processamento, você poderá visualizar e baixar a transcrição
        """) 