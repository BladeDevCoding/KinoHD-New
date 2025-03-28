from flask import Flask, request, jsonify
from movie_search import search_movie_kinopoisk, create_direct_search_url
import urllib.parse

app = Flask(__name__)

@app.route('/search', methods=['GET'])
def search():
    movie_name = request.args.get('movie', '')
    if not movie_name:
        return jsonify({"error": "Не вказано назву фільму"}), 400
    
    # Шукаємо на Кінопошуку
    results = search_movie_kinopoisk(movie_name)
    
    # Якщо результатів немає, створюємо пряме посилання
    if not results:
        direct_url = create_direct_search_url(movie_name)
        results = [{
            "title": f"Пошук для: {movie_name}",
            "url": direct_url,
            "id": None,
            "is_direct_search": True
        }]
    
    return jsonify({
        "movie": movie_name,
        "results": results
    })

@app.route('/', methods=['GET'])
def home():
    return """
    <html>
        <head>
            <title>Пошук фільмів на sspoisk.ru</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                .form-group { margin-bottom: 15px; }
                input[type="text"] { width: 70%; padding: 8px; }
                button { padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
                #results { margin-top: 20px; }
                .result-item { margin-bottom: 15px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .result-title { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
                .loading { text-align: center; padding: 20px; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <h1>Пошук фільмів на sspoisk.ru</h1>
            <div class="form-group">
                <input type="text" id="movie-name" placeholder="Введіть назву фільму..." autofocus>
                <button onclick="searchMovie()">Пошук</button>
            </div>
            <div id="results"></div>
            
            <script>
                // Додаємо обробник Enter для поля вводу
                document.getElementById('movie-name').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        searchMovie();
                    }
                });
                
                function searchMovie() {
                    const movieName = document.getElementById('movie-name').value;
                    if (!movieName) return;
                    
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '<div class="loading">Шукаємо фільми...</div>';
                    
                    fetch(`/search?movie=${encodeURIComponent(movieName)}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.results && data.results.length > 0) {
                                let html = `<h2>Результати пошуку для "${data.movie}":</h2>`;
                                data.results.forEach((result, index) => {
                                    html += `
                                        <div class="result-item">
                                            <div class="result-title">${index + 1}. ${result.title || 'Без назви'}</div>
                                            <p><a href="${result.url}" target="_blank">${result.url}</a></p>
                                            ${result.id ? `<p>ID: ${result.id}</p>` : ''}
                                            ${result.is_direct_search ? '<p><em>Пряме посилання для пошуку</em></p>' : ''}
                                        </div>
                                    `;
                                });
                                resultsDiv.innerHTML = html;
                            } else {
                                resultsDiv.innerHTML = `<p>Нічого не знайдено для "${data.movie}"</p>`;
                            }
                        })
                        .catch(error => {
                            resultsDiv.innerHTML = `<p class="error">Помилка при пошуку: ${error.message}</p>`;
                        });
                }
            </script>
        </body>
    </html>
    """

@app.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({
        "name": "SSPoisk API",
        "version": "1.0.0",
        "description": "API для пошуку фільмів на sspoisk.ru",
        "endpoints": [
            {
                "path": "/search",
                "method": "GET",
                "params": {
                    "movie": "Назва фільму для пошуку"
                },
                "description": "Пошук фільмів за назвою"
            }
        ]
    })

if __name__ == '__main__':
    app.run(debug=True) 