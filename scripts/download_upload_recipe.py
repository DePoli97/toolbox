#!/usr/bin/env python3

##################################################
__NAME__ = f'Delvitech Recipe Conveyor'
__DESCRIPTION__ = 'lightweight utility to download, upload, and export in JSON format Neith Recipes.'
__VERSION_ = 'v1.0.4'
__AUTHOR__ = 'Matteo Riva'
##################################################
## Usage: call this script from terminal, read tutorial by calling it with the --help flag.
##################################################

import os
import json
import argparse

import requests

##################################################
############## MUTABLE PARAMETERS ################
##################################################

PROTO_SCHEME = 'http://'
PORT = 3000

##################################################
################## UTIL FUNCS ####################
##################################################

def login(ip, user, password, verbose):
    auth_dict = {"username": user, "password": password}

    r_login = requests.post(f'{PROTO_SCHEME}{ip}:{PORT}/v1/auth/login', json=auth_dict)
    login_token = r_login.json()['access_token']

    if verbose:
        print(f'ACCESS_TOKEN for {ip}: {login_token}')

    return login_token

def sanitize_path(path):
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    return path

def check_response(response):
    is_good_response = 'pcba_descriptor' in response
    if is_good_response:
        print(f'done :)')
    else:
        print('failed :(')

    return is_good_response

##################################################

def delete_recipe_from_ip(ip, token, recipe_id):
    print(f'Deleting Recipe from {ip}... ', end='', flush=True)

    auth_header = {'Cookie': f'access_token={token}'}
    r_delete_recipe = requests.delete(url=f'{PROTO_SCHEME}{ip}:{PORT}/v1/recipe/{recipe_id}',
                                      headers=auth_header)

    if r_delete_recipe.ok:
        print(f'done :)')
    else:
        print('failed :(')
        print(f'Something went wrong, target ({ip}) response:\n{r_delete_recipe}')

def get_recipe_from_ip(ip, token, recipe_id, recipe_ver):
    print(f'Downloading Recipe from {ip}... ', end='', flush=True)

    auth_header = {'Cookie': f'access_token={token}'}
    r_get_recipe = requests.get(url=f'{PROTO_SCHEME}{ip}:{PORT}/v1/recipe/{recipe_id}/{recipe_ver}',
                                headers=auth_header)

    r_get_recipe.encoding = r_get_recipe.apparent_encoding
    response = r_get_recipe.json()

    if not check_response(response):
        print(f'Something went wrong, target ({ip}) response:\n{response}')

    return response

def get_recipe_from_path(path):
    path = sanitize_path(path)
    with open(path, 'r') as infile:
        recipe = json.load(infile)
    return recipe

##################################################

def save_recipe_to_ip(ip, token, recipe):
    print(f'Uploading recipe to {ip}... ', end='', flush=True)

    auth_header = {'Cookie': f'access_token={token}'}
    r_save_recipe = requests.post(url=f'{PROTO_SCHEME}{ip}:{PORT}/v1/recipe/',
                                  headers=auth_header,
                                  json=recipe)
    r_save_recipe.encoding = r_save_recipe.apparent_encoding
    response = r_save_recipe.json()

    if check_response(response):
        print(f"New RecipeID: {response['pcba_descriptor']['id']}, Version: {response['pcba_descriptor']['version']}, Name: {response['pcba_descriptor']['recipe_name']}")
    else:
        print(f'Something went wrong, target ({ip}) response:\n{response}')

def save_recipe_to_path(path, recipe):
    recipe_id = recipe['pcba_descriptor']['id']
    recipe_ver = recipe['pcba_descriptor']['version']

    path = os.path.join(path, f'recipe_id{recipe_id}_v{recipe_ver}.json')
    path = sanitize_path(path)

    print(f'Saving Recipe to "{path}"... ', end='', flush=True)
    try:
        with open(path, 'w') as outfile:
            json.dump(recipe, outfile, indent=2)
        print(f'done :)')
    except Exception as e:
        print(f'failed :(\n{e}')

##################################################

def rename_recipe(recipe, new_name):
    new_name = new_name.replace('~name~', recipe['pcba_descriptor']['recipe_name'])
    recipe['pcba_descriptor']['recipe_name'] = new_name
    return recipe

##################################################

def main(args):
    # Retrieve Recipe from path/IP
    if args.from_path is not None:
        recipe = get_recipe_from_path(path=args.from_path)
    else:
        usr, pwd = args.credentials.split(':')
        src_login_token = login(ip=args.from_ip,
                                user=usr,
                                password=pwd,
                                verbose=args.verbose)

        recipe = get_recipe_from_ip(ip=args.from_ip,
                                    token=src_login_token,
                                    recipe_id=args.id,
                                    recipe_ver=args.version)

        # Optionally remove Recipe ID (all versions)
        if args.delete_origin:
            delete_recipe_from_ip(ip=args.from_ip,
                                  token=src_login_token,
                                  recipe_id=args.id)

    # Optionally change Recipe name
    if args.rename is not None:
        recipe = rename_recipe(recipe=recipe,
                               new_name=args.rename)

    # Save Recipe to path
    if args.to_path is not None:
        save_recipe_to_path(path=args.to_path,
                            recipe=recipe)

    # Save Recipe to IP
    if args.to_ip is not None:
        if args.from_ip == args.to_ip:
            trg_login_token = src_login_token
        else:
            usr, pwd = args.credentials.split(':')
            trg_login_token = login(ip=args.to_ip,
                                    user=usr,
                                    password=pwd,
                                    verbose=args.verbose)

        save_recipe_to_ip(ip=args.to_ip,
                          token=trg_login_token,
                          recipe=recipe)

if __name__ == '__main__':
    class SaneFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter): pass
    parser = argparse.ArgumentParser(prog=__NAME__,
                                     usage='download_upload_recipe.py [-h] [--credentials CREDENTIALS] (--from-path FROM_PATH | --from-ip FROM_IP --id ID [--version VERSION] [--delete-origin]) [--rename NEW_NAME] [--to-path TO_PATH] [--to-ip TO_IP] [--verbose]',
                                     description=f'{__NAME__} ({__VERSION_}), maintained by {__AUTHOR__}.\n{__DESCRIPTION__}',
                                     epilog='example usage:\ndownload_upload_recipe.py --id=42\n\t\t\t  --from-ip=172.16.14.14\n\t\t\t  --to-ip=172.16.14.12\n\t\t\t  --to-path=/home/delvitech/recipes/\n ',
                                     formatter_class=SaneFormatter)

    # Add script arguments
    parser.add_argument('--id',
                        help="Recipe ID to be retrieved. Use only with --from-ip argument.",
                        type=int)
    parser.add_argument('--version',
                        type=int,
                        help="Recipe version to be retrieved. Use only with --from-ip argument.",
                        default=1)
    parser.add_argument('--rename',
                        help="new name for retrieved Recipe. You can use '~name~' to get the current Recipe name. Use format 'user/recipe_name' to store it in a folder in Neith.",)

    in_recipe = parser.add_mutually_exclusive_group(required=True)
    in_recipe.add_argument('--from-path',
                           help="file path to retrieve the Recipe from.")

    in_recipe.add_argument('--from-ip',
                           help="IP address to retrieve the Recipe from. Must specify ID and VERSION.")

    parser.add_argument('--to-path',
                           help="folder path to save the retrieved Recipe at.")
    parser.add_argument('--to-ip',
                        help="IP address to send the retrieved Recipe to.")

    parser.add_argument('--credentials',
                        default='admin:password',
                        help="user and password to login in Neith. Must have the format 'user:password'.")

    parser.add_argument('--verbose',
                        action='store_true',
                        default=False,
                        help="show access tokens for IP connections.")

    parser.add_argument('--delete-origin',
                        action='store_true',
                        default=False,
                        help="delete all versions of specified Recipe ID from FROM_IP.")

    # Parse arguments and check compatibility
    args = parser.parse_args()

    if args.from_ip is not None and args.id is None:
        parser.error("--from-ip requires --id")

    if args.delete_origin and args.from_ip is None:
        parser.error("--delete-origin requires --from-ip")

    main(args)

