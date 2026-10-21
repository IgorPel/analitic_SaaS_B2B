from django.core.cache import cache
from .analytic_func import revenue as revenue, ltv, analyze_sales


def get_cached_revenue(store_id, start_date=None, end_date=None):

    cache_key = f"revenue_{store_id}_{start_date}_{end_date}"


    cached_data = cache.get(cache_key)

    if cached_data is not None:

        return cached_data


    db_result = list(revenue(store_id, start_date, end_date))


    cache.set(cache_key, db_result, timeout=900)

    return db_result


def get_cached_ltv(store_id, start_date=None, end_date=None):
    cache_key = f"revenue_{store_id}_{start_date}_{end_date}"


    cached_data = cache.get(cache_key)

    if cached_data is not None:

        return cached_data


    db_result = list(ltv(store_id, start_date, end_date))


    cache.set(cache_key, db_result, timeout=900)

    return db_result

def get_cached_sales(store_id, product, start_date=None, end_date=None):
    cache_key = f"revenue_{store_id}_{start_date}_{end_date}"


    cached_data = cache.get(cache_key)

    if cached_data is not None:

        return cached_data


    db_result = list(analyze_sales(store_id, product, start_date, end_date))


    cache.set(cache_key, db_result, timeout=900)

    return db_result
