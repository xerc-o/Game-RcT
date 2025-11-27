# file: game_with_preview.py
# Jalankan: python game_with_preview.py
import pygame
import random
import math
import sys
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# ---------- Inisialisasi ----------
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RcT - Sesuaikan Karaktermu")
clock = pygame.time.Clock()
FONT_BIG = pygame.font.SysFont(None, 48)
FONT_MED = pygame.font.SysFont(None, 32)
FONT_SMALL = pygame.font.SysFont(None, 22)

# ---------- Utility ----------
def load_image_dialog():
    """
    Buka dialog file (Tkinter) untuk memilih gambar dan mengembalikan path.
    (Tkinter digunakan hanya untuk file dialog)
    """
    root = Tk()
    root.withdraw()         # sembunyikan window utama Tk
    root.attributes("-topmost", True)  # pastikan dialog tampil di depan
    filename = askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
    root.destroy()
    return filename or None

def scale_image_keep_ratio(img_surf, max_w, max_h):
    """Skalakan surface pygame agar muat dalam kotak max_w x max_h (menjaga rasio)."""
    w, h = img_surf.get_size()
    scale = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(img_surf, (max(1, int(w * scale)), max(1, int(h * scale))))

# ---------- Game objects ----------
def angle_to(sx, sy, tx, ty):
    return math.atan2(ty - sy, tx - sx)

class Bullet:
    def __init__(self, x, y, angle, owner):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 8
        self.owner = owner  # "player" or "enemy"
        self.radius = 5

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def draw(self, surf):
        if self.owner == "player":
            color = (0, 150, 255)   # biru pemain
        else:
            color = (255, 200, 0)   # kuning musuh
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), self.radius)

    def is_offscreen(self):
        return self.x < -50 or self.x > WIDTH + 50 or self.y < -50 or self.y > HEIGHT + 50

class Character:
    def __init__(self, x, y, img_surf=None, shape="square", color=(255,255,255)):
        self.x = x
        self.y = y
        self.speed = 3
        self.health = 100
        self.max_health = 100
        self.alive = True
        self.img = img_surf  # pygame Surface atau None
        self.shape = shape
        self.color = color
        self.size = 48  # ukuran standar untuk menggambar bila tidak ada img

    def clamp_position(self):
        # batasi agar tidak keluar border (mencegah hilang)
        margin = 20
        self.x = max(margin, min(WIDTH - margin, self.x))
        self.y = max(margin, min(HEIGHT - margin, self.y))

    def draw(self, surf):
        if not self.alive:
            return
        if self.img:
            w, h = self.img.get_size()
            surf.blit(self.img, (int(self.x - w/2), int(self.y - h/2)))
        else:
            # fallback bentuk sederhana
            if self.shape == "square":
                pygame.draw.rect(surf, self.color, (self.x - 20, self.y - 20, 40, 40))
            elif self.shape == "circle":
                pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 20)
            elif self.shape == "triangle":
                points = [(self.x, self.y-22), (self.x-20, self.y+18), (self.x+20, self.y+18)]
                pygame.draw.polygon(surf, self.color, points)

    def draw_healthbar(self, surf, x, y):
        # health bar (background merah, foreground hijau)
        pygame.draw.rect(surf, (150, 0, 0), (x, y, 100, 12))
        hp_w = max(0, min(100, int(self.health)))
        pygame.draw.rect(surf, (0, 200, 0), (x, y, hp_w, 12))

# ---------- Game state & functions ----------
bullets = []
player = None
enemies = []
game_state = "menu"   # menu / playing / win / game_over
level = 1
selected_player_img = None
selected_enemy_img = None
preview_player_surf = None
preview_enemy_surf = None

