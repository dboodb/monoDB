import telebot
from pymongo import MongoClient
from random import randint, uniform
from config import token, mongotoken

# Токен бота
bot = telebot.TeleBot(token, parse_mode=None)

# Подключение БД
cluster = MongoClient(mongotoken)
db = cluster["mongobot"]
collection = db["mongo"]


# Переменные


# Регистрация
@bot.message_handler(commands=['start', 'reg'])
def reg_user(message):
    telegram_id = message.from_user.id
    if collection.count_documents({"telegram_id": telegram_id}) == 0:
        nick = bot.send_message(message.chat.id, 'Введите ваш ник:')
        bot.register_next_step_handler(nick, nick_create)
    else:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы!\nСписок команд: /help')


def nick_create(message):
    nick = message.text
    name = message.from_user.first_name
    telegram_id = message.from_user.id
    username = message.from_user.username
    id_reg = 1
    while collection.count_documents({"_id": id_reg}) != 0:
        id_reg += 1
    if collection.count_documents({"_id": id_reg}) == 0:
        collection.insert_one({"_id": id_reg, "name": name, "nick": nick, "telegram_id": telegram_id,
                               "username": username, "admin": 0, "balance": 10000})
        bot.send_message(message.chat.id, f"Успешно зарегистрированы!\nСписок команд: /help")
        print(f'Новый участник: {name}')


# Старт / помощь
@bot.message_handler(commands=['help', 'помощь'])
def help_reg(message):
    telegram_id = message.from_user.id
    admin = collection.find_one({"telegram_id": telegram_id})["admin"]
    bot.send_message(message.chat.id,
                     "Мои команды:\n👤Просмотреть свой профиль: Профиль\n🤑Узнать баланс: Баланс\n"
                     "🆘Отправить вопрос: репорт\n💵Передать средства: передать"
                     "\n\nИгры:\n  🎰Казино")
    if admin == 1:
        bot.send_message(message.chat.id, 'Админские команды:\n'
                                          ' 1 уровень: \n   /setbalance - установить баланс пользователю\n'
                                          '   /admins - вывести список всех админов\n'
                                          '   /getid - получить ид\n'
                                          '   /getinfo - получить инфо об игроке\n')
    elif admin > 1:
        bot.send_message(message.chat.id, 'Админские команды:\n'
                                          ' 1 уровень:\n   /setbalance - установить баланс пользователю\n'
                                          '   /admins - вывести список всех админов\n'
                                          '   /getid - получить ид\n'
                                          '   /getinfo - получить инфо об игроке\n'
                                          ' 2 уровень:\n   /setadmin - выдать права администратора\n'
                                          '   /deladmin - забрать права администратора\n'
                                          '   /delakk - удалить аккаунт игроку')


# Казино
@bot.message_handler(commands=['casino'])
def game_casino(message):
    dice = bot.send_message(message.chat.id, 'Ваша ставка: ')
    bot.register_next_step_handler(dice, dice_start)


def dice_start(message):
    telegram_id = message.from_user.id
    dice = float(message.text)
    kof = randint(1, 2)
    balance = collection.find_one({"telegram_id": telegram_id})["balance"]
    if balance < dice:
        bot.send_message(message.chat.id, 'У вас недостаточно средст для игры 😔')
    else:
        if kof == 1:
            kof_dice = uniform(1.5, 1.3)
            win = int(dice * kof_dice)
            balance = collection.find_one({"telegram_id": telegram_id})["balance"]
            bot.send_message(message.chat.id, f'🤑Ваш выигрышь составляет: {win}')
            collection.update_one({"telegram_id": telegram_id}, {"$set": {"balance": balance + win}})
        elif kof == 2:
            balance = collection.find_one({"telegram_id": telegram_id})["balance"]
            bot.send_message(message.chat.id, f'😞Вы проиграли(')
            collection.update_one({"telegram_id": telegram_id}, {"$set": {"balance": balance - dice}})


# ------Админ команды---------------------------------------------------------------------------------
# Установка баланса
@bot.message_handler(commands=['setbalance'])
def admin_setbalance(message):
    telegram_id = message.from_user.id
    admin = collection.find_one({"telegram_id": telegram_id})["admin"]
    if admin < 1:
        bot.send_message(message.chat.id, 'Вы не админ 😢')
    else:
        user_telegram_id = bot.send_message(message.chat.id, 'Введите ид пользователя: ')
        bot.register_next_step_handler(user_telegram_id, setbalance)


