from machine import Pin, SPI
import sdcard
import uos
import gc
#import io
import time
import json

import inky_helper as ih
from inky_frame import BLACK, BLUE, GREEN, RED, WHITE

from urllib import urequest
from pngdec import PNG

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

# USB Power
usb_present_pin = Pin("WL_GPIO2", machine.Pin.IN)
USB_POWER = True if usb_present_pin.value() == 1 else False

# Setup for the display.
graphics = PicoGraphics(DISPLAY)
png = PNG(graphics)
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
    from location import SERVER, LOCATION_ID, BEARER
except ImportError:
    print("Create location.py with your location")

# Get some memory back, we really need it!
gc.collect()

URL = f"{SERVER}/{LOCATION_ID}?report=1"

# Interval in minutes, 90 is a good shout, the weather forecast doesn't really update that often anwyay
UPDATE_INTERVAL = 90

MARGIN = 20
KEY_WIDTH = 85
COLUMN_WIDTH = 68
COLUMN_GAP = 35
ROW_START=160
ROW_START_HOURLY=190
ROW_HEIGHT=20
ROW_GAP=10

feed = None
mode = "summary"
summaryOffset = 0
hourlyOffset = 0

def get_x_offset(column):
    return MARGIN + KEY_WIDTH + (column * COLUMN_GAP if column > 0 else 0) + (column * COLUMN_WIDTH)

column_offsets = [
    get_x_offset(0),
    get_x_offset(1),
    get_x_offset(2),
    get_x_offset(3),
    get_x_offset(4),
    get_x_offset(5),
    get_x_offset(6)
]

weekday = [
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat',
    'Sun'
]

weather_mapping = {
    "drizzle": {"/sd/images/64x/thick_cloud_unbroken.png", "/sd/images/64x/drizzle.png"},
    "heavy rain": {"/sd/images/64x/thick_cloud.png", "/sd/images/64x/heavy_rain.png"},
    "heavy rain showers": {"/sd/images/64x/thick_cloud.png", "/sd/images/64x/heavy_rain.png", "/sd/images/64x/partial_sun.png"},
    "light cloud": {"/sd/images/64x/light_cloud.png"},
    "light rain": {"/sd/images/64x/thick_cloud.png", "/sd/images/64x/light_rain.png"},
    "light rain showers": {"/sd/images/64x/thick_cloud.png", "/sd/images/64x/light_rain.png", "/sd/images/64x/partial_sun.png"},
    "partly cloudy": {"/sd/images/64x/light_cloud.png", "/sd/images/64x/partial_sun.png"},
    "sunny": {"/sd/images/64x/full_sun.png"},
    "sunny intervals": {"/sd/images/64x/light_cloud.png", "/sd/images/64x/partial_sun.png"},
    "thick cloud": {"/sd/images/64x/thick_cloud_unbroken.png"},
    "thundery showers": {"/sd/images/64x/thick_cloud.png", "/sd/images/64x/lightning.png", "/sd/images/64x/partial_sun.png"},
    "clear sky night": {"/sd/images/64x/clear_sky_night.png"},
    "light cloud night": {"/sd/images/64x/light_cloud.png"},
    "light rain showers night": {"/sd/images/64x/thick_cloud.png", "/sd/images/64x/light_rain.png", "/sd/images/64x/partial_moon.png"},
    "partly cloudy night": {"/sd/images/64x/light_cloud.png", "/sd/images/64x/partial_moon.png"},
    "thick cloud night": {"/sd/images/64x/thick_cloud_unbroken.png", "/sd/images/64x/partial_moon.png"},
    "thundery showers night": {"/sd/images/64x/thick_cloud.png", "/sd/images/64x/lightning.png", "/sd/images/64x/partial_moon.png"}
}

reportLabels = [
    "Min",
    "Max",
    "Rain",
    "Wind",
    " Dir",
    "UV",
    "Pollut.",
    "Pollen",
    "Sunrise",
    "Sunset"
]

hourlyLabels = [
    "Temp",
    "Rain",
    "Humid.",
    "Press.",
    "Wind",
    " Dir",
    "Visib.",
]

reportFields = [
    ["minTempC", "mostLikelyLowTemperatureC"],
    ["maxTempC", "mostLikelyHighTemperatureC"],
    "precipitationProbabilityInPercent",
    ["windSpeedMph", "gustSpeedMph"],
    "windDirection",
    "uvIndexText",
    "pollutionIndexText",
    "pollenIndexText",
    "sunrise",
    "sunset"
]

