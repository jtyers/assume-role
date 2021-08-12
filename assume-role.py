#!/usr/bin/env python3

import configparser
import colorama
import json
import os
#import nuclear
import subprocess
import sys

def msg(*a):
    print(colorama.Fore.GREEN, *a, colorama.Style.RESET_ALL, file=sys.stderr)

def warn(*a):
    print(colorama.Fore.RED, *a, colorama.Style.RESET_ALL, file=sys.stderr)

def main(profile, cmd=os.environ['SHELL']):
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser('~/.aws/config'))

    try:
        role_arn = config.get('profile '+profile, 'role_arn')

    except configparser.NoSectionError:
        warn('profile', profile, 'does not exist')
        sys.exit(1)

    except configparser.NoOptionError:
        warn('profile', profile, 'has no role_arn defined')
        sys.exit(1)

    p = subprocess.run([
        'aws', 'sts', 'assume-role',
        '--role-arn', role_arn,
        '--role-session-name', 'assume-role-session',
    ], capture_output=True)
    
    try:
        p.check_returncode()

    except subprocess.CalledProcessError as e:
        warn('assume-role for profile', profile, 'failed')
        warn(e.stderr.decode('utf-8'))
        sys.exit(1)

    response = json.loads(p.stdout)
    msg(profile, ': running', cmd)

    p = subprocess.run(cmd, env={
        **os.environ,
        'AWS_ACCESS_KEY_ID': response['Credentials']['AccessKeyId'],
        'AWS_SECRET_ACCESS_KEY': response['Credentials']['SecretAccessKey'],
        'AWS_SESSION_TOKEN': response['Credentials']['SessionToken'],
        'AWS_SESSION_EXPIRATION': response['Credentials']['Expiration'],
        'AWS_PROFILE': profile,
        'AWS_ASSUMED_ROLE_ARN': response['AssumedRoleUser']['Arn'],
    })

    sys.exit(p.returncode)

if __name__ == '__main__':
    colorama.init()

    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2:])

    else:
        main(sys.argv[1])