def setbalance(message):
    user_telegram_id = int(message.text)
    if collection.count_documents({"telegram_id": user_telegram_id}) == 0:
        bot.send_message(373112925, 'Аккаунт с таким id не найден в Базе Данных. 🔴')
    else:
        admin_telegram_id = message.from_user.id
        admin_name = collection.find_one({"telegram_id": admin_telegram_id})["name"]
        money = 100000
        user_name = collection.find_one({"telegram_id": user_telegram_id})["name"]
        collection.update_one({"telegram_id": user_telegram_id}, {"$set": {"balance": money}})
        bot.send_message(message.chat.id, f"Пользователю {user_name} установлен счёт {money} ✅")
        bot.send_message(user_telegram_id, f'Администратор {admin_name} установил вам счет {money} 🤑')


# Выдача админки
@bot.message_handler(commands=['setadmin'])
def set_adm_lvl(message):
    telegram_id = message.from_user.id
    admin = collection.find_one({"telegram_id": telegram_id})["admin"]
    if admin == 0:
        bot.send_message(message.chat.id, 'Вы не админ 😢')
    elif admin == 1:
        bot.send_message(message.chat.id, 'Вы у вас недостаточный уровень админки 😢')
    else:
        user_telegram_id = bot.send_message(message.chat.id, 'Введите ид пользователя: ')
        bot.register_next_step_handler(user_telegram_id, setadmin)



def setadmin(message):
    user_telegram_id = int(message.text)
    if collection.count_documents({"telegram_id": user_telegram_id}) == 0:
        bot.send_message(373112925, 'Аккаунт с таким id не найден в Базе Данных. 🔴')
    else:
        user_admin = collection.find_one({"telegram_id": user_telegram_id})["admin"]
        user_name = collection.find_one({"telegram_id": user_telegram_id})["name"]
        admin_telegram_id = message.from_user.id
        admin_name = collection.find_one({"telegram_id": admin_telegram_id})["name"]
        if user_admin == 0:
            collection.update_one({"telegram_id": user_telegram_id}, {"$set": {"admin": 1}})
            bot.send_message(message.chat.id, f'Пользователю {user_name} установлены права администратора ✅')
            bot.send_message(user_telegram_id, f'Администратор {admin_name} выдал вам права администратора 😄')
        else:
            bot.send_message(message.chat.id, 'Пользователь уже имеет права администратора 🔴')


# Забрать админку
@bot.message_handler(commands=['deladmin'])
def del_adm_lvl(message):
    telegram_id = message.from_user.id
    admin = collection.find_one({"telegram_id": telegram_id})["admin"]
    if admin == 0:
        bot.send_message(message.chat.id, 'Вы не админ 😢')
    elif admin == 1:
        bot.send_message(message.chat.id, 'У вас недостаточно прав админки 😢')
    else:
        user_telegram_id = bot.send_message(message.chat.id, 'Введите ид пользователя: ')
        bot.register_next_step_handler(user_telegram_id, deladmin)


def deladmin(message):
    user_telegram_id = int(message.text)
    if collection.count_documents({"telegram_id": user_telegram_id}) == 0:
        bot.send_message(373112925, 'Аккаунт с таким id не найден в Базе Данных. 🔴')
    else:
        user_admin = collection.find_one({"telegram_id": user_telegram_id})["admin"]
        user_name = collection.find_one({"telegram_id": user_telegram_id})["name"]
        admin_telegram_id = message.from_user.id
        admin_name = collection.find_one({"telegram_id": admin_telegram_id})["name"]
        if user_admin == 1:
            collection.update_one({"telegram_id": user_telegram_id}, {"$set": {"admin": 0}})
            bot.send_message(message.chat.id, f'У пользователя {user_name} убраны права администратора ✅')
            bot.send_message(user_telegram_id, f'Администратор {admin_name} забрал у вас права администратора 😒')
        else:
            bot.send_message(message.chat.id, 'У пользователя нет прав администратора 🔴')


# Удаление аккаунта
@bot.message_handler(commands=['delakk'])
def del_user_akk(message):
    telegram_id = message.from_user.id
    admin = collection.find_one({"telegram_id": telegram_id})["admin"]
    if admin == 0:
        bot.send_message(message.chat.id, 'Вы не админ 😢')
    elif admin == 1:
        bot.send_message(message.chat.id, 'У вас недостаточно прав админки 😢')
    else:
        user_telegram_id = bot.send_message(message.chat.id, 'Введите ид пользователя: ')
        bot.register_next_step_handler(user_telegram_id, delakk)


