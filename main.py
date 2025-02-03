import pygame
import random
import math
import sys
import json
import numpy as np

# 初始化PyGame
pygame.init()

# 窗口设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("dick射击训练器")

# 颜色配置
COLORS = {
    "background": (30, 30, 30),
    "target": (0, 255, 100),
    "text": (255, 255, 255),
    "menu": (100, 200, 255),
    "highlight": (255, 150, 50)
}

# 难度配置
DIFFICULTIES = {
    "easy": {"speed_range": (1, 3), "size_range": (30, 50), "spawn_delay": 1.0},
    "normal": {"speed_range": (3, 5), "size_range": (20, 40), "spawn_delay": 0.7},
    "hard": {"speed_range": (5, 8), "size_range": (15, 30), "spawn_delay": 0.5}
}

GAME_DURATION = 30  # 游戏时长


class GameState:
    MENU = 0
    PLAYING = 1
    END = 2


class MovingSquare:
    def __init__(self, difficulty):
        cfg = DIFFICULTIES[difficulty]
        self.side = random.randint(*cfg["size_range"])
        half_side = self.side // 2

        self.x = random.randint(half_side, WIDTH - half_side)
        self.y = random.randint(half_side, HEIGHT - half_side)

        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(*cfg["speed_range"])
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed

        self.spawn_time = pygame.time.get_ticks()
        self.rect = pygame.Rect(self.x - half_side, self.y - half_side, self.side, self.side)

    def update(self):
        half_side = self.side // 2
        self.x += self.dx
        self.y += self.dy

        if self.x < half_side or self.x > WIDTH - half_side:
            self.dx *= -1
        if self.y < half_side or self.y > HEIGHT - half_side:
            self.dy *= -1

        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        pygame.draw.rect(surface, COLORS["target"], self.rect, 3)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class AimTrainer:
    def __init__(self):
        self.state = GameState.MENU
        self.load_highscores()
        self.total_shots = 0
        self.reaction_times = []
        self.current_target = None
        self.difficulty = "normal"

        # 字体初始化
        try:
            self.font_large = pygame.font.SysFont("simhei", 72)
            self.font_medium = pygame.font.SysFont("simhei", 36)
            self.font_small = pygame.font.SysFont("simhei", 24)
        except:
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)

        self.sound_enabled = True
        pygame.mixer.init(frequency=44100, size=-16, channels=1)

    def load_highscores(self):
        try:
            with open("highscores.json", "r") as f:
                self.highscores = json.load(f)
        except:
            self.highscores = {"easy": 0, "normal": 0, "hard": 0}

    def save_highscores(self):
        with open("highscores.json", "w") as f:
            json.dump(self.highscores, f)

    def start_game(self, difficulty):
        self.difficulty = difficulty
        self.score = 0
        self.start_time = pygame.time.get_ticks()
        self.total_shots = 0
        self.reaction_times = []
        self.current_target = MovingSquare(difficulty)
        self.state = GameState.PLAYING

    def draw_menu(self):
        screen.fill(COLORS["background"])
        title = self.font_large.render("射击训练器", True, COLORS["menu"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        y = 250
        for i, diff in enumerate(DIFFICULTIES):
            diff_name = {
                "easy": "简单",
                "normal": "普通",
                "hard": "困难"
            }.get(diff, diff)

            text = self.font_medium.render(
                f"{diff_name}模式 (最高分: {self.highscores[diff]})",
                True,
                COLORS["menu"] if i != 1 else COLORS["highlight"]
            )
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))
            y += 60

        tip = self.font_small.render("使用 1-3 选择难度，空格键开始", True, COLORS["text"])
        screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, 500))

    def play_system_sound(self, sound_type):
        if not self.sound_enabled:
            return
        try:
            freq = 1000 if sound_type == "hit" else 500
            duration = 100
            sample_rate = 44100
            wave = np.array([32767 * ((i // (sample_rate // freq)) % 2)
                             for i in range(int(sample_rate * duration / 1000))],
                            dtype=np.int16)
            sound = pygame.mixer.Sound(buffer=wave)
            sound.set_volume(0.3)
            sound.play()
        except Exception as e:
            print(f"音效生成失败: {str(e)}")

    def run(self):
        clock = pygame.time.Clock()
        while True:
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000 if self.state == GameState.PLAYING else 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_highscores()
                    pygame.quit()
                    sys.exit()

                if self.state == GameState.MENU:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_1:
                            self.difficulty = "easy"
                        elif event.key == pygame.K_2:
                            self.difficulty = "normal"
                        elif event.key == pygame.K_3:
                            self.difficulty = "hard"
                        elif event.key == pygame.K_SPACE:
                            self.start_game(self.difficulty)

                elif self.state == GameState.PLAYING:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.total_shots += 1
                        if self.current_target.is_clicked(event.pos):
                            self.play_system_sound("hit")
                            self.score += 1
                            react_time = pygame.time.get_ticks() - self.current_target.spawn_time
                            self.reaction_times.append(react_time)
                            self.current_target = MovingSquare(self.difficulty)
                        else:
                            self.play_system_sound("miss")
                            self.score = max(0, self.score - 1)

                elif self.state == GameState.END:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.state = GameState.MENU

            if self.state == GameState.PLAYING:
                if self.current_target:
                    self.current_target.update()
                    if elapsed >= GAME_DURATION:
                        self.state = GameState.END
                        if self.score > self.highscores[self.difficulty]:
                            self.highscores[self.difficulty] = self.score
                        self.save_highscores()

            screen.fill(COLORS["background"])

            if self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.PLAYING:
                if self.current_target:
                    self.current_target.draw(screen)
                    stats = [
                        f"得分: {self.score}",
                        f"剩余时间: {max(0, GAME_DURATION - elapsed):.1f}s",
                        f"命中率: {self.accuracy:.1f}%" if self.total_shots > 0 else "",
                        f"平均反应: {sum(self.reaction_times) / len(self.reaction_times):.0f}ms" if self.reaction_times else ""
                    ]
                    y = 10
                    for line in stats:
                        text = self.font_small.render(line, True, COLORS["text"])
                        screen.blit(text, (10, y))
                        y += 25
            elif self.state == GameState.END:
                lines = [
                    f"最终得分: {self.score}",
                    f"命中率: {self.accuracy:.1f}%",
                    f"平均反应时间: {self.avg_reaction_time}ms",
                    f"新纪录! 🎉" if self.score > self.highscores[self.difficulty] else ""
                ]
                y = HEIGHT // 2 - 100
                for line in lines:
                    text = self.font_medium.render(line, True, COLORS["text"])
                    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))
                    y += 50
                restart = self.font_small.render("按空格键返回菜单", True, COLORS["text"])
                screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT - 100))

            pygame.display.flip()
            clock.tick(60)

    @property
    def accuracy(self):
        return (len(self.reaction_times) / self.total_shots * 100) if self.total_shots > 0 else 0.0

    @property
    def avg_reaction_time(self):
        return sum(self.reaction_times) / len(self.reaction_times) if self.reaction_times else 0.0


if __name__ == "__main__":
    game = AimTrainer()
    game.run()