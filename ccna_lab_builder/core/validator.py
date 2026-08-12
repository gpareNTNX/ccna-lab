from dataclasses import dataclass

@dataclass
class CheckResult:
    node: str
    command: str
    passed: bool
    missing: list
    output: str

class Validator:
    @staticmethod
    def validate_output(check, output):
        upper = output.upper()
        missing = [token for token in check.get("contains", []) if token.upper() not in upper]
        return CheckResult(
            node=check["node"], command=check["command"],
            passed=not missing, missing=missing, output=output,
        )

    def validate_pasted(self, scenario, outputs):
        results = []
        for check in scenario.get("checks", []):
            key = (check["node"], check["command"])
            results.append(self.validate_output(check, outputs.get(key, "")))
        return results

    @staticmethod
    def score(results):
        if not results:
            return 0
        return round(100 * sum(1 for r in results if r.passed) / len(results))
