from owletpy.OwletPy import OwletPy
import sys
import time
from pprint import pprint

if len(sys.argv) != 3:
    print('usage:  python3 test.py username password \n')
else:

    print('using username: ' + sys.argv[1] + '\n')
    print('using password: ' + sys.argv[2] + '\n')

    print('\n\n\n')

    pyowletClient = OwletPy(sys.argv[1], sys.argv[2])

    print('Our client is instantiated and should have populated attributes')

    print('DSN: ' + pyowletClient.dsn)
    print('\n\n')
    print('BASE_STATION_ON: ' + str(pyowletClient.base_station_on))
    print('\n\n')
    print('movement: ' + str(pyowletClient.movement))
    print('\n\n')
    print('prop_expire_time: ' + str(pyowletClient.prop_expire_time))
    print('\n\n\n')
    
    print('These properties will fetch new information automatically if the information is older than 15 seconds.\n')
    print('You can also bypass the ratelimiting and refresh the properties manually\n')

    pyowletClient.update_properties()
    
    print('Or query for raw measurements individually\n')
    
    properties = [
        'OXYGEN_LEVEL',
        'HEART_RATE',
        'BASE_STATION_ON',
        'BATT_LEVEL',
        'MOVEMENT',
        'SOCK_OFF',
        'CHARGE_STATUS',
        'BABY_NAME',
        'SOCK_CONNECTION'
    ]

    # Get individual raw properties
    for measure in properties:
        val = pyowletClient.get_properties(measure)
        print(val)
        print('\n')
