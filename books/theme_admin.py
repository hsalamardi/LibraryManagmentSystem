from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from .models import ThemeConfiguration, ThemePreset


@admin.register(ThemeConfiguration)
class ThemeConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'is_active', 
        'color_preview', 
        'created_at', 
        'updated_at',
        'preview_button',
        'apply_button'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'color_preview_large']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Primary Colors', {
            'fields': ('primary_color', 'primary_dark', 'primary_light'),
            'classes': ('collapse',)
        }),
        ('Secondary Colors', {
            'fields': ('secondary_color', 'accent_color'),
            'classes': ('collapse',)
        }),
        ('Status Colors', {
            'fields': ('success_color', 'warning_color', 'danger_color', 'info_color'),
            'classes': ('collapse',)
        }),
        ('Background Colors', {
            'fields': ('background_primary', 'background_secondary', 'background_dark'),
            'classes': ('collapse',)
        }),
        ('Text Colors', {
            'fields': ('text_primary', 'text_secondary', 'text_muted', 'text_white'),
            'classes': ('collapse',)
        }),
        ('Border Colors', {
            'fields': ('border_color', 'border_light', 'border_dark'),
            'classes': ('collapse',)
        }),
        ('Card & Component Colors', {
            'fields': ('card_background', 'card_border', 'card_shadow', 'button_radius'),
            'classes': ('collapse',)
        }),
        ('Navigation Colors', {
            'fields': ('navbar_background', 'navbar_text', 'navbar_hover'),
            'classes': ('collapse',)
        }),
        ('Footer Colors', {
            'fields': ('footer_background', 'footer_text'),
            'classes': ('collapse',)
        }),
        ('Book Card Colors', {
            'fields': (
                'book_card_background', 'book_card_border', 'book_card_hover',
                'book_available_color', 'book_borrowed_color', 'book_overdue_color'
            ),
            'classes': ('collapse',)
        }),
        ('Dashboard Colors', {
            'fields': (
                'dashboard_card_bg', 'dashboard_stat_primary', 'dashboard_stat_success',
                'dashboard_stat_warning', 'dashboard_stat_danger'
            ),
            'classes': ('collapse',)
        }),
        ('Preview', {
            'fields': ('color_preview_large',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def color_preview(self, obj):
        """Display a small color preview in the list view."""
        return format_html(
            '<div style="display: flex; gap: 2px;">' +
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;" title="Primary"></div>' +
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;" title="Secondary"></div>' +
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;" title="Accent"></div>' +
            '</div>',
            obj.primary_color,
            obj.secondary_color,
            obj.accent_color
        )
    color_preview.short_description = 'Colors'
    
    def color_preview_large(self, obj):
        """Display a comprehensive color preview."""
        if not obj.pk:
            return "Save the theme first to see preview"
        
        return format_html(
            '''
            <div style="padding: 20px; background: #f5f5f5; border-radius: 8px;">
                <h3>Theme Color Preview</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                    
                    <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0 0 10px 0; color: #333;">Primary Colors</h4>
                        <div style="display: flex; gap: 5px;">
                            <div style="width: 40px; height: 40px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Primary"></div>
                            <div style="width: 40px; height: 40px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Primary Dark"></div>
                            <div style="width: 40px; height: 40px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Primary Light"></div>
                        </div>
                        <small style="color: #666;">Primary • Dark • Light</small>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0 0 10px 0; color: #333;">Status Colors</h4>
                        <div style="display: flex; gap: 5px;">
                            <div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Success"></div>
                            <div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Warning"></div>
                            <div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Danger"></div>
                            <div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Info"></div>
                        </div>
                        <small style="color: #666;">Success • Warning • Danger • Info</small>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0 0 10px 0; color: #333;">Book Status</h4>
                        <div style="display: flex; gap: 5px;">
                            <div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Available"></div>
                            <div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Borrowed"></div>
                            <div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ddd;" title="Overdue"></div>
                        </div>
                        <small style="color: #666;">Available • Borrowed • Overdue</small>
                    </div>
                    
                    <div style="background: {}; padding: 15px; border-radius: 8px; border: 1px solid {};">
                        <h4 style="margin: 0 0 10px 0; color: {};">Sample Card</h4>
                        <p style="margin: 0; color: {}; font-size: 14px;">This is how cards will look with your theme colors.</p>
                        <div style="margin-top: 10px;">
                            <button style="background: {}; color: white; border: none; padding: 8px 16px; border-radius: {}; margin-right: 5px;">Primary</button>
                            <button style="background: {}; color: white; border: none; padding: 8px 16px; border-radius: {};">Secondary</button>
                        </div>
                    </div>
                    
                </div>
            </div>
            ''',
            obj.primary_color, obj.primary_dark, obj.primary_light,
            obj.success_color, obj.warning_color, obj.danger_color, obj.info_color,
            obj.book_available_color, obj.book_borrowed_color, obj.book_overdue_color,
            obj.card_background, obj.card_border, obj.text_primary, obj.text_secondary,
            obj.primary_color, obj.button_radius, obj.secondary_color, obj.button_radius
        )
    color_preview_large.short_description = 'Theme Preview'
    
    def preview_button(self, obj):
        """Add a preview button for each theme."""
        if obj.pk:
            return format_html(
                '<a class="button" href="{}/preview/" target="_blank">Preview</a>',
                obj.pk
            )
        return "-"
    preview_button.short_description = 'Preview'
    
    def apply_button(self, obj):
        """Add an apply button to make theme active."""
        if obj.pk and not obj.is_active:
            return format_html(
                '<a class="button" href="{}/apply/" onclick="return confirm(\'Make this theme active?\')">Apply</a>',
                obj.pk
            )
        elif obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return "-"
    apply_button.short_description = 'Action'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:theme_id>/preview/', self.admin_site.admin_view(self.preview_theme), name='theme_preview'),
            path('<int:theme_id>/apply/', self.admin_site.admin_view(self.apply_theme), name='theme_apply'),
            path('export-css/', self.admin_site.admin_view(self.export_css), name='theme_export_css'),
        ]
        return custom_urls + urls
    
    def preview_theme(self, request, theme_id):
        """Preview a theme without applying it."""
        theme = get_object_or_404(ThemeConfiguration, pk=theme_id)
        css_content = theme.generate_css()
        
        # Return CSS content for preview
        response = HttpResponse(css_content, content_type='text/css')
        response['Content-Disposition'] = f'attachment; filename="{theme.name.lower().replace(" ", "_")}_preview.css"'
        return response
    
    def apply_theme(self, request, theme_id):
        """Apply a theme as the active theme."""
        theme = get_object_or_404(ThemeConfiguration, pk=theme_id)
        
        # Deactivate all themes
        ThemeConfiguration.objects.update(is_active=False)
        
        # Activate selected theme
        theme.is_active = True
        theme.save()
        
        messages.success(request, f'Theme "{theme.name}" has been applied successfully!')
        return self.response_redirect(request, '../')
    
    def export_css(self, request):
        """Export the active theme as CSS file."""
        active_theme = ThemeConfiguration.get_active_theme()
        css_content = active_theme.generate_css()
        
        response = HttpResponse(css_content, content_type='text/css')
        response['Content-Disposition'] = f'attachment; filename="{active_theme.name.lower().replace(" ", "_")}_theme.css"'
        return response
    
    def response_redirect(self, request, url):
        """Helper method for redirects."""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('admin:books_themeconfiguration_changelist'))


@admin.register(ThemePreset)
class ThemePresetAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_built_in', 'created_at', 'apply_preset_button']
    list_filter = ['is_built_in', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_built_in')
        }),
        ('Theme Data', {
            'fields': ('theme_data',),
            'classes': ('collapse',)
        }),
        ('Preview', {
            'fields': ('preview_image',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def apply_preset_button(self, obj):
        """Add button to apply preset to active theme."""
        if obj.pk:
            return format_html(
                '<a class="button" href="{}/apply-preset/" onclick="return confirm(\'Apply this preset to active theme?\')">Apply Preset</a>',
                obj.pk
            )
        return "-"
    apply_preset_button.short_description = 'Action'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:preset_id>/apply-preset/', self.admin_site.admin_view(self.apply_preset), name='apply_theme_preset'),
        ]
        return custom_urls + urls
    
    def apply_preset(self, request, preset_id):
        """Apply a preset to the active theme."""
        preset = get_object_or_404(ThemePreset, pk=preset_id)
        active_theme = ThemeConfiguration.get_active_theme()
        
        # Apply preset data to active theme
        preset.apply_to_theme(active_theme)
        active_theme.save()
        
        messages.success(request, f'Preset "{preset.name}" has been applied to the active theme!')
        return self.response_redirect(request, '../')
    
    def response_redirect(self, request, url):
        """Helper method for redirects."""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('admin:books_themepreset_changelist'))


# Custom admin site modifications
class ThemeAdminMixin:
    """Mixin to add theme-related functionality to admin."""
    
    def get_extra_context(self, request):
        """Add theme context to admin pages."""
        context = super().get_extra_context(request) if hasattr(super(), 'get_extra_context') else {}
        
        try:
            active_theme = ThemeConfiguration.get_active_theme()
            context['active_theme'] = active_theme
            context['theme_css_vars'] = active_theme.to_css_variables()
        except:
            pass
        
        return context


# Add custom CSS to admin
def admin_theme_css(request):
    """Generate CSS for admin interface based on active theme."""
    try:
        active_theme = ThemeConfiguration.get_active_theme()
        css_vars = active_theme.to_css_variables()
        
        admin_css = f"""
        /* Custom admin theme CSS */
        :root {{
            {'; '.join([f'{key}: {value}' for key, value in css_vars.items()])}
        }}
        
        #header {{
            background: var(--primary-color) !important;
        }}
        
        .module h2, .module caption, .inline-group h2 {{
            background: var(--primary-color) !important;
        }}
        
        .button, input[type=submit], input[type=button], .submit-row input, a.button {{
            background: var(--primary-color) !important;
            border-color: var(--primary-dark) !important;
        }}
        
        .button:hover, input[type=submit]:hover, input[type=button]:hover, .submit-row input:hover, a.button:hover {{
            background: var(--primary-dark) !important;
        }}
        
        .selector-chosen h2 {{
            background: var(--success-color) !important;
        }}
        
        .calendar td.selected a {{
            background: var(--primary-color) !important;
        }}
        
        .timelist a {{
            background: var(--primary-color) !important;
        }}
        """
        
        return HttpResponse(admin_css, content_type='text/css')
    except:
        return HttpResponse('/* No active theme */', content_type='text/css')