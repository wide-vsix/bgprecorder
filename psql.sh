#!/bin/bash
source .env
PGPASSWORD=$BGPRECORDER_DB_PASSWORD
sudo docker-compose exec postgres psql --username=$BGPRECORDER_DB_USER  -d $BGPRECORDER_DB_NAME 
