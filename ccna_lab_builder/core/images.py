from pathlib import Path
import re

def _slug(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return value or "custom"

def detect_image(path):
    p = Path(path)
    if not p.is_file():
        raise ValueError("Image file not found.")
    name = p.name
    low = name.lower()

    if "vios_l2" in low or "viosl2" in low:
        stem = re.sub(r"\.(qcow2?|img)$", "", name, flags=re.I)
        return {
            "kind": "IOSvL2",
            "template": "viosl2",
            "folder": "viosl2-" + _slug(stem.replace("vios_l2-", "").replace("viosl2-", "")),
            "disk": "virtioa.qcow2",
        }
    if "vios" in low and "l2" not in low:
        stem = re.sub(r"\.(qcow2?|img)$", "", name, flags=re.I)
        return {
            "kind": "IOSv",
            "template": "vios",
            "folder": "vios-" + _slug(stem.replace("vios-", "")),
            "disk": "virtioa.qcow2",
        }
    raise ValueError("Unsupported image. V4 currently imports IOSv and IOSvL2 QEMU images.")

def install_image(ssh, local_path, image, log=print):
    p = Path(local_path)
    remote = f"/opt/unetlab/addons/qemu/{image['folder']}"
    log(f"Creating {remote}")
    ssh.exec(f"mkdir -p '{remote}'")
    log(f"Uploading {p.name}...")
    ssh.upload(p, f"{remote}/{image['disk']}")
    out, err = ssh.exec("/opt/unetlab/wrappers/unl_wrapper -a fixpermissions")
    if err.strip():
        log("fixpermissions: " + err.strip())
    log(f"Installed: {image['folder']}")
    return image["folder"]
