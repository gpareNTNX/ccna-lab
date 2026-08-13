# Scenario V2 engine

Scenario V2 adds per-lab topologies and structured validation while keeping all legacy `contains` checks compatible.

## Design goals

- Create only the IOSv / IOSvL2 nodes required by the selected exercise.
- Keep topology, tasks and validation rules together in one scenario definition.
- Prefer state-aware checks over loose substring matching.
- Preserve human-readable remediation commands on failures.
- Keep lab access credentials standardized and documented in the GUI.

## Supported assertion types

`contains`, `not_contains`, `regex`, `ssh_enabled`, `interface_ipv4`, `vlan`, `ospf_neighbor`, `route`, `trunk`, `etherchannel`, `hsrp`, and `cdp_neighbor`.

Legacy checks using only `contains` are converted automatically.

## Topology format

```json
{
  "schema_version": 2,
  "topology": {
    "nodes": [
      {"name": "R1", "template": "vios", "left": "20%", "top": "40%"},
      {"name": "SW1", "template": "viosl2", "left": "60%", "top": "40%"}
    ],
    "links": [
      {"a": "R1", "a_if": "Gi0/0", "b": "SW1", "b_if": "Gi0/0"}
    ]
  }
}
```

Automatic cabling continues to use the existing EVE-NG interface API and remains controlled by the experimental cabling checkbox. When disabled, the Builder creates the exact node set and logs that links must be connected manually.

## Content policy

The additional labs in `scenarios_v2.json` are original scenarios written for this application. Public CCNA lab repositories may be used to identify useful topic coverage, but third-party exercise text, paid-course material, Packet Tracer files, images and solution text are not copied into this project.
