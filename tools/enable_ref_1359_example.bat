@echo off
REM Edit the database path if your HomeSeer installation differs.
REM Stop the mcsMQTT plugin before running the --apply command.

python mcsmqtt_bulk_enable.py ^
  --db "C:\Program Files (x86)\HomeSeer HS4\Data\mcsMQTT\mcsMQTT.db" ^
  --homeseer-url "http://192.168.0.193" ^
  --broker-ip "192.168.0.5" ^
  --refs "1359" ^
  --apply

pause
