# Changelog

## Unreleased

- Clarified that EVE-NG is a pre-existing external server and is not deployed by this project
- Renamed the GUI subtitle from `EVE-NG deployment` to `Existing EVE-NG integration`
- Clarified that Windows/macOS packages contain only the desktop client application
- Separated end-user requirements from build-machine requirements
- Clarified that IOS image import targets the existing EVE-NG server

## 5.2.2 — 2026-09-08

- Fixed Advanced lab SSH-native cabling when EVE-NG API node IDs temporarily differ from the freshly generated `.unl` node IDs
- Made exact `.unl` node names authoritative during SSH-native link creation while preserving endpoint and interface validation
- Expanded installed-image discovery to show every QEMU image folder instead of hiding unsupported families
- Added inventory discovery for IOL, Dynamips and Docker images on the connected EVE-NG host
- Added case-insensitive IOSv detection plus `vios_l2-*` and related IOSvL2 folder aliases
- Added an Installed EVE-NG image inventory panel to the Images page
- Added regression tests for stale API node IDs and complete multi-family image inventory parsing

## 5.1.2 — 2026-09-07

- Increased graceful QEMU shutdown confirmation during lab swaps from 10 to 30 seconds
- Added a per-node EVE-NG stop retry when a bulk lab stop is accepted but QEMU runtimes remain active
- Added a final stale-runtime cleanup path using SIGTERM and, only as a last resort, SIGKILL
- Scoped forced signals to QEMU processes whose EVE runtime working directory contains the exact lab UUID, so other labs are not targeted
- Added regression tests for per-node retry, UUID-scoped signals, SIGTERM recovery and SIGKILL last-resort behavior

## 4.6.1 — 2026-08-30

- Fixed EVE error 20033 by never trusting a network ID returned incidentally by `POST /networks`
- Cabling now re-reads both EVE `/networks` and `/links` and uses only network IDs advertised as valid Ethernet endpoints
- Added post-connect interface verification so a link is accepted only when EVE reports the expected `network_id` on the interface
- Failed lab generation now stops and deletes the partially-created lab when cleanup APIs are available
- Restored Device Console to the stable exact-runtime resolver; aggressive stop/start recovery is now scoped to Live Validator only
- Added use of EVE-NG's real `/labs/close` API after a lab is stopped
- Added regression tests for misleading network IDs, endpoint verification, and EVE lab close

## 4.6.0 — 2026-08-30

- Added a persistent `Replace existing lab automatically` option for Master and Training Lab generation
- Existing labs can now be stopped, have their interactive consoles closed, be deleted, and be rebuilt automatically instead of failing with EVE error 60016
- Lab replacement waits for EVE-NG to confirm that the old `.unl` file is gone before rebuilding
- Restored the interactive console's stable exact-runtime lookup path before invoking aggressive stale-runtime recovery
- Limited controlled node recycling in Device Console to a fallback after normal console discovery genuinely fails
- Preserved the stricter runtime-recovery behavior for Live Validator
- Added unit tests for lab deletion/rebuild handling and console recovery isolation

## 4.5.1 — 2026-08-30

- Added strict runtime checks after STOP ALL so lab changes wait for QEMU to exit instead of trusting API state alone
- Added controlled stale-node recovery for console access: verify PID state, stop stale nodes, wait for runtime exit, restart, then verify console readiness
- Prevented automatic lab swaps from continuing while the previous lab still has running QEMU processes

## 4.5.0 — 2026-08-30

- Added a global single-active-lab controller across Master, Training, Challenge and Device Console workflows
- Switching labs now closes interactive console sessions for the previous topology before the change
- Automatically stops the previously active EVE-NG lab before starting or opening another one
- On first lab activation, discovers other EVE-NG labs in the configured folder and stops them so only the selected topology remains active
- Added a header indicator showing which lab is active/stopped and why a swap is happening
- Added a `STOP & CLOSE ACTIVE LAB` control for safely stopping the tracked lab and clearing its console sessions
- Reused the controller in the existing challenge cleanup path so all lab types follow the same runtime policy
- Added regression tests for first activation cleanup, subsequent swaps, same-lab reuse and stop-failure aborts

## 4.4.0 — 2026-08-30

- Added SSH-native automatic cabling for generated Master and Training labs
- Replaced EVE-NG REST network/link creation with direct `.unl` topology editing over SSH to avoid Community-edition HTTP 400 `Invalid network id` failures
- Generated links now use hidden Ethernet bridge networks and exact interface IDs, followed by EVE fixpermissions and lab reopen
- Disabled the legacy `Experimental API cabling` checkbox because automatic SSH-native cabling is now the stable default path
- Added regression tests for `.unl` path safety and hidden-link generation

