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
import db

from shop.models import Product
from shop.models import Cart
from shop.models import Customer
from shop.models import Order
import sqlite3

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cur = conn.cursor()

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


"""Show Location"""
def location(update, context):
        context.bot.send_location(update.effective_chat.id,
                                  latitude = 55.70938, longitude = 37.62232)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Наш адрес м.Тульская\n"
                                 f"Большая Тульская 13\n Тел.+7 999 9999999")


"""Show product"""
def show_product(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = update.callback_query.data
    title = name(data)
    price_ = price(title)
    keyboard = [[InlineKeyboardButton("Add to Cart", callback_data = "add_to_cart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_photo(update.effective_chat.id, photo=open(f"{data}.png", "rb"),
                           caption=f"<b>{title}\n{price_}</b>", reply_markup=reply_markup,
                           parse_mode=telegram.ParseMode.HTML)


"""Products Catalog"""
def catalog(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    keyboard = [
        [InlineKeyboardButton(f"{db.name(1)}", callback_data="1")],
        [InlineKeyboardButton(f"{db.name(2)}", callback_data="2")],
        [InlineKeyboardButton(f"{db.name(3)}", callback_data="3")],
        [InlineKeyboardButton(f"{db.name(4)}", callback_data="4")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    c, created = Customer.objects.get_or_create(telegram_id=chat_id,
                                                defaults={
                                                "name": update.message.chat.username,
                                                })
    update.message.reply_text(f"<i><u>Please choose product</u></i>",
                              reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)


"""Main Menu"""
def start(update, context):
    chat_id = update.effective_chat.id
    username = update.message.from_user.username
    c, created = Customer.objects.get_or_create(telegram_id=chat_id,
                                                defaults={"name": update.message.from_user.username,})
    custom_keyboard = [["Catalog"], ["Cart", "Contacts"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id,
                            text=f"{username} your ID is {chat_id}",
                            reply_markup=reply_markup)

class Command(BaseCommand):
    help = "Telegram-bot"

    def handle(self, *args, **options):
        request = Request( connect_timeout=0.5, read_timeout=0.5,)
        bot = Bot(request=request, token=settings.TOKEN)
        print(bot.get_me())

        updater = Updater(bot=bot, use_context=True,)

        start_handler = CommandHandler("start", start)
        updater.dispatcher.add_handler(start_handler)

        catalog_handler = MessageHandler(Filters.text("Catalog"), catalog)
        updater.dispatcher.add_handler(catalog_handler)

        show_product_handler = CallbackQueryHandler(show_product, pattern= '^[0-9]$')
        updater.dispatcher.add_handler(show_product_handler)

        add_product_handler = CallbackQueryHandler(db.add_product, pattern="add_to_cart")
        updater.dispatcher.add_handler(add_product_handler)

        cart_handler = MessageHandler(Filters.text("Cart"), db.cart)
        updater.dispatcher.add_handler(cart_handler)

        del_cart_handler = CallbackQueryHandler(db.del_cart, pattern="delete_cart")
        updater.dispatcher.add_handler(del_cart_handler)

        payment_handler = CallbackQueryHandler(db.checkout, pattern="proceed_to")
        updater.dispatcher.add_handler(payment_handler)

        contacts_handler = MessageHandler(Filters.text("Contacts"), location)
        updater.dispatcher.add_handler(contacts_handler)






        updater.start_polling()
        updater.idle()
