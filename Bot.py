from aiogram import types, executor, Dispatcher, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
import logging
import datetime
import requests
import calendar


bot = Bot(token=config.token)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
current_datetime = datetime.datetime.now()
users = {}


async def on_start(register_user: bool, message: types.Message):
    user_id = message.from_user.id
    if register_user:
        users[user_id] = {'username': message.from_user.username, 'chat_id': user_id}
        f = open('bd.txt', 'w')
        f.write(str(users))
        f.close()


@dp.message_handler(commands=['start'])
async def button_1(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        await on_start(register_user=True, message=message)

    markup = InlineKeyboardMarkup()
    calendar = InlineKeyboardButton(text="Открыть календарь", callback_data="calendar")
    markup.add(calendar)

    await bot.send_message(message.chat.id, config.textStart, reply_markup=markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data == "calendar")
async def year(call: types.Message):
    reply_markup = InlineKeyboardMarkup(row_width=5)

    keyboard_buttons = [types.InlineKeyboardButton(text=text, callback_data=f'button_year-{text}') for i, text in
                        enumerate([f'{i}' for i in range(2009, int(current_datetime.year) + 1)])]

    reply_markup.add(*keyboard_buttons)

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text='Начнем с выбора года:', reply_markup=reply_markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("button_year-"))
async def month(callback_query: types.CallbackQuery):
    year_ = callback_query.data.split('-')[1]

    reply_markup = InlineKeyboardMarkup(row_width=4)

    keyboard_buttons = [types.InlineKeyboardButton(text=text, callback_data=f'button_month-{i + 1}-{year_}') for i, text in
                        enumerate([f'{i}' for i in range(1, 13)])]
    back = InlineKeyboardMarkup(text='Назад', callback_data='calendar')

    reply_markup.add(*keyboard_buttons)
    reply_markup.add(back)

    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=f'Вы выбрали {year_} год, теперь очередь месяца', reply_markup=reply_markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("button_month-"))
async def day(callback_query: types.CallbackQuery):
    month_ = callback_query.data.split('-')[1]
    year_ = callback_query.data.split('-')[2]
    mx = {
        1: "январь",
        2: "февраль",
        3: "март",
        4: "апрель",
        5: "май",
        6: "июнь",
        7: "июль",
        8: "август",
        9: "сентябрь",
        10: "октябрь",
        11: "ноябрь",
        12: "декабрь"
    }

    reply_markup = InlineKeyboardMarkup(row_width=4)

    keyboard_buttons = [types.InlineKeyboardButton(text=text, callback_data=f'button_day-{text}-{month_}-{year_}') for i, text in
                        enumerate([f'{i}' for i in range(1, calendar.monthrange(int(year_), int(month_))[1] + 1)])]
    back = InlineKeyboardMarkup(text='Назад', callback_data=f'button_year-{year_}')

    reply_markup.add(*keyboard_buttons)
    reply_markup.add(back)
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                text=f'Вы выбрали {mx[int(month_)]} {year_} года, теперь выберем день', reply_markup=reply_markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("button_day-"))
async def cursday(callback_query: types.CallbackQuery):
    day_ = callback_query.data.split('-')[1]
    month_ = callback_query.data.split('-')[2]
    year_ = callback_query.data.split('-')[3]
    base_url = "https://api.coinbase.com/v2/prices/spot?"

    desired_date = f"{year_}-{f'0{month_}' if int(month_) < 10 else month_}-{f'0{day_}' if int(day_) < 10 else day_}"
    url = f"{base_url}currency=USD&date={desired_date}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        bitcoin_price = data["data"]["amount"]

        reply_markup = InlineKeyboardMarkup()

        reply_markup.add(InlineKeyboardButton(text='Заполнить заново', callback_data='calendar'))
        back = InlineKeyboardMarkup(text='Назад', callback_data=f'button_month-{month_}-{year_}')
        reply_markup.add(back)
        await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                                    text=f"Курс BTC на {desired_date.replace('-', '.')}: *${bitcoin_price}*", reply_markup=reply_markup, parse_mode='Markdown')

    else:
        reply_markup = InlineKeyboardMarkup()
        reply_markup.add(InlineKeyboardButton(text='Заполнить заново', callback_data='calendar'))
        back = InlineKeyboardMarkup(text='Назад', callback_data=f'button_month-{month_}-{year_}')
        reply_markup.add(back)
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text='Не удалось получить данные о курсе BTC', reply_markup=reply_markup, parse_mode='Markdown')


if __name__ == '__main__':
    executor.start_polling(dp)
