# Architecture

## Layers

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
   +-- IOS image installer
   +-- Lab builder
   +-- Console tunnel
   +-- Live validator
   |
EVE-NG
   |
   +-- IOSv
   +-- IOSvL2
```

## Why two EVE connections?

The application uses:

1. **EVE API** for lab lifecycle and inventory.
2. **SSH** for image installation and tunneled console access.

This avoids requiring Cisco console ports to be exposed directly to the workstation.

## Live validation

The validator:

1. obtains a node's console URL from EVE;
2. extracts its dynamic Telnet port;
3. opens an SSH `direct-tcpip` channel to `127.0.0.1:<console-port>` on EVE;
4. sends a read-only `show` command;
5. tests expected tokens;
6. returns PASS/FAIL and a score.

The validator does not configure the device.
