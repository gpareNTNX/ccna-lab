"""GUI package bootstrap extensions."""

from ccna_lab_builder.gui import topology_canvas as _topology_canvas
from ccna_lab_builder.gui.automatic_cabling import install_automatic_cabling
from ccna_lab_builder.gui.console_workspace import install_console_workspace
from ccna_lab_builder.gui.console_target_compat import install_console_target_compat
from ccna_lab_builder.gui.console_lab_discovery import install_global_console_lab_discovery
from ccna_lab_builder.gui.terminal_stream_compat import install_terminal_stream_compat


if not getattr(_topology_canvas.install_topology_workspace, "_console_wrapped", False):
    _original_install_topology_workspace = _topology_canvas.install_topology_workspace

    def _install_topology_and_console(window):
        _original_install_topology_workspace(window)
        install_console_workspace(window)
        install_console_target_compat(window)
        install_global_console_lab_discovery(window)
        install_terminal_stream_compat(window)
        install_automatic_cabling(window)

    _install_topology_and_console._console_wrapped = True
    _topology_canvas.install_topology_workspace = _install_topology_and_console
