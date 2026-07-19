WIDTH = 1000
HEIGHT = 700
TITLE = "Orbital Miner"

CELL = 72
LEFT = 104
TOP = 112
COLUMNS = 11
ROWS = 7

BACKGROUND = (3, 8, 25)
PANEL = (12, 25, 52)
TEXT = (232, 247, 255)
ACCENT = (54, 199, 255)
BUTTON = (23, 63, 105)


def cell_center(cell):
    column, row = cell
    return (
        LEFT + column * CELL + CELL / 2,
        TOP + row * CELL + CELL / 2,
    )


class AnimatedCharacter:
    def __init__(
        self,
        cell,
        idle_name,
        move_name,
        idle_count=2,
    ):
        self.cell = cell
        self.start_cell = cell
        self.target_cell = cell

        self.idle_frames = [
            f"{idle_name}_{index}"
            for index in range(idle_count)
        ]
        self.move_frames = [
            f"{move_name}_{index}"
            for index in range(4)
        ]

        self.actor = Actor(
            self.idle_frames[0],
            cell_center(cell),
        )

        self.frame = 0
        self.frame_timer = 0.0
        self.progress = 0.0
        self.is_moving = False

    def move_to(self, cell):
        self.start_cell = self.cell
        self.target_cell = cell
        self.progress = 0.0
        self.is_moving = True
        self.frame = 0
        self.frame_timer = 0.0
        self.actor.image = self.move_frames[0]

    def update(self, dt):
        finished = False

        if self.is_moving:
            self.progress = min(
                1.0,
                self.progress + dt / 0.22,
            )

            amount = self.progress
            amount = amount * amount * (
                3 - 2 * amount
            )

            start_x, start_y = cell_center(
                self.start_cell
            )
            end_x, end_y = cell_center(
                self.target_cell
            )

            self.actor.pos = (
                start_x
                + (end_x - start_x) * amount,
                start_y
                + (end_y - start_y) * amount,
            )

            if self.progress == 1:
                self.cell = self.target_cell
                self.actor.pos = cell_center(
                    self.cell
                )
                self.is_moving = False
                self.frame = 0
                self.actor.image = (
                    self.idle_frames[0]
                )
                finished = True

        if self.is_moving:
            frames = self.move_frames
            frame_time = 0.09
        else:
            frames = self.idle_frames
            frame_time = 0.25

        self.frame_timer += dt

        if self.frame_timer >= frame_time:
            self.frame_timer = 0.0
            self.frame = (
                self.frame + 1
            ) % len(frames)
            self.actor.image = frames[self.frame]

        return finished


class Astronaut(AnimatedCharacter):
    def __init__(self, cell):
        super().__init__(
            cell,
            "astronaut_idle",
            "astronaut_fly",
            4,
        )

        self.health = 3
        self.collected = 0


class Enemy(AnimatedCharacter):
    def __init__(
        self,
        enemy_type,
        route,
    ):
        super().__init__(
            route[0],
            f"{enemy_type}_idle",
            f"{enemy_type}_move",
        )

        self.route = route
        self.route_index = 0

    def take_turn(self):
        self.route_index = (
            self.route_index + 1
        ) % len(self.route)

        self.move_to(
            self.route[self.route_index]
        )


