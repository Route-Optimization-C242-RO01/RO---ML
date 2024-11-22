import requests
import numpy as np
import random
import math


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
                if birds[i, j] > birds[i, l]:
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

        routes.append(bird_routes)  # Simpan rute hawk ini

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

def total_jarak_rute(routes, data, all_birds_distances):
