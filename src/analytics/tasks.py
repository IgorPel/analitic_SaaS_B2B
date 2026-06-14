# tasks.py
from decimal import Decimal
from itertools import islice

from celery import shared_task
from click.core import batch

from .models import Product, Category, Company, Store, Customer, Order, ImportIssue, OrderItem, PriceHistory
import csv
import os

    

def build_catogory_map(company_id):
    categories = Category.objects.filter(company_id=company_id)
    id_map = {category.id: category for category in categories}

    category_map = {}

    def full_path(category):
        path_parts = []
        current = category

        while current is not None:
            path_parts.insert(0, current.name)
            current = id_map[current.parent_id]

        return " > ".join(path_parts)

    for category in categories:
        full_path = full_path(category)
        category_map[full_path] = category

    return category_map


@shared_task(bind=True)
def process_warehouse_data(self, file_path, store_id, company_id):

    company = Company.objects.filter(id=company_id).first()

    if not company:
        raise Exception("Company not found")

    store = Store.objects.filter(company_id=company_id, id=store_id).first()

    if not store:
        return {"status": "error", "message": "Store not found"}

    category_map = build_catogory_map(company_id)
    products = Product.objects.filter(store=store)
    products_map = {product.sku: product for product in products}
    breakpoint()
    categores_to_create = []
    products_to_create = []
    m2m_links = []
    mistakes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            row_count = sum(1 for row in csv_file)
            csv_file.seek(0)
            
            for i, row in enumerate(reader):
                sku = row['product_sku'].strip()
                raw_category_path = row['category_path'].strip()
       
                if raw_category_path not in category_map:
                    part_categories = [cat.strip() for cat in raw_category_path.split('>')]
                    current_path = ""
                    parent_obj = None
                    for part in part_categories:
                        current_path = f"{current_path} > {part}" if current_path else part

                        if current_path not in category_map:
                            new_cat = Category.objects.create(
                                name=part,
                                parent=parent_obj,
                                company=company
                            )
                            category_map[current_path] = new_cat
                        parent_obj = category_map[current_path]

                if sku not in products_map:
                    new_product = Product(
                        name=row['product_name'].strip(),
                        sku=sku,
                        store=store,
                        current_price=row['price']
                    )
                    products_to_create.append(new_product)
                    products_map[sku] = new_product
                    m2m_links.append((sku, category_map[raw_category_path]))
                else:
                    existing_product = products_map[sku]

                    if getattr(existing_product, 'id', None):
                        if str(existing_product.current_price) != str(row['price']):
                            mistakes.append({
                                'type': 'PRICE_UPDATE',
                                'product_sku': sku,
                                'old_price': existing_product.current_price,
                                'new_price': row['price']
                            })
                if i % 100 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'processed': i,
                            'total': row_count,
                            'percent': int(i / row_count * 100)
                        }
                    )
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if len(categores_to_create) > 0:
        for category in categores_to_create:
            category.save()

    if len(products_to_create) > 0:
        created_products = Product.objects.bulk_create(products_to_create)
        new_products_map = {product.sku: product for product in created_products}

        ProductCategoryThrough = Category.products.through
        
        through_objects_to_create = []
    
        for sku, cat_obj in m2m_links:
            prod_obj = new_products_map[sku]
            
            through_objects_to_create.append(
                ProductCategoryThrough(
                    product_id=prod_obj.id, 
                    category_id=cat_obj.id
                )
            )
        
        if through_objects_to_create:
            ProductCategoryThrough.objects.bulk_create(through_objects_to_create)

    return {
        "status": "success",
        "info": {
            "products_created": len(products_to_create),
            "category_created": len(categores_to_create)
        },
        "notices": mistakes
    }

