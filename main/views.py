from django.shortcuts import render
from django.core.cache import cache
from django.core.paginator import Paginator
import requests
import hashlib
import re

NSFW_KEYWORDS = {"hentai", "ecchi", "adult", "pornographic", "erotica","smut"}

def parse_markdown_links(text):
    """Convert markdown links to HTML links"""
    # Convert [text](url) to <a href="url">text</a>
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    replacement = r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>'
    return re.sub(pattern, replacement, text)


def is_nsfw(genres):
    return any(
        g.get("genre", "").lower() in NSFW_KEYWORDS
        for g in genres
    )

def home(request):
    """Home page view"""
    show_nsfw = request.session.get('show_nsfw', False)
    context = {'show_nsfw': show_nsfw}
    
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/home/home_partial.html", context)
    
    return render(request, "src/home/home.html", context)


def about(request):
    """About page view"""
    context = {}
    
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/about/about_partial.html", context)
    
    return render(request, "src/about/about.html", context)


def contact(request):
    """Contact page view"""
    context = {}
    
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/contact/contact_partial.html", context)
    
    return render(request, "src/contact/contact.html", context)


def upload(request):
    """Upload page view"""
    context = {}
    
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/upload/upload_partial.html", context)
    
    return render(request, "src/upload/upload.html", context)


def paper(request):
    """Paper page view"""
    context = {}
    
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/paper/paper_partial.html", context)
    
    return render(request, "src/paper/paper.html", context)

def author_list(request):
    """Author listing page with search functionality"""
    search_query = request.GET.get('search', '').strip()
    page_number = request.GET.get('page', 1)
    
    # Fall back to session if no search query
    if not search_query:
        search_query = request.session.get('last_author_search', '')
    
    page_obj = None
    
    if search_query:
        # Save to session for later
        request.session['last_author_search'] = search_query
        
        # Create base cache key
        search_hash = hashlib.md5(search_query.lower().encode()).hexdigest()
        
        # Try to get paginator metadata from cache
        paginator_cache_key = f"author_paginator_{search_hash}"
        cached_paginator_data = cache.get(paginator_cache_key)
        
        if cached_paginator_data:
            # We have cached paginator data
            num_pages = cached_paginator_data['num_pages']
            per_page = cached_paginator_data['per_page']
            total_count = cached_paginator_data['total_count']
            
            # Try to get this specific page from cache
            page_cache_key = f"author_page_{search_hash}_{page_number}"
            cached_page = cache.get(page_cache_key)
            
            if cached_page:
                # Create a mock page object with cached data
                page_obj = _create_cached_page(
                    cached_page['results'],
                    int(page_number),
                    num_pages,
                    per_page,
                    total_count,
                    cached_page['has_next'],
                    cached_page['has_previous']
                )
                print(f"Loaded page {page_number} from cache")
        
        # If not in cache, fetch from API
        if not page_obj:
            page_obj = _fetch_and_cache_author_search(search_query, page_number, search_hash)
    
    # Get NSFW setting from session (default to False)
    show_nsfw = request.session.get('show_nsfw', False)
    
    context = {
        'search_query': search_query,
        'author_results': page_obj.object_list if page_obj else [],
        'page_obj': page_obj,
        'show_nsfw': show_nsfw
    }
    
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/author/author_partial.html", context)
    
    return render(request, "src/author/author.html", context)


def series_list(request):
    """Series listing page with search functionality"""
    search_query = request.GET.get('search', '').strip()
    page_number = request.GET.get('page', 1)
    
    # Fall back to session if no search query
    if not search_query:
        search_query = request.session.get('last_series_search', '')
    
    page_obj = None
    
    if search_query:
        # Save to session for later
        request.session['last_series_search'] = search_query
        
        # Create base cache key
        search_hash = hashlib.md5(search_query.lower().encode()).hexdigest()
        
        # Try to get paginator metadata from cache
        paginator_cache_key = f"manga_paginator_{search_hash}"
        cached_paginator_data = cache.get(paginator_cache_key)
        
        if cached_paginator_data:
            # We have cached paginator data
            num_pages = cached_paginator_data['num_pages']
            per_page = cached_paginator_data['per_page']
            total_count = cached_paginator_data['total_count']
            
            # Try to get this specific page from cache
            page_cache_key = f"manga_page_{search_hash}_{page_number}"
            cached_page = cache.get(page_cache_key)
            
            if cached_page:
                # Create a mock page object with cached data
                page_obj = _create_cached_page(
                    cached_page['results'],
                    int(page_number),
                    num_pages,
                    per_page,
                    total_count,
                    cached_page['has_next'],
                    cached_page['has_previous']
                )
                print(f"Loaded page {page_number} from cache")
        
        # If not in cache, fetch from API
        if not page_obj:
            page_obj = _fetch_and_cache_series_search(search_query, page_number, search_hash)
    
    # Get NSFW setting from session (default to False)
    show_nsfw = request.session.get('show_nsfw', False)
    
    context = {
        'search_query': search_query,
        'manga_results': page_obj.object_list if page_obj else [],
        'page_obj': page_obj,
        'show_nsfw': show_nsfw
    }
    
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/series/series_partial.html", context)
    
    return render(request, "src/series/series.html", context)




