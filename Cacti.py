from scene import *
from random import randint, random, choice
from sound import play_effect, stop_effect
from colorsys import hsv_to_rgb
from math import sin
from functools import partial
from copy import copy
import json, ui
import motion

GAME_FONT = 'AvenirNext-Heavy'
game_character = 'Dog_Face'
characters = 'Dog_Face Bear_Face Cow_Face'.split()
characters_row_2 = 'Cat_Face Monkey_Face Hamster_Face'.split()

class SelectACharacterView(ui.View):
	def __init__(self):
		self.background_color = (0, 0.02, 0.1)
		self.add_subview(self.make_header())
		for i, character in enumerate(characters):
			self.add_subview(self.make_button(40 + i * 155, character))
		for i, character in enumerate(characters_row_2):
			self.add_subview(self.make_button2(40 + i * 155, character))

	@classmethod
	def make_header(cls):
		header = ui.Label(frame = (40, 19.5, 700, 116.5))
		header.text_color = 'white'
		header.text = 'Select A Character'
		header.font = (GAME_FONT, 50)
		return header

	@classmethod
	def character_tapped(cls, sender):
		global game_character
		game_character = sender.name
		root_view.remove_subview(SelectACharacterView()) # this does not work
		root_view.add_subview(scene_view)

	@classmethod
	def make_button(cls, x, image_name = 'Dog_Face'):
		img = ui.Image.named(image_name).with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)
		button = ui.Button(name=image_name, frame=(x, 160, 128, 128), image=img)
		button.action=cls.character_tapped
		return button
		
	@classmethod # easy but longer way to add another row of characters
	def make_button2(cls, x, image_name = 'Cat_Face'):
		img = ui.Image.named(image_name).with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)
		button = ui.Button(name=image_name, frame=(x, 365, 128, 128), image=img)
		button.action=cls.character_tapped
		return button

def change_character(sender):
	c = SelectACharacterView()
	c.present(style='sheet', hide_title_bar=True)

@ui.in_background
def play_game(sender):
	root_view.add_subview(scene_view)

class Star (object):
	def __init__(self):
		self.x = randint(0, 768)
		self.y = randint(0, 1024)
		self.v = random() * 5 + 1
	def update(self):
		self.y -= self.v

class StarField (object):
	def __init__(self, scene, count):
		self.scene = scene
		self.stars = []
		for i in xrange(count):
			self.stars.append(Star())

	def update(self):
		removed_stars = set()
		for star in self.stars:
			star.update()
			if star.y < 0:
				removed_stars.add(star)
		for removed_star in removed_stars:
			self.stars.remove(removed_star)
			new_star = Star()
			new_star.y = self.scene.size.h
			self.stars.append(new_star)

	def draw(self):
		background(0, 0.02, 0.1)
		for star in self.stars:
			a = (star.v / 5) * 0.7
			fill(a, a, a)
			rect(star.x, star.y, 3, 3)

class Player (object):
	def __init__(self, scene):
		self.scene = scene
		self.x = scene.size.w / 2
		self.dead = False
	def update(self):
		motion.start_updates()
		px = motion.get_gravity()
		gx = px[0] * 50
		self.x = min(max(self.x + gx, 20), self.scene.size.w - 20)
	def draw(self):
		push_matrix()
		translate(self.x, 20)
		rotate(0)
		image(game_character, 0, 0, 64, 64)
		pop_matrix()
	def bbox(self):
		return Rect(self.x - 20, 20, 40, 85)

class Enemy (object):
	def __init__(self, scene):
		self.scene = scene
		self.hit = False
		self.x = randint(20, 768-20)
		self.initial_x = self.x
		self.y = 1024
		self.a = 1.0
		self.removed = False
		self.dead = False
		r = random()
		if r < 0.1:
			self.size = 128
			self.color = Color(0, 1, 1)
			self.points = 500
			self.energy = 3
			self.bullet_type = 3
		elif r < 0.5:
			self.size = 96
			self.color = Color(0, 1, 0)
			self.points = 250
			self.energy = 2
			self.bullet_type = 2
		else:
			self.size = 64
			self.color = Color(1, 0, 1)
			self.points = 100
			self.energy = 1
			self.bullet_type = 1
		self.fire_freq = randint(20, 200)
		self.fire = False
		self.t = randint(0, self.fire_freq)
		self.speed = 1.0 / self.size * 500
		self.amp = random() * 300

	def update(self, dt):
		self.y -= self.speed
		self.x = self.initial_x + sin(self.y / 100) * self.amp
		self.amp = max(self.amp * 0.99, 0)
		if self.y < -64:
			self.removed = True
		if self.dead:
			self.a -= 0.1
			if self.a <= 0:
				self.removed = True
		else:
			self.t += 1
			if not self.dead and self.t % self.fire_freq == 0:
				play_effect('Laser_5')
				if self.bullet_type == 1:
					bullet = Bullet(self.x, self.y)
					bullet.vy = -10
					bullet.bullet_type = 1
					self.scene.enemy_bullets.append(bullet)
				elif self.bullet_type == 2:
					for vx in [-3, 3]:
						bullet = Bullet(self.x, self.y)
						bullet.vy = -10
						bullet.vx = vx
						bullet.bullet_type = 2
						self.scene.enemy_bullets.append(bullet)
				else:
					for vx in [-3, 0, 3]:
						bullet = Bullet(self.x, self.y)
						bullet.vy = -10
						bullet.vx = vx
						bullet.bullet_type = 3
						self.scene.enemy_bullets.append(bullet)

	def draw(self):
		if self.hit:
			tint(1, 0, 0, self.a)
		else:
			tint(self.color.r, self.color.g, self.color.b, self.a)
		image('Cactus', self.x - self.size/2,
		self.y - self.size/2, self.size, self.size)
		tint(1, 1, 1)

	def bbox(self):
		s = self.size
		return Rect(self.x - s/2 * 0.9, self.y - s/2 * 0.8, s * 0.9, s * 0.8)

