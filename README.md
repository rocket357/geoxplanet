# geoxplanet
Rebirth of https://sourceforge.net/projects/geoxplanet/

How to use:

    pip install netaddr requests
    git clone https://github.com/rocket357/geoxplanet.git
    cd geoxplanet/src
    python GeoXPlanet.py

Current status:
The "infrastructure" code is in place, minus the actual image generation bits.  For now, the code will auto-download
the Maxmind GeoLite2 database (corruption occurs on Windows, workarounds below), unzip it, and format the data into
a sqlite3 database.  Then the code will loop over netstat output (planned: pflow/netflow support) and perform db lookups
on the IP Connections it finds to public IPs.

Windows Corruption workaround:

    1) Download:  https://geolite.maxmind.com/download/geoip/database/GeoLite2-City-CSV.zip
    2) Move the downloaded file to %USERPROFILE%/.config/GeoXPlanet
    3) Unzip the file to %USERPROFILE%/.config/GeoXPlanet/GeoLite2/
    
This will create %USERPROFILE%/.config/GeoXPlanet/GeoLite2/GeoLite2-City-CSV_$DATE
Then relaunch the script which will then perform a sanity check on the database and rebuild it upon failure.
