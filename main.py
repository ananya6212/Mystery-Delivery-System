import json
import math
import sys


# Calculate Euclidean distance between two points
def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    distance = math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )

    return distance


# Find the nearest agent using deterministic tie-breaking
def find_nearest_agent(
    package,
    agents,
    warehouses,
    current_locations,
    agent_stats
):
    warehouse_id = package["warehouse"]
    warehouse_location = warehouses[warehouse_id]

    nearest_agent = None
    shortest_distance = float("inf")

    for agent_id in agents:

        # Use the agent's current location
        agent_location = current_locations[agent_id]

        distance = calculate_distance(
            agent_location,
            warehouse_location
        )

        if distance < shortest_distance:
            shortest_distance = distance
            nearest_agent = agent_id

        elif distance == shortest_distance:
            # Tie-breaker 1:
            # Agent with fewer assigned packages wins
            current_agent_packages = agent_stats[agent_id]["packages_delivered"]
            nearest_agent_packages = agent_stats[nearest_agent]["packages_delivered"]

            if current_agent_packages < nearest_agent_packages:
                nearest_agent = agent_id

            # Tie-breaker 2:
            # If package counts are also equal,
            # smaller agent ID wins
            elif (
                current_agent_packages == nearest_agent_packages
                and agent_id < nearest_agent
            ):
                nearest_agent = agent_id

    return nearest_agent


# Simulate one package delivery
def simulate_delivery(
    package,
    agent_id,
    current_locations,
    warehouses
):
    # Agent starts from its CURRENT location
    agent_location = current_locations[agent_id]

    warehouse_location = warehouses[
        package["warehouse"]
    ]

    destination = package["destination"]

    # Agent travels to the warehouse
    distance_to_warehouse = calculate_distance(
        agent_location,
        warehouse_location
    )

    # Agent travels from warehouse to destination
    distance_to_destination = calculate_distance(
        warehouse_location,
        destination
    )

    # Total distance for this package
    total_distance = (
        distance_to_warehouse +
        distance_to_destination
    )

    return total_distance


# Validate input data
def validate_data(data):

    # Required top-level fields
    required_fields = [
        "warehouses",
        "agents",
        "packages"
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(
                f"Missing required field: {field}"
            )

    # Validate warehouses
    if not isinstance(data["warehouses"], dict):
        raise ValueError(
            "'warehouses' must be an object"
        )

    # Validate agents
    if not isinstance(data["agents"], dict):
        raise ValueError(
            "'agents' must be an object"
        )

    # Validate packages
    if not isinstance(data["packages"], list):
        raise ValueError(
            "'packages' must be a list"
        )

    # Make sure every package refers to an existing warehouse
    for package in data["packages"]:

        if "warehouse" not in package:
            raise ValueError(
                f"Package {package.get('id', 'unknown')} "
                "is missing 'warehouse'"
            )

        warehouse_id = package["warehouse"]

        if warehouse_id not in data["warehouses"]:
            raise ValueError(
                f"Package {package.get('id', 'unknown')} "
                f"refers to unknown warehouse: {warehouse_id}"
            )

        if "destination" not in package:
            raise ValueError(
                f"Package {package.get('id', 'unknown')} "
                "is missing 'destination'"
            )


# Build the complete report
def build_report(data):

    # Validate input before processing
    validate_data(data)

    warehouses = data["warehouses"]
    agents = data["agents"]
    packages = data["packages"]

    # Store delivery statistics for each agent
    agent_stats = {}

    for agent_id in agents:
        agent_stats[agent_id] = {
            "packages_delivered": 0,
            "total_distance": 0
        }

    # ⭐ Stateful agent locations
    # Each agent initially starts at its original position
    current_locations = agents.copy()

    # Process every package
    for package in packages:

        # Find nearest agent based on CURRENT location
        agent_id = find_nearest_agent(
            package,
            agents,
            warehouses,
            current_locations,
            agent_stats
        )

        # Calculate delivery distance
        distance = simulate_delivery(
            package,
            agent_id,
            current_locations,
            warehouses
        )

        # Update agent statistics
        agent_stats[agent_id]["packages_delivered"] += 1
        agent_stats[agent_id]["total_distance"] += distance

        # ⭐ Stateful update
        # Agent now finishes at the package destination
        current_locations[agent_id] = package["destination"]

    # Calculate efficiency for each agent
    for agent_id, stats in agent_stats.items():

        if stats["packages_delivered"] > 0:
            stats["efficiency"] = (
                stats["total_distance"] /
                stats["packages_delivered"]
            )
        else:
            stats["efficiency"] = 0

    # Only agents who delivered packages can be best_agent
    eligible_agents = {
        agent_id: stats
        for agent_id, stats in agent_stats.items()
        if stats["packages_delivered"] > 0
    }

    if eligible_agents:
        best_agent = min(
            eligible_agents,
            key=lambda agent_id:
                eligible_agents[agent_id]["efficiency"]
        )
    else:
        best_agent = None

    # Create agent report
    report = {}

    for agent_id, stats in agent_stats.items():
        report[agent_id] = {
            "packages_delivered": stats["packages_delivered"],
            "total_distance": round(
                stats["total_distance"],
                2
            ),
            "efficiency": round(
                stats["efficiency"],
                2
            )
        }

    # ⭐ Overall summary
    total_packages = len(packages)

    delivered_packages = sum(
        stats["packages_delivered"]
        for stats in agent_stats.values()
    )

    total_distance = sum(
        stats["total_distance"]
        for stats in agent_stats.values()
    )

    if delivered_packages > 0:
        average_distance = (
            total_distance /
            delivered_packages
        )
    else:
        average_distance = 0

    report["best_agent"] = best_agent

    report["summary"] = {
        "total_packages": total_packages,
        "delivered_packages": delivered_packages,
        "total_distance": round(
            total_distance,
            2
        ),
        "average_distance": round(
            average_distance,
            2
        )
    }

    return report


def main():

    # Accept input/output paths as CLI arguments
    #
    # Example:
    # python main.py data.json report.json

    input_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "data.json"
    )

    output_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "report.json"
    )

    try:

        # Read input data
        with open(input_path, "r") as file:
            data = json.load(file)

        # Build report
        report = build_report(data)

        print("\nFinal Report:")
        print(
            json.dumps(
                report,
                indent=4
            )
        )

        # Save report
        with open(output_path, "w") as file:
            json.dump(
                report,
                file,
                indent=4
            )

        print(
            f"\nReport saved successfully to {output_path}"
        )

    except FileNotFoundError:
        print(
            f"Error: Input file '{input_path}' was not found."
        )

    except json.JSONDecodeError:
        print(
            f"Error: '{input_path}' contains invalid JSON."
        )

    except ValueError as error:
        print(f"Validation Error: {error}")


if __name__ == "__main__":
    main()