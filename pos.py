import flask, flask.views
from flask import url_for, request, session, redirect, jsonify, Response, make_response, current_app
from jinja2 import environment, FileSystemLoader
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.orderinglist import ordering_list
from flask.ext import admin
from flask.ext.admin.contrib import sqla
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin import Admin, BaseView, expose
from flask import render_template, request
from functools import update_wrapper
from flask import session, redirect
from datetime import timedelta
from datetime import datetime
from sqlalchemy.sql import func
import requests
import datetime
import time
import json
import uuid
import os

app = flask.Flask(__name__)
db = SQLAlchemy(app)
app.secret_key = '234234rfascasascqweqscasefsdvqwefe2323234dvsv'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'
# os.environ['DATABASE_URL']
# 'sqlite:///local.db'
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    stock = db.Column(db.Float())

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(20))
    description = db.Column(db.String(1000))
    price = db.Column(db.Float())

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    product_id = db.Column(db.Integer)

class OptionAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer)
    option_id = db.Column(db.Integer)

class ItemAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer)
    consumption_per_order = db.Column(db.Float())
    product_id = db.Column(db.Integer)

class Cashier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    id_no = db.Column(db.String(20))
    password = db.Column(db.String(20))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(30))
    time = db.Column(db.String(10))
    cashier_id = db.Column(db.Integer())
    total = db.Column(db.Float())
    amount_tendered = db.Column(db.Float())
    change = db.Column(db.Float())
    cashier_name = db.Column(db.String(60))
    customer_name = db.Column(db.String(60))
    status = db.Column(db.String(60),default='Pending')
    remarks = db.Column(db.String(60),default='Pending')
    payed = db.Column(db.Boolean())
    timestamp = db.Column(db.String(50))

class TransactionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer)
    item_id = db.Column(db.Integer)
    item_name = db.Column(db.String(100))
    item_qty = db.Column(db.Integer())
    price = db.Column(db.Integer())
    done = db.Column(db.Boolean())

class POSAdmin(sqla.ModelView):
    column_display_pk = True
    
admin = Admin(app)
admin.add_view(POSAdmin(Item, db.session))
admin.add_view(POSAdmin(Product, db.session))
admin.add_view(POSAdmin(Cashier, db.session))
admin.add_view(POSAdmin(Transaction, db.session))
admin.add_view(POSAdmin(ItemAllocation, db.session))
admin.add_view(POSAdmin(Option, db.session))
admin.add_view(POSAdmin(OptionAllocation, db.session))
admin.add_view(POSAdmin(TransactionItem, db.session))


@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('user_id'):
        return redirect('/login')
    inventory = Item.query.order_by(Item.name).all()
    history = Transaction.query.filter_by(date=time.strftime("%B %d, %Y")).order_by(Transaction.timestamp.desc())
    rice_meals = Product.query.filter_by(category='Rice Meals').order_by(Product.name).all()
    unli_rice_meals = Product.query.filter_by(category='Unli Rice Meals').order_by(Product.name).all()
    sausage_on_stick = Product.query.filter_by(category='Sausage on Stick').order_by(Product.name).all()
    sausage_on_bun = Product.query.filter_by(category='Sausage on Bun').order_by(Product.name).all()
    asian_meal = Product.query.filter_by(category='Asian Meal').order_by(Product.name).all()
    combo_meal = Product.query.filter_by(category='Combo Meal').order_by(Product.name).all()
    drinks = Product.query.filter_by(category='Drinks').order_by(Product.name).all()
    addons = Product.query.filter_by(category='Addons').order_by(Product.name).all()
    others = Product.query.filter_by(category='Others').order_by(Product.name).all()
    paid_transactions = Transaction.query.filter_by(date=time.strftime("%B %d, %Y"),payed=True).all()
    transaction_total = sum(record.total for record in paid_transactions)

    if session.get('cart_items'):
        return render_template(
            'index.html',
            rice_meals=rice_meals,
            unli_rice_meals=unli_rice_meals,
            sausage_on_stick=sausage_on_stick,
            sausage_on_bun=sausage_on_bun,
            asian_meal=asian_meal,
            combo_meal=combo_meal,
            drinks=drinks,
            addons=addons,
            others=others,
            items = session['cart_items'],
            inventory = inventory,
            total = session['total'],
            history = history,
            transaction_total=transaction_total
            ), 200

    return render_template(
            'index.html',
            rice_meals=rice_meals,
            unli_rice_meals=unli_rice_meals,
            sausage_on_stick=sausage_on_stick,
            sausage_on_bun=sausage_on_bun,
            asian_meal=asian_meal,
            combo_meal=combo_meal,
            drinks=drinks,
            addons=addons,
            others=others,
            inventory = inventory,
            history = history,
            transaction_total=transaction_total
            ), 200

