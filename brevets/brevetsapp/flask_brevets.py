"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)
"""

import flask
from flask import request, redirect, url_for, render_template
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations
#import config

import logging

import os
from pymongo import MongoClient


###
# Globals
###
app = flask.Flask(__name__)


# CONFIG = config.configuration()
client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.tododb


###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')


# Renders display.html that has the last saved data
@app.route("/_display")
def _dispaly():
    app.logger.debug("ACP Brevet Disaplay")
    return flask.render_template('display.html', items = list(db.tododb.find()))


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float)
    app.logger.debug("km={}".format(km))
    app.logger.debug("request.args: {}".format(request.args))
    date = request.args.get('date', type=str)                   # gets date
    time = arrow.get(date, 'YYYY-MM-DDTHH:mm')                  # create arrow for date
    length = request.args.get('length', type=int)               # gets brevet total length
    # FIXME!
    # Right now, only the current time is passed as the start time
    # and control distance is fixed to 200
    # You should get these from the webpage!

    # Now able to choose brevet race length and is now passing adjusted arrow for time
    open_time = acp_times.open_time(km, length, time).format('YYYY-MM-DDTHH:mm')
    close_time = acp_times.close_time(km, length, time).format('YYYY-MM-DDTHH:mm')
    result = {"open": open_time, "close": close_time}
    return flask.jsonify(result=result)

@app.route("/_submit", methods=['POST'])
def _submit():
    app.logger.debug("Got data to submit")
    db.tododb.drop()
    for i in range(len(request.form.getlist('km'),)):
        item_doc = {
            'km': request.form.getlist('km'),
            'open': request.form.getlist('open'),
            'close': request.form.getlist('close')
        }
    db.tododb.insert_one(item_doc)
    return redirect(url_for('index'))


#############

# app.debug = CONFIG.DEBUG
# if app.debug:
#     app.logger.setLevel(logging.DEBUG)
#
# if __name__ == "__main__":
#     print("Opening for global access on port {}".format(CONFIG.PORT))
#     app.run(port=CONFIG.PORT, host="0.0.0.0")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