hourlyFields = [
    ["temperatureC", "feelsLikeTemperatureC"],
    "precipitationProbabilityInPercent",
    "humidity",
    "pressure",
    ["windSpeedMph", "gustSpeedMph"],
    "windDirection",
    "visibility",
]

unitFields = {
    "minTempC": "°C",
    "maxTempC": "°C",
    "humidity": "%",
    "precipitationProbabilityInPercent": "%",
    "gustSpeedMph": "mph",
    "pollutionIndexText": "",
    "pollenIndexText": "",
    "pressure": "mb",
    "sunrise": "",
    "sunset": "",
    "temperatureC": "°C",
    "uvIndexText": "",
    "visibility": "",
    "windDirection": "",
    "windSpeedMph": "mph",
}

def get_json():
    try:
        socket = urequest.urlopen(URL, headers={"Authorization": f"Bearer {BEARER}"})
        data = bytearray(1024)
        with open('/sd/forecast.json', mode="w") as f:
            while True:
                bytes_read = socket.readinto(data)
                if bytes_read == 0:
                    break
                f.write(data[:bytes_read])
        del data
        socket.close()
        gc.collect()
        forecast = open('/sd/forecast.json', mode="r")
        output = json.load(forecast)
        forecast.close()
        gc.collect()
        return output

    except OSError as e:
        print(e)
        return False

def update():
    global feed
    feed = None
    feed = get_json()

def isHourlyNight(timeslot, date):
    idx = feed["summary"]["localDate"].index(date)
    sunset = feed["summary"]["sunset"][idx]
    sunrise = feed["summary"]["sunrise"][idx]
    if (timeslot > sunset or timeslot < sunrise):
        return True
    return False

def draw_weather_icon(weather_codes, nighttime):
    for idx, entry in enumerate(weather_codes):
        for image in weather_mapping[f"{entry.lower()}{' night' if nighttime and idx == 0 else ''}"]:
            png.open_file(image)
            png.decode(column_offsets[idx], 80)

def draw_weather(weather, x, y, nighttime=False):
    for entry in weather_mapping[f"{weather.lower()}{' night' if nighttime else ''}"]:
        png.open_file(entry)
        png.decode(x, y)

def draw_weather_icon_hourly(weather_codes, timeslots, date):
    for idx, weather_code in enumerate(weather_codes):
        isNight = isHourlyNight(timeslots[idx], date)
        draw_weather(weather_code, column_offsets[idx], 120, isNight)

def draw_summary_key(labels):
    row_start = (ROW_START if mode == "summary" else ROW_START_HOURLY)
    for idx, fieldName in enumerate(labels):
        graphics.text(fieldName, 20, row_start + (0 if idx == 0 else idx * ROW_HEIGHT + (idx  * ROW_GAP)), scale=2)

def format_unit(field):
    return unitFields[field]

def draw_summary(report, offset):
    row_start = (ROW_START if mode == "summary" else ROW_START_HOURLY)
    for row_idx, field in enumerate(reportFields if mode == "summary" else hourlyFields):
        if type(field) == list:
            value = ""
            for col_idx, x_offset in enumerate(column_offsets):
                value = "/".join([str(report[e][col_idx + offset] or 0) for e in field])
                graphics.text(
                    f"{value}{format_unit(field[0])}",
                    x_offset,
                    row_start + (row_idx * 30 if row_idx > 0 else 0),
                    scale=2
                )
        else:
            for col_idx, entry in enumerate(report[field][offset:len(column_offsets) + offset]):
                value = str(entry or 0)
                graphics.text(
                    f"{value}{format_unit(field)}",
                    column_offsets[col_idx % 7],
                    row_start + (row_idx * 30 if row_idx > 0 else 0),
                    scale=2
                )

def draw():
    global summaryOffset
    global hourlyOffset
    
    graphics.set_font("bitmap8")

    # Clear the screen
    graphics.set_pen(WHITE)
    graphics.clear()
    graphics.set_pen(BLACK)

    # Draws 2 articles from the feed if they're available.
    if ((mode is None or mode == 'summary') and feed is not False and len(feed["summary"]["localDate"])) > 0:
        summary = feed["summary"]
        current_time = time.localtime(time.time())
        # 600x448
        # Title
        graphics.set_pen(graphics.create_pen(0, 200, 0))
        graphics.rectangle(0, 0, WIDTH, 40)
        graphics.set_pen(WHITE)
        graphics.text(f"BBC {len(summary["localDate"])} day forecast for {feed["name"]}", 10, 10, WIDTH, 3)

        graphics.set_pen(BLACK)

        for idx, date in enumerate(summary["localDate"][summaryOffset:len(column_offsets) + summaryOffset]):
            label = f"{date[-2:]}-{date[5:7]}"
            if summaryOffset == 0:
                if idx == 0:
                    label = "Tonight" if feed["isNight"] else "Today"
                else:
                    label = weekday[(current_time[6] + idx) % 7]
            graphics.text(label, column_offsets[idx], 50, scale=3)

        draw_weather_icon(
            summary["weatherTypeText"][summaryOffset:len(column_offsets) + summaryOffset],
            True if feed["isNight"] and summaryOffset == 0 else False
        )

        graphics.set_pen(BLACK)

        draw_summary_key(reportLabels)
        draw_summary(summary, summaryOffset)
