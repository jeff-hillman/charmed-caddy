#!/usr/bin/env python3
# Copyright 2021 Jeff Hillman
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging
import ops.lib

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus
from ops.pebble import ServiceStatus
from charms.nginx_ingress_integrator.v0.ingress import IngressRequires


logger = logging.getLogger(__name__)

CADDYFILE_TEMPLATE = "Caddyfile"
CADDY_CONFIG = "/etc/caddy/Caddyfile"

class CaddyCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.caddy_pebble_ready, self._on_caddy_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self._stored.set_default(hostname=[])
        self.ingress = IngressRequires(
            self,
            {
                "service-hostname": self.config["hostname"],
                "service-name": self.app.name,
                "service-port": 8080,
            },
        )

    def _on_caddy_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "caddy layer",
            "description": "pebble config layer for caddy",
            "services": {
                "caddy": {
                    "override": "replace",
                    "summary": "caddy",
                    "command": "caddy run --config /etc/caddy/Caddyfile --adapter caddyfile",
                    "startup": "enabled",
                    "environment": {},
                }
            },
        }
        # Add intial Pebble config layer using the Pebble API
        container.add_layer("caddy", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()
        self._configure_caddy_service()

#    def _render_template(self):
#        from jinja2 import Environment, PackageLoader, select_autoescape
#        env = Environment(
#            #loader=PackageLoader("caddy"),
#            autoescape=select_autoescape()
#        )
#        template = CADDYFILE_TEMPLATE
#        config = template.render(hostname=self.config["hostname"], file_server=self.config["file-server"])
#        container = self.unit.get_container("caddy")
#        container.push(CADDY_CONFIG, config, make_dirs=True)

    def _render_template(self):
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        env = Environment(loader=FileSystemLoader("templates/"))
        template = env.get_template(CADDYFILE_TEMPLATE)
        config = template.render(hostname=self.config["hostname"], file_server=self.config["file-server"])
        container = self.unit.get_container("caddy")
        container.push(CADDY_CONFIG, config, make_dirs=True)

    def _on_config_changed(self, _):
        """Just an example to show how to deal with changed configuration.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        current = self.config["hostname"]
        if current not in self._stored.hostname:
            logger.debug("found a new hostname: %r", current)
            self._stored.hostname.append(current)
        # Get the caddy container so we can configure/manipulate it
        container = self.unit.get_container(self.app.name)
        # Create a new config layer
        #layer = self._on_caddy_pebble_ready()

        self._configure_caddy_service()
        if container.can_connect():
            # All is well, set an ActiveStatus
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("waiting for Pebble in workload container")

    def _configure_caddy_service(self, event = None):
        container = self.unit.get_container(self.app.name)
        if not container.can_connect():
            logger.debug("XXX leaving CONFIG CHANGED early, pebble not ready?")
            return

        self._render_template()

        svc = container.get_service("caddy")
        if svc.is_running():
            container.restart("caddy")
        else:
            container.start("caddy")
        logger.debug("XXX applications: " + str(container.get_services()))
        logger.debug("XXX END OF CONFIG CHANGED")



if __name__ == "__main__":
    main(CaddyCharm)
