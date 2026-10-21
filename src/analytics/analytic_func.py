import bisect
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .models import Customer, Order, OrderItem

from django.db import models
from django.db.models import Func, Max, Min, Sum, Avg, Count, Window, F, QuerySet, OuterRef, Subquery, IntegerField, ExpressionWrapper
from django.db.models.functions import TruncDay, TruncMonth, ExtractYear, ExtractMonth
from django.forms.models import model_to_dict
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class NestedSum(Func):
    function = 'SUM'
    window_compatible = True


def find_nearest_index(data, target_value, key):

    some = [r[key] for r in data]
    return bisect.bisect_left(some, target_value)


def DefaultValue(default_value, type_value, **kwards):
    return type_value(default_value)


def DefaultValueLeft(key_fill, data, default_value, type_value, target_key, **kwards):

    index = find_nearest_index(data, key_fill['value'], key_fill['key'])

    if index > 0:
        return data[index - 1][target_key]
    else:
        return type_value(default_value)

def DefaultValueRight(key_fill, data, target_key, **kwargs):

    if len(data) == 0:
        raise IndexError

    index = find_nearest_index(data, key_fill['value'], key_fill['key'])
    if index < len(data):
        return data[index][target_key]
    else:
        return data[-1][target_key]


def quick_print(message):
    print(message, flush=True)

