import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import json

def search_movie_kinopoisk(movie_name):
    """
    Шукає фільм безпосередньо на Кінопошуку
    
    Args:
        movie_name (str): Назва фільму для пошуку
    
    Returns:
        list: Список результатів з посиланнями на sspoisk.ru
    """
    # Кодуємо назву фільму для URL
    encoded_query = urllib.parse.quote(movie_name)
    
    # Формуємо URL для пошуку на Кінопошуку
    search_url = f"https://www.kinopoisk.ru/index.php?kp_query={encoded_query}"
    
    # Заголовки для імітації браузера
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5,en;q=0.3",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Виконуємо запит до Кінопошуку
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        # Зберігаємо HTML для відлагодження
        with open("kinopoisk_results.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        # Парсимо HTML-відповідь
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # Шукаємо результати пошуку
        # Метод 1: Пошук через основні елементи результатів
        search_items = soup.find_all('p', class_='name')
        for item in search_items:
            a_tag = item.find('a')
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href')
                if href.startswith('/film/') or href.startswith('/series/') or href.startswith('/serial/'):
                    title = a_tag.text.strip()
                    # Формуємо повне посилання
                    full_kinopoisk_url = f"https://www.kinopoisk.ru{href}"
                    # Замінюємо на sspoisk.ru
                    sspoisk_url = full_kinopoisk_url.replace('kinopoisk.ru', 'sspoisk.ru')
                    results.append({
                        "title": title,
                        "url": sspoisk_url,
                        "id": extract_id_from_url(sspoisk_url)
                    })
        
        # Метод 2: Пошук через всі посилання
        if not results:
            for a_tag in soup.find_all('a'):
                href = a_tag.get('href', '')
                if href.startswith('/film/') or href.startswith('/series/') or href.startswith('/serial/'):
                    # Перевіряємо, чи містить посилання ID
                    if re.search(r'/(film|series|serial)/\d+', href):
                        title = a_tag.text.strip()
                        if not title:
                            # Якщо текст порожній, спробуємо знайти заголовок в батьківському елементі
                            parent = a_tag.find_parent('div')
                            if parent:
                                title_elem = parent.find('p', class_='name')
                                if title_elem:
                                    title = title_elem.text.strip()
                        
                        # Формуємо повне посилання
                        full_kinopoisk_url = f"https://www.kinopoisk.ru{href}"
                        # Замінюємо на sspoisk.ru
                        sspoisk_url = full_kinopoisk_url.replace('kinopoisk.ru', 'sspoisk.ru')
                        results.append({
                            "title": title or "Невідома назва",
                            "url": sspoisk_url,
                            "id": extract_id_from_url(sspoisk_url)
                        })
        
        # Видаляємо дублікати за URL
        unique_results = []
        seen_urls = set()
        for result in results:
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)
        
        return unique_results
    
    except requests.exceptions.RequestException as e:
        print(f"Помилка при виконанні запиту до Кінопошуку: {e}")
        return []

def search_movie_kinopoisk_api(movie_name):
    """
    Шукає фільм через неофіційний API Кінопошуку
    
    Args:
        movie_name (str): Назва фільму для пошуку
    
    Returns:
        list: Список результатів з посиланнями на sspoisk.ru
    """
    # Кодуємо назву фільму для URL
    encoded_query = urllib.parse.quote(movie_name)
    
    # Використовуємо неофіційний API Кінопошуку
    search_url = f"https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword?keyword={encoded_query}"
    
    # Заголовки для API
    headers = {
        "X-API-KEY": "ваш_api_ключ",  # Потрібно отримати ключ на https://kinopoiskapiunofficial.tech/
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        for item in data.get("films", []):
            film_id = item.get("filmId")
            title = item.get("nameRu") or item.get("nameEn") or "Невідома назва"
            year = item.get("year", "")
            
            # Формуємо посилання на Кінопошук
            kinopoisk_url = f"https://www.kinopoisk.ru/film/{film_id}/"
            # Замінюємо на sspoisk.ru
            sspoisk_url = kinopoisk_url.replace("kinopoisk.ru", "sspoisk.ru")
            
            results.append({
                "title": f"{title} ({year})" if year else title,
                "url": sspoisk_url,
                "id": str(film_id)
            })
        
        return results
    
    except requests.exceptions.RequestException as e:
        print(f"Помилка при виконанні запиту до API Кінопошуку: {e}")
        return []

def extract_id_from_url(url):
    """
    Витягує ID фільму/серіалу з URL
    """
    pattern = re.compile(r'/(film|series|serial)/(\d+)')
    match = pattern.search(url)
    if match:
        return match.group(2)
    return None

def create_direct_search_url(movie_name):
    """
    Створює пряме посилання для пошуку на sspoisk.ru
    """
    encoded_query = urllib.parse.quote(movie_name)
    return f"https://sspoisk.ru/index.php?kp_query={encoded_query}"

def main():
    movie_name = input("Введіть назву фільму для пошуку: ")
    
    print("Шукаємо на Кінопошуку...")
    results = search_movie_kinopoisk(movie_name)
    
    if results:
        print(f"\nЗнайдено {len(results)} результатів:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            if result['id']:
                print(f"   ID: {result['id']}")
            print()
    else:
        print("Результатів не знайдено через прямий пошук.")
        print("Створюємо пряме посилання для пошуку на sspoisk.ru...")
        direct_url = create_direct_search_url(movie_name)
        print(f"Пряме посилання: {direct_url}")

if __name__ == "__main__":
    main() 