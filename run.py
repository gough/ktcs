#!/usr/bin/env python

from ktcs import app
from config import DEBUG, HOST

app.run(debug=DEBUG, host=HOST)
