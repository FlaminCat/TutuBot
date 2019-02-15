import requests
import config
import parsing
import time
from openpyxl import load_workbook
import telebot
from bs4 import BeautifulSoup
import json


bot = telebot.TeleBot(config.token)
wb = load_workbook(filename='tutu_routes.xlsx', read_only=True)
ws = wb['Лист1']
station_id = {}

for row in ws.rows:
    for cell in range(0, len(row), 2):
        station_id[row[cell].value] = row[cell+1].value


def num_words(text):
    count = 1   # предполагается, что сообщение не пустое
    for i in text:
        if i == ' ':
            count += 1
    return count


def get_id(message):
    if num_words(message) == 2:
        departure, destination = message.split()
        if departure == destination:
            return None
        departure_id = []
        destination_id = []
        for station in station_id.keys():
            if departure == station:
                departure_id = []
                departure_id.append(station_id[station])
                break
            else:
                if departure in station:
                    departure_id.append(station_id[station])
        for station in station_id.keys():
            if destination == station:
                destination_id = []
                destination_id.append(station_id[station])
                break
            else:
                if destination in station:
                    destination_id.append(station_id[station])
        ids = [departure_id, destination_id]
        return ids

    else:
        return None


def all_routes(message):
    if get_id(message):
        ids = get_id(message)
        departure_id, destination_id = ids[0], ids[1]
        headers = {"Accept-Language": "en-US,en;q=0.5"}
        trips = []

        for departure_station in departure_id:
            for destination_station in destination_id:
                url = 'https://suggest.travelpayouts.com/search?service=tutu_trains&term={departure}&term2=' \
                      '{destination}'.format(departure=departure_station, destination=destination_station)
                response = requests.get(url, headers=headers)
                if json.loads(response.text):
                    trips += json.loads(response.text)['trips']

        if trips:
            return trips

    else:
        return None


@bot.message_handler(commands=['start', 'commands'])
def commands_list(message):
    bot.send_message(message.chat.id, "Use following commands:\n/fast *From* *To* - to get the fastest train\n"
                                      "/cheap *From* *To* - to get the cheapest trains\n"
                                      "Or type: *From* *To* *Date* - to find and book tickets on date",
                     parse_mode='HTML')


@bot.message_handler(commands=['fast'])
def get_fastest(message):
    text = message.text.replace('/fast ', '')
    if all_routes(text):
        trips = all_routes(text)

        # find fastest one
        min_time = trips[0]['travelTimeInSeconds']
        fastest_train_number = trips[0]['trainNumber']
        for train in trips:
            if train['travelTimeInSeconds'] < min_time:
                min_time = train['travelTimeInSeconds']
                fastest_train_number = train['trainNumber']

        url = 'https://poezd.ru/raspisanie/{trainNumber}/'.format(trainNumber=fastest_train_number)
        min_time_h = int(min_time) // 3600
        min_time_m = (int(min_time) % 3600) // 60
        bot.send_message(message.chat.id, "Here is the schedule of the fastest train: {url} \nTrip time: "
                                          "{min_time_h}h {min_time_m}m".
                         format(url=url, min_time_h=min_time_h, min_time_m=min_time_m), parse_mode='HTML')

    else:
        bot.send_message(message.chat.id, 'Please, check your input', parse_mode='HTML')


