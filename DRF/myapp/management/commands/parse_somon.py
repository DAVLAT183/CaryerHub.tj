from django.core.management.base import BaseCommand
from DRF.myapp.parsing_service import parse_somon_tj_jobs


class Command(BaseCommand):
    help = 'Parse jobs from somon.tj'

    def add_arguments(self, parser):
        parser.add_argument('--max-jobs', type=int, default=20, help='Maximum number of jobs to parse')

    def handle(self, *args, **options):
        max_jobs = options['max_jobs']
        self.stdout.write(f'Starting parsing from somon.tj (max {max_jobs} jobs)...')
        
        result = parse_somon_tj_jobs(max_jobs)
        
        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully parsed: {result.get("created", 0)} created, '
                    f'{result.get("updated", 0)} updated, {result.get("errors", 0)} errors'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'Parsing failed: {result.get("error", "Unknown error")}')
            )