def least_stock(items):
    stock = items[0].stock
    for item in items:
        if item.stock < stock:
            stock = item.stock
    return stock


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if session.get('user_id'):
        return redirect('/')
    return flask.render_template('login.html')


@app.route('/authenticate', methods=['GET', 'POST'])
def auth_user():
    data = flask.request.form.to_dict()
    user = Cashier.query.filter_by(id_no=data['username'],password=data['password']).first()
    if not user or user == None:
        return redirect('/login')
    session['user_id'] = user.id_no
    session['display_name'] = '%s %s' %(user.first_name,user.last_name)
    return redirect('/')


@app.route('/item/qty/get', methods=['GET', 'POST'])
def get_quantity():
    product_id = flask.request.form.get('product_id')
    product = Product.query.filter_by(id=product_id).one()
    session['product_id'] = product_id
    item_ids = ItemAllocation.query.filter_by(product_id=product_id).all()
    options = Option.query.filter_by(product_id=product_id).all()
    items = []
    for item in item_ids:
        items.append(Item.query.filter_by(id=item.item_id).first())

    option_item_ids = []
    for option in options:
        option_item_ids.append(OptionAllocation.query.filter_by(option_id=option.id).all())

    option_items = []
    for option_item in option_item_ids:
        for item in option_item:
            option_items.append(Product.query.filter_by(id=item.item_id).first())

    stock = least_stock(items)

    return jsonify(
        item_name = product.name,
        item_stock = stock,
        template = flask.render_template('quantity.html', price=product.price,stock=stock,options=options,option_items=option_items,option_item_ids=option_item_ids)
        ),200


@app.route('/item/order/add', methods=['GET', 'POST'])
def order_item():
    product = Product.query.filter_by(id=session['product_id']).one()
    qty = flask.request.form.get('qty')
    options_id = flask.request.form.getlist('options_id[]')
    options_name = flask.request.form.getlist('options_name[]')
    items = []
    item_ids = ItemAllocation.query.filter_by(product_id=product.id).all()
    for item in item_ids:
        items.append(Item.query.filter_by(id=item.item_id).first())

    if options_id:
        for option in options_id:
            option_items = ItemAllocation.query.filter_by(product_id=option).all()
            for item in option_items:
                items.append(Item.query.filter_by(id=item.item_id).first())

    if session.get('cart_items'):
        same_options = False
        for i in session['cart_items']:
            if i['id'] == product.id and i['options'] == options_id and options_id != None:
                current_qty = int(i['quantity']) 
                i['quantity'] = current_qty + int(qty)
                i['price'] += float(qty) * product.price
                same_options = True
                for item in items:
                    allocation = ItemAllocation.query.filter_by(item_id=item.id,product_id=product.id).first()
                    if allocation:
                        item.stock -= (float(qty) * allocation.consumption_per_order)
                    else:
                        item.stock -= float(qty)
                db.session.commit()
                break
        if same_options == False:
            existing = False
            for i in session['cart_items']:
                if i['id'] == product.id and i['options'] == options_id:
                    current_qty = float(i['quantity']) 
                    i['quantity'] = current_qty + float(qty)
                    i['price'] += float(qty) * product.price
                    existing = True
                    for item in items:
                        allocation = ItemAllocation.query.filter_by(item_id=item.id,product_id=product.id).first()
                        if allocation:
                            item.stock -= (float(qty) * allocation.consumption_per_order)
                        else:
                            item.stock -= float(qty)
                        db.session.commit()
                    break
            if not existing:
                session['cart_items'].append({
                    "id":product.id,
                    "name":'%s (%s)' % (product.name,", ".join(options_name)),
                    "options":options_id,
                    "quantity":qty,
                    "price":product.price * float(qty)
                    })
                for item in items:
                    allocation = ItemAllocation.query.filter_by(item_id=item.id,product_id=product.id).first()
                    if allocation:
                        item.stock -= (float(qty) * allocation.consumption_per_order)
                    else:
                        item.stock -= float(qty)
                db.session.commit()
    else:
        session['cart_items'] = [{
                "id":product.id,
                "name":'%s (%s)' % (product.name,", ".join(options_name)),
                "options":options_id,
                "quantity":qty,
                "price":product.price * float(qty)
                }]
        for item in items:
            allocation = ItemAllocation.query.filter_by(item_id=item.id,product_id=product.id).first()
            if allocation:
                item.stock -= (float(qty) * allocation.consumption_per_order)
            else:
                item.stock -= float(qty)
        db.session.commit()

    session['total'] = 0
    for i in session['cart_items']:
        session['total'] += i['price']

    inventory = Item.query.order_by(Item.name).all()
    return jsonify(
        transaction_template=flask.render_template('transaction.html',items=session['cart_items'], total=session['total']),
        inventory_template=flask.render_template('inventory.html',inventory=inventory)
        ) 


