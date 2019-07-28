"""
TODO:
- (DONE) Take in name, phone number, zipcode, highest temp, lowest temp,
rain, and snow, and the time last messaged.
- (DONE) write script to hit Open Weather Map API for location, and
determine if someone should get a text
- (DONE) set up twilio for text messages
- (DONE) figure out how to run through/read info from the database
- (DONE) figure out how to update the database with a new time
(last sent text, so they don't get updated again for some period of time)
- build a front end connected to the database
- Hide twilio and Weather Map authentication keys, postgres
- Run fxn every __ min
 """
import datetime
import requests
import os
from twilio.rest import Client
import psycopg2

# example info from database:
#data = [['30080', 40, 80, True, True, datetime.datetime.now() - datetime.timedelta(days=1), 'Natalie', '6782188624'],
#['94117', 60, 40, True, True, None, 'Yash', '6302173889']]


def main():
    data = getDataAndFormat()
    for individualData in data:
        # checkWeather is a boolean
        # determines whether or not the program calls API for user
        checkWeather = checkAgain(individualData[5])
        if not checkWeather:
            continue
        # zipData contains the weather info for user's zipcode
        zipData = locationWeather(individualData[0])
        badWeather = checkWeatherConditions(individualData, zipData)
        if len(badWeather) == 0:
            print("nothing bad")
            continue
        textContent = formatText(individualData[6], badWeather)
        sendText(textContent, individualData[7])
        update_last_message_time(individualData[7])

def update_last_message_time(phone):
    sql = """ UPDATE public."userData"
                SET "lastMessage"= now()
                WHERE phone = '{0}'""".format(str(phone))
    err = None
    conn = None
    updated_rows = 0
    try:
        conn = psycopg2.connect(host=os.environ['postgres_host'],database=os.environ['postgres_database'], user=os.environ['postgres_user'], password=os.environ['postgres_password'])
        cur = conn.cursor()
        cur.execute(sql)
        updated_rows = cur.rowcount
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        err = error
        print("error", error)
    finally:
        if conn is not None:
            conn.close()
    return err

def getDataAndFormat():
    databaseConnect = psycopg2.connect(host=os.environ['postgres_host'],database=os.environ['postgres_database'], user=os.environ['postgres_user'], password=os.environ['postgres_password'])
    cur = databaseConnect.cursor()
    cur.execute('SELECT * FROM public."userData";')
    data = cur.fetchall()
    cur.close()
    return data

def sendText(content, phone):
    account_sid = os.environ['twilio_account_sid']
    auth_token = os.environ['twilio_auth_token']
    client = Client(account_sid, auth_token)

    message = client.messages \
        .create(
            body=content,
            from_='+14702607494',
            to='+1' + phone
        )



def formatText(name, badWeather):
    message = ""
    for condition in badWeather:
        condition = condition + "\n"
        message += condition
    outputString = "Hello, {}!\nThe weather in your location has changed recently.\n{}".format(name, message)
    return outputString

# checks the location weather conditions against user's bad weather input
# returns a list of the weather conditions that are considered bad
def checkWeatherConditions(individualData, zipData):
    #print(zipData)
    zipTempKelvin = zipData["main"]["temp"]
    zipTempF = round(((zipTempKelvin - 273.15) * (9/5) + 32), 2)
    badWeather = []
    # compare location temp to bad weather conditions
    if zipTempF > individualData[2]:
        hot = "The temperature is {} ºF.".format(zipTempF)
        badWeather.append(hot)
    if zipTempF < individualData[1]:
        cold = "The temperature is {} ºF.".format(zipTempF)
        badWeather.append(cold)
    if individualData[3] or individualData[4]:
        zipWeather = zipData["weather"][0]["main"]
        if individualData[3] == True:
            if zipWeather == "Rain":
                weather = "It is currently raining."
                badWeather.append(weather)
        if individualData[3] == True:
            if zipWeather == "Snow":
                weather = "It is currently snowing."
                badWeather.append(weather)
    return badWeather


# gets weather at zipcode location
def locationWeather(zip):
    zipURL = "http://api.openweathermap.org/data/2.5/weather?zip={},us&APPID={}".format(str(zip), os.environ['weather_api_key'])
    zipSearch = requests.get(zipURL)
    if zipSearch.status_code == 200:
            zipData = zipSearch.json()
            return zipData

# last message in datetime format
def checkAgain(lastMessage):
    if lastMessage == None:
        return True
        # send text
    currentTime = datetime.datetime.utcnow()
    # gives time since last text in hours
    time = currentTime - lastMessage
    timeSinceText = (currentTime - lastMessage).total_seconds() / 3600
    if timeSinceText >= 12:
        return True
        # send text
    return False

main()