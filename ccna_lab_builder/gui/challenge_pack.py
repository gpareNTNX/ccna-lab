"""Isolated Cisco Challenge Labs UI plus EVE-NG VPCS support."""
from __future__ import annotations
import re, shlex, time, types, tkinter as tk
from tkinter import ttk
from ccna_lab_builder.core.builder import LabBuilder
from ccna_lab_builder.core.challenges import ChallengeCatalog
from ccna_lab_builder.core.live_validation import LiveValidator
from ccna_lab_builder.gui.console_workspace import ConsoleWorkspace
VERSION = "4.8.0"


def _install_vpcs_builder_support():
    current = LabBuilder._scenario_node_payload
    if getattr(current, "_vpcs_support", False): return
    def payload(spec, router_image, switch_image):
        if spec.get("template") != "vpcs": return current(spec, router_image, switch_image)
        return {"type":"vpcs","template":"vpcs","config":int(spec.get("config",0)),"delay":int(spec.get("delay",0)),"icon":spec.get("icon","Desktop.png"),"image":"","name":spec["name"],"left":str(spec.get("left","50%")),"top":str(spec.get("top","50%")),"ethernet":1}
    payload._vpcs_support = True
    LabBuilder._scenario_node_payload = staticmethod(payload)


def _vpcs_runtime_backend(validator, node_id):
    lab_uuid = str(getattr(validator, "_active_lab_uuid", "") or "")
    suffix = f"/{lab_uuid}/{int(node_id)}"
    cmd = "target="+shlex.quote(suffix)+"; for pid in $(pgrep -f '/opt/vpcsu/bin/vpcs|[[:space:]]vpcs[[:space:]]' 2>/dev/null); do cwd=$(readlink /proc/$pid/cwd 2>/dev/null || true); case \"$cwd\" in /opt/unetlab/tmp/*\"$target\") printf '__PID__=%s\\n__CWD__=%s\\n' \"$pid\" \"$cwd\"; exit 0;; esac; done"
    out, err = validator.ssh.exec(cmd)
    pid = cwd = ""
    for line in out.splitlines():
        if line.startswith("__PID__="): pid = line.split("=",1)[1]
        elif line.startswith("__CWD__="): cwd = line.split("=",1)[1]
    if not cwd:
        validator._runtime_note = f"No VPCS process cwd matched /opt/unetlab/tmp/*{suffix}. stderr={err.strip() or 'none'}"
        return None
    match = re.match(r"^/opt/unetlab/tmp/(\d+)/", cwd)
    if not match: return None
    pod = int(match.group(1)); port = 32768 + pod * 128 + int(node_id)
    if not validator.ssh.console_listener_info(port):
        validator._runtime_note = f"VPCS runtime {cwd} exists but console port {port} is not listening."
        return None
    validator.log(f"EVE VPCS runtime matched lab_uuid={lab_uuid}, node_id={node_id}, pid={pid}: 127.0.0.1:{port}")
    return {"kind":"tcp","host":"127.0.0.1","port":port,"source":"vpcs-runtime","lab_uuid":lab_uuid,"node_id":int(node_id),"pid":pid or "unknown","runtime_dir":cwd}


def _install_vpcs_console_support():
    current = LiveValidator._console_backend
    if getattr(current, "_vpcs_support", False): return
    def backend(self, lab, node_id, node_info=None, attempts=15, delay=1.0):
        if str((node_info or {}).get("template", "")).lower() != "vpcs":
            return current(self, lab, node_id, node_info=node_info, attempts=attempts, delay=delay)
        for attempt in range(max(1, attempts)):
            found = _vpcs_runtime_backend(self, node_id)
            if found: return found
            if attempt == 0:
                self.api.start_node(lab, node_id)
            if attempt < attempts - 1: time.sleep(delay)
        raise RuntimeError(f"No exact VPCS console backend available for node {node_id}. {getattr(self, '_runtime_note', '')}")
    backend._vpcs_support = True
    LiveValidator._console_backend = backend


def _install_vpcs_icon_support():
    current = ConsoleWorkspace._kind_for_node
    if getattr(current, "_challenge_vpcs_icon", False): return
    def kind(node):
        return "terminal" if str(node.get("template", "")).lower() == "vpcs" else current(node)
    kind._challenge_vpcs_icon = True
    ConsoleWorkspace._kind_for_node = staticmethod(kind)


def _lab_path(window, scenario):
    return window._scenario_lab_path(scenario)


def _render_topology(window, scenario):
    window.topology_canvas.set_topology(scenario["topology"], title=f"{scenario['id']} — {scenario['name']}", subtitle=f"Cisco Challenge • {scenario['difficulty']} • {scenario['minutes']} min")
    window._topology_mode = "scenario"


