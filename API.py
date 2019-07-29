# ------------------------- CONFIGURE ENVIRONMENT ------------------------- #

# Load API tools
import flask
from flask import request, jsonify, render_template, send_from_directory

# Standard math and data libraries
import numpy as np
import pandas as pd

# Date time for date operations
import datetime

# File operations and OS
import os

# Levenshtein fuzzy comparisons
from fuzzywuzzy import fuzz 
from fuzzywuzzy import process

# Import string cleaning functions
import re

# Configure paths
from pathlib import Path
data_path = Path('Datasets')

# ------------------------- IMPORT MANUAL DATA ------------------------- #

# Import from CSV
DataFrame = pd.read_csv(data_path / 'ManualData.csv', encoding = "utf-8");

# Replace missing with NaN object
DataFrame.fillna(np.nan);

# Create Datetime object
Dates = pd.to_datetime( DataFrame[[ DataFrame.columns[0] ]].stack() ).unstack()

# Replace old dates with Datetime
DataFrame[[ DataFrame.columns[0] ]] = Dates[[ Dates.columns[0] ]];

# Convert into a list of dictionaries
DataDict = DataFrame.to_dict('records');

# Define string truncating function
def shorten( string ):
    return str( string.split()[0] )
    
# Efficiently apply truncation to holiday_type column
DataFrame[ DataFrame.columns[3] ] = DataFrame[ DataFrame.columns[3] ].apply(shorten);

# ------------------------- CREATE FLASK API ------------------------- #

# Instantiate the app
app = flask.Flask(__name__);
app.config["DEBUG"] = True;

# ---------- HOME PAGE ---------- #
@app.route('/', methods=['GET'])
def Home():
    return render_template('homepage.html')

# ---------- DOCS PAGE ---------- #
@app.route('/docs', methods=['GET'])
def Docs():
    return render_template('dev_docs.html')

# ---------- HOLIDAY CALL ---------- #
@app.route('/api/holiday', methods=['GET'], defaults={'holiday_type': None})
def GetHolidays( record_count = 10, holiday_type = None ):
    
    # ---------- Settings / Setup ---------- #
    
    # Fuzzy logic tolerances
    threshold = 60
    
    # Get current day
    today = datetime.datetime.today()
    
    # ---------- Handle date_range ---------- #
    
    # If num then cast to int for safety
    if 'record_count' in request.args:
        record_count = int(request.args['record_count'])
        print("Option: record_count = {}".format( record_count ))

    # Sort the next dates within the specified range
    next_dates = sorted( [d for d in DataFrame[ DataFrame.columns[0] ].tolist() if d > today], key = lambda s: s - today )[ 0 : record_count ]
    
    # ---------- Handle holiday_type ---------- #
    
    # Handle holiday_type optionality
    if 'holiday_type' in request.args:
        
        # Pass argument to local variable
        holiday_type = request.args['holiday_type']
        
        # Clean numbers and special characters from query
        holiday_type = re.sub('[!@#$%^&*()0123456789<>,./?;:]', '', holiday_type)
    
        # Setup fuzzy logic comparisons
        similarity = np.array([])
        selected_type = np.nan

        # Iteratively compare the holiday_type with the available options
        for option in DataFrame[ DataFrame.columns[3] ].unique():
            similarity = np.append( similarity, fuzz.ratio( holiday_type, option) )

        # Test for acceptable matches
        if max(similarity) >= threshold:
            selected_type = DataFrame[ DataFrame.columns[3] ].unique()[ np.argmax( similarity ) ]
        
        # Shoutout for debugging
        print("Option: holiday_type = {}".format( selected_type ))
        
        # Run selection
        Selection = DataFrame.loc[ DataFrame[ DataFrame.columns[3] ] == selected_type ].loc[ DataFrame[ DataFrame.columns[0] ] > today ][ 0 : record_count ]
        
    else:
        # Run selection without holiday_type
        Selection = DataFrame[ DataFrame[ DataFrame.columns[0] ].isin(next_dates) ]
        
    # Convert to dict-array then to JSON and return
    return jsonify( Selection.to_dict('records') );

# Execute
if __name__ == '__main__':
    app.run()

