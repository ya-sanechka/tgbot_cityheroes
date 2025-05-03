import logging
import sqlite3
from collections import defaultdict
from datetime import datetime
from pprint import pprint
from random import choice

import requests
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, CallbackQueryHandler
from config import BOT_TOKEN
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3

# Создаем подключение к базе данных (файл my_database.db будет создан)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
reply_keyboard = [['/my_profile', '/new_order'],
                  ['/favorite', '/hz']]
inline_keyboard = [
    [
        InlineKeyboardButton("👍", callback_data="1"),
        InlineKeyboardButton("👎", callback_data="2"),
    ]]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
users = defaultdict()
last_requests = []
bd = sqlite3.connect('Users.sqlite')


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf'Здравствуйте! {user.mention_html()}! Добро пожаловать в наше сообщество "Из теплых рук"!🍽️',
    )
    cursor = bd.cursor()
    tgnik = update.effective_user.username

    result_s = cursor.execute(f"""SELECT * FROM Sellers
                    WHERE tg_nik = ?""", (tgnik,)).fetchall()
    result_b = cursor.execute(f"""SELECT * FROM Buyers
                        WHERE tg_nik = ?""", (tgnik,)).fetchall()

    if result_s or result_b:
        await update.message.reply_text('Вы уже зарегистрированы!🙌')

    else:
        await update.message.reply_text(
            'Давайте познакомимся! Выберете Вашу роль здесь: Вы будете продавать блюда или же покупать?\n напишите "Продавец" или "Покупатель"')
        return 1


async def getting_role(update, context):
    role = update.message.text
    if role.lower() == 'продавец':
        sqlite_insert_query = """INSERT INTO Sellers
                                          (name, description, verification, marks, city, tg_nik, user_link)
                                          VALUES
                                          (?, ?, ?, ?, ?, ?, ?);"""
        username = list(list(str(update.effective_user).split('id='))[1].split(','))[0]
        tgnik = update.effective_user.username
        link = str(update.effective_user)
        print(tgnik)
        cursor = bd.cursor()
        data_tuple = ('no', 'None', 'no', '0', 'None', tgnik, link)
        cursor.execute(sqlite_insert_query, data_tuple)
        bd.commit()
        await update.message.reply_text('Как Вас зовут?')
    elif role.lower() == 'покупатель':
        sqlite_insert_query = """INSERT INTO Buyers
                                                  (name, city, tg_nik, user_link)
                                                  VALUES
                                                  (?, ?, ?, ?);"""
        username = list(list(str(update.effective_user).split('id='))[1].split(','))[0]
        tgnik = update.effective_user.username
        link = str(update.effective_user)
        print(tgnik)
        cursor = bd.cursor()
        data_tuple = ('no', 'None', tgnik, link)
        cursor.execute(sqlite_insert_query, data_tuple)
        bd.commit()
        await update.message.reply_text('Как Вас зовут?')

    return 2


async def getting_name(update, context):
    name1 = update.message.text
    sqlite_insert_query = """UPDATE Sellers SET name = ? WHERE tg_nik = ?"""
    bd.cursor().execute(sqlite_insert_query,
                        (name1, update.effective_user.username))
    bd.commit()
    sqlite_insert_query = """UPDATE Buyers SET name = ? WHERE tg_nik = ?"""
    bd.cursor().execute(sqlite_insert_query,
                        (name1, update.effective_user.username))
    bd.commit()
    await update.message.reply_text('Приятно познакомиться! \nИз какого вы города?')
    return 3


async def getting_city(update, context):
    city1 = update.message.text.lower()

    sqlite_insert_query = """UPDATE Sellers SET city = ? WHERE tg_nik = ?"""
    bd.cursor().execute(sqlite_insert_query,
                        (city1, update.effective_user.username))
    bd.commit()
    sqlite_insert_query = """UPDATE Buyers SET city = ? WHERE tg_nik = ?"""
    bd.cursor().execute(sqlite_insert_query,
                        (city1, update.effective_user.username))
    bd.commit()

    cursor = bd.cursor()
    tgnik = update.effective_user.username

    result_s = cursor.execute(f"""SELECT * FROM Sellers
                                    WHERE tg_nik = ?""", (tgnik,)).fetchall()
    if result_s:
        await update.message.reply_text(
            'Отлично! \nРасскажите про ваши любимые рецепты и блюда, которые вы умеете готовить и хотите продавать!😋')
        return 4
    else:
        await update.message.reply_text('Отлично! Спасибо за регистрацию!')
        await update.message.reply_text('Для просмотра предложений нажмите /new_order в основном меню.',
                                        reply_markup=markup)


async def getting_description(update, context):
    descr1 = update.message.text

    cursor = bd.cursor()
    tgnik = update.effective_user.username

    result_s = cursor.execute(f"""SELECT * FROM Sellers
                        WHERE tg_nik = ?""", (tgnik,)).fetchall()
    if result_s:
        sqlite_insert_query = """UPDATE Sellers SET description = ? WHERE tg_nik = ?"""
        bd.cursor().execute(sqlite_insert_query,
                            (descr1, update.effective_user.username))
        bd.commit()
        await update.message.reply_text('Отлично! Спасибо за регистрацию!')
        await update.message.reply_text('Как только кто-то захочет сделать у Вас заказ, мы Вас оповестим!')

    return 5


