#!/usr/bin/env python3
"""
Script de limpeza automática para YouTube Buddy
Remove sessões antigas e arquivos temporários
"""

import os
import sys
import argparse
import tempfile
import shutil
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db_manager

def cleanup_old_sessions(days_old: int = 7):
    """Remove sessões antigas do banco de dados"""
    print(f"🧹 Removendo sessões com mais de {days_old} dias...")
    
    try:
        db_manager.cleanup_old_sessions(days_old)
        print("✅ Limpeza de sessões concluída!")
    except Exception as e:
        print(f"❌ Erro na limpeza de sessões: {e}")

def cleanup_temp_files():
    """Remove arquivos temporários antigos"""
    print("🗑️ Limpando arquivos temporários...")
    
    temp_base = tempfile.gettempdir()
    cleaned_count = 0
    
    try:
        for item in os.listdir(temp_base):
            if item.startswith("youtube_buddy_"):
                item_path = os.path.join(temp_base, item)
                if os.path.isdir(item_path):
                    # Verificar se é antigo (mais de 1 dia)
                    creation_time = datetime.fromtimestamp(os.path.getctime(item_path))
                    if datetime.now() - creation_time > timedelta(days=1):
                        shutil.rmtree(item_path)
                        cleaned_count += 1
        
        print(f"✅ {cleaned_count} diretórios temporários removidos!")
    except Exception as e:
        print(f"❌ Erro na limpeza de arquivos temporários: {e}")

def show_database_stats():
    """Mostra estatísticas do banco de dados"""
    print("📊 Estatísticas do banco de dados:")
    
    try:
        stats = db_manager.get_database_stats()
        print(f"   • Sessões ativas (7 dias): {stats['active_sessions']}")
        print(f"   • Total de transcrições: {stats['total_transcriptions']}")
        print(f"   • Conteúdo gerado: {stats['total_generated_content']}")
        print(f"   • Tamanho do banco: {stats['database_size_mb']} MB")
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")

def main():
    parser = argparse.ArgumentParser(description="Script de limpeza do YouTube Buddy")
    parser.add_argument("--days", type=int, default=7, 
                       help="Dias para considerar sessões antigas (padrão: 7)")
    parser.add_argument("--stats-only", action="store_true",
                       help="Apenas mostrar estatísticas, sem limpar")
    parser.add_argument("--no-temp", action="store_true",
                       help="Não limpar arquivos temporários")
    
    args = parser.parse_args()
    
    print("🤖 YouTube Buddy - Script de Limpeza")
    print("=" * 40)
    
    # Mostrar estatísticas
    show_database_stats()
    print()
    
    if args.stats_only:
        print("📋 Modo apenas estatísticas - nenhuma limpeza realizada.")
        return
    
    # Limpeza de sessões antigas
    cleanup_old_sessions(args.days)
    print()
    
    # Limpeza de arquivos temporários
    if not args.no_temp:
        cleanup_temp_files()
        print()
    
    # Mostrar estatísticas finais
    print("📊 Estatísticas após limpeza:")
    show_database_stats()
    
    print("\n✅ Limpeza concluída!")

if __name__ == "__main__":
    main() 