def delakk(message):
    user_telegram_id = int(message.text)
    if collection.count_documents({"telegram_id": user_telegram_id}) == 0:
        bot.send_message(373112925, 'Аккаунт с таким id не найден в Базе Данных. 🔴')
    else:
        user_name = collection.find_one({"telegram_id": user_telegram_id})["name"]
        admin_telegram_id = message.from_user.id
        admin_name = collection.find_one({"telegram_id": admin_telegram_id})["name"]
        if user_telegram_id is None:
            bot.send_message(user_telegram_id, f'Такого аккаунта не существует😒')
        else:
            collection.delete_one({"telegram_id": user_telegram_id})
            bot.send_message(user_telegram_id, f'Администратор {admin_name} удалил ваш аккаунт в боте 😢')
            bot.send_message(message.chat.id, f'Вы успешно удалили аккаунта пользователя {user_name} ✅')


# Список админов
@bot.message_handler(commands=["admins"])
def admin_list(message):
    user_telegram_id = message.from_user.id
    user_admin = collection.find_one({"telegram_id": user_telegram_id})["admin"]
    if user_admin > 0:
        admins = collection.find({"admin": 1})
        count_admin = collection.count_documents({'admin': 1})
        bot.send_message(message.chat.id, f'Всего 1 уровней: {count_admin}')
        for b in admins:
            adm_name = b["name"]
            adm_telegram_id = b["telegram_id"]
            bot.send_message(message.chat.id, f'Имя: {adm_name}, Ид: {adm_telegram_id}')
        admins = collection.find({"admin": 2})
        count_admin = collection.count_documents({'admin': 2})
        bot.send_message(message.chat.id, f'Всего 2 уровней: {count_admin}')
        for b in admins:
            adm_name = b["name"]
            adm_telegram_id = b["telegram_id"]
            bot.send_message(message.chat.id, f'Имя: {adm_name}, Ид: {adm_telegram_id}')
    else:
        bot.send_message(message.chat.id, 'Вы не админ!')




# Узнать ид игрока
@bot.message_handler(commands=['getid'])
def get_user_id(message):
    telegram_id = message.from_user.id
    admin = collection.find_one({"telegram_id": telegram_id})["admin"]
    if admin == 0:
        bot.send_message(message.chat.id, 'Вы не админ 😢')
    else:
        user_telegram_username = bot.send_message(message.chat.id, 'Введите короткое имя пользователя: ')
        bot.register_next_step_handler(user_telegram_username, get_id)


def get_id(message):
    user_telegram_username = str(message.text)
    if collection.count_documents({"username": user_telegram_username}) == 0:
        bot.send_message(373112925, 'Аккаунт с таким id не найден в Базе Данных. 🔴')
    else:
        user_id = collection.find_one({"username": user_telegram_username})["telegram_id"]
        bot.send_message(message.chat.id, user_id)


# Инфо о пользователе
@bot.message_handler(commands=['getinfo'])
def get_info(message):
    telegram_id = message.from_user.id
    admin = collection.find_one({"telegram_id": telegram_id})["admin"]
    if admin == 0:
        bot.send_message(message.chat.id, 'Вы не админ 😢')
    else:
        user_info = bot.send_message(message.chat.id, 'Введите id пользователя: ')
        bot.register_next_step_handler(user_info, get_user_info)


def get_user_info(message):
    user_telegram_id = int(message.text)
    if collection.count_documents({"telegram_id": user_telegram_id}) == 0:
        bot.send_message(373112925, 'Аккаунт с таким id не найден в Базе Данных. 🔴')
    else:
        user_id = collection.find_one({"telegram_id": user_telegram_id})["_id"]
        user_name = collection.find_one({"telegram_id": user_telegram_id})["name"]
        user_nick = collection.find_one({"telegram_id": user_telegram_id})["nick"]
        user_username = collection.find_one({"telegram_id": user_telegram_id})["username"]
        user_admin = collection.find_one({"telegram_id": user_telegram_id})["admin"]
        user_balance = collection.find_one({"telegram_id": user_telegram_id})["balance"]
        bot.send_message(message.chat.id, f'👤Информация о пользоваетеле @{user_username}:\n'
                                          f'😎Ид: {user_id}\n'
                                          f'😇Имя: {user_name}\n'
                                          f'🤩Ник: {user_nick}\n'
                                          f'🙊Ид телеграм: {user_telegram_id}\n'
                                          f'👤Короткое имя: @{user_username}\n'
                                          f'💪Уровень админки: {user_admin}\n'
                                          f'💰Баланс: {user_balance}')


