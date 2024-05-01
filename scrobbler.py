from datetime import datetime, timedelta
import math
import requests
import argparse
import sys
import discogs_client

version = 1.0

# SET YOUR KEYS HERE
DISCOGS_TOKEN="YOUR KEY"
MALOJA_URL="INSTANCE"
MALOJA_API_KEY="YOUR KEY"


# color codes for printing in terminal
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    NUMBER = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# parse parameters
parser = argparse.ArgumentParser(
                    prog='MalojaManualScrobbler',
                    description='Script to manually scrobble albums to your maloja instance',
                    epilog='Please refer to the github repo for more information')

parser.add_argument("-ar", "--artist", type=str)
parser.add_argument("-al", "--album", type=str)
parser.add_argument("-r","--release",type=str)
parser.add_argument("-d","--date",type=str)

args = parser.parse_args()
artist = args.artist
album = args.album
release_id = args.release
date_argument = args.date

client = discogs_client.Client("MalojaManualScrobbler/{}".format(version), user_token=DISCOGS_TOKEN)

if release_id and release_id.isdigit():
    release_id = int(release_id)
else: # get release manually if not defined by parameters
    
    # check if enough parameters passed
    if ((not album or not artist) and not release_id):
        print(bcolors.FAIL + "Artist or Album not defined" + bcolors.ENDC)
        sys.exit()
    result_count = 0



    # search for passed parameters
    try:
        results = client.search(album,artist=artist,type='release')
    except:
        print(bcolors.FAIL + "Search failed" + bcolors.ENDC)
        sys.exit();


    # display search results
    print("------ " + bcolors.BOLD + "RESULTS" + bcolors.ENDC + " ------")
    result_count = 0

    max_iterations = 20 # maximum number of results to show
    for entry in results:

        if result_count == max_iterations:
            break

        result_count += 1
        print("[" + str(result_count) + "] " + entry.title)
    print("---------------------\n")
    chosen_entry = int(input("Choose result (1-" + str(result_count) + "):"))

    # check user input
    # !!yet to implement
    release_id = results[chosen_entry-1].id
# fetch release
try:
    release = client.release(release_id)
except Exception as e:
    print(bcolors.FAIL + "Could not fetch release nr. " + str(release_id) + "[ " + e + "]" + bcolors.ENDC)
    sys.exit()

if date_argument:
    datetime_str = date_argument
else:
    datetime_str = input("When did you start listening to this release? (" + bcolors.OKBLUE + "DD/MM/YY HH:MM" + bcolors.ENDC + "), (or " + bcolors.OKBLUE + "ENTER" + bcolors.ENDC + " for now):")

# check user input
if datetime_str.strip() == "":
    start_time = datetime.now()
else:
    try:
        start_time = datetime.strptime(datetime_str, '%d/%m/%y %H:%M')
    except ValueError:
        print(bcolors.FAIL + "Please input a valid date in the given format or press enter" + str(release_id) + bcolors.ENDC)
        sys.exit()
# !!  yet to do

endpoint = f"{MALOJA_URL}/apis/mlj_1/newscrobble?key={MALOJA_API_KEY}"
headers = {"Content-Type": "application/json"}

tracknum = 0
print("Scrobbling release nr. " + bcolors.OKBLUE +  str(release_id) + bcolors.ENDC)
for track in release.tracklist:

    tracknum += 1
    if track.duration: # check if track even has a duration listed
        # Split the duration string into minutes and seconds
        minutes, seconds = map(int, track.duration.split(':'))
        # Create a timedelta object with the given minutes and seconds
        delta = timedelta(minutes=minutes, seconds=seconds)
        total_seconds = delta.total_seconds() # for scrobbling
        total_seconds = math.ceil(total_seconds) # round up for error correction
    else:
        delta = timedelta(seconds=10)
        total_seconds = 10
    # scrobbling
    scrobble_data = {
        "artists": [artist.name for artist in release.artists],
        "title": track.title,
        "duration": total_seconds,
        "time": int(start_time.timestamp())
    }
   
    

    start_time = start_time + delta # create new starttime for next track

    # scrobble
    response = requests.post(endpoint, json=scrobble_data, headers=headers)
    if response.status_code == 200:
       print(bcolors.OKGREEN + "[" + str(tracknum) +  "] SUCCEED (" + track.title + ")" + bcolors.ENDC)        
    else:
        print(bcolors.FAIL + "[" + str(tracknum) + "9 FAILED ("+ track.title + ")" + bcolors.ENDC)

