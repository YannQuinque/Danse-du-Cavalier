import tkinter as tk
import tkinter.messagebox as messagebox

DEFAULT_ROWS = 8
DEFAULT_COLS = 8
SQUARE_SIZE = 60
LIGHT_COLOR = "#a6d489"
DARK_COLOR = "#07461b"
SOLUTION_START_COLOR = "#4a90e2"

root = tk.Tk()
root.title("Échiquier")

# Mode selection buttons
mode_frame = tk.Frame(root)
mode_frame.pack(pady=6)

def reset_game_confirm():
    if messagebox.askyesno("Confirmer", "Réinitialiser l'échiquier ?"):
        reset_game()

def select_mode(mode):
    global rows, cols, valid_squares, SQUARE_SIZE
    if mode == "8x8":
        rows, cols = 8, 8
        valid_squares = set((r, c) for r in range(rows) for c in range(cols))
        SQUARE_SIZE = 60
        root.title("Échiquier 8x8")
    elif mode == "4x3":
        # interpret 4x3 as 4 columns x 3 rows
        rows, cols = 3, 4
        valid_squares = set((r, c) for r in range(rows) for c in range(cols))
        SQUARE_SIZE = 90
        root.title("Échiquier 4x3")
    elif mode == "5x5":
        rows, cols = 5, 5
        valid_squares = set((r, c) for r in range(rows) for c in range(cols))
        SQUARE_SIZE = 90
        root.title("Échiquier 5x5")
    elif mode == "15":
        # 4x4 board with top-left corner removed
        rows, cols = 4, 4
        valid_squares = set((r, c) for r in range(rows) for c in range(cols))
        if (0, 0) in valid_squares:
            valid_squares.remove((0, 0))
        SQUARE_SIZE = 90
        root.title("Échiquier 15 cases")
    # resize canvas and redraw board
    canvas.config(width=cols * SQUARE_SIZE, height=rows * SQUARE_SIZE)
    try:
        size_scale.set(SQUARE_SIZE)
    except Exception:
        pass
    draw_board()
    reset_game()

# buttons
tk.Button(mode_frame, text="8x8", command=lambda: select_mode("8x8")).pack(side=tk.LEFT, padx=4)
tk.Button(mode_frame, text="4x3", command=lambda: select_mode("4x3")).pack(side=tk.LEFT, padx=4)
tk.Button(mode_frame, text="5x5", command=lambda: select_mode("5x5")).pack(side=tk.LEFT, padx=4)
tk.Button(mode_frame, text="15 cases", command=lambda: select_mode("15")).pack(side=tk.LEFT, padx=4)
# reset and undo buttons
reset_button = tk.Button(mode_frame, text="Reset", command=reset_game_confirm)
reset_button.pack(side=tk.LEFT, padx=8)
undo_button = tk.Button(mode_frame, text="Undo (Ctrl+Z)", command=lambda: undo_move())
undo_button.pack(side=tk.LEFT, padx=4)
solution_button = tk.Button(mode_frame, text="Solution OFF", command=lambda: toggle_solution_mode())
solution_button.pack(side=tk.LEFT, padx=4)

# current board dimensions (rows x cols)
rows = DEFAULT_ROWS
cols = DEFAULT_COLS

canvas = tk.Canvas(root, width=cols * SQUARE_SIZE, height=rows * SQUARE_SIZE)
canvas.pack()

# Control to adjust square size
def set_square_size(val):
    global SQUARE_SIZE
    # ignore manual changes when auto-fit is active
    try:
        if auto_fit_var.get():
            return
    except Exception:
        pass
    try:
        SQUARE_SIZE = int(val)
    except Exception:
        return
    canvas.config(width=cols * SQUARE_SIZE, height=rows * SQUARE_SIZE)
    draw_board()
    reset_game()

size_frame = tk.Frame(root)
size_frame.pack(pady=4)
size_scale = tk.Scale(size_frame, label="Taille case", from_=20, to=120, orient=tk.HORIZONTAL, command=set_square_size)
size_scale.set(SQUARE_SIZE)
size_scale.pack()

# Auto-fit checkbox
auto_fit_var = tk.BooleanVar(value=False)
def on_toggle_auto_fit():
    if auto_fit_var.get():
        # disable slider
        size_scale.config(state=tk.DISABLED)
        apply_auto_fit()
    else:
        size_scale.config(state=tk.NORMAL)

auto_fit_check = tk.Checkbutton(size_frame, text="Auto-fit", variable=auto_fit_var, command=on_toggle_auto_fit)
auto_fit_check.pack()

