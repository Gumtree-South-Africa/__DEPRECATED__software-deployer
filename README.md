Deployer NG
==

Goal
--
A modular, extendable, configuration-driven deployment system.

To do
--
- Order of steps may need to depend on the state of the host (i.e. stop needs to come before unpack if redeploying the version that is currently active)
- ~~Separate Package and Service classes? Or how to implment actions that don't require packages to be provided? (i.e. restarting services)~~
- Templating or defaults sections in configuration files
- Database migrations
- Load balancer control
- ~~Logging is duplicated when creating multiple instances of an object (i.e. FabricHelper)~~
- Parallelism of steps doesn't make sense yet (i.e. stop all services on all hosts, then activate, etc)
