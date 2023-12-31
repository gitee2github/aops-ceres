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
import configparser
import subprocess
import unittest
from unittest import mock

from libconf import AttrDict

from ceres.conf.constant import CommandExitCode
from ceres.function.status import SUCCESS, FAIL
from ceres.manages.plugin_manage import Plugin, GalaGopher

target_probes = (
    AttrDict([('name', 'test_no_check_1'), ('command', 'test'), ('param', ''), ('switch', 'on')]),
    AttrDict([('name', 'test_no_check_2'), ('command', ''), ('param', ''), ('switch', 'off')]),
    AttrDict(
        [
            ('name', 'test_with_check_1'),
            ('command', ''),
            ('param', ''),
            ('start_check', ''),
            ('check_type', 'count'),
            ('switch', 'on'),
        ]
    ),
    AttrDict(
        [
            ('name', 'test_with_check_2'),
            ('command', ''),
            ('param', ''),
            ('start_check', ''),
            ('check_type', 'count'),
            ('switch', 'off'),
        ]
    ),
    AttrDict(
        [
            ('name', 'test_with_check_3'),
            ('command', ''),
            ('param', ''),
            ('start_check', ''),
            ('check_type', 'count'),
            ('switch', 'auto'),
        ]
    ),
    AttrDict(
        [
            ('name', 'test_with_check_4'),
            ('command', ''),
            ('param', ''),
            ('start_check', ''),
            ('check_type', 'count'),
            ('switch', 'auto'),
        ]
    ),
)