def _fetch_manga_detail(series_id):
    """Fetch manga details from API and apply transformations"""
    manga_detail = None
    error_message = None

    cache_key = f"manga_detail_{series_id}"
    cached_detail = cache.get(cache_key)

    if cached_detail:
        print(f"Loading from cache for series {series_id}")
        manga_detail = cached_detail
    else:
        print(f"Fetching from API for series {series_id}")
        try:
            response = requests.get(
                f"https://api.mangaupdates.com/v1/series/{series_id}",
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                manga_detail = response.json()
                if manga_detail.get("description"):
                    manga_detail["description"] = parse_markdown_links(manga_detail["description"])
                print(f"API Response keys: {manga_detail.keys() if manga_detail else 'None'}")
                print(f"Has description: {'description' in manga_detail if manga_detail else False}")
                cache.set(cache_key, manga_detail, 60 * 60)
            else:
                error_message = f"API returned {response.status_code}"
        except Exception as e:
            error_message = str(e)

    # ✅ CLEAN AUTHORS HERE
    if manga_detail and "authors" in manga_detail:
        seen = set()
        manga_detail["authors_clean"] = []

        for a in manga_detail["authors"]:
            if a["type"] == "Author" and a["author_id"] not in seen:
                seen.add(a["author_id"])
                manga_detail["authors_clean"].append({
                    "id": a["author_id"],
                    "name": a["name"]
                })

    return manga_detail, error_message

def series_detail(request, series_id):
    """Series detail page - check cache, load skeleton or content directly"""
    context = {
        "series_id": series_id,
    }
    
    # Check if data is cached
    cache_key = f"manga_detail_{series_id}"
    
    if cache.get(cache_key):
        # Data is cached, fetch and render directly
        manga_detail, error_message = _fetch_manga_detail(series_id)
        show_nsfw = request.session.get('show_nsfw', False)
        
        context.update({
            "manga": manga_detail,
            "error_message": error_message,
            "show_nsfw": show_nsfw
        })
        
        # If HTMX request, return the partial
        if request.headers.get("HX-Request") == "true":
            return render(request, "src/series_detail/series_detail_partial.html", context)
        
        # Full page load with cached content - render full page with partial directly
        return render(request, "src/series_detail/series_detail_full.html", context)
    
    # Data not cached, show skeleton
    # If HTMX request, return just the skeleton without base template
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/series_detail/series_detail_skeleton.html", context)
    
    return render(request, "src/series_detail/series_detail.html", context)

def series_detail_content(request, series_id):
    """Lazy load series detail content via HTMX - fetches from API"""
    manga_detail, error_message = _fetch_manga_detail(series_id)
    
    print(f"Final context - manga exists: {manga_detail is not None}, has description: {'description' in manga_detail if manga_detail else False}")
    
    # Get NSFW setting from session (default to False)
    show_nsfw = request.session.get('show_nsfw', False)
    
    context = {
        "series_id": series_id,
        "manga": manga_detail,
        "error_message": error_message,
        "show_nsfw": show_nsfw
    }

    return render(request, "src/series_detail/series_detail_partial.html", context)

def toggle_nsfw(request):
    """Toggle NSFW content visibility"""
    show_nsfw = request.session.get('show_nsfw', False)
    request.session['show_nsfw'] = not show_nsfw
    
    # If it's an HTMX request, return the series partial to refresh the results
    if request.headers.get("HX-Request") == "true":
        # Get current search params
        search_query = request.GET.get('search', '').strip() or request.session.get('last_series_search', '')
        page_number = request.GET.get('page', 1)
        
        # Reuse the same logic from series_list
        page_obj = None
        if search_query:
            search_hash = hashlib.md5(search_query.lower().encode()).hexdigest()
            paginator_cache_key = f"manga_paginator_{search_hash}"
            cached_paginator_data = cache.get(paginator_cache_key)
            
            if cached_paginator_data:
                page_cache_key = f"manga_page_{search_hash}_{page_number}"
                cached_page = cache.get(page_cache_key)
                
                if cached_page:
                    page_obj = _create_cached_page(
                        cached_page['results'],
                        int(page_number),
                        cached_paginator_data['num_pages'],
                        cached_paginator_data['per_page'],
                        cached_paginator_data['total_count'],
                        cached_page['has_next'],
                        cached_page['has_previous']
                    )
            
            if not page_obj:
                page_obj = _fetch_and_cache_series_search(search_query, page_number, search_hash)
        
        context = {
            'search_query': search_query,
            'manga_results': page_obj.object_list if page_obj else [],
            'page_obj': page_obj,
            'show_nsfw': not show_nsfw
        }
        
        return render(request, "src/series/series_partial.html", context)
    
    # Fallback for non-HTMX requests
    return render(request, "components/navbar.html", {'show_nsfw': not show_nsfw})

def _fetch_author_detail(author_id):
    """Fetch author details and series from API"""
    cache_key = f"author_detail_{author_id}"
    series_cache_key = f"author_series_{author_id}"
    
    author = cache.get(cache_key)
    author_series = cache.get(series_cache_key)
    error_message = None

    # Fetch author details
    if not author:
        try:
            response = requests.get(
                f"https://api.mangaupdates.com/v1/authors/{author_id}",
                timeout=10
            )

            print(f"Author API Status code: {response.status_code}")

            if response.status_code == 200:
                author = response.json()
                cache.set(cache_key, author, 60*60)
            elif response.status_code == 404:
                error_message = "Author not found"
            else:
                error_message = f"API returned {response.status_code}"
        except Exception as e:
            error_message = str(e)
            print(f"Author API Error: {e}")
    
    if author and not author_series:
        try:
            print(f"Fetching series for author {author_id}")
            response = requests.post(
                f"https://api.mangaupdates.com/v1/authors/{author_id}/series",
                json={}, 
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            print(f"Series API Status code: {response.status_code}")

            if response.status_code == 200:
                author_series = response.json()
                print(f"Found {author_series.get('total_series', 0)} series")
                cache.set(series_cache_key, author_series, 60*60)
            else:
                print(f"Series API returned {response.status_code}")
                print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"Error fetching author series: {e}")
            author_series = None

    return author, author_series, error_message

def author_detail(request, author_id):
    """Author detail page - check cache, load skeleton or content directly"""
    context = {
        "author_id": author_id,
    }
    
    # Check if data is cached
    cache_key = f"author_detail_{author_id}"
    series_cache_key = f"author_series_{author_id}"
    
    if cache.get(cache_key) and cache.get(series_cache_key):
        # Both data is cached, fetch and render directly
        author, author_series, error_message = _fetch_author_detail(author_id)
        show_nsfw = request.session.get('show_nsfw', False)
        
        context.update({
            "author": author,
            "author_series": author_series,
            "error_message": error_message,
            "show_nsfw": show_nsfw
        })
        
        # If HTMX request, return the partial
        if request.headers.get("HX-Request") == "true":
            return render(request, "src/author_detail/author_detail_partial.html", context)
        
        # Full page load with cached content - render full page with partial directly
        return render(request, "src/author_detail/author_detail_full.html", context)
    
    # Data not cached, show skeleton
    # If HTMX request, return just the skeleton without base template
    if request.headers.get("HX-Request") == "true":
        return render(request, "src/author_detail/author_detail_skeleton.html", context)
    
    return render(request, "src/author_detail/author_detail.html", context)

def author_detail_content(request, author_id):
    """Lazy load author detail content via HTMX - fetches from API"""
    author, author_series, error_message = _fetch_author_detail(author_id)

    show_nsfw = request.session.get('show_nsfw', False)

    context = {
        "author_id": author_id,
        "author": author,
        "author_series": author_series,
        "error_message": error_message,
        "show_nsfw": show_nsfw
    }   

    return render(request, "src/author_detail/author_detail_partial.html", context)






# Helper functions

def _create_cached_page(object_list, number, num_pages, per_page, total_count, has_next, has_previous):
    """Create a mock page object from cached data"""
    class CachedPage:
        def __init__(self, object_list, number, num_pages, has_next, has_previous):
            self.object_list = object_list
            self.number = number
            self.has_next = lambda: has_next
            self.has_previous = lambda: has_previous
            self.next_page_number = lambda: number + 1 if has_next else None
            self.previous_page_number = lambda: number - 1 if has_previous else None
            
            class MockPaginator:
                def __init__(self, num_pages, per_page, count):
                    self.num_pages = num_pages
                    self.per_page = per_page
                    self.count = count
            
            self.paginator = MockPaginator(num_pages, per_page, total_count)
        
        def has_other_pages(self):
            return self.paginator.num_pages > 1
    
    return CachedPage(object_list, number, num_pages, has_next, has_previous)


def _fetch_and_cache_series_search(search_query, page_number, search_hash):
    """Fetch series search results from API and cache them"""
    try:
        print(f"Fetching from API for search: {search_query}")
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
                        'series_id': (result.get('record') or {}).get('series_id'),
                        'title': (result.get('record') or {}).get('title'),
                        'description': (result.get('record') or {}).get('description', ''),
                        'image': (result.get('record') or {}).get('image', {}),
                        'genres': (result.get('record') or {}).get('genres') or [],
                        'is_nsfw': False if not (result.get('record') or {}).get('genres') else is_nsfw((result.get('record') or {}).get('genres')),
                    }
                }
                for result in full_results
                if result.get('record')
            ]
      
            # Paginate results
            per_page = 20
            paginator = Paginator(manga_results, per_page)
            page_obj = paginator.get_page(page_number)
            
            # Cache paginator metadata
            paginator_data = {
                'num_pages': paginator.num_pages,
                'per_page': per_page,
                'total_count': paginator.count
            }
            paginator_cache_key = f"manga_paginator_{search_hash}"
            cache.set(paginator_cache_key, paginator_data, 60 * 30)
            
            # Cache each page separately
            for page_num in paginator.page_range:
                page = paginator.get_page(page_num)
                page_data = {
                    'results': list(page.object_list),
                    'has_next': page.has_next(),
                    'has_previous': page.has_previous()
                }
                page_cache_key = f"manga_page_{search_hash}_{page_num}"
                cache.set(page_cache_key, page_data, 60 * 30)
            
            print(f"Cached {paginator.num_pages} pages for search: {search_query}")
            return page_obj
            
    except Exception as e:
        print(f"API Error: {e}")
        return None