@app.route('/item/delete/get', methods=['GET', 'POST'])
def get_item_to_delete():
    product_id = flask.request.form.get('product_id')
    product = Product.query.filter_by(id=product_id).one()
    session['delete_id'] = product_id
    return jsonify(
        product_name = product.name
        ),200


@app.route('/transaction/item/delete/get', methods=['GET', 'POST'])
def get_item_to_delete_transaction():
    product_id = flask.request.form.get('product_id')
    product = TransactionItem.query.filter_by(id=product_id).one()
    session['delete_id'] = product_id
    return jsonify(
        product_name = product.item_name
        ),200


@app.route('/transaction/cancel', methods=['GET', 'POST'])
def cancel_transaction():
    if session.get('cart_items'):
        del(session['cart_items'])
    return flask.render_template('transaction.html')


@app.route('/transaction/item/delete', methods=['GET', 'POST'])
def delete_item_from_transaction():
    transaction_item = TransactionItem.query.filter_by(id=session['delete_id']).one()
    items = []
    product = Product.query.filter_by(id=transaction_item.item_id).one()
    item_ids = ItemAllocation.query.filter_by(product_id=product.id).all()
    for item in item_ids:
        items.append(Item.query.filter_by(id=item.item_id).first())

    for item in items:
        allocation = ItemAllocation.query.filter_by(item_id=item.id,product_id=product.id).first()
        item.stock += (float(transaction_item.item_qty) * allocation.consumption_per_order)

    transaction = Transaction.query.filter_by(id=session['transaction_id']).one()
    transaction.total -= transaction_item.price

    db.session.delete(transaction_item)
    db.session.commit()

    inventory = Item.query.order_by(Item.name).all()
    items = TransactionItem.query.filter_by(transaction_id=session['transaction_id']).all()
    return jsonify(
        inventory_template=flask.render_template('inventory.html',inventory=inventory),
        transaction_info_template=flask.render_template('transaction_info.html',transaction=transaction,items=items)
        )


@app.route('/item/delete', methods=['GET', 'POST'])
def delete_item_from_order():
    product = Product.query.filter_by(id=session['delete_id']).one()
    items = []
    item_ids = ItemAllocation.query.filter_by(product_id=product.id).all()
    for item in item_ids:
        items.append(Item.query.filter_by(id=item.item_id).first())

    for i in session['cart_items']:
        if i['id'] == product.id:
            if i['options'] != None:
                for option in i['options']:
                    option_items = ItemAllocation.query.filter_by(product_id=option).all()
                    for item in option_items:
                        items.append(Item.query.filter_by(id=item.item_id).first())
            for item in items:
                allocation = ItemAllocation.query.filter_by(item_id=item.id,product_id=product.id).first()
                if allocation:
                    item.stock += (float(i['quantity']) * allocation.consumption_per_order)
                else:
                    item.stock += float(i['quantity'])
            db.session.commit()
            item_index = session['cart_items'].index(i)
            del session['cart_items'][item_index]
            break

    session['total'] = 0
    for i in session['cart_items']:
        session['total'] += i['price']   

    inventory = Item.query.order_by(Item.name).all()
    return jsonify(
        item_count = len(session['cart_items']),
        transaction_template=flask.render_template('transaction.html',items=session['cart_items'], total=session['total']),
        inventory_template=flask.render_template('inventory.html',inventory=inventory)
        )


