import os

import testinfra
import testinfra.utils.ansible_runner
import urllib.request

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def get_service_name(host):
    if host.system_info.distribution == 'freebsd':
        return 'blackbox_exporter'
    elif host.system_info.distribution == 'ubuntu':
        return 'prometheus-blackbox-exporter'
    raise NameError('Unknown distribution')


def get_ansible_vars(host):
    return host.ansible.get_variables()


def get_ansible_facts(host):
    return host.ansible('setup')['ansible_facts']


def read_remote_file(host, filename):
    f = host.file(filename)
    assert f.exists
    assert f.content is not None
    return f.content.decode('utf-8')


def is_docker(host):
    ansible_facts = get_ansible_facts(host)
    if 'ansible_virtualization_type' in ansible_facts:
        if ansible_facts['ansible_virtualization_type'] == 'docker':
            return True
    return False


def get_listen_ports(host):
    return [9115]


def get_listen_address(host):
    ansible_facts = get_ansible_facts(host)
    if host.system_info.distribution == 'freebsd':
        return ansible_facts['ansible_em1']['ipv4'][0]['address']
    elif host.system_info.distribution == 'ubuntu':
        return ansible_facts['ansible_eth1']['ipv4']['address']
    else:
        raise NameError('Unknown distribution')


def test_hosts_file(host):
    f = host.file('/etc/hosts')

    assert f.exists
    assert f.user == 'root'
    assert f.group == 'root' or f.group == 'wheel'


def test_service(host):
    s = host.service(get_service_name(host))

    # XXX in docker, host.service() does not work
    if not is_docker(host):
        assert s.is_running
        assert s.is_enabled


def test_port(host):
    ports = get_listen_ports(host)
    address = get_listen_address(host)

    for p in ports:
        assert host.socket("tcp://%s:%d" % (address, p)).is_listening


def test_api(host):
    ports = get_listen_ports(host)
    address = get_listen_address(host)
    url = "http://%s:%d" % (address, ports[0])
    with urllib.request.urlopen(url) as f:
        content = f.read().decode('utf-8').replace("\n", "")

        assert content is not None
