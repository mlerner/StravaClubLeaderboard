from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, jsonify, abort
import requests
import json
import datetime
import calendar
import os

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():

    #If you posted, try to redirect to a club page (you submitted the club ID form)
    if request.method == 'POST':
        if request.form['club_id']:
            club_id = request.form['club_id']
            print club_id
            redirect_url = '/club/' + club_id
            return redirect(redirect_url)
    return render_template('index.html')

@app.route('/club/<club_id>')
def show_club_leaderboard(club_id):
    club_data = {}
    existing_users = {}
    returned_club_data = requests.get('http://www.strava.com/api/v1/clubs/' + str(club_id))
    #    If you don't have an error message in the returned JSON, continue.
    #    otherwise, 404. Maybe someone is trying to break your code...
    if u'error' not in returned_club_data.json:
        existing_users = requests.get('http://www.strava.com/api/v1/clubs/' + str(club_id) + '/members')
        leaderboard = map_rides_to_users(existing_users, club_id)
        leaderboard_by_elevation = sorted(leaderboard, key=lambda k: k['elevation_gain'], reverse=True)
        leaderboard_by_average_climbing = sorted(leaderboard, key=lambda k: k['climbing_per_ride'], reverse=True)
        leaderboard_by_distance = sorted(leaderboard, key=lambda k: k['distance'], reverse=True)
        leaderboard_by_rides = sorted(leaderboard, key=lambda k: k['number_of_rides'], reverse=True)
        club_data = returned_club_data.json 
        now = datetime.datetime.now()
        current_month = calendar.month_name[now.month]
        return render_template('club.html', leaderboard_date=current_month, club_data=club_data, ranked_by_elevation=leaderboard_by_elevation, ranked_by_avg_climbing=leaderboard_by_average_climbing, ranked_by_rides=leaderboard_by_rides, ranked_by_distance=leaderboard_by_distance)
    abort(404)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def map_rides_to_users(existing_users, club_id):
    offset = 0
    leaderboard = []
    now = datetime.datetime.now()
    print existing_users.json
    for member in existing_users.json[u'members']:

        #   Initialize the user data you want to rank on
        member['distance'] = 0
        member['elevation_gain'] = 0
        member['moving_time'] = 0
        member['number_of_rides'] = 0
        member['climbing_per_ride'] = 0
        receiving_json_results = True

        #   While you haven't changed the receiving JSON flag, continue 
        #   adding rides to the user collection.
        while(receiving_json_results):
            club_ride_data_url = 'http://app.strava.com/api/v1/rides?athleteId=' + str(member[u'id']) +'&startDate=' + str(now.year) +'-' + str(now.month) + '-01&clubId=' + str(club_id) + '&offset=' + str(offset)
            #print club_ride_data_url
            club_ride_data = requests.get(club_ride_data_url)
            if len(club_ride_data.json[u'rides']) == 0:
                receiving_json_results = False;
            else:
                for ride in club_ride_data.json[u'rides']:
                    ride_result_data = requests.get('http://www.strava.com/api/v2/rides/' + str(ride[u'id']))

                    #   Add up all of the metrics
                    member['distance'] += ride_result_data.json[u'ride'][u'distance']
                    member['elevation_gain'] += ride_result_data.json[u'ride'][u'elevation_gain']
                    member['moving_time'] += (ride_result_data.json[u'ride'][u'moving_time'])
                    member['number_of_rides'] += 1
            offset = offset + 50
        if member['number_of_rides'] == 0:
            member['climbing_per_ride'] = 0
        else:
            member['climbing_per_ride'] = (member['elevation_gain']/member['number_of_rides'])
        leaderboard.append(member)
        offset = 0
        #print club_ride_data.json

    return leaderboard

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

