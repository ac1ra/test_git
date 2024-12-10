import json
import telebot
import datetime
import sqlite3

DB_FILE = 'db_sleepbot.db'


def TG_TOKEN():
    input_token_key = input('Введите ваш токен к телеботу:')
    if input_token_key is None:
        print('Вы ввели пустой ключ. Доступ запрещен.')
    else:
        return telebot.TeleBot(input_token_key)


def create_tables(db_name):
    connect = sqlite3.connect(db_name)
    # connect.execute("PRAGMA foreign_keys = ON;")
    cursor = connect.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT
    )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sleep_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        sleep_time DATETIME,
        wake_time DATETIME DEFAULT NULL,
        sleep_quality INTEGER DEFAULT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sleep_record_id INTEGER,
        text TEXT,
        FOREIGN KEY (sleep_record_id) REFERENCES sleep_records (id)
    )''')

    connect.commit()
    cursor.close()


def add_user(db_name, user_id: int, name: str):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    cursor.execute(
        '''INSERT INTO users (id, name) VALUES (?, ?)''', (user_id, name))
    connect.commit()
    cursor.close()


def add_sleep_records(db_name, sleep_time, wake_time, sleep_quality: int):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    cursor.execute('''
    INSERT INTO sleep_records (user_id,sleep_time,wake_time,sleep_quality) VALUES (?,?,?,?)
    ''', (cursor.lastrowid, sleep_time, wake_time, sleep_quality))
    print(type(cursor.lastrowid), cursor.lastrowid)
    connect.commit()
    cursor.close()


def add_notes(db_name, notetext: str):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()

    cursor.execute(
        '''INSERT INTO notes (sleep_record_id,text) VALUES (?,?)''', (cursor.lastrowid, notetext))

    cursor.execute('''
    SELECT users.id, notes.id FROM users
    JOIN notes ON users.id = notes.sleep_record_id
    ''')
    connect.commit()
    cursor.close()


def get_user_id(db_name, user_id: int):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    searched_user: int | None = cursor.execute(
        '''SELECT id FROM users WHERE id = ?''', (user_id,)).fetchone()
    connect.commit()
    cursor.close()
    if searched_user:
        return searched_user
    return None


def create_user(db_name, user_id: int, name: str) -> None:
    if not get_user_id(db_name=DB_FILE, user_id=user_id):
        add_user(db_name=DB_FILE, user_id=user_id, name=name)


bot = TG_TOKEN()

dict_full = {}
dict_part = {}
list_tuple = ()


@bot.message_handler(commands=['start'])
def start(message):

    if dict_full == {}:
        bot.send_message(
            message.chat.id, f"Привет!Я буду помогать тебе отслеживать параметры сна. Используй команды /sleep, /wake, /quality и /notes.")
    else:
        dict_full.update()
        bot.send_message(
            message.chat.id, f"Привет!Я буду помогать тебе отслеживать параметры сна. Используй команды /sleep, /wake, /quality и /notes.")


convert_date = datetime.datetime.now()


@bot.message_handler(commands=['sleep'])
def start(message):
    bot.send_message(
        message.chat.id, f"Спокойной ночи! Не забудьте сообщить мне, когда проснешься командой /wake.")

    convert_date = datetime.datetime.fromtimestamp(message.date)
    dict_part['start_time'] = convert_date


@bot.message_handler(commands=['wake'])
def start(message):
    end_calc = datetime.datetime.now() - convert_date
    dict_part['duration'] = end_calc.total_seconds()
    if 0 < end_calc.total_seconds() <= 60:
        bot.send_message(
            message.chat.id, f"Доброе утро! Ты проспал около {round(end_calc.total_seconds(), 2)}секунд. Не забудь оценить качество сна командой /quality и оставить заметки командой /notes")

    elif 60 < end_calc.total_seconds() <= 60*60:
        bot.send_message(
            message.chat.id, f"Доброе утро! Ты проспал около {round(end_calc.total_seconds()/60, 2)} минут. Не забудь оценить качество сна командой /quality и оставить заметки командой /notes")
    else:
        bot.send_message(
            message.chat.id, f"Доброе утро! Ты проспал около {round(end_calc.total_seconds()/60*60, 2)} часов. Не забудь оценить качество сна командой /quality и оставить заметки командой /notes")


@bot.message_handler(content_types=['text'])
def catcher(message):
    if '/quality' in message.text:
        point = message.text.split('/quality')[1]
        if point == "":
            bot.send_message(
                message.chat.id, 'Вы не ввел данные. Пожалуйста введите по примеру: /quality 1...10 :')
        else:
            dict_part['quality'] = point
            dict_full[message.from_user.id] = dict_part
            bot.send_message(
                message.chat.id, f"Заметка успешно сохранена!")
            print(message.from_user.id, message.from_user.username)

            create_user(db_name=DB_FILE, user_id=message.from_user.id,
                        name=message.from_user.username)

            add_sleep_records(DB_FILE, dict_part['start_time'], datetime.datetime.today(
            ) + (datetime.datetime.fromtimestamp(
                dict_part['duration'])-datetime.datetime(1970, 1, 1)), point)
            print("Данные успешно внесены в DB")

    elif '/notes' in message.text:
        note = message.text.split('/notes')[1]
        if note == "":
            bot.send_message(
                message.chat.id, 'Вы не ввел данные. Пожалуйста введите по примеру: /notes ... :')
        else:
            dict_part['notes'] = note
            dict_full[message.from_user.id] = dict_part

            with open('sleepbot_log.json', 'a') as json_f:
                json.dump(dict_full, json_f, default=str)

            print(dict_part['notes'])
            add_notes(DB_FILE, dict_part['notes'])

            bot.send_message(message.chat.id, f"Заметка успешно сохранена!")


create_tables(DB_FILE)

bot.polling(none_stop=True)
