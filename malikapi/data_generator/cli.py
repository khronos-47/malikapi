import argparse
from scenarios import scenario_basic

def main():
    parser = argparse.ArgumentParser("Data generator")
    parser.add_argument("--scenario", default="basic")
    parser.add_argument("--steps", type=int, default=100)
    args = parser.parse_args()

    if args.scenario == "basic":
        scenario_basic(steps=args.steps)
    else:
        raise ValueError("Unknown scenario")

if __name__ == "__main__":
    main()
