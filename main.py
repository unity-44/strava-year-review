from flask import Flask, redirect, request, session, render_template
import os
import requests
from datetime import datetime
import calendar
import polyline

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')

@app.route('/')
def index():
    # Return some HTML with an "Authorize" button
    return render_template('index.html')

@app.route('/authorize')
def authorize():
    # Redirect the user to the Strava authorization page
    return redirect(
        f'http://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}&response_type=code&redirect_uri=http://localhost:4444/exchange_token&approval_prompt=force&scope=read,activity:read'
    )

@app.route('/exchange_token')
def exchange_token():
    # Get the authorization code from the query string
    code = request.args.get('code')

    # If there is no code in the query string, return an error message
    if not code:
        return 'No authorization code found in the query string', 400

    # Exchange the authorization code for an access token
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
    )

    # If the request was successful, store the access token in the session and redirect the user to the /get_data route
    if response.status_code == 200:
        session['access_token'] = response.json()['access_token']
        return redirect('/authorization_successful')
    else:
        return 'Failed to exchange authorization code for access token', 400

@app.route('/authorization_successful')
def authorization_successful():
    return render_template('authorization_successful.html')

@app.route('/home')
def home():
    # Fetch the latest activity 
    activities = fetch_activities(session['access_token'])
    if activities:
        latest_activity = activities[0] # Assuming the activities are sorted by date
        longest_activity = most_km = find_longest_activity(activities)
        most_km_month, most_km, months = most_km_ridden_in_a_month(activities)
        months = {calendar.month_name[month]: round(km, 0) for month, km in months.items()}
        sorted_months = sorted(months.items(), key=lambda item: item[1], reverse=True)
        d_months = dict(sorted_months)
        polyline_latest_activity = latest_activity['polyline']
        decoded_polyline = polyline.decode(polyline_latest_activity)
        

    else:
        latest_activity = None


    # Render the home.html template and pass the latest activity and longest activity to the template
    return render_template('home.html', activity=latest_activity, longest_activity=longest_activity, most_km_month=most_km_month, most_km=most_km, months=list(d_months.keys())[0][:3], decoded_polyline=decoded_polyline )



def fetch_activities(access_token):
    # Use the access token to fetch data from Strava
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://www.strava.com/api/v3/athlete/activities', headers=headers)
    data = response.json()

    # Process the data
    activities = []
    for activity in data:
        id = activity['id']
        name = activity['name']
        distance = activity['distance'] / 1000  # Convert distance from meters to kilometers
        average_speed = activity['average_speed'] * 3.6 # Convert speed from m/s to km/h
        start_date_local =  activity['start_date_local']
        polyline = activity['map']['summary_polyline']


        activities.append({
            'id': id,
            'name': name,
            'distance': round(distance, 2),  # Round to 2 decimal places
            'average_speed': round(average_speed, 2),
            'start_date_local' : start_date_local,
            'polyline': polyline,

        })

    return activities

def find_longest_activity(activities):
    # Find the activity with the longest distance
    longest_activity = {'distance': 0}
    for activity in activities:
        distance = activity.get('distance', 0) # Access the distance value using the 'distance' key
        if distance > longest_activity.get('distance'):
            longest_activity = activity

    return longest_activity


def most_km_ridden_in_a_month(activities):
    # Find the month with the most kilometers ridden
    months = {}
    for activity in activities:
        start_date = datetime.strptime(activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ')
        month = start_date.month # Get the month number
        if month in months:
            months[month] += activity['distance']
        else:
            months[month] = activity['distance']

    # Find the month with the most kilometers ridden
    most_km = 0
    most_km_month = None
    for month, km in months.items():
        if km > most_km:
            most_km = km
            most_km_month = calendar.month_name[month]

    return most_km_month, round(most_km, 0), months  # Round to 2 decimal places



if __name__ == '__main__':
    app.run(debug=True, port=4444)
def index():
    return 'Hello, World!'
