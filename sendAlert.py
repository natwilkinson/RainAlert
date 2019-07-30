import datetime
import requests
import os
from twilio.rest import Client
import psycopg2

# example info from database:
#[('30080', 40, 80, True, True, datetime.datetime.now() - datetime.timedelta(days=1), 'Natalie', '6782188624'),
#('94117', 60, 40, True, True, None, 'Yash', '6302173889')]

# [ (), (), ()]
def main():
    data = get_data_and_format()
    for individual_data in data:
        # checkWeather is a boolean
        # determines whether or not the program calls API for user
        #checkWeather = user_notification_status(individual_data[5])
        #if not checkWeather:
            #continue
        # zip_data contains the weather info for user's zipcode
        zip_data = location_weather(individual_data[0])
        bad_weather = check_weather_conditions(individual_data, zip_data)
        if len(bad_weather) == 0:
            print("nothing bad")
            continue
        text_content = format_text(individual_data[6], bad_weather)
        send_text(text_content, individual_data[7])
        update_last_message_time(individual_data[7])

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

def get_data_and_format():
    database_connect = psycopg2.connect(host=os.environ['postgres_host'],database=os.environ['postgres_database'], user=os.environ['postgres_user'], password=os.environ['postgres_password'])
    cur = database_connect.cursor()
    cur.execute(""" SELECT * FROM public."userData"
                        WHERE "userData"."lastMessage" < now() - interval '12 hours'
                        OR "userData"."lastMessage" is null;""")
    data = cur.fetchall()
    cur.close()
    return data

def send_text(content, phone):
    account_sid = os.environ['twilio_account_sid']
    auth_token = os.environ['twilio_auth_token']
    client = Client(account_sid, auth_token)

    message = client.messages \
        .create(
            body=content,
            from_='+14702607494',
            to='+1' + phone
        )



def format_text(name, bad_weather):
    message = ""
    for condition in bad_weather:
        condition = condition + "\n"
        message += condition
    output_string = "Hello, {}!\nThe weather in your location has changed recently.\n{}".format(name, message)
    return output_string

# checks the location weather conditions against user's bad weather input
# returns a list of the weather conditions that are considered bad
def check_weather_conditions(individual_data, zip_data):
    #print(zip_data)
    zip_temp_kelvin = zip_data["main"]["temp"]
    zip_temp_f = round(((zip_temp_kelvin - 273.15) * (9/5) + 32), 2)
    bad_weather = []
    # compare location temp to bad weather conditions
    if zip_temp_f > individual_data[2]:
        hot = "The temperature is {} ºF.".format(zip_temp_f)
        bad_weather.append(hot)
    if zip_temp_f < individual_data[1]:
        cold = "The temperature is {} ºF.".format(zip_temp_f)
        bad_weather.append(cold)
    if individual_data[3] or individual_data[4]:
        zip_weather = zip_data["weather"][0]["main"]
        if individual_data[3] == True:
            if zip_weather == "Rain":
                weather = "It is currently raining."
                bad_weather.append(weather)
        if individual_data[3] == True:
            if zip_weather == "Snow":
                weather = "It is currently snowing."
                bad_weather.append(weather)
    return bad_weather


# gets weather at zipcode location
def location_weather(zip):
    zip_URL = "http://api.openweathermap.org/data/2.5/weather?zip={},us&APPID={}".format(str(zip), os.environ['weather_api_key'])
    zip_search = requests.get(zip_URL)
    if zip_search.status_code == 200:
            zip_data = zip_search.json()
            return zip_data

# last message in datetime format
def user_notification_status(last_message):
    if last_message == None:
        return True
        # send text
    current_time = datetime.datetime.utcnow()
    # gives time since last text in hours
    time = current_time - last_message
    time_since_text = (current_time - last_message).total_seconds() / 3600
    if time_since_text >= 12:
        return True
        # send text
    return False

main()