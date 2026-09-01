"""GUI package bootstrap extensions."""

from ccna_lab_builder.gui import topology_canvas as _topology_canvas
from ccna_lab_builder.gui.automatic_cabling import install_automatic_cabling
from ccna_lab_builder.gui.connection_feedback import install_connection_feedback
from ccna_lab_builder.gui.console_lab_discovery import install_global_console_lab_discovery
from ccna_lab_builder.gui.console_target_compat import install_console_target_compat
from ccna_lab_builder.gui.console_workspace import install_console_workspace
from ccna_lab_builder.gui.lab_rebuild_console_fix import (
    install_lab_rebuild_and_console_fix,
)
from ccna_lab_builder.gui.runtime_recovery import install_runtime_recovery
from ccna_lab_builder.gui.single_active_lab import install_single_active_lab
from ccna_lab_builder.gui.ssh_native_cabling import install_ssh_native_cabling
from ccna_lab_builder.gui.stability_461 import install_stability_461
from ccna_lab_builder.gui.terminal_stream_compat import install_terminal_stream_compat
from ccna_lab_builder.gui.validator_vlan_compat import install_vlan_validation_compat


if not getattr(_topology_canvas.install_topology_workspace, "_console_wrapped", False):
    _original_install_topology_workspace = _topology_canvas.install_topology_workspace

    def _install_topology_and_console(window):
        _original_install_topology_workspace(window)
        install_console_workspace(window)
        install_console_target_compat(window)
        install_global_console_lab_discovery(window)
        install_terminal_stream_compat(window)
        install_automatic_cabling(window)
        install_single_active_lab(window)
        install_runtime_recovery(window)
        install_lab_rebuild_and_console_fix(window)
        install_stability_461(window)
        install_connection_feedback(window)
        install_ssh_native_cabling(window)
        install_vlan_validation_compat(window)

    _install_topology_and_console._console_wrapped = True
    _topology_canvas.install_topology_workspace = _install_topology_and_console