@bot.message_handler(commands=['cheap'])
def get_cheapest(message):
    text = message.text.replace('/cheap ', '')
    if all_routes(text):
        trips = all_routes(text)

        # find cheapest ones
        min_plazcard = 0
        min_plazcard_id = None
        min_coupe = 0
        min_coupe_id = None
        min_lux = 0
        min_lux_id = None
        min_sedentary = 0
        min_sedentary_id = None
        min_soft = 0
        min_soft_id = None

        for train in trips:
            for train_type in train['categories']:
                if train_type['type'] == 'plazcard' and ((train_type['price'] < min_plazcard) or min_plazcard == 0):
                    min_plazcard = train_type['price']
                    min_plazcard_id = train['trainNumber']
                if train_type['type'] == 'coupe' and ((train_type['price'] < min_coupe) or min_coupe == 0):
                    min_coupe = train_type['price']
                    min_coupe_id = train['trainNumber']
                if train_type['type'] == 'lux' and ((train_type['price'] < min_lux) or min_lux == 0):
                    min_lux = train_type['price']
                    min_lux_id = train['trainNumber']
                if train_type['type'] == 'sedentary' and ((train_type['price'] < min_sedentary) or min_sedentary == 0):
                    min_sedentary = train_type['price']
                    min_sedentary_id = train['trainNumber']
                if train_type['type'] == 'soft' and ((train_type['price'] < min_soft) or min_soft == 0):
                    min_soft = train_type['price']
                    min_soft_id = train['trainNumber']

        url = 'https://poezd.ru/raspisanie/{trainNumber}/'
        response = 'Cheapest trains:\n'

        if min_plazcard_id:
            schedule = url.format(trainNumber=min_plazcard_id)
            response += 'Plazcard --> {min_plazcard}₽\n{schedule}\n'.\
                format(min_plazcard=min_plazcard, schedule=schedule)
        if min_coupe_id:
            schedule = url.format(trainNumber=min_coupe_id)
            response += 'Coupe --> {min_coupe}₽\n{schedule}\n'.\
                format(min_coupe=min_coupe, schedule=schedule)
        if min_lux_id:
            schedule = url.format(trainNumber=min_lux_id)
            response += 'Lux --> {min_lux}₽\n{schedule}\n'.\
                format(min_lux=min_lux, schedule=schedule)
        if min_sedentary_id:
            schedule = url.format(trainNumber=min_sedentary_id)
            response += 'Sedentary --> {min_sedentary}₽\n{schedule}\n'.\
                format(min_sedentary=min_sedentary, schedule=schedule)
        if min_soft_id:
            schedule = url.format(trainNumber=min_soft_id)
            response += 'Soft --> {min_soft}₽\n{schedule}'.\
                format(min_soft=min_soft, schedule=schedule)

        bot.send_message(message.chat.id, response, parse_mode='HTML')

    else:
        bot.send_message(message.chat.id, 'Please, check your input', parse_mode='HTML')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def find_on_date(message):
    if num_words(message.text) == 3:
        points = message.text.split()[0] + ' ' + message.text.split()[1]
        date = message.text.split()[2]
        if get_id(points):
            ids = get_id(points)
            departure_id, destination_id = ids[0], ids[1]
            response = 'Here are the trains:\n'
            for departure in departure_id:
                for destination in destination_id:
                    trains = parsing.sense(departure, destination, date)

                    if trains:
                        for train in trains:
                            train_id = train['train_id']
                            response += '№{train_id}  '.format(train_id=train_id)
                            departure_time = train['departure_time']
                            arrival_time = train['arrival_time']
                            response += '{departure_time} - {arrival_time}\n'.format(departure_time=departure_time,
                                                                                    arrival_time=arrival_time)
                            departure_station = train['departure_station']
                            if departure_station:
                                response += 'From: {departure_station}'.format(departure_station=departure_station)
                            arrival_station = train['arrival_station']
                            if arrival_station:
                                response += ' --> To {arrival_station}'.format(arrival_station=arrival_station)
                            trip_duration = train['trip_duration']
                            response += ' ({trip_duration})\n'.format(trip_duration=trip_duration)
                            price_of_seats = train['price_of_seats']
                            if 'not provided' not in price_of_seats:
                                response += 'Common: {price_of_seats}  '.format(price_of_seats=price_of_seats)
                            price_of_coupe = train['price_of_coupe']
                            if 'not provided' not in price_of_coupe:
                                response += 'Coupe: {price_of_coupe}  '.format(price_of_coupe=price_of_coupe)
                            price_of_luxe = train['price_of_luxe']
                            if 'not provided' not in price_of_luxe:
                                response += 'Luxe: {price_of_luxe}'.format(price_of_luxe=price_of_luxe)
                            buy_ticket = train['buy_ticket']
                            if buy_ticket:
                                response += '\nBuy: {buy_ticket}\n\n'.format(buy_ticket=buy_ticket)

                    else:
                        bot.send_message(message.chat.id, 'No trains available', parse_mode='HTML')

            bot.send_message(message.chat.id, response, parse_mode='HTML')

        else:
            bot.send_message(message.chat.id, 'Please, check your input', parse_mode='HTML')

    else:
        bot.send_message(message.chat.id, "Please use form: 'From To Date'\nOR use /commands for commands list",
                         parse_mode='HTML')


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)

        except Exception as e:
            print(e)
            time.sleep(15)