class BasicAnalytics(ABC):

    _result : QuerySet = None
    _listed_result : List[Dict] = None
    _table : models.Model = None
    _standart_pre_values : List[str] = []
    _standart_post_values : List[str] = []
    _standart_order : List[str] = []
    _additional_cols : List[str] = []
    _format_map : dict[str, Tuple[str, callable]] = None
    _graphs : str = None
    _x_axis : str = None


    _pre_pipeline : List[str] = ['_pre_stories', '_pre_statuses', '_pre_dates', '_pre_values', '_pre_group_and_limit']
    _post_pipeline : List[str] = ['_post_order_by', '_post_limit', '_post_listed_result', '_post_fill_gaps']


    def _format_graph_key(self, value):
        """Базовий метод форматування ключа (за замовчуванням повертає як є)"""
        return str(value)

    def _pre_values(self):
        quick_print("VALUES")
        self.status_print("Before")
        if self.fields:
            base_fields = self.possible_fields()
            for field in self.fields:
                if field not in base_fields:
                    print("ERROR FIELD", flush=True)
                    return
            self._result = self._result.values(*self.fields)
        else:
            self._result = self._result.values(*self._pre_standart_values)
        self.status_print("After")


    def _post_listed_result(self):
        quick_print(f'List Result:|{self.__class__}|')
        if self.__class__ == "src.analytics.analytic_func.LTV":
            for it in self._result:
                quick_print(list(it))
            quick_print("Parametrs: ")
            quick_print(self.__dict__)
        self._listed_result = list(self._result.values(*self._post_standart_values)) if self._result is not None else None


    def status_print(self, message: str = ""):

        if self.__class__.__name__ != 'LTV':
            return

        quick_print("=" * 60)
        quick_print(f"[STATUS DEBUG] {message} (Class: {self.__class__.__name__})")
        quick_print("=" * 60)


        quick_print("--- Parameters ---")
        clean_params = {
            k: v for k, v in self.__dict__.items()
            if k not in ('_result', '_listed_result')
        }
        for param, val in clean_params.items():
            quick_print(f"  {param}: {val}")


        if self._result is not None:
            quick_print("\n--- Result (_result) ---")
            try:

                if hasattr(self._result, 'first'):
                    sample = self._result.first()
                elif isinstance(self._result, (list, tuple)) and self._result:
                    sample = self._result[0]
                else:
                    sample = None

                quick_print(f"  Type: {type(self._result)}")
                quick_print(f"  Sample row: {sample}")
            except Exception as e:
                quick_print(f"  Error reading _result: {e}")


        if self._listed_result is not None:
            quick_print(f"\n--- Listed Result (_listed_result: {len(self._listed_result)} items) ---")
            for item in self._listed_result:
                quick_print(f"  {item}")

        quick_print("=" * 60 + "\n")

    def _run_methods_by_prefix(self, prefix: str):
        methods = self._pre_pipeline if prefix == '_pre_' else self._post_pipeline
        for method_name in methods:
            method = getattr(self, method_name, None)
            if callable(method):
                method()


    def __init__(self, **kwards):

        quick_print(f'Initializing {self.__class__.__name__} with parameters: {kwards}')
        self.stores = kwards.pop('stores_id', None)
        self.statuses = kwards.pop('statuses', None)
        self.start_date = kwards.pop('start_date', None)
        self.end_date = kwards.pop('end_date', None)
        self.fields = kwards.pop('fields', None)
        self.orders_by = kwards.pop('orders_by', None)
        self.limit = kwards.pop('limits', None)
        self.fill_blank = kwards.pop('fill_blank', False)
        self.final_limit = kwards.pop('final_limit', None)
        self.group_and_limit = kwards.pop('group_and_limit', None)
        self._extra_params = kwards

    @classmethod
    def _get_right(self, raw, key):
        match key:
            case 'days':
                return raw.get('days') if isinstance(raw, dict) else getattr(raw, 'days', None)
            case 'revenue':
                return raw.get('revenue') if isinstance(raw, dict) else getattr(raw, 'revenue', None)
            case 'cumulative_revenue':
                return raw.get('cumulative_revenue') if isinstance(raw, dict) else getattr(raw, 'cumulative_revenue', None)
            case 'total_price':
                return raw.get('total_price') if isinstance(raw, dict) else getattr(raw, 'total_price', None)
            case 'customer':
                return Customer.objects.get(id=raw).email if raw is not None and Customer.objects.filter(id=raw).exists() else "Unknown_Customer"
            case _:
                return raw.get(key) if isinstance(raw, dict) else getattr(raw, key, None)

    @classmethod
    def formulating_raw(cls, raw_data, format_map, multiple: Tuple[str, str, callable] = None):
        json = []
        for row in raw_data:
            formulated_row = {}
            if multiple is not None:

                key_name = multiple[1]
                raw_graph_val = row.get(key_name) if isinstance(row, dict) else getattr(row, key_name, None)


                formatted_graph_val = multiple[2](key_name, raw_graph_val) if multiple[2] else str(raw_graph_val)
            else:
                formatted_graph_val = None

            for json_key, (db_key, formatter) in format_map.items():
                raw_value = row.get(db_key) if isinstance(row, dict) else getattr(row, db_key, None)
                final_json_key = f'{formatted_graph_val}/{json_key}' if multiple is not None and db_key != multiple[0] else json_key
                formulated_row[final_json_key] = formatter(raw_value) if raw_value is not None else f'Error to {db_key}: 404'

            json.append(formulated_row)
        return json


    def _post_fill_gaps(self):
        if not self.fill_blank or self._listed_result is None or len(self._listed_result) == 0:
            return

        key_field = self.fill_blank['key']
        unique_field = self.fill_blank['uniques']

        funce = {'timedelta': timedelta, 'float': float, 'int': int}
        types = {key: type(value) for key, value in self._listed_result[0].items() if value is not None}
        func, per, value = self.fill_blank['delta']['func'], self.fill_blank['delta']['per'], self.fill_blank['delta']['value']
        is_date = self.fill_blank.get('data_type') == 'date'
        to_fill = []

        delta = funce[func](**{per: value}) if is_date else funce[func](value)

        if self.fill_blank['method'] == 'AtoZ':
            start = datetime.fromisoformat(self.fill_blank['start']).replace(tzinfo=timezone.utc) if is_date else self.fill_blank['start']
            end = datetime.fromisoformat(self.fill_blank['end']).replace(tzinfo=timezone.utc) if is_date else self.fill_blank['end']
            while start <= end:
                to_fill.append(start)
                start += delta
        elif self.fill_blank['method'] == 'in_container':
            res = self._result.values(key_field).distinct()
            to_fill = list(res.values_list(key_field, flat=True))

        uniques = set(self._result.values_list(unique_field, flat=True).distinct())
        unique_data = defaultdict(list)
        som = defaultdict(set)

        for row in self._listed_result:
            unique_value = row[unique_field]
            key_value = row[key_field]

            som[key_value].add(unique_value)
            unique_data[unique_value].append(row)


        for u in unique_data:
            unique_data[u].sort(key=lambda r: r[key_field])

        defaults_funcs = {
            'DefaultValue': DefaultValue,
            'DefaultValueLeft': DefaultValueLeft,
            'DefaultValueRight': DefaultValueRight
        }

        for item in to_fill:
            not_present_uniques = uniques - som[item]
            for unique in not_present_uniques:
                new_row = {key_field: item, unique_field: unique}
                for key, (default_func, default_value) in self.fill_blank['to_fill'].items():
                    new_row[key] = defaults_funcs[default_func](
                        key_fill={'key': key_field, 'value': item},
                        data=unique_data[unique],
                        default_value=default_value,
                        type_value=types.get(key, float),
                        target_key=key
                    )
                self._listed_result.append(new_row)
                unique_data[unique].append(new_row)
                unique_data[unique].sort(key=lambda r: r[key_field])


        self._listed_result.sort(key=lambda r: r[key_field])


    def modificator_decorater(func):
        def wrapper(self, *args, **kwards):

            self._result = self._table.objects.all()

            self._run_methods_by_prefix('_pre_')

            if not self._result.exists():
                return None

            func(self, *args, **kwards)

            if self._result is not None:
                self._run_methods_by_prefix('_post_')

            return self._result

        return wrapper

    @abstractmethod
    @modificator_decorater
    def func(self, **kwards) -> QuerySet:
        pass


    def formulating(self, format_map=None, graphs=None, x_axis=None, **kwards):
        if isinstance(graphs, str):
            graphs = graphs.strip('"\'')

        graphs = graphs if graphs is not None else self._graphs
        format_map = format_map if format_map is not None else self._format_map
        x_axis = x_axis if x_axis is not None else self._x_axis

        if not self._result.exists() and not self._listed_result:
            return []

        final_json = []
        if graphs is not None and graphs != "No":
            grouped_data = defaultdict(list)
            data_source = self._listed_result if self._listed_result else self._result

            for row in data_source:
                x_val = row.get(x_axis) if isinstance(row, dict) else getattr(row, x_axis, None)
                grouped_data[x_val].append(row)


            formatter_func = getattr(self, '_format_graph_key', lambda k, v: str(v))

            for graph, rows in grouped_data.items():
                to_add = self.formulating_raw(rows, format_map, (x_axis, graphs, formatter_func))
                merged = {}
                for item in to_add:
                    merged.update(item)
                final_json.append(merged)
        else:
            data_source = self._listed_result if self._listed_result else self._result
            final_json = self.formulating_raw(data_source, format_map)

        if self.final_limit:
            final_json = final_json[:self.final_limit]

        return final_json


    def _pre_stories(self):
        if self.stores:
            self._result = self._result.filter(store_id__in=self.stores)

    def _pre_statuses(self):
        if self.statuses:
            self._result = self._result.filter(status__in=self.statuses)
        else:
            self._result = self._result.filter(status=Order.Status.COMPLETED)

    def _pre_dates(self):
        self._result = self._result.within_dates(self.start_date, self.end_date)

    def _post_order_by(self):
        if self.orders_by:
            base_fields = self.possible_fields()
            for field in self.orders_by:
                if field not in base_fields:
                    print("ERROR FIELD", flush=True)
                    return
            self._result = self._result.order_by(*self.orders_by)
        elif hasattr(self, '_standart_order'):
            self._result = self._result.order_by(*self._standart_order)

    def _post_limit(self):
        if self.limit and isinstance(self.limit, int) and self.limit > 0:
            self._result = self._result[:self.limit]

    def _pre_group_and_limit(self):
        if not hasattr(self, 'group_and_limit') or not self.group_and_limit:
            return

        limit = self.group_and_limit.get('limit')
        group_by = self.group_and_limit.get('group_by', {})
        re_order_by = self.group_and_limit.get('order_by', [])

        if not group_by:
            return

        if isinstance(re_order_by, str):
            re_order_by = [re_order_by]

        values_fields = []
        annotate_fields = {}
        funce = {'Sum': Sum, 'Avg': Avg, 'Count': Count, 'Max': Max, 'Min': Min, 'F': F}

        for field, func in group_by.items():
            if func == 'F':
                values_fields.append(field)
            elif func in funce:
                annotate_fields[f'{field}_{func.lower()}'] = funce[func](field)

        if not values_fields:
            return

        main_group_field = values_fields[0]

        top_qs = self._result.values(main_group_field).annotate(**annotate_fields)

        if re_order_by:
            top_qs = top_qs.order_by(*re_order_by)

        if limit:
            top_qs = top_qs[:limit]

        top_ids = list(top_qs.values_list(main_group_field, flat=True))
        self._result = self._result.filter(**{f"{main_group_field}__in": top_ids})

    def print_structured_result_list(self):
        for row in self._listed_result:
            print(row)


    @classmethod
    def AnalyzedTable(cls) -> str:
        return cls._table._meta.verbose_name

    @classmethod
    def possible_fields(cls) -> List[str]:
        return [f.name for f in cls._table._meta.get_fields()] + cls._additional_cols


