from django.core.management.base import BaseCommand, CommandError

from news.models import NewsSource
from news.views import refresh_source


class Command(BaseCommand):
    help = "Aktualisiert aktive Nachrichtenquellen."

    def add_arguments(self, parser):
        parser.add_argument("--pk", type=int, help="Nur eine einzelne Quelle aktualisieren.")

    def handle(self, *args, **options):
        queryset = NewsSource.objects.filter(is_active=True).select_related("target_group").order_by("name")

        if options["pk"]:
            queryset = queryset.filter(pk=options["pk"])
            if not queryset.exists():
                raise CommandError(f"Keine aktive Quelle mit ID {options['pk']} gefunden.")

        refreshed = 0
        failed = 0

        for source in queryset:
            try:
                created_or_updated, found_links = refresh_source(source)
            except Exception as exc:
                source.last_error = str(exc)
                source.save(update_fields=["last_error", "updated_at"])
                failed += 1
                self.stderr.write(self.style.ERROR(f"{source.name}: {exc}"))
                continue

            refreshed += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"{source.name}: {created_or_updated} Nachrichten und {found_links} Hinweise aktualisiert."
                )
            )

        self.stdout.write(f"Fertig: {refreshed} Quellen aktualisiert, {failed} Fehler.")
