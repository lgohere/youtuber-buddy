"""
Django management command to reprocess pending transcriptions.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.transcriptions.models import Transcription
from apps.transcriptions.tasks import process_youtube_transcription, process_audio_transcription
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reprocess all pending transcriptions or delete them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of transcriptions to process',
        )
        parser.add_argument(
            '--source-type',
            choices=['youtube', 'audio_upload', 'video_upload'],
            help='Only process transcriptions from specific source type',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete pending transcriptions instead of reprocessing them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        source_type = options['source_type']
        delete_mode = options['delete']

        # Build query
        queryset = Transcription.objects.filter(status='pending')
        
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        if limit:
            queryset = queryset[:limit]

        pending_transcriptions = list(queryset)
        
        if not pending_transcriptions:
            self.stdout.write(
                self.style.WARNING('Nenhuma transcrição pendente encontrada.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Encontradas {len(pending_transcriptions)} transcrições pendentes.')
        )

        if delete_mode:
            # Delete mode
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN - As seguintes transcrições seriam DELETADAS:')
                )
                for transcription in pending_transcriptions:
                    self.stdout.write(f'  - ID: {transcription.id}, Tipo: {transcription.source_type}, '
                                    f'Arquivo: {transcription.original_filename or transcription.source_url}')
            else:
                # Confirm deletion
                confirm = input(f'Tem certeza que deseja DELETAR {len(pending_transcriptions)} transcrições pendentes? (sim/não): ')
                if confirm.lower() in ['sim', 's', 'yes', 'y']:
                    deleted_count = 0
                    for transcription in pending_transcriptions:
                        try:
                            self.stdout.write(f'Deletando transcrição ID: {transcription.id}')
                            transcription.delete()
                            deleted_count += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'Erro ao deletar transcrição {transcription.id}: {e}')
                            )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {deleted_count} transcrições deletadas com sucesso!')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('Operação cancelada.')
                    )
        else:
            # Reprocess mode (existing functionality)
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN - As seguintes transcrições seriam reprocessadas:')
                )
                for transcription in pending_transcriptions:
                    self.stdout.write(f'  - ID: {transcription.id}, Tipo: {transcription.source_type}, '
                                    f'Arquivo: {transcription.original_filename or transcription.source_url}')
            else:
                processed_count = 0
                for transcription in pending_transcriptions:
                    try:
                        self.stdout.write(f'Reprocessando transcrição ID: {transcription.id}')
                        
                        # Start appropriate task
                        if transcription.source_type == 'youtube':
                            task = process_youtube_transcription.delay(str(transcription.id))
                        else:
                            task = process_audio_transcription.delay(str(transcription.id))
                        
                        self.stdout.write(f'  Task iniciada: {task.id}')
                        processed_count += 1
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Erro ao reprocessar transcrição {transcription.id}: {e}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {processed_count} transcrições enviadas para reprocessamento!')
                ) 