@app.route('/transaction/existing', methods=['GET', 'POST'])
def get_existing_transactions():
    existing = Transaction.query.filter_by(date=time.strftime("%B %d, %Y"),payed=False).order_by(Transaction.timestamp.desc()).all()
    return flask.render_template('existing.html',existing=existing)


@app.route('/item/adjust/get', methods=['GET', 'POST'])
def get_item_to_adjust():
    item_id = flask.request.form.get('item_id')
    item = Item.query.filter_by(id=item_id).first()
    session['adjust_id'] = item_id
    return jsonify(
        current_stock=item.stock,
        item_name=item.name
        ),200


@app.route('/item/adjust', methods=['GET', 'POST'])
def adjust_item():
    item = Item.query.filter_by(id=session['adjust_id']).first()
    data = flask.request.form.to_dict()
    item.stock += float(data['plus']) - float(data['minus'])
    db.session.commit()
    inventory = Item.query.order_by(Item.name).all()
    return jsonify(
        status='success',
        error=None,
        inventory_template=flask.render_template('inventory.html',inventory=inventory)
        ),201


@app.route('/transaction/cash/amount', methods=['GET', 'POST'])
def get_amount_tendered():
    session['customer_name'] = flask.request.form.get('customer_name')
    return jsonify(total=session['total']),200


@app.route('/transaction/id/save', methods=['GET', 'POST'])
def save_transaction_id():
    transaction_id = flask.request.form.get('id')
    session['transaction_id'] = transaction_id
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    return jsonify(
        customer_name=transaction.customer_name,
        total=session['total']
        ),200


@app.route('/transaction/void/id', methods=['GET', 'POST'])
def void_id():
    session['void_id'] = flask.request.form.get('id')
    return jsonify(
        status='success',
        error=''
        ),200


@app.route('/transaction/void/confirm', methods=['GET', 'POST'])
def confirm_void():
    transaction = Transaction.query.filter_by(id=session['void_id']).first()
    # transaction_items = TransactionItem.query.filter_by(transaction_id=transaction.id).all()
    # for transaction in transaction_items:

    transaction_items = TransactionItem.query.filter_by(transaction_id=transaction.id).all()

    for transaction_item in transaction_items:
        product = Product.query.filter_by(id=transaction_item.item_id).first()
        product_items = ItemAllocation.query.filter_by(product_id=product.id).all()
        for product_item in product_items:
            item = Item.query.filter_by(id=product_item.item_id).first()
            item.stock += float(transaction_item.item_qty) * product_item.consumption_per_order
        db.session.delete(transaction_item)
        
    db.session.delete(transaction)
    db.session.commit()
    history = Transaction.query.filter_by(date=time.strftime("%B %d, %Y")).order_by(Transaction.timestamp.desc())
    transaction_total = sum(record.total for record in history)
    inventory = Item.query.order_by(Item.name).all()
    return jsonify(
        status='success',
        error='',
        history_template=flask.render_template('history.html',history=history,transaction_total=transaction_total),
        inventory_template=flask.render_template('inventory.html',inventory=inventory)
        ),201


@app.route('/transaction/existing/add', methods=['GET', 'POST'])
def add_to_existing():
    transaction = Transaction.query.filter_by(id=session['transaction_id']).first()
    transaction.total += session['total']
    transaction.status = 'Pending'
    transaction.remarks = 'Pending'
    db.session.commit()

    for item in session['cart_items']:
        transaction_item = TransactionItem(
            transaction_id=transaction.id,
            item_id=item['id'],
            item_name=item['name'],
            item_qty=item['quantity'],
            price=item['price'],
            done=False
        )
        db.session.add(transaction_item)
    db.session.commit()

    session['cart_items'] = []
    history = Transaction.query.filter_by(date=time.strftime("%B %d, %Y")).order_by(Transaction.timestamp.desc())
    paid_transactions = Transaction.query.filter_by(date=time.strftime("%B %d, %Y"),payed=True).all()
    transaction_total = sum(record.total for record in paid_transactions)

    return jsonify(
        status='success',
        error='',
        transaction_template=flask.render_template('no_transaction.html'),
        history_template=flask.render_template('history.html',history=history,transaction_total=transaction_total)
        ),201


