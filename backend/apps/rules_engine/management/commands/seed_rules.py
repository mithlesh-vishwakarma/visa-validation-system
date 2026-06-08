from django.core.management.base import BaseCommand
from rules_engine.models import CountryRule

class Command(BaseCommand):
    help = 'Seeds initial country visa rules'

    def handle(self, *args, **kwargs):
        rules_data = [
            {
                'country': 'Canada',
                'visa_type': 'Tourist',
                'required_documents': ['Passport', 'Bank Statement', 'ITR', 'Photo'],
                'rules': {
                    'passport_min_validity_months': 6,
                    'min_bank_balance': 300000,
                }
            },
            {
                'country': 'UK',
                'visa_type': 'Tourist',
                'required_documents': ['Passport', 'Bank Statement', 'Employment Letter', 'Salary Slips'],
                'rules': {
                    'passport_min_validity_months': 6,
                    'min_bank_balance': 400000,
                }
            },
            {
                'country': 'USA',
                'visa_type': 'Tourist',
                'required_documents': ['Passport', 'DS-160 Confirmation', 'Visa Fee Receipt', 'Bank Statement'],
                'rules': {
                    'passport_min_validity_months': 6,
                    'min_bank_balance': 500000,
                }
            }
        ]

        for rule in rules_data:
            obj, created = CountryRule.objects.update_or_create(
                country=rule['country'],
                visa_type=rule['visa_type'],
                defaults={
                    'required_documents': rule['required_documents'],
                    'rules': rule['rules']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created rule for {rule['country']} - {rule['visa_type']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated rule for {rule['country']} - {rule['visa_type']}"))
