import requests
from telethon import TelegramClient, events

url = "http://127.0.0.1:1880/poplach" #loopback na endpoint v nodered

#data z api
api_id = "api_id"
api_hash = "api_hash"
sesion_name = "sesion_name"
#----

chat = "FIREPORTcz_bot" #jméno fireportu na telegramu
#chat = "Zdenda_bot" #for testing ;-)

client = TelegramClient(sesion_name, api_id, api_hash) #definice klienta z knihovny telethon viz. 2 řádek

@client.on(events.NewMessage(chats=chat, incoming=True)) #na co má klient reagovat
async def newmess(event): #kdž přijde nová zpráva, async ve zkratce říká, že se funkce provádějí nezávisle na sobě, pokud by bylo více funkcí nečeká se než se dokončí jedna, ale zároveň se vykonává druhá (https://realpython.com/python-async-features/)
	mess = event.raw_text.splitlines() #vyčtení zprávy a rozdělení řádků do seznamu

	kategorie = mess[0] #ze sezanmu jeddnotlivé informace
	lokace = mess[1]
	dopres = mess[2]
	tech = mess[3]

	kategorie = kategorie[2:] #odebrání emoji ze zprávy
	lokace = lokace[3:] #emoji pro lokaci a dopřeasnění zabírají dva charaktery
	dopres = dopres[3:]
	tech = tech[2:]

	data = {"fireport": "poplach", "kategorie": kategorie, "lokace": lokace, "dopres": dopres, "tech": tech} # data pro nodered
	response = requests.post(url, json=data) #posílání přes post na nodered

	print(response) #výpis odpovedi od noderedu, není potřeba je pro ujištění se, že data došli
	#v nodered je potřeba navázat http response s kódem 200, aby python skript veděl, že nodered data přijal

client.start() #start telegram klienta
client.run_until_disconnected() #nekonečná smyčka pro telegram klienta