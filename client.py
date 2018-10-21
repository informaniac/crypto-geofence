import requests
import json
from phe import paillier

decimal_places = 3

outside_all_boundaries_x = 0
outside_all_boundaries_y = 0

# somewhere in kansas
inside_x_boundaries_x = 38.445804
inside_x_boundaries_y = -99.716238

# somewhere in new mexico
inside_y_boundaries_x = 35.982334
inside_y_boundaries_y = -105.473879

inside_colorado_x = 39.222653
inside_colorado_y = -105.343049

def normalize_deg_x(deg):
    return round((deg+90)*10**decimal_places)

def normalize_deg_y(deg):
    return round((deg+180)*10**decimal_places)

def evaluate_response(public_key, private_key, response):
    print('  evaluation of aligned geofence')
    # rebuild the encrypted numbers with our public key
    data = response.json()
    e_south_border_distance = paillier.EncryptedNumber(public_key, int(data['lat']))
    e_north_border_distance = paillier.EncryptedNumber(public_key, int(data['lat2']))
    e_west_border_distance = paillier.EncryptedNumber(public_key, int(data['lng']))
    e_east_border_distance = paillier.EncryptedNumber(public_key, int(data['lng2']))

    # decrypt the encrypted distances
    south_border_distance = private_key.decrypt(e_south_border_distance)
    north_border_distance = private_key.decrypt(e_north_border_distance)
    west_border_distance = private_key.decrypt(e_west_border_distance)
    east_border_distance = private_key.decrypt(e_east_border_distance)

    # evaluate the distances
    match_x = east_border_distance >= 0 and west_border_distance <= 0
    match_y = north_border_distance >= 0 and south_border_distance <= 0

    if match_x and match_y:
        print('    Position is in Colorado')
    elif match_x:
        print('    Position is in between longitude boundaries')
    elif match_y:
        print('    Position is in between latitude boundaries')
    else:
        print('    Position is elsewhere')

def evaluate_response_rotated(public_key, private_key, response):
    print('  evaluation of rotated geofence')
    data = response.json()
    e_AP_dot_AB = paillier.EncryptedNumber(public_key, int(data['e_AP_dot_AB']))
    e_AP_dot_AD = paillier.EncryptedNumber(public_key, int(data['e_AP_dot_AD']))
    AP_dot_AB = private_key.decrypt(e_AP_dot_AB)
    AP_dot_AD = private_key.decrypt(e_AP_dot_AD)

    sq_AB = int(data['sq_AB'])
    sq_AD = int(data['sq_AD'])

    border1_match = (0 <= AP_dot_AB <= sq_AB)
    border2_match = (0 <= AP_dot_AD <= sq_AD)

    if border1_match and border2_match:
        print('    Position is in Colorado')
    elif border1_match:
        print('    Position is inside one of the borders (border1)')
    elif border2_match:
        print('    Position is inside one of the borders (border2)')
    else:
        print('    Position is ouside Colorado')


def send_to_server(x, y, public_key):
    encrypted_lat = public_key.encrypt(normalize_deg_x(x))
    encrypted_lng = public_key.encrypt(normalize_deg_y(y))
    return requests.get("http://127.0.0.1:5000/calculate?g="+str(public_key.g)+"&n="+str(public_key.n)+"&lat="+str(encrypted_lat.ciphertext())+"&lng="+str(encrypted_lng.ciphertext()))

def send_to_server_rotated(x, y, public_key):
    encrypted_lat = public_key.encrypt(normalize_deg_x(x))
    encrypted_lng = public_key.encrypt(normalize_deg_y(y))
    return requests.get("http://127.0.0.1:5000/calculate_rotated?g="+str(public_key.g)+"&n="+str(public_key.n)+"&lat="+str(encrypted_lat.ciphertext())+"&lng="+str(encrypted_lng.ciphertext()))

if __name__ == '__main__':
    public_key, private_key = paillier.generate_paillier_keypair(n_length=1024)
    print('testing position outside all boundaries')
    response_outside = send_to_server(outside_all_boundaries_x, outside_all_boundaries_y, public_key)
    evaluate_response(public_key, private_key, response_outside)
    response_outside2 = send_to_server_rotated(outside_all_boundaries_x, outside_all_boundaries_y, public_key)
    evaluate_response_rotated(public_key, private_key, response_outside2)
    print('')

    print('testing position inside x boundaries')
    response_inside_x = send_to_server(inside_x_boundaries_x, inside_x_boundaries_y, public_key)
    evaluate_response(public_key, private_key, response_inside_x)
    response_inside_x2 = send_to_server_rotated(inside_x_boundaries_x, inside_x_boundaries_y, public_key)
    evaluate_response_rotated(public_key, private_key, response_inside_x2)
    print('')

    print('testing position inside y boundaries')
    response_inside_y = send_to_server(inside_y_boundaries_x, inside_y_boundaries_y, public_key)
    evaluate_response(public_key, private_key, response_inside_y)
    response_inside_y2 = send_to_server_rotated(inside_y_boundaries_x, inside_y_boundaries_y, public_key)
    evaluate_response_rotated(public_key, private_key, response_inside_y2)
    print('')

    print('testing position inside colorado')
    response_inside = send_to_server(inside_colorado_x, inside_colorado_y, public_key)
    evaluate_response(public_key, private_key, response_inside)
    response_inside2 = send_to_server_rotated(inside_colorado_x, inside_colorado_y, public_key)
    evaluate_response_rotated(public_key, private_key, response_inside2)

