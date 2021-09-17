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
import urllib

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus

logger = logging.getLogger(__name__)


class CaddyCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        self.ingress = IngressRequires(
            self,
            {
                "service-hostname": self.config["hostname"],
                "service-name": self.app.name,
                "service-port": 8080,
            },
        )

    def _render_template(self):
        from jinja2 import Environment, PackageLoader, select_autoescape
        env = Environment(
            loader=PackageLoader("caddy"),
            autoescape=select_autoescape()
        )
        template = env.get_template("Caddyfile")
        config = template.render(hostname=self.config["hostname"], file_server=self.config["file-server"].lower())
        container.push('/etc/caddy/Caddyfile', config, make_dirs=True)

    def _on_config_changed(self, event):
        """Handle the config-changed event"""
        # Get the caddy container so we can configure/manipulate it
        container = self.unit.get_container("caddy")
        # Create a new config layer
        layer = self._caddy_layer()

        if container.can_connect():
            # Get the current config
            services = container.get_plan().to_dict().get("services", {})
            # Check if there are any changes to services
            if services != layer["services"]:
                # Changes were made, add the new layer
                container.add_layer("caddy", layer, combine=True)
                logging.info("Added updated layer 'caddy' to Pebble plan")
                # Restart it and report a new status to Juju
                container.stop("caddy")
                self._render_template()
                container.start("caddy")
                logging.info("Restarted caddy service")
            # All is well, set an ActiveStatus
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("waiting for Pebble in workload container")

    def _caddy_layer(self):
        """Returns a Pebble configration layer for Caddy"""
        return {
            "summary": "caddy layer",
            "description": "pebble config layer for caddy",
            "services": {
                "caddy": {
                    "override": "replace",
                    "summary": "caddy",
                    "command": "caddy start",
                    "startup": "enabled",
                    "environment": {
                        "HOSTNAME": self.config["hostname"],
                        "FILE_SERVER": self.config["file-server"].lower(),
                        "WEBROOT": "/srv",
                    },
                }
            },
        }


if __name__ == "__main__":
    main(CaddyCharm)
