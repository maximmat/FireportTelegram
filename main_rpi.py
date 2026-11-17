import os
from dotenv import load_dotenv
import requests
from telethon import TelegramClient, events
from time import sleep
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
import re
import sys
import traceback
import asyncio
import functools

load_dotenv()

setup = 0

#data z api
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
sesion_name = os.getenv("SESSION_NAME", "Fireport")
#----

if not api_id or not api_hash:
	raise ValueError("Chyba: TELEGRAM_API_ID nebo TELEGRAM_API_HASH chybí v .env souboru!")

chat = "FIREPORTcz_bot" #jméno fireportu na telegramu
#chat = "Zdenda_bot"



client = TelegramClient(
	sesion_name, 
	api_id, 
	api_hash,
	device_model="Desktop",      # Podvržení modelu
	system_version="Windows 11", # Podvržení OS
	app_version="4.8.1",         # Verze oficiálního Telegram klienta
	lang_code="en"
)

@client.on(events.NewMessage(chats=chat, incoming=True)) #na co má klient reagovat
async def newmess(event): #kdž přijde nová zpráva, async ve zkratce říká, že se funkce provádějí nezávisle na sobě, pokud by bylo více funkcí nečeká se než se dokončí jedna, ale zároveň se vykonává druhá (https://realpython.com/python-async-features/)
		try:
			raw_text = event.raw_text
			mess = [line.strip() for line in raw_text.splitlines() if line.strip()]
	
			kategorie = ""
			lokace = ""
			dopres_lokace = "" # 🏠
			dopres_info = ""   # ℹ️
			tech = ""          # 🚒
			gps_lat = ""
			gps_lon = ""
	
			def clean(text):
				# Rozdělí podle první mezery (většina emoji je oddělena mezerou)
				parts = text.split(' ', 1)
				return parts[1].strip() if len(parts) > 1 else text.strip()
	
	
			for line in mess:
				if line.startswith("🔥"):
					kategorie = clean(line)
			
				elif line.startswith("🏙️") or line.startswith("🏙"): # Někdy se liší varianta emoji
					lokace = clean(line)
				
				elif line.startswith("🏠"):
					dopres_lokace = clean(line)
				
				elif line.startswith("ℹ️") or line.startswith("ℹ"):
					dopres_info = clean(line)
				
				elif line.startswith("🚒"):
					tech = clean(line)
				
				elif "http" in line: # Odkaz poznáme podle 'http', emoji se může lišit (🌍/🗺️)
					# Zkusíme najít GPS v odkazu
					match = re.search(r'q=([0-9\.]+),([0-9\.]+)', line)
					if match:
						gps_lat = match.group(1)
						gps_lon = match.group(2)
						print(f"DEBUG: Nalezeny GPS: {gps_lat}, {gps_lon}")
	
			popis_parts = []
			if dopres_lokace: popis_parts.append(dopres_lokace)
			if dopres_info:   popis_parts.append(dopres_info)
		
			# Spojíme je svislítkem nebo čárkou
			dopres_full = " | ".join(popis_parts)
	
			data = {
				"fireport": "poplach",
				"kategorie": kategorie,
				"lokace": lokace,
				"dopres": dopres_full,
				"tech": tech,
				"gps_lat": gps_lat,
				"gps_lon": gps_lon
			}
		
			print(f"Odesílám data: {data}")
	
			requests.post("http://127.0.0.1:5000/novy-vyjezd", json=data)

			requests.post("http://127.0.0.1:1880/poplach", json=data)
	
			requests.get("http://192.168.0.69:6879")
	
			sleep(2)

		except Exception as e:
			chyba_deatil = traceback.format_exc()
			var_chyba = f"Chyba při zpracování zprávy:\n{chyba_deatil}"
			print("=== CHYBA ZPRACOVÁNÍ ===")
			print(var_chyba)



def auth_failed():
	raise ValueError("Telethon vyžaduje autentizaci.")

async def watchdog_ping():
	loop = asyncio.get_event_loop()
	while True:
		try:
			func = functools.partial(requests.post, "http://127.0.0.1:5000/ping", timeout=2)
			await loop.run_in_executor(None, func)
		except Exception as e:
			pass

		await asyncio.sleep(60)


if __name__ == "__main__":
	if setup == 1:
		print("=== REŽIM SETUP: Generování session ===")
		client.start()

		print("\nÚspěšně přihlášeo!")
		print("Nyní změň 'setup = 0'")

		client.disconnect()
		sys.exit(0)

	elif setup == 0:
		print("=== REŽIM PRODUKCE ===")

		try:
			requests.post(
					"http://127.0.0.1:5000/set-status",
					json={"offline": False},
					timeout=5
					)
			client.start(phone=auth_failed)

			client.loop.create_task(watchdog_ping())

			client.run_until_disconnected()

		except Exception as e:
			chyba_deatil = traceback.format_exc()
			var_chyba = f"Kritická chyba Telegram klienta:\n{chyba_deatil}"
		
			print("=== KRITICKÁ CHYBA KLIENTA ===")
			print(var_chyba)
		
		
			try:
				print("Status changed")
				req = requests.post(
					"http://127.0.0.1:5000/set-status",
					json={"offline": True},
					timeout=5
					)
				print(req)
		
			except Exception as e:
				print(f"Nelze kontaktovat dashboard: {e}")
		
		
			sys.exit(1)
