import sqlite3
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Bot
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.utils.request import Request
from telegram import Location, ChatLocation, User
import datetime
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import logging
import re

def name(id):
    conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("SELECT name FROM shop_product WHERE id = (?)", (id,))
    name = cur.fetchone()[0]
    return name

def price(title):
    conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("SELECT price FROM shop_product WHERE name = (?)", (title,))
    price = cur.fetchone()[0]
    return price

def checkout(update: Update, context: CallbackContext):
    conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
    cur = conn.cursor()
    query = update.callback_query
    query.answer()
    chat_id = query.from_user.id
    username = query.from_user.username
    cur.execute('''SELECT id FROM shop_customer WHERE
                telegram_id = (?)''', (chat_id,))
    callback_customer_id = cur.fetchone()[0]
    cur.execute('''SELECT SUM(shop_cart.quantity * shop_product.price)
                FROM shop_cart JOIN shop_product ON shop_product.id = shop_cart.product_id
                WHERE shop_cart.customer_id = (?)''', (callback_customer_id,))
    total_sum = cur.fetchone()[0]
    cur.execute('''SELECT shop_product.name, shop_cart.quantity, shop_customer.name
                   FROM shop_product JOIN shop_cart JOIN shop_customer
                   ON shop_product.id = shop_cart.product_id
                   AND shop_customer.id = shop_cart.customer_id
                   WHERE customer_id = (?)''', (callback_customer_id,))
    checkout_cart = cur.fetchall()
    checkout_cart1 = "\n".join(str(el) for el in checkout_cart)
    checkout_cart_ = checkout_cart1.replace("(","").replace(")","")
    checkout_list = list(checkout_cart)
    cur.execute('''SELECT shop_product.name, shop_cart.quantity FROM shop_product
                   JOIN shop_cart ON shop_product.id = shop_cart.product_id
                   WHERE customer_id = (?)''', (callback_customer_id,))
    list_order = cur.fetchall()
    list_order1 = "\n".join(str(el) for el in list_order)
    list_order_ = list_order1.replace("(","").replace(")","")
    for item in checkout_list:
        product_id = item[0]
        quantity = item[1]
        total = total_sum
        date = datetime.datetime.now()
        name = item[2]
        cur.execute('''INSERT INTO shop_order (quantity, total, created_at, customer_id, product_id)
                    VALUES (?, ?, ?, ?, ?)''', (quantity, total, date, name, product_id,))
        conn.commit()
    cur.execute('''DELETE FROM shop_cart WHERE customer_id = (?)''', (callback_customer_id,))
    conn.commit()
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"<b>*Checkout* :</b>\n-------------\n"
                             f"<u>{list_order_}</u>\nTotal = <b>{total_sum}</b>"
                             f"\n------------- \n Pay to SBER Account Number : 123123123",
                             parse_mode=telegram.ParseMode.HTML)

def del_cart(update: Update, context: CallbackContext):
    conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
    cur = conn.cursor()
    query = update.callback_query
    query.answer()
    chat_id = query.from_user.id
    username = query.from_user.username
    cur.execute("SELECT id FROM shop_customer WHERE telegram_id = (?)", (chat_id,))
    callback_customer_id = cur.fetchone()[0]
    cur.execute("DELETE FROM shop_cart WHERE customer_id = (?)", (callback_customer_id,))
    cart = cur.fetchall()
    conn.commit()
    cur.close()
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"<b>{username}</b> your cart is empty!",
                             parse_mode=telegram.ParseMode.HTML)

def cart(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    keyboard = [[
        InlineKeyboardButton(f"Delete cart", callback_data="delete_cart"),
        InlineKeyboardButton(f"Proceed to checkout", callback_data="proceed_to")
        ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''SELECT id FROM shop_customer WHERE telegram_id = (?)''', (chat_id,))
    callback_customer_id = cur.fetchone()[0]
    cur.execute('''SELECT shop_product.name, shop_cart.quantity FROM shop_product
                JOIN shop_cart ON shop_product.id = shop_cart.product_id
                WHERE customer_id = (?)''', (callback_customer_id,))
    cart = cur.fetchall()
    cart_list = "\n".join(str(el) for el in cart)
    cart_list_ = cart_list.replace("(","").replace(")","")
    cur.execute('''SELECT SUM(shop_cart.quantity * shop_product.price) FROM shop_cart
                JOIN shop_product ON shop_product.id = shop_cart.product_id
                WHERE shop_cart.customer_id = (?)''', (callback_customer_id,))
    cart_sum = cur.fetchone()[0]
    if cart_sum is None:
        update.message.reply_text(f"<b>Your cart is empty {username}!</b>",
                                  parse_mode=telegram.ParseMode.HTML)
    else:
        update.message.reply_text(f"Your cart <b>{username}</b>:\n <u>{cart_list_}</u>\n"
                                  f"<i>Subtotal:</i>\n <b>{cart_sum}</b>",
                                  reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)

def add_product(update: Update, context: CallbackContext):
    conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
    cur = conn.cursor()
    query = update.callback_query
    query.answer()
    chat_id = query.from_user.id
    username = query.from_user.username
    callback_product = update.callback_query.message.caption
    callback_product_ = callback_product.split("\n")
    cur.execute('''SELECT id FROM shop_product WHERE name = (?)''', (callback_product_[0],))
    callback_product_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM shop_customer WHERE telegram_id = (?)", (chat_id,))
    callback_customer_id = cur.fetchone()[0]
    cur.execute('''SELECT customer_id , product_id FROM shop_cart
                WHERE customer_id = (?) AND product_id = (?);''',
                (callback_customer_id, callback_product_id,))
    cart = cur.fetchone()
    if cart is None:
        cur.execute('''INSERT INTO shop_cart (quantity, customer_id, product_id)
                    VALUES (?, ?, ?)''',
                   (1, callback_customer_id, callback_product_id,))
        conn.commit()
        cur.close()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"<b>{username}</b>, {callback_product_[0]} added to your cart.",
                                 parse_mode=telegram.ParseMode.HTML)
    else:
        cur.execute('''SELECT quantity FROM shop_cart WHERE customer_id = (?)
                    AND product_id = (?)''', (callback_customer_id, callback_product_id,))
        quantity = cur.fetchone()[0]
        update_quantity = quantity + 1
        cur.execute('''Update shop_cart SET quantity = (?)
                    WHERE customer_id = (?) AND product_id = (?)''',
                   (update_quantity, callback_customer_id, callback_product_id,))
        conn.commit()
        cur.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"+1 {callback_product_[0]}")
