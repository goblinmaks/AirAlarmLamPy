import machine
import time
import network
import binascii
import logging
import uasyncio as asyncio
import ujson as json
import ure as re
import usocket as socket

log = logging.getLogger('airAlarmLamp')
log.level = min(logging.INFO, logging._level)


#SSID = "Flower.SHome"
PASSWORD = "FB:JwJN[J0tY"
SSID = "Flower"
PASSWORD = "eZH{3f?P)y8Y"


# Timeout for WiFi connection in seconds
WIFI_CONNECT_TIMEOUT = 60

# Define the GPIO pin connected to the button and LED
BUTTON_PIN = 4
LED_PIN = 16

# Create a WLAN (WiFi) object
wlan = network.WLAN(network.STA_IF)

button = machine.Pin(BUTTON_PIN, machine.Pin.IN)
chip_id = binascii.hexlify(machine.unique_id()).decode()

# Create an event
button_event = asyncio.Event()
alarm_event = asyncio.Event()


def button_callback(pin):
    print("Button callback!")
    # Set the event when the button is pressed
    button_event.set()

# Set up the button as an input with a callback on the falling edge
button.irq(trigger=machine.Pin.IRQ_RISING, handler=button_callback)

# Function to connect to WiFi
def initial_wifi_connect(_ssid, _password):
    try:
        log.info("Init wifi connection")
        wlan.active(False)
        wlan.active(True)
        wlan.config(txpower=20)
        log.debug(wlan.scan())
        wlan.connect(_ssid, _password)
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > WIFI_CONNECT_TIMEOUT:
                wlan.active(False)
                return False
            time.sleep(1)
            log.debug("Connecting to Wi-Fi...")
        log.info("IP Address: {}".format(wlan.ifconfig()[0]))
        return True
    except Exception as e:
        wlan.active(False)
        log.warning('Error connecting to WiFi:', str(e))


def start_ap_mode():
    log.info('Started in AP mode')
    ap_id = 'AirAlarmLamp_{}'.format(chip_id)
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ap_id, dhcp_hostname= ap_id)
    log.info("Connect to '{}', IP Address: {}".format(ap_id, ap.ifconfig()[0]))

async def handle_request(reader, writer):
    # Log client request
    request_line = await reader.readline()
    log.debug("Client requested: {}".format(request_line.decode().strip()))

    # HTML content
    html_content = """<!DOCTYPE html>
<html>
<head><title>MicroPython Web Server</title></head>
<body>
<h1>Hello, MicroPython!</h1>
<p>This is a test page.</p>
</body>
</html>
"""
    # HTTP response
    response = "HTTP/1.1 200 OK\r\n"
    response += "Content-Type: text/html\r\n"
    response += "Content-Length: {}\r\n\r\n".format(len(html_content))
    response += html_content

    # Send response to the client
    await writer.awrite(response.encode("utf-8"))
    await writer.aclose()

async def web_server():
    log.debug("web_server start")
    server = await asyncio.start_server(handle_request, "0.0.0.0", 80)
    log.info("Server started at 0.0.0.0:80")

async def button_handler():
    log.debug("button_handler start")
    while True:
        # Wait for the button event to be set
        await button_event.wait()
        log.info("Button pressed!")
        # Clear the event for the next button press
        button_event.clear()


async def request_handler():
    log.debug("time_handler start")
    while True:
        log.debug("processing ....")
        await asyncio.sleep_ms(10000)


async def lamp_service():
    log.debug("lamp service started")
    # Start the button handler task
    asyncio.create_task(button_handler())
    asyncio.create_task(request_handler())
    while True:
        await asyncio.sleep_ms(100) 


def main():
    log.info("ESP8266 Chip ID: {}".format(chip_id))  
    loop = asyncio.get_event_loop()
    #loop.create_task(button_handler())
    
    asyncio.run(web_server())    

    if initial_wifi_connect(SSID, PASSWORD):
        # Run the event loop
        asyncio.run(lamp_service())
    else:
        start_ap_mode()
    
    #asyncio.run(lamp_service())
    loop.run_forever()   

if __name__ == "__main__":
    main()