class Powerup (object):
	def __init__(self, scene, powerup_type):
		self.x = randint(20, 768-20)
		self.y = scene.size.h + 20
		self.hue = 0.0
		self.rot = 0.0
		self.t = 0.0
		self.powerup_type = powerup_type
	def update(self):
		self.hue += 0.02
		self.y -= 10
		self.rot -= 3.0
		self.t += 0.1
	def draw(self):
		if self.powerup_type == 0:
			s = 50 + sin(self.t) * 10
			image('Heart', self.x - s/2, self.y - s/2, s, s)
		else:
			push_matrix()
			tint(*hsv_to_rgb(self.hue, 1, 1))
			translate(self.x, self.y)
			rotate(self.rot)
			image('Snake', -32, -32, 64, 64)
			tint(1, 1, 1)
			pop_matrix()
	def bbox(self):
		return Rect(self.x - 32, self.y - 32, 64, 64)

class Bullet (object):
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.vx = 0
		self.vy = 0
		self.bullet_type = 0
		self.pass_through = False
		self.hue = 0.0
	def update(self):
		self.x += self.vx
		self.y += self.vy
		if self.pass_through:
			self.hue += 0.02
	def draw(self):
		if self.pass_through:
			fill(*hsv_to_rgb(self.hue, 1, 1))
			ellipse(self.x - 4, self.y - 4, 8, 8)
		elif self.bullet_type == 0:
			fill(1, 1, 0)
			ellipse(self.x - 4, self.y - 4, 8, 8)
		elif self.bullet_type == 1:
			fill(1, 0, 1)
			rect(self.x - 2, self.y - 8, 4, 16)
		elif self.bullet_type == 2:
			fill(0, 1, 0)
			ellipse(self.x - 4, self.y - 4, 8, 8)
		elif self.bullet_type == 3:
			fill(0, 1, 1)
			ellipse(self.x - 4, self.y - 4, 8, 8)

	def hit_test(self, rect):
		return Point(self.x, self.y) in rect

