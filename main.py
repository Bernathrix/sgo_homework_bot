import asyncio
import requests
import json
from contextlib import suppress
import hashlib
import codecs
import binascii
import datetime as dt
from datetime import timedelta, datetime
from aiogram import Bot, Dispatcher, executor, types, filters
import cfg
import os
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import textwrap
from aiogram.utils.exceptions import (MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted,
                                      MessageToDeleteNotFound)



#Feeling some data
API_TOKEN = cfg.token
headers = cfg.headers
payload = cfg.payload
default = "нет домашнего задания"

#Creating bot
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

#function to delete media gruup message
async def delete_group_message(message):
    for i in message:
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await i.delete()

#From sgo data_format to datatime object + weekDay
def parser_date(date):
    year = date[0:4]
    month = date[5:7]
    day = date[8:10]
    date_str = "{}-{}-{} 17:00:00".format(year, month, day)
    date_time_obj = dt.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    weekDay = datetime.weekday(date_time_obj)
    today = ""
    match weekDay:
        case 0:
            today = "Понедельник"
        case 1:
            today = "Вторник"
        case 2:
            today = "Среда"
        case 3:
            today = "Четверг"
        case 4:
            today = "Пятница"
        case 5:
            today = "Суббота"
        case 6:
            today = "Воскресенье"
    return [date_time_obj, today]

#next school day
def today():
    now = datetime.now()
    weekDay = datetime.weekday(now)
    if weekDay == 5:
        now = now + timedelta(2)
        return now
    elif weekDay == 6:
        now = now + timedelta(1)
        return now
    if int(now.strftime("%H")) < 7:
        return now
    else:
        now = now + timedelta(1)
    return now

#current week + next week
def week_data():
    now = datetime.now()
    weekDay = datetime.weekday(now)
    weekStart = now - timedelta(weekDay)
    weekEnd = weekStart + timedelta(6)
    dict = {
        'weekStart': weekStart.strftime("%Y-%m-%d"),
        'weekEnd': weekEnd.strftime("%Y-%m-%d"),
        'nextWeekStart': (weekStart + timedelta(7)).strftime("%Y-%m-%d"),
        'nextWeekEnd': (weekEnd + timedelta(7)).strftime("%Y-%m-%d"),
    }
    if weekDay == 5 or weekDay == 4 or weekDay == 6:
        dict['weekStart'], dict['weekEnd'] = dict['nextWeekStart'], dict['nextWeekEnd']
    return dict

#autoruzation to sgo
def autorization(payload):
    login = payload['login']
    password = payload['password']
    with requests.Session() as s:
        get_data = s.post('https://sgo.e-mordovia.ru/webapi/auth/getdata', headers=headers)
        if get_data.status_code != 200:
            return get_data
        else:
            data1 = json.loads(get_data.text)
            salt = data1['salt']
            pw2 = str(binascii.hexlify(hashlib.md5(bytes(salt + str(binascii.hexlify(hashlib.md5(bytes(password, 'utf-8')).digest()))[2:34], 'utf-8')).digest()))[2:34]
            pw = pw2[:len(password)]
            data = {
                #Here u can use ur school id's, default is: Республика Мордовия, г. Рузаевка, Общеобразовательная "Лицей №4"
                'LoginType': '1',
                'cid': '2',
                'sid': '13',
                'pid': '-1258',
                'cn': '1258',
                'sft': '2',
                'scid': '1088',
                #some login data
                'UN': login,
                'PW': pw,
                'lt': data1['lt'],
                'pw2': pw2,
                'ver': data1['ver'],
            }
            login = s.post('https://sgo.e-mordovia.ru/webapi/login', headers=headers, data=data)
            return login

#class to save previous messages
class Storage():

    def __init__(self):
        self.x = 0
        self.links = []

    def find_link(self, assignment):
        for i in assignment.split(' '):
            if len(i) > 5:
                if i[:4] == "http":
                    self.links.append(i)
                    break

    def show_links(self):
        list1 = self.links
        self.links = []
        return list1

    def set(self, key):
        self.x = key

    def get(self):
        return self.x

#creating object of this class
storage = Storage()

#get all unparsed week_data
def get_assigns(login, data):
    login_info = json.loads(login.text)
    headers2 = headers
    studentId = login_info['accountInfo']['user']['id']
    headers2['at'] = login_info['at']
    dict = {
        'ESRNSec': login.cookies.get_dict()['ESRNSec'],
    }
    params = {
        'studentId': studentId,
        'weekEnd': data['weekEnd'],
        'weekStart': data['weekStart'],
        'withLaAssigns': 'true',
        'yearId': '4301',
    }
    lessons_list = requests.get('https://sgo.e-mordovia.ru/webapi/student/diary', params=params, cookies=dict, headers=headers2)
    return lessons_list

