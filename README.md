# E-paper (e-ink) dashboard project for the ESP8266
The e-paper dashboard displays current weather and news on the e-ink display. The ESP8266 calls periodically the backend service (AWS Lambda), parses the data and displays the data in the e-paper display. 

The backend AWS Lambda collects the data from the various datasources such as the weather service and news RSS feeds. The Lambda returns the data as a JSON string. AWS infra (API Gateway) is deployed manually.

## Electrical components
- E-paper display: Waveshare 5.83 inch 600x448 B&W
- ESP8266: NodeMCU (Amica)

## Libraries
- GxEPD2_BW
- ESP8266WiFi
- WiFiClientSecure
- ArduinoJson

## AWS Python Lambda
- epaper-dashboard-backend.py

## Credits
Copyright (c) 2020 Mika Mäkelä
