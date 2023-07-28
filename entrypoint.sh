#!/bin/bash

if [ "$ENV" = 'TEST' ]; then
    python -m unittest tests
else 
    exec gunicorn --bind :8080 --workers 1 --threads 1 --timeout 120 app:app
fi