@app.route('/transaction/history/get', methods=['GET', 'POST'])
def get_history():
    history = Transaction.query.filter_by(date=time.strftime("%B %d, %Y")).order_by(Transaction.timestamp.desc())
    paid_transactions = Transaction.query.filter_by(date=time.strftime("%B %d, %Y"),payed=True).all()
    transaction_total = sum(record.total for record in paid_transactions)
    return jsonify(
        status='success',
        error='',
        history_template=flask.render_template('history.html',history=history,transaction_total=transaction_total)
        ),201


@app.route('/transaction/later/amount', methods=['GET', 'POST'])
def get_amount_tendered_later():
    transaction_id = flask.request.form.get('id')
    session['transaction_id'] = transaction_id
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    return jsonify(total=transaction.total),200


@app.route('/transaction/finish/cash', methods=['GET', 'POST'])
def finish_transaction():
    tendered = flask.request.form.get('tendered')
    transaction = Transaction(
        date = time.strftime("%B %d, %Y"),
        time = time.strftime("%-I:%M %p"),
        customer_name = session['customer_name'].capitalize(),
        cashier_id = session['user_id'],
        cashier_name = session['display_name'],
        total=session['total'],
        amount_tendered=tendered,
        change=float(tendered) - float(session['total']),
        payed=True,
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        )
    db.session.add(transaction)
    db.session.commit()

    for item in session['cart_items']:
        transaction_item = TransactionItem(
            transaction_id=transaction.id,
            item_id=item['id'],
            item_name=item['name'],
            item_qty=item['quantity'],
            price=item['price'],
            done=False
        )
        db.session.add(transaction_item)

    db.session.commit()
    session['cart_items'] = []
    history = Transaction.query.filter_by(date=time.strftime("%B %d, %Y")).order_by(Transaction.timestamp.desc())
    paid_transactions = Transaction.query.filter_by(date=time.strftime("%B %d, %Y"),payed=True).all()
    transaction_total = sum(record.total for record in paid_transactions)
    return jsonify(
        status='success',
        error='',
        transaction_template=flask.render_template('no_transaction.html'),
        history_template=flask.render_template('history.html',history=history,transaction_total=transaction_total)
        ),201


@app.route('/transaction/finish/later/pay', methods=['GET', 'POST'])
def finish_later_pay():
    transaction = Transaction.query.filter_by(id=session['transaction_id']).first()
    amount_tendered = flask.request.form.get('tendered')
    transaction.payed = True
    transaction.amount_tendered = amount_tendered
    transaction.change = float(amount_tendered) - float(transaction.total)
    db.session.commit()

    history = Transaction.query.filter_by(date=time.strftime("%B %d, %Y")).order_by(Transaction.timestamp.desc())
    paid_transactions = Transaction.query.filter_by(date=time.strftime("%B %d, %Y"),payed=True).all()
    transaction_total = sum(record.total for record in paid_transactions)
    return jsonify(
        status='success',
        error='',
        history_template=flask.render_template('history.html',history=history,transaction_total=transaction_total)
        ),201


@app.route('/transaction/finish/later', methods=['GET', 'POST'])
def finish_later():
    transaction = Transaction(
        date = time.strftime("%B %d, %Y"),
        time = time.strftime("%-I:%M %p"),
        cashier_id = session['user_id'],
        cashier_name = session['display_name'],
        customer_name = flask.request.form.get('customer_name').capitalize(),
        total=session['total'],
        payed=False,
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        )
    db.session.add(transaction)
    db.session.commit()

    for item in session['cart_items']:
        transaction_item = TransactionItem(
            transaction_id=transaction.id,
            item_id=item['id'],
            item_name=item['name'],
            item_qty=item['quantity'],
            price=item['price'],
            done=False
        )
        db.session.add(transaction_item)

    db.session.commit()
    session['cart_items'] = []
    history = Transaction.query.filter_by(date=time.strftime("%B %d, %Y")).order_by(Transaction.timestamp.desc())
    paid_transactions = Transaction.query.filter_by(date=time.strftime("%B %d, %Y"),payed=True).all()
    transaction_total = sum(record.total for record in paid_transactions)
    return jsonify(
        status='success',
        error='',
        transaction_template=flask.render_template('no_transaction.html'),
        history_template=flask.render_template('history.html',history=history,transaction_total=transaction_total)
        ),201


