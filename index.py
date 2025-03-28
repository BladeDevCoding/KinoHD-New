import json
import urllib.parse
import requests
import os
import time
import re
from http.server import BaseHTTPRequestHandler

# Перевіряємо, чи встановлено змінну середовища для API ключа
KINOPOISK_API_KEY = os.environ.get('KINOPOISK_API_KEY', '6ca43889-42a5-4ef4-8de7-ab98315826d3')

# Кеш для результатів пошуку
search_cache = {}
CACHE_EXPIRY = 3600  # 1 година в секундах

def search_movie_kinopoisk_api(movie_name):
    """
    Шукає фільм через неофіційний API Кінопошуку
    """
    # Перевіряємо кеш
    cache_key = movie_name.lower()
    current_time = time.time()
    
    if cache_key in search_cache:
        cache_entry = search_cache[cache_key]
        if current_time - cache_entry['timestamp'] < CACHE_EXPIRY:
            return cache_entry['results']
    
    try:
        # Кодуємо назву фільму для URL
        encoded_query = urllib.parse.quote(movie_name)
        
        # Використовуємо неофіційний API Кінопошуку
        search_url = f"https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword?keyword={encoded_query}"
        
        # Заголовки для API
        headers = {
            "X-API-KEY": KINOPOISK_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        for item in data.get("films", []):
            film_id = item.get("filmId")
            title = item.get("nameRu") or item.get("nameEn") or "Невідома назва"
            year = item.get("year", "")
            film_type = item.get("type", "").lower()
            
            # Визначаємо тип (фільм чи серіал)
            path_type = "film"
            if film_type in ["tv_series", "mini_series", "tv_show"]:
                path_type = "series"
            
            # Формуємо посилання на Кінопошук
            kinopoisk_url = f"https://www.kinopoisk.ru/{path_type}/{film_id}/"
            # Замінюємо на sspoisk.ru
            sspoisk_url = kinopoisk_url.replace("kinopoisk.ru", "sspoisk.ru")
            
            results.append({
                "title": f"{title} ({year})" if year else title,
                "url": sspoisk_url,
                "id": str(film_id),
                "year": year,
                "type": film_type
            })
        
        # Зберігаємо результати в кеш
        search_cache[cache_key] = {
            'results': results,
            'timestamp': current_time
        }
        
        return results
    
    except Exception as e:
        print(f"Помилка при виконанні запиту до API Кінопошуку: {e}")
        return []

def create_direct_search_url(movie_name):
    """
    Створює пряме посилання для пошуку на sspoisk.ru
    """
    encoded_query = urllib.parse.quote(movie_name)
    return f"https://sspoisk.ru/index.php?kp_query={encoded_query}"

# HTML шаблон для головної сторінки
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSPoisk - Пошук фільмів</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎬</text></svg>">
    <style>
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --accent-color: #e74c3c;
            --text-color: #333;
            --light-bg: #f5f5f5;
            --card-bg: #fff;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--light-bg);
            margin: 0;
            padding: 0;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background-color: var(--primary-color);
            color: white;
            padding: 1rem 0;
            text-align: center;
            margin-bottom: 2rem;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            margin: 0;
            font-size: 2.5rem;
        }
        
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.8;
            margin-top: 0.5rem;
        }
        
        .search-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 2rem;
        }
        
        .search-box {
            display: flex;
            width: 100%;
            max-width: 600px;
            margin-bottom: 1rem;
        }
        
        .search-input {
            flex: 1;
            padding: 12px 15px;
            font-size: 1rem;
            border: 2px solid #ddd;
            border-radius: 4px 0 0 4px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .search-input:focus {
            border-color: var(--secondary-color);
        }
        
        .search-button {
            background-color: var(--secondary-color);
            color: white;
            border: none;
            padding: 12px 20px;
            font-size: 1rem;
            cursor: pointer;
            border-radius: 0 4px 4px 0;
            transition: background-color 0.3s;
        }
        
        .search-button:hover {
            background-color: #2980b9;
        }
        
        .results-container {
            margin-top: 2rem;
        }
        
        .results-title {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--primary-color);
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: 0.5rem;
        }
        
        .result-card {
            background-color: var(--card-bg);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .result-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .result-title {
            font-size: 1.3rem;
            margin-top: 0;
            margin-bottom: 0.5rem;
            color: var(--primary-color);
        }
        
        .result-url {
            margin-bottom: 0.5rem;
        }
        
        .result-url a {
            color: var(--secondary-color);
            text-decoration: none;
            word-break: break-all;
        }
        
        .result-url a:hover {
            text-decoration: underline;
        }
        
        .result-id {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0;
        }
        
        .direct-search-note {
            font-style: italic;
            color: var(--accent-color);
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            font-size: 1.2rem;
            color: #666;
        }
        
        .error-message {
            background-color: #ffeaea;
            color: var(--accent-color);
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .no-results {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        
        footer {
            text-align: center;
            margin-top: 3rem;
            padding: 1rem 0;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid #ddd;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .search-box {
                flex-direction: column;
            }
            
            .search-input {
                border-radius: 4px;
                margin-bottom: 0.5rem;
            }
            
            .search-button {
                border-radius: 4px;
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>SSPoisk 🎬</h1>
            <div class="subtitle">Пошук фільмів та серіалів</div>
        </div>
    </header>
    
    <div class="container">
        <div class="search-container">
            <div class="search-box">
                <input type="text" id="movie-name" class="search-input" placeholder="Введіть назву фільму або серіалу..." autofocus>
                <button onclick="searchMovie()" class="search-button">Пошук</button>
            </div>
        </div>
        
        <div id="results" class="results-container"></div>
    </div>
    
    <footer>
        <div class="container">
            <p>© 2023 SSPoisk - Сервіс пошуку фільмів та серіалів</p>
            <p>Розроблено з ❤️ для українських користувачів</p>
        </div>
    </footer>
    
    <script>
        // Додаємо обробник Enter для поля вводу
        document.getElementById('movie-name').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchMovie();
            }
        });
        
        function searchMovie() {
            const movieName = document.getElementById('movie-name').value.trim();
            if (!movieName) return;
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">Шукаємо фільми та серіали...</div>';
            
            // Додаємо timestamp для запобігання кешуванню
            const timestamp = new Date().getTime();
            fetch(`/api/search?movie=${encodeURIComponent(movieName)}&_=${timestamp}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.results && data.results.length > 0) {
                        let html = `<h2 class="results-title">Результати пошуку для "${data.movie}":</h2>`;
                        data.results.forEach((result, index) => {
                            html += `
                                <div class="result-card">
                                    <h3 class="result-title">${index + 1}. ${result.title || 'Без назви'}</h3>
                                    <p class="result-url"><a href="${result.url}" target="_blank">${result.url}</a></p>
                                    ${result.id ? `<p class="result-id">ID: ${result.id}</p>` : ''}
                                    ${result.is_direct_search ? '<p class="direct-search-note">Пряме посилання для пошуку</p>' : ''}
                                </div>
                            `;
                        });
                        resultsDiv.innerHTML = html;
                    } else {
                        resultsDiv.innerHTML = `<div class="no-results">Нічого не знайдено для "${data.movie}"</div>`;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    resultsDiv.innerHTML = `<div class="error-message">Помилка при пошуку: ${error.message}</div>`;
                });
        }
        
        // Перевіряємо, чи є параметр movie в URL
        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            const movieParam = urlParams.get('movie');
            if (movieParam) {
                document.getElementById('movie-name').value = movieParam;
                searchMovie();
            }
        };
    </script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Парсимо URL
        path = self.path.split('?')[0]
        
        # Отримуємо параметри запиту
        query_params = {}
        if '?' in self.path:
            query_string = self.path.split('?')[1]
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = urllib.parse.unquote(value)
        
        # Обробляємо різні шляхи
        if path == '/api/search':
            self.handle_search(query_params)
        elif path == '/api/info':
            self.handle_info()
        elif path == '/health':
            self.handle_health()
        else:
            # Всі інші шляхи повертають головну сторінку
            self.handle_home()
    
    def handle_search(self, query_params):
        movie_name = query_params.get('movie', '')
        
        if not movie_name:
            self.send_error_response(400, {"error": "Не вказано назву фільму"})
            return
        
        # Шукаємо через API Кінопошуку
        results = search_movie_kinopoisk_api(movie_name)
        
        # Якщо результатів немає, створюємо пряме посилання
        if not results:
            direct_url = create_direct_search_url(movie_name)
            results = [{
                "title": f"Пошук для: {movie_name}",
                "url": direct_url,
                "id": None,
                "is_direct_search": True
            }]
        
        # Формуємо відповідь
        response = {
            "movie": movie_name,
            "results": results
        }
        
        self.send_json_response(200, response)
    
    def handle_info(self):
        info = {
            "name": "SSPoisk API",
            "version": "1.0.0",
            "description": "API для пошуку фільмів на sspoisk.ru",
            "endpoints": [
                {
                    "path": "/api/search",
                    "method": "GET",
                    "params": {
                        "movie": "Назва фільму для пошуку"
                    },
                    "description": "Пошук фільмів за назвою"
                },
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "Перевірка стану сервісу"
                }
            ]
        }
        
        self.send_json_response(200, info)
    
    def handle_health(self):
        health = {
            "status": "ok",
            "timestamp": time.time(),
            "service": "SSPoisk API",
            "version": "1.0.0"
        }
        
        self.send_json_response(200, health)
    
    def handle_home(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HOME_TEMPLATE.encode('utf-8'))
    
    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, status_code, error_data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))

def handler(event, context):
    return Handler(event, context) 