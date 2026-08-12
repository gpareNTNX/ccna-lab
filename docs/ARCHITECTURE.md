# Architecture

## Deployment boundary

EVE-NG is **pre-existing external infrastructure**. It is outside the installation lifecycle of this application.

```text
Client workstation                      Existing server
------------------                     ----------------
CCNA EVE Lab Builder  -- API + SSH --> EVE-NG
                                             |
                                             +-- IOSv
                                             +-- IOSvL2
                                             +-- CCNA labs
```

The Windows/macOS installers deploy only the client-side application.

## Application layers

```text
Tkinter GUI
   |
   +-- Settings
   +-- Scenario catalog
   +-- Validator
   |
Core services
   |
   +-- EVE API client
   +-- SSH/SCP client
   +-- IOS image importer
   +-- Lab builder
   +-- Console tunnel
   +-- Live validator
   |
Existing EVE-NG server
```

## Why two EVE connections?

The application uses:

1. **EVE API** for lab lifecycle and inventory.
2. **SSH** for image import and tunneled console access.

This avoids requiring Cisco console ports to be exposed directly to the workstation.

## Live validation

The validator:

1. obtains a node's console URL from EVE;
2. extracts its dynamic Telnet port;
3. opens an SSH `direct-tcpip` channel to `127.0.0.1:<console-port>` on the existing EVE server;
4. sends a read-only `show` command;
5. tests expected tokens;
6. returns PASS/FAIL and a score.

The validator does not configure the device and does not modify the EVE-NG server installation.
