import tkinter as tk
import tkinter.messagebox as messagebox

BOARD_SIZE = 8
SQUARE_SIZE = 60
LIGHT_COLOR = "#a6d489"
DARK_COLOR = "#07461b"

root = tk.Tk()
root.title("Échiquier 8x8")

canvas = tk.Canvas(root, width=BOARD_SIZE * SQUARE_SIZE, height=BOARD_SIZE * SQUARE_SIZE)
canvas.pack()

# IDs for the knight drawing so we can remove it when placing a new one
knight_shape_id = None
knight_text_id = None
knight_image = None
knight_photo = None

# Board square IDs and colors so we can recolor squares
square_ids = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
original_colors = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

# Track visited squares (yellow) and current move highlights
visited = set()
current_move_positions = []

# Current knight board position (row, col) or None
knight_pos = None

# Try to load an image named 'knight.png' in the same folder. If not found, fallback to text.
try:
    knight_photo = tk.PhotoImage(file="knight.png")
except Exception:
    knight_photo = None

def draw_board():
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            x1 = col * SQUARE_SIZE
            y1 = row * SQUARE_SIZE
            x2 = x1 + SQUARE_SIZE
            y2 = y1 + SQUARE_SIZE
            color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
            rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            square_ids[row][col] = rect_id
            original_colors[row][col] = color

def place_knight(row, col):
    global knight_shape_id, knight_text_id, knight_image, knight_pos
    # Remove previous knight if any
    if knight_shape_id is not None:
        canvas.delete(knight_shape_id)
        knight_shape_id = None
    if knight_text_id is not None:
        canvas.delete(knight_text_id)
        knight_text_id = None
    # Remove previous move highlights
    clear_move_markers()

    x_center = col * SQUARE_SIZE + SQUARE_SIZE // 2
    y_center = row * SQUARE_SIZE + SQUARE_SIZE // 2
    if knight_photo:
        # keep reference to the image to prevent GC
        knight_image = knight_photo
        knight_shape_id = canvas.create_image(x_center, y_center, image=knight_image)
    else:
        r = SQUARE_SIZE // 3
        knight_shape_id = canvas.create_oval(x_center - r, y_center - r, x_center + r, y_center + r, fill="#ffffff", outline="#000000")
        knight_text_id = canvas.create_text(x_center, y_center, text="♞", font=("Helvetica", int(SQUARE_SIZE/2)), fill="#000000")

    # Mark this square as visited (yellow)
    visited.add((row, col))
    canvas.itemconfig(square_ids[row][col], fill="#f9e426")

    # update current knight position
    knight_pos = (row, col)

    # After placing the knight, compute and display possible moves
    moves = knight_moves(row, col)
    show_move_markers(moves)
    # after showing moves, check for end condition
    check_end_condition(moves)

def on_canvas_click(event):
    col = event.x // SQUARE_SIZE
    row = event.y // SQUARE_SIZE
    if 0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE:
        # If the knight is not yet placed, allow any initial placement.
        # Otherwise only allow the click if it's a legal knight move and not visited.
        if knight_pos is None:
            place_knight(row, col)
        else:
            allowed = ((row, col) in knight_moves(knight_pos[0], knight_pos[1])) and ((row, col) not in visited)
            if allowed:
                place_knight(row, col)

def knight_moves(row, col):
    deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    moves = []
    for dr, dc in deltas:
        r = row + dr
        c = col + dc
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            moves.append((r, c))
    return moves

def show_move_markers(moves):
    global current_move_positions
    current_move_positions = []
    for r, c in moves:
        # color the square red to indicate a possible move
        # don't override visited color (yellow) — visited should stay yellow
        if (r, c) not in visited:
            canvas.itemconfig(square_ids[r][c], fill="#e52626")
        current_move_positions.append((r, c))

def clear_move_markers():
    global current_move_positions
    for r, c in current_move_positions:
        # restore original color unless it's visited
        if (r, c) in visited:
            canvas.itemconfig(square_ids[r][c], fill="#f9e426")
        else:
            canvas.itemconfig(square_ids[r][c], fill=original_colors[r][c])
    current_move_positions = []


def check_end_condition(moves):
    # moves: list of legal knight moves from current position
    # check whether any move is to an unvisited square
    unvisited = [m for m in moves if m not in visited]
    if not unvisited:
        if len(visited) == BOARD_SIZE * BOARD_SIZE:
            messagebox.showinfo("Gagné", "Le cavalier a visité toutes les cases !")
        else:
            messagebox.showinfo("Perdu", "Aucun coup possible — vous avez perdu.")
        # propose de rejouer
        if messagebox.askyesno("Rejouer?", "Voulez-vous recommencer ?"):
            reset_game()


def reset_game():
    global visited, knight_pos, knight_shape_id, knight_text_id
    # clear visited
    visited.clear()
    # remove knight drawing
    if knight_shape_id is not None:
        canvas.delete(knight_shape_id)
    if knight_text_id is not None:
        canvas.delete(knight_text_id)
    # restore board colors
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            canvas.itemconfig(square_ids[r][c], fill=original_colors[r][c])
    # clear markers and reset position
    clear_move_markers()
    knight_pos = None


draw_board()
canvas.bind("<Button-1>", on_canvas_click)

root.mainloop()
