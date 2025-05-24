import re
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import yt_dlp as youtube_dl
import argparse
import os
import sys

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            'compat_opts': {'ffmpeg': 'false'},  # Added compatibility options
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

def main():
    parser = argparse.ArgumentParser(description="Extrai transcrição de um vídeo do YouTube.")
    parser.add_argument("video_url", nargs='?', help="URL do vídeo do YouTube para extrair a transcrição.")

    args = parser.parse_args()

    # Solicitar URL do vídeo se não fornecido
    if not args.video_url:
        video_url = input("Por favor, insira a URL do vídeo do YouTube: ").strip()
    else:
        video_url = args.video_url.strip()

    # Validar a URL do YouTube
    if not validate_youtube_url(video_url):
        logger.error("A URL fornecida não é válida para o YouTube. Por favor, insira uma URL válida.")
        sys.exit(1)

    logger.info(f"Extraindo transcrição do vídeo: {video_url}")

    transcript, title, upload_date = get_youtube_transcript_and_title(video_url)

    if transcript and title:
        try:
            # Sanitizar o título para usar como nome de arquivo
            safe_title = sanitize_filename(title)
            output_filename = f"{safe_title}.txt"

            # Definir um diretório padrão para salvar as transcrições
            output_dir = "texts/"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Título: {title}\n")
                f.write(f"Data de Upload: {upload_date}\n\n")
                f.write("Transcrição:\n")
                f.write(transcript)
            logger.info(f"Transcrição salva em: {output_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar a transcrição no arquivo: {e}")
    else:
        logger.error("Falha ao extrair a transcrição.")

if __name__ == "__main__":
    main()