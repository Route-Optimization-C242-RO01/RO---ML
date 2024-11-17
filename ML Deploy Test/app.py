from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)

# Array untuk menyimpan data
demand_array = [0]

def generate_initial_population(pop_size, num_customers):
    population = []
    for _ in range(pop_size):
        
        particle = np.random.permutation(num_customers) + 1  # Generate a random route excluding depot
        population.append(particle)
    return np.array(population)

# Route formation for VRP with capacity constraints
def form_routes(data, individual):
    routes = []
    vehicle_capacity = data["vehicle_capacities"]
    demand_data = data["demands"]
    depot = data["depot"]

    assigned_customers = set()
    idx = 0

    for vehicle_id in range(data["num_vehicles"]):
        route = [depot]
        load = 0
        while idx < len(individual):
            customer = individual[idx]
            if customer in assigned_customers:
                idx += 1
                continue

            demand = demand_data[customer]
            if load + demand <= vehicle_capacity[vehicle_id]:
                load += demand
                route.append(customer)
                assigned_customers.add(customer)
                idx += 1
            else:
                break

        route.append(depot)
        routes.append((route, load))

    unassigned_customers = [cust for cust in individual if cust not in assigned_customers]
    for customer in unassigned_customers:
        route = [depot, customer, depot]
        load = demand_data[customer]
        routes.append((route, load))

    return routes

# Calculate distance for each route
def calculate_route_distance(route, distance_matrix):
    distance = 0
    for i in range(len(route) - 1):
        distance += distance_matrix[route[i]][route[i + 1]]
    return distance

# Calculate fitness (total distance)
def calculate_fitness(data, individual):
    routes = form_routes(data, individual)
    total_distance = sum(calculate_route_distance(route[0], data["distance_matrix"]) for route in routes)
    return total_distance
# Function: Update best nest
def update_best_nest(position, fitness_values):
    best_idx = np.argmin(fitness_values)
    return position[best_idx], fitness_values[best_idx]

# Function: Cuckoo Search for VRP
def cuckoo_search(data, birds=20, discovery_rate=0.25, alpha_value=0.01, lambda_value=1.5, iterations=2000):
    num_customers = len(data["demands"]) - 1
    position = generate_initial_population(birds, num_customers)
    fitness_values = np.array([calculate_fitness(data, individual) for individual in position])

    best_position, best_fitness = update_best_nest(position, fitness_values)

    for iteration in range(iterations):
        # Replace random birds (solutions) with new solutions
        for i in range(birds):
            new_solution = np.copy(position[i])
            print(f"Length of new_solution: {len(new_solution)}")
            print(f"new_solution: {new_solution}")
            idx1, idx2 = np.random.choice(len(new_solution), 2, replace=False)
            new_solution[idx1], new_solution[idx2] = new_solution[idx2], new_solution[idx1]
            new_fitness = calculate_fitness(data, new_solution)
            if new_fitness < fitness_values[i]:
                position[i] = new_solution
                fitness_values[i] = new_fitness

        # Update positions by abandoning some nests based on discovery rate
        abandoned_nests = int(np.ceil(discovery_rate * birds))
        for _ in range(abandoned_nests):
            bird = np.random.randint(0, birds)
            new_solution = np.random.permutation(num_customers) + 1
            new_fitness = calculate_fitness(data, new_solution)
            if new_fitness < fitness_values[bird]:
                position[bird] = new_solution
                fitness_values[bird] = new_fitness

        # Update the best solution found so far
        current_best_position, current_best_fitness = update_best_nest(position, fitness_values)
        if current_best_fitness < best_fitness:
            best_position, best_fitness = current_best_position, current_best_fitness
    best_routes = form_routes(data, best_position)
    return best_routes, best_fitness

