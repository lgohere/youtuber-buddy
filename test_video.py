#!/usr/bin/env python3
"""
Script de teste para verificar se o processamento de vídeo está funcionando
"""

import os
import sys
import tempfile
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ffmpeg():
    """Testa se FFmpeg está funcionando"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg está funcionando")
            return True
        else:
            print("❌ FFmpeg não está funcionando")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar FFmpeg: {e}")
        return False

def test_moviepy():
    """Testa se MoviePy está funcionando"""
    try:
        from moviepy.editor import VideoFileClip
        from moviepy.config import get_setting
        
        ffmpeg_binary = get_setting("FFMPEG_BINARY")
        print(f"MoviePy está usando FFmpeg em: {ffmpeg_binary}")
        
        if os.path.exists(ffmpeg_binary):
            print("✅ MoviePy está configurado corretamente")
            return True
        else:
            print("❌ MoviePy não encontrou FFmpeg")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar MoviePy: {e}")
        return False

def test_pydub():
    """Testa se PyDub está funcionando"""
    try:
        from pydub import AudioSegment
        print("✅ PyDub está funcionando")
        return True
    except Exception as e:
        print(f"❌ Erro ao testar PyDub: {e}")
        return False

def main():
    print("=== Teste de Configuração do Sistema ===")
    print()
    
    # Testar FFmpeg
    print("1. Testando FFmpeg...")
    ffmpeg_ok = test_ffmpeg()
    print()
    
    # Testar MoviePy
    print("2. Testando MoviePy...")
    moviepy_ok = test_moviepy()
    print()
    
    # Testar PyDub
    print("3. Testando PyDub...")
    pydub_ok = test_pydub()
    print()
    
    # Resultado final
    print("=== Resultado ===")
    if ffmpeg_ok and moviepy_ok and pydub_ok:
        print("✅ Todos os testes passaram! O sistema está pronto para processar vídeos.")
        return 0
    else:
        print("❌ Alguns testes falharam. Verifique a instalação das dependências.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 