#        print("Pub Date")
#        graphics.text(f"Last Updated: {dayOne['pubDate']}", 10, 470, WIDTH, 1)
    elif ((mode == "hourly") and feed is not False and len(feed["hourly"]["timeslot"])) > 0:
        if (hourlyOffset + 7) > len(feed["hourly"]["timeslot"]):
            print(f"Overflow {hourlyOffset} in {feed["hourly"]["timeslot"]}")
            hourlyOffset -= 7
            return

        hourly = feed['hourly']

        end = hourlyOffset + len(column_offsets)
        
        dates = hourly["localDate"][hourlyOffset:end]

        graphics.set_pen(graphics.create_pen(0, 200, 0))
        graphics.rectangle(0, 0, WIDTH, 40)
        graphics.set_pen(WHITE)
        graphics.text(f"BBC hourly forecast on {dates[0]} for {feed["name"]}", 10, 10, WIDTH, 3)
        
        graphics.set_pen(BLACK)
        
        for idx, date in enumerate(dates):
            label = f"{date[-2:]}-{date[5:7]}"
            graphics.text(label, column_offsets[idx], 50, scale=3)

        for idx, timeslot  in enumerate(hourly["timeslot"][hourlyOffset:end]):
            graphics.text(timeslot, column_offsets[idx], 80, scale=3)

        draw_weather_icon_hourly(hourly["weatherTypeText"][hourlyOffset:end], hourly["timeslot"][hourlyOffset:end], date)
        graphics.set_pen(BLACK)

        draw_summary_key(hourlyLabels)
        draw_summary(hourly, hourlyOffset)
    else:
        graphics.set_pen(RED)
        graphics.rectangle(0, (HEIGHT // 2) - 20, WIDTH, 40)
        graphics.set_pen(BLACK)
        graphics.text("Unable to display weather!",
                      5, (HEIGHT // 2) - 15, WIDTH, 2)
        graphics.text("Check your network settings in wifi.py / location.py and sd card log file",
                      5, (HEIGHT // 2) + 2, WIDTH, 2)

    graphics.update()

last_json_update = None
idle_time = None

while True:
    drawScreen = False
    if last_json_update is None or ((time.time() - last_json_update) > (UPDATE_INTERVAL * 60)):
        ih.write_log("Update weather data")
        last_json_update = time.time()
        update()
        drawScreen = True
        time.sleep(0.5)

    if (USB_POWER is False and idle_time is not None and time.time() - idle_time) > 10:
        ih.write_log("Idle time reached")
        idle_time = None
        ih.sleep(UPDATE_INTERVAL)
    elif ih.inky_frame.button_a.read() and (summaryOffset != 0 or mode == "hourly"):
        mode = "summary"
        summaryOffset = 0
        hourlyOffset = 0
        idle_time = None
        drawScreen = True
    elif ih.inky_frame.button_e.read():
        summaryOffset = 0 + len(column_offsets)
        idle_time = None
        drawScreen = True
    elif USB_POWER is False and ih.inky_frame.button_c.read():
        idle_time = None
        ih.sleep(UPDATE_INTERVAL)
    elif ih.inky_frame.button_b.read() and mode == "hourly" and hourlyOffset >= 7:
        hourlyOffset -= 7
        idle_time = None
        drawScreen = True
    elif ih.inky_frame.button_d.read():
        if (mode == 'summary'):
            mode = "hourly"
            hourlyOffset = 0
        else:
            hourlyOffset += 7
        idle_time = None
        drawScreen = True
    else:
        time.sleep(0.5)
    
    if drawScreen:
        ih.write_log("Drawing screen")
        ih.led_warn.on()
        draw()
        ih.led_warn.off()

    if idle_time is None:
        ih.write_log("Setting idle time")
        idle_time = time.time()

#    print(f"Last JSON Update {last_json_update} Idle time {idle_time} UPDATE_INTERVAL {UPDATE_INTERVAL}")
#    print(f"Time elapsed since last json update {time.time() - last_json_update}")
