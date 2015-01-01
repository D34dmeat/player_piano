#!/bin/bash

cd $HOME/player_piano
source env/bin/activate
mkdir -p logs
crossbar start &> logs/app.log