def _fetch_and_cache_author_search(search_query, page_number, search_hash):
    """Fetch author search results from API and cache them"""
    try:
        print(f"Fetching from API for author search: {search_query}")
        response = requests.post(
            'https://api.mangaupdates.com/v1/authors/search',
            json={'search': search_query},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            full_results = data.get('results', [])
            
            # Filter to only include needed fields
            author_results = [
                {
                    'record': {
                        'author_id': (result.get('record') or {}).get('id'),
                        'name': (result.get('record') or {}).get('name'),
                    }
                }
                for result in full_results
                if result.get('record')
            ]
      
            # Paginate results
            per_page = 20
            paginator = Paginator(author_results, per_page)
            page_obj = paginator.get_page(page_number)
            
            # Cache paginator metadata
            paginator_data = {
                'num_pages': paginator.num_pages,
                'per_page': per_page,
                'total_count': paginator.count
            }
            paginator_cache_key = f"author_paginator_{search_hash}"
            cache.set(paginator_cache_key, paginator_data, 60 * 30)
            
            # Cache each page separately
            for page_num in paginator.page_range:
                page = paginator.get_page(page_num)
                page_data = {
                    'results': list(page.object_list),
                    'has_next': page.has_next(),
                    'has_previous': page.has_previous()
                }
                page_cache_key = f"author_page_{search_hash}_{page_num}"
                cache.set(page_cache_key, page_data, 60 * 30)
            
            print(f"Cached {paginator.num_pages} pages for author search: {search_query}")
            return page_obj
            
    except Exception as e:
        print(f"Author API Error: {e}")
        return None