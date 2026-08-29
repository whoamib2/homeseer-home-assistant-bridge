@echo off
REM Edit the database path if your HomeSeer installation differs.
REM Stop the mcsMQTT plugin before running the --apply command.

python mcsmqtt_bulk_enable.py ^
  --db "C:\Program Files (x86)\HomeSeer HS4\Data\mcsMQTT\mcsMQTT.db" ^
  --homeseer-url "http://homeseer.local" ^
  --broker-ip "192.168.1.10" ^
  --refs "1234" ^
  --apply

pause
