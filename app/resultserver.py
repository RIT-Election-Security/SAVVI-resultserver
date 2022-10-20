from quart import Quart, render_template, request

from .ballotserver_utils import challenge_ballot, get_election_results, get_counted_hashes, get_received_hashes

import logging
import graypy
import time

my_logger = logging.getLogger('resultserver')
my_logger.setLevel(logging.DEBUG)
handler = graypy.GELFHTTPHandler('127.0.0.1', port=12201)
#handler = graypy.GELFHandler('127.0.0.1', 12201)
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
        data = await request.body
        decoded = None
        try:
            # lets see if its encoded
            decoded = data.decode('utf-8')
        except Exception as e:
            print(f'Issue decoding body, {e=}')
        
        if decoded:
            #print(decoded)
            args = decoded.split("&")
            #print(args)
            for index, arg in enumerate(args):
                if "email" in arg.lower()  or "password" in arg.lower():
                    args[index] = "cleansed"

        #print(f"CLEANED {args=}")
        my_logger.debug(str(request.headers)+"\nBODY: "+str(args))

        try:
            verification_code = form["verification_code"]
            challenged = challenge_ballot(verification_code)
            if challenged:
                return await render_template("challenge.html", ballot=challenged)
            else:
                return await render_template("challenge.html", error="Verification code does not match a spoiled ballot")
        except KeyError:
            return await render_template("challenge.html", error="Verification code is required")
