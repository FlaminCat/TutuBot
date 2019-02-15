import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver


def scrapper(parser):
	train_list = []
	try:
		for i in parser:
			train_info = i.get('data-ti-train-card').split('|')
			voc = {'train_id': train_info[1]}
			voc['departure_time'] = train_info[5]
			voc['arrival_time'] = train_info[4]
			voc['trip_duration'] = ''.join(re.split(r'\xa0', i.find('span', {'data-ti': 'travel_time'}).text))
			voc['departure_station'] = i.find('span', {'class': 'partial__block__2LwTY t-gray'}).text
			voc['arrival_station'] = i.find('span', {'class': 'arrivalInfoWithDateOffset__block__2SXMU t-gray'}).text
			voc['train_rating'] = re.split(r'О', i.find('div', {'class': r'withoutSeats__wrapper__3WkSL'}).text)[0]
			try:
				voc['price_seat'] = ''.join(re.split(r'\xa0', i.findAll('span', {'class': 't-ttl_third'})[0].text))
			except:
				voc['price_plaz'] = 'No seat tickets'
			try:
				voc['price_coupe'] = ''.join(re.split(r'\xa0', i.findAll('span', {'class': 't-ttl_third'})[1].text))
			except:
				voc['price_coupe'] = 'No coupe tickets'	
			try:
				voc['price_luxury'] = ''.join(re.split(r'\xa0', i.findAll('span', {'class': 't-ttl_third'})[2].text))
			except:
				voc['price_luxury'] = 'No luxury tickets'
			try:
				sample = re.split(r':', i.find('span', {'class': 'bottomLinks__closestDays__3qzph'}).text)[1]
				voc['closest_days'] = sample[:-1]
			except:
				voc['closest_days'] = 'No trains in closest days'

			train_list.append(voc)
	except:
		'Could not find any trains.'

	return train_list


def scrapper_with_date(parser):
	train_list = []
	try:
		for i in parser:
			train_info = i.get('data-ti-train-card').split('|')
			voc = {'train_id': train_info[1]}
			voc['departure_time'] = train_info[5]
			voc['arrival_time'] = train_info[4]
			voc['trip_duration'] = ''.join(re.split(r'\xa0', i.find('span', {'class': 't-txt-s route_time', 'data-ti': 'route_time'}).text))
			voc['departure_station'] = i.find('div', {'class': 't-gray'}).find('span', {'class': 't-txt-s'}).text
			voc['arrival_station'] = i.findAll('div', {'class': 't-gray'})[1].text
			voc['train_rating'] = i.find('div', {'data-ti': 'user_rating_value'}).text
			try:
				voc['number_of_seats'] = i.findAll('div', {'class': 'topBottomPrices__topBottomContainer__2hUBN undefined'})[0].find('span', \
					{'class': 'pseudo__link__1r2b- topBottomPrices__seatsCountWithPopup__1lBEb'}).text
				voc['price_of_seats'] = adding_space(''.join(re.split(r'\xa0', i.findAll('div', {'class': 'topBottomPrices__topBottomContainer__2hUBN undefined'})[0] \
					.find('span', {'class': 'seats_price t-txt-s'}).text)))
			except:
				voc['number_of_seats'] = 'Seats are not provided'
				voc['price_of_seats'] = 'Seats are not provided'
			try:
				voc['number_of_coupe'] = i.findAll('div', {'class': 'topBottomPrices__topBottomContainer__2hUBN undefined'})[1].find('span', \
					{'class': 'pseudo__link__1r2b- topBottomPrices__seatsCountWithPopup__1lBEb'}).text
				voc['price_of_coupe'] = adding_space(''.join(re.split(r'\xa0', i.findAll('div', {'class': 'topBottomPrices__topBottomContainer__2hUBN undefined'})[1] \
					.find('span', {'class': 'seats_price t-txt-s'}).text)))
			except:
				voc['number_of_coupe'] = 'Coupe is not provided'
				voc['price_of_coupe'] = 'Coupe is not provided'
			try:
				voc['number_of_luxe'] = i.findAll('div', {'class': 'topBottomPrices__topBottomContainer__2hUBN undefined'})[2].find('span', \
					{'class': 'pseudo__link__1r2b- topBottomPrices__seatsCountWithPopup__1lBEb'}).text
				voc['price_of_luxe'] = adding_space(''.join(re.split(r'\xa0', i.findAll('div', {'class': 'topBottomPrices__topBottomContainer__2hUBN undefined'})[2] \
					.find('span', {'class': 'seats_price t-txt-s'}).text)))
			except:
				voc['number_of_luxe'] = 'Luxe is not provided'
				voc['price_of_luxe'] = 'Luxe is not provided'
			voc['buy_ticket'] = 'https://www.tutu.ru' + str(i.find('a', {'class': 'g-link'}).get('href'))

			train_list.append(voc)
	except:
		'Could not find any trains.'

	return train_list


def sense(departure, arrival, date=None):
	if date is not None:
		driver = webdriver.Chrome("/Users/andrey/Downloads/chromedriver")
		driver.get(f'https://www.tutu.ru/poezda/rasp_d.php?nnst1={departure}&nnst2={arrival}&date={date}')
		response = driver.page_source
		soup = BeautifulSoup(response, "html.parser")

		try:
			case = scrapper_with_date(soup.findAll('div', {'class': 'b-train__schedule__train_card'}))
		except:
			pass

		return case 
	else:
		response = requests.get(f'https://www.tutu.ru/poezda/rasp_d.php?nnst1={departure}&nnst2={arrival}')
		soup = BeautifulSoup(response.text, "html.parser")
		
		try:
			option1 = scrapper(soup.findAll('tr', {'class': 'table__tr__WH2PE b-train__schedule__train_card s-hovered'}))
		except:
			pass
		
		try:
			option2 = scrapper(soup.findAll('tr', {'class': 'table__tr__WH2PE b-train__schedule__train_card'}))
		except:
			pass
		
		result2 = option1 + option2
		return result2


def adding_space(obj):
	part1 = obj[0:2]
	part2 = obj[2:-1]
	spaced = str(part1) + ' ' + str(part2) + ' Р'
	return spaced

