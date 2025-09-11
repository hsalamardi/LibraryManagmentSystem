from django.core.management.base import BaseCommand
from books.models import ThemeConfiguration, ThemePreset


class Command(BaseCommand):
    help = 'Create default theme configurations and presets'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating default themes...')
        
        # Create default theme presets
        presets = [
            {
                'name': 'Classic Blue',
                'description': 'Professional blue theme with clean design',
                'theme_data': {
                    'primary_color': '#2563eb',
                    'primary_dark': '#1d4ed8',
                    'primary_light': '#3b82f6',
                    'secondary_color': '#64748b',
                    'accent_color': '#f59e0b',
                    'success_color': '#10b981',
                    'warning_color': '#f59e0b',
                    'danger_color': '#ef4444',
                    'background_primary': '#ffffff',
                    'background_secondary': '#f8fafc',
                    'text_primary': '#1e293b',
                    'text_secondary': '#64748b',
                    'border_color': '#e2e8f0',
                }
            },
            {
                'name': 'Forest Green',
                'description': 'Nature-inspired green theme',
                'theme_data': {
                    'primary_color': '#059669',
                    'primary_dark': '#047857',
                    'primary_light': '#10b981',
                    'secondary_color': '#6b7280',
                    'accent_color': '#f59e0b',
                    'success_color': '#10b981',
                    'warning_color': '#f59e0b',
                    'danger_color': '#ef4444',
                    'background_primary': '#ffffff',
                    'background_secondary': '#f0fdf4',
                    'text_primary': '#1f2937',
                    'text_secondary': '#6b7280',
                    'border_color': '#d1fae5',
                }
            },
            {
                'name': 'Royal Purple',
                'description': 'Elegant purple theme for academic institutions',
                'theme_data': {
                    'primary_color': '#7c3aed',
                    'primary_dark': '#6d28d9',
                    'primary_light': '#8b5cf6',
                    'secondary_color': '#64748b',
                    'accent_color': '#f59e0b',
                    'success_color': '#10b981',
                    'warning_color': '#f59e0b',
                    'danger_color': '#ef4444',
                    'background_primary': '#ffffff',
                    'background_secondary': '#faf5ff',
                    'text_primary': '#1e293b',
                    'text_secondary': '#64748b',
                    'border_color': '#e9d5ff',
                }
            },
            {
                'name': 'Sunset Orange',
                'description': 'Warm orange theme with energetic feel',
                'theme_data': {
                    'primary_color': '#ea580c',
                    'primary_dark': '#c2410c',
                    'primary_light': '#f97316',
                    'secondary_color': '#64748b',
                    'accent_color': '#eab308',
                    'success_color': '#10b981',
                    'warning_color': '#f59e0b',
                    'danger_color': '#ef4444',
                    'background_primary': '#ffffff',
                    'background_secondary': '#fff7ed',
                    'text_primary': '#1e293b',
                    'text_secondary': '#64748b',
                    'border_color': '#fed7aa',
                }
            },
            {
                'name': 'Dark Mode',
                'description': 'Modern dark theme for reduced eye strain',
                'theme_data': {
                    'primary_color': '#3b82f6',
                    'primary_dark': '#2563eb',
                    'primary_light': '#60a5fa',
                    'secondary_color': '#6b7280',
                    'accent_color': '#fbbf24',
                    'success_color': '#10b981',
                    'warning_color': '#f59e0b',
                    'danger_color': '#ef4444',
                    'background_primary': '#1f2937',
                    'background_secondary': '#111827',
                    'text_primary': '#f9fafb',
                    'text_secondary': '#d1d5db',
                    'border_color': '#374151',
                    'card_background': '#374151',
                    'navbar_background': '#111827',
                    'navbar_text': '#f9fafb',
                }
            },
            {
                'name': 'University Red',
                'description': 'Bold red theme for university libraries',
                'theme_data': {
                    'primary_color': '#dc2626',
                    'primary_dark': '#b91c1c',
                    'primary_light': '#ef4444',
                    'secondary_color': '#64748b',
                    'accent_color': '#f59e0b',
                    'success_color': '#10b981',
                    'warning_color': '#f59e0b',
                    'danger_color': '#ef4444',
                    'background_primary': '#ffffff',
                    'background_secondary': '#fef2f2',
                    'text_primary': '#1e293b',
                    'text_secondary': '#64748b',
                    'border_color': '#fecaca',
                }
            }
        ]
        
        # Create theme presets
        for preset_data in presets:
            preset, created = ThemePreset.objects.get_or_create(
                name=preset_data['name'],
                defaults={
                    'description': preset_data['description'],
                    'theme_data': preset_data['theme_data'],
                    'is_built_in': True
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created theme preset: {preset.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Theme preset already exists: {preset.name}')
                )
        
        # Create default active theme if none exists
        if not ThemeConfiguration.objects.filter(is_active=True).exists():
            default_theme = ThemeConfiguration.objects.create(
                name='Default NTA Library Theme',
                description='Default professional theme for NTA Library',
                is_active=True,
                # Use Classic Blue preset colors
                primary_color='#2563eb',
                primary_dark='#1d4ed8',
                primary_light='#3b82f6',
                secondary_color='#64748b',
                accent_color='#f59e0b',
                success_color='#10b981',
                warning_color='#f59e0b',
                danger_color='#ef4444',
                background_primary='#ffffff',
                background_secondary='#f8fafc',
                text_primary='#1e293b',
                text_secondary='#64748b',
                border_color='#e2e8f0',
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created default active theme: {default_theme.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Active theme already exists')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created default themes and presets!')
        )
        self.stdout.write(
            'You can now access the theme configuration in Django Admin under "Theme Configurations"'
        )