class Game (Scene):
	def setup(self):
		self.frame_count = 0
		self.delayed_invocations = []
		self.frenzy = False
		self.touch_disabled = False
		self.star_field = StarField(self, 30)
		self.player = Player(self)
		self.energy = 100
		self.score = 0
		self.player.dead = False
		self.stars = []
		self.bullets = []
		self.enemies = []
		self.powerups = []
		self.enemy_bullets = []
		self.shot_fired = False
		self.effects_layer = Layer(Rect(0, 0, self.size.w, self.size.h))
		self.spawn()

	def spawn(self):
		self.enemies.append(Enemy(self))
		self.delay(random() + 0.5, self.spawn)
		if random() < 0.05:
			powerup = Powerup(self, choice([0, 1]))
			self.powerups.append(powerup)

	def draw(self):
		self.shot_fired = False
		self.star_field.update()
		self.star_field.draw()

		removed_bullets = set()
		removed_enemy_bullets = set()
		removed_enemies = set()

		fill(1, 1, 0)
		for bullet in self.bullets:
			bullet.update()
			bullet.draw()
			if bullet.y > 1024:
				removed_bullets.add(bullet)

		player_rect = self.player.bbox()
		fill(1, 0, 1)
		for bullet in self.enemy_bullets:
			bullet.update()
			bullet.draw()
			if bullet.y < -4:
				removed_enemy_bullets.add(bullet)
			elif not self.player.dead and bullet.hit_test(player_rect):
				removed_enemy_bullets.add(bullet)
				self.energy -= 10
				play_effect('Explosion_6')

		for enemy in self.enemies:
			enemy.update(self.dt)
			enemy.draw()
			enemy_rect = enemy.bbox()
			if not enemy.dead:
				for bullet in self.bullets:
					if bullet.hit_test(enemy_rect):
						removed_bullets.add(bullet)
						enemy.energy -= 1
						enemy.hit = True
						self.delay(0.1, partial(enemy.__setattr__, 'hit', False))
						if enemy.energy <= 0:
							enemy.dead = True
							self.score += enemy.points
							play_effect('Explosion_4')
						else:
							play_effect('Explosion_5')
				if not self.player.dead and player_rect.intersects(enemy_rect):
					play_effect('Explosion_6')
					enemy.dead = True
					self.energy -= 10
			if enemy.removed:
				removed_enemies.add(enemy)

		removed_powerups = set()
		for powerup in self.powerups:
			powerup.update()
			powerup.draw()
			if player_rect.intersects(powerup.bbox()):
				if powerup.powerup_type == 0:
					play_effect('Coin_2')
					self.energy = min(100, self.energy + 20)
				else:
					play_effect('Powerup_3')
					self.frenzy = True
					self.delay(5.0, partial(self.__setattr__, 'frenzy', False))
				removed_powerups.add(powerup)
			elif powerup.y < -32:
				removed_powerups.add(powerup)

		map(self.powerups.remove, removed_powerups)
		map(self.enemies.remove, removed_enemies)
		map(self.bullets.remove, removed_bullets)
		map(self.enemy_bullets.remove, removed_enemy_bullets)

		if not self.player.dead and self.energy <= 0:
			self.game_over()

		if not self.player.dead:
			self.player.update()
			self.player.draw()
		self.draw_status_bar()
		self.effects_layer.update(self.dt)
		self.effects_layer.draw()
		tint(1, 1, 1)

		self.frame_count += 1
		if not self.player.dead and len(self.touches) > 0:
			if self.frame_count % 12 == 0:
				self.fire()

	def high_score(self, name, score):
		file_name = 'highscores.json'
		high_scores = {}

		try:
			with open(file_name) as in_file:
				high_scores = json.load(in_file)
		except IOError:
			pass

		curr_high_score = high_scores.get(name, score - 1)
		if score >= curr_high_score:
			high_scores[name] = score
			h = TextLayer('NEW HIGH SCORE', GAME_FONT, 69)
			h.frame.center(self.size.w / 2, self.size.h - 300)
			play_effect('Coin_5')
			self.effects_layer.add_layer(h)
			with open(file_name, 'w') as out_file:
				json.dump(high_scores, out_file)

	def get_score(self, name, score): # for displaying current best score
		file_name = 'highscores.json'
		high_scores = {}

		try:
			with open(file_name) as in_file:
				high_scores = json.load(in_file)
		except IOError:
			pass

		curr_high_score = high_scores.get(name, score - 1)
		if score >= curr_high_score:
			high_scores[name] = score
			text('Best: ' + str(self.score), GAME_FONT, 20,
			self.size.w / 2, self.size.h - 27)
		else:
			text('Best: ' + str(curr_high_score), GAME_FONT, 20,
			self.size.w / 2, self.size.h - 27)

	def game_over(self):
		motion.stop_updates()
		self.player.dead = True
		self.touch_disabled = True
		play_effect('Laser_4')
		t = TextLayer('Game Over', GAME_FONT, 100)
		ts = TextLayer('Tap to Play Again', GAME_FONT, 50)
		ts.frame.center(self.size.w / 2, self.size.h - 630)
		t.frame.center(self.bounds.center())
		self.delay(2.0, partial(self.__setattr__, 'touch_disabled', False))
		t.scale_x, t.scale_y = 0.0, 0.0
		ts.scale_x, ts.scale_y = 0.0, 0.0
		t.animate('scale_x', 1.0, 1.0, curve=curve_bounce_out)
		t.animate('scale_y', 1.0, 1.0, curve=curve_bounce_out)
		ts.animate('scale_x', 1.0, 1.0, curve=curve_bounce_out)
		ts.animate('scale_y', 1.0, 1.0, curve=curve_bounce_out)
		self.effects_layer.add_layer(t)
		self.effects_layer.add_layer(ts)
		self.high_score('P1', int(self.score))

	def touch_began(self, touch):
		if self.player.dead and not self.touch_disabled:
			play_effect('Powerup_1')
			self.setup()
			return
		elif not self.player.dead:
			self.frame_count = 0
			self.fire()

	def fire(self):
		if self.shot_fired: return
		if self.frenzy:
			for vx in [-3, 0, 3]:
				bullet = Bullet(self.player.x, 110)
				bullet.vy = 15
				bullet.vx = vx
				bullet.pass_through = True
				self.bullets.append(bullet)
		else:
			bullet = Bullet(self.player.x, 110)
			bullet.vy = 15
			self.bullets.append(bullet)
		play_effect('Laser_6')
		self.shot_fired = True

	def draw_status_bar(self):
		hue = (self.energy / 100.0) * 0.35 + 1.0
		r, g, b = hsv_to_rgb(hue, 1, 1)
		fill(r, g, b)
		rect(0, self.size.h - 5, self.energy / 100.0 * self.size.w, 10)
		text(str(self.score), GAME_FONT, 40, self.size.w / 2, self.size.h - 65)
		self.get_score('P1', int(self.score)) # putting this here lets it update as score goes up
		
v = ui.load_view('Cacti')
v.background_color = (0, 0.02, 0.1)

w, h = ui.get_screen_size()
root_view = v
scene_view = SceneView()
scene_view.frame = (0, 0, w, h)
scene_view.scene = Game ()
screensize = ui.get_screen_size()
display = 'landscape' if screensize[0] > 768 else 'portrait'
root_view.present(orientations=[display], hide_title_bar=True )
