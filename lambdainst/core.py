from datetime import timedelta, datetime
import lcoreapi
from django.conf import settings
from django.core.mail import mail_admins
import logging

cluster_messages = settings.LAMBDAINST_CLUSTER_MESSAGES

lcore_settings = settings.LCORE

LCORE_BASE_URL = lcore_settings.get('BASE_URL')
LCORE_API_KEY = lcore_settings['API_KEY']
LCORE_API_SECRET = lcore_settings['API_SECRET']
LCORE_SOURCE_ADDR = lcore_settings.get('SOURCE_ADDRESS')
LCORE_INST_SECRET = lcore_settings['INST_SECRET']

# The default is to log the exception and only raise it if we cannot show
# the previous value or a default value instead.
LCORE_RAISE_ERRORS = bool(lcore_settings.get('RAISE_ERRORS', False))

LCORE_CACHE_TTL = lcore_settings.get('CACHE_TTL', 60)
if isinstance(LCORE_CACHE_TTL, int):
    LCORE_CACHE_TTL = timedelta(seconds=LCORE_CACHE_TTL)
assert isinstance(LCORE_CACHE_TTL, timedelta)

VPN_AUTH_STORAGE = settings.VPN_AUTH_STORAGE
assert VPN_AUTH_STORAGE in ('core', 'inst')

core_api = lcoreapi.API(LCORE_API_KEY, LCORE_API_SECRET, LCORE_BASE_URL)


class APICache:
    """ Cache data for a time, try to update and silence errors.
    Outdated data is not a problem.
    """
    def __init__(self, ttl=None, initial=None):
        self.cache_date = datetime.fromtimestamp(0)
        self.ttl = ttl or LCORE_CACHE_TTL

        self.has_cached_value = initial is not None
        self.cached = initial() if initial else None

    def query(self, wrapped, *args, **kwargs):
        try:
            return wrapped(*args, **kwargs)
        except lcoreapi.APIError:
            logger = logging.getLogger('django.request')
            logger.exception("core api error")

            if LCORE_RAISE_ERRORS:
                raise

            if not self.has_cached_value:
                # We only return a default value if we were given one.
                # Prevents returning an unexpected None.
                raise

            # Return previous value
            return self.cached

    def __call__(self, wrapped):
        def wrapper(*args, **kwargs):
            if self.cache_date > (datetime.now() - self.ttl):
                return self.cached

            self.cached = self.query(wrapped, *args, **kwargs)

            # New results *and* errors are cached
            self.cache_date = datetime.now()
            return self.cached
        return wrapper


@APICache(initial=lambda: 0)
def current_active_sessions():
    return core_api.get(core_api.info['current_instance'] + '/sessions', active=True)['total_count']


@APICache(initial=lambda: [])
def get_locations():
    gateways = core_api.get('/gateways/')
    locations = {}

    for gw in gateways.list_iter():
        cc = gw['cluster_name']

        if cc not in locations:
            locations[cc] = dict(
                servers=0,
                bandwidth=0,
                hostname='gw.' + cc + '.204vpn.net',
                country_code=cc,
                message=cluster_messages.get(cc),
            )

        locations[cc]['servers'] += 1
        locations[cc]['bandwidth'] += gw['bandwidth']

    locations = sorted(locations.items(), key=lambda x: x[1]['country_code'])
    return locations


def create_user(username, cleartext_password):
    """ The password will be hashed and stored safely on the core,
    so we have to send it clearly here.
    """
    path = core_api.info['current_instance'] + '/users/'
    core_api.post(path, data={
        'username': username,
        'password': cleartext_password,
        'expiration_date': datetime(1, 1, 1).isoformat(),  # Expired.
    })


def update_user_expiration(user):
    path = core_api.info['current_instance'] + '/users/' + user.username

    try:
        if not user.is_active:
            core_api.patch(path, data={
                'expiration_date': datetime(1, 1, 1).isoformat(),  # Expired.
            })
            return

        core_api.patch(path, data={
            'expiration_date': user.vpnuser.expiration,
        })
    except lcoreapi.APIError:
        # User can't do anything to this, we should just report it
        logger = logging.getLogger('django.request')
        logger.exception("core api error, missing user (exp update)")


def update_user_password(user, cleartext_password):
    path = core_api.info['current_instance'] + '/users/' + user.username

    try:
        core_api.patch(path, data={
            'password': cleartext_password,
        })
    except lcoreapi.APINotFoundError:
        # This time we can try fix it!
        create_user(user.username, cleartext_password)
    except lcoreapi.APIError:
        # and maybe fail.
        logger = logging.getLogger('django.request')
        logger.exception("core api error (password update)")


def delete_user(username):
    path = core_api.info['current_instance'] + '/users/' + username
    core_api.delete(path)