class TestPluginManage(unittest.TestCase):
    @mock.patch('ceres.manages.plugin_manage.execute_shell_command')
    @mock.patch.object(Plugin, 'get_plugin_status')
    def test_start_service_should_return_success_when_plugin_is_already_running(
        self, mock_plugin_status, mock_execute_shell_command
    ):
        mock_plugin_status.return_value = "running"
        mock_execute_shell_command.return_value = CommandExitCode.SUCCEED, "", ""
        self.assertEqual(SUCCESS, Plugin('test').start_service())

    @mock.patch('ceres.manages.plugin_manage.execute_shell_command')
    @mock.patch.object(Plugin, 'get_plugin_status')
    def test_start_service_should_return_success_when_make_plugin_running_successful(
        self, mock_plugin_status, mock_execute_shell_command
    ):
        mock_plugin_status.return_value = "active"
        mock_execute_shell_command.return_value = CommandExitCode.SUCCEED, "", ""
        self.assertEqual(SUCCESS, Plugin('test').start_service())

    @mock.patch('ceres.manages.plugin_manage.execute_shell_command')
    @mock.patch.object(Plugin, 'get_plugin_status')
    def test_start_service_should_return_fail_when_execute_shell_command_failed(
        self, mock_plugin_status, mock_execute_shell_command
    ):
        mock_plugin_status.return_value = "active"
        mock_execute_shell_command.return_value = CommandExitCode.FAIL, "", ""
        self.assertEqual(FAIL, Plugin('test').start_service())

    @mock.patch('ceres.manages.plugin_manage.execute_shell_command')
    def test_get_plugin_status_should_return_plugin_status_when_execute_shell_command_successful(
        self, mock_execute_shell_command
    ):
        mock_shell_stdout = " Active: failed (Result: exit-code) since Mon 2023-07-03 15:57:07 CST; 24h ago"
        mock_execute_shell_command.return_value = CommandExitCode.SUCCEED, mock_shell_stdout, ""
        self.assertEqual("failed", Plugin('test').get_plugin_status())

    @mock.patch('ceres.manages.plugin_manage.execute_shell_command')
    def test_get_plugin_status_should_return_empty_string_when_execute_shell_command_failed(
        self, mock_execute_shell_command
    ):
        mock_execute_shell_command.return_value = CommandExitCode.FAIL, "", ""
        self.assertEqual("", Plugin('test').get_plugin_status())

    @mock.patch.object(Plugin, 'get_plugin_status')
    def test_stop_service_should_return_success_when_plugin_is_already_stopping(self, mock_plugin_status):
        mock_plugin_status.return_value = "inactive"
        res = Plugin('test').stop_service()
        self.assertEqual(SUCCESS, res)

    @mock.patch('ceres.manages.plugin_manage.execute_shell_command')
    @mock.patch.object(Plugin, 'get_plugin_status')
    def test_stop_service_should_return_success_when_execute_shell_command_successful(
        self, mock_plugin_status, mock_execute_shell_command
    ):
        mock_plugin_status.return_value = "running"
        mock_execute_shell_command.return_value = CommandExitCode.SUCCEED, "", ""
        res = Plugin('test').stop_service()
        self.assertEqual(SUCCESS, res)

    def test_change_probe_status_should_return_success_list_and_empty_failure_list_when_input_all_right(self):
        probe_status = {
            'test_no_check_1': 'off',
            "test_no_check_2": "on",
            "test_with_check_1": "auto",
            "test_with_check_2": "auto",
            "test_with_check_3": "on",
            "test_with_check_4": "off",
        }
        res, fail_list = GalaGopher()._GalaGopher__change_probe_status(target_probes, probe_status, {'success': []})
        expect_success_res = list(probe_status.keys())
        self.assertEqual((expect_success_res, {}), (res['success'], fail_list))

    def test_change_probe_status_should_return_success_list_and_failure_list_when_part_of_input_probe_name_is_not_in_target_probes(
        self,
    ):
        probe_status = {
            'test_no_check_1': 'off',
            "test_no_check_3": "on",
            "test_with_check_1": "auto",
            "test_with_check_2": "auto",
            "test_with_check_3": "on",
            "test_with_check_5": "off",
        }
        res, fail_list = GalaGopher()._GalaGopher__change_probe_status(target_probes, probe_status, {'success': []})
        expect_success_res = ['test_no_check_1', 'test_with_check_1', 'test_with_check_2', 'test_with_check_3']
        expect_fail_res = {"test_no_check_3": "on", "test_with_check_5": "off"}
        self.assertEqual((expect_success_res, expect_fail_res), (res['success'], fail_list))

    def test_change_probe_status_should_return_failure_list_when_input_probe_name_is_not_support_auto(self):
        probe_status = {'test_no_check_1': 'auto', "test_no_check_2": "auto"}
        res, fail_list = GalaGopher()._GalaGopher__change_probe_status(target_probes, probe_status, {'success': []})
        expect_fail_res = {"test_no_check_1": "auto", "test_no_check_2": "auto"}
        self.assertEqual(expect_fail_res, fail_list)

    @mock.patch('builtins.open', mock.mock_open())
    @mock.patch.object(GalaGopher, "_GalaGopher__change_probe_status")
    @mock.patch("ceres.manages.plugin_manage.load_gopher_config")
    @mock.patch("ceres.conf.configuration")
    def test_change_items_status_should_return_fail_list_is_empty_when_all_input_is_correct(
        self, mock_configuration, mock_gopher_config, mock_gopher_change_probe
    ):
        mock_input = {"mock_probe1": "on", "mock_probe2": "off", "mock_probe3": "auto"}
        mock_configuration.return_value = configparser.RawConfigParser()
        mock_gopher_config.return_value = AttrDict([('test', 'test')])
        mock_gopher_config.get.side_effect = [AttrDict(), AttrDict()]
        mock_gopher_change_probe.return_value = ({'success': ['mock_probe1', "mock_probe2", 'mock_probe3']}, {})
        res = GalaGopher().change_items_status(mock_input)
        self.assertEqual([], res.get("failure"))

    @mock.patch("ceres.manages.plugin_manage.load_gopher_config")
    def test_change_items_status_should_return_all_probes_change_failed_when_gopher_config_is_null(
        self, mock_gopher_config
    ):
        mock_input = {"mock_probe1": "on", "mock_probe2": "off", "mock_probe3": "auto"}
        mock_gopher_config.return_value = AttrDict()

        res = GalaGopher().change_items_status(mock_input)
        self.assertEqual(['mock_probe1', 'mock_probe2', 'mock_probe3'], res.get("failure"))

    @mock.patch('builtins.open', mock.mock_open())
    @mock.patch.object(GalaGopher, "_GalaGopher__change_probe_status")
    @mock.patch("ceres.manages.plugin_manage.load_gopher_config")
    @mock.patch("ceres.conf.configuration")
    def test_change_items_status_should_return_succeed_and_fail_list_when_part_of_input_probe_is_incorrect_or_input_probe_is_not_support_auto(
        self, mock_configuration, mock_gopher_config, mock_gopher_change_probe
    ):
        mock_input = {"mock_probe1": "on", "mock_probe2": "off", "mock_incorrect_probe": "auto"}
        mock_configuration.return_value = configparser.RawConfigParser()
        mock_gopher_config.return_value = AttrDict([('test', 'test')])
        mock_gopher_config.get.side_effect = [AttrDict(), AttrDict()]
        mock_gopher_change_probe.return_value = (
            {'success': ['mock_probe1', "mock_probe2"]},
            {"mock_incorrect_probe": "auto"},
        )
        res = GalaGopher().change_items_status(mock_input)
        self.assertEqual(["mock_incorrect_probe"], res.get("failure"))

    @mock.patch('builtins.open', mock.mock_open())
    @mock.patch.object(GalaGopher, "_GalaGopher__change_probe_status")
    @mock.patch("ceres.manages.plugin_manage.load_gopher_config")
    @mock.patch("ceres.conf.configuration")
    def test_change_items_status_should_return_fail_list_when_all_input_probe_is_incorrect_or_not_support_auto(
        self, mock_configuration, mock_gopher_config, mock_gopher_change_probe
    ):
        mock_input = {"mock_probe1": "on", "mock_probe2": "off", "mock_probe3": "auto"}
        mock_configuration.return_value = configparser.RawConfigParser()
        mock_gopher_config.return_value = AttrDict([('test', 'test')])
        mock_gopher_config.get.side_effect = [AttrDict(), AttrDict()]
        mock_gopher_change_probe.return_value = ({'success': []}, mock_input)
        res = GalaGopher().change_items_status(mock_input)
        self.assertEqual(list(mock_input.keys()), res.get("failure"))

    @mock.patch("ceres.manages.plugin_manage.load_gopher_config")
    def test_get_collect_status_should_return_collect_items_and_its_status_when_load_gopher_config_is_succeed(
        self, mock_gopher_config
    ):
        mock_gopher_cfg = AttrDict(
            [
                (
                    'probes',
                    (
                        AttrDict([('name', 'probe1'), ('switch', 'on')]),
                        AttrDict([('name', 'probe2'), ('switch', 'off')]),
                    ),
                ),
                (
                    'extend_probes',
                    (
                        AttrDict([('name', 'probe3'), ('switch', 'off')]),
                        AttrDict([('name', 'probe4'), ('start_check', 'mock'), ('switch', 'auto')]),
                    ),
                ),
            ]
        )
        expect_res = [
            {'probe_name': 'probe1', 'probe_status': 'on', 'support_auto': False},
            {'probe_name': 'probe2', 'probe_status': 'off', 'support_auto': False},
            {'probe_name': 'probe3', 'probe_status': 'off', 'support_auto': False},
            {'probe_name': 'probe4', 'probe_status': 'auto', 'support_auto': True},
        ]
        mock_gopher_config.return_value = mock_gopher_cfg
        res = GalaGopher.get_collect_status()
        self.assertEqual(expect_res, res)

    @mock.patch("ceres.manages.plugin_manage.load_gopher_config")
    def test_get_collect_status_should_return_empty_list_when_load_gopher_config_is_failed(self, mock_gopher_config):
        mock_gopher_config.return_value = AttrDict()
        res = GalaGopher.get_collect_status()
        self.assertEqual([], res)

    @mock.patch("ceres.manages.plugin_manage.plugin_status_judge")
    @mock.patch("ceres.manages.plugin_manage.INSTALLABLE_PLUGIN", ["mock1", "mock2"])
    def test_get_installed_plugin_should_return_installed_plugin_list_when_part_plugin_is_installed_which_plugin_in_installable_plugin(
        self, mock_judge_res
    ):
        mock_judge_res.side_effect = [True, False]
        res = Plugin.get_installed_plugin()
        self.assertEqual(["mock1"], res)

    @mock.patch("ceres.manages.plugin_manage.plugin_status_judge")
    @mock.patch("ceres.manages.plugin_manage.INSTALLABLE_PLUGIN", [])
    def test_get_installed_plugin_should_return_empty_list_when_installable_plugin_is_null(self, mock_judge_res):
        mock_judge_res.return_value = True
        res = Plugin.get_installed_plugin()
        self.assertEqual([], res)

    @mock.patch("ceres.manages.plugin_manage.plugin_status_judge")
    @mock.patch("ceres.manages.plugin_manage.INSTALLABLE_PLUGIN", ['mock1', 'mock2'])
    def test_get_installed_plugin_should_return_empty_list_when_plugin_is_not_installed_which_plugin_in_installable_plugin(
        self, mock_judge_res
    ):
        mock_judge_res.return_value = False
        res = Plugin.get_installed_plugin()
        self.assertEqual([], res)

    @mock.patch('ceres.manages.plugin_manage.execute_shell_command')
    def test_get_pid_should_return_pid_string_when_all_is_right(self, mock_execute_shell_command):
        mock_execute_shell_command.return_value = CommandExitCode.SUCCEED, 'Main PID: 749', ""
        res = Plugin.get_pid('')
        self.assertEqual('749', res)

    @mock.patch('ceres.manages.plugin_manage.execute_shell_command')
    def test_get_pid_should_return_empty_string_when_command_execution_failed(self, mock_execute_shell_command):
        mock_execute_shell_command.return_value = CommandExitCode.FAIL, "", ""
        res = Plugin.get_pid('')
        self.assertEqual('', res)

    @mock.patch('ceres.manages.plugin_manage.load_gopher_config')
    def test_get_collect_items_should_return_empty_set_when_gopher_config_is_empty(self, mock_gopher_config):
        mock_gopher_config.return_value = AttrDict()
        res = GalaGopher.get_collect_items()
        self.assertEqual(set(), res)

    @mock.patch('ceres.manages.plugin_manage.load_gopher_config')
    def test_get_collect_items_should_return_collect_items_when_load_gopher_config_succeed(self, mock_gopher_config):
        mock_gopher_config.return_value = AttrDict(
            [
                (
                    'probes',
                    (
                        AttrDict([('name', 'probe1'), ('switch', 'on')]),
                        AttrDict([('name', 'probe2'), ('switch', 'off')]),
                    ),
                ),
                (
                    'extend_probes',
                    (
                        AttrDict([('name', 'probe3'), ('switch', 'off')]),
                        AttrDict([('name', 'probe4'), ('start_check', 'mock'), ('switch', 'auto')]),
                    ),
                ),
            ]
        )
        res = GalaGopher.get_collect_items()
        expect_res = {'probe1', 'probe2', 'probe3', 'probe4'}
        self.assertEqual(expect_res, res)

    @mock.patch('ceres.manages.plugin_manage.load_gopher_config')
    def test_get_collect_items_should_return_empty_set_when_load_gopher_config_failed(self, mock_gopher_config):
        mock_gopher_config.return_value = AttrDict(
            [
                (
                    'probes',
                    (
                        AttrDict([('name', 'probe1'), ('switch', 'on')]),
                        AttrDict([('name', 'probe2'), ('switch', 'off')]),
                    ),
                ),
                (
                    'extend_probes',
                    (
                        AttrDict([('name', 'probe3'), ('switch', 'off')]),
                        AttrDict([('name', 'probe4'), ('switch', 'auto')]),
                    ),
                ),
            ]
        )
        res = GalaGopher.get_collect_items()
        expect_res = {'probe1', 'probe2', 'probe3', 'probe4'}
        self.assertEqual(expect_res, res)
