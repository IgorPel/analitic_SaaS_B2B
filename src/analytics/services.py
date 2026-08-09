from django.core.cache import cache
from .analytic_func import revenue as revenue, ltv, analyze_sales

# Імпорти інших твоїх модулів...

def get_cached_revenue(store_id, start_date=None, end_date=None):
    # 1. Формуємо унікальний ключ
    cache_key = f"revenue_{store_id}_{start_date}_{end_date}"
    
    # 2. Перевіряємо, чи є дані в Redis
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        # Cache Hit: Дані знайдені! Повертаємо їх миттєво, не чіпаючи PostgreSQL
        return cached_data
        
    # 3. Cache Miss: Даних немає. Викликаємо нашу важку функцію ORM (яку ми писали раніше)
    # Зверни увагу: QuerySet треба виконати (наприклад, перетворити в list), 
    # бо сам по собі "лінивий" QuerySet в Redis не покладеш.
    db_result = list(revenue(store_id, start_date, end_date))
    
    # 4. Зберігаємо результат у Redis на 15 хвилин (900 секунд)
    cache.set(cache_key, db_result, timeout=900)
    
    return db_result


def get_cached_ltv(store_id, start_date=None, end_date=None):
    cache_key = f"revenue_{store_id}_{start_date}_{end_date}"
    
    # 2. Перевіряємо, чи є дані в Redis
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        # Cache Hit: Дані знайдені! Повертаємо їх миттєво, не чіпаючи PostgreSQL
        return cached_data
        
    # 3. Cache Miss: Даних немає. Викликаємо нашу важку функцію ORM (яку ми писали раніше)
    # Зверни увагу: QuerySet треба виконати (наприклад, перетворити в list), 
    # бо сам по собі "лінивий" QuerySet в Redis не покладеш.
    db_result = list(ltv(store_id, start_date, end_date))
    
    # 4. Зберігаємо результат у Redis на 15 хвилин (900 секунд)
    cache.set(cache_key, db_result, timeout=900)
    
    return db_result

def get_cached_sales(store_id, product, start_date=None, end_date=None):
    cache_key = f"revenue_{store_id}_{start_date}_{end_date}"
    
    # 2. Перевіряємо, чи є дані в Redis
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        # Cache Hit: Дані знайдені! Повертаємо їх миттєво, не чіпаючи PostgreSQL
        return cached_data
        
    # 3. Cache Miss: Даних немає. Викликаємо нашу важку функцію ORM (яку ми писали раніше)
    # Зверни увагу: QuerySet треба виконати (наприклад, перетворити в list), 
    # бо сам по собі "лінивий" QuerySet в Redis не покладеш.
    db_result = list(analyze_sales(store_id, product, start_date, end_date))
    
    # 4. Зберігаємо результат у Redis на 15 хвилин (900 секунд)
    cache.set(cache_key, db_result, timeout=900)
    
    return db_result