#If threre is no homework returns default
def check_on_assignment(lesson):
    for k in lesson:
        if k == 'assignments':
            return lesson[k][0]['assignmentName']
        else:
            continue
    return default

#Drawer of the image
def drawe_the_day(day):
    date = parser_date(day['date'])
    image = Image.open('pattern.jpg')  # /root/bot/
    default_font = ImageFont.truetype("/root/bot/impact.ttf", size=50)
    small_font = ImageFont.truetype("/root/bot/impact.ttf", size=40)
    draw_text = ImageDraw.Draw(image)
    date_str = "{}: {}".format(date[1], date[0].strftime("%d.%m.%Y"))
    draw_text.text(
        (1430, 20),
        date_str,
        font=small_font,
        fill="#ffffff",
    )
    i = 0
    dif = 0
    for lesson in day['lessons']:
        if i == 0 and lesson['number'] == 2:
            dif = 1
            i += 1
        else:
            i += 1
        if "Родной язык (русский)" == lesson['subjectName']:
            lesson['subjectName'] = "Родной язык"
        if "Основы безопасности жизнедеятельности" == lesson['subjectName']:
            lesson['subjectName'] = "ОБЖ"
        if "Обществознание" == lesson['subjectName']:
            lesson['subjectName'] = "Общество."
        bruh_line = ""
        our_line = "{}. {}".format(lesson['number'], lesson['subjectName'])
        lines = textwrap.wrap(our_line, width=15)
        if len(lines) > 1:
            for line in lines:
                bruh_line += line + "\n     "
        else:
            bruh_line = our_line
        box = cfg.box
        # Name
        draw_text.text(
            box["{}".format(lesson['number'] - dif)],
            bruh_line,
            font=default_font,
            fill="#000000",
        )
        # Info
        bruh_line = ""
        checking = check_on_assignment(lesson)
        storage.find_link(checking)
        lines = textwrap.wrap(checking, width=60)
        if len(lines) > 1:
            for line in lines:
                bruh_line += line + "\n"
        else:
            bruh_line = check_on_assignment(lesson)
        draw_text.text(
            box["{}-as".format(lesson['number'] - dif)],
            bruh_line,
            font=default_font,
            fill="#000000",
        )
    for i in range(5):
        if os.path.exists("result{}.jpg".format(i)) == True:
            continue
        else:
            image.save("result{}.jpg".format(i))
            break

#Function to check sgo for new homework every 1 minute
async def find_new_assigns(message):
    do_login = autorization(payload)
    i = 0
    j = 0
    old_lessons = ""
    new_lessons = ""
    old_lessons_1 = ""
    new_lessons_1 = ""
    if do_login.status_code != 200:
        print(do_login.text)
        return await message.answer("Автоматический поиск дз остановлен. Текст ошибки в консоли")

    else:
        print("Autorization successful {}".format(do_login.status_code))
        cookies = True
        while True:
            week_info = week_data()

            #current_week

            week = {
                'weekStart': week_info['weekStart'],
                'weekEnd': week_info['weekEnd'],
            }
            lessons_list = get_assigns(do_login, week)
            if lessons_list.status_code != 200:
                cookies = False
                break
            else:
                print("Assignments are gotten {}".format(lessons_list.status_code))
                new_lessons = json.loads(lessons_list.text)
                if i == 0:
                    i += 1
                    old_lessons = new_lessons
                    continue
                if old_lessons == new_lessons:
                    print("they are the same on this week")
                    print(week_info)
                else:
                    print("I found New Assignment")
                    list_of_new = dif_lessons(old_lessons, new_lessons)
                    old_lessons = new_lessons
                    for new in list_of_new:
                        date = parser_date(new['day'])
                        final_str = "*Новое домашнее задание!* \n *Дата: {}, {}* \n".format(date[1], date[0].strftime("%d.%m.%Y"))
                        final_str += "*{}. {}:* _{}_ \n".format(new['number'], new['subject'], new['assignment'])
                        await message.answer(final_str, parse_mode="Markdown")

            #next_week

            week = {
                'weekStart': week_info['nextWeekStart'],
                'weekEnd': week_info['nextWeekEnd'],
            }

            lessons_list = get_assigns(do_login, week)
            if lessons_list.status_code != 200:
                cookies = False
                break
            else:
                print("Assignments are gotten {}".format(lessons_list.status_code))
                new_lessons_1 = json.loads(lessons_list.text)
                if j == 0:
                    j += 1
                    old_lessons_1 = new_lessons_1
                    continue
                #new_lessons_1['weekDays'][0]['lessons'][4]['assignments'] = [{'assignmentName': "idi nahuy"}]
                if old_lessons_1 == new_lessons_1:
                    print("they are the same on next week")
                    await asyncio.sleep(60)
                    continue
                else:
                    print("I found New Assignment")
                    list_of_new = dif_lessons(old_lessons_1, new_lessons_1)
                    old_lessons_1 = new_lessons_1
                    for new in list_of_new:
                        date = parser_date(new['day'])
                        final_str = "*Новое домашнее задание!* \n*{}: {}* \n".format(date[1], date[0].strftime(
                            "%d.%m.%Y"))
                        final_str += "*{}. {}:* _{}_ \n".format(new['number'], new['subject'], new['assignment'])
                        await message.answer(final_str, parse_mode="Markdown")
            await asyncio.sleep(60)

        if cookies == False:
            return await find_new_assigns(message)