class Revenue(BasicAnalytics):

    _table : models.Model = Order
    _pre_standart_values = ['order_date', 'total_price']
    _post_standart_values = ['days', 'revenue']
    _standart_order = ['days']
    _additional_cols = ['days', 'revenue']
    _format_map = {
        'date': ('days', lambda x: x.strftime('%Y-%m-%d')),
        'revenue': ('revenue', lambda x: float(x))
    }


    @BasicAnalytics.modificator_decorater
    def func(self, **kwards)  -> QuerySet:
        self._result = self._result.annotate(
                days=TruncDay('order_date'),
            ).values(
                'days'
            ).annotate(
                revenue=models.Sum('total_price')
            )

class LTV(BasicAnalytics):

    _table : models.Model = Order
    _pre_standart_values = ['customer', 'total_price', 'order_date']
    _post_standart_values = ['cumulative_revenue', 'customer', 'days', 'total_price']
    _standart_order = ['order_date']
    _additional_cols = ['cumulative_revenue']
    _format_map = {
        'date': ('days', lambda x: x.strftime('%Y-%m-%d')),
        'cm_revenue': ('cumulative_revenue', lambda x: float(x)),
        'revenue': ('total_price', lambda x: float(x))
    }

    _graphs = 'customer'
    _x_axis = 'days'

    def _format_graph_key(self, key: str, value):
        if value is None:
            return "Unknown"


        if key == 'customer':
            customer = Customer.objects.filter(id=value).first()
            return customer.email if customer else "Unknown_Customer"


        return str(value)


    _pre_pipeline : List[str] = ['_pre_stories', '_pre_statuses', '_pre_dates', '_pre_values', '_pre_unique_dates', '_pre_group_and_limit']


    def _pre_unique_dates(self):
        quick_print("Uniques Dates")
        self.status_print("Before")

        if self._extra_params.get('unique_dates', False):
            self._result = self._result.annotate(
                days=TruncDay('order_date')
            ).values(
                'customer', 'days'
            ).annotate(
                total_prices=Sum('total_price')
            )
            self._post_standart_values = ['cumulative_revenue', 'customer', 'days', 'total_prices']
            self._format_map = {
                **self._format_map,
                'revenue': ('total_prices', lambda x: float(x))
            }
        self.status_print("After")


    @BasicAnalytics.modificator_decorater
    def func(self, **kwards)  -> QuerySet:

        if self._extra_params.get('unique_dates', False):

            win_expr = NestedSum(Sum('total_price'))
            dates = 'days'
        else:
            win_expr = Sum('total_price')
            dates = 'order_date'

        self._result = self._result.annotate(
                cumulative_revenue=Window(
                    expression=win_expr,
                    partition_by=F('customer'),
                    order_by=F(dates).asc()
                ),

            )

        if not self._extra_params.get('unique_dates', False):
            self._result = self._result.annotate(days=TruncDay('order_date'))


