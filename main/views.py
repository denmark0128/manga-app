from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from django.shortcuts import render
import requests

def home(request, paper_id=None):
    # Get the current path
    path = request.path
    context = {}
    
    # Check if it's a paper detail page
    if paper_id:
        manga_detail = None
        error_message = None
        
        try:
            print(f"Fetching manga details for ID: {paper_id}")
            response = requests.get(
                f'https://api.mangaupdates.com/v1/series/{paper_id}',
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                manga_detail = response.json()
                print(f"Successfully fetched: {manga_detail.get('title', 'Unknown')}")
            else:
                error_message = f"API returned status {response.status_code}"
        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(error_message)
        
        context = {
            'paper_id': paper_id,
            'manga': manga_detail,
            'error_message': error_message
        }
        
        if request.headers.get("HX-Request") == "true":
            return render(request, "src/paper_detail/paper_detail_partial.html", context)
        return render(request, "src/paper_detail/paper_detail.html", context)
    
    # Determine which template to use based on path
    if path == '/about/':
        template_name = 'about/about'
    elif path == '/contact/':
        template_name = 'contact/contact'
    elif path == '/paper/':
    # Get search from URL or session
        search_query = request.GET.get('search', '') or request.session.get('last_paper_search', '')
        manga_results = []
        
        if search_query:
            # Save to session for later
            request.session['last_paper_search'] = search_query
            
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
            except Exception as e:
                print(f"API Error: {e}")
        
        context = {
            'search_query': search_query,
            'manga_results': manga_results
        }
        template_name = 'paper/paper'
    elif path == '/upload/':
        template_name = 'upload/upload'
    else:
        template_name = 'home/home'
    
    # Check if it's an HTMX request
    if request.headers.get("HX-Request") == "true":
        return render(request, f"src/{template_name}_partial.html", context)
    
    return render(request, f"src/{template_name}.html", context)