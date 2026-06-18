from django.core.management.base import BaseCommand

from apps.agent.definition_service import AgentDefinitionService


class Command(BaseCommand):
    help = "Seed default independent Agent definitions, prompts and routes."

    def handle(self, *args, **options):
        created = AgentDefinitionService.ensure_defaults()
        self.stdout.write(self.style.SUCCESS(f"independent agents ready, created={created}"))
