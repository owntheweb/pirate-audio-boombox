from random import randrange, random


class Star:
    def __init__(
            self,
            canvas_width=240,
            canvas_height=240,
            warp_speed_amount=0.005,
            star_size=5,
            pos_x=0,
            pos_y=0,
            ):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.warp_speed_amount = warp_speed_amount
        self.star_size = star_size
        if pos_x == 0:
            self.pos_x = randrange(self.canvas_width)
        else:
            self.pos_x = pos_x
        if pos_x == 0:
            self.pos_y = randrange(self.canvas_height)
        else:
            self.pos_y = pos_y
        self.brightness = random()

    def update_position(self):
        self.pos_x += (
            self.pos_x - (self.canvas_width / 2)
        ) * (self.warp_speed_amount)
        self.pos_y += (
            self.pos_y - (self.canvas_height / 2)
        ) * (self.warp_speed_amount)

        self.brightness += 0.01
        if self.brightness > 1.0:
            self.brightness = 1.0

        if (
            self.pos_x > self.canvas_width + self.star_size or
            self.pos_x < -self.star_size or
            self.pos_y > self.canvas_height + self.star_size or
            self.pos_y < -self.star_size
        ):
            self.pos_x = randrange(self.canvas_width)
            self.pos_y = randrange(self.canvas_height)
            self.brightness = 0.0


class Triangle:
    def __init__(
            self,
            canvas_width=240,
            canvas_height=240,
            warp_speed_amount=0.005,
            rotation_amount=0.3
            ):

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.warp_speed_amount = warp_speed_amount
        self.rotation_amount = rotation_amount
        self.pos_x = round(self.canvas_width * 0.5)
        self.pos_y = round(self.canvas_height * 0.5)
        self.brightness = 0.55
        self.radius = 10.0
        self.rotation = 0.0
        self.cleanup = False

    def update_position(self):
        self.brightness += 0.025
        if self.brightness > 1.0:
            self.brightness = 1.0

        self.rotation -= self.rotation_amount

        self.radius *= 1 + self.warp_speed_amount
        if self.radius > self.canvas_width * 1.5:
            self.cleanup = True


class PilWarpSpeed:
    def __init__(
            self,
            star_count=10,
            star_size=8,
            include_triangles=True,
            warp_speed_amount=0.005,
            canvas_width=240,
            canvas_height=240,
            throttle_frames=0,
            ):
        self.star_count = star_count
        self.star_size = star_size
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.warp_speed_amount = warp_speed_amount
        self.throttle_frames = throttle_frames
        self.throttle_frame = 0
        self.stars = self.create_stars()
        self.include_triangles = include_triangles
        self.triangle_spawn_every = 50
        self.triangle_spawn_i = 0
        self.triangles = []
        self.fast_forward()

    # TODO: This smells funny:
    # Run for a few iterations to make it look nice on first frame
    def fast_forward(self):
        for i in range(200):
            self.loop()

    def create_stars(self):
        stars = []
        for i in range(self.star_count):
            stars.append(Star(
                self.canvas_width,
                self.canvas_height,
                self.warp_speed_amount,
                self.star_size
            ))
        return stars

    def cleanup_triangles(self):
        cleaned_triangles = []
        for triangle in self.triangles:
            if not triangle.cleanup:
                cleaned_triangles.append(triangle)
        self.triangles = cleaned_triangles

    def create_triangle(self):
        self.triangle_spawn_i += 1
        if (self.triangle_spawn_i >= self.triangle_spawn_every or
                len(self.triangles) == 0):
            self.triangle_spawn_i = 0
            self.triangles.append(Triangle(
                    canvas_width=self.canvas_width,
                    canvas_height=self.canvas_height,
                    warp_speed_amount=self.warp_speed_amount,
                    rotation_amount=0.3
                )
            )

    def throttle_animation(self):
        if self.throttle_frames > 0:
            if self.throttle_frame < self.throttle_frames:
                self.throttle_frame += 1
                return True
            self.throttle_frame = 0
            return False

    def loop(self):
        for triangle in self.triangles:
            triangle.update_position()
        self.cleanup_triangles()
        self.create_triangle()
        for star in self.stars:
            star.update_position()

    def draw(self, image_draw, color):
        for triangle in self.triangles:
            image_draw.regular_polygon(
                bounding_circle=(
                    triangle.pos_x,
                    triangle.pos_y,
                    triangle.radius
                ),
                n_sides=3,
                rotation=triangle.rotation,
                fill=None,
                outline=(
                    round(color[0] * triangle.brightness * 0.6),
                    round(color[1] * triangle.brightness * 0.6),
                    round(color[2] * triangle.brightness * 0.6)
                ),
                width=4
            )
        for star in self.stars:
            image_draw.rectangle(
                (
                    star.pos_x,
                    star.pos_y,
                    star.pos_x + (self.star_size * star.brightness),
                    star.pos_y + (self.star_size * star.brightness)),
                (
                    round(color[0] * star.brightness),
                    round(color[1] * star.brightness),
                    round(color[2] * star.brightness)
                )
            )
