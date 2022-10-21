from quart import Quart, render_template, request

from .ballotserver_utils import challenge_ballot, get_election_results, get_counted_hashes, get_received_hashes

import logging
import graypy
import time

my_logger = logging.getLogger('resultserver')
my_logger.setLevel(logging.DEBUG)
handler = graypy.GELFTLSHandler('100.64.242.2', port=12201, certfile='/app/data/server.crt', keyfile='/app/data/server.key')
my_logger.addHandler(handler)


my_logger.debug("RESULTSERVER LOGGER SETUP COMPLETE")

app = Quart(__name__)


@app.route("/")
async def home():
    """
    Home page, welcome

    Returns:
        Rendered template of homepage
    """
    return await render_template('home.html')


@app.route("/results")
async def results():
    """
    Query the ballotserver for the election results

    Returns:
        Rendered template of the results page
    """
    results = get_election_results()
    return await render_template('results.html', results=results)

@app.route("/received_hashes")
async def received_hashes():
    hashes = get_received_hashes()
    return await render_template("hashes.html", title="Received Hashes", hashes=hashes)

@app.route("/counted_hashes")
async def counted_hashes():
    hashes = get_counted_hashes()
    return await render_template("hashes.html", title="Counted Hashes", hashes=hashes)


@app.route("/challenge", methods=["GET", "POST"])
async def challenge():
    """
    Querry the ballotserver by verification code to challenge a spoiled ballot

    Returns:
        Rendered template of challenged ballot or blank if failed
    """
    if request.method == "GET":
        return await render_template("challenge.html")
    elif request.method == "POST":
        form = await request.form
        #print(request.headers)
        data = await request.body
        decoded = None
        try:
            # lets see if its encoded
            decoded = data.decode('utf-8')
            my_logger.debug(str(request.headers)+"\nBODY: "+str(decoded))
        except Exception as e:
            my_logger.debug(f'Issue decoding body, {e=}'+'\n'+request.headers)

        try:
            verification_code = form["verification_code"]
            challenged = challenge_ballot(verification_code)
            if challenged:
                return await render_template("challenge.html", ballot=challenged)
            else:
                return await render_template("challenge.html", error="Verification code does not match a spoiled ballot")
        except KeyError:
            return await render_template("challenge.html", error="Verification code is required")