def apply_auto_fit():
    # compute available area inside root for the canvas
    try:
        root.update_idletasks()
        controls_h = mode_frame.winfo_height() + size_frame.winfo_height() + 40
        avail_w = max(100, root.winfo_width() - 40)
        avail_h = max(100, root.winfo_height() - controls_h)
        # choose square size to fit columns and rows
        new_size = max(20, min(avail_w // cols, avail_h // rows))
        global SQUARE_SIZE
        SQUARE_SIZE = new_size
        canvas.config(width=cols * SQUARE_SIZE, height=rows * SQUARE_SIZE)
        try:
            size_scale.set(SQUARE_SIZE)
        except Exception:
            pass
        draw_board()
        reset_game()
    except Exception:
        pass

def on_root_configure(event):
    if auto_fit_var.get():
        apply_auto_fit()

root.bind("<Configure>", on_root_configure)

# IDs for the knight drawing so we can remove it when placing a new one
knight_shape_id = None
knight_text_id = None
knight_image = None
knight_photo = None

# Board square IDs and colors so we can recolor squares (will be initialized in draw_board)
square_ids = []
original_colors = []

# Track visited squares (yellow) and current move highlights
visited = set()
current_move_positions = []
# history of moves in order (for undo)
move_history = []
# only allow one undo per new move
undo_used = False

# Current knight board position (row, col) or None
knight_pos = None

# set of valid squares (some modes may remove squares); initialized in select_mode/draw_board
valid_squares = set()

# Solution visualization state
solution_mode = False
solution_start_pos = None
solution_line_ids = []

# Try to load an image named 'knight.png' in the same folder. If not found, fallback to text.
try:
    knight_photo = tk.PhotoImage(file="knight.png")
except Exception:
    knight_photo = None

def draw_board():
    global square_ids, original_colors, valid_squares
    # clear canvas and (re)create square id arrays based on current rows/cols
    canvas.delete("all")
    square_ids = [[None for _ in range(cols)] for _ in range(rows)]
    original_colors = [[None for _ in range(cols)] for _ in range(rows)]
    # ensure valid_squares is initialized for current mode if empty
    if not valid_squares:
        for r in range(rows):
            for c in range(cols):
                valid_squares.add((r, c))

    for row in range(rows):
        for col in range(cols):
            x1 = col * SQUARE_SIZE
            y1 = row * SQUARE_SIZE
            x2 = x1 + SQUARE_SIZE
            y2 = y1 + SQUARE_SIZE
            if (row, col) in valid_squares:
                color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
            else:
                # inactive square (removed for specific modes)
                color = "#444444"
            rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            square_ids[row][col] = rect_id
            original_colors[row][col] = color

    if solution_mode:
        update_solution_visuals()


def solution_center(row, col):
    return col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2


def update_solution_visuals():
    global solution_start_pos, solution_line_ids
    # remove any existing solution path lines
    for line_id in solution_line_ids:
        try:
            canvas.delete(line_id)
        except Exception:
            pass
    solution_line_ids = []

    if not solution_mode:
        if solution_start_pos and solution_start_pos in visited:
            r, c = solution_start_pos
            canvas.itemconfig(square_ids[r][c], fill=visited_color(r, c))
        return

    if not move_history:
        return

    solution_start_pos = move_history[0]
    sr, sc = solution_start_pos
    if (sr, sc) in visited:
        canvas.itemconfig(square_ids[sr][sc], fill=SOLUTION_START_COLOR)

    for index in range(1, len(move_history)):
        r1, c1 = move_history[index - 1]
        r2, c2 = move_history[index]
        x1, y1 = solution_center(r1, c1)
        x2, y2 = solution_center(r2, c2)
        line_id = canvas.create_line(x1, y1, x2, y2, fill="#000000", width=3)
        solution_line_ids.append(line_id)


def set_solution_mode(on):
    global solution_mode
    solution_mode = on
    update_solution_visuals()
    try:
        solution_button.config(text="Solution ON" if on else "Solution OFF", relief=tk.SUNKEN if on else tk.RAISED)
    except Exception:
        pass


def toggle_solution_mode():
    set_solution_mode(not solution_mode)


def visited_color(row, col):
    # use a darker yellow for dark squares and a lighter yellow for light squares
    if (row + col) % 2 == 0:
        return "#fff59d"
    return "#f7c928"


def place_knight(row, col, record=True):
    global knight_shape_id, knight_text_id, knight_image, knight_pos, move_history, solution_start_pos
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

    # Prevent illegal moves from being applied when recording a new move
    if record and knight_pos is not None:
        allowed_moves = legal_moves(knight_pos[0], knight_pos[1])
        if (row, col) not in allowed_moves:
            return

    # Mark this square as visited (yellow) if it's a valid square
    if (row, col) in valid_squares:
        visited.add((row, col))
        canvas.itemconfig(square_ids[row][col], fill=visited_color(row, col))
        if record:
            is_first_move = len(move_history) == 0
            move_history.append((row, col))
            # allow one undo after this new move
            global undo_used
            undo_used = False
            try:
                undo_button.config(state=tk.NORMAL)
            except Exception:
                pass
            if solution_mode:
                if is_first_move:
                    solution_start_pos = (row, col)
                update_solution_visuals()
    # update current knight position
    knight_pos = (row, col)
    # After placing the knight, compute and display possible moves
    moves = legal_moves(row, col)
    show_move_markers(moves)
    # after showing moves, check for end condition
    check_end_condition(moves)

def on_canvas_click(event):
    col = event.x // SQUARE_SIZE
    row = event.y // SQUARE_SIZE
    if 0 <= col < cols and 0 <= row < rows:
        # If the knight is not yet placed, allow any initial placement.
        # Otherwise only allow the click if it's a legal knight move and not visited.
        if knight_pos is None:
            if (row, col) in valid_squares:
                place_knight(row, col)
        else:
            if (row, col) in visited:
                return
            allowed_moves = legal_moves(knight_pos[0], knight_pos[1])
            if (row, col) in allowed_moves:
                place_knight(row, col)

def undo_move():
    global move_history, visited, knight_pos, knight_shape_id, knight_text_id, undo_used
    if undo_used:
        return
    if not move_history:
        return
    # remove current position
    last = move_history.pop()
    if last in visited:
        visited.remove(last)
    # restore color of last square
    r, c = last
    try:
        canvas.itemconfig(square_ids[r][c], fill=original_colors[r][c])
    except Exception:
        pass
    # remove knight drawing
    if knight_shape_id is not None:
        canvas.delete(knight_shape_id)
        knight_shape_id = None
    if knight_text_id is not None:
        canvas.delete(knight_text_id)
        knight_text_id = None
    # if there is a previous move, place knight there without recording
    if move_history:
        prev = move_history[-1]
        pr, pc = prev
        # draw knight at previous pos without adding to history
        place_knight(pr, pc, record=False)
    else:
        # no moves left
        knight_pos = None
        clear_move_markers()
    if solution_mode:
        update_solution_visuals()
    undo_used = True
    try:
        undo_button.config(state=tk.DISABLED)
    except Exception:
        pass

def knight_moves(row, col):
    deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    moves = []
    for dr, dc in deltas:
        r = row + dr
        c = col + dc
        if (r, c) in valid_squares:
            moves.append((r, c))
    return moves


def legal_moves(row, col):
    return [move for move in knight_moves(row, col) if move not in visited]

def show_move_markers(moves):
    global current_move_positions
    current_move_positions = []
    for r, c in moves:
        # color the square red to indicate a possible move
        canvas.itemconfig(square_ids[r][c], fill="#e52626")
        current_move_positions.append((r, c))

def clear_move_markers():
    global current_move_positions
    for r, c in current_move_positions:
        # restore original color unless it's visited
        if (r, c) in visited:
            canvas.itemconfig(square_ids[r][c], fill=visited_color(r, c))
        else:
            canvas.itemconfig(square_ids[r][c], fill=original_colors[r][c])
    current_move_positions = []


def check_end_condition(moves):
    # moves: list of legal knight moves from current position
    # check whether any move is to an unvisited square
    unvisited = [m for m in moves if m not in visited]
    if not unvisited:
        if len(visited) == len(valid_squares):
            messagebox.showinfo("Gagné", "Le cavalier a visité toutes les cases !")
        else:
            messagebox.showinfo("Perdu", "Aucun coup possible — vous avez perdu.")
        # propose de rejouer
        if messagebox.askyesno("Rejouer?", "Voulez-vous recommencer ?"):
            reset_game()


def reset_game():
    global visited, knight_pos, knight_shape_id, knight_text_id, undo_used, solution_start_pos
    # clear visited
    visited.clear()
    # clear move history
    global move_history
    move_history.clear()
    undo_used = False
    solution_start_pos = None
    if solution_mode:
        update_solution_visuals()
    try:
        undo_button.config(state=tk.NORMAL)
    except Exception:
        pass
    # remove knight drawing
    if knight_shape_id is not None:
        canvas.delete(knight_shape_id)
        knight_shape_id = None
    if knight_text_id is not None:
        canvas.delete(knight_text_id)
        knight_text_id = None
    # restore board colors
    for r in range(rows):
        for c in range(cols):
            canvas.itemconfig(square_ids[r][c], fill=original_colors[r][c])
    # clear markers and reset position
    clear_move_markers()
    knight_pos = None


draw_board()
canvas.bind("<Button-1>", on_canvas_click)

# Keyboard shortcut: Ctrl+Z to undo
root.bind_all('<Control-z>', lambda e: undo_move())
root.bind_all('<Control-Z>', lambda e: undo_move())
# Redo shortcut removed

root.mainloop()
