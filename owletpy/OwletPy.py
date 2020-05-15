REQUIREMENTS = ['pyrebase==3.0.27']


import json
import logging
import time
import sys
import requests
import pyrebase

logging.basicConfig(filename='pyowlet.log', level=logging.DEBUG)


class OwletPy(object):

    def __init__(self, username, password, prop_ttl=15):
        self.auth_token = None
        self.expire_time = 0
        self.prop_expire_time = 0
        self.prop_ttl = prop_ttl
        self.app_active_expire = 0
        self.app_active_ttl = 5
        self.username = username
        self.password = password
        self.headers = None
        self.auth_header = None
        self.monitored_properties = []
        self.app_active_prop_id = None
        self.owlet_region = 'world'
        self.region_config = {
                                'world': {
                                    'url_mini': 'https://ayla-sso.owletdata.com/mini/',
                                    'url_signin': 'https://user-field-1a2039d9.aylanetworks.com/api/v1/token_sign_in',
                                    'url_base': 'https://ads-field-1a2039d9.aylanetworks.com/apiv1',
                                    'apiKey': 'AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA',
                                    'databaseURL': 'https://owletcare-prod.firebaseio.com',
                                    'storage_bucket': 'owletcare-prod.appspot.com',
                                    'app_id': 'sso-prod-3g-id',
                                    'app_secret': 'sso-prod-UEjtnPCtFfjdwIwxqnC0OipxRFU',
                                },
                                'europe': {
                                    'url_mini': 'https://ayla-sso.eu.owletdata.com/mini/',
                                    'url_signin': 'https://user-field-eu-1a2039d9.aylanetworks.com/api/v1/token_sign_in',
                                    'url_base': 'https://ads-field-eu-1a2039d9.aylanetworks.com/apiv1',
                                    'apiKey': 'AIzaSyDm6EhV70wudwN3iOSq3vTjtsdGjdFLuuM',
                                    'databaseURL': 'https://owletcare-prod-eu.firebaseio.com',
                                    'storage_bucket': 'owletcare-prod-eu.appspot.com',
                                    'app_id': 'OwletCare-Android-EU-fw-id',
                                    'app_secret': 'OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw',
                                }
                              }


        self.auth_token = self.login(username, password)
        self.dsn = self.get_dsn()

        self.update_properties()

    def get_auth_header(self):
        '''
        Get the auth token. If the current token has not expired, return that.
        Otherwise login and get a new token and return that token.
        '''

        # if the auth token doesnt exist or has expired, login to get a new one
        if (self.auth_token is None) or (self.expire_time <= time.time()):
            logging.debug('Auth Token expired, need to get a new one')
            self.login(self.username, self.password)

        self.auth_header = {'content-type': 'application/json',
                            'accept': 'application/json',
                            'Authorization': 'auth_token ' + self.auth_token
                            }

        return self.auth_header

    def get_dsn(self):
        dsnurl = 'https://ads-field-1a2039d9.aylanetworks.com/apiv1/devices.json'
        response = requests.get(dsnurl, headers=self.get_auth_header())
        # data = auth_header(url)
        json_data = response.json()
        # FIXME: this is just returning the first device in the list
        # dsn = json_data[0]['device']['dsn']
        return json_data[0]['device']['dsn']

    def get_properties(self, measure=None, set_active=True):

        if set_active is True:
            self.set_app_active()

        properties_url = 'https://ads-field-1a2039d9.aylanetworks.com/apiv1/dsns/{}/properties'.format(
            self.dsn)

        if measure is not None:
            properties_url = properties_url + '/' + measure

        response = requests.get(properties_url, headers=self.get_auth_header())
        data = response.json()

        if measure is not None:
            return data['property']

        return data

    def set_app_active(self):

        if self.app_active_expire < time.time():

            if self.app_active_prop_id is None:
                prop = self.get_properties('APP_ACTIVE', False)
                self.app_active_prop_id = prop['key']

            data_point_url = 'https://ads-field-1a2039d9.aylanetworks.com/apiv1/properties/{}/datapoints.json'.format(
                self.app_active_prop_id)

            payload = {'datapoint': {'value': 1}}
            resp = requests.post(
                data_point_url,
                json=payload,
                headers=self.get_auth_header()
            )

            self.app_active_expire = time.time() + self.app_active_ttl

    def update_properties(self):

        self.set_app_active()

        data = self.get_properties()

        for value in data:
            name = value['property']['name'].lower()
            val = value['property']['value']

            if name not in self.monitored_properties:
                self.monitored_properties.append(name)

            self.__setattr__(name, val)

        self.prop_expire_time = time.time() + self.prop_ttl

    def __getattribute__(self, attr):

        monitored = object.__getattribute__(self, 'monitored_properties')
        prop_exp = object.__getattribute__(self, 'prop_expire_time')

        if attr in monitored and prop_exp <= time.time():
            self.update_properties()

        return object.__getattribute__(self, attr)

    def login(self, email, password):
        try:
            owlet_user, owlet_pass = email, password
            if not len(owlet_user):
                raise FatalError("OWLET_USER is empty")
            if not len(owlet_pass):
                raise FatalError("OWLET_PASS is empty")
        except KeyError as e:
            raise FatalError("OWLET_USER or OWLET_PASS env var is not defined")
        if self.owlet_region not in self.region_config:
            raise FatalError("OWLET_REGION env var '{}' not recognised - must be one of {}".format(
                self.owlet_region, self.region_config.keys()))
        if self.auth_token is not None and (self.expire_time > time.time()):
            return
        # authenticate against pyrebase, get the JWT
        config = {
                "apiKey": self.region_config[self.owlet_region]['apiKey'],
                "databaseURL": self.region_config[self.owlet_region]['databaseURL'],
                "storageBucket":self.region_config[self.owlet_region]['storage_bucket'],
                "authDomain": None,
                }
        pb = pyrebase.initialize_app(config)
        auth = pb.auth()
        user = auth.sign_in_with_email_and_password(owlet_user, owlet_pass)
        jwt = user['idToken']
        # authenticate against owletdata.com, get the mini_token
        r = requests.get(self.region_config[self.owlet_region]
                         ['url_mini'], headers={'Authorization': jwt})
        r.raise_for_status()
        mini_token = r.json()['mini_token']
        # authenticate against Ayla, get the access_token
        r = requests.post(self.region_config[self.owlet_region]['url_signin'], json={
                    "app_id": self.region_config[self.owlet_region]['app_id'],
                    "app_secret": self.region_config[self.owlet_region]['app_secret'],
                    "provider": "owl_id",
                    "token": mini_token,
                    })
        r.raise_for_status()
        self.auth_token = r.json()['access_token']
        # we will re-auth 60 seconds before the token expires
        self.expire_time = time.time() + r.json()['expires_in'] - 60