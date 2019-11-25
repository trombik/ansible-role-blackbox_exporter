# `trombik.blackbox_exporter`

`ansible` role for `blackbox_exporter`.

# Requirements

# Role Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `blackbox_exporter_package` | Package name of `blackbox_exporter` | `{{ __blackbox_exporter_package }}` |
| `blackbox_exporter_service` | Service name of `blackbox_exporter` | `{{ __blackbox_exporter_service }}` |
| `blackbox_exporter_extra_packages` | A list of extra package to install | `[]` |
| `blackbox_exporter_user` | User name of `blackbox_exporter` | `{{ __blackbox_exporter_user }}` |
| `blackbox_exporter_group` | Group name of `blackbox_exporter` | `{{ __blackbox_exporter_group }}` |
| `blackbox_exporter_extra_groups` | A list of extra groups for `blackbox_exporter_user` | `[]` |
| `blackbox_exporter_log_dir` | Path to log directory | `{{ __blackbox_exporter_log_dir }}` |
| `blackbox_exporter_config_dir` | Path to the configuration directory | `{{ __blackbox_exporter_config_dir }}` |
| `blackbox_exporter_config_file` | Path to `blackbox_exporter.yml` | `{{ blackbox_exporter_config_dir }}/blackbox_exporter.yml` |
| `blackbox_exporter_config` | The content of `blackbox_exporter.yml` | `""` |
| `blackbox_exporter_flags` | See below | `""` |

## `blackbox_exporter_flags`

This variable is used for overriding defaults for startup scripts. In Debian
variants, the value is the content of `/etc/default/blackbox_exporter`. In RedHat
variants, it is the content of `/etc/sysconfig/blackbox_exporter`. In FreeBSD, it
is the content of `/etc/rc.conf.d/blackbox_exporter`. In OpenBSD, the value is
passed to `rcctl set blackbox_exporter`.

## Debian

| Variable | Default |
|----------|---------|
| `__blackbox_exporter_service` | `prometheus-blackbox-exporter` |
| `__blackbox_exporter_package` | `prometheus-blackbox-exporter` |
| `__blackbox_exporter_config_dir` | `/etc/blackbox` |
| `__blackbox_exporter_user` | `prometheus` |
| `__blackbox_exporter_group` | `prometheus` |
| `__blackbox_exporter_log_dir` | `/var/log/prometheus` |

## FreeBSD

| Variable | Default |
|----------|---------|
| `__blackbox_exporter_service` | `blackbox_exporter` |
| `__blackbox_exporter_package` | `net-mgmt/blackbox_exporter` |
| `__blackbox_exporter_config_dir` | `/usr/local/etc` |
| `__blackbox_exporter_user` | `prometheus` |
| `__blackbox_exporter_group` | `prometheus` |
| `__blackbox_exporter_log_dir` | `/var/log/blackbox_exporter` |

# Dependencies

# Example Playbook