async def finding_orders(update, context):
    cursor = bd.cursor()
    tgnik = update.effective_user.username

    result_b = cursor.execute(f"""SELECT * FROM Buyers
                            WHERE tg_nik = ?""", (tgnik,)).fetchall()

    needed_city = result_b[0][2]
    cursor = bd.cursor()
    needed_orders = cursor.execute(f"""SELECT * FROM Sellers
                                WHERE city = ?""", (needed_city,)).fetchall()

    if needed_orders:
        cursor = bd.cursor()
        needed_orders1 = cursor.execute(f"""SELECT * FROM Needed
                                        WHERE b = ?""", (
            (update.effective_user.username),)).fetchall()
        if needed_orders1:
            sql_delete_query = """DELETE FROM Needed WHERE b = ?"""

            cursor.execute(sql_delete_query, (tgnik,))
            bd.commit()

        sqlite_insert_query = """INSERT INTO Needed
                              (b, ssids)
                              VALUES
                              (?, ?);"""

        cursor = bd.cursor()
        s_list = [i[6] for i in needed_orders]
        data_tuple = (update.effective_user.username, ','.join(s_list))
        cursor.execute(sqlite_insert_query, data_tuple)
        bd.commit()
        await update.message.reply_text(f'Для Вас найдено {len(needed_orders)} предложений:')
        await show_anket(update, context)

    else:
        await update.message.reply_text('В вашем городе ничего не найдено😭\nПопробуйте позже.')


async def show_anket(update, context):
    print(1)
    tgnik = update.effective_user.username

    cursor = bd.cursor()
    mb_orders = cursor.execute(f"""SELECT * FROM Needed
                                    WHERE b = ?""", (tgnik,)).fetchall()
    if mb_orders:
        if mb_orders[0][1]:
            mb_order = list(mb_orders[0][1].split(','))[0]
            print(mb_order)
            sqlite_insert_query = """INSERT INTO Watching
                                  (user_b, user_s)
                                  VALUES
                                  (?, ?);"""


            cursor = bd.cursor()
            data_tuple = (update.effective_user.username, mb_order)
            cursor.execute(sqlite_insert_query, data_tuple)
            bd.commit()
            shown_order = cursor.execute(f"""SELECT * FROM Sellers
                                            WHERE tg_nik = ?""", (mb_order,)).fetchall()[0]

            print(shown_order)
            marks = list(map(int, shown_order[4].split(',')))
            av_m = sum(marks) / len(marks)
            ans = (f'{shown_order[1]}\nОписание: {shown_order[2]}\nПрошел проверку: {shown_order[3]}\nРейтинг пользователей: {av_m}')


            all_mb_order = list(mb_orders[0][1].split(','))
            if len(all_mb_order) >= 2:
                all_mb_order1 = all_mb_order[1:]
            else:
                all_mb_order1 = []
            sqlite_insert_query = """UPDATE Needed SET ssids = ? WHERE b = ?"""
            print('---',mb_order)
            bd.cursor().execute(sqlite_insert_query,
                                (str(','.join(list(all_mb_order1))), update.effective_user.username))
            bd.commit()

            reply_markup1 = InlineKeyboardMarkup(inline_keyboard)
            if update.message:
                await update.message.reply_text(ans)
                await update.message.reply_text('Сделать заказ?', reply_markup=reply_markup1)
            elif update.callback_query:
                await update.callback_query.message.reply_text(ans)
                await update.callback_query.message.reply_text('Сделать заказ?', reply_markup=reply_markup1)
        else:
            if update.message:
                await update.message.reply_text('Вы просмотрели все доступные предложения. \nЧтобы посмотреть заново, выберите команду /new_order')
            elif update.callback_query:
                await update.callback_query.message.reply_text('Вы просмотрели все доступные предложения. \nЧтобы посмотреть заново, выберите команду /new_order')



async def button(update, context):
    query = update.callback_query
    await query.answer()
    if int(query.data) == 1:
        cursor = bd.cursor()
        tgnik = update.effective_user.username

        result_s = cursor.execute(f"""SELECT * FROM Watching
                                WHERE user_b = ?""", (tgnik,)).fetchall()
        seller = result_s[-1][2]

        tgnik = update.effective_user.username
        sqlite_insert_query = """INSERT INTO Orders
                              (buyer, seller, time, accepted)
                              VALUES
                              (?, ?, ?, ?);"""

        cursor = bd.cursor()
        data_tuple = (tgnik, seller, str(datetime.now()), 'нет')
        cursor.execute(sqlite_insert_query, data_tuple)
        bd.commit()
        await query.edit_message_text('👍')
        await ask_for_m(update, context)
    else:
        await query.edit_message_text('👎')
        if query.message:
            await show_anket(update, context)
async def ask_for_m(update, context):
    if update.message:
        await update.message.reply_text('Напишите о ваших пожеланиях к заказу, и мы передадим их продавцу')
    elif update.callback_query:
        await update.callback_query.message.reply_text('Напишите о ваших пожеланиях к заказу, и мы передадим их продавцу')
    return 5



async def getting_message(update, context):
    print(1)
    message = update.message.text
    print(message)
    tgnik = update.effective_user.username

    cursor = bd.cursor()
    my_orders = cursor.execute(f"""SELECT * FROM Orders
                                            WHERE buyer = ?""", (tgnik,)).fetchall()
    seller = my_orders[-1][2]

    sqlite_insert_query = """UPDATE Orders SET message = ? WHERE buyer = ? AND seller = ?"""
    bd.cursor().execute(sqlite_insert_query,
                        (message, tgnik, seller))
    bd.commit()
    print('done')


async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(

        entry_points=[CommandHandler('start', start)],

        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_role)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_name)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_city)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_description)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_message)],


        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getting_role", getting_role))
    application.add_handler(CommandHandler("getting_name", getting_name))
    application.add_handler(CommandHandler("getting_city", getting_city))
    application.add_handler(CommandHandler("getting_description", getting_description))
    application.add_handler(CommandHandler("getting_message", getting_message))
    application.add_handler(CommandHandler("new_order", finding_orders))
    application.add_handler(CommandHandler("show_anket", show_anket))

    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == '__main__':
    main()
