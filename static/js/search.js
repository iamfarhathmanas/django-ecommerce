/**
 * Enhanced search with auto-suggest and debouncing
 */
(function() {
    'use strict';

    const SearchEnhancer = {
        init: function() {
            const searchInput = document.getElementById('search-input') || document.querySelector('input[name="q"]');
            if (!searchInput) return;

            this.searchInput = searchInput;
            this.suggestionsContainer = this.createSuggestionsContainer();
            this.debounceTimer = null;
            this.currentQuery = '';

            this.attachEvents();
        },

        createSuggestionsContainer: function() {
            const container = document.createElement('div');
            container.id = 'search-suggestions';
            container.className = 'search-suggestions dropdown-menu';
            container.style.display = 'none';
            this.searchInput.parentElement.style.position = 'relative';
            this.searchInput.parentElement.appendChild(container);
            return container;
        },

        attachEvents: function() {
            this.searchInput.addEventListener('input', (e) => {
                this.handleInput(e.target.value);
            });

            this.searchInput.addEventListener('focus', () => {
                if (this.currentQuery) {
                    this.showSuggestions(this.currentQuery);
                }
            });

            document.addEventListener('click', (e) => {
                if (!this.searchInput.contains(e.target) && 
                    !this.suggestionsContainer.contains(e.target)) {
                    this.hideSuggestions();
                }
            });

            // Handle keyboard navigation
            this.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
                    this.handleKeyboard(e);
                }
            });
        },

        handleInput: function(query) {
            query = query.trim();
            this.currentQuery = query;

            clearTimeout(this.debounceTimer);

            if (query.length < 2) {
                this.hideSuggestions();
                return;
            }

            this.debounceTimer = setTimeout(() => {
                this.fetchSuggestions(query);
            }, 300); // 300ms debounce
        },

        fetchSuggestions: function(query) {
            const url = `/search-suggestions/?q=${encodeURIComponent(query)}&limit=5`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    this.displaySuggestions(data.results || []);
                })
                .catch(error => {
                    console.error('Search suggestions error:', error);
                });
        },

        displaySuggestions: function(suggestions) {
            if (suggestions.length === 0) {
                this.hideSuggestions();
                return;
            }

            this.suggestionsContainer.innerHTML = suggestions.map(item => {
                const matchClass = item.match_type || '';
                return `
                    <a href="/products/${item.slug}/" class="dropdown-item search-suggestion ${matchClass}">
                        <strong>${this.highlightMatch(item.title, this.currentQuery)}</strong>
                    </a>
                `;
            }).join('');

            this.showSuggestions();
        },

        highlightMatch: function(text, query) {
            if (!query) return text;
            const regex = new RegExp(`(${query})`, 'gi');
            return text.replace(regex, '<mark>$1</mark>');
        },

        showSuggestions: function() {
            this.suggestionsContainer.style.display = 'block';
        },

        hideSuggestions: function() {
            this.suggestionsContainer.style.display = 'none';
        },

        handleKeyboard: function(e) {
            const items = this.suggestionsContainer.querySelectorAll('.search-suggestion');
            const current = this.suggestionsContainer.querySelector('.search-suggestion.active');
            let index = Array.from(items).indexOf(current);

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                index = (index + 1) % items.length;
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                index = index <= 0 ? items.length - 1 : index - 1;
            } else if (e.key === 'Enter' && current) {
                e.preventDefault();
                current.click();
                return;
            }

            items.forEach(item => item.classList.remove('active'));
            if (items[index]) {
                items[index].classList.add('active');
            }
        }
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => SearchEnhancer.init());
    } else {
        SearchEnhancer.init();
    }
})();

