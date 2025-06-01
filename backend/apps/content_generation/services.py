"""
Services for content generation using Google Generative AI.
Migrated from original agents/content_generator.py
"""
import os
import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone
import google.generativeai as genai
from .models import ContentGeneration, GeneratedTitle, GeneratedChapter

logger = logging.getLogger(__name__)


@dataclass
class ContentResult:
    """Resultado da geração de conteúdo"""
    status: str
    content: str
    agent_used: str
    error: Optional[str] = None


class ContentGenerationService:
    """
    Service for generating YouTube content using Google Generative AI
    """
    
    def __init__(self):
        # Configure Google Generative AI
        api_key = settings.GOOGLE_API_KEY
        logger.info(f"[ContentGenerationService] Initializing. Attempting to load GOOGLE_API_KEY.")
        
        # Mask most of the API key for security in logs
        api_key_display = "Not set or empty"
        if api_key: # Check if api_key is not None and not empty
            if len(api_key) > 7: # Standard Google API keys are longer
                api_key_display = f"starts with '{api_key[:4]}', ends with '{api_key[-3:]}', length {len(api_key)}"
            elif len(api_key) > 0:
                api_key_display = f"set, length {len(api_key)} (too short to be a typical Google API key, value: '{api_key[:4]}...')"
            else: # Empty string
                api_key_display = "set, but is an empty string"

        logger.info(f"[ContentGenerationService] Value of settings.GOOGLE_API_KEY: {api_key_display}")

        if api_key: # Check if api_key is not None and not empty string
            logger.info(f"[ContentGenerationService] GOOGLE_API_KEY seems present. Attempting to configure genai.")
            try:
                genai.configure(api_key=api_key) # Use the original api_key variable
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("[ContentGenerationService] Gemini Model configured successfully with API key from Django settings.")
            except Exception as e:
                logger.error(f"[ContentGenerationService] Error configuring genai with API key from Django settings: {e}")
                self.model = None
        else:
            logger.error(f"[ContentGenerationService] GOOGLE_API_KEY is missing or empty in Django settings. Cannot configure Gemini.")
            self.model = None
    
    def detect_transcription_language(self, transcription: str) -> str:
        """Detect language of transcription text using OpenAI GPT-4o-mini."""
        try:
            # Check if OpenAI API key is available
            openai_api_key = settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else None
            if not openai_api_key:
                logger.warning("OpenAI API key não encontrada, usando português por padrão")
                return "pt|Português (Brasil)"
            
            # Remove timestamps for better language detection
            text_without_timestamps = re.sub(r'^\d{1,2}:\d{2}(?::\d{2})?\s+', '', transcription, flags=re.MULTILINE)
            
            # Get first few lines for analysis
            lines = [line.strip() for line in text_without_timestamps.split('\n') if line.strip()]
            sample_text = ' '.join(lines[:10])  # First 10 lines
            
            logger.info(f"[AGENTE 1 - OpenAI] Detectando idioma do texto: {sample_text[:100]}...")
            
            if len(sample_text) < 50:
                logger.info("[AGENTE 1 - OpenAI] Texto muito curto, retornando português por padrão")
                return "pt|Português (Brasil)"
            
            # Import OpenAI here to avoid import errors if not installed
            import openai
            
            # Configure OpenAI client
            client = openai.OpenAI(api_key=openai_api_key)
            
            # Simple prompt for language detection
            prompt = f"""
Identifique o idioma deste texto. Analise cuidadosamente as palavras.

Texto: {sample_text[:300]}

EXEMPLOS:
- Se contém "Olá pessoal", "vamos falar", "bem-vindos", "não", "então", "também" = Português (Brasil)
- Se contém "Hello", "everyone", "let's", "the", "and", "very" = English  
- Se contém "Hola", "todos", "vamos a", "también", "muy" = Español

Responda APENAS no formato: pt|Português (Brasil) OU en|English OU es|Español"""

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um especialista em detecção de idiomas. Seja preciso e responda apenas no formato solicitado."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0
            )
            
            detected = response.choices[0].message.content.strip()
            logger.info(f"[AGENTE 1 - OpenAI] Idioma detectado: '{detected}'")
            
            # Validate response format
            if '|' in detected and len(detected.split('|')) == 2:
                code, name = detected.split('|')
                code = code.strip().lower()
                name = name.strip()
                
                # Validate code
                valid_codes = ['pt', 'en', 'es']
                if code in valid_codes:
                    logger.info(f"[AGENTE 1 - OpenAI] ✅ Idioma validado: {code} - {name}")
                    return f"{code}|{name}"
            
            # Fallback to Portuguese
            logger.warning(f"[AGENTE 1 - OpenAI] ⚠️ Resposta inválida: '{detected}', usando português por padrão")
            return "pt|Português (Brasil)"
            
        except Exception as e:
            logger.error(f"[AGENTE 1 - OpenAI] ❌ Erro na detecção de idioma: {e}")
            return "pt|Português (Brasil)"
    
    def _generate_content_sync(self, agent_name: str, prompt: str, lang_code: str = 'pt') -> ContentResult:
        """Generate content using Google Generative AI (synchronous) with detected language."""
        try:
            if not self.model:
                return ContentResult(
                    status="error",
                    content="",
                    agent_used=agent_name,
                    error="Google API não configurada"
                )
            
            logger.info(f"[AGENTE 2 - Gemini] Gerando conteúdo em IDIOMA: {lang_code}")
            
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            
            logger.info(f"[AGENTE 2 - Gemini] ✅ Conteúdo gerado com sucesso")
            
            return ContentResult(
                status="success",
                content=response.text,
                agent_used=agent_name
            )
        except Exception as e:
            # Log the full traceback for detailed error information
            logger.error(f"[AGENTE 2 - Gemini] ❌ Erro detalhado ao gerar conteúdo com {agent_name} (Idioma: {lang_code}):", exc_info=True)
            
            error_message = str(e)
            # Try to get more specific error from Google API if possible
            if hasattr(e, 'args') and e.args:
                if isinstance(e.args[0], str) and 'API key not valid' in e.args[0]:
                    error_message = "API key do Google inválida ou não configurada corretamente."
                elif isinstance(e.args[0], str):
                    error_message = e.args[0]

            return ContentResult(
                status="error",
                content="",
                agent_used=agent_name,
                error=error_message # Ensure error is always a string
            )
    
    def generate_titles(self, transcription_text: str, title_types: Optional[List[str]] = None, use_markdown: bool = False, lang_code: str = 'pt', lang_name: str = 'Português (Brasil)') -> ContentResult:
        """Generate optimized YouTube titles using multi-agent system."""
        # title_types logic can remain as is, or be simplified if UI drives the specific list
        # For now, assuming title_types are passed if specific ones are desired (e.g. from ContentGeneration.title_types)
        # or defaults are applied if None.
        
        # AGENTE 1: Language detection is now done before calling this, lang_code and lang_name are passed in.
        # lang_info = self.detect_transcription_language(transcription_text)
        # lang_code, lang_name = lang_info.split('|')
        
        logger.info(f"[SISTEMA MULTI-AGENTES - TÍTULOS] Gerando títulos em {lang_name} ({lang_code}). Markdown: {use_markdown}")
        
        language_instruction = f"""
🚨 GERE TODO O CONTEÚDO EXCLUSIVAMENTE EM {lang_name.upper()} ({lang_code.upper()})
🚨 NÃO misture idiomas na resposta
🚨 Use as palavras e estruturas típicas do {lang_name.upper()}

CONFIRMAÇÃO DE IDIOMA DETECTADO:
- Código: {lang_code}
- Idioma: {lang_name}
- Responsável pela geração: Gemini (Agente 2)
"""
        
        if use_markdown:
            format_instruction = """
FORMATAÇÃO DA RESPOSTA:
Use formatação Markdown para organizar a resposta:
- **Negrito** para destacar títulos e palavras-chave importantes
- *Itálico* para justificativas e explicações
- `Código` para códigos de idioma ou termos técnicos
- Listas numeradas para organizar os tipos de título
- Quebras de linha para melhor legibilidade
"""
        else:
            format_instruction = """
FORMATAÇÃO DA RESPOSTA:
Use apenas texto simples, sem formatação especial.
Organize de forma clara e legível, mas sem usar markdown, negrito, itálico ou outros elementos de formatação.
"""

        # Consolidate title types for the prompt, if any are specified
        tipos_solicitados_str = "TODOS OS TIPOS ABAIXO"
        if title_types:
            tipos_solicitados_str = ", ".join(title_types)


        prompt = f"""
🤖 SISTEMA MULTI-AGENTES - COMUNICAÇÃO ENTRE AGENTES:
- AGENTE 1 (OpenAI): Detectou idioma = {lang_code} ({lang_name})
- AGENTE 2 (Gemini): Deve gerar conteúdo em {lang_name}

INSTRUÇÕES OBRIGATÓRIAS PARA AGENTE 2 (Gemini):
{language_instruction}

{format_instruction}

Você é um especialista avançado em YouTube SEO, com profundo conhecimento das melhores práticas da plataforma.

ESPECIALIZAÇÃO EM TÍTULOS:

Analise esta transcrição de vídeo e gere títulos otimizados.

TRANSCRIÇÃO:
{transcription_text}

TIPOS DE TÍTULO SOLICITADOS: {tipos_solicitados_str}
Gere um título para CADA UM dos tipos solicitados.

Para cada tipo de título, forneça:
- O TIPO DE TÍTULO como um cabeçalho (ex: ### Título Impactante)
- Título sugerido
- Justificativa (por que funciona)
- Palavras-chave utilizadas

DEFINIÇÕES DOS TIPOS DE TÍTULO (Use estas definições para guiar a geração):
- Impactante: (Objetivo: Usar emoção, intensidade e palavras fortes para gerar cliques.) Crie um título impactante com linguagem forte e que gere uma reação emocional no público. Use verbos no imperativo e palavras de alto impacto. Exemplo: 👉 Ele Destruiu Tudo em Apenas 5 Minutos!
- Analítico: (Objetivo: Foca em dados, análises, comparações, ideal para vídeos informativos ou de opinião.) Gere um título com linguagem analítica, que sugira uma análise profunda ou comparação entre dados, fatos ou situações. Exemplo: 📊 Por Que Esse Time Está Caindo de Produção? Análise Completa
- Agressivo: (Objetivo: Estilo direto, provocativo, ótimo para vídeos de opinião, crítica ou polêmica.) Crie um título agressivo com tom provocativo ou de confronto. Ideal para vídeos que geram debate ou indignação. Exemplo: 🔥 Esse Jogador NÃO PODE Mais Ser Titular!
- Nicho: (Objetivo: Usa termos que só quem é do nicho entende, criando senso de pertencimento.) Crie um título usando expressões, termos técnicos ou memes específicos do nicho do vídeo. Público-alvo: pessoas que já conhecem o tema. Exemplo (futebol): ⚽ Esse Cara É o Novo "Camisa 10 Raiz"?
- Engajamento: (Objetivo: Estimula comentários, opiniões e compartilhamentos.) Gere um título que convide o público a dar sua opinião, usar perguntas ou temas divisivos. Exemplo: 💬 Quem Foi o Melhor em Campo? Deixe Sua Opinião!
- Curiosidade: (Objetivo: Deixa um mistério no ar, sem revelar o desfecho.) Crie um título que desperte curiosidade extrema, fazendo o público querer descobrir o que acontece. Evite entregar tudo no título. Exemplo: ❓ Você Não Vai Acreditar no Que Aconteceu no Final…
- SEO Clássico: (Objetivo: Focado em otimização, com palavra-chave + tema central.) Crie um título claro, direto, com as principais palavras-chave para ranqueamento no YouTube. Ideal para vídeos evergreen e didáticos. Exemplo: 🔍 Como Funciona o VAR no Futebol Brasileiro
- Storytelling: (Objetivo: Introduz uma história ou uma jornada (ótimo para vlogs, bastidores, narrativas).) Crie um título que pareça o começo de uma história real, com início, conflito e expectativa de resolução. Exemplo: 📽️ Tudo Deu Errado no Meu Primeiro Dia no Novo Clube…
- Shorts: (Objetivo: Títulos curtos, diretos, com punch inicial.) Gere um título com até 50 caracteres, estilo viral, para vídeos curtos do YouTube Shorts. Exemplo: ⚡ Ele Gritou Isso no Meio do Treino!
- Live/Podcast: (Objetivo: Com nomes + tema + tom de conversa.) Crie um título com o nome dos participantes + o assunto principal + tom convidativo para assistir uma conversa. Exemplo: 🎙️ Com fulano: Os Bastidores do Mercado da Bola

IMPORTANTE: 
- Retorne APENAS os títulos organizados conforme solicitado
- NÃO inclua explicações introdutórias como "Here are some suggestions" ou "Okay, I understand"
- Vá direto ao conteúdo solicitado
- Gere títulos seguindo exatamente os tipos solicitados EM {lang_name.upper()}
- Se "shorts" for solicitado, o título deve ter no máximo 50 caracteres"""
        
        return self._generate_content_sync(
            agent_name="youtube_titulo_specialist",
            prompt=prompt,
            lang_code=lang_code
        )

    def generate_description(self, transcription_text: str, description_type: str = "analítica", use_markdown: bool = False, lang_code: str = 'pt', lang_name: str = 'Português (Brasil)') -> ContentResult:
        """Generate optimized YouTube description using multi-agent system."""
        
        logger.info(f"[SISTEMA MULTI-AGENTES - DESCRIÇÃO] Gerando descrição tipo '{description_type}' em {lang_name} ({lang_code}). Markdown: {use_markdown}")

        language_instruction = f"""
🚨 GERE TODO O CONTEÚDO EXCLUSIVAMENTE EM {lang_name.upper()} ({lang_code.upper()})
🚨 NÃO misture idiomas na resposta
🚨 Use as palavras e estruturas típicas do {lang_name.upper()}

CONFIRMAÇÃO DE IDIOMA DETECTADO:
- Código: {lang_code}
- Idioma: {lang_name}
- Responsável pela geração: Gemini (Agente 2)
"""
        
        if use_markdown:
            format_instruction = """
FORMATAÇÃO DA RESPOSTA:
Use formatação Markdown para organizar a resposta com estrutura clara e profissional.
"""
        else:
            format_instruction = """
FORMATAÇÃO DA RESPOSTA:
Use apenas texto simples, sem formatação especial.
"""

        prompt = f"""
🤖 SISTEMA MULTI-AGENTES - COMUNICAÇÃO ENTRE AGENTES:
- AGENTE 1 (OpenAI): Detectou idioma = {lang_code} ({lang_name})
- AGENTE 2 (Gemini): Deve gerar conteúdo em {lang_name}

INSTRUÇÕES OBRIGATÓRIAS PARA AGENTE 2 (Gemini):
{language_instruction}

{format_instruction}

Você é um especialista em SEO para YouTube, com domínio total das estratégias que maximizam o alcance, retenção e engajamento dos vídeos na plataforma.

ESPECIALIZAÇÃO EM DESCRIÇÕES:

Analise esta transcrição de vídeo e gere uma descrição otimizada.

TRANSCRIÇÃO:
{transcription_text}

TIPO DE DESCRIÇÃO SOLICITADA: {description_type.upper()}
Use a definição abaixo para guiar a geração da descrição:

DEFINIÇÕES DOS TIPOS DE DESCRIÇÃO:
- Analítica: (Foco: Explicações, detalhes e argumentos.) Escreva uma descrição com tom analítico e informativo. Estruture os parágrafos com clareza, aprofunde nos temas discutidos no vídeo, destaque dados, análises ou conclusões. Ideal para vídeos de opinião, notícias, análises táticas, conteúdo educacional.
- Curiosidade (Gera Curiosidade): (Foco: Prender o público com perguntas e mistério.) Escreva uma descrição com foco em curiosidade. Faça perguntas ao leitor, insinue reviravoltas, crie expectativa sobre o conteúdo do vídeo sem entregar todos os detalhes. Utilize frases com mistério e mantenha o leitor intrigado.
- Hashtags (Resumida e Focada em Hashtags): (Foco: SEO + uso forte de tags.) Gere uma descrição curta, direta e com alto volume de hashtags otimizadas para SEO. Inclua apenas uma introdução objetiva (1-2 linhas) sobre o tema, seguida de hashtags relevantes e estratégicas para posicionamento.
- Tópicos: (Foco: Organização e escaneabilidade.) Escreva a descrição em formato de tópicos com marcadores claros (bullet points, emojis ou traços). Liste os assuntos principais tratados no vídeo e utilize palavras-chave em cada ponto. Ideal para vídeos com conteúdo diversificado ou didático.
- Gatilhos (Gatilhos de Curiosidade): (Foco: Emocional + incentivo ao clique.) Crie uma descrição com gatilhos mentais como "você vai se surpreender", "ninguém te contou isso", "não cometa esse erro" ou "o que ninguém esperava aconteceu". Use frases curtas e com ritmo acelerado, focando no lado emocional do espectador.
- Engajamento (Focada em Engajamento): (Foco: Conversão e ações do público.) Escreva uma descrição persuasiva, com vários CTAs ao longo do texto. Peça explicitamente para o público curtir, se inscrever, ativar o sininho, comentar, compartilhar e salvar o vídeo. Pode incluir perguntas diretas ao público para estimular comentários.

ESTRUTURA OBRIGATÓRIA (exceto para tipo 'Hashtags'):
- Resumo instigante (primeiras 2-3 linhas)
- Desenvolvimento do tema conforme o tipo de descrição
- Palavras-chave naturalmente inseridas
- Call-to-action no final (se aplicável ao tipo)
- Quebras de linha para escaneabilidade

IMPORTANTE:
- Retorne APENAS a descrição conforme solicitado
- NÃO inclua explicações introdutórias ou comentários adicionais
- Vá direto ao conteúdo da descrição
- Gere a descrição EM {lang_name.upper()}"""
        return self._generate_content_sync(
            agent_name=f"youtube_description_specialist_{description_type}",
            prompt=prompt,
            lang_code=lang_code
        )

    def generate_chapters(self, transcription_text: str, num_chapters: int = 6, use_markdown: bool = False, lang_code: str = 'pt', lang_name: str = 'Português (Brasil)') -> ContentResult:
        """Generate YouTube chapters using multi-agent system."""

        logger.info(f"[SISTEMA MULTI-AGENTES - CAPÍTULOS] Gerando {num_chapters} capítulos em {lang_name} ({lang_code}). Markdown: {use_markdown}")
        
        language_instruction = f"""
🚨 GERE TODO O CONTEÚDO EXCLUSIVAMENTE EM {lang_name.upper()} ({lang_code.upper()})
🚨 NÃO misture idiomas na resposta
🚨 Os títulos dos capítulos devem ser concisos e no idioma {lang_name.upper()}
"""
        # Formatting instruction for chapters is subtly different (less emphasis on bold/italics, more on list structure)
        if use_markdown: # Markdown for chapters often means just the timestamp and title
            format_instruction = """
FORMATAÇÃO DA RESPOSTA:
Liste os capítulos no formato:
0:00 Título Conciso do Capítulo 1
1:23 Título Conciso do Capítulo 2
...
Use formatação Markdown para organizar os capítulos de forma clara, mas os títulos dos capítulos em si devem ser texto simples.
"""
        else: # Plain text for chapters
            format_instruction = """
FORMATAÇÃO DA RESPOSTA:
Liste os capítulos no formato:
0:00 Título Conciso do Capítulo 1
1:23 Título Conciso do Capítulo 2
...
Use apenas texto simples, sem formatação especial.
"""
        prompt = f"""
🤖 SISTEMA MULTI-AGENTES - COMUNICAÇÃO ENTRE AGENTES:
- AGENTE 1 (OpenAI): Detectou idioma = {lang_code} ({lang_name})
- AGENTE 2 (Gemini): Deve gerar conteúdo em {lang_name}

INSTRUÇÕES OBRIGATÓRIAS PARA AGENTE 2 (Gemini):
{language_instruction}

{format_instruction}

Você é um especialista em estruturação de conteúdo para YouTube, especializado em criar capítulos (timestamps) que melhoram a experiência do usuário e o engajamento do vídeo.

ESPECIALIZAÇÃO EM CAPÍTULOS:

Analise esta transcrição com timestamps e crie capítulos otimizados:

TRANSCRIÇÃO COM TIMESTAMPS:
{transcription_text}

NÚMERO DE CAPÍTULOS SOLICITADO: {num_chapters}

REGRAS:
- Usar timestamps exatos da transcrição (formato 0:00, 1:34, 2:47)
- Crie EXATAMENTE {num_chapters} capítulos. Se necessário, agrupe partes menores para formar blocos mais coesos ou divida blocos maiores.
- Títulos curtos e objetivos para cada capítulo (máximo 5-6 palavras)
- Evitar frases completas nos títulos dos capítulos
- Facilitar navegação rápida e melhorar SEO interno

IMPORTANTE:
- Retorne APENAS a lista de capítulos no formato solicitado
- NÃO inclua explicações introdutórias ou comentários adicionais
- Vá direto aos capítulos
- Gere os capítulos EM {lang_name.upper()}, seguindo os timestamps existentes, com títulos curtos e objetivos"""
        return self._generate_content_sync(
            agent_name="youtube_chapters_specialist",
            prompt=prompt,
            lang_code=lang_code
        )

    def process_content_generation(self, content_generation: ContentGeneration) -> bool:
        """Process content generation request."""
        logger.info(f"[PROCESS_CONTENT_GENERATION] Starting for ID: {content_generation.id}, User: {content_generation.user}, Type: '{content_generation.content_type}', Markdown: {content_generation.use_markdown}")
        logger.info(f"[PROCESS_CONTENT_GENERATION] Title types: {content_generation.title_types}, Desc type: {content_generation.description_type}, Max chapters: {content_generation.max_chapters}")

        transcription_text = content_generation.transcription.transcription_text
        if not transcription_text:
            content_generation.status = 'failed'
            content_generation.error_message = "Transcrição não encontrada ou vazia."
            content_generation.save()
            logger.error(f"[PROCESS_CONTENT_GENERATION] Failed for ID: {content_generation.id}. Transcription text is missing.")
            return False

        content_generation.status = 'processing'
        content_generation.save()

        # Detect language ONCE for all sub-generations if not already detected from transcription
        # Or, prefer the language detected by the transcription process itself if available
        lang_code_name_str = content_generation.transcription.language_detected
        
        if not lang_code_name_str or '|' not in lang_code_name_str:
            # If transcription didn't detect language or format is wrong, detect it now.
            logger.info(f"[PROCESS_CONTENT_GENERATION] Language not found or invalid in transcription ({lang_code_name_str}). Detecting language for ContentGeneration ID: {content_generation.id}")
            lang_code_name_str = self.detect_transcription_language(transcription_text)
            # Save newly detected language to the ContentGeneration model as well
            content_generation.language_detected = lang_code_name_str 
            content_generation.save() # Save immediately
            logger.info(f"[PROCESS_CONTENT_GENERATION] Language detected and set: {lang_code_name_str} for ContentGeneration ID: {content_generation.id}")
        else:
            logger.info(f"[PROCESS_CONTENT_GENERATION] Using language from transcription: {lang_code_name_str} for ContentGeneration ID: {content_generation.id}")

        try:
            lang_parts = lang_code_name_str.split('|')
            if len(lang_parts) == 2:
                lang_code, lang_name = lang_parts[0].strip(), lang_parts[1].strip()
            else: # Fallback if split doesn't work as expected
                logger.warning(f"[PROCESS_CONTENT_GENERATION] Invalid language format '{lang_code_name_str}', defaulting to Portuguese.")
                lang_code, lang_name = 'pt', 'Português (Brasil)'
                content_generation.language_detected = "pt|Português (Brasil)" # Correct the stored format
                content_generation.save()
        except Exception as e:
            logger.error(f"[PROCESS_CONTENT_GENERATION] Error splitting language string '{lang_code_name_str}': {e}. Defaulting to Portuguese.")
            lang_code, lang_name = 'pt', 'Português (Brasil)'
            content_generation.language_detected = "pt|Português (Brasil)" # Correct the stored format
            content_generation.save()


        generated_outputs = []
        final_error_message = ""
        overall_success = True
        
        # Determine which parts to generate based on content_type and specific fields
        # The UI has checkboxes for "Gerar Títulos", "Gerar Descrição", "Gerar Capítulos"
        # These are reflected in the `content_type` field and specific option fields.
        
        generate_titles_flag = False
        generate_description_flag = False
        generate_chapters_flag = False

        if content_generation.content_type == 'complete':
            # For 'complete', we only generate content for which specific options are provided
            # This allows users to select which parts they want in the complete package
            
            logger.info(f"[COMPLETE PACKAGE] Processing complete package for ID: {content_generation.id}")
            logger.info(f"[COMPLETE PACKAGE] title_types: {content_generation.title_types}")
            logger.info(f"[COMPLETE PACKAGE] description_type: {content_generation.description_type}")
            logger.info(f"[COMPLETE PACKAGE] max_chapters: {content_generation.max_chapters}")
            
            # Generate titles if title_types is provided (not None and not empty list)
            if content_generation.title_types is not None and len(content_generation.title_types) > 0:
                generate_titles_flag = True
                logger.info(f"[COMPLETE PACKAGE] Will generate titles with types: {content_generation.title_types}")
            
            # Generate description if description_type is provided
            if content_generation.description_type:
                generate_description_flag = True
                logger.info(f"[COMPLETE PACKAGE] Will generate description of type: {content_generation.description_type}")
                
            # Generate chapters if max_chapters is provided and > 0
            if content_generation.max_chapters is not None and content_generation.max_chapters > 0:
                generate_chapters_flag = True
                logger.info(f"[COMPLETE PACKAGE] Will generate {content_generation.max_chapters} chapters")
        elif content_generation.content_type == 'titles':
            generate_titles_flag = True
        elif content_generation.content_type == 'description':
            generate_description_flag = True
        elif content_generation.content_type == 'chapters':
            generate_chapters_flag = True

        # 1. Generate Titles if requested
        if generate_titles_flag:
            logger.info(f"[PROCESS_CONTENT_GENERATION - {content_generation.content_type.upper()}] Attempting to generate titles.")
            titles_result = self.generate_titles(
                transcription_text,
                title_types=content_generation.title_types if content_generation.title_types else None, # Pass existing list or None
                use_markdown=content_generation.use_markdown,
                lang_code=lang_code,
                lang_name=lang_name
            )
            if titles_result.status == "success":
                generated_outputs.append(f"--- TÍTULOS GERADOS ---\n{titles_result.content}")
                # Logic to save individual GeneratedTitle objects would go here
                # For now, adding to the main content field for simplicity in this refactor
            else:
                overall_success = False
                error_msg_title = f"Falha ao gerar títulos: {titles_result.error or 'Erro desconhecido'}"
                final_error_message += error_msg_title + "\\n"
                logger.error(f"[PROCESS_CONTENT_GENERATION - {content_generation.content_type.upper()}] Titles result: Status {titles_result.status}, Error: {titles_result.error}")
                generated_outputs.append(error_msg_title)

        # 2. Generate Description if requested
        if generate_description_flag:
            # Use the specific description_type chosen by the user
            desc_type_to_generate = content_generation.description_type or "analítica" # Default if somehow empty
            logger.info(f"[PROCESS_CONTENT_GENERATION - {content_generation.content_type.upper()}] Attempting to generate description type: {desc_type_to_generate}.")
            description_result = self.generate_description(
                transcription_text,
                description_type=desc_type_to_generate,
                use_markdown=content_generation.use_markdown,
                lang_code=lang_code,
                lang_name=lang_name
            )
            if description_result.status == "success":
                generated_outputs.append(f"--- DESCRIÇÃO - {desc_type_to_generate.upper()} ---\n{description_result.content}")
            else:
                overall_success = False
                error_msg_desc = f"Falha ao gerar descrição ({desc_type_to_generate}): {description_result.error or 'Erro desconhecido'}"
                final_error_message += error_msg_desc + "\\n"
                logger.error(f"[PROCESS_CONTENT_GENERATION - {content_generation.content_type.upper()}] Description result for {desc_type_to_generate}: Status {description_result.status}, Error: {description_result.error}")
                generated_outputs.append(error_msg_desc)
        
        # 3. Generate Chapters if requested
        if generate_chapters_flag:
            num_chapters_to_generate = content_generation.max_chapters or 6 # Default if somehow empty
            logger.info(f"[PROCESS_CONTENT_GENERATION - {content_generation.content_type.upper()}] Attempting to generate {num_chapters_to_generate} chapters.")
            chapters_result = self.generate_chapters(
                transcription_text,
                num_chapters=num_chapters_to_generate,
                use_markdown=content_generation.use_markdown,
                lang_code=lang_code,
                lang_name=lang_name
            )
            if chapters_result.status == "success":
                generated_outputs.append(f"--- CAPÍTULOS GERADOS ({num_chapters_to_generate} capítulos) ---\n{chapters_result.content}")
                # Logic to save individual GeneratedChapter objects would go here
            else:
                overall_success = False
                error_msg_chap = f"Falha ao gerar capítulos: {chapters_result.error or 'Erro desconhecido'}"
                final_error_message += error_msg_chap + "\\n"
                logger.error(f"[PROCESS_CONTENT_GENERATION - {content_generation.content_type.upper()}] Chapters result: Status {chapters_result.status}, Error: {chapters_result.error}")
                generated_outputs.append(error_msg_chap)

        if not generate_titles_flag and not generate_description_flag and not generate_chapters_flag:
            logger.warning(f"[PROCESS_CONTENT_GENERATION] No specific content parts were requested for generation ID: {content_generation.id} with content_type '{content_generation.content_type}'. This might indicate an issue with how content_type is set or interpreted.")
            # If it's not 'complete' and no specific type matches, it's an unhandled case or an error.
            if content_generation.content_type not in ['titles', 'description', 'chapters', 'complete']:
                 final_error_message += f"Tipo de conteúdo '{content_generation.content_type}' não manipulado."
                 overall_success = False


        content_generation.generated_content = "\\n\\n".join(generated_outputs)
        
        if overall_success and generated_outputs: # Ensure something was actually generated
            content_generation.status = 'completed'
            content_generation.error_message = None
            logger.info(f"[PROCESS_CONTENT_GENERATION] Result set to SUCCESS for ID: {content_generation.id}")
        elif not generated_outputs and overall_success: # No errors, but nothing generated (e.g. 'complete' but no options chosen)
            content_generation.status = 'failed' # Or perhaps 'completed_empty' / 'completed_with_warnings'
            content_generation.error_message = "Nenhum conteúdo foi solicitado para geração ou as opções não foram configuradas."
            logger.warning(f"[PROCESS_CONTENT_GENERATION] No content generated for ID: {content_generation.id}, though no explicit errors occurred. Setting to FAILED.")
        else: # Some error occurred
            content_generation.status = 'failed'
            content_generation.error_message = final_error_message.strip()
            logger.error(f"[PROCESS_CONTENT_GENERATION] Result set to FAILED for ID: {content_generation.id}. Errors: {final_error_message.strip()}")

        content_generation.completed_at = timezone.now()
        content_generation.save()
        
        logger.info(f"[PROCESS_CONTENT_GENERATION] Final check. Result object: {content_generation.status}, Generated outputs count: {len(generated_outputs)}")
        return overall_success and bool(generated_outputs) 