class AnalyzeSales(BasicAnalytics):

    _table : models.Model = OrderItem
    _standart_values = ['product', 'total_units_sold', 'total_orders', 'price_at_purchase']
    _standart_order = ['-price_at_purchase']
    _additional_cols = ['total_units_sold', 'total_orders']
    _format_map = {
            'price_at_purchase': ('price_at_purchase', lambda x: float(x)),
            'units': ('total_units_sold', lambda x: float(x)),
    }
    _per = 'product'


    def _pre_stories(self):
        if self.stores:
            self._result = self._result.filter(order__store_id__in=self.stores)

    def _pre_statuses(self):
        if self.statuses:
            self._result = self._result.filter(order__status__in=self.statuses)
        else:
            self._result = self._result.filter(order__status=Order.Status.COMPLETED)

    @BasicAnalytics.modificator_decorater
    def func(self, **kwards) -> QuerySet:
        products = kwards.get('products_id')
        if not products:
            print(f'!!! parametr product_id is None')
            return None
        self._result = self._result.filter(product__in=products)
        self._result = self._result.values(
                'price_at_purchase'
            ).annotate(
                total_units_sold=models.Sum('quantity'),
                total_orders=Count('order', distinct=True)
            )

class GeneralStats(BasicAnalytics):

    _table : models.Model = Order
    _standart_values = ['total_revenue', 'total_orders', 'avarage_order_price']
    _standart_order = ['total_revenue']
    _additional_cols = ['total_revenue', 'total_orders', 'avarage_order_price']

    @BasicAnalytics.modificator_decorater
    def func(self, **kwards)  -> QuerySet:
        self._result = self._result.annotate(
                total_revenue=Sum('total_price'),
                total_orders=Count('id'),
                avarage_order_price=Avg('total_price')
            )