def reset_level():
    """Inisialisasi ulang level sesuai variable level (jumlah musuh = level)."""
    global bullets, player, enemies
    bullets = []
    # player spawn di tengah (gunakan gambar yang dipilih jika ada)
    p_img = None
    if selected_player_img:
        p_img = scale_image_keep_ratio(selected_player_img, 64, 64)
    player = Character(WIDTH//2, HEIGHT//2, img_surf=p_img, shape="circle", color=(0,255,255))
    # buat musuh sebanyak 'level'
    enemies = []
    for i in range(level):
        e_img = None
        if selected_enemy_img:
            e_img = scale_image_keep_ratio(selected_enemy_img, 56, 56)
        ex = random.randint(80, WIDTH-80)
        ey = random.randint(80, HEIGHT-80)
        enemies.append(Character(ex, ey, img_surf=e_img, shape=random.choice(["square","circle","triangle"]), color=(255,80,80)))
    return

def start_game_from_menu():
    global level, game_state
    level = 1
    reset_level()
    game_state = "playing"

# ---------- Menu drawing + preview ----------
def draw_menu():
    screen.fill((18, 24, 32))
    title = FONT_BIG.render("Pilih Gambar Karaktermu", True, (220,220,220))
    screen.blit(title, (200, 30))

    # Tombol Player image
    pygame.draw.rect(screen, (40, 90, 200), (120, 120, 240, 60))
    t = FONT_MED.render("Pilih Gambar Player", True, (255,255,255))
    screen.blit(t, (140, 135))

    # Tombol Enemy image
    pygame.draw.rect(screen, (200, 60, 60), (440, 120, 240, 60))
    t2 = FONT_MED.render("Pilih Gambar Musuh", True, (255,255,255))
    screen.blit(t2, (460, 135))

    # Preview area kotak player
    pygame.draw.rect(screen, (50,50,50), (120, 200, 240, 160))
    label = FONT_SMALL.render("Preview Player", True, (200,200,200))
    screen.blit(label, (120, 200 - 24))
    if preview_player_surf:
        # center preview
        pw, ph = preview_player_surf.get_size()
        screen.blit(preview_player_surf, (120 + (240 - pw)//2, 200 + (160 - ph)//2))
    else:
        hint = FONT_SMALL.render("Belum pilih gambar", True, (140,140,140))
        screen.blit(hint, (120 + 40, 200 + 70))

    # Preview area kotak enemy
    pygame.draw.rect(screen, (50,50,50), (440, 200, 240, 160))
    label2 = FONT_SMALL.render("Preview Musuh", True, (200,200,200))
    screen.blit(label2, (440, 200 - 24))
    if preview_enemy_surf:
        ew, eh = preview_enemy_surf.get_size()
        screen.blit(preview_enemy_surf, (440 + (240 - ew)//2, 200 + (160 - eh)//2))
    else:
        hint2 = FONT_SMALL.render("Belum pilih gambar", True, (140,140,140))
        screen.blit(hint2, (440 + 40, 200 + 70))

    # Tombol START (aktif jika kedua gambar terpilih)
    can_start = (selected_player_img is not None and selected_enemy_img is not None)
    start_color = (60,200,80) if can_start else (60,80,60)
    pygame.draw.rect(screen, start_color, (300, 400, 200, 60))
    txt = FONT_MED.render("Mulai Game", True, (0,0,0) if can_start else (200,200,200))
    screen.blit(txt, (340, 415))

    # Petunjuk
    info = FONT_SMALL.render("Klik tombol untuk memilih file JPG/PNG. Gunakan mouse untuk menembak, WASD gerak.", True, (180,180,180))
    screen.blit(info, (80, 500))

# ---------- Game Over & Win screens ----------
def draw_gameplay():
    screen.fill((12, 18, 28))

    # draw player & enemies
    if player and player.alive:
        player.draw(screen)
    for e in enemies:
        if e.alive:
            e.draw(screen)

    # draw bullets
    for b in bullets:
        b.draw(screen)

    # health bars: player kiri-bawah
    if player:
        player.draw_healthbar(screen, 20, HEIGHT - 40)
    # enemies health top area; spread per enemy
    start_x = 20
    for e in enemies:
        if e.alive:
            e.draw_healthbar(screen, start_x, 20)
            start_x += 120

    # level info
    lv = FONT_SMALL.render(f"Level: {level}", True, (200,200,200))
    screen.blit(lv, (WIDTH - 120, HEIGHT - 35))

def draw_game_over():
    screen.fill((10,10,10))
    t = FONT_BIG.render("GAME OVER", True, (230,60,60))
    screen.blit(t, (WIDTH//2 - t.get_width()//2, 200))
    s = FONT_MED.render("Main lagi? Y = ya / N = tidak", True, (200,200,200))
    screen.blit(s, (WIDTH//2 - s.get_width()//2, 280))

def draw_win_screen():
    screen.fill((8,30,8))
    t = FONT_BIG.render("MENANG!", True, (80,240,120))
    screen.blit(t, (WIDTH//2 - t.get_width()//2, 180))
    s = FONT_MED.render("Lanjut level berikut? (Y/N)", True, (220,220,220))
    screen.blit(s, (WIDTH//2 - s.get_width()//2, 260))
    info = FONT_SMALL.render(f"Level sekarang: {level}", True, (200,200,200))
    screen.blit(info, (WIDTH//2 - info.get_width()//2, 320))

# ---------- Input rects untuk menu buttons ----------
btn_player_rect = pygame.Rect(120, 120, 240, 60)
btn_enemy_rect  = pygame.Rect(440, 120, 240, 60)
btn_start_rect  = pygame.Rect(300, 400, 200, 60)

# ---------- Main loop ----------
running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Menu interactions ---
        if game_state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if btn_player_rect.collidepoint(mx, my):
                    # pilih gambar player
                    path = load_image_dialog()
                    if path:
                        try:
                            img = pygame.image.load(path).convert_alpha()
                            selected_player_img = img
                            preview_player_surf = scale_image_keep_ratio(img, 220, 140)
                        except Exception as ex:
                            print("Gagal memuat gambar player:", ex)
                elif btn_enemy_rect.collidepoint(mx, my):
                    # pilih gambar enemy
                    path = load_image_dialog()
                    if path:
                        try:
                            img = pygame.image.load(path).convert_alpha()
                            selected_enemy_img = img
                            preview_enemy_surf = scale_image_keep_ratio(img, 220, 140)
                        except Exception as ex:
                            print("Gagal memuat gambar enemy:", ex)
                elif btn_start_rect.collidepoint(mx, my):
                    if selected_player_img and selected_enemy_img:
                        # mulai level pertama
                        level = 1
                        reset_level()
                        game_state = "playing"

        # --- Gameplay interactions ---
        elif game_state == "playing":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # player menembak (arah mouse)
                if player and player.alive:
                    mx, my = pygame.mouse.get_pos()
                    ang = angle_to(player.x, player.y, mx, my)
                    bullets.append(Bullet(player.x, player.y, ang, "player"))

        # --- Game over / win keyboard ---
        elif game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    level = 1
                    reset_level()
                    game_state = "playing"
                elif event.key == pygame.K_n:
                    running = False
        elif game_state == "win":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    level += 1
                    reset_level()
                    game_state = "playing"
                elif event.key == pygame.K_n:
                    running = False

    # ---------- STATE UPDATES ----------
    if game_state == "menu":
        draw_menu()

    elif game_state == "playing":
        # -- player movement (WASD) --
        keys = pygame.key.get_pressed()
        if player and player.alive:
            vx = vy = 0
            if keys[pygame.K_w]: vy -= 1
            if keys[pygame.K_s]: vy += 1
            if keys[pygame.K_a]: vx -= 1
            if keys[pygame.K_d]: vx += 1
            # normalisasi kecepatan diagonal
            if vx != 0 or vy != 0:
                norm = math.hypot(vx, vy)
                vx /= norm
                vy /= norm
                player.x += vx * player.speed
                player.y += vy * player.speed
                player.clamp_position()

        # -- enemy AI: bergerak acak dan tembak --
        for e in enemies:
            if e.alive:
                # random walk: ubah arah kadang2
                if random.randint(0, 60) == 0:
                    ang = random.uniform(0, 2*math.pi)
                    e.dir_x = math.cos(ang)
                    e.dir_y = math.sin(ang)
                    e.move_time = random.randint(20, 80)
                # move if properties exist, else init
                if hasattr(e, "move_time") and e.move_time > 0:
                    e.x += getattr(e, "dir_x", 0) * e.speed
                    e.y += getattr(e, "dir_y", 0) * e.speed
                    e.move_time -= 1
                else:
                    # kecil gerakan acak supaya tidak diam
                    e.x += random.uniform(-1,1) * e.speed * 0.5
                    e.y += random.uniform(-1,1) * e.speed * 0.5
                e.clamp_position()
                # tembak acak ke player
                if player and player.alive and random.randint(1, 90) == 1:
                    ang = angle_to(e.x, e.y, player.x, player.y)
                    bullets.append(Bullet(e.x, e.y, ang, "enemy"))

        # -- update bullets (gerak, collision, hapus) --
        for b in bullets[:]:
            b.update()

            # hilangkan kalau keluar layar
            if b.is_offscreen():
                bullets.remove(b)
                continue

            # collision bullet -> enemy (jika bullet dari player)
            if b.owner == "player":
                for e in enemies:
                    if e.alive and math.hypot(b.x - e.x, b.y - e.y) < 28:
                        e.health -= 15
                        if b in bullets:
                            bullets.remove(b)
                        break

            # collision bullet -> player (jika bullet dari enemy)
            elif b.owner == "enemy":
                if player and player.alive and math.hypot(b.x - player.x, b.y - player.y) < 28:
                    player.health -= 12
                    if b in bullets:
                        bullets.remove(b)
                    # don't break; handle other bullets

        # -- cek hidup / mati --
        all_dead = True
        for e in enemies:
            if e.health <= 0:
                e.alive = False
            if e.alive:
                all_dead = False
        if all_dead:
            game_state = "win"

        if player and player.health <= 0:
            player.alive = False
            game_state = "game_over"

        # -- draw gameplay --
        draw_gameplay()

    elif game_state == "game_over":
        draw_game_over()

    elif game_state == "win":
        draw_win_screen()

    # update layar
    pygame.display.flip()

# ---------- exit ----------
pygame.quit()
sys.exit()
