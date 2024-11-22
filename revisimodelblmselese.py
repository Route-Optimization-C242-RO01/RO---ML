import requests
import numpy as np

def geocode_addresses(addresses, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    results = []
    coordinates = []  # Variabel untuk menyimpan hasil latitude dan longitude

    for address in addresses:
        params = {"address": address, "key": api_key}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK':
                location = data['results'][0]['geometry']['location']
                results.append({
                    "address": address,
                    "latitude": location['lat'],
                    "longitude": location['lng']
                })
                # Tambahkan latitude dan longitude ke dalam variabel coordinates
                coordinates.append(f"{location['lat']},{location['lng']}")
            else:
                results.append({
                    "address": address,
                    "error": data['status']
                })
        else:
            results.append({
                "address": address,
                "error": f"HTTP Error: {response.status_code}"
            })
    
    return results, coordinates

# Daftar alamat untuk di-geocode
addresses = [
    "Monumen Nasional, Jalan Tugu Monas, RT.5/RW.2, Gambir, Kecamatan Gambir, Kota Jakarta Pusat, Daerah Khusus Ibukota Jakarta 10110, Indonesia",
    "Museum Textile, Jl. Aipda Ks Tubun No 2-4, Kota Bambu Selatan, Palmerah, Kota Jakarta Barat, DKI Jakarta, Indonesia, 11420",
    "Chicken Popop Kemayoran, Jl. Haji Jiung, Kemayoran, Kemayoran, Kota Jakarta Pusat, Dki Jakarta, Indonesia, 10620",
    "Bank Syariah Mega Indonesia PT, Jalan Kh Hasyim Ashari 9, Petojo Utara, Gambir, Kota Jakarta Pusat, Dki Jakarta, Indonesia, 10130",
    "Jl. Kali Pasir No. 99, Cikini, Menteng, Kota Jakarta Pusat, Dki Jakarta, Indonesia, 10340",
    "Jl. Sangihe Dalam Blok B No. 15, Cideng, Gambir, Kota Jakarta Pusat, DKI Jakarta, Indonesia, 10150"
]

# API Key Anda
api_key = "AIzaSyB1byYrh8YOO9uLcnQMjUOSN8AjTTiOw58"

# Proses semua alamat
geocode_results, coordinates = geocode_addresses(addresses, api_key)

# Tampilkan hasil geocoding
for result in geocode_results:
    if "error" in result:
        print(f"Address: {result['address']}, Error: {result['error']}")
    else:
        print(f"Address: {result['address']}, Latitude: {result['latitude']}, Longitude: {result['longitude']}")

# Tampilkan koordinat yang tersimpan
print("\nKoordinat yang tersimpan:")
print(coordinates)

def calculate_distance_matrix(origins, destinations, api_key, mode="driving"):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": "|".join(origins),         # Gabungkan origins dengan tanda '|'
        "destinations": "|".join(destinations), # Gabungkan destinations dengan tanda '|'
        "key": api_key,
        "mode": mode,                       # Mode transportasi: driving, walking, bicycling, transit
        "departure_time": "now"
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            matrix = []
            for row in data['rows']:
                distances = []
                for element in row['elements']:
                    if element['status'] == 'OK':
                        distance_text = element['distance']['text']
                        distance_value = float(distance_text.replace(" km", "").replace(" m", ""))
                        distances.append(distance_value)
                    else:
                        distances.append("N/A")
                matrix.append(distances)
            return matrix, data['origin_addresses'], data['destination_addresses']
        else:
            return None, f"Error: {data['status']}"
    else:
        return None, f"HTTP Error: {response.status_code}"

matrix, origins, destinations = calculate_distance_matrix(coordinates, coordinates, api_key)

if matrix:
    # Tampilkan header matriks
    print("Distance Matrix (m):")
    print(" " * 20 + " | ".join(f"{dest[:20]}" for dest in destinations))
    print("-" * (25 + len(destinations) * 25))
    
    # Tampilkan isi matriks
    for origin, row in zip(origins, matrix):
        print(f"{origin[:20]:<20} | " + " | ".join(f"{dist:<10}" for dist in row))
else:
    print(f"Error: {destinations}")

print(matrix)

def create_data_model():
    data = {}
    data['distance_matrix'] = matrix
    data['demands'] = [0, 5, 8, 3, 7, 4]
    data["vehicle_capacities"] = [10, 10, 10]
    data["num_vehicles"] = 3
    data["depot"] = 0
    return data

def form_routes_with_warning(demands, capacities):
    """
    Membentuk rute awal dengan peringatan jika pelanggan tidak terlayani.
    """
    routes = []
    dropped_customers = []  # Pelanggan yang tidak terlayani
    served_customers = set()  # Set pelanggan yang sudah dilayani
    k = 0  # Kendaraan
    current_route = []
    current_capacity = capacities[k]

    for customer in range(1, len(demands)):
        if customer in served_customers:  # Abaikan pelanggan yang sudah dilayani
            continue
        if current_capacity >= demands[customer]:
            current_route.append(customer)
            current_capacity -= demands[customer]
            served_customers.add(customer)
        else:
            routes.append(current_route)
            k += 1
            if k >= len(capacities):  # Jika kendaraan habis, tandai pelanggan yang belum terlayani
                dropped_customers.append(customer)
            else:
                current_route = [customer]
                current_capacity = capacities[k] - demands[customer]
                served_customers.add(customer)

    if current_route:  # Tambahkan rute terakhir jika ada
        routes.append(current_route)

    return routes, dropped_customers

def validate_vehicle_capacities(routes, demands, capacities):
    """
    Validasi apakah total permintaan pelanggan dalam rute kendaraan melebihi kapasitas.
    """
    warnings = []
    for vehicle, route in enumerate(routes):
        total_demand = sum(demands[customer] for customer in route)
        if total_demand > capacities[vehicle]:
            warnings.append(
                f"Kendaraan {vehicle + 1}: Total permintaan pelanggan ({total_demand}) "
                f"melebihi kapasitas kendaraan ({capacities[vehicle]})."
            )
    return warnings

def levy_flight(routes, demands, capacities):
    """
    Menghasilkan rute baru menggunakan mekanisme Levy Flight dengan validasi unik pelanggan.
    """
    new_routes = [route.copy() for route in routes]
    # Pilih dua rute secara acak
    if len(new_routes) > 1:
        route1, route2 = np.random.choice(len(new_routes), 2, replace=False)
        # Tukar pelanggan secara acak antara dua rute
        if new_routes[route1] and new_routes[route2]:
            idx1 = np.random.randint(len(new_routes[route1]))
            idx2 = np.random.randint(len(new_routes[route2]))
            if new_routes[route2][idx2] not in new_routes[route1]:
                new_routes[route1][idx1], new_routes[route2][idx2] = (
                    new_routes[route2][idx2],
                    new_routes[route1][idx1],
                )
    return new_routes

def calculate_route_distance(routes, distance_matrix):
    """
    Menghitung jarak total per rute kendaraan.
    """
    total_distance = 0
    for route in routes:
        route_distance = 0
        prev_location = 0  # Mulai dari depot
        for customer in route:
            route_distance += distance_matrix[prev_location][customer]
            prev_location = customer
        route_distance += distance_matrix[prev_location][0]  # Kembali ke depot
        total_distance += route_distance
    return total_distance

def cuckoo_search_vrp(data, birds=10, discovery_rate=0.25, iterations=100):
    """
    Implementasi algoritma Cuckoo Search untuk VRP.
    """
    distance_matrix = data["distance_matrix"]
    demands = data["demands"]
    capacities = data["vehicle_capacities"]

    # Inisialisasi populasi solusi awal
    population = []
    dropped_customers_list = []
    for _ in range(birds):
        routes, dropped_customers = form_routes_with_warning(demands, capacities)
        population.append(routes)
        dropped_customers_list.append(dropped_customers)
    
    fitness = [calculate_route_distance(sol, distance_matrix) for sol in population]

    # Iterasi algoritma
    for iteration in range(1, iterations + 1):
        for i in range(birds):
            new_solution = levy_flight(population[i], demands, capacities)
            new_fitness = calculate_route_distance(new_solution, distance_matrix)
            if new_fitness < fitness[i]:
                population[i] = new_solution
                fitness[i] = new_fitness

        # Replace beberapa solusi secara acak
        num_replace = int(discovery_rate * birds)
        for _ in range(num_replace):
            idx = np.random.randint(birds)
            routes, dropped_customers = form_routes_with_warning(demands, capacities)
            population[idx] = routes
            fitness[idx] = calculate_route_distance(routes, distance_matrix)
            dropped_customers_list[idx] = dropped_customers

    # Cari solusi terbaik
    best_idx = np.argmin(fitness)
    best_solution = population[best_idx]
    best_distance = fitness[best_idx]

    return best_solution, best_distance

data = create_data_model()
best_solution, best_distance = cuckoo_search_vrp(data)
print("\nHasil Akhir:")
print("Solusi terbaik (rute kendaraan):")
for vehicle, route in enumerate(best_solution):
    print(f"  Kendaraan {vehicle + 1}: {route}")
print(f"Jarak total terbaik: {best_distance} km")