#Function to return image of the day
def show_lessons(lessons, mode='default'):
    if mode == 'default':
        for day in lessons['weekDays']:
            drawe_the_day(day)
    elif mode == 'tomorrow':
        today1 = today()
        date = today1.strftime('%Y-%m-%dT00:00:00')
        check = 0
        for day in lessons['weekDays']:
            print(date)
            if day['date'] != date:
                need_date1 = parser_date(day['date'])[0]
                if today1 < need_date1:
                    return drawe_the_day(day)
                continue
            else:
                return drawe_the_day(day)
        if check == 0:
            image = Image.open("wrf.jpg")
            return image.save("result0.jpg")


#Find dofferens between 2 weeks
def dif_lessons(old_lessons, new_lessons):
    list_of_new = []
    for i in range(len(new_lessons['weekDays'])):
        day_old = old_lessons['weekDays'][i]
        day_new = new_lessons['weekDays'][i]
        for j in range(len(day_new['lessons'])):
            lessons_old = day_old["lessons"][j]
            lessons_new = day_new["lessons"][j]
            if check_on_assignment(lessons_new) != check_on_assignment(lessons_old):
                list_of_new.append({'day': day_new['date'], 'number': lessons_new['number'], 'subject': lessons_new['subjectName'], 'assignment': check_on_assignment(lessons_new)})
            else:
                continue
    return list_of_new


#Start finder of new homeworks
@dp.message_handler(commands=['поехали'])
async def find_new_assigns1(message: types.Message):
    await message.answer("Автоматический поиск дз запущен")
    await find_new_assigns(message)


#Send tomorrow photo
@dp.message_handler(commands=['завтра'])
async def diary(message: types.Message):
    do_login = autorization(payload)
    if do_login.status_code != 200:
        print(do_login.text)
        return await message.answer("Я в душе не ебу, но код ошибки в консоли")
    else:
        lessons_list = get_assigns(do_login, week_data())
        if lessons_list.status_code != 200:
            print(lessons_list.text)
            return await message.answer("Я в душе не ебу, но код ошибки в консоли")
        else:
            x = storage.get()
            if x != 0:
                await delete_group_message(x)
            await types.ChatActions.upload_photo()
            show_lessons(json.loads(lessons_list.text), 'tomorrow')
            media = types.MediaGroup()
            media.attach_photo(types.InputFile('result0.jpg'))
            previous_message = await message.reply_media_group(media=media)
            links = storage.show_links()
            for link in links:
                mes = await message.answer(link)
                previous_message.append(mes)
            storage.set(previous_message)
            os.remove("result0.jpg")


#send photo of whole current week
@dp.message_handler(commands=['неделя'])
async def diary1(message: types.Message):
    do_login = autorization(payload)
    if do_login.status_code != 200:
        print(do_login.text)
        return await message.answer("Я в душе не ебу, но код ошибки в консоли")
    else:
        lessons_list = get_assigns(do_login, week_data())
        if lessons_list.status_code != 200:
            print(lessons_list.text)
            return await message.answer("Я в душе не ебу, но код ошибки в консоли")
        else:
            x = storage.get()
            if x != 0:
                await delete_group_message(x)
            await types.ChatActions.upload_photo()
            show_lessons(json.loads(lessons_list.text))
            check = 0
            media = types.MediaGroup()
            for i in range(5):
                if os.path.exists("result{}.jpg".format(i)) == True:
                    media.attach_photo(types.InputFile('result{}.jpg'.format(i)))
                    check += 1
            if check == 0:
                await message.answer("УРА КАНИКУЛЫ (или какая-то ошибка, я не ебу)")
            else:
                previous_message = await message.reply_media_group(media=media)
                links = storage.show_links()
                for link in links:
                    mes = await message.answer(link)
                    previous_message.append(mes)
                storage.set(previous_message)
            for i in range(5):
                if os.path.exists("result{}.jpg".format(i)) == True:
                    os.remove("result{}.jpg".format(i))


#start our bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
