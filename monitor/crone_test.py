import time

import requests


def monitor_heartbeat(url, interval):
    while True:
        response = requests.get(url)
        print(f"Wysłano zapytanie POST do {url}")
        if response.status_code == 200:
            print(f"Serwer działa poprawnie. Odpowiedź otrzymana: {response.status_code}")
        else:
            print(f"Ostrzeżenie: Nieprawidłowa odpowiedź serwera! Kod odpowiedzi: {response.status_code}")

        time.sleep(interval)


url = "http://127.0.0.1:8000/crone/4"
interval = 15

print(f"Rozpoczęto monitorowanie serwera {url} co {interval} sekund.")
monitor_heartbeat(url, interval)
