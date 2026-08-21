# Changelog

## Unreleased

- Clarified that EVE-NG is a pre-existing external server and is not deployed by this project
- Renamed the GUI subtitle from `EVE-NG deployment` to `Existing EVE-NG integration`
- Clarified that Windows/macOS packages contain only the desktop client application
- Separated end-user requirements from build-machine requirements
- Clarified that IOS image import targets the existing EVE-NG server

## 4.3.2 — 2026-08-21

- Added recursive discovery of real EVE-NG `.unl` labs through the existing SSH connection
- Added an `EVE LAB` selector and refresh control to Device Console
- Added AUTO resolution across `/opt/unetlab/labs`, including labs outside the configured folder
- Added safe ambiguity handling when multiple labs contain the same topology node
- Added clearer diagnostics showing discovered EVE labs when no matching node can be found

## 4.3.1 — 2026-08-21

- Fixed Device Console attempts against predicted `.unl` paths that do not exist on EVE-NG
- Added verification of the active topology lab before opening an IOS console
- Added scenario/Validator target resolution and configured-folder discovery for matching labs
- Added clear guidance to build the Master Lab or create the selected scenario when no real lab exists
- Preserved exact EVE-NG runtime/QEMU console discovery after the lab target is resolved

## 4.3.0 — 2026-08-21

- Added a dedicated interactive Device Console workspace
- Added double-click console access directly from Topology devices
- Added multiple simultaneous device console tabs
- Reused exact EVE-NG runtime/QEMU console discovery from Live Validator
- Added interactive Enter, Tab, arrow, Ctrl+C and clipboard-paste terminal input
- Added connect, reconnect, clear, disconnect and disconnect-all controls
- Added user-provided router, switch, cloud, terminal, firewall and server icons
- Added transparent optimized PNG assets without adding a runtime image dependency
- Added icon-based topology node rendering with live validation status badges

## 4.2.0 — 2026-08-21

- Added an EVE-inspired graphical Topology Canvas workspace
- Added automatic rendering of scenario nodes, links, interface labels and device groups
- Added a Master Lab topology view sourced from the existing topology definition
- Added a live validation overlay with per-device pass, fail and partial states
- Added node selection for validation detail inspection
- Added automatic synchronization between Training Lab selection and the topology view
- Added a dedicated Topology navigation entry while preserving existing lab-builder behavior
- Added per-page task activity feedback for IOS Images, Master Lab, Training Labs and Validator
- Added macOS Tk Listbox compatibility handling for unsupported active color options

## 4.1.0 — 2026-08-12

- Added Windows x64 PyInstaller deployment
- Added Inno Setup Windows installer
- Added macOS Apple Silicon packaging
- Added macOS Intel packaging
- Added DMG creation
- Added optional Developer ID signing support
- Added Apple notarytool / stapling workflow
- Added GitHub Actions multi-platform release pipeline
- Added deployment documentation and tests

## 4.0.0 — 2026-08-12

- Reorganized project for GitHub
- Added persistent non-secret settings
- Added EVE-NG API client cleanup
- Added image inventory scanning
- Added 20 data-driven CCNA scenarios
- Added fresh scenario-lab creation
- Added live SSH-tunneled console validation
- Added compatibility-isolated experimental cabling
- Added tests and GitHub Actions CI
- Added complete project documentation
