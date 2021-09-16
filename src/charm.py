#!/usr/bin/env python3
# Copyright 2021 ubuntu
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class CaddyCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.caddy_pebble_ready, self._on_caddy_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.fortune_action, self._on_fortune_action)
        self._stored.set_default(hostname=[])

    def _on_caddy_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.
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
                    "command": "caddy start",
                    "startup": "enabled",
                    "environment": {"hostname": self.model.config["hostname"]},
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
                    "environment": {"hostname": self.model.config["hostname"]},
               }
           },
        }
    def _on_config_changed(self, _):
        """Just an example to show how to deal with changed configuration.
        """
        current = self.config["hostname"]
        if current not in self._stored.hostname:
            logger.debug("found a new hostname: %r", current)
            self._stored.hostname.append(current)
        container = self.unit.get_container("caddy")
        layer = self._caddy_layer()
        services = container.get_plan().to_dict().get("services", {})
        if services != layer["services"]:
            # Changes were made, add the new layer
            container.add_layer("caddy", layer, combine=True)
            logging.info("Added updated layer 'caddy' to Pebble plan")
            # Stop the service if it is already running
            if container.get_service("caddy").is_running():
                container.stop("caddy")
            # Restart it and report a new status to Juju
            container.start("caddy")
            logging.info("Restarted caddy service")
        # All is well, set an ActiveStatus
        self.unit.status = ActiveStatus()

    def _on_fortune_action(self, event):
        """Just an example to show how to receive actions.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle actions, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the actions.py file.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        fail = event.params["fail"]
        if fail:
            event.fail(fail)
        else:
            event.set_results({"fortune": "A bug in the code is worth two in the documentation."})


if __name__ == "__main__":
    main(CaddyCharm)
