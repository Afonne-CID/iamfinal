import json
from jose import jwt
from functools import wraps
from urllib.request import urlopen
from flask import Flask, request


AUTH0_DOMAIN = 'iamfinal.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'iamfinal'


## AuthError Exception
class AuthError(Exception):
    '''AuthError Exception class
    A standardized way to communicate auth failure modes
    '''
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header
def get_token_auth_header():
    '''Retrieves Access Token from the Header if exists, else raises exception
    '''
    auth = request.headers.get('Authorization', None)
    if auth is None:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization Header is required.'
        }, 401)
    
    auth_tokenized = auth.split(' ')
    auth_tokenized[0].lower() == 'bearer'
    if auth_tokenized[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization Header must start with "Bearer".'
        }, 401)

    if len(auth_tokenized) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found'
        }, 401)

    if len(auth_tokenized) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be <bearer> <token>'
        }, 401)
    
    return auth_tokenized[1]


def check_permissions(permission, payload):
    '''Confirms that permissions and `permission` in payload
    '''
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_request',
            'description': 'Permissions not in JWT'
        }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized_access',
            'description': 'Permission not found'
        }, 403)

    return True


def verify_decode_jwt(token):
    '''Verifies and authenticates or reject a user
    '''
    jsonurl = urlopen('https://{}/.well-known/jwks.json'.format(AUTH0_DOMAIN))
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed'
        }, 401)
    
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://{}/'.format(AUTH0_DOMAIN)
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': '''Invalid claims.
                                Please cross-check your audience and issuer'''
            }, 401)

        except Exception as e:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token'
            }, 400)

    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key'
    }, 400)


def requires_auth(permissions=''):
    '''@requires_auth(permission) decorator method
    '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permissions, payload)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator