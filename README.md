# charmed caddy

## Description

k8s charmed caddy for juju deployments.  This charm will allow for auto-generation of an SSL cert using a local provider.  It can also be configured to be an HTTP/HTTPS fileserver that can be configured to be browseable.

## Usage

juju deploy caddy --resource caddy=caddy


## Relations

none at this time

## OCI Images

caddy:latest

## TODO

- Configure proper ACME cert generation
- Add actions to upload files to fileserver

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines 
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.
