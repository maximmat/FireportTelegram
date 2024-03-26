import requests
from telethon import TelegramClient, events

url = "http://192.168.1.7:1880/poplach" #endpoint v nodered
data = {"fireport": "poplach"} #data co dorazí do noderedu

#data z api
api_id = "12345"
api_hash = "b123548a2356452f1544"
sesion_name = "Fireport"
#----

chat = "FIREPORTcz_bot" #jméno fireportu na telegramu
#chat = "Zdenda_bot" #for testing ;-)

client = TelegramClient(sesion_name, api_id, api_hash) #definice klienta z knihovny telethon viz. 2 řádek

@client.on(events.NewMessage(chats=chat)) #na co má klient reagovat
async def newmess(event): #kdž přijde nová zpráva, async ve zkratce říká, že se funkce provádějí nezávisle na sobě, pokud by bylo více funkcí nečeká se než se dokončí jedna, ale zároveň se vykonává druhá (https://realpython.com/python-async-features/)
        response = requests.post(url, json=data) #posílání přes post na nodered

        print(response) #výpis odpovedi od noderedu, není potřeba je pro ujištění se, že data došli
        #v nodered je potřeba navázat http response s kédem 200, aby python skript veděl, že nodered data přijal

client.start() #start telegram klienta
client.run_until_disconnected() #nekonečná smyčka pro telegram klienta