# Print detailed solution
def get_detailed_solution(data, routes, total_distance):
    total_load = 0
    solution_details = []  # To store the details for each vehicle

    for vehicle_id, (route, load) in enumerate(routes):
        route_distance = calculate_route_distance(route, data["distance_matrix"])
        route_load = 0
        vehicle_output = {
            "vehicle_id": vehicle_id + 1,
            "route": [],
            "route_distance": route_distance,
            "route_load": 0
        }

        for i in range(len(route) - 1):
            node = route[i]
            demand = data["demands"][node]
            route_load += demand
            vehicle_output["route"].append({"node": node, "load": route_load})

        vehicle_output["route"].append({"node": route[-1], "load": route_load})
        vehicle_output["route_distance"] = route_distance
        vehicle_output["route_load"] = route_load
        solution_details.append(vehicle_output)
        total_load += route_load

    return {
        "total_distance": total_distance,
        "total_load": total_load,
        "routes": solution_details
    }



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Ambil data input dari form
        user_input = request.form.get('input_field')
        
        # Simpan input ke dalam array
        if user_input and user_input.isdigit():
            demand_array.append(int(user_input))
        print("Current demands:", demand_array)

    return render_template('test.html', data=demand_array)


def create_data_model():
    if len(demand_array) <= 1:  # Only the depot is present
        raise ValueError("No valid customer demands provided! Please input customer demands.")
    data = {}
    data["distance_matrix"] = [
        [0, 548, 776, 696, 582, 274, 502, 194, 308, 194, 536, 502, 388, 354, 468, 776, 662],
      [548, 0, 684, 308, 194, 502, 730, 354, 696, 742, 1084, 594, 480, 674, 1016, 868, 1210],
      [776, 684, 0, 992, 878, 502, 274, 810, 468, 742, 400, 1278, 1164, 1130, 788, 1552, 754],
      [696, 308, 992, 0, 114, 650, 878, 502, 844, 890, 1232, 514, 628, 822, 1164, 560, 1358],
      [582, 194, 878, 114, 0, 536, 764, 388, 730, 776, 1118, 400, 514, 708, 1050, 674, 1244],
      [274, 502, 502, 650, 536, 0, 228, 308, 194, 240, 582, 776, 662, 628, 514, 1050, 708],
      [502, 730, 274, 878, 764, 228, 0, 536, 194, 468, 354, 1004, 890, 856, 514, 1278, 480],
      [194, 354, 810, 502, 388, 308, 536, 0, 342, 388, 730, 468, 354, 320, 662, 742, 856],
      [308, 696, 468, 844, 730, 194, 194, 342, 0, 274, 388, 810, 696, 662, 320, 1084, 514],
      [194, 742, 742, 890, 776, 240, 468, 388, 274, 0, 342, 536, 422, 388, 274, 810, 468],
      [536, 1084, 400, 1232, 1118, 582, 354, 730, 388, 342, 0, 878, 764, 730, 388, 1152, 354],
      [502, 594, 1278, 514, 400, 776, 1004, 468, 810, 536, 878, 0, 114, 308, 650, 274, 844],
      [388, 480, 1164, 628, 514, 662, 890, 354, 696, 422, 764, 114, 0, 194, 536, 388, 730],
      [354, 674, 1130, 822, 708, 628, 856, 320, 662, 388, 730, 308, 194, 0, 342, 422, 536],
      [468, 1016, 788, 1164, 1050, 514, 514, 662, 320, 274, 388, 650, 536, 342, 0, 764, 194],
      [776, 868, 1552, 560, 674, 1050, 1278, 742, 1084, 810, 1152, 274, 388, 422, 764, 0, 798],
      [662, 1210, 754, 1358, 1244, 708, 480, 856, 514, 468, 354, 844, 730, 536, 194, 798, 0]
    ]
    data["demands"] = demand_array
    data["vehicle_capacities"] = [15, 15, 15, 15]
    data["num_vehicles"] = 4
    data["depot"] = 0
    return data

@app.route('/optimize', methods=['POST'])
def optimize():
    data = create_data_model()
    best_routes, best_distance = cuckoo_search(data)
    solution  = get_detailed_solution(data, best_routes, best_distance)
    return render_template('optimize.html', solution=solution)

if __name__ == '__main__':
    app.run(debug=True)
print(demand_array)