@app.route('/order/list', methods=['GET', 'POST'])
def order_list():
    orders = Transaction.query.filter_by(status='Pending').order_by(Transaction.timestamp).all()
    items = []
    for order in orders:
        items.append(TransactionItem.query.filter_by(transaction_id=order.id).all())
    return flask.render_template('orders.html', orders=orders,items=items)


@app.route('/order/list/update', methods=['GET', 'POST'])
def update_list():
    orders = Transaction.query.filter_by(status='Pending').order_by(Transaction.timestamp).all()
    items = []
    for order in orders:
        items.append(TransactionItem.query.filter_by(transaction_id=order.id).all())
    return flask.render_template('orders_update.html', orders=orders,items=items)


@app.route('/order/status/update', methods=['GET', 'POST'])
def update_order_status():
    data = flask.request.form.to_dict()
    order = Transaction.query.filter_by(id=data['id']).first()
    items = TransactionItem.query.filter_by(transaction_id=order.id).all()
    order.remarks = data['status']
    if data['status'] == 'Done':  
        order.status = 'Done'
        for item in items:
            item.done = True
    db.session.commit()

    return redirect('/order/list/update')


@app.route('/transaction/info', methods=['GET', 'POST'])
def get_transaction_info():
    transaction_id = flask.request.form.get('id')
    session['transaction_id'] = transaction_id
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    items = TransactionItem.query.filter_by(transaction_id=transaction_id).all()
    return flask.render_template('transaction_info.html',transaction=transaction,items=items)


@app.route('/session/clear', methods=['GET', 'POST'])
def clear_session():
    session.clear()
    return jsonify(status='success'),200



@app.route('/sauce/create', methods=['GET', 'POST'])
def create_sauce_allocation():
    for i in range(41):
        catsup = OptionAllocation(
            item_id=52,
            option_id=i+8
            )
        mustard = OptionAllocation(
            item_id=53,
            option_id=i+8
            )
        mixed = OptionAllocation(
            item_id=54,
            option_id=i+8
            )

        db.session.add(catsup)
        db.session.add(mustard)
        db.session.add(mixed)
        db.session.commit()

    return 'done'


@app.route('/drinks/create', methods=['GET', 'POST'])
def create_drink_allocation():
    for i in range(8):
        iced_tea = OptionAllocation(
            item_id=44,
            option_id=i+1
            )
        juice = OptionAllocation(
            item_id=45,
            option_id=i+1
            )

        db.session.add(iced_tea)
        db.session.add(juice)
        db.session.commit()

    return 'done'


@app.route('/db/update', methods=['GET', 'POST'])
def update_database():
    items = Item.query.all()
    products = Product.query.all()
    item_allocation = ItemAllocation.query.all()
    options = Option.query.all()
    option_allocation = OptionAllocation.query.all()

    db.drop_all()
    db.create_all()

    for item in items:
        add_item = Item(
            name = item.name,
            stock = item.stock
            )
        db.session.add(add_item)

    for product in products:
        add_prod = Product(
            name=product.name,
            category=product.category,
            description=product.description,
            price=product.price
            )
        db.session.add(add_prod)

    for alloc in item_allocation:
        add_alloc = ItemAllocation(
            product_id=alloc.product_id,
            item_id=alloc.item_id,
            consumption_per_order=alloc.consumption_per_order,
            )
        db.session.add(add_alloc)

    for option in options:
        add_option = Option(
            name=option.name,
            product_id=option.product_id
            )
        db.session.add(add_option)

    for option_alloc in option_allocation:
        allocation = OptionAllocation(
            item_id=option_alloc.item_id,
            option_id=option_alloc.option_id
            )
        db.session.add(option_alloc)

    db.session.commit()
    return jsonify(status='success'), 201


