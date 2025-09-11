from django.core.cache import cache
from .models import ThemeConfiguration


def theme_context(request):
    """
    Context processor to add theme variables to all templates.
    This makes theme colors and settings available in every template.
    """
    try:
        # Get active theme from cache or database
        active_theme = cache.get('active_theme_context')
        if active_theme is None:
            active_theme = ThemeConfiguration.get_active_theme()
            cache.set('active_theme_context', active_theme, 3600)  # Cache for 1 hour
        
        # Return theme variables for templates
        return {
            'theme': active_theme,
            'theme_vars': active_theme.to_css_variables() if active_theme else {},
            'theme_css': active_theme.generate_css() if active_theme else '',
        }
    except Exception as e:
        # Fallback in case of any errors
        return {
            'theme': None,
            'theme_vars': {},
            'theme_css': '',
        }


def clear_theme_cache():
    """
    Utility function to clear theme-related cache.
    Call this when themes are updated.
    """
    cache.delete('active_theme')
    cache.delete('active_theme_context')
    cache.delete_many([f'theme_{i}' for i in range(1, 100)])  # Clear individual theme caches