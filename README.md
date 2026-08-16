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

### Usage


| Button | Action                                                                           |
| ------ | -------------------------------------------------------------------------------- |
| A      | Returns to first page of summary data, or no action                              |
| B      | If viewing hourly data goes back a page if possible.                             |
| C      | Deep sleep if on battery power                                                   |
| D      | Move on a page in hourly data or start viewing hourly data                       |
| E      | Views second page of summary data or no action, 15th day of summary data ignored |

### To Do

At the moment it deep sleeps for 1hr 30 before refreshing data.  Deep sleep plays havoc with USB power, it should detect USB but may not.

## License

Will add a new LICENSE (prob GPLv3) shortly.

This project contains code originally written and provided by Pimoroni under the MIT license included here as required:

```
MIT License

Copyright (c) 2018 Pimoroni Ltd.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
