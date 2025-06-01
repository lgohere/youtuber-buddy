from django.core.management.base import BaseCommand
from apps.transcriptions.models import Transcription
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Delete pending transcriptions with various filtering options'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all pending transcriptions',
        )
        parser.add_argument(
            '--older-than',
            type=int,
            help='Delete pending transcriptions older than X hours',
        )
        parser.add_argument(
            '--source-type',
            choices=['youtube', 'audio_upload', 'video_upload'],
            help='Only delete transcriptions from specific source type',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of transcriptions to delete',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_all = options['all']
        older_than_hours = options['older_than']
        source_type = options['source_type']
        limit = options['limit']
        force = options['force']

        # Build query
        queryset = Transcription.objects.filter(status='pending')
        
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        if older_than_hours:
            cutoff_time = timezone.now() - timedelta(hours=older_than_hours)
            queryset = queryset.filter(created_at__lt=cutoff_time)
        
        queryset = queryset.order_by('created_at')
        
        if limit:
            queryset = queryset[:limit]

        pending_transcriptions = list(queryset)
        
        if not pending_transcriptions:
            self.stdout.write(
                self.style.WARNING('Nenhuma transcrição pendente encontrada com os critérios especificados.')
            )
            return

        # Show what will be deleted
        self.stdout.write(
            self.style.SUCCESS(f'Encontradas {len(pending_transcriptions)} transcrições pendentes para deletar.')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - As seguintes transcrições seriam DELETADAS:')
            )
            for transcription in pending_transcriptions:
                age_hours = (timezone.now() - transcription.created_at).total_seconds() / 3600
                self.stdout.write(
                    f'  - ID: {transcription.id}, Tipo: {transcription.source_type}, '
                    f'Arquivo: {transcription.original_filename or transcription.source_url}, '
                    f'Idade: {age_hours:.1f}h'
                )
            return

        # Confirmation
        if not force:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('ATENÇÃO: Esta operação é irreversível!'))
            
            # Show details
            for transcription in pending_transcriptions[:5]:  # Show first 5
                age_hours = (timezone.now() - transcription.created_at).total_seconds() / 3600
                self.stdout.write(
                    f'  - ID: {transcription.id}, Tipo: {transcription.source_type}, '
                    f'Arquivo: {transcription.original_filename or transcription.source_url}, '
                    f'Idade: {age_hours:.1f}h'
                )
            
            if len(pending_transcriptions) > 5:
                self.stdout.write(f'  ... e mais {len(pending_transcriptions) - 5} transcrições')
            
            self.stdout.write('')
            confirm = input(f'Tem certeza que deseja DELETAR {len(pending_transcriptions)} transcrições pendentes? (digite "DELETAR" para confirmar): ')
            if confirm != 'DELETAR':
                self.stdout.write(
                    self.style.WARNING('Operação cancelada. Para confirmar, digite exatamente "DELETAR".')
                )
                return

        # Delete transcriptions
        deleted_count = 0
        failed_count = 0
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Iniciando deleção...'))
        
        for transcription in pending_transcriptions:
            try:
                transcription_info = f'ID: {transcription.id} ({transcription.source_type})'
                transcription.delete()
                deleted_count += 1
                self.stdout.write(f'  ✅ Deletado: {transcription_info}')
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Erro ao deletar ID {transcription.id}: {e}')
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== RESUMO ==='))
        self.stdout.write(f'Deletadas com sucesso: {deleted_count}')
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Falharam: {failed_count}'))
        
        self.stdout.write('')
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {deleted_count} transcrições pendentes deletadas com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Nenhuma transcrição foi deletada.')
            ) 