# Management command to create AI assistant
# management/commands/create_ai_assistant.py
from django.core.management.base import BaseCommand
from whats_app.models import AIAssistant

class Command(BaseCommand):
    help = 'Create AI Assistant'

    def handle(self, *args, **options):
        assistant, created = AIAssistant.objects.get_or_create(
            name="WhatsApp AI",
            defaults={'is_active': True}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('AI Assistant created successfully'))
        else:
            self.stdout.write(self.style.SUCCESS('AI Assistant already exists'))