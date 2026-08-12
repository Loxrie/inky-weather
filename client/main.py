from machine import Pin, SPI
import sdcard
import uos
import gc
# import io
import time
import json

import inky_helper as ih
from inky_frame import BLACK, BLUE, GREEN, RED, WHITE

from urllib import urequest
from pngdec import PNG

# import qrcode

# Uncomment the line for your Inky Frame display size
#from picographics import PicoGraphics, DISPLAY_INKY_FRAME_4 as DISPLAY  # 4.0"
#from picographics import PicoGraphics, DISPLAY_INKY_FRAME as DISPLAY      # 5.7"
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"
#from picographics import DISPLAY_INKY_FRAME_SPECTRA_7 as DISPLAY  # 7.3" Spectra

from picographics import PicoGraphics

# Mount sd card
sd_spi = SPI(0, sck=Pin(18, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(16, Pin.OUT))
sd = sdcard.SDCard(sd_spi, Pin(22))
uos.mount(sd, "/sd")
gc.collect()

# A short delay to give USB chance to initialise
time.sleep(0.5)

# Setup for the display.
graphics = PicoGraphics(DISPLAY)
WIDTH, HEIGHT = graphics.get_bounds()
graphics.set_font("bitmap8")

# Turn any LEDs off that may still be on from last run.
ih.clear_button_leds()
ih.led_warn.off()

try:
    from wifi import WIFI_PASSWORD, WIFI_SSID
    ih.network_connect(WIFI_SSID, WIFI_PASSWORD)
except ImportError:
    print("Create wifi.py with your WiFi credentials")

try:
    from location import LOCATION_ID, LOCATION_NAME, BEARER
except ImportError:
    print("Create location.py with your location")

# Get some memory back, we really need it!
gc.collect()

URL = f"https://localhost:3001/weather/{LOCATION_ID}"

# Title
# Sunday: Sunny Intervals, Minimum Temperature: 15\xb0C (59\xb0F) Maximum Temperature: 31\xb0C (87\xb0F)
# "(?P<day>\w+): (?P<summary>[A-z ]+), Minimum Temperature: (?P<min>\d+).*Maximum Temperature: (?P<max>\d+)"
# summaryRegex = re.compile("([A-z ]+): ([A-z ]+)(?:, Minimum Temperature: )(\d+\xb0C) (?:\(\d+\xb0F\) Maximum Temperature: )?(\d+\xb0C)?")
# descriptionRegex = re.compile("Wind Direction: ([a-z-]+), Wind Speed: (\d+mph), Visibility: ([A-z ]+), Pressure: (\d+mb), Humidity: (\d+%), UV Risk: (\d+), Pollution: ([A-z\- ]+), (?:(Sunrise): ([0-9:]+) [A-Z]+)?(?:, )?(?:(Sunset): ([0-9:]+) [A-Z]+)?")

# Length of time between updates in minutes.
# Frequent updates will reduce battery life!
UPDATE_INTERVAL = 90

MARGIN = 20
KEY_WIDTH = 120
COLUMN_WIDTH = 68
COLUMN_GAP = 20
ROW_START=160
ROW_HEIGHT=20
ROW_GAP=10
# code = qrcode.QRCode()

weather_mapping = {
    "drizzle": {"/sd/images/64x/fragments/thick-cloud-unbroken.png", "/sd/images/64x/fragments/drizzle.png"},
    "heavy rain": {"/sd/images/64x/fragments/thick-cloud.png", "/sd/images/64x/fragments/heavy-rain.png"},
    "heavy rain showers": {"/sd/images/64x/fragments/thick-cloud.png", "/sd/images/64x/fragments/heavy-rain.png", "/sd/images/64x/fragments/partial-sun.png"},
    "light cloud": {"/sd/images/64x/fragments/light-cloud-unbroken.png"},
    "light rain": {"/sd/images/64x/fragments/thick-cloud.png", "/sd/images/64x/fragments/light-rain.png"},
    "light rain showers": {"/sd/images/64x/fragments/thick-cloud.png", "/sd/images/64x/fragments/light-rain.png", "/sd/images/64x/fragments/partial-sun.png"},
    "partly cloudy": {"/sd/images/64x/fragments/light-cloud.png", "/sd/images/64x/fragments/partial-sun.png"},
    "sunny": {"/sd/images/64x/sunny.png"},
    "sunny intervals": {"/sd/images/64x/fragments/light-cloud.png", "/sd/images/64x/fragments/partial-sun.png"},
    "thundery showers": {"/sd/images/64x/fragments/thick-cloud.png", "/sd/images/64x/fragments/lightning.png", "/sd/images/64x/fragments/partial-sun.png"},
    "clear sky night": {"/sd/images/64x/clear-sky-night.png"},
    "light rain showers night": {"/sd/images/64x/fragments/thick-cloud.png", "/sd/images/64x/fragments/light-rain.png", "/sd/images/64x/fragments/partial-moon.png"},
    "partly cloudy night": {"/sd/images/64x/fragments/light-cloud.png", "/sd/images/64x/fragments/partial-moon.png"},
    "thundery showers night": {"/sd/images/64x/fragments/thick-cloud.png", "/sd/images/64x/fragments/lightning.png", "/sd/images/64x/fragments/partial-moon.png"}
}

def measure_qr_code(size, code):
    w, h = code.get_size()
    module_size = int(size / w)
    return module_size * w, module_size


def draw_qr_code(ox, oy, size, code):
    size, module_size = measure_qr_code(size, code)
    graphics.set_pen(WHITE)
    graphics.rectangle(ox, oy, size, size)
    graphics.set_pen(BLACK)
    for x in range(size):
        for y in range(size):
            if code.get_module(x, y):
                graphics.rectangle(ox + x * module_size, oy + y * module_size, module_size, module_size)


def get_json():
    try:
        socket = urequest.urlopen(URL, headers={"Authorization": f"Bearer {BEARER}"})
        # data = bytearray(1024)
        # with open('/sd/forecast.json', mode="wb") as f:
        #     while True:
        #         if socket.readinto(data) == 0:
        #             break
        #         f.write(data)
        # socket.close()
        # print(gc.mem_free())
        gc.collect()
        # stream = io.open('/sd/forecast.json', mode="r")
        # print(gc.mem_free())
        output = json.load(socket)
        gc.collect()
        return output

    except OSError as e:
        print(e)
        return False


feed = None


def update():
    global feed
    feed = get_json()

def get_x_offset(column):
    return MARGIN + KEY_WIDTH + (column * COLUMN_GAP if column > 0 else 0) + (column * COLUMN_WIDTH)

def is_nighttime():
    now = time.localtime()
    if (now[3] > 21 or now[3] < 6):
        return True
    return False

def draw_weather_icon(png, weather_codes, x_offsets, nighttime):
    for idx, entry in enumerate(weather_codes):
        for image in weather_mapping[f"{entry.lower()}{' night' if nighttime and idx == 0 else ''}"]:
            png.open_file(image)
            png.decode(x_offsets[idx], 80)

def draw_weather(png, weather, x, y, nighttime=False):
    for entry in weather_mapping[f"{weather.lower()}{' night' if nighttime else ''}"]:
        png.open_file(entry)
        png.decode(x, y)

reportLabels = [
    "Min:",
    "Max:",
    "Rain:",
    "Wind",
    "Gust",
    "Direction",
    "UV Risk",
    "Pollution",
    "Pollen",
    "Sunrise",
    "Sunset"
]

reportFields = [
    ["minTempC", "mostLikelyLowTemperatureC"],
    ["maxTempC", "mostLikelyHighTemperatureC"],
    "precipitationProbabilityInPercent",
    "windSpeedMph",
    "gustSpeedMph",
    "windDirection",
    "uvIndexText",
    "pollutionIndexText",
    "pollenIndexText",
    "sunrise",
    "sunset"
]

unitFields = {
    "minTempC": "°C",
    "maxTempC": "°C",
    "precipitationProbabilityInPercent": "$",
    "windSpeedMph": "mph",
    "gustSpeedMph": "mph",
    "windDirection": "",
    "uvIndexText": "",
    "pollutionIndexText": "",
    "pollenIndexText": "",
    "sunrise": "",
    "sunset": ""
}

def draw_summary_key():
    for idx, fieldName in enumerate(reportLabels):
        graphics.text(fieldName, 20, ROW_START + (0 if idx == 0 else idx * ROW_HEIGHT + (idx  * ROW_GAP)), scale=2)

def format_unit(field):
    return unitFields[field]

def draw_summary(report, x_offsets, day_offset):
    for row_idx, field in enumerate(reportFields):
        if type(field) == list:
            value = ""
            for col_idx, x_offset in enumerate(x_offsets):
                value = "/".join([str(report[e][day_offset:len(x_offsets)][col_idx] or 0) for e in field])
                graphics.text(f"{value}{format_unit(field[0])}" ,  x_offset, 160 + (row_idx * 30 if row_idx > 0 else 0), scale=2)
        else:
            for col_idx, entry in enumerate(report[field][day_offset:len(x_offsets)]):
                value = str(entry or 0)
                graphics.text(f"{value}{format_unit(field)}",  x_offsets[col_idx], 160 + (row_idx * 30 if row_idx > 0 else 0), scale=2)
    

mode = None
summaryOffset = 0

def draw():
    global feed
    global mode
    global summaryOffset
    graphics.set_font("bitmap8")

    # Clear the screen
    graphics.set_pen(WHITE)
    graphics.clear()
    graphics.set_pen(BLACK)

    # Draws 2 articles from the feed if they're available.
    if ((mode is None or mode == 'summary') and len(feed["summary"]["localDate"])) > 0:
        # 600x448
        # Title
        graphics.set_pen(graphics.create_pen(0, 200, 0))
        graphics.rectangle(0, 0, WIDTH, 40)
        graphics.set_pen(WHITE)
        graphics.text(f"BBC {len(feed["summary"]["localDate"])} day forecast for {feed["name"]}", 10, 10, WIDTH, 3)

        graphics.set_pen(BLACK)

        column_offsets = [
            get_x_offset(0),
            get_x_offset(1),
            get_x_offset(2),
            get_x_offset(3),
            get_x_offset(4),
            get_x_offset(5),
            get_x_offset(6)
        ]

        for idx, time in enumerate(feed["summary"]["localDate"][summaryOffset:len(column_offsets)]):
            graphics.text(f"{time[-2:]}-{time[5:7]}", column_offsets[idx], 50, scale=3)

        png = PNG(graphics)
        draw_weather_icon(png, feed["summary"]["weatherTypeText"][summaryOffset:len(column_offsets)], column_offsets, True if feed["isNight"] and summaryOffset == 0 else False)
        graphics.set_pen(BLACK)

        draw_summary_key()
        draw_summary(feed["summary"], column_offsets, summaryOffset)

#
#        draw_summary(png, dayOne, x_offset_column_1)
#        draw_summary(png, dayTwo, x_offset_column_2)
#        draw_summary(png, dayThree, x_offset_column_3)
#
#        print("Pub Date")
#        graphics.text(f"Last Updated: {dayOne['pubDate']}", 10, 470, WIDTH, 1)
#
#        code.set_text(f"https://www.bbc.co.uk/weather/{LOCATION_ID}")
#        draw_qr_code(WIDTH - 110, 65, 100, code)

    else:
        graphics.set_pen(RED)
        graphics.rectangle(0, (HEIGHT // 2) - 20, WIDTH, 40)
        graphics.set_pen(BLACK)
        graphics.text("Unable to display weather!",
                      5, (HEIGHT // 2) - 15, WIDTH, 2)
        graphics.text("Check your network settings in wifi.py",
                      5, (HEIGHT // 2) + 2, WIDTH, 2)

    graphics.update()

while True:
    update()
    ih.led_warn.on()
    draw()
    ih.led_warn.off()
    ih.sleep(UPDATE_INTERVAL)