```yaml
---
- hosts: localhost
  roles:
    - ansible-role-blackbox_exporter
  pre_tasks:
    - name: Dump all hostvars
      debug:
        var: hostvars[inventory_hostname]
  post_tasks:
    - name: List all services (systemd)
      # workaround ansible-lint: [303] service used in place of service module
      shell: "echo; systemctl list-units --type service"
      changed_when: false
      when:
        # in docker, init is not systemd
        - ansible_virtualization_type != 'docker'
        - ansible_os_family == 'RedHat' or ansible_os_family == 'Debian'
    - name: list all services (FreeBSD service)
      # workaround ansible-lint: [303] service used in place of service module
      shell: "echo; service -l"
      changed_when: false
      when:
        - ansible_os_family == 'FreeBSD'
  vars:
    os_blackbox_exporter_flags:
      OpenBSD: ""
      FreeBSD: |
        blackbox_exporter_listen_address={{ ansible_default_ipv4['address'] }}:9115
        blackbox_exporter_log_file={{ blackbox_exporter_log_dir }}/blackbox_exporter.log
      Debian: |
        ARGS="--config.file=/etc/prometheus/blackbox.yml --web.listen-address={{ ansible_default_ipv4['address'] }}:9115"
      RedHat: ""
    blackbox_exporter_flags: "{{ os_blackbox_exporter_flags[ansible_os_family] }}"

    # https://github.com/prometheus/blackbox_exporter/blob/master/example.yml
    blackbox_exporter_config:
      modules:
        http_2xx_example:
          prober: http
          timeout: 5s
          http:
            valid_http_versions: ["HTTP/1.1", "HTTP/2"]
            valid_status_codes: []  # Defaults to 2xx
            method: GET
            headers:
              Host: vhost.example.com
              Accept-Language: en-US
              Origin: example.com
            no_follow_redirects: false
            fail_if_ssl: false
            fail_if_not_ssl: false
            fail_if_body_matches_regexp:
              - "Could not connect to database"
            fail_if_body_not_matches_regexp:
              - "Download the latest version here"
            fail_if_header_matches:  # Verifies that no cookies are set
              - header: Set-Cookie
                allow_missing: true
                regexp: '.*'
            fail_if_header_not_matches:
              - header: Access-Control-Allow-Origin
                regexp: '(\*|example\.com)'
            tls_config:
              insecure_skip_verify: false
            preferred_ip_protocol: "ip4"  # defaults to "ip6"
            ip_protocol_fallback: false  # no fallback to "ip6"
        http_post_2xx:
          prober: http
          timeout: 5s
          http:
            method: POST
            headers:
              Content-Type: application/json
            body: '{}'
        http_basic_auth_example:
          prober: http
          timeout: 5s
          http:
            method: POST
            headers:
              Host: "login.example.com"
            basic_auth:
              username: "username"
              password: "mysecret"
        tls_connect:
          prober: tcp
          timeout: 5s
          tcp:
            tls: true
        tcp_connect_example:
          prober: tcp
          timeout: 5s
        imap_starttls:
          prober: tcp
          timeout: 5s
          tcp:
            query_response:
              - expect: "OK.*STARTTLS"
              - send: ". STARTTLS"
              - expect: "OK"
              - starttls: true
              - send: ". capability"
              - expect: "CAPABILITY IMAP4rev1"
        smtp_starttls:
          prober: tcp
          timeout: 5s
          tcp:
            query_response:
              - expect: "^220 ([^ ]+) ESMTP (.+)$"
              - send: "EHLO prober"
              - expect: "^250-STARTTLS"
              - send: "STARTTLS"
              - expect: "^220"
              - starttls: true
              - send: "EHLO prober"
              - expect: "^250-AUTH"
              - send: "QUIT"
        irc_banner_example:
          prober: tcp
          timeout: 5s
          tcp:
            query_response:
              - send: "NICK prober"
              - send: "USER prober prober prober :prober"
              - expect: "PING :([^ ]+)"
                send: "PONG ${1}"
              - expect: "^:[^ ]+ 001"
        icmp_example:
          prober: icmp
          timeout: 5s
          icmp:
            preferred_ip_protocol: "ip4"
            source_ip_address: "127.0.0.1"
        dns_udp_example:
          prober: dns
          timeout: 5s
          dns:
            query_name: "www.prometheus.io"
            query_type: "A"
            valid_rcodes:
              - NOERROR
            validate_answer_rrs:
            validate_authority_rrs:
            validate_additional_rrs:
        dns_soa:
          prober: dns
          dns:
            query_name: "prometheus.io"
            query_type: "SOA"
        dns_tcp_example:
          prober: dns
          dns:
            transport_protocol: "tcp"  # defaults to "udp"
            preferred_ip_protocol: "ip4"  # defaults to "ip6"
            query_name: "www.prometheus.io"
```

# License

```
Copyright (c) 2016 Tomoyuki Sakurai <y@trombik.org>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```

# Author Information

Tomoyuki Sakurai <y@trombik.org>
