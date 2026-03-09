import pygame
import pymunk
import random
import math

# ------------------
# 기본 설정
# ------------------

width,height=1200,800
fps=60

T=1
F=2

FE_BIND_PROB=0.5
ALPHA=0.7        # 전하 반발 강도
K_OFF=0.00001      # 해리 확률

pygame.init()
screen=pygame.display.set_mode((width,height))
clock=pygame.time.Clock()

space=pymunk.Space()
space.gravity=(0,1)
space.iterations=30

tannins=[]
irons=[]
joints=[]

# ------------------
# 벽 (닫힌 용기)
# ------------------

walls=[
    pymunk.Segment(space.static_body,(0,0),(width,0),2),
    pymunk.Segment(space.static_body,(0,height),(width,height),2),
    pymunk.Segment(space.static_body,(0,0),(0,height),2),
    pymunk.Segment(space.static_body,(width,0),(width,height),2)
]

for w in walls:
    w.elasticity=1

space.add(*walls)

# ------------------
# 입자 생성
# ------------------

def make_tannin():
    body=pymunk.Body(2,pymunk.moment_for_circle(2,0,15))
    body.position=random.uniform(50,width-50),random.uniform(50,height-50)
    body.velocity=random.uniform(-120,120),random.uniform(-120,120)
    shape=pymunk.Circle(body,15)
    shape.elasticity=1
    shape.collision_type=T
    shape.fe_count=0
    space.add(body,shape)
    tannins.append(shape)

def make_iron():
    body=pymunk.Body(1,pymunk.moment_for_circle(1,0,4))
    body.position=random.uniform(50,width-50),random.uniform(50,height-50)
    body.velocity=random.uniform(-150,150),random.uniform(-150,150)
    shape=pymunk.Circle(body,4)
    shape.elasticity=1
    shape.collision_type=F
    shape.t_count=0
    space.add(body,shape)
    irons.append(shape)

# ------------------
# 결합 반응
# ------------------

def react_tf(arbiter,space,data):
    s1,s2=arbiter.shapes

    if s1.collision_type==T:
        t,f=s1,s2
    else:
        t,f=s2,s1

    if t.fe_count>=10 or f.t_count>=3:
        return True

    # 이미 연결 방지
    for j in joints:
        if (j.t==t and j.f==f):
            return True

    n=t.fe_count+f.t_count
    prob=FE_BIND_PROB*math.exp(-ALPHA*n)

    if random.random()<prob:
        t.fe_count+=1
        f.t_count+=1

        joint=pymunk.PinJoint(t.body,f.body)
        joint.t=t
        joint.f=f
        space.add(joint)
        joints.append(joint)

    return True

space.on_collision(T,F,begin=react_tf)

# ------------------
# 초기 농도
# ------------------

for _ in range(100):
    make_tannin()

for _ in range(100):
    make_iron()

font=pygame.font.SysFont(None,24)
time_elapsed=0

# ------------------
# 메인 루프
# ------------------

running=True
while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False

    dt=1/fps
    time_elapsed+=dt
    space.step(dt)

    # 해리 처리
    for j in joints[:]:
        if random.random()<K_OFF:
            j.t.fe_count-=1
            j.f.t_count-=1
            space.remove(j)
            joints.remove(j)

    screen.fill((0,0,0))

    # 탄닌
    for t in tannins:
        pygame.draw.circle(screen,(0,200,0),
                           (int(t.body.position.x),
                            int(t.body.position.y)),15)

    # 철
    for f in irons:
        pygame.draw.circle(screen,(160,160,160),
                           (int(f.body.position.x),
                            int(f.body.position.y)),4)

    # 결합선
    for j in joints:
        pygame.draw.line(screen,(100,100,255),
                         j.a.position,
                         j.b.position,1)

    free_fe=sum([1 for f in irons if f.t_count==0])
    free_t=sum([1 for t in tannins if t.fe_count==0])

    text=font.render(f"time={time_elapsed:.1f}",True,(255,255,255))
    screen.blit(text,(10,10))
    text=font.render(f"Free Fe={free_fe}",True,(255,255,255))
    screen.blit(text,(10,30))
    text=font.render(f"Free Tannins={free_t}",True,(255,255,255))
    screen.blit(text,(10,50))

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
