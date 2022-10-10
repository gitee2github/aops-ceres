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
import os
import re
from typing import List

from flask import Response, jsonify

from ceres.conf.constant import (
    INSTALLABLE_PLUGIN,
    INFORMATION_ABOUT_RPM_SERVICE,
    SCANNED_APPLICATION,
    PLUGIN_WITH_CLASS,
    HOST_COLLECT_INFO_SUPPORT
)
from ceres.function.status import StatusCode, PARAM_ERROR, SUCCESS
from ceres.manages import plugin_manage
from ceres.manages.collect_manage import Collect
from ceres.manages.token_manage import TokenManage
from ceres.manages.resource_manage import Resource
from ceres.function.util import plugin_status_judge, validate_data
from ceres.function.schema import STRING_ARRAY


@TokenManage.validate_token
def get_host_info(info_type: List[str]) -> Response:
    """
    get basic info about machine

    Args:
        info_type(list): e.g [mem,os,cpu,disk]
    Returns:
        Response: e.g
            {
                "code": int,
                "msg" : "xxx",
                "resp":{
                    "os":{
                        'os_version': os_version,
                        'bios_version': bios_version,
                        'kernel': kernel_version
                        },
                    "cpu":{
                        "architecture": string,
                        "core_count": string,
                        "model_name": string,
                        "vendor_id": string,
                        "l1d_cache": string,
                        "l1i_cache": string,
                        "l2_cache": string,
                        "l3_cache": string
                        },
                    "memory":{
                        "size": "xx GB",
                        "total": int,
                        "info": [
                            {
                                "size": "xx GB",
                                "type": "DDR4",
                                "speed": "xxxx MT/s",
                                "manufacturer": "string"
                            }
                            ...
                            ]
                        }
                    "disk":[
                                {
                                    "capacity": xx GB
                                    "model": "string",
                            }
                        ]
                    }
            }
    """

    if len(info_type) == 0:
        return jsonify(StatusCode.make_response_body(
            (SUCCESS, Collect().get_host_info(HOST_COLLECT_INFO_SUPPORT))))
    count = len(set(info_type).union(set(HOST_COLLECT_INFO_SUPPORT)))
    if count > len(HOST_COLLECT_INFO_SUPPORT):
        return jsonify(StatusCode.make_response_body(PARAM_ERROR))
    return jsonify(StatusCode.make_response_body((SUCCESS, Collect().get_host_info(info_type))))


@TokenManage.validate_token
def ceres_plugin_info() -> Response:
    """
    get all info about ceres

    Returns:
        Response:
            a list which contains cpu,memory,collect items of plugin,running status and so on.for
        example
            {
                code:   int,
                msg:    string
                resp:[{
                        "plugin_name": "string",
                        "is_installed": true,
                        "status": "string",
                        "collect_items": [{
                            "probe_name": "string",
                            "probe_status": "string"} ],
                        "resource": [{
                        "name": "string",
                        "limit_value": "string",
                        "current_value": "string}]}]
            }
    """
    plugin_list = INSTALLABLE_PLUGIN
    if len(plugin_list) == 0:
        return jsonify(StatusCode.make_response_body((SUCCESS, {'resp': []})))

    res = []
    for plugin_name in plugin_list:
        plugin_running_info = {
            'plugin_name': plugin_name,
            'collect_items': [],
            'status': None,
            'resource': []
        }

        if not plugin_status_judge(plugin_name):
            plugin_running_info['is_installed'] = False
            res.append(plugin_running_info)
            continue
        plugin_running_info['is_installed'] = True

        service_name = INFORMATION_ABOUT_RPM_SERVICE.get(plugin_name).get('service_name')
        plugin = plugin_manage.Plugin(service_name)

        status = plugin.get_plugin_status()
        if status == 'active':
            pid = plugin_manage.Plugin.get_pid(service_name)
            cpu_current = Resource.get_current_cpu(service_name, pid)
            memory_current = Resource.get_current_memory(pid)
        else:
            cpu_current = None
            memory_current = None
        cpu_limit = Resource.get_cpu_limit(service_name)
        memory_limit = Resource.get_memory_limit(service_name)

        collect_items_status = []
        plugin_class_name = PLUGIN_WITH_CLASS.get(plugin_name, '')
        if hasattr(plugin_manage, plugin_class_name):
            plugin_obj = getattr(plugin_manage, plugin_class_name)
            if hasattr(plugin_obj, 'get_collect_items'):
                collect_items_status = plugin_obj.get_collect_status()

        resource = []
        cpu = {}
        cpu['name'] = 'cpu'
        cpu['current_value'] = cpu_current
        cpu['limit_value'] = cpu_limit
        memory = {}
        memory['name'] = 'memory'
        memory['current_value'] = memory_current
        memory['limit_value'] = memory_limit
        resource.append(cpu)
        resource.append(memory)
        plugin_running_info['status'] = status
        plugin_running_info['collect_items'] = collect_items_status
        plugin_running_info['resource'] = resource
        res.append(plugin_running_info)
    return jsonify(StatusCode.make_response_body((SUCCESS, {'resp': res})))


@TokenManage.validate_token
def get_application_info() -> Response:
    """
        get the running applications in the target list

    Returns:
       Response:
            List[str]:applications which is running
    """
    target_applications = SCANNED_APPLICATION
    res = {
        "resp": {
            "running": []
        }
    }
    for application_name in target_applications:
        status_info = plugin_status_judge(application_name)
        if status_info != '':
            status = re.search(r':.+\(', status_info).group()[1:-1].strip()
            if status == 'active':
                res['resp']['running'].append(application_name)
    return jsonify(StatusCode.make_response_body((SUCCESS, res)))


@TokenManage.validate_token
def collect_file(config_path_list: List[str]) -> Response:
    """
        Get configuration file content

    Args:
        config_path_list(List[str]): It contains some file path

    Returns:
        Response:  {
                "success_files": [],
                "fail_files": [],
                "infos": [
                        {   path: file_path,
                            file_attr: {
                            mode:  0755,
                            owner: owner,
                            group: group
                            },
                            content: content
                            }
                        ]
                }

    """
    if not validate_data(config_path_list, STRING_ARRAY):
        return jsonify(StatusCode.make_response_body(PARAM_ERROR))

    result = {
        "success_files": [],
        "fail_files": [],
        "infos": [
        ]
    }

    for file_path in config_path_list:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            result['fail_files'].append(file_path)
            continue

        info = Collect.get_file_info(file_path)
        if not info:
            result['fail_files'].append(file_path)
            continue
        result['success_files'].append(file_path)
        result['infos'].append(info)
    return jsonify(result)
