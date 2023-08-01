import time
import Adafruit_DHT
import requests

GPIO_PIN = 4
ENDPOINT = "things.ubidots.com"
DEVICE_LABEL = "weather-station"
VARIABLE_LABEL1 = "temperature"
VARIABLE_LABEL2 = "humidity"
TOKEN = "BBFF-gmkkTyqNgfU7RzCfghfCxKk0EcgMli" # replace with your TOKEN
DELAY = 60  # Delay in seconds 
def post_var(payload, url=ENDPOINT, device=DEVICE_LABEL, token=TOKEN):
    try:
        url = "http://{}/api/v1.6/devices/{}".format(url, device)
        headers = {"X-Auth-Token": token, "Content-Type": "application/json"}

        attempts = 0
        status_code = 400

        while status_code >= 400 and attempts < 5:
            print("[INFO] Sending data, attempt number: {}".format(attempts))
            req = requests.post(url=url, headers=headers,
                                json=payload)
            status_code = req.status_code
            attempts += 1
            time.sleep(1)

        print("[INFO] Results:")
        print(req.text)
    except Exception as e:
        print("[ERROR] Error posting, details: {}".format(e))

def main():
    # Simulates sensor values
    h, t = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, GPIO_PIN)
    if h is not None and t is not None:
            print('溫度={0:0.1f}度C 濕度={1:0.1f}%'.format(t, h))
    # Builds Payload and topíc
    payload = {VARIABLE_LABEL1: t,VARIABLE_LABEL2: h}
    # Sends data
    post_var(payload)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(DELAY)