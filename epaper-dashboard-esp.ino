/*
 * (c) Mika Mäkelä - 2020
 * E-paper (e-ink) dashboard project for the ESP8266
 */

#define ENABLE_GxEPD2_GFX 0

#include <GxEPD2_BW.h>
#include <Fonts/FreeMonoBold9pt7b.h>
#include <Fonts/FreeSans12pt7b.h>
#include <Fonts/FreeSansBold12pt7b.h>
#include <Fonts/FreeSansBold18pt7b.h>
#include <Fonts/FreeSerifBold18pt7b.h>
#include <Fonts/FreeSansBold24pt7b.h>

#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include "arduino_secrets.h"

GxEPD2_BW<GxEPD2_583, GxEPD2_583::HEIGHT / 2> display(GxEPD2_583(/*CS=D6*/ 5, /*DC=D3*/ 0, /*RST=D4*/ 2, /*BUSY=D2*/ 4));

const char *ssid_home = SECRET_SSID_HOME;
const char *password_home = SECRET_PASS_HOME;
const char *host_dev = SECRET_AWS_HOST_DEV;
const char *api_key_dev = SECRET_AWS_KEY_DEV;
const int httpsPort = 443;

void setup()
{
  Serial.begin(115200);
  Serial.println("setup");
  delay(100);
  display.init(115200);

  // connect to Wifi
  connectWifi();

  // make request to the AWS backend service
  String aws_data = callAWS(host_dev, api_key_dev);

  // update content to the e-paper display
  drawEpaper(aws_data);

  Serial.println("setup done");

  // go to deep sleep
  ESP.deepSleep(300e6);
}

void loop()
{
}

void drawEpaper(String aws_data)
{
  Serial.println("drawEpaper");

  const size_t capacity = 2 * JSON_ARRAY_SIZE(0) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(7) + 800;

  DynamicJsonDocument doc(capacity);
  deserializeJson(doc, aws_data);

  const String tempOut = doc["tempOut"];
  const String temp6h = doc["temp6h"];
  const String temp12h = doc["temp12h"];
  const String temp24h = doc["temp24h"];
  const String rhOut = doc["rhOut"];
  const String ws10Out = doc["ws10Out"];
  const String tempIn = doc["tempIn"];
  const String rhIn = doc["rhIn"];
  const String tempTulo = doc["tempTulo"];
  const String rhTulo = doc["rhTulo"];

  const String rss0 = doc["rss"][0];
  const String rss1 = doc["rss"][1];
  const String rss2 = doc["rss"][2];
  const String rss3 = doc["rss"][3];
  const String rss4 = doc["rss"][4];

  display.setRotation(1);
  display.setFont(&FreeSansBold24pt7b);
  display.setTextColor(GxEPD_BLACK);

  display.setFullWindow();
  display.firstPage();
  
  do
  {
    display.fillScreen(GxEPD_WHITE);

    // Print outside
    display.setFont(&FreeSansBold18pt7b);
    display.setCursor(0, 30);
    display.print("Ulkona");

    display.setFont(&FreeSansBold24pt7b);

    display.setCursor(0, 80);
    display.print(tempOut);

    display.setCursor(100, 80);
    display.print(ws10Out + "m/s");

    display.setFont(&FreeSansBold18pt7b);
    display.setCursor(300, 30);
    display.print("6h: " + temp6h);
    display.setCursor(300, 60);
    display.print("12h: " + temp12h);
    display.setCursor(300, 90);
    display.print("24h: " + temp24h);

    // Print inside
    display.setFont(&FreeSansBold12pt7b);

    display.setCursor(0, 120);
    display.print("Sisa: " + tempIn + "'C / " + rhIn + "%   Tulo: " + tempTulo + "'C / " + rhTulo + "%");

    display.drawFastHLine(0, 130, 450, 0x0000);
    display.drawFastHLine(0, 131, 450, 0x0000);

    // Print RSS
    display.setFont(&FreeSerifBold18pt7b);

    display.setCursor(0, 163);
    display.print("- " + rss0 + " -\r\n" + rss1 + "\r\n\r\n" + rss2 + "\r\n\r\n" + rss3 + "\r\n\r\n" + rss4);
  } while (display.nextPage());

  Serial.println("drawEpaper done");
}

void connectWifi()
{
  Serial.print("Connecting to ");
  Serial.println(ssid_home);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid_home, password_home);

  //IPAddress ip(192,168,1,50);
  //IPAddress gateway(192,168,1,1);
  //IPAddress subnet(255,255,255,0);
  //WiFi.config(ip, gateway, subnet);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");

    if (WiFi.status() == WL_NO_SSID_AVAIL)
    {
      WiFi.disconnect();
      break;
    }
  }

  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

/*
 * Call the AWS endpoint
 */
String callAWS(const char *host, String api_key)
{

  WiFiClientSecure client;
  Serial.print("connecting to ");
  Serial.println(host);

  // ###### Open HTTP connection #######
  if (!client.connect(host, httpsPort))
  {
    Serial.println("connection failed");
    delay(10000);
    return "";
  }

  String url = "/dev/epaperbff";

  // ###### Send GET Request ######
  client.print(String("GET ") + url + " HTTP/1.1\r\n" +
               "Host: " + host + "\r\n" +
               "User-Agent: epaper-esp8266\r\n" +
               "x-api-key: " + api_key + "\r\n" +
               "Connection: close\r\n\r\n");

  Serial.println("request sent");

  while (client.connected())
  {
    String line = client.readStringUntil('\n');

    if (line == "\r")
    {
      Serial.println("headers received");
      break;
    }
  }

  String line = client.readStringUntil('}');
  line = line + "}";

  client.stop();

  Serial.println("reply was:");
  Serial.println(line);

  return line;
}
