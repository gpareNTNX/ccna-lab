"""GUI package bootstrap extensions."""

from ccna_lab_builder.gui import topology_canvas as _topology_canvas
from ccna_lab_builder.gui.advanced_lab_ui import install_advanced_lab_ui
from ccna_lab_builder.gui.automatic_cabling import install_automatic_cabling
from ccna_lab_builder.gui.challenge_pack import install_challenge_pack
from ccna_lab_builder.gui.connection_feedback import install_connection_feedback
from ccna_lab_builder.gui.console_lab_discovery import install_global_console_lab_discovery
from ccna_lab_builder.gui.console_target_compat import install_console_target_compat
from ccna_lab_builder.gui.console_workspace import install_console_workspace
from ccna_lab_builder.gui.creator_credit import install_creator_credit
from ccna_lab_builder.gui.eve_inventory_cabling_fix import install_eve_inventory_cabling_fix
from ccna_lab_builder.gui.lab_rebuild_console_fix import (
    install_lab_rebuild_and_console_fix,
)
from ccna_lab_builder.gui.learning_experience import install_learning_experience
from ccna_lab_builder.gui.manual_validation_only import install_manual_validation_only
from ccna_lab_builder.gui.nutanix_bonus import install_nutanix_bonus
from ccna_lab_builder.gui.nutanix_bonus_compat import install_nutanix_bonus_compat
from ccna_lab_builder.gui.nutanix_bonus_scan_fix import install_nutanix_bonus_scan_fix
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
        install_challenge_pack(window)
        install_advanced_lab_ui(window)
        install_learning_experience(window)
        install_manual_validation_only(window)
        install_nutanix_bonus(window)
        install_nutanix_bonus_compat(window)
        install_nutanix_bonus_scan_fix(window)
        install_eve_inventory_cabling_fix(window)
        install_creator_credit(window)

    _install_topology_and_console._console_wrapped = True
    _topology_canvas.install_topology_workspace = _install_topology_and_console