class TopsProducts(BasicAnalytics):

    _table : models.Model = OrderItem
    _standart_values = ['product_name', 'total_units_sold']
    _standart_order = ['-total_units_sold']
    _additional_cols = ['product_name', 'total_units_sold']

    def _pre_stories(self):
        if self.stores:
            self._result = self._result.filter(order__store_id__in=self.stores)

    def _pre_statuses(self):
        if self.statuses:
            self._result = self._result.filter(order__status__in=self.statuses)
        else:
            self._result = self._result.filter(order__status=Order.Status.COMPLETED)

    def _post_limit(self):
        if self._limit:
            self._result = self._result[:self._limit]
        else:
            self._result = self._result[:5]


    @BasicAnalytics.modificator_decorater
    def func(self, **kwards)  -> QuerySet:
        self._result = self._result.values(
            'product__name'
        ).annotate(
            total_units_sold=Sum(F('quantity') * F('price_at_purchase'))
        )


class TopsCategories(BasicAnalytics):

    _table : models.Model = OrderItem
    _post_standart_values = ['category_name', 'total_revenue']
    _pre_standart_values = ['product', 'quantity', 'price_at_purchase']
    _standart_order = ['-total_revenue']
    _additional_cols = ['category_name', 'total_revenue']

    _format_map = {
        'category_name': ('category_name', lambda x: str(x)),
        'total_revenue': ('total_revenue', lambda x: float(x) if x is not None else 0.0)
    }

    def _pre_stories(self):
        if self.stores:
            self._result = self._result.filter(order__store_id__in=self.stores)

    def _pre_statuses(self):
        if self.statuses:
            self._result = self._result.filter(order__status__in=self.statuses)
        else:
            self._result = self._result.filter(order__status=Order.Status.COMPLETED)

    @BasicAnalytics.modificator_decorater
    def func(self, **kwards)  -> QuerySet:
        self._result = self._result.values(
            category_name=F('product__category__name')
        ).annotate(
            total_revenue=Sum(F('quantity') * F('price_at_purchase'))
        )


class CohortAnalyze(BasicAnalytics):

    _table : models.Model = Order
    _standart_values = ['cohort_month', 'delta', 'users_count']
    _standart_order = ['cohort_month', 'delta']
    _additional_cols = ['cohort_month', 'order_month', 'delta', 'users_count']

    @BasicAnalytics.modificator_decorater
    def func(self, **kwards) -> QuerySet:
        base_qs = self._result

        first_order_subquery = base_qs.filter(
            customer_id=OuterRef("customer_id")
        ).order_by("order_date").values("order_date")[:1]

        self._result.filter(
            customer_id=OuterRef("customer_id")
        ).order_by("order_date").values("order_date")[:1]

        self._result = base_qs.annotate(
            cohort_date=Subquery(first_order_subquery)
        ).filter(
            cohort_date__isnull=False
        ).annotate(
            cohort_month=TruncMonth('cohort_date'),
            order_month=TruncMonth('order_date')
        ).annotate(
            delta=ExpressionWrapper(
                (ExtractYear('order_month') - ExtractYear('cohort_month')) * 12 +
                (ExtractMonth('order_month') - ExtractMonth('cohort_month')),
                output_field=IntegerField()
            )
        ).values('cohort_month', 'delta').annotate(
            users_count=Count('customer_id', distinct=True)
        )

    def formulating(self):
        grouped_cohorts = defaultdict(dict)
        for row in self._result:
            cohort_name = row['cohort_month'].strftime('%b %Y')
            delta = row['delta']
            count = row['users_count']

            grouped_cohorts[cohort_name][delta] = count

        final_json = []

        for cohort, deltas in grouped_cohorts.items():
            cohort_size = deltas.get(0, 0)

            if cohort_size == 0:
                continue

            retention_rates = []

            max_delta = max(deltas.keys())

            for d in range(max_delta + 1):
                users_at_delta = deltas.get(d, 0)
                percent = round((users_at_delta / cohort_size) * 100, 1)
                retention_rates.append(percent)

            final_json.append({
                "cohort": cohort,
                "cohort_size": cohort_size,
                "retention": retention_rates
            })

        return final_json
