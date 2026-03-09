import pygame
import pymunk
import pymunk.pygame_util
import random

width,height=600,400
fps=60

S=1 #Substrate
A=2 #Active site
P=3 #Product

turn_time=0.3

measure_time=3
measure_frames=int(measure_time*fps)
frame_count=0
reaction_count=0

trials=10
v0_sum=0
trial_count=0

init_substrates=500

pygame.init()
screen=pygame.display.set_mode((width,height))
clock=pygame.time.Clock()

space=pymunk.Space()
space.gravity=(0,0)

draw=pymunk.pygame_util.DrawOptions(screen)

def open_space(body):
    x,y=body.position
    body.position=(x%width,y%height)

substrates=[]
products=[]
enzymes=[]

def make_substrate():
    body=pymunk.Body(1,pymunk.moment_for_circle(1,0,4))
    body.position=random.uniform(0,width),random.uniform(0,height)
    body.velocity=random.uniform(-200,200),random.uniform(-200,200)
    shape=pymunk.Circle(body,4)
    shape.elasticity=1
    shape.collision_type=S
    shape.color=(80,150,255,255)
    space.add(body,shape)
    substrates.append(shape)

def make_product(pos,vel):
    body=pymunk.Body(1,pymunk.moment_for_circle(1,0,4))
    body.position=pos
    body.velocity=vel
    shape=pymunk.Circle(body,4)
    shape.elasticity=1
    shape.collision_type=P
    shape.color=(255,200,80,255)
    space.add(body,shape)
    products.append(shape)

def make_enzyme():
    body=pymunk.Body(5,pymunk.moment_for_circle(5,0,10))
    body.position=random.uniform(0,width),random.uniform(0,height)
    body.velocity=random.uniform(-80,80),random.uniform(-80,80)

    body.bound=False
    body.bound_velocity=None

    inactive=pymunk.Circle(body,10)
    inactive.elasticity=1
    inactive.color=(80,255,120,255)

    active=pymunk.Circle(body,3,offset=(10,0))
    active.elasticity=1
    active.collision_type=A
    active.color=(255,50,50,255)

    space.add(body,inactive,active)
    enzymes.append(body)

def react(arbiter,space,data):
    shape1,shape2=arbiter.shapes
    if shape1.collision_type==S:
        s=shape1
        site=shape2
    else:
        s=shape2
        site=shape1
    enzyme=site.body
    if enzyme.bound:
        return False
    enzyme.bound=True
    enzyme.will_react=(random.random()<0.5)
    enzyme.t_event=turn_time
    enzyme.bound_velocity=s.body.velocity
    space.remove(s.body,s)
    substrates.remove(s)
    return False

def finish_reaction(e):
    global reaction_count
    make_product(e.position,e.bound_velocity)
    e.bound=False
    reaction_count+=1

def release_substrate(e):
    e.bound=False
    body=pymunk.Body(1,pymunk.moment_for_circle(1,0,4))
    body.position=e.position
    body.velocity=e.velocity
    shape=pymunk.Circle(body,4)
    shape.elasticity=1
    shape.collision_type=S
    shape.color=(80,150,255,255)
    space.add(body,shape)
    substrates.append(shape)

space.on_collision(S,A,begin=react)

for _ in range(init_substrates):
    make_substrate()

for _ in range(5):
    make_enzyme()

running=True
while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False
    dt=1/fps
    space.step(dt)
    frame_count+=1
    if frame_count==measure_frames:
        v0=reaction_count/measure_time
        v0_sum+=v0
        trial_count+=1
        reaction_count=0
        frame_count=0
        for s in substrates:
            space.remove(s.body,s)
        substrates.clear()
        for _ in range(init_substrates):
            make_substrate()
        for p in products:
            space.remove(p,p.body)
        products.clear()
    if trial_count==trials:
        print(v0_sum/trials)
        running=False
    for s in substrates+products:
        open_space(s.body)
    for e in enzymes:
        open_space(e)
        if e.bound:
            e.t_event-=dt
            if e.t_event<=0:
                if e.will_react:
                    finish_reaction(e)
                else:
                    release_substrate(e)
    screen.fill((30,30,30))
    space.debug_draw(draw)
    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
