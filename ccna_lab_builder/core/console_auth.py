import re
import time


LAB_IOS_USERNAME = "admin"
LAB_IOS_PASSWORD = "CCNAadmin!"
LAB_ENABLE_SECRET = "CCNAenable!"


def install_console_auth():
    """Teach CiscoConsole to authenticate with the documented lab credentials."""
    from ccna_lab_builder.core.ssh import CiscoConsole

    if getattr(CiscoConsole, "_training_auth_installed", False):
        return

    def wait_for_prompt(self, timeout=90.0, pulse=2.0):
        deadline = time.monotonic() + timeout
        transcript = []
        username_sent = False
        login_password_sent = False

        while time.monotonic() < deadline:
            self.send("")
            remaining = max(0.05, deadline - time.monotonic())
            output = self.read_until_prompt(timeout=min(pulse, remaining))
            if output:
                transcript.append(output)

            prompt = self._last_prompt(output)
            if prompt:
                return prompt

            recent = "\n".join(transcript[-3:])
            lower = recent.lower()

            if "username:" in lower and not username_sent:
                self.send(LAB_IOS_USERNAME)
                username_sent = True
                response = self.read(0.25)
                if response:
                    transcript.append(response)
                if "password:" in response.lower() and not login_password_sent:
                    self.send(LAB_IOS_PASSWORD)
                    login_password_sent = True
                    response = self.read_until_prompt(
                        timeout=min(4.0, max(0.05, deadline - time.monotonic()))
                    )
                    if response:
                        transcript.append(response)
                    prompt = self._last_prompt(response)
                    if prompt:
                        return prompt
                continue

            if (
                re.search(r"password:\s*$", recent, re.IGNORECASE)
                and not login_password_sent
            ):
                self.send(LAB_IOS_PASSWORD)
                login_password_sent = True
                response = self.read_until_prompt(
                    timeout=min(4.0, max(0.05, deadline - time.monotonic()))
                )
                if response:
                    transcript.append(response)
                prompt = self._last_prompt(response)
                if prompt:
                    return prompt
                continue

            if "initial configuration dialog" in lower:
                self.send("no")
                response = self.read(
                    min(2.0, max(0.05, deadline - time.monotonic()))
                )
                if response:
                    transcript.append(response)
                prompt = self._last_prompt(response)
                if prompt:
                    return prompt

            if "press return" in lower:
                self.send("")

        tail = "\n".join(transcript[-3:]).strip()
        if len(tail) > 1200:
            tail = tail[-1200:]
        detail = tail or "<no IOS console text received>"
        raise RuntimeError(
            "IOS console connected, but authentication/boot did not reach an EXEC "
            f"prompt within {int(timeout)} seconds. Last console output: {detail}"
        )

    def ensure_privileged(self, timeout=90.0):
        boot_timeout = max(90.0, float(timeout))
        prompt = self.current_prompt(timeout=min(4.0, boot_timeout))
        if not prompt:
            prompt = self.wait_for_prompt(timeout=boot_timeout)

        if "(config" in prompt.lower():
            output = self.command("end", timeout=5.0)
            prompt = self._last_prompt(output) or self.current_prompt(timeout=5.0)

        if prompt and prompt.endswith(">"):
            self.drain()
            self.send("enable")
            output = self.read(0.35)
            next_prompt = self._last_prompt(output)
            if "password:" in output.lower():
                self.send(LAB_ENABLE_SECRET)
                output += self.read_until_prompt(timeout=5.0)
                next_prompt = self._last_prompt(output)
            elif not next_prompt:
                output += self.read_until_prompt(timeout=5.0)
                next_prompt = self._last_prompt(output)
            prompt = next_prompt

        if not prompt or not prompt.endswith("#") or "(config" in prompt.lower():
            raise RuntimeError(
                "Validator could not reach privileged EXEC mode using the documented "
                f"lab credentials. Current prompt: {prompt or 'unknown'}"
            )
        return prompt

    CiscoConsole.wait_for_prompt = wait_for_prompt
    CiscoConsole.ensure_privileged = ensure_privileged
    CiscoConsole._training_auth_installed = True