def _install_page(window):
    w=window; catalog=w.challenge_catalog
    w.t_challenges=ttk.Frame(w.page_host, style="Page.TFrame"); w.t_challenges.grid(row=0,column=0,sticky="nsew")
    head=ttk.Frame(w.t_challenges,style="Page.TFrame"); head.pack(fill="x",pady=(0,12))
    ttk.Label(head,text="Cisco Challenge Labs",style="Title.TLabel").pack(anchor="w")
    ttk.Label(head,text="Isolated EVE-NG adaptations • CCNA labs 01-37 stay unchanged",style="Muted.TLabel").pack(anchor="w",pady=(4,0))
    mode=tk.StringVar(value="CCNA CHALLENGES"); box=ttk.Combobox(head,textvariable=mode,state="readonly",values=("CCNA CHALLENGES","LEGACY / ADVANCED","PKT ARCHIVE"),width=22); box.pack(anchor="e",pady=(8,0))
    body=ttk.Frame(w.t_challenges,style="Page.TFrame"); body.pack(fill="both",expand=True); body.grid_columnconfigure(1,weight=1); body.grid_rowconfigure(0,weight=1)
    lst=tk.Listbox(body,width=35,bg=w.SURFACE,fg=w.TEXT,selectbackground=w.ACCENT_DARK,selectforeground="#fff",highlightthickness=0,bd=0,font=(w.font_family,10)); lst.grid(row=0,column=0,sticky="nsew",padx=(0,12))
    card=tk.Frame(body,bg=w.SURFACE,highlightbackground=w.BORDER,highlightthickness=1); card.grid(row=0,column=1,sticky="nsew")
    title=tk.Label(card,text="Select a challenge",bg=w.SURFACE,fg=w.TEXT,font=(w.font_family,16,"bold"),anchor="w"); title.pack(fill="x",padx=18,pady=(18,4))
    meta=tk.Label(card,text="",bg=w.SURFACE,fg=w.MUTED,font=(w.font_family,9),anchor="w"); meta.pack(fill="x",padx=18)
    text=tk.Text(card,wrap="word",state="disabled",bg=w.INPUT,fg=w.TEXT,relief="flat",bd=0,padx=14,pady=12,font=(w.font_family,10)); text.pack(fill="both",expand=True,padx=18,pady=14)
    controls=ttk.Frame(card,style="Card.TFrame"); controls.pack(fill="x",padx=18,pady=(0,18))
    create=ttk.Button(controls,text="CREATE / REBUILD CHALLENGE",style="Accent.TButton"); create.pack(side="right")
    topo=ttk.Button(controls,text="OPEN TOPOLOGY"); topo.pack(side="right",padx=6)
    valid=ttk.Button(controls,text="OPEN VALIDATOR"); valid.pack(side="right",padx=6)

    def entries():
        if mode.get()=="CCNA CHALLENGES": return catalog.all()
        status="legacy" if mode.get()=="LEGACY / ADVANCED" else None
        return [x for x in catalog.archive() if status is None or x["status"] in {"legacy","blocked","review"}]
    def refresh(*_):
        lst.delete(0,"end")
        for item in entries(): lst.insert("end", f"{item['id']}  {item['name']}")
        title.config(text="Select a challenge"); meta.config(text=""); create.config(state="disabled"); topo.config(state="disabled"); valid.config(state="disabled")
        text.config(state="normal"); text.delete("1.0","end"); text.config(state="disabled")
    def selected(*_):
        sel=lst.curselection()
        if not sel:return
        item=entries()[sel[0]]
        text.config(state="normal"); text.delete("1.0","end")
        if item.get("buildable"):
            w.current_challenge=item; w.current_scenario=item; title.config(text=f"{item['id']} — {item['name']}"); meta.config(text=f"{item['domain']} • {item['difficulty']} • {item['minutes']} min")
            text.insert("1.0",item["objective"]+"\n\nTASKS\n"+"\n".join(f"{i+1}. {t}" for i,t in enumerate(item["tasks"]))+"\n\nSOURCE BASIS\n"+", ".join(item["source_basis"]))
            w._set_validation_target(_lab_path(w,item)); _render_topology(w,item); create.config(state="normal"); topo.config(state="normal"); valid.config(state="normal")
        else:
            title.config(text=f"{item['id']} — {item['name']}"); meta.config(text=f"Migration state: {item['status'].upper()}"); text.insert("1.0","Reference-only Packet Tracer source. It is intentionally isolated from automatic EVE-NG generation until a safe IOSv/IOSvL2/VPCS adaptation exists."); create.config(state="disabled"); topo.config(state="disabled"); valid.config(state="disabled")
        text.config(state="disabled")
    def create_lab():
        if not getattr(w,"current_challenge",None): return
        w.current_scenario=w.current_challenge; w.bg(w.create_scenario_lab)
    def open_topo():
        if getattr(w,"current_challenge",None): _render_topology(w,w.current_challenge); w._nav_buttons["topology"].invoke()
    def open_valid(): w.show_page("validator")
    create.config(command=create_lab); topo.config(command=open_topo); valid.config(command=open_valid); box.bind("<<ComboboxSelected>>",refresh); lst.bind("<<ListboxSelect>>",selected); refresh()

    original=w.show_page
    def show_page(self,key):
        if key!="challenges": return original(key)
        self.t_challenges.tkraise(); self._current_page="challenges"; self.page_title.config(text="Cisco Challenge Labs")
        for k,b in self._nav_buttons.items(): b.configure(bg=self.SURFACE_ALT if k=="challenges" else self.SIDEBAR,fg=self.ACCENT if k=="challenges" else self.MUTED)
    w.show_page=types.MethodType(show_page,w)
    parent=w._nav_buttons["validator"].master; w._nav_button(parent,"challenges","★  Challenge Labs","Cisco Challenge Labs"); w._nav_buttons["challenges"].config(command=lambda:w.show_page("challenges"))


def install_challenge_pack(window):
    if getattr(window,"_challenge_pack_installed",False): return window
    _install_vpcs_builder_support(); _install_vpcs_console_support(); _install_vpcs_icon_support(); window.challenge_catalog=ChallengeCatalog(); window.current_challenge=None; _install_page(window); window._challenge_pack_installed=True
    try: window.winfo_toplevel().title(f"CCNA 200-301 EVE-NG Lab Builder v{VERSION}")
    except tk.TclError: pass
    return window
