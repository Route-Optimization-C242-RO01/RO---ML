import numpy as np
import random
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from collections import OrderedDict
import requests

app = Flask(__name__)
api = Api(app)


# Fungsi untuk memproses data JSON
def Convert_Json(data_json):
    Nama_Jalan = [item.get('Street', '') for item in data_json['data']]
    Kota = [item.get('City', '') for item in data_json['data']]
    Provinsi = [item.get('Province', '') for item in data_json['data']]
    Kapasitas = [int(item.get('Kg', 0)) for item in data_json['data']]
    Kode_Pos = [item.get('Postal_Code', '') for item in data_json['data']]
    Banyak_Kendaraan = data_json['Number_of_vehicles']

    Addresses = [f"{a},{b},{c}" for a, b, c in zip(Nama_Jalan, Kota, Provinsi)]
    return Addresses, Kapasitas, Banyak_Kendaraan, Nama_Jalan, Kota, Provinsi, Kode_Pos


def calculate_distance_matrix(origins, destinations, api_key, mode="driving"):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": "|".join(origins),  # Gabungkan origins dengan tanda '|'
        "destinations": "|".join(destinations),  # Gabungkan destinations dengan tanda '|'
        "key": api_key,
        "mode": mode,  # Mode transportasi: driving, walking, bicycling, transit
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
                        distance_value = float(distance_text.replace(",", "").replace(" km", "").replace(" m", ""))
                        distances.append(distance_value)
                    else:
                        distances.append("N/A")
                matrix.append(distances)
            return matrix, data['origin_addresses'], data['destination_addresses']
        else:
            return None, f"Error: {data['status']}"
    else:
        return None, f"HTTP Error: {response.status_code}"