@shared_task(bind=True)
def process_sales_data(self, file_path, company_id, store_id):
    company = Company.objects.filter(id=company_id).first()
    if not company:
        raise Exception("Company not found")

    store = Store.objects.filter(company_id=company_id, id=store_id).first()
    if not store:
        return {"status": "error", "message": "Store not found"}

    uncategorized_category, _ = Category.objects.get_or_create(
        name="Без категорії (Автоматично)", 
        company=company,
        defaults={'parent': None}
    )

    Order_Status = {
        'COMPLETED': Order.Status.COMPLETED,
        'CANCELED': Order.Status.CANCELED,
        'RETURNED': Order.Status.RETURNED
    }
    
    rows_processed = 0
    total_issues_found = 0 
    
    products_map = {p.sku: p for p in Product.objects.filter(store=store)}
    try:

        with open(file_path, mode='r', encoding='utf-8') as f:
               row_count = sum(1 for _ in f) - 1 
            
        if row_count <= 0:
            return {"status": "error", "message": "Файл порожній або містить лише заголовки"}
        

        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
         
            while True:
                batch = list(islice(reader, 1000))
                
                if not batch:
                    break
                
                issues_to_log = []
                customers_map = {}
                unique_emails_in_batch = set()
                unique_skus_in_batch = set()
                unique_orders_in_batch = {}
                total_cost_order = {}
                    
                for i, row in enumerate(batch):
                    unique_emails_in_batch.add(row['customer_email'].strip())
                    unique_skus_in_batch.add(row['product_sku'].strip())

                    order_id = row['order_id'].strip()
                    
                    quantity = int(row['quantity'])
                    price = Decimal(row['price'])
                    item_total = quantity * price

                    if order_id not in unique_orders_in_batch:
                        total_cost_order[order_id] = item_total
                        unique_orders_in_batch[order_id] = {
                            'customer_email': row['customer_email'].strip(),
                            'date': row['order_date'],
                            'status': row['status'].strip().upper() 
                        }
                    else:
                        if row['customer_email'] != unique_orders_in_batch[order_id]['customer_email']:
                            issues_to_log.append(
                                ImportIssue(
                                    company=company,
                                    task_id=self.request.id,
                                    type='CUSTOMER_MISMATCH',
                                    description=f'Order {order_id} have more than one customer email.',
                                    row_number=rows_processed + i + 1
                                )
                            )
                           
                        if row['status'] != unique_orders_in_batch[order_id]['status']:
                            issues_to_log.append(
                                ImportIssue(
                                    company=company,
                                    task_id=self.request.id,
                                    type='STATUS_MISMATCH',
                                    description=f'Order {order_id} have different status.',
                                    row_number=rows_processed + i + 1
                                )
                            )
                           
                        if row['order_date'] != str(unique_orders_in_batch[order_id]['date']):
                            issues_to_log.append(
                                ImportIssue(
                                    company=company,
                                    task_id=self.request.id,
                                    type='DATE_MISMATCH',
                                    description=f'Order {order_id} have different date.',
                                    row_number=rows_processed + i + 1
                                )
                            )

                        total_cost_order[order_id] += item_total

                existing_customers = Customer.objects.filter(email__in=unique_emails_in_batch)
                for c in existing_customers:
                    customers_map[c.email] = c

                customers_to_create = []
                for email in unique_emails_in_batch:
                    if email not in customers_map:
                        customers_to_create.append(Customer(email=email, company=company))
                    
                if customers_to_create:
                    created_customers = Customer.objects.bulk_create(customers_to_create)
                    for c in created_customers:
                        customers_map[c.email] = c
           
                missing_products = unique_skus_in_batch - set(products_map.keys())
                
                draft_products_to_create = []

                for sku in missing_products:
                    draft_products_to_create.append(
                        Product(
                            name=f"Auto-drafted for {sku}",
                            sku=sku,
                            store=store,
                            current_price=Decimal(next(row['price'] for row in batch if row['product_sku'] == sku))
                        )
                    )
           
                    issues_to_log.append(
                        ImportIssue(
                            company=company,
                            task_id=self.request.id,
                            type='MISSING_SKU', 
                            description=f"SKU '{sku}' created as draft.",
                            row_number=next(i for i, row in enumerate(batch) if row['product_sku'] == sku)  + 1 + rows_processed
                        )
                    )
                
                if draft_products_to_create:
                    created_products = Product.objects.bulk_create(draft_products_to_create)

                    for p in created_products:
                        p.category.add(uncategorized_category)
                        products_map[p.sku] = p 

                
                orders_map = {}
                existing_orders = Order.objects.filter(order_id__in=unique_orders_in_batch.keys())
                for o in existing_orders:
                    orders_map[o.order_id] = o

                orders_to_create = []
                orders_to_update = [] 

                for order_id, order_data in unique_orders_in_batch.items():
                    current_batch_sum = total_cost_order[order_id]
                    if order_id not in orders_map:
                
                        customer_obj = customers_map[order_data['customer_email']]
                        orders_to_create.append(
                            Order(
                                order_id=order_id,
                                customer=customer_obj,
                                status=Order_Status.get(order_data['status'], Order.Status.COMPLETED),
                                order_date=order_data['date'], 
                                store=store,
                                total_price=current_batch_sum
                            )
                        )
                    else:
                        breakpoint()
                        existing_order = orders_map[order_id]
                        

                        if order_data['customer_email'] != orders_map[order_id].customer.email:
                            issues_to_log.append(
                                ImportIssue(
                                    company=company,
                                    task_id=self.request.id,
                                    type='CUSTOMER_MISMATCH',
                                    description=f'Order {order_id} have more than one customer email.',
                                    row_number=next((
                                            i + rows_processed + 2 for i, row in enumerate(batch) if 
                                                row['order_id'] == order_id and 
                                                row['customer_email'] == order_data['customer_email']
                                            ), -1
                                        )
                                )
                            )
                           
                        if Order_Status.get(order_data['status']) != orders_map[order_id].status:
                            issues_to_log.append(
                                ImportIssue(
                                    company=company,
                                    task_id=self.request.id,
                                    type='STATUS_MISMATCH',
                                    description=f'Order {order_id} have different status.',
                                    row_number=next((
                                            i + rows_processed + 2 for i, row in enumerate(batch) if 
                                                row['order_id'] == order_id and 
                                                row['status'] == order_data['status']
                                                ), -1
                                        )
                                )
                            )
                           
                        if order_data['date'] != str(orders_map[order_id].order_date):
                            issues_to_log.append(
                                ImportIssue(
                                    company=company,
                                    task_id=self.request.id,
                                    type='DATE_MISMATCH',
                                    description=f'Order {order_id} have different date.',
                                    row_number=next((
                                            i for i, row in enumerate(batch) if 
                                                row['order_id'] == order_id and 
                                                row['status'] == order_data['status']
                                                ), -1
                                        ) + rows_processed + 2
                                )
                            )
                           
                        existing_order.total_cost += current_batch_sum
                        orders_to_update.append(existing_order)

                if orders_to_create:
                    created_orders = Order.objects.bulk_create(orders_to_create)
                    for o in created_orders:
                        orders_map[o.order_id] = o
                        
                if orders_to_update:
                    Order.objects.bulk_update(orders_to_update, ['total_cost'])

                order_items_to_create = []

                for row in batch:
                    order_id = row['order_id'].strip()
                    sku = row['product_sku'].strip()
                    
                    order_items_to_create.append(
                        OrderItem(
                            order=orders_map[order_id],
                            product=products_map[sku],
                            quantity=int(row['quantity']),  
                            price_at_purchase=Decimal(row['price'])   
                        )
                    )

                OrderItem.objects.bulk_create(order_items_to_create)

                if issues_to_log:
                    ImportIssue.objects.bulk_create(issues_to_log)
                    total_issues_found += len(issues_to_log)

                rows_processed += len(batch)
                self.update_state(
                        state='PROGRESS',
                        meta={
                            'processed': rows_processed,
                            'total': row_count,
                            'percent': int(rows_processed / row_count * 100)
                        }
                    )

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    return {
        "status": "success",
        "processed_rows": rows_processed,
        "has_issues": total_issues_found > 0,
        "issues_count": total_issues_found
    }
