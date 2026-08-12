# Weather client for inky frame 7.3" and small express client proxy

## Notes

I have not tested the instructions in this README in a clean environment they written from memory.

## Express Proxy

### Description

The weather rss feed from the Beeb only covers 3 days, the JSON data is crazy verbose and exhausts the tiny Pico's memory. Inspired by Open Meteo's data format this proxy attempts to squish the data in a similar way.

The reasoning behind this is:

| Data                      | Size (bytes) |
| ------------------------- | ------------ |
| BBC                       | 234260       |
| Optimised Daily data only | 1728         |
| Opimised Daily and hourly | 24796        |

Some data is omitted, verbose / repetitive data mostly, plus Farenheit and Kph. Feel free to swap them if you want full metric or imperial rather than my hybrid unit preferences.

### Compilation

### Building and Running

Use nvm or install the node in .nvmrc

```
npm install
```

Create a .env file containing some base64 encoded string for your token[^1] and a port

```.env
PORT=3001
BEARER=mybase64string==
```

Then run in dev

```
# Dev watch
npm run dev
```

```
# Run from dist
npm run build
npm run start
```

### Deployment

The intention is for this to run from pm2 and use a ProxyPass from Apache2.

To run with pm2 modify `environment.config.json` to contain:

```
{
  "apps": [
    {
      "name": "tiny-weather",
      "script": "./dist/index.js",
      "env": {
        "POST": "3001",
        "BEARER": "mybase64string=="
      }
    }
  ]
}
```

You can then add and launch with:

```
npm run pm2:add
```

There are also `pm2:start`, `pm2:stop`, `pm2:remove`, and `pm2:restart` commands.

This is not watched by default.

### Queries

Queries follow the format:

```
/weather/<id>
```

for a basic report including daily summaries.

Or for an extended report including all hourly data:

```
/weather/<id>?report=1
```

## Inky Frame 7.3" client

This is designed to run on the old 7 colour inky frame 7.3 now discontinued that has the Pico on board. May well run elsewhere but will need modifying. If you're not running on a Pico you problem don't need to go to these lengths as you won't have the memory restrictions.

### Building

Create and use a python venv. Source it, install `cairosvg` in it with pip.

```
cd images
python svg2png
```

Create a `wifi.py` containing your wifi creds:

```
WIFI_SSID = ""
WIFI_PASSWORD = ""
```

Create a `location.py` file containing, location id comes from BBC weather website and is the numbers at the end. `BEARER` should be the same string as before[^1]:

```
LOCATION_ID = ""
BEARER = "base64encodedstring=="
```

### Deploying

Put your SD card in your computer and copy the images dir to it, or modify the source code to exclude `/sd` from the image paths and push them to the pico.

#### With images on SD

Use thonny, upload

```
lib
inky_helper.py
location.py
main.py
wifi.py
```

#### Without images on SD

Same as above but also upload `images`

[^1]: Yes this isn't a proper Bearer token, feel free to implement JWT or some other authentication if your needs require it.

### To Do

At the moment it deep sleeps for 1hr 30 before refreshing data.

Navigation across days.

Some way of navigating and displaying the hourly data.  Screen refresh is so slow I'm not sure.

Maybe

* Button 'A' changes page.
* Render only 4 columns
* Button 'B' to 'E' display detailed data for that column.
* In the detail screen button A goes back, other buttons paginate details unless by some miracle I can fit them.