class OrbitalMinerGame:
    def __init__(self):
        self.state = "menu"
        self.sound_enabled = True

        self.start_button = Rect(
            350,
            290,
            300,
            62,
        )
        self.sound_button = Rect(
            350,
            370,
            300,
            62,
        )
        self.exit_button = Rect(
            350,
            450,
            300,
            62,
        )

        self.reset_world()
        music.play("space_theme")

    def reset_world(self):
        self.ship_cell = (0, 6)

        self.ship = Actor(
            "spaceship_closed",
            cell_center(self.ship_cell),
        )

        self.astronaut = Astronaut((1, 6))

        mineral_cells = [
            (2, 1),
            (5, 5),
            (8, 1),
            (9, 5),
        ]

        self.minerals = {
            cell: Actor(
                "asteroid_0",
                cell_center(cell),
            )
            for cell in mineral_cells
        }

        satellite_route = [
            (1, 3),
            (2, 3),
            (3, 3),
            (4, 3),
            (5, 3),
            (4, 3),
            (3, 3),
            (2, 3),
        ]

        rocket_route = [
            (7, 2),
            (8, 2),
            (9, 2),
            (10, 2),
            (10, 3),
            (10, 4),
            (9, 4),
            (8, 4),
            (7, 4),
            (7, 3),
        ]

        self.enemies = [
            Enemy(
                "satellite",
                satellite_route,
            ),
            Enemy(
                "rocket",
                rocket_route,
            ),
        ]

    def play_sound(self, name):
        if self.sound_enabled:
            getattr(sounds, name).play()

    def start_game(self):
        self.reset_world()
        self.state = "playing"
        self.play_sound("menu_click")

    def toggle_sound(self):
        self.sound_enabled = (
            not self.sound_enabled
        )

        if self.sound_enabled:
            music.play("space_theme")
            self.play_sound("menu_click")
        else:
            music.stop()

    def move_player(self, key):
        if self.state != "playing":
            return

        if self.astronaut.is_moving:
            return

        directions = {
            keys.LEFT: (-1, 0),
            keys.A: (-1, 0),
            keys.RIGHT: (1, 0),
            keys.D: (1, 0),
            keys.UP: (0, -1),
            keys.W: (0, -1),
            keys.DOWN: (0, 1),
            keys.S: (0, 1),
        }

        if key not in directions:
            return

        change_x, change_y = directions[key]

        column = (
            self.astronaut.cell[0]
            + change_x
        )
        row = (
            self.astronaut.cell[1]
            + change_y
        )

        is_inside = (
            0 <= column < COLUMNS
            and 0 <= row < ROWS
        )

        if is_inside:
            self.astronaut.move_to(
                (column, row)
            )

            for enemy in self.enemies:
                enemy.take_turn()

    def finish_turn(self):
        hero = self.astronaut

        if hero.cell in self.minerals:
            del self.minerals[hero.cell]
            hero.collected += 1

            self.play_sound(
                "mineral_collect"
            )

            if not self.minerals:
                self.ship.image = (
                    "spaceship_open"
                )

        for enemy in self.enemies:
            crossed = (
                hero.start_cell
                == enemy.cell
                and hero.cell
                == enemy.start_cell
            )

            same_cell = (
                hero.cell == enemy.cell
            )

            if same_cell or crossed:
                hero.health -= 1
                self.play_sound("damage")
                break

        if hero.health <= 0:
            self.state = "lost"
            self.play_sound("game_over")

        elif (
            not self.minerals
            and hero.cell == self.ship_cell
        ):
            self.state = "won"
            self.play_sound("victory")

    def update(self, dt):
        if self.state != "playing":
            return

        finished = self.astronaut.update(dt)

        for enemy in self.enemies:
            enemy.update(dt)

        if finished:
            self.finish_turn()

    def draw_button(
        self,
        rectangle,
        label,
    ):
        screen.draw.filled_rect(
            rectangle,
            BUTTON,
        )
        screen.draw.rect(
            rectangle,
            ACCENT,
        )
        screen.draw.text(
            label,
            center=rectangle.center,
            fontsize=32,
            color=TEXT,
        )

    def draw_menu(self):
        screen.draw.text(
            "ORBITAL MINER",
            center=(500, 145),
            fontsize=64,
            color=TEXT,
        )

        screen.draw.text(
            "Hücre tabanlı uzay roguelike oyunu",
            center=(500, 215),
            fontsize=27,
            color=ACCENT,
        )

        self.draw_button(
            self.start_button,
            "Oyuna Başla",
        )

        if self.sound_enabled:
            sound_text = (
                "Müzik ve Ses: AÇIK"
            )
        else:
            sound_text = (
                "Müzik ve Ses: KAPALI"
            )

        self.draw_button(
            self.sound_button,
            sound_text,
        )

        self.draw_button(
            self.exit_button,
            "Çıkış",
        )

    def draw_world(self):
        for row in range(ROWS):
            for column in range(COLUMNS):
                rectangle = Rect(
                    LEFT + column * CELL,
                    TOP + row * CELL,
                    CELL,
                    CELL,
                )

                if (
                    row + column
                ) % 2 == 0:
                    color = (8, 20, 42)
                else:
                    color = PANEL

                screen.draw.filled_rect(
                    rectangle,
                    color,
                )
                screen.draw.rect(
                    rectangle,
                    PANEL,
                )

        self.ship.draw()

        for mineral in (
            self.minerals.values()
        ):
            mineral.draw()

        for enemy in self.enemies:
            enemy.actor.draw()

        self.astronaut.actor.draw()

        hero = self.astronaut

        screen.draw.text(
            (
                f"Can: {hero.health}   "
                f"Maden: "
                f"{hero.collected}/4"
            ),
            midtop=(500, 30),
            fontsize=30,
            color=TEXT,
        )

        screen.draw.text(
            "Ok tuşları / WASD: hareket",
            midbottom=(500, 684),
            fontsize=23,
            color=ACCENT,
        )

    def draw_result(self):
        won = self.state == "won"

        if won:
            title = "GÖREV TAMAMLANDI!"
            color = (80, 240, 160)
        else:
            title = "GÖREV BAŞARISIZ"
            color = (255, 100, 110)

        result_box = Rect(
            250,
            200,
            500,
            280,
        )

        screen.draw.filled_rect(
            result_box,
            PANEL,
        )

        screen.draw.text(
            title,
            center=(500, 275),
            fontsize=48,
            color=color,
        )

        screen.draw.text(
            (
                "ENTER: Tekrar Oyna    "
                "ESC: Ana Menü"
            ),
            center=(500, 385),
            fontsize=25,
            color=TEXT,
        )

    def draw(self):
        screen.fill(BACKGROUND)

        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_world()

            if self.state in (
                "won",
                "lost",
            ):
                self.draw_result()

    def mouse_down(self, pos):
        if self.state != "menu":
            return

        if self.start_button.collidepoint(pos):
            self.start_game()

        elif self.sound_button.collidepoint(pos):
            self.toggle_sound()

        elif self.exit_button.collidepoint(pos):
            raise SystemExit

    def key_down(self, key):
        if self.state == "playing":
            self.move_player(key)

        elif self.state in (
            "won",
            "lost",
        ):
            if key == keys.RETURN:
                self.start_game()

            elif key == keys.ESCAPE:
                self.state = "menu"


game = OrbitalMinerGame()


def draw():
    game.draw()


def update(dt):
    game.update(dt)


def on_key_down(key):
    game.key_down(key)


def on_mouse_down(pos):
    game.mouse_down(pos)