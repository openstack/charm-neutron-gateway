from unittest.mock import MagicMock, call, patch, ANY

import charmhelpers.core.hookenv as hookenv
import neutron_utils
try:
    import neutronclient
except ImportError:
    neutronclient = None

from test_utils import (
    CharmTestCase
)

TO_PATCH = [
    'config',
    'get_os_codename_install_source',
    'apt_update',
    'apt_upgrade',
    'apt_install',
    'apt_autoremove',
    'apt_purge',
    'filter_missing_packages',
    'configure_installation_source',
    'log',
    'add_bridge',
    'add_bridge_port',
    'add_ovsbridge_linuxbridge',
    'get_bridges_and_ports_map',
    'is_linuxbridge_interface',
    'headers_package',
    'full_restart',
    'os_release',
    'service_running',
    'NetworkServiceContext',
    'ExternalPortContext',
    'service_stop',
    'determine_dkms_package',
    'service_restart',
    'is_relation_made',
    'lsb_release',
    'mkdir',
    'copy2',
    'init_is_systemd',
    'os_application_version_set',
    'NeutronAPIContext',
    'enable_ipfix',
    'disable_ipfix',
    'disable_neutron_lbaas',
]


class TestNeutronUtils(CharmTestCase):

    def setUp(self):
        super(TestNeutronUtils, self).setUp(neutron_utils, TO_PATCH)
        self.headers_package.return_value = 'linux-headers-2.6.18'
        self._set_distrib_codename('trusty')
        self.maxDiff = None

    def tearDown(self):
        super(TestNeutronUtils, self).tearDown()
        # Reset cached cache
        hookenv.cache = {}

    def _set_distrib_codename(self, newcodename):
        self.lsb_release.return_value = {'DISTRIB_CODENAME': newcodename}

    def test_valid_plugin(self):
        self.config.return_value = 'ovs'
        self.assertTrue(neutron_utils.valid_plugin())
        self.config.return_value = 'nsx'
        self.assertTrue(neutron_utils.valid_plugin())

    def test_invalid_plugin(self):
        self.config.return_value = 'invalid'
        self.assertFalse(neutron_utils.valid_plugin())

    def test_get_early_packages_ovs(self):
        self.config.return_value = 'ovs'
        self.determine_dkms_package.return_value = [
            'openvswitch-datapath-dkms']
        self.assertEqual(
            neutron_utils.get_early_packages(),
            ['openvswitch-datapath-dkms', 'linux-headers-2.6.18'])

    def test_get_early_packages_nsx(self):
        self.config.return_value = 'nsx'
        self.assertEqual(
            neutron_utils.get_early_packages(),
            [])

    def test_get_early_packages_empty(self):
        self.config.return_value = 'noop'
        self.assertEqual(neutron_utils.get_early_packages(),
                         [])

    def test_get_packages_ovs_icehouse(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'icehouse'
        self.assertTrue('neutron-vpn-agent' in neutron_utils.get_packages())
        self.assertFalse('neutron-l3-agent' in neutron_utils.get_packages())

    def test_get_packages_ovs_juno_utopic(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'juno'
        self._set_distrib_codename('utopic')
        self.assertFalse('neutron-vpn-agent' in neutron_utils.get_packages())
        self.assertTrue('neutron-l3-agent' in neutron_utils.get_packages())

    def test_get_packages_ovs_juno_trusty(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'juno'
        self.assertTrue('neutron-vpn-agent' in neutron_utils.get_packages())
        self.assertFalse('neutron-l3-agent' in neutron_utils.get_packages())

    def test_get_packages_ovs_kilo(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'kilo'
        self.assertTrue('python-neutron-fwaas' in neutron_utils.get_packages())

    def test_get_packages_ovs_liberty(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'liberty'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertFalse('python-mysqldb' in packages)
        self.assertTrue('python-pymysql' in packages)

    def test_get_packages_ovs_mitaka(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'mitaka'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertTrue('neutron-openvswitch-agent' in packages)
        self.assertFalse('neutron-plugin-openvswitch-agent' in packages)
        self.assertFalse('python-mysqldb' in packages)
        self.assertTrue('python-pymysql' in packages)

    def test_get_packages_ovs_newton(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.disable_neutron_lbaas.return_value = False
        self.os_release.return_value = 'newton'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertTrue('neutron-openvswitch-agent' in packages)
        self.assertFalse('neutron-plugin-openvswitch-agent' in packages)
        self.assertFalse('neutron-lbaas-agent' in packages)
        self.assertFalse('python-mysqldb' in packages)
        self.assertTrue('python-pymysql' in packages)

    def test_get_packages_ovs_rocky(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=True)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'rocky'
        packages = neutron_utils.get_packages()
        self.assertEqual(
            len(packages),
            len([p for p in packages if not p.startswith('python-')])
        )
        self.assertTrue('python3-neutron-lbaas' in packages)

    def test_get_packages_ovs_train(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=True)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'train'
        packages = neutron_utils.get_packages()
        self.assertEqual(
            len(packages),
            len([p for p in packages if not p.startswith('python-')])
        )
        self.assertFalse('python3-neutron-lbaas' in packages)
        self.assertFalse('neutron-lbaasv2-agent' in packages)

    def test_get_purge_packages_ovs(self):
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'queens'
        self.assertEqual([], neutron_utils.get_purge_packages())

    def test_get_purge_packages_ovs_rocky(self):
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'rocky'
        self.assertEqual([
            'python-mysqldb',
            'python-psycopg2',
            'python-oslo.config',
            'python-nova',
            'python-neutron',
            'python-neutron-fwaas',
            'python-neutron-lbaas'],
            neutron_utils.get_purge_packages()
        )

    def test_get_purge_packages_ovs_train(self):
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'train'
        self.assertEqual([
            'python-mysqldb',
            'python-psycopg2',
            'python-oslo.config',
            'python-nova',
            'python-neutron',
            'python-neutron-fwaas',
            'python-neutron-lbaas',
            'python3-neutron-lbaas',
            'neutron-lbaasv2-agent'],
            neutron_utils.get_purge_packages()
        )

    def test_get_purge_packages_nsx_train(self):
        self.config.return_value = 'nsx'
        self.os_release.return_value = 'train'
        self.assertEqual([
            'python-mysqldb',
            'python-psycopg2',
            'python-oslo.config',
            'python-nova',
            'python-neutron',
            'python-neutron-fwaas',
            'python-neutron-lbaas',
            'python3-neutron-lbaas'],
            neutron_utils.get_purge_packages()
        )

    def test_get_packages_ovsodl_icehouse(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs-odl'
        self.disable_neutron_lbaas.return_value = False
        self.os_release.return_value = 'icehouse'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertFalse('neutron-plugin-openvswitch-agent' in packages)
        self.assertFalse('neutron-openvswitch-agent' in packages)
        self.assertTrue('neutron-lbaas-agent' in packages)

    def test_get_packages_ovsodl_newton(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs-odl'
        self.disable_neutron_lbaas.return_value = False
        self.os_release.return_value = 'newton'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertFalse('neutron-plugin-openvswitch-agent' in packages)
        self.assertFalse('neutron-openvswitch-agent' in packages)
        self.assertFalse('neutron-lbaas-agent' in packages)
        self.assertTrue('neutron-lbaasv2-agent' in packages)

    def test_get_packages_l3ha(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.get_os_codename_install_source.return_value = 'juno'
        self.os_release.return_value = 'juno'
        self.assertTrue('keepalived' in neutron_utils.get_packages())

    @patch('charmhelpers.contrib.network.ovs.charm_name')
    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_starts_service_if_required(
            self, mock_config, charm_name):
        charm_name.return_value = "neutron-gateway"
        mock_config.side_effect = self.test_config.get
        self.config.return_value = 'ovs'
        self.service_running.return_value = False
        neutron_utils.configure_ovs()
        self.assertTrue(self.full_restart.called)

    def test_configure_ovs_doesnt_restart_service(self):
        self.service_running.return_value = True
        neutron_utils.configure_ovs()
        self.assertFalse(self.full_restart.called)

    @patch('charmhelpers.contrib.network.ovs.charm_name')
    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_ovs_ext_port(self, mock_config, charm_name):
        charm_name.return_value = "neutron-gateway"
        mock_config.side_effect = self.test_config.get
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs')
        self.test_config.set('ext-port', 'eth0')
        self.ExternalPortContext.return_value = \
            DummyExternalPortContext(return_value={'ext_port': 'eth0'})
        neutron_utils.configure_ovs()
        self.add_bridge.assert_has_calls([
            call('br-int', brdata=ANY),
            call('br-ex', brdata=ANY),
            call('br-data', brdata=ANY)
        ])
        self.add_bridge_port.assert_called_with(
            'br-ex', 'eth0', ifdata=ANY, portdata=ANY
        )

    @patch('charmhelpers.contrib.openstack.context.list_nics',
           return_value=['eth0', 'eth0.100', 'eth0.200'])
    @patch('charmhelpers.contrib.network.ovs.charm_name')
    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_ovs_data_port(self, mock_config, charm_name, _nics):
        charm_name.return_value = "neutron-gateway"
        self.is_linuxbridge_interface.return_value = False
        mock_config.side_effect = self.test_config.get
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs')
        self.ExternalPortContext.return_value = \
            DummyExternalPortContext(return_value=None)
        # Test back-compatibility i.e. port but no bridge (so br-data is
        # assumed)
        self.test_config.set('data-port', 'eth0')
        neutron_utils.configure_ovs()
        self.add_bridge.assert_has_calls([
            call('br-int', brdata=ANY),
            call('br-ex', brdata=ANY),
            call('br-data', brdata=ANY)
        ])
        calls = [call('br-data', 'eth0', promisc=True, ifdata=ANY,
                      portdata=ANY)]
        self.add_bridge_port.assert_has_calls(calls)

        # Now test with bridge:port format and bogus bridge
        self.test_config.set('data-port', 'br-foo:eth0')
        self.add_bridge.reset_mock()
        self.add_bridge_port.reset_mock()
        neutron_utils.configure_ovs()
        self.add_bridge.assert_has_calls([
            call('br-int', brdata=ANY),
            call('br-ex', brdata=ANY),
            call('br-data', brdata=ANY)
        ])
        # Not called since we have a bogus bridge in data-ports
        self.assertFalse(self.add_bridge_port.called)

        # Now test with bridge:port format
        self.test_config.set('bridge-mappings', 'net1:br1')
        self.test_config.set('data-port', 'br1:eth0.100 br1:eth0.200')
        self.add_bridge.reset_mock()
        self.add_bridge_port.reset_mock()
        neutron_utils.configure_ovs()
        self.add_bridge.assert_has_calls([
            call('br-int', brdata=ANY),
            call('br-ex', brdata=ANY),
            call('br1', brdata=ANY)
        ])
        calls = [
            call('br1', 'eth0.100', promisc=True, ifdata=ANY, portdata=ANY),
            call('br1', 'eth0.200', promisc=True, ifdata=ANY, portdata=ANY)]
        self.add_bridge_port.assert_has_calls(calls, any_order=True)

    @patch('charmhelpers.contrib.openstack.context.list_nics',
           return_value=['br-eth0'])
    @patch('charmhelpers.contrib.network.ovs.charm_name')
    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_ovs_data_port_bridge(
            self, mock_config, charm_name, _nics):
        charm_name.return_value = "neutron-gateway"
        self.is_linuxbridge_interface.return_value = True
        mock_config.side_effect = self.test_config.get
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs')
        self.ExternalPortContext.return_value = \
            DummyExternalPortContext(return_value=None)
        # Test back-compatibility i.e. port but no bridge (so br-data is
        # assumed)
        self.test_config.set('data-port', 'br-eth0')
        neutron_utils.configure_ovs()

        # Also check that new bridges and ports are marked as managed by us:
        expected_brdata = {
            'external-ids': {'charm-neutron-gateway': 'managed'},
        }
        expected_ifdata = {
            'external-ids': {'charm-neutron-gateway': 'br-data'},
        }
        expected_portdata = expected_ifdata

        self.add_bridge.assert_has_calls([
            call('br-int', brdata=expected_brdata),
            call('br-ex', brdata=expected_brdata),
            call('br-data', brdata=expected_brdata)
        ])
        calls = [call('br-data', 'br-eth0', ifdata=expected_ifdata,
                      portdata=expected_portdata)]
        self.add_ovsbridge_linuxbridge.assert_has_calls(calls)

    @patch('charmhelpers.contrib.network.ovs.charm_name')
    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_enable_ipfix(self, mock_config, charm_name):
        charm_name.return_value = "neutron-gateway"
        mock_config.side_effect = self.test_config.get
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs')
        self.test_config.set('ipfix-target', '127.0.0.1:80')
        neutron_utils.configure_ovs()
        self.enable_ipfix.assert_has_calls([
            call('br-int', '127.0.0.1:80'),
            call('br-ex', '127.0.0.1:80'),
            call('br-data', '127.0.0.1:80'),
        ])

    @patch.object(neutron_utils, 'DataPortContext')
    @patch('charmhelpers.contrib.network.ovs.charm_name')
    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_ensure_ext_port_overriden(
            self, mock_config, charm_name, mock_data_port_context):
        charm_name.return_value = "neutron-gateway"
        mock_config.side_effect = self.test_config.get
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs')
        self.get_bridges_and_ports_map.return_value = {
            'br-data': ['p4', 'p5'],
            'br1': ['p6'],
        }
        self.test_config.set(
            'data-port',
            'br-data:p4 br-data:p5 br1:p6')
        self.test_config.set('bridge-mappings', 'net0:br-data net1:br1')
        self.test_config.set('ext-port', None)
        self.ExternalPortContext.return_value = \
            DummyExternalPortContext(return_value={'ext_port': 'eth0'})
        mock_data_port_context.return_value = \
            DummyDataPortContext(return_value={
                'p4': 'br-data',
                'p5': 'br-data',
                'p6': 'br1',
            })
        self.is_linuxbridge_interface.return_value = False
        neutron_utils.configure_ovs()
        # Ensure that ext-port was ignored.
        self.assertNotIn(call('br-ex', 'eth0', ifdata=ANY, portdata=ANY),
                         self.add_bridge_port.call_args_list)

    @patch.object(neutron_utils, 'register_configs')
    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_do_openstack_upgrade(self, mock_renderer,
                                  mock_register_configs):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        mock_configs = MagicMock()
        mock_register_configs.return_value = mock_configs
        self.config.side_effect = self.test_config.get
        self.is_relation_made.return_value = False
        self.test_config.set('openstack-origin', 'cloud:precise-havana')
        self.test_config.set('plugin', 'ovs')
        self.get_os_codename_install_source.return_value = 'havana'
        self.os_release.return_value = 'havana'
        self.filter_missing_packages.side_effect = lambda x: x
        neutron_utils.do_openstack_upgrade(mock_configs)
        mock_register_configs.assert_called_with('havana')
        self.assertTrue(self.log.called)
        self.apt_update.assert_called_with(fatal=True)
        dpkg_opts = [
            '--option', 'Dpkg::Options::=--force-confnew',
            '--option', 'Dpkg::Options::=--force-confdef',
        ]
        self.apt_upgrade.assert_called_with(
            options=dpkg_opts, fatal=True, dist=True
        )
        self.configure_installation_source.assert_called_with(
            'cloud:precise-havana'
        )
        self.apt_purge.assert_not_called()
        self.apt_autoremove.assert_not_called()

    @patch.object(neutron_utils, 'register_configs')
    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_do_openstack_upgrade_rocky(self, mock_renderer,
                                        mock_register_configs):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=True)
        mock_configs = MagicMock()
        mock_register_configs.return_value = mock_configs
        self.config.side_effect = self.test_config.get
        self.is_relation_made.return_value = False
        self.test_config.set('openstack-origin', 'cloud:bionic-rocky')
        self.test_config.set('plugin', 'ovs')
        self.get_os_codename_install_source.return_value = 'rocky'
        self.os_release.return_value = 'rocky'
        self.filter_missing_packages.side_effect = lambda x: x
        neutron_utils.do_openstack_upgrade(mock_configs)
        mock_register_configs.assert_called_with('rocky')
        self.assertTrue(self.log.called)
        self.apt_update.assert_called_with(fatal=True)
        dpkg_opts = [
            '--option', 'Dpkg::Options::=--force-confnew',
            '--option', 'Dpkg::Options::=--force-confdef',
        ]
        self.apt_upgrade.assert_called_with(
            options=dpkg_opts, fatal=True, dist=True
        )
        self.apt_purge.assert_called_with(
            neutron_utils.PURGE_PACKAGES, fatal=True
        )
        self.apt_autoremove.assert_called_with(
            purge=True, fatal=True
        )
        self.configure_installation_source.assert_called_with(
            'cloud:bionic-rocky'
        )
        self.service_restart.assert_called_once_with('neutron-metadata-agent')

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_ovs(self, mock_renderer):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'diablo'
        self.is_relation_made.return_value = False
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NEUTRON_DHCP_AGENT_CONF,
                 neutron_utils.NEUTRON_METADATA_AGENT_CONF,
                 neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF,
                 neutron_utils.NEUTRON_L3_AGENT_CONF,
                 neutron_utils.NEUTRON_ML2_PLUGIN_CONF,
                 neutron_utils.EXT_PORT_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_ovs_odl(self, mock_renderer):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs-odl')
        self.is_relation_made.return_value = False
        self.get_os_codename_install_source.return_value = 'icehouse'
        self.os_release.return_value = 'icehouse'
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NEUTRON_DHCP_AGENT_CONF,
                 neutron_utils.NEUTRON_METADATA_AGENT_CONF,
                 neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF,
                 neutron_utils.NEUTRON_L3_AGENT_CONF,
                 neutron_utils.EXT_PORT_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_amqp_nova(self, mock_renderer):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.is_relation_made.return_value = True
        self.os_release.return_value = 'diablo'
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NEUTRON_DHCP_AGENT_CONF,
                 neutron_utils.NEUTRON_METADATA_AGENT_CONF,
                 neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF,
                 neutron_utils.NEUTRON_L3_AGENT_CONF,
                 neutron_utils.NEUTRON_ML2_PLUGIN_CONF,
                 neutron_utils.EXT_PORT_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs(self, mock_get_packages):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.disable_neutron_lbaas.return_value = False
        self.get_os_codename_install_source.return_value = 'havana'
        mock_get_packages.return_value = ['neutron-vpn-agent']
        self.os_release.return_value = 'icehouse'
        ex_map = {
            neutron_utils.NEUTRON_CONF: sorted([
                'neutron-lbaas-agent',
                'neutron-plugin-openvswitch-agent',
                'neutron-dhcp-agent',
                'neutron-vpn-agent',
                'neutron-metering-agent',
                'neutron-metadata-agent']),
            neutron_utils.NEUTRON_DNSMASQ_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_LBAAS_AGENT_CONF:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_ML2_PLUGIN_CONF:
            ['neutron-plugin-openvswitch-agent'],
            neutron_utils.NEUTRON_METADATA_AGENT_CONF:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_VPNAAS_AGENT_CONF: [
                'neutron-vpn-agent'],
            neutron_utils.NEUTRON_L3_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_DHCP_AGENT_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_FWAAS_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_METERING_AGENT_CONF:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_CONF: ['nova-api-metadata'],
            neutron_utils.EXT_PORT_CONF: ['ext-port'],
            neutron_utils.PHY_NIC_MTU_CONF: ['os-charm-phy-nic-mtu'],
            neutron_utils.NEUTRON_DHCP_AA_PROFILE_PATH: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_OVS_AA_PROFILE_PATH:
                ['neutron-plugin-openvswitch-agent'],
            neutron_utils.NEUTRON_L3_AA_PROFILE_PATH: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_METADATA_AA_PROFILE_PATH:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_METERING_AA_PROFILE_PATH:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_API_METADATA_AA_PROFILE_PATH:
            ['nova-api-metadata'],
        }
        self.assertEqual(neutron_utils.restart_map(), ex_map)

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs_post_trusty(self, mock_get_packages):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        # No VPN agent after trusty
        mock_get_packages.return_value = ['neutron-l3-agent']
        self.os_release.return_value = 'diablo'
        rmap = neutron_utils.restart_map()
        for services in rmap.values():
            self.assertFalse('neutron-vpn-agent' in services)

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs_odl(self, mock_get_packages):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs-odl'
        self.disable_neutron_lbaas.return_value = False
        mock_get_packages.return_value = ['neutron-vpn-agent']
        self.os_release.return_value = 'icehouse'
        ex_map = {
            neutron_utils.NEUTRON_CONF: sorted([
                'neutron-lbaas-agent',
                'neutron-vpn-agent',
                'neutron-dhcp-agent',
                'neutron-metering-agent',
                'neutron-metadata-agent']),
            neutron_utils.NEUTRON_DNSMASQ_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_LBAAS_AGENT_CONF:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_METADATA_AGENT_CONF:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_VPNAAS_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_L3_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_DHCP_AGENT_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_FWAAS_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_METERING_AGENT_CONF:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_CONF: ['nova-api-metadata'],
            neutron_utils.EXT_PORT_CONF: ['ext-port'],
            neutron_utils.PHY_NIC_MTU_CONF: ['os-charm-phy-nic-mtu'],
            neutron_utils.NEUTRON_DHCP_AA_PROFILE_PATH: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_METADATA_AA_PROFILE_PATH:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_METERING_AA_PROFILE_PATH:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_API_METADATA_AA_PROFILE_PATH:
            ['nova-api-metadata'],
        }

        self.assertEqual(neutron_utils.restart_map(), ex_map)

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_nsx(self, mock_renderer):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'nsx'
        self.os_release.return_value = 'diablo'
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NEUTRON_DHCP_AGENT_CONF,
                 neutron_utils.NEUTRON_METADATA_AGENT_CONF,
                 neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    def test_stop_services_ovs(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'diablo'
        neutron_utils.stop_services()
        calls = [call('neutron-dhcp-agent'),
                 call('neutron-plugin-openvswitch-agent'),
                 call('nova-api-metadata'),
                 call('neutron-l3-agent'),
                 call('neutron-metadata-agent')]
        self.service_stop.assert_has_calls(
            calls,
            any_order=True,
        )

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_pre_install(self, mock_renderer):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self.config.return_value = 'ovs'
        self.is_relation_made.return_value = False
        self.os_release.return_value = 'diablo'
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF,
                 neutron_utils.NEUTRON_L3_AGENT_CONF,
                 neutron_utils.NEUTRON_ML2_PLUGIN_CONF,
                 neutron_utils.EXT_PORT_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    def test_copy_file_without_update(self):
        src = 'dummy_source_dir/dummy_file'
        dst = 'dummy_des_dir'
        neutron_utils.copy_file(src, dst)
        self.assertTrue(self.mkdir.called)
        self.assertTrue(self.copy2.called)

    @patch('neutron_utils.os.path.isfile')
    def test_copy_file_with_update(self, _isfile):
        src = 'dummy_source_dir/dummy_file'
        dst = 'dummy_des_dir'
        _isfile.return_value = False
        neutron_utils.copy_file(src, dst, force=True)
        self.assertTrue(self.mkdir.called)
        self.assertTrue(self.copy2.called)

    @patch('neutron_utils.os.remove')
    @patch('neutron_utils.os.path.isfile')
    def test_remove_file_exists(self, _isfile, _remove):
        path = 'dummy_des_dir/dummy_file'
        _isfile.return_value = True
        neutron_utils.remove_file(path)
        self.assertTrue(_remove.called)
        self.assertFalse(self.log.called)

    @patch('neutron_utils.os.remove')
    @patch('neutron_utils.os.path.isfile')
    def test_remove_file_non_exists(self, _isfile, _remove):
        path = 'dummy_des_dir/dummy_file'
        _isfile.return_value = False
        neutron_utils.remove_file(path)
        self.assertFalse(_remove.called)
        self.assertTrue(self.log.called)

    def test_resolve_config_files_ovs_liberty(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self._set_distrib_codename('trusty')
        self.os_release.return_value = 'liberty'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'liberty')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        INC_CONFIG = [neutron_utils.NEUTRON_ML2_PLUGIN_CONF]
        EXC_CONFIG = [neutron_utils.NEUTRON_OVS_AGENT_CONF,
                      neutron_utils.NEUTRON_LBAASV2_AA_PROFILE_PATH]
        for config in INC_CONFIG:
            self.assertTrue(config in actual_configs)
        for config in EXC_CONFIG:
            self.assertTrue(config not in actual_configs)

    def test_resolve_config_files_ovs_mitaka(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self._set_distrib_codename('trusty')
        self.os_release.return_value = 'mitaka'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'mitaka')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        INC_CONFIG = [neutron_utils.NEUTRON_OVS_AGENT_CONF]
        EXC_CONFIG = [neutron_utils.NEUTRON_ML2_PLUGIN_CONF,
                      neutron_utils.NEUTRON_LBAASV2_AA_PROFILE_PATH]
        for config in INC_CONFIG:
            self.assertTrue(config in actual_configs)
        for config in EXC_CONFIG:
            self.assertTrue(config not in actual_configs)

    def test_resolve_config_files_ovs_trusty(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self._set_distrib_codename('trusty')
        self.os_release.return_value = 'mitaka'
        self.is_relation_made = False
        self.disable_neutron_lbaas.return_value = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'mitaka')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        INC_CONFIG = [neutron_utils.EXT_PORT_CONF,
                      neutron_utils.PHY_NIC_MTU_CONF,
                      neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH]
        for config in INC_CONFIG:
            self.assertTrue(config in actual_configs)

    def test_resolve_config_files_ovs_xenial(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self._set_distrib_codename('xenial')
        self.os_release.return_value = 'mitaka'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'mitaka')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        EXC_CONFIG = [neutron_utils.EXT_PORT_CONF,
                      neutron_utils.PHY_NIC_MTU_CONF,
                      neutron_utils.NEUTRON_LBAASV2_AA_PROFILE_PATH]
        for config in EXC_CONFIG:
            self.assertTrue(config not in actual_configs)

    def test_resolve_config_files_ovs_newton(self):
        self.patch_object(neutron_utils, 'disable_nova_metadata',
                          return_value=False)
        self._set_distrib_codename('xenial')
        self.os_release.return_value = 'newton'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'newton')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        EXC_CONFIG = [neutron_utils.EXT_PORT_CONF,
                      neutron_utils.PHY_NIC_MTU_CONF,
                      neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH]
        for config in EXC_CONFIG:
            self.assertTrue(config not in actual_configs)


class DummyNetworkServiceContext():

    def __init__(self, return_value):
        self.return_value = return_value

    def __call__(self):
        return self.return_value


class DummyExternalPortContext():

    def __init__(self, return_value):
        self.return_value = return_value

    def __call__(self):
        return self.return_value


class DummyDataPortContext():

    def __init__(self, return_value):
        self.return_value = return_value

    def __call__(self):
        return self.return_value


cluster1 = ['cluster1-machine1.internal']
cluster2 = ['cluster2-machine1.internal', 'cluster2-machine2.internal'
            'cluster2-machine3.internal']


class TestNeutronAgentReallocation(CharmTestCase):

    def setUp(self):
        if not neutronclient:
            raise self.skipTest('Skipping, no neutronclient installed')
        super(TestNeutronAgentReallocation, self).setUp(neutron_utils,
                                                        TO_PATCH)

    def tearDown(self):
        # Reset cached cache
        hookenv.cache = {}

    def test_assess_status(self):
        with patch.object(neutron_utils, 'assess_status_func') as asf:
            callee = MagicMock()
            asf.return_value = callee
            neutron_utils.assess_status('test-config')
            asf.assert_called_once_with('test-config')
            callee.assert_called_once_with()
            self.os_application_version_set.assert_called_with(
                neutron_utils.VERSION_PACKAGE
            )

    @patch.object(neutron_utils, 'get_optional_interfaces')
    @patch.object(neutron_utils, 'sequence_status_check_functions')
    @patch.object(neutron_utils, 'REQUIRED_INTERFACES')
    @patch.object(neutron_utils, 'services')
    @patch.object(neutron_utils, 'make_assess_status_func')
    def test_assess_status_func(self,
                                make_assess_status_func,
                                services,
                                REQUIRED_INTERFACES,
                                sequence_functions,
                                get_optional_interfaces):
        services.return_value = ['s1']
        REQUIRED_INTERFACES.copy.return_value = {'int': ['test 1']}
        get_optional_interfaces.return_value = {'opt': ['test 2']}
        sequence_functions.return_value = 'sequence_return'
        neutron_utils.assess_status_func('test-config')
        # ports=None whilst port checks are disabled.
        make_assess_status_func.assert_called_once_with(
            'test-config',
            {'int': ['test 1'], 'opt': ['test 2']},
            charm_func='sequence_return', services=['s1'], ports=None)
        sequence_functions.assert_called_once_with(
            neutron_utils.check_optional_relations,
            neutron_utils.check_ext_port_data_port_config)

    def test_pause_unit_helper(self):
        with patch.object(neutron_utils, '_pause_resume_helper') as prh:
            neutron_utils.pause_unit_helper('random-config')
            prh.assert_called_once_with(neutron_utils.pause_unit,
                                        'random-config')
        with patch.object(neutron_utils, '_pause_resume_helper') as prh:
            neutron_utils.resume_unit_helper('random-config')
            prh.assert_called_once_with(neutron_utils.resume_unit,
                                        'random-config')

    @patch.object(neutron_utils, 'services')
    def test_pause_resume_helper(self, services):
        f = MagicMock()
        services.return_value = ['s1']
        with patch.object(neutron_utils, 'assess_status_func') as asf:
            asf.return_value = 'assessor'
            neutron_utils._pause_resume_helper(f, 'some-config')
            asf.assert_called_once_with('some-config')
            # ports=None whilst port checks are disabled.
            f.assert_called_once_with('assessor', services=['s1'], ports=None)

    @patch.object(neutron_utils, 'subprocess')
    @patch.object(neutron_utils, 'shutil')
    @patch('os.path.exists')
    def test_install_systemd_override_systemd(self, _os_exists, _shutil,
                                              _subprocess):
        '''
        Ensure systemd override is only installed on systemd based systems
        '''
        self.init_is_systemd.return_value = True
        _os_exists.return_value = False
        neutron_utils.install_systemd_override()
        _os_exists.assert_called_with(
            '/etc/systemd/system/nova-api-metadata.service.d/override.conf'
        )
        self.mkdir.assert_called_with(
            '/etc/systemd/system/nova-api-metadata.service.d'
        )
        _shutil.copy.assert_called_with(
            'files/override.conf',
            '/etc/systemd/system/nova-api-metadata.service.d/override.conf'
        )
        _subprocess.check_call.assert_called_with(
            ['systemctl', 'daemon-reload']
        )

    @patch.object(neutron_utils, 'context')
    def test_configure_apparmor_mitaka(self, context):
        self.os_release.return_value = 'mitaka'
        context.AppArmorContext = MagicMock()
        neutron_utils.configure_apparmor()
        context.AppArmorContext.assert_any_call(
            neutron_utils.NEUTRON_LBAAS_AA_PROFILE
        )

    @patch.object(neutron_utils, 'context')
    def test_configure_apparmor_newton(self, context):
        self.os_release.return_value = 'newton'
        context.AppArmorContext = MagicMock()
        neutron_utils.configure_apparmor()
        context.AppArmorContext.assert_any_call(
            neutron_utils.NEUTRON_LBAASV2_AA_PROFILE
        )

    @patch.object(neutron_utils, 'disable_nova_metadata')
    def test_deprecated_services(self, disable_nova_metadata):
        self.os_release.return_value = 'train'
        disable_nova_metadata.return_value = True
        self.assertEqual(neutron_utils.deprecated_services(),
                         ['nova-api-metadata',
                          'neutron-lbaasv2-agent'])
