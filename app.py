# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()
Base.prepare(autoload_with=engine)
print(Base)
Measurement = Base.classes.measurement
Station = Base.classes.station

session = Session(engine)

app = Flask(__name__)

@app.route("/")
def home():
    """List all available routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/YYYY-MM-DD<br/>"
        f"/api/v1.0/startYYYY-MM-DD/endYYYY-MM-DD;"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data."""
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    if most_recent_date is None:
        return jsonify({"error": "No data available."}), 404

    one_year_ago = dt.datetime.strptime(most_recent_date[0], "%Y-%m-%d") - dt.timedelta(days=365)

    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()

    if not results:
        return jsonify({"error": "No data available for the last 12 months."}), 404

    precipitation_data = {date: prcp for date, prcp in results}

    session.close()

    return jsonify(precipitation_data)


@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    with engine.connect() as conn:
        station_results = conn.execute("SELECT station FROM Station").fetchall()
        stations_list = [result[0] for result in station_results]

    if not stations_list:
        return jsonify({"error": "No stations available."}), 404

    session.close()

    return jsonify(stations_list)


@app.route("/api/v1.0/tobs")
def tobs():
    """Return the temperature observations for the previous year of the most active station."""
    session = Session(engine)

    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).\
        first()

    most_recent_date = session.query(Measurement.date).\
        filter(Measurement.station == most_active_station[0]).\
        order_by(Measurement.date.desc()).\
        first()

    one_year_ago = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d') - dt.timedelta(days=365)

    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station[0]).\
        filter(Measurement.date >= one_year_ago).\
        all()

    tobs_data = {date: tobs for date, tobs in results}

    session.close()

    return jsonify(tobs_data)


@app.route("/api/v1.0/<start>")
def temperature_start(start):
    """Return the minimum, average, and maximum temperatures for dates greater than or equal to the start date."""
    session = Session(engine)

    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start).\
        all()

    temperature_data = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    session.close()

    return jsonify(temperature_data)


@app.route("/api/v1.0/<start>/<end>")
def temperature_start_end(start, end):
    """Return the minimum, average, and maximum temperatures for dates from the start date to the end date (inclusive)."""
    session = Session(engine)

    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).\
        all()

    temperature_data = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    session.close()

    return jsonify(temperature_data)

if __name__ == '__main__':
    app.run(debug=True)
