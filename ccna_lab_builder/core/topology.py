import uuid

NODES = {
    "R1-EDGE":    {"template":"vios",   "left":"12%", "top":"17%", "interfaces":8},
    "R2-HQ":      {"template":"vios",   "left":"34%", "top":"17%", "interfaces":8},
    "R3-HQ":      {"template":"vios",   "left":"57%", "top":"17%", "interfaces":8},
    "R4-BRANCH":  {"template":"vios",   "left":"75%", "top":"47%", "interfaces":8},
    "R5-ISP":     {"template":"vios",   "left":"84%", "top":"17%", "interfaces":8},
    "SW1-CORE":   {"template":"viosl2", "left":"34%", "top":"40%", "interfaces":8},
    "SW2-DIST":   {"template":"viosl2", "left":"57%", "top":"40%", "interfaces":8},
    "SW3-ACCESS": {"template":"viosl2", "left":"26%", "top":"70%", "interfaces":8},
    "SW4-BRANCH": {"template":"viosl2", "left":"68%", "top":"70%", "interfaces":8},
}

LINKS = [
    ("R1-EDGE", "Gi0/0", "R2-HQ", "Gi0/0"),
    ("R2-HQ", "Gi0/1", "R3-HQ", "Gi0/0"),
    ("R3-HQ", "Gi0/1", "R4-BRANCH", "Gi0/0"),
    ("R1-EDGE", "Gi0/1", "R5-ISP", "Gi0/0"),
    ("R2-HQ", "Gi0/2", "SW1-CORE", "Gi0/0"),
    ("R3-HQ", "Gi0/2", "SW2-DIST", "Gi0/0"),
    ("SW1-CORE", "Gi0/1", "SW2-DIST", "Gi0/1"),
    ("SW1-CORE", "Gi0/2", "SW3-ACCESS", "Gi0/0"),
    ("SW2-DIST", "Gi0/2", "SW4-BRANCH", "Gi0/0"),
    ("R4-BRANCH", "Gi0/1", "SW4-BRANCH", "Gi0/1"),
]

def node_payload(name, router_image, switch_image):
    spec = NODES[name]
    template = spec["template"]
    return {
        "type": "qemu",
        "template": template,
        "config": "Unconfigured",
        "delay": 0,
        "icon": "Switch.png" if template == "viosl2" else "Router.png",
        "image": switch_image if template == "viosl2" else router_image,
        "name": name,
        "left": spec["left"],
        "top": spec["top"],
        "ram": "1024",
        "console": "telnet",
        "cpu": 1,
        "ethernet": spec["interfaces"],
        "uuid": str(uuid.uuid4()),
    }

def all_node_payloads(router_image, switch_image):
    return [node_payload(name, router_image, switch_image) for name in NODES]
