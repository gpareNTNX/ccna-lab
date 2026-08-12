import argparse
from ccna_lab_builder.core.scenarios import ScenarioCatalog

def main():
    parser = argparse.ArgumentParser(description="CCNA EVE Lab Builder utilities")
    parser.add_argument("--list-labs", action="store_true")
    args = parser.parse_args()
    if args.list_labs:
        for lab in ScenarioCatalog().all():
            print(f"{lab['id']}  {lab['name']:<28} {lab['domain']}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
