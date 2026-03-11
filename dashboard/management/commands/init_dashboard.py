from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import PatientDashboard

class Command(BaseCommand):
    help = 'Initialize dashboard data for existing users'
    
    def handle(self, *args, **kwargs):
        # Create dashboards for all users
        users = User.objects.all()
        for user in users:
            dashboard, created = PatientDashboard.objects.get_or_create(user=user)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created dashboard for {user.username}'))
        
        self.stdout.write(self.style.SUCCESS('Dashboard initialization complete!'))