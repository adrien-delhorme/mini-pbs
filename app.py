import httpx
import datetime
import math

from collections import OrderedDict
from flask import Flask
from flask import render_template
from flask import request, redirect
from flask import send_from_directory
from flask import abort

app = Flask(__name__)

station_information = None
API_BASE_URL = "http://api.citybik.es/v2"

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == "GET":
        context = httpx.get(f"{API_BASE_URL}/networks/").json()
        return render_template("index.html", **context)
    elif request.method == "POST":
        return redirect(f"/{request.form['network']}/")


@app.route("/favicon.ico")
def favicon():
    """Serve the favicon to avoid routing conflicts"""
    return send_from_directory("static", "favicon.ico", mimetype="image/x-icon")

@app.route("/<string:network_id>/")
def stations(network_id):
    favorites = request.args.getlist("fav")
    
    try:
        response = httpx.get(f"{API_BASE_URL}/networks/{network_id}?fields=id,name,location,stations", follow_redirects=True)
        response.raise_for_status()  # Raise exception for HTTP errors
        context = response.json()
    except httpx.HTTPStatusError:
        abort(404)
    except (httpx.RequestError, ValueError) as e:
        # Handle network errors or JSON decode errors
        abort(500)

    def compare(other):
        try:
            return (favorites.index(other["id"]), other["id"])
        except ValueError:
            return (math.inf, other["id"])

    # Display user favorites stations first, and keep the order
    context["network"]["stations"] = sorted(context["network"]["stations"], key=compare)

    context.update({
        "favorites": favorites,
        "now": datetime.datetime.now().strftime("%H:%M")
    })
    return render_template("stations.html", **context)


@app.route("/sw.js")
def service_worker():
    """Route to serve the service worker from the root
    
    Service workers have a scope restriction: a service worker registered from
    /static/sw.js can only control pages under /static/, not the entire app.
    By serving it from the root (/sw.js), it can control all routes:
    /, /<network_id>/, /static/..., etc.
    This is the standard practice for PWAs.
    """
    return send_from_directory("static", "sw.js", mimetype="application/javascript")

