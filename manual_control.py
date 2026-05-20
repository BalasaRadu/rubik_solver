import sys
import time
import serial
import kociemba

VALID_COLORS = {'W', 'G', 'Y', 'B', 'R', 'O'}
PORT_SERIAL = '/dev/ttyUSB0'
BAUD_RATE = 115200

ORIENTATIONS = [
    ("BLUE", "WHITE", "GREEN"),
    ("WHITE", "GREEN", "YELLOW"),
    ("GREEN", "YELLOW", "BLUE"),
    ("YELLOW", "BLUE", "WHITE"),
    ("BLUE", "RED", "GREEN"),
    ("BLUE", "ORANGE", "GREEN")
]

base_pos = 1
cube_pos = {'top': 'U', 'bottom': 'D', 'front': 'F', 'back': 'B', 'left': 'L', 'right': 'R'}
sequence = []

def get_face_input(left_color, face_color, right_color):
    print(f"\nCURRENT FACE: {left_color} - {face_color} - {right_color}")
    matrix = []
    for i in range(3):
        while True:
            row = input(f"Row {i + 1}: ").strip().upper()
            if len(row) == 3 and all(char in VALID_COLORS for char in row):
                matrix.append(row)
                break
            else:
                print(f"Error: Row must have 3 colors in {VALID_COLORS}.")
    return {
        "orientation": f"{left_color} - {face_color} - {right_color}",
        "face_color": face_color,
        "left_color": left_color,
        "right_color": right_color,
        "matrix": matrix
    }

def apply_flip():
    global cube_pos
    cube_pos['top'], cube_pos['back'], cube_pos['bottom'], cube_pos['front'] = \
        cube_pos['front'], cube_pos['top'], cube_pos['back'], cube_pos['bottom']
    sequence.extend(['flip', 'open'])

def apply_spin(direction):
    global base_pos, cube_pos
    if direction == 1:
        cube_pos['front'], cube_pos['left'], cube_pos['back'], cube_pos['right'] = \
            cube_pos['right'], cube_pos['front'], cube_pos['left'], cube_pos['back']
        if base_pos == 0:
            sequence.extend(['open', 'start'])
            base_pos = 1
        elif base_pos == 1:
            sequence.extend(['open', 'cw'])
            base_pos = 2
    elif direction == -1:
        cube_pos['front'], cube_pos['right'], cube_pos['back'], cube_pos['left'] = \
            cube_pos['left'], cube_pos['front'], cube_pos['right'], cube_pos['back']
        if base_pos == 2:
            sequence.extend(['open', 'start'])
            base_pos = 1
        elif base_pos == 1:
            sequence.extend(['open', 'ccw'])
            base_pos = 0

def move_to_bottom(logical_face):
    while True:
        pos = next(p for p, f in cube_pos.items() if f == logical_face)
        if pos == 'bottom':
            break
        elif pos == 'top':
            apply_flip()
        elif pos == 'front':
            apply_flip()
        elif pos == 'back':
            apply_flip()
        elif pos == 'left':
            if base_pos > 0:
                apply_spin(-1)
            else:
                apply_spin(1)
        elif pos == 'right':
            if base_pos < 2:
                apply_spin(1)
            else:
                apply_spin(-1)

def apply_face_turn(direction):
    global base_pos
    turns = [1] if direction == 1 else [-1] if direction == -1 else [1, 1]
    
    for turn in turns:
        base_move = -1 if turn == 1 else 1
        
        if base_move == 1 and base_pos == 2:
            apply_spin(-1)
        elif base_move == -1 and base_pos == 0:
            apply_spin(1)
            
        cmd = 'start' if (base_pos + base_move) == 1 else 'cw' if base_move == 1 else 'ccw'
        base_pos += base_move
        sequence.extend(['closed', cmd, 'open'])

def generate_robot_sequence(solution):
    global sequence, base_pos, cube_pos
    sequence = ['open']
    base_pos = 1
    cube_pos = {'top': 'U', 'bottom': 'D', 'front': 'F', 'back': 'B', 'left': 'L', 'right': 'R'}
    
    solution_moves = solution.split()
    for move in solution_moves:
        face = move[0]
        if len(move) > 1:
            if move[1] == "'":
                direction = -1
            elif move[1] == '2':
                direction = 2
        else:
            direction = 1
            
        move_to_bottom(face)
        apply_face_turn(direction)
            
    return sequence

def serial_connection():
    try:
        print(f"Connecting to {PORT_SERIAL}...")
        connection = serial.Serial()
        connection.port = PORT_SERIAL
        connection.baudrate = BAUD_RATE
        connection.timeout = 1
        connection.setDTR(False)
        connection.setRTS(False)
        connection.open()
        time.sleep(2)
        print("Successful connection!\n")
        return connection
    except serial.SerialException as e:
        print(f"Error while connecting to {PORT_SERIAL}.")
        print(f"Error: {e}")
        sys.exit(1)

def send_command(esp32, cmd):
    esp32.write((cmd + '\n').encode('utf-8'))
    print(f"-> trimis: {cmd}")
    
    time.sleep(0.1)
    while esp32.in_waiting > 0:
        answer = esp32.readline().decode('utf-8', errors='ignore').strip()
        if answer:
            print(f"[ESP32] {answer}")
            
    time.sleep(3)

def main():
    print("="*50)
    print("READING RUBIK'S CONFIGURATIONS")
    print("VALID COLORS: W, G, Y, B, R, O")
    print("="*50)

    cube_state = {}
    for left, face, right in ORIENTATIONS:
        face_data = get_face_input(left, face, right)
        cube_state[face] = face_data['matrix']

    color_to_facelet = {
        'R': 'U', 'G': 'R', 'W': 'F',
        'O': 'D', 'B': 'L', 'Y': 'B'
    }

    kociemba_matrices = {
        'U': cube_state['RED'],
        'R': cube_state['GREEN'],
        'F': cube_state['WHITE'],
        'D': cube_state['ORANGE'],
        'L': cube_state['BLUE'],
        'B': cube_state['YELLOW']
    }

    cube_string = ""
    for face in ['U', 'R', 'F', 'D', 'L', 'B']:
        for row in kociemba_matrices[face]:
            for color in row:
                cube_string += color_to_facelet[color]

    print("\n" + "="*50)
    print(f"KOCIEMBA STRING: {cube_string}")
    print("="*50)

    try:
        solution = kociemba.solve(cube_string)
        print(f"\nSOLUTION: {solution}")
    except Exception as e:
        print(f"\nERROR: Invalid cube configuration! {e}")
        sys.exit(1)

    robot_sequence = generate_robot_sequence(solution)
    print(f"\nROBOT SEQUENCE ({len(robot_sequence)} commands generated)")
    
    esp32 = serial_connection()
    
    print("\nStarting physical solving...\n")
    for cmd in robot_sequence:
        send_command(esp32, cmd)
        
    esp32.close()
    print("\nCUBE SOLVED!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram closed by user.")
        sys.exit(0)