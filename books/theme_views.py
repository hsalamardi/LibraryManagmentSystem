from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from django.core.cache import cache
from .models import ThemeConfiguration


@require_GET
@cache_page(60 * 60)  # Cache for 1 hour
def theme_css(request):
    """
    Serve dynamic CSS based on the active theme configuration.
    This endpoint generates CSS with theme variables that can be included in templates.
    """
    try:
        # Get active theme
        active_theme = ThemeConfiguration.get_active_theme()
        
        # Generate CSS content
        css_content = active_theme.generate_css()
        
        # Create response with proper content type
        response = HttpResponse(css_content, content_type='text/css')
        
        # Add cache headers
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        response['ETag'] = f'"theme-{active_theme.id}-{active_theme.updated_at.timestamp()}"'
        
        return response
        
    except Exception as e:
        # Return empty CSS if there's an error
        return HttpResponse('/* Theme CSS error */', content_type='text/css')


@require_GET
def theme_variables_json(request):
    """
    Return theme variables as JSON for JavaScript usage.
    """
    import json
    
    try:
        active_theme = ThemeConfiguration.get_active_theme()
        theme_vars = active_theme.to_css_variables()
        
        response_data = {
            'theme_name': active_theme.name,
            'theme_id': active_theme.id,
            'variables': theme_vars,
            'updated_at': active_theme.updated_at.isoformat()
        }
        
        response = HttpResponse(
            json.dumps(response_data, indent=2),
            content_type='application/json'
        )
        response['Cache-Control'] = 'public, max-age=3600'
        
        return response
        
    except Exception as e:
        return HttpResponse(
            json.dumps({'error': 'Theme not found'}),
            content_type='application/json',
            status=404
        )


def clear_theme_cache_view(request):
    """
    Clear theme cache (for admin use).
    """
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)
    
    from .context_processors import clear_theme_cache
    clear_theme_cache()
    
    return HttpResponse('Theme cache cleared successfully')