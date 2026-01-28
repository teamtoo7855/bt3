#!/bin/sh
export FLASK_APP=./src/index.py
uv run flask --debug run -p 8080