# ----------------------------------------------------------------------------------------------------

# Текстовые команды
@bot.message_handler(content_types=['text'])
def on_text(message):
    btn = message.text.lower()
    if btn == 'профиль':
        show_profile(message)
    elif btn == 'баланс':
        show_balance(message)
    elif btn == 'репорт':
        report_send(message)
    elif btn == 'передать':
        trade(message)
    elif btn == 'помощь':
        help(message)


# Профиль
def show_profile(message):
    if message.text.lower() == 'профиль':
        telegram_id = message.from_user.id
        user_id = collection.find_one({"telegram_id": telegram_id})["_id"]
        admin = collection.find_one({"telegram_id": telegram_id})["admin"]
        name = collection.find_one({"telegram_id": telegram_id})["name"]
        nick = collection.find_one({"telegram_id": telegram_id})["nick"]
        telegram_id = collection.find_one({"telegram_id": telegram_id})["telegram_id"]
        balance = collection.find_one({"telegram_id": telegram_id})["balance"]
        if admin == 0:
            bot.send_message(message.chat.id,
                             f'😎Ваш id: {user_id}\n😇Ваше имя: {name}\n🤩Ваш ник: {nick}\n🙊Телаграм id: {telegram_id}'
                             f'\n💰Баланс: {balance}')
        else:
            bot.send_message(message.chat.id,
                             f'😎Ваш id: {user_id}\n😇Ваше имя: {name}\n🤩Ваш ник: {nick}\n🙊Телаграм id: {telegram_id}\n'
                             f'👑Уровень админки: {admin}\n💰Баланс: {balance}')


# Баланс
def show_balance(message):
    if message.text.lower() == 'баланс':
        telegram_id = message.from_user.id
        balance = collection.find_one({"telegram_id": telegram_id})["balance"]
        bot.send_message(message.chat.id, f'💰Ваш баланс: {balance}')


# Репорт
def report_send(message):
    if message.text.lower() == 'репорт':
        report = bot.send_message(message.chat.id, 'Введите ваш вопрос: ')
        bot.register_next_step_handler(report, send_report)


def send_report(message):
    report = str(message.text)
    creater_id = collection.find_one({"admin": 2})["telegram_id"]
    user_telegram_id = message.from_user.id
    user_name = collection.find_one({"telegram_id": user_telegram_id})["name"]
    user_username = collection.find_one({"telegram_id": user_telegram_id})["username"]
    bot.send_message(creater_id,
                     f'Поступил репорт от игрока {user_name}, ид игрока {user_telegram_id}.\nРепорт:\n{report}\n'
                     f'Ответить пользователю: @{user_username}')
    bot.send_message(message.chat.id, f'Вы успешно отправили Ваш вопрос, ожидайте, в скором времени вам ответят ✅')


# Передать средства
def trade(message):
    if message.text.lower() == 'передать':
        id_trade = bot.send_message(message.chat.id, 'Введите id кому передать: ')
        bot.register_next_step_handler(id_trade, trade_send)


def trade_send(message):
    id_trade = int(message.text)
    if collection.count_documents({"telegram_id": id_trade}) == 0:
        bot.send_message(373112925, 'Аккаунт с таким id не найден в Базе Данных. 🔴')
    else:
        id_trade_name = collection.find_one({"telegram_id": id_trade})["name"]
        trade_balance = collection.find_one({"telegram_id": id_trade})["balance"]
        user_telegram_id = message.from_user.id
        user_name = collection.find_one({"telegram_id": user_telegram_id})["name"]
        user_balance = collection.find_one({"telegram_id": user_telegram_id})["balance"]
        if user_balance < 10000:
            bot.send_message(message.chat.id, 'На вашем счету недостаточно средств!')
        else:
            bot.send_message(message.chat.id, f'Вы успешно передали 10000 игроку {id_trade_name}!')
            collection.update_one({"telegram_id": user_telegram_id}, {"$set": {"balance": user_balance - 10000}})
            bot.send_message(id_trade, f'Игрок {user_name} перевел вам 10000 со своего счета.')
            collection.update_one({"telegram_id": id_trade}, {"$set": {"balance": trade_balance + 10000}})


bot.polling(none_stop=True, interval=0)
