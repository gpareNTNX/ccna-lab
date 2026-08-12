# Validation engine

## Live mode

Select a scenario in **Training Labs**, start the relevant EVE-NG nodes, then open **Validator**.

Enter the `.unl` path, for example:

```text
/CCNA-200-301/CCNA-10-OSPF.unl
```

Click **VALIDATE LIVE**.

Example result:

```text
Score: 100%

PASS | R2-HQ | show ip ospf neighbor
PASS | R3-HQ | show ip protocols
```

## How checks work

A check is intentionally simple and transparent:

```json
{
  "node": "R2-HQ",
  "command": "show ip ospf neighbor",
  "contains": ["FULL"]
}
```

This is not a formal Cisco configuration parser. It is a practice validator designed to answer: *does the operational output demonstrate the expected state?*

## Safety

The live validator sends only the scenario's `show` commands. It does not enter configuration mode.
