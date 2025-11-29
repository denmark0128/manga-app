from django.shortcuts import render
from django.core.cache import cache
import requests
import hashlib

def home(request, series_id=None):
    # Get the current path
    path = request.path
    context = {}
    
    # Check if it's a series detail page
    if series_id:
        manga_detail = None
        error_message = None
        
        # Create cache key for detail page
        cache_key = f"manga_detail_{series_id}"
        cached_detail = cache.get(cache_key)
        
        if cached_detail:
            manga_detail = cached_detail
        else:
            try:
                print(f"Fetching manga details for ID: {series_id}")
                response = requests.get(
                    f'https://api.mangaupdates.com/v1/series/{series_id}',
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    manga_detail = response.json()
                    print(f"Successfully fetched: {manga_detail.get('title', 'Unknown')}")
                    
                    # Cache for 1 hour
                    cache.set(cache_key, manga_detail, 60 * 60)
                else:
                    error_message = f"API returned status {response.status_code}"
            except Exception as e:
                error_message = f"Error: {str(e)}"
                print(error_message)
        
        context = {
            'series_id': series_id,
            'manga': manga_detail,
            'error_message': error_message
        }
        
        if request.headers.get("HX-Request") == "true":
            return render(request, "src/series_detail/series_detail_partial.html", context)
        return render(request, "src/series_detail/series_detail.html", context)
    
    # Determine which template to use based on path
    if path == '/about/':
        template_name = 'about/about'
    elif path == '/contact/':
        template_name = 'contact/contact'
    elif path == '/series/':
        # Get search from URL or session
        search_query = request.GET.get('search', '').strip() or request.session.get('last_series_search', '')
        manga_results = []
        
        if search_query:
            # Save to session for later
            request.session['last_series_search'] = search_query
            
            # Create safe cache key using hash
            cache_key = f"manga_search_{hashlib.md5(search_query.lower().encode()).hexdigest()}"
            cached_results = cache.get(cache_key)
            
            if cached_results:
                manga_results = cached_results
            else:
                try:
                    response = requests.post(
                        'https://api.mangaupdates.com/v1/series/search',
                        json={'search': search_query},
                        headers={'Content-Type': 'application/json'}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        full_results = data.get('results', [])
                        
                        # Filter to only include needed fields
                        manga_results = [
                            {
                                'record': {
                                    'series_id': result['record']['series_id'],
                                    'title': result['record']['title'],
                                    'description': result['record'].get('description', ''),
                                    'image': result['record'].get('image', {})
                                }
                            }
                            for result in full_results
                        ]
                        
                        # Cache for 30 minutes
                        cache.set(cache_key, manga_results, 60 * 30)
                except Exception as e:
                    print(f"API Error: {e}")
        
        context = {
            'search_query': search_query,
            'manga_results': manga_results
        }
        template_name = 'series/series'
    elif path == '/upload/':
        template_name = 'upload/upload'
    else:
        template_name = 'home/home'
    
    # Check if it's an HTMX request
    if request.headers.get("HX-Request") == "true":
        return render(request, f"src/{template_name}_partial.html", context)
    
    return render(request, f"src/{template_name}.html", context)