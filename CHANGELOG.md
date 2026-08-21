# Changelog

## Unreleased

- Clarified that EVE-NG is a pre-existing external server and is not deployed by this project
- Renamed the GUI subtitle from `EVE-NG deployment` to `Existing EVE-NG integration`
- Clarified that Windows/macOS packages contain only the desktop client application
- Separated end-user requirements from build-machine requirements
- Clarified that IOS image import targets the existing EVE-NG server

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
