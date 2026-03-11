from django.core.management.base import BaseCommand
from ai_models.train_models import ModelTrainer
from ai_models.models import AIModel

class Command(BaseCommand):
    help = 'Setup initial AI models'
    
    def handle(self, *args, **kwargs):
        self.stdout.write("Setting up AI models...")
        
        # Create initial model records
        models_data = [
            {
                'name': 'Spiral Drawing Classifier',
                'model_type': 'spiral',
                'description': 'Analyzes spiral drawings for Parkinson\'s tremors',
                'status': 'untrained',
            },
            {
                'name': 'Voice Analysis Classifier',
                'model_type': 'voice',
                'description': 'Analyzes voice recordings for speech patterns',
                'status': 'untrained',
            },
            {
                'name': 'Symptom Quiz Evaluator',
                'model_type': 'quiz',
                'description': 'Evaluates symptom questionnaires for risk assessment',
                'status': 'untrained',
            },
            {
                'name': 'Ensemble Predictor',
                'model_type': 'ensemble',
                'description': 'Combines predictions from multiple models',
                'status': 'untrained',
            },
        ]
        
        for data in models_data:
            model, created = AIModel.objects.get_or_create(
                model_type=data['model_type'],
                defaults=data
            )
            if created:
                self.stdout.write(f"Created {data['model_type']} model")
            else:
                self.stdout.write(f"{data['model_type']} model already exists")
        
        self.stdout.write(self.style.SUCCESS("AI models setup complete!"))
        
        # Ask if user wants to train models
        response = input("\nDo you want to train the models now? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            self.stdout.write("Starting model training...")
            trainer = ModelTrainer()
            results = trainer.train_all_models()
            self.stdout.write(self.style.SUCCESS("Model training complete!"))