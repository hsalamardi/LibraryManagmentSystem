/**
 * Mobile Enhancement JavaScript
 * Provides enhanced mobile user experience for the Library Management System
 */

(function() {
    'use strict';
    
    // Mobile detection
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    // Initialize mobile enhancements when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initMobileNavigation();
        initTouchEnhancements();
        initResponsiveSearch();
        initMobileOptimizations();
        initAccessibilityFeatures();
        initPerformanceOptimizations();
    });
    
    /**
     * Initialize mobile navigation with hamburger menu
     */
    function initMobileNavigation() {
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            navbarToggler.addEventListener('click', function() {
                navbarCollapse.classList.toggle('show');
                
                // Update aria-expanded attribute for accessibility
                const isExpanded = navbarCollapse.classList.contains('show');
                navbarToggler.setAttribute('aria-expanded', isExpanded);
                
                // Add animation class
                navbarCollapse.style.transition = 'all 0.3s ease';
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', function(event) {
                if (!navbarToggler.contains(event.target) && !navbarCollapse.contains(event.target)) {
                    navbarCollapse.classList.remove('show');
                    navbarToggler.setAttribute('aria-expanded', 'false');
                }
            });
            
            // Close menu when pressing Escape key
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape' && navbarCollapse.classList.contains('show')) {
                    navbarCollapse.classList.remove('show');
                    navbarToggler.setAttribute('aria-expanded', 'false');
                    navbarToggler.focus();
                }
            });
        }
    }
    
    /**
     * Initialize touch enhancements for better mobile interaction
     */
    function initTouchEnhancements() {
        if (!isTouch) return;
        
        // Add touch feedback to buttons and interactive elements
        const interactiveElements = document.querySelectorAll('.btn, .card, .book-item, .nav-link');
        
        interactiveElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
                this.style.transition = 'transform 0.1s ease';
            });
            
            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                }, 100);
            });
            
            element.addEventListener('touchcancel', function() {
                this.style.transform = '';
            });
        });
        
        // Improve scroll performance on mobile
        document.body.style.webkitOverflowScrolling = 'touch';
        
        // Add swipe gestures for book cards
        initSwipeGestures();
    }
    
    /**
     * Initialize swipe gestures for book cards
     */
    function initSwipeGestures() {
        const bookItems = document.querySelectorAll('.book-item');
        
        bookItems.forEach(item => {
            let startX = 0;
            let startY = 0;
            let currentX = 0;
            let currentY = 0;
            
            item.addEventListener('touchstart', function(e) {
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
            });
            
            item.addEventListener('touchmove', function(e) {
                currentX = e.touches[0].clientX;
                currentY = e.touches[0].clientY;
            });
            
            item.addEventListener('touchend', function(e) {
                const diffX = startX - currentX;
                const diffY = startY - currentY;
                
                // Check if it's a horizontal swipe
                if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                    if (diffX > 0) {
                        // Swipe left - show more options
                        showBookOptions(this);
                    } else {
                        // Swipe right - hide options
                        hideBookOptions(this);
                    }
                }
            });
        });
    }
    
    /**
     * Show book options on swipe
     */
    function showBookOptions(bookItem) {
        const existingOptions = bookItem.querySelector('.book-options');
        if (existingOptions) return;
        
        const options = document.createElement('div');
        options.className = 'book-options';
        options.innerHTML = `
            <button class="btn btn-sm btn-primary" onclick="viewBook(this)">
                <i class="fas fa-eye"></i> View
            </button>
            <button class="btn btn-sm btn-success" onclick="borrowBook(this)">
                <i class="fas fa-book"></i> Borrow
            </button>
        `;
        
        options.style.cssText = `
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            gap: 8px;
            background: rgba(255, 255, 255, 0.95);
            padding: 8px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            animation: slideInRight 0.3s ease;
        `;
        
        bookItem.style.position = 'relative';
        bookItem.appendChild(options);
        
        // Auto-hide after 3 seconds
        setTimeout(() => hideBookOptions(bookItem), 3000);
    }
    
    /**
     * Hide book options
     */
    function hideBookOptions(bookItem) {
        const options = bookItem.querySelector('.book-options');
        if (options) {
            options.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => options.remove(), 300);
        }
    }
    
    /**
     * Initialize responsive search functionality
     */
    function initResponsiveSearch() {
        const searchInput = document.querySelector('.search-input');
        if (!searchInput) return;
        
        // Add search suggestions for mobile
        const searchContainer = searchInput.parentElement;
        const suggestions = document.createElement('div');
        suggestions.className = 'search-suggestions';
        suggestions.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #e9ecef;
            border-top: none;
            border-radius: 0 0 8px 8px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        `;
        
        searchContainer.appendChild(suggestions);
        
        // Debounced search
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value, suggestions);
            }, 300);
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(event) {
            if (!searchContainer.contains(event.target)) {
                suggestions.style.display = 'none';
            }
        });
        
        // Voice search support (if available)
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            addVoiceSearch(searchInput);
        }
    }
    
    /**
     * Perform search and show suggestions
     */
    function performSearch(query, suggestionsContainer) {
        if (query.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        // Mock search suggestions (replace with actual API call)
        const mockSuggestions = [
            'JavaScript Programming',
            'Python for Beginners',
            'Web Development',
            'Data Science',
            'Machine Learning'
        ].filter(item => item.toLowerCase().includes(query.toLowerCase()));
        
        if (mockSuggestions.length > 0) {
            suggestionsContainer.innerHTML = mockSuggestions
                .map(suggestion => `
                    <div class="search-suggestion-item" style="
                        padding: 12px 16px;
                        cursor: pointer;
                        border-bottom: 1px solid #f8f9fa;
                    " onclick="selectSuggestion('${suggestion}')">
                        ${suggestion}
                    </div>
                `).join('');
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    }
    
    /**
     * Add voice search functionality
     */
    function addVoiceSearch(searchInput) {
        const voiceButton = document.createElement('button');
        voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceButton.className = 'voice-search-btn';
        voiceButton.style.cssText = `
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #6c757d;
            font-size: 1.1rem;
            cursor: pointer;
            padding: 4px;
        `;
        
        searchInput.parentElement.appendChild(voiceButton);
        
        voiceButton.addEventListener('click', function() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.lang = 'en-US';
            recognition.continuous = false;
            recognition.interimResults = false;
            
            recognition.onstart = function() {
                voiceButton.style.color = '#e74c3c';
                voiceButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            };
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                searchInput.value = transcript;
                searchInput.dispatchEvent(new Event('input'));
            };
            
            recognition.onend = function() {
                voiceButton.style.color = '#6c757d';
                voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
            };
            
            recognition.start();
        });
    }
    
    /**
     * Initialize mobile-specific optimizations
     */
    function initMobileOptimizations() {
        // Prevent zoom on input focus for iOS
        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
            const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea, select');
            inputs.forEach(input => {
                if (parseFloat(getComputedStyle(input).fontSize) < 16) {
                    input.style.fontSize = '16px';
                }
            });
        }
        
        // Add pull-to-refresh functionality
        if (isMobile) {
            initPullToRefresh();
        }
        
        // Optimize images for mobile
        optimizeImagesForMobile();
        
        // Add mobile-specific loading states
        addMobileLoadingStates();
    }
    
    /**
     * Initialize pull-to-refresh functionality
     */
    function initPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let pullDistance = 0;
        const threshold = 100;
        
        const refreshIndicator = document.createElement('div');
        refreshIndicator.className = 'pull-refresh-indicator';
        refreshIndicator.innerHTML = '<i class="fas fa-sync-alt"></i> Pull to refresh';
        refreshIndicator.style.cssText = `
            position: fixed;
            top: -60px;
            left: 50%;
            transform: translateX(-50%);
            background: #3498db;
            color: white;
            padding: 12px 24px;
            border-radius: 0 0 12px 12px;
            font-size: 0.9rem;
            z-index: 1001;
            transition: top 0.3s ease;
        `;
        
        document.body.appendChild(refreshIndicator);
        
        document.addEventListener('touchstart', function(e) {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
            }
        });
        
        document.addEventListener('touchmove', function(e) {
            if (window.scrollY === 0 && startY > 0) {
                currentY = e.touches[0].clientY;
                pullDistance = currentY - startY;
                
                if (pullDistance > 0) {
                    e.preventDefault();
                    const progress = Math.min(pullDistance / threshold, 1);
                    refreshIndicator.style.top = `${-60 + (60 * progress)}px`;
                    
                    if (pullDistance > threshold) {
                        refreshIndicator.innerHTML = '<i class="fas fa-sync-alt"></i> Release to refresh';
                        refreshIndicator.style.background = '#27ae60';
                    }
                }
            }
        });
        
        document.addEventListener('touchend', function() {
            if (pullDistance > threshold) {
                refreshIndicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                refreshIndicator.style.top = '-60px';
                refreshIndicator.style.background = '#3498db';
                refreshIndicator.innerHTML = '<i class="fas fa-sync-alt"></i> Pull to refresh';
            }
            
            startY = 0;
            pullDistance = 0;
        });
    }
    
    /**
     * Optimize images for mobile devices
     */
    function optimizeImagesForMobile() {
        const images = document.querySelectorAll('img');
        
        images.forEach(img => {
            // Add loading="lazy" for better performance
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
            
            // Add error handling
            img.addEventListener('error', function() {
                this.src = '/static/images/placeholder-book.svg';
                this.alt = 'Image not available';
            });
            
            // Add loading placeholder
            if (!img.complete) {
                img.style.background = 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)';
                img.style.backgroundSize = '200% 100%';
                img.style.animation = 'loading 1.5s infinite';
                
                img.addEventListener('load', function() {
                    this.style.background = '';
                    this.style.animation = '';
                });
            }
        });
    }
    
    /**
     * Add mobile-specific loading states
     */
    function addMobileLoadingStates() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                    submitBtn.disabled = true;
                }
            });
        });
    }
    
    /**
     * Initialize accessibility features for mobile
     */
    function initAccessibilityFeatures() {
        // Add skip link for keyboard navigation
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'skip-link';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 1002;
        `;
        
        skipLink.addEventListener('focus', function() {
            this.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', function() {
            this.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Improve focus management
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', function() {
            document.body.classList.remove('keyboard-navigation');
        });
    }
    
    /**
     * Initialize performance optimizations
     */
    function initPerformanceOptimizations() {
        // Lazy load content below the fold
        if ('IntersectionObserver' in window) {
            const lazyElements = document.querySelectorAll('.lazy-load');
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('loaded');
                        observer.unobserve(entry.target);
                    }
                });
            });
            
            lazyElements.forEach(el => observer.observe(el));
        }
        
        // Preload critical resources
        const criticalLinks = document.querySelectorAll('a[href*="/books/"], a[href*="/dashboard"]');
        criticalLinks.forEach(link => {
            link.addEventListener('mouseenter', function() {
                const prefetchLink = document.createElement('link');
                prefetchLink.rel = 'prefetch';
                prefetchLink.href = this.href;
                document.head.appendChild(prefetchLink);
            }, { once: true });
        });
    }
    
    // Global functions for mobile interactions
    window.selectSuggestion = function(suggestion) {
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.value = suggestion;
            searchInput.form.submit();
        }
    };
    
    window.viewBook = function(button) {
        const bookItem = button.closest('.book-item');
        const bookId = bookItem.dataset.bookId;
        if (bookId) {
            window.location.href = `/books/${bookId}/`;
        }
    };
    
    window.borrowBook = function(button) {
        const bookItem = button.closest('.book-item');
        const bookId = bookItem.dataset.bookId;
        if (bookId) {
            // Add loading state
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;
            
            // Simulate API call (replace with actual implementation)
            setTimeout(() => {
                alert('Borrow request submitted!');
                button.innerHTML = '<i class="fas fa-check"></i> Requested';
                button.classList.remove('btn-success');
                button.classList.add('btn-secondary');
            }, 1000);
        }
    };
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%) translateY(-50%); opacity: 0; }
            to { transform: translateX(0) translateY(-50%); opacity: 1; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0) translateY(-50%); opacity: 1; }
            to { transform: translateX(100%) translateY(-50%); opacity: 0; }
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        .keyboard-navigation *:focus {
            outline: 2px solid #3498db !important;
            outline-offset: 2px !important;
        }
        
        .skip-link:focus {
            top: 6px !important;
        }
    `;
    
    document.head.appendChild(style);
    
})();