def geocode_addresses(addresses, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    results = []
    coordinates = []
    Latitude = []
    Longitude = []

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
                coordinates.append(f"{location['lat']},{location['lng']}")
                Latitude.append(location['lat'])
                Longitude.append(location['lng'])
            else:
                results.append({"address": address, "error": data['status']})
        else:
            results.append({"address": address, "error": f"HTTP Error: {response.status_code}"})

    return results, coordinates, Latitude, Longitude


# matrix, origins, destinations = calculate_distance_matrix(coordinates, coordinates, api_key)

# if matrix:
#     # Tampilkan header matriks
#     print("Distance Matrix (m):")
#     print(" " * 20 + " | ".join(f"{dest[:20]}" for dest in destinations))
#     print("-" * (25 + len(destinations) * 25))

#     # Tampilkan isi matriks
#     for origin, row in zip(origins, matrix):
#         print(f"{origin[:20]:<20} | " + " | ".join(f"{dist:<10}" for dist in row))
# else:
#     print(f"Error: {destinations}")

# def create_data_model():
#     data = {}
#     data['distance_matrix'] = matrix
#     data['demands'] = Kapasitas
#     data["vehicle_capacities"] = 10 # Ini disesuaikan jadi berapa
#     data["num_vehicles"] = Banyak_Kendaraan
#     data["depot"] = 0
#     return data


def membangkitkan_populasi_awal(banyak_birds, banyak_pelanggan):
    birds = []
    for i in range(banyak_birds):
        bird = []
        for j in range(banyak_pelanggan):
            bird.append(random.uniform(0, 1))
        birds.append(bird)
    return birds


def mengurutkan_bilangan_permutasi(birds, banyak_birds, banyak_pelanggan):
    permutasi_birds = []
    for i in range(banyak_birds):
        permutasi_bird = []
        for j in range(banyak_pelanggan):
            k = 1
            for l in range(banyak_pelanggan):
                if birds[i][j] > birds[i][l]:
                    k = k + 1
            permutasi_bird.append(k)
        permutasi_birds.append(permutasi_bird)
    return permutasi_birds


def pembentukan_rute_vrp(permutasi_birds, data):
    routes = []
    max_capacity = data["vehicle_capacities"]
    num_vehicles = data["num_vehicles"]  # Jumlah kendaraan yang tersedia
    demands = data["demands"]  # Permintaan pelanggan

    for bird_index, permutasi_bird in enumerate(permutasi_birds):
        bird_routes = []  # Rute untuk satu bird
        current_route = []  # Rute sementara
        current_capacity = 0  # Kapasitas sementara
        vehicle_count = 1  # Kendaraan pertama
        visited_customers = set()  # Melacak pelanggan yang sudah dikunjungi

        for customer_index in permutasi_bird:
            # Jika pelanggan sudah dikunjungi, lewati
            if customer_index in visited_customers:
                continue

            # Tambahkan permintaan pelanggan ke rute saat ini
            demand = demands[customer_index]
            if current_capacity + demand > max_capacity:
                # Simpan rute jika kapasitas terlampaui atau kendaraan habis
                bird_routes.append(current_route)
                current_route = []  # Reset rute sementara
                current_capacity = 0  # Reset kapasitas
                vehicle_count += 1  # Gunakan kendaraan baru

                # Periksa jika kendaraan tidak cukup
                if vehicle_count > num_vehicles:
                    break

            # Tambahkan pelanggan ke rute saat ini
            current_route.append(customer_index)
            current_capacity += demand
            visited_customers.add(customer_index)  # Tandai pelanggan sebagai dikunjungi

        # Simpan rute terakhir jika masih ada pelanggan
        if current_route:
            bird_routes.append(current_route)

        # Periksa jika ada pelanggan yang belum dikunjungi
        remaining_customers = set(range(1, len(data["demands"]))) - visited_customers
        for customer in remaining_customers:
            # Tambahkan pelanggan yang belum dikunjungi ke rute baru
            if len(bird_routes) < num_vehicles:
                bird_routes.append([customer])
            else:
                bird_routes[-1].append(customer)  # Tambahkan ke rute terakhir jika kendaraan penuh

        routes.append(bird_routes)  # Simpan rute bird ini

    return routes


def menghitung_jarak_per_rute(routes, data):
    """
    Menghitung total jarak tempuh setiap rute (kendaraan) untuk setiap bird.
    """
    distance_matrix = data["distance_matrix"]  # Matriks jarak
    all_birds_distances = []  # Menyimpan total jarak tempuh untuk semua birds

    for bird_index, bird_routes in enumerate(routes):  # Iterasi setiap bird
        bird_distances = []  # Menyimpan jarak total untuk semua rute dalam satu bird

        for route in bird_routes:  # Iterasi setiap rute (kendaraan)
            total_distance = 0

            # Tambahkan jarak dari depot ke pelanggan pertama
            if route:
                total_distance += distance_matrix[0][route[0]]

            # Hitung jarak antar pelanggan dalam rute
            for i in range(len(route) - 1):
                total_distance += distance_matrix[route[i]][route[i + 1]]

            # Tambahkan jarak dari pelanggan terakhir kembali ke depot
            if route:
                total_distance += distance_matrix[route[-1]][0]

            bird_distances.append(total_distance)  # Simpan jarak total untuk rute ini

        all_birds_distances.append(bird_distances)  # Simpan jarak untuk semua rute dalam bird ini

    return all_birds_distances


def menghitung_jarak_total_birds(all_birds_distances):
    """
    Menghitung total jarak tempuh untuk setiap birds (fungsi tujuan).
    """
    total_distances = []  # Menyimpan jarak total untuk setiap birds

    for bird_distances in all_birds_distances:  # Iterasi setiap bird
        total_distance = sum(bird_distances)  # Total jarak adalah penjumlahan jarak semua rute
        total_distances.append(total_distance)  # Simpan total jarak untuk bird ini

    return total_distances


# Fungsi: Lévy Flight
def levy_flight(mean):
    u1 = np.random.uniform(-0.5 * np.pi, 0.5 * np.pi)
    u2 = np.random.uniform(-0.5 * np.pi, 0.5 * np.pi)
    v = np.random.uniform(0.0, 1.0)
    x1 = np.sin((mean - 1.0) * u1) / np.power(np.cos(u1), 1.0 / (mean - 1.0))
    x2 = np.power(np.cos((2.0 - mean) * u2) / (-np.log(v)), (2.0 - mean) / (mean - 1.0))
    return x1 * x2


# Fungsi: Replace Bird
def replace_bird(position, alpha_value, lambda_value, min_values, max_values, objective_function):
    random_bird = np.random.randint(position.shape[0])
    levy_values = levy_flight(lambda_value)
    new_solution = np.copy(position[random_bird, :-1])
    rand_factors = np.random.rand(len(min_values))
    new_solution = np.clip(new_solution + alpha_value * levy_values * new_solution * rand_factors, min_values,
                           max_values)
    new_fitness = objective_function(np.argsort(new_solution).astype(int) + 1)
    if new_fitness < position[random_bird, -1]:
        position[random_bird, :-1] = new_solution
        position[random_bird, -1] = new_fitness
    return position


# Fungsi: Update Positions
def update_positions(position, discovery_rate, min_values, max_values, objective_function):
    updated_position = np.copy(position)
    abandoned_nests = int(np.ceil(discovery_rate * position.shape[0])) + 1
    fitness_values = position[:, -1]
    nest_list = np.argsort(fitness_values)[-abandoned_nests:]
    random_birds = np.random.choice(position.shape[0], size=2, replace=False)
    bird_j, bird_k = random_birds
    for i in nest_list:
        rand = np.random.rand(updated_position.shape[1] - 1)
        if np.random.rand() > discovery_rate:
            updated_position[i, :-1] = np.clip(
                updated_position[i, :-1] + rand * (updated_position[bird_j, :-1] - updated_position[bird_k, :-1]),
                min_values, max_values)
    updated_position[:, -1] = [objective_function(np.argsort(bird[:-1]).astype(int) + 1) for bird in updated_position]
    return updated_position


def cetak_hasil(routes, data, all_birds_distances):
    """
    Mencetak rute per kendaraan dan statistik seperti total jarak dan load.
    Jika kendaraan melebihi kapasitas, tampilkan alert di bawah kendaraan tersebut.
    """
    demands = data["demands"]
    total_distance = 0
    total_load = 0
    max_capacity = data["vehicle_capacities"]

    print("\n=== Hasil Rute ===")
    for vehicle_idx, (route, distances) in enumerate(zip(routes, all_birds_distances[0])):
        # Lat = []
        # Long = []
        route_distance = distances  # Total jarak untuk kendaraan ini
        route_load = sum(demands[customer] for customer in route if customer != data["depot"])
        total_distance += route_distance
        total_load += route_load

        # Tampilkan rute untuk kendaraan ini (dengan depot di awal dan akhir)
        route_str = " -> ".join(
            f"{customer} Load({demands[customer]})" if customer != data["depot"] else f"{customer} Load(0)"
            for customer in [data["depot"]] + route + [data["depot"]]
        )
        # for customer in route :
        #     if customer != data['depot'] :
        #         Lat.append(Latitude[customer])
        #         Long.append(Longitude[customer])

        print(f"Route for vehicle {vehicle_idx}:")
        print(f"  {route_str}")
        print(f"  Distance of the route: {route_distance:.2f}m")
        print(f"  Load of the route: {route_load}")
        # print(f" Koordinat pelanggan secara berurutan(Latitude) : {Lat}")
        # print(f" Koordinat pelanggan secara berurutan(Longitude) : {Long}")

        # Jika load kendaraan melebihi kapasitas, tampilkan alert
        if route_load > max_capacity:
            print(f"  **ALERT**: Kapasitas kendaraan {vehicle_idx} ({route_load}) melebihi maksimum ({max_capacity})!")

    print(f"\nTotal Distance of all routes: {total_distance:.2f}m")
    print(f"Total Load of all routes: {total_load}")


# Fungsi Utama: VRP Cuckoo Search
def vrp_cuckoo_search(data, birds=10, iterations=100, alpha_value=0.01, lambda_value=1.5, discovery_rate=0.25):
    banyak_pelanggan = len(data['demands']) - 1
    birds_population = membangkitkan_populasi_awal(birds, banyak_pelanggan)
    permutasi_birds = mengurutkan_bilangan_permutasi(birds_population, birds, banyak_pelanggan)

    def objective_function(permutasi):
        routes = pembentukan_rute_vrp([permutasi], data)
        all_birds_distances = menghitung_jarak_per_rute(routes, data)
        total_distances = menghitung_jarak_total_birds(all_birds_distances)
        return total_distances[0]

    fitness_values = [objective_function(permutasi) for permutasi in permutasi_birds]
    population = np.hstack([np.array(birds_population), np.array(fitness_values)[:, np.newaxis]])

    best_individual = population[population[:, -1].argsort()][0, :]
    for count in range(iterations):
        # print(f"\n=== Iterasi {count + 1} ===")
        # print(f"Total Jarak (Fitness): {best_individual[-1]}")

        # Cetak rute per kendaraan dari solusi terbaik saat ini
        best_permutation = [int(p) + 1 for p in np.argsort(best_individual[:-1])]
        routes = pembentukan_rute_vrp([best_permutation], data)[0]
        all_birds_distances = menghitung_jarak_per_rute([routes], data)
        # cetak_hasil(routes, data, all_birds_distances)

        # Lévy flights dan replace bird
        for _ in range(birds):
            population = replace_bird(population, alpha_value, lambda_value, [0] * banyak_pelanggan,
                                      [1] * banyak_pelanggan, objective_function)
        population = update_positions(population, discovery_rate, [0] * banyak_pelanggan, [1] * banyak_pelanggan,
                                      objective_function)
        current_best = population[population[:, -1].argsort()][0, :]
        if best_individual[-1] > current_best[-1]:
            best_individual = np.copy(current_best)

    # Solusi terbaik di akhir iterasi
    best_permutation = [int(p) + 1 for p in np.argsort(best_individual[:-1])]
    best_distance = best_individual[-1]
    final_routes = pembentukan_rute_vrp([best_permutation], data)[0]
    final_all_birds_distances = menghitung_jarak_per_rute([final_routes], data)
    cetak_hasil(final_routes, data, final_all_birds_distances)
    return best_permutation, best_distance, final_routes


@app.route('/api/Solution', methods=['POST'])
def get_solution():
    # Mendapatkan data JSON dari request
    data_input = request.get_json()

    if not data_input:
        return jsonify({"error": "Invalid JSON"}), 400

    # Memproses data JSON
    addresses, Kapasitas, Banyak_Kendaraan, Nama_Jalan, Kota, Provinsi, Kode_Pos = Convert_Json(data_input)

    # API Key Anda
    api_key = "AIzaSyB1byYrh8YOO9uLcnQMjUOSN8AjTTiOw58"

    # Geocoding
    geocode_results, coordinates, Latitude, Longitude = geocode_addresses(addresses, api_key)

    # Hitung matriks jarak
    matrix, origins, destinations = calculate_distance_matrix(coordinates, coordinates, api_key)

    # Buat data model
    def create_data_model():
        data = {}
        data['distance_matrix'] = matrix
        data['demands'] = Kapasitas
        data["vehicle_capacities"] = 500  # Ini disesuaikan
        data["num_vehicles"] = Banyak_Kendaraan
        data["depot"] = 0
        return data

    data = create_data_model()

    # Optimalisasi VRP dengan Cuckoo Search
    best_solution, best_distance, final_routes = vrp_cuckoo_search(
        data, birds=10, iterations=100, alpha_value=0.01, lambda_value=1.5, discovery_rate=0.25
    )

    # Mengonversi solusi ke format JSON yang bisa dikembalikan
    Kendaraan = 0
    Hasil = {}
    depot_location = {
        "latitude": Latitude[0],
        "longitude": Longitude[0],
        "street": Nama_Jalan[0],
        "city": Kota[0],
        "province": Provinsi[0],
        "postal_code": Kode_Pos[0]
    }

    for sol in final_routes:
        Kendaraan += 1
        Rute = []
        Rute.append(depot_location)
        for pelanggan in sol:
            Location_Data = {
                "latitude": Latitude[pelanggan],
                "longitude": Longitude[pelanggan],
                "street": Nama_Jalan[pelanggan],
                "city": Kota[pelanggan],
                "province": Provinsi[pelanggan],
                "postal_code": Kode_Pos[pelanggan]
            }
            Rute.append(Location_Data)
        Rute.append(depot_location)
        Hasil[f"Kendaraan{Kendaraan}"] = Rute

    solution = OrderedDict({
        "Hasil": Hasil,
        "Total_Jarak_Ditempuh": best_distance
    })

    # Mengembalikan solusi dalam format JSON
    return jsonify(solution)


if __name__ == '__main__':
    app.run(debug=True)

