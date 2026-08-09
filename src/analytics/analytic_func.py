from collections import defaultdict

from .models import Order, OrderItem

from django.db import models
from django.db.models import Sum, Avg, Count, Window, F, QuerySet, OuterRef, Subquery, IntegerField, ExpressionWrapper
from django.db.models.functions import TruncDay, TruncMonth, ExtractYear, ExtractMonth

from abc import ABC, abstractmethod
from typing import List



class BasicAnalytics(ABC):

    _result : QuerySet = None
    _table : models.Model = None
    _standart_values : List[str] = []
    _standart_order : List[str] = []
    _additional_cols : List[str] = []
    _format_map = {}
    _graphs = None

    def __init__(self, **kwards):
        self.stores = kwards.get('stores_id')
        self.statuses = kwards.get('statuses')
        self.start_date = kwards.get('start_date')
        self.end_date = kwards.get('end_date')
        self.fields = kwards.get('fields')
        self.orders_by = kwards.get('orders_by')
        self.limit = kwards.get('limits')

    def modificator_decorater(func):
        def wrapper(self, *args, **kwards):

            self._result = self._table.objects.all()
            self._run_methods_by_prefix('_pre_')
  
            func(self, *args, **kwards)

            if self._result is not None:
                self._run_methods_by_prefix('_post_')

            return self._result

        return wrapper

    @abstractmethod
    @modificator_decorater
    def func(self, **kwards) -> QuerySet:
        pass

    def _run_methods_by_prefix(self, prefix: str):
        for attr_name in dir(self):
            if attr_name.startswith(prefix):
                method = getattr(self, attr_name)
                if callable(method):
                    method()

    def formulating(self, format_map=None, graphs=None):
        graphs = graphs if graphs is not None else self._graphs
        format_map = format_map if format_map is not None else self._format_map
        
        def MakeGraph(rows):
            json = []
            for row in rows:
                formulated_row = {}
                for json_key, (db_key, formatter) in self._format_map.items():
                    raw_value = row.get(db_key)
                    formulated_row[json_key] = formatter(raw_value) if raw_value is not None else 0
                json.append(formulated_row)
            return json
        
        
        final_json = []
        if graphs:
           grouped_by = self._result.order_by().values_list(self._graphs, flat=True).distinct()

           for graph in grouped_by:
               final_json.append({graph: MakeGraph(self._result.filter(**{self._graphs: graph}))})
        else:
            final_json = MakeGraph(self._result)

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

    def _post_values(self):
        if self.fields:
            base_fields = self.possible_fields()
            for field in self.fields:
                if field not in base_fields:
                    print("ERROR FIELD")
                    return
            self._result = self._result.values(*self.fields)
        elif hasattr(self, '_standart_values'):
            self._result = self._result.values(*self._standart_values)

    def _post_order_by(self):
        if self.orders_by:
            base_fields = self.possible_fields()
            for field in self.orders_by:
                if field not in base_fields:
                    print("ERROR FIELD")
                    return
            self._result = self._result.order_by(*self.orders_by)
        elif hasattr(self, '_standart_order'):
            self._result = self._result.order_by(*self._standart_order)

    def _post_limit(self):
        if self.limit:
            self._result = self._result[:self.limit]

    def possible_fields(self) -> List[str]:
        return [f.name for f in self._table._meta.get_fields()] + self._additional_cols

class Revenue(BasicAnalytics):

    _table : models.Model = Order
    _standart_values = ['days', 'revenue']
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
                revenue=models.Sum('total_price'))

class LTV(BasicAnalytics):

    _table : models.Model = Order
    _standart_values = ['cumulative_revenue', 'customer', 'total_price', 'days']
    _standart_order = ['order_date']
    _additional_cols = ['cumulative_revenue']
    _format_map = {
            'date': ('days', lambda x: x.strftime('%Y-%m-%d')),
            'revenue': ('cumulative_revenue', lambda x: float(x))
        }
    _graphs = 'customer'

    @BasicAnalytics.modificator_decorater
    def func(self, **kwards)  -> QuerySet:
        self._result = self._result.annotate(
                cumulative_revenue=Window(
                    expression=Sum('total_price'),
                    partition_by=F('customer'),
                    order_by=F('order_date').asc()
                ),
                days=TruncDay('order_date')
            )

class AnalyzeSales(BasicAnalytics):

    _table : models.Model = OrderItem
    _standart_values = ['product', 'total_units_sold', 'total_orders', 'price_at_purchase']
    _standart_order = ['-price_at_purchase']
    _additional_cols = ['total_units_sold', 'total_orders']
    _format_map = {
            'price_at_purchase': ('price_at_purchase', lambda x: float(x)),
            'units': ('total_units_sold', lambda x: float(x)),
    }
    _graphs = 'product'


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
        print(f'\n\n\nProducts: {products}\nType: {type(products)}\n\n\n')
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
            'product'
        ).annotate(
            product_name='product__name',
            total_units_sold=Sum(F('quantity') * F('price_at_purchase'))
        )


class TopsCategories(BasicAnalytics):

    _table : models.Model = OrderItem
    _standart_values = ['category_name', 'total_units_sold']
    _standart_order = ['-total_units_sold']
    _additional_cols = ['category_name', 'total_units_sold']

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
            'product__category'
        ).annotate(
            category_name='product__category__name',
            total_units_sold=Sum(F('quantity') * F('price_at_purchase'))
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