## 4.3.2 — 2026-08-30

- Verified installed VPCS console ports against the live QEMU runtime before using them
- Added Community fallback console-port derivation for the standard `32768 + pod*128 + node_id` mapping when the runtime uses the EVE wrapper stdio backend
- Extended SSH runtime parsing to recognize `/opt/unetlab/wrappers/unl_wrapper` VPCS processes in addition to direct QEMU command lines
- Added regression tests for exact VPCS runtime ports and Community pod/node port derivation

## 4.3.1 — 2026-08-30

- Fixed Community-edition challenge console startup for VPCS nodes when the API returns Guacamole paths or no native console port
- Challenge consoles now reuse the same EVE runtime discovery backend as IOSv/IOSvL2 consoles and retry after node start
- Added VPCS-aware console validation and regression tests for runtime-discovered console ports

## 4.3.0 — 2026-08-30

- Added an isolated `Cisco Challenge` lab pack sourced from the five challenge `.unl` files in the supplied EVE-NG workbook
- Added per-scenario EVE-NG lab creation so converted labs use their own topology instead of the shared 12-node Master topology
- Added built-in VPCS node support for challenge topologies, including native EVE-NG `vpcs` payloads and console access
- Added Challenge Lab UI with objectives, tasks, topology rendering, lab creation, console shortcuts and live validation
- Added automatic rollback cleanup when a challenge lab build fails after creating the `.unl`
- Added tests to guarantee the 37 CCNA labs remain unchanged and converted challenge topologies are self-contained
- Documented source provenance and the workbook answer-key conflict for the HSRPv2 lab

## 4.2.0 — 2026-08-30

- Added a live learning topology workspace with real-time node status, link state and validator overlays
- Added clickable device actions for console access and start/stop control directly from the topology map
- Added progressive hints that turn failed checks into focused remediation guidance without immediately revealing the full solution
- Added attempt history with validation scores, runtime actions and per-lab learning progress
- Added a repeatable reset workflow that stops, removes and rebuilds the current training lab from a clean topology
- Added live runtime polling against EVE-NG and live validation refresh hooks while keeping networking state tied to the real backend

## 4.1.0 — 2026-08-30

- Added a guided topology preview to Master Lab and Training Labs
- Added device-role visualization for routers, switches, hosts and infrastructure nodes
- Added automatic lab topology rendering when a lab is selected
- Added device console workspace with multi-tab interactive CLI sessions
- Added topology-to-console integration so double-clicking a node opens its live EVE-NG console
- Added manual device selector for console access from inside the application
- Added live validation panel with command-by-command results and score display
- Added exact-node console discovery so validation never silently targets another lab
- Added regression tests for explicit per-lab topologies, interface reuse, validator targeting and console lookup behavior

## 4.0.0 — 2026-08-30

- Redesigned the entire desktop UI with a modern CCNA learning-dashboard layout
- Added sidebar navigation, dashboard overview cards, connection status chips and page-level actions
- Added a persistent activity log so long-running EVE-NG tasks stay visible without blocking dialogs
- Added an async task runner so connectivity tests, image scans, image imports, master-lab generation and training-lab generation no longer freeze the interface
- Added task progress indicators and clearer Ready / Working / Error state feedback
- Preserved all existing EVE-NG API, SSH, lab generation, validator and compatibility functionality

## 3.1.0 — 2026-08-30

- Fixed GUI freezing during Test Connection when EVE-NG is slow or unreachable
- Added HTTP and SSH connection timeouts so failed tests return promptly instead of hanging indefinitely
- Added a visible progress state while connectivity tests run
- Restored the Test Connection button after both successful and failed attempts
- Added friendly connection error messages with guidance to verify EVE-NG host, port and credentials

## 3.0.0 — 2026-08-30

- Replaced the old `images/` staging workflow with direct image import from the GUI
- Added separate router and switch image selectors to the `IOS Images` tab
- Added automatic IOSv / IOSvL2 image detection before upload
- Added automatic upload into the correct EVE-NG QEMU folder
- Added automatic `fixpermissions` after each upload
- Added an EVE-NG `SCAN INSTALLED IMAGES` action so the app can reuse images already present on the server
- Added persistent EVE-NG settings stored outside the application bundle

## 2.0.0 — 2026-08-30

- Added installer-first deployment for macOS and Windows
- Added EVE-NG host/user/password SSH configuration to the GUI and persistent settings
- Added SSH upload support for IOSv and IOSvL2 images with automatic EVE-NG `fixpermissions`
- Added native macOS packaging (`.app` + `.dmg`) with launch script and installer guide
- Added native Windows packaging (`.exe`) with installer script and guide

## 1.0.0 — 2026-08-30

- Initial structured release