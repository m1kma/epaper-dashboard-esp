# E-paper (e-ink) dashboard project for the ESP8266
The backend service (separate AWS Lambda) is used to collect data from the various datasources such as weather service and news RSS feeds. The data is formatted to the JSON by the backend. The ESP8266 calls the backend service, parses the JSON string and displays the data in the e-paper display.

## Components
- E-paper display model: Waveshare 5.83 inch 600x448 B&W
- ESP8266 model: NodeMCU (Amica)

## Libraries
- GxEPD2_BW
- ESP8266WiFi
- WiFiClientSecure
- ArduinoJson

## Credits
Copyright (c) 2020 Mika Mäkelä
