import re


def install_inline_prompt_parser():
    """Accept an IOS prompt that appears immediately after a password prompt."""
    from ccna_lab_builder.core.ssh import CiscoConsole

    if getattr(CiscoConsole, "_inline_prompt_parser_installed", False):
        return

    original = CiscoConsole._last_prompt

    def last_prompt(cls, text):
        prompt = original(text)
        if prompt:
            return prompt
        match = re.search(
            r"([A-Za-z0-9_.:/()\-]+[>#])\s*$",
            str(text or ""),
        )
        return match.group(1) if match else None

    CiscoConsole._last_prompt = classmethod(last_prompt)
    CiscoConsole._inline_prompt_parser_installed = True