@app.route('/db/rebuild', methods=['GET', 'POST'])
def rebuild_database():
    db.drop_all()
    db.create_all()

    item = Item(
        name = 'German Supreme Cheesy',
        stock = 15
        )

    item1 = Item(
        name = 'German Cheesy Spicy',
        stock = 15
        )

    item2 = Item(
        name = 'Hungarian',
        stock = 15
        )

    item3 = Item(
        name = 'Polish',
        stock = 15
        )

    item4 = Item(
        name = 'Schublig',
        stock = 15
        )

    item5 = Item(
        name = 'Chicken',
        stock = 15
        )

    item6 = Item(
        name = 'Beef Bangers',
        stock = 15
        )

    item7 = Item(
        name = 'Rice',
        stock = 15
        )

    item8 = Item(
        name = 'Egg',
        stock = 15
        )

    item9 = Item(
        name = 'Iced Tea',
        stock = 15
        )

    item10 = Item(
        name = 'San Mig Light',
        stock = 15
        )

    item11 = Item(
        name = 'Pale Pilsen',
        stock = 15
        )

    item12 = Item(
        name = 'Juice',
        stock = 15
        )

    # RICE MEALS
    product = Product(
        name='German Supreme Cheesy',
        category='Rice Meals',
        description='desc',
        price=59.00
        )

    product1 = Product(
        name='German Cheesy Spicy',
        category='Rice Meals',
        description='desc',
        price=59.00
        )

    product2 = Product(
        name='Hungarian',
        category='Rice Meals',
        description='desc',
        price=59.00
        )

    product3 = Product(
        name='Polish',
        category='Rice Meals',
        description='desc',
        price=59.00
        )

    product4 = Product(
        name='Schublig',
        category='Rice Meals',
        description='desc',
        price=59.00
        )

    product5 = Product(
        name='Chicken',
        category='Rice Meals',
        description='desc',
        price=59.00
        )

    product5 = Product(
        name='Beef Bangers',
        category='Rice Meals',
        description='desc',
        price=59.00
        )


    # UNLI RICE MEALS
    product6 = Product(
        name='German Supreme Cheesy',
        category='Unli Rice Meals',
        description='desc',
        price=79.00
        )

    product7 = Product(
        name='German Cheesy Spicy',
        category='Unli Rice Meals',
        description='desc',
        price=79.00
        )

    product8 = Product(
        name='Hungarian',
        category='Unli Rice Meals',
        description='desc',
        price=79.00
        )

    product9 = Product(
        name='Polish',
        category='Unli Rice Meals',
        description='desc',
        price=79.00
        )

    product10 = Product(
        name='Schublig',
        category='Unli Rice Meals',
        description='desc',
        price=79.00
        )

    product11 = Product(
        name='Chicken',
        category='Unli Rice Meals',
        description='desc',
        price=79.00
        )

    product12 = Product(
        name='Beef Bangers',
        category='Unli Rice Meals',
        description='desc',
        price=79.00
        )


    # SAUSAGE ON BUN
    product13 = Product(
        name='German Supreme Cheesy',
        category='Sausage on Bun',
        description='desc',
        price=59.00
        )

    product14 = Product(
        name='German Cheesy Spicy',
        category='Sausage on Bun',
        description='desc',
        price=59.00
        )

    product15 = Product(
        name='Hungarian',
        category='Sausage on Bun',
        description='desc',
        price=59.00
        )

    product16 = Product(
        name='Polish',
        category='Sausage on Bun',
        description='desc',
        price=59.00
        )

    product17 = Product(
        name='Schublig',
        category='Sausage on Bun',
        description='desc',
        price=59.00
        )

    product18 = Product(
        name='Chicken',
        category='Sausage on Bun',
        description='desc',
        price=59.00
        )

    product19 = Product(
        name='Beef Bangers',
        category='Sausage on Bun',
        description='desc',
        price=59.00
        )


    # SAUSAGE ON STICK
    product20 = Product(
        name='German Supreme Cheesy',
        category='Sausage on Stick',
        description='desc',
        price=49.00
        )

    product21 = Product(
        name='German Cheesy Spicy',
        category='Sausage on Stick',
        description='desc',
        price=49.00
        )

    product22 = Product(
        name='Hungarian',
        category='Sausage on Stick',
        description='desc',
        price=49.00
        )

    product23 = Product(
        name='Polish',
        category='Sausage on Stick',
        description='desc',
        price=49.00
        )

    product24 = Product(
        name='Schublig',
        category='Sausage on Stick',
        description='desc',
        price=49.00
        )

    product25 = Product(
        name='Chicken',
        category='Sausage on Stick',
        description='desc',
        price=49.00
        )

    product26 = Product(
        name='Beef Bangers',
        category='Sausage on Stick',
        description='desc',
        price=49.00
        )


    # ASIAN MEAL
    product27 = Product(
        name='German Supreme Cheesy',
        category='Asian Meal',
        description='desc',
        price=39.00
        )

    product28 = Product(
        name='German Cheesy Spicy',
        category='Asian Meal',
        description='desc',
        price=39.00
        )

    product29 = Product(
        name='Hungarian',
        category='Asian Meal',
        description='desc',
        price=39.00
        )

    product30 = Product(
        name='Polish',
        category='Asian Meal',
        description='desc',
        price=39.00
        )

    product31 = Product(
        name='Schublig',
        category='Asian Meal',
        description='desc',
        price=39.00
        )

    product32 = Product(
        name='Chicken',
        category='Asian Meal',
        description='desc',
        price=39.00
        )

    product33 = Product(
        name='Beef Bangers',
        category='Asian Meal',
        description='desc',
        price=39.00
        )

    # COMBO MEAL
    product34 = Product(
        name='German Supreme Cheesy',
        category='Combo Meal',
        description='desc',
        price=99.00
        )

    product35 = Product(
        name='German Cheesy Spicy',
        category='Combo Meal',
        description='desc',
        price=99.00
        )

    product36 = Product(
        name='Hungarian',
        category='Combo Meal',
        description='desc',
        price=99.00
        )

    product37 = Product(
        name='Polish',
        category='Combo Meal',
        description='desc',
        price=99.00
        )

    product38 = Product(
        name='Schublig',
        category='Combo Meal',
        description='desc',
        price=99.00
        )

    product39 = Product(
        name='Chicken',
        category='Combo Meal',
        description='desc',
        price=99.00
        )

    product40 = Product(
        name='Beef Bangers',
        category='Combo Meal',
        description='desc',
        price=99.00
        )
    db.session.add(item)
    db.session.add(item1)
    db.session.add(item2)
    db.session.add(item3)
    db.session.add(item4)
    db.session.add(item5)
    db.session.add(item6)
    db.session.add(item7)
    db.session.add(item8)
    db.session.add(item9)
    db.session.add(item10)
    db.session.add(item11)
    db.session.add(item12)
    
    db.session.add(product)
    db.session.add(product1)
    db.session.add(product2)
    db.session.add(product3)
    db.session.add(product4)
    db.session.add(product5)
    db.session.add(product6)
    db.session.add(product7)
    db.session.add(product8)
    db.session.add(product9)
    db.session.add(product10)
    db.session.add(product11)
    db.session.add(product12)
    db.session.add(product13)
    db.session.add(product14)
    db.session.add(product15)
    db.session.add(product16)
    db.session.add(product17)
    db.session.add(product18)
    db.session.add(product19)
    db.session.add(product20)
    db.session.add(product21)
    db.session.add(product22)
    db.session.add(product23)
    db.session.add(product24)
    db.session.add(product25)
    db.session.add(product26)
    db.session.add(product27)
    db.session.add(product28)
    db.session.add(product29)
    db.session.add(product30)
    db.session.add(product31)
    db.session.add(product32)
    db.session.add(product33)
    db.session.add(product34)
    db.session.add(product35)
    db.session.add(product36)
    db.session.add(product37)
    db.session.add(product38)
    db.session.add(product39)
    db.session.add(product40)

    db.session.commit()

    return jsonify(status='success'), 201


if __name__ == '__main__':
    app.debug = True
    app.run(host='192.168.2.44',port=80)
    # host='192.168.2.44',port=80