#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2022-2022. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN 'AS IS' BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
from json import encoder
from typing import NoReturn
import argparse

import connexion
from ceres.conf import configuration
from ceres.conf.constant import REGISTER_HELP_INFO, CERES_CONFIG_PATH
from ceres.function.status import SUCCESS
from ceres.function.util import (
    get_dict_from_file,
    update_ini_data_value
)
from ceres.function.register import register_info_to_dict, register


def start(*args) -> NoReturn:
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'ceres'}, pythonic_params=True)
    app.run(host=configuration.ceres.get("IP"), port=configuration.ceres.get('PORT'))


def register_on_manager(args: argparse.Namespace) -> NoReturn:
    """
    get args from command-line and register on manager

    Args:
        args(argparse.Namespace): args parser

    Returns:
        dict: token or error message
    """
    if args.data:
        register_info = register_info_to_dict(args.data)
    else:
        register_info = get_dict_from_file(args.path)
    if register_info.get('ceres_host') is not None:
        update_ini_data_value(CERES_CONFIG_PATH,
                              'ceres', 'port', register_info.get('ceres_host'))
    if register(register_info) == SUCCESS:
        print('Register Success')
    else:
        print('Register Fail')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--Help', action='store_true',
                        help='more info about register')

    subparsers = parser.add_subparsers()
    subparse_start = subparsers.add_parser('start', help='start plugin')
    subparse_start.set_defaults(function=start)

    subparse_register = subparsers.add_parser('register',
                                              help='to register in manager')
    group = subparse_register.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--path', type=str,
                       help="file contains data which register need")
    group.add_argument('-d', '--data', type=str,
                       help="json data which register need")
    subparse_register.set_defaults(function=register_on_manager)

    args = parser.parse_args()
    if args.Help:
        print(REGISTER_HELP_INFO)
    else:
        try:
            args.function(args)
        except AttributeError:
            print('error: you can get help for -h')


if __name__ == '__main__':
    main()
