
#your sgo-e auth data (Necessary exactly student account)
payload = {
    "login": "login",
    "password": "password",
}


#your_tg_bot token here
token = 'Bot-Token'


#just header filler
headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en,ru;q=0.9,ru-RU;q=0.8,en-US;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://sgo.e-mordovia.ru',
    'Referer': 'https://sgo.e-mordovia.ru/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


#Coordinates for final_image
box = {
    '1': (65, 90),
    '1-as': (500, 90),
    '2': (65, 226),
    '2-as': (500, 226),
    '3': (65, 362),
    '3-as': (500, 362),
    '4': (65, 498),
    '4-as': (500, 498),
    '5': (65, 634),
    '5-as': (500, 634),
    '6': (65, 780),
    '6-as': (500, 780),
    '7': (65, 916),
    '7-as': (500, 916),
}