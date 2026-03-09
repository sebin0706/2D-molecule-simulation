import pymunk
import random
import math
import statistics

REPEATS=100
FE_FIXED=100
RATIOS=[i/10 for i in range(1,11)]

FE_BIND_PROB=0.5
ALPHA=0.7
K_OFF=0.00001

DT=1/60
TOTAL_STEPS=4800
MEASURE_START=3600
MEASURE_INTERVAL=60

T=1
F=2

def get_clusters(tannins,irons,joints):
    graph={x:[] for x in tannins+irons}

    for j in joints:
        if j.t in graph and j.f in graph:
            graph[j.t].append(j.f)
            graph[j.f].append(j.t)

    visited=set()
    clusters=[]

    for node in graph:
        if node not in visited:
            stack=[node]
            cluster=[]
            while stack:
                n=stack.pop()
                if n not in visited:
                    visited.add(n)
                    cluster.append(n)
                    stack.extend(graph[n])
            clusters.append(cluster)

    return clusters


for ratio in RATIOS:

    precip_repeat=[]
    fe_repeat=[]

    for _ in range(REPEATS):

        # ===== space 생성 =====
        space=pymunk.Space()
        space.gravity=(0,0)

        static=space.static_body
        walls=[
            pymunk.Segment(static,(0,0),(1200,0),1),
            pymunk.Segment(static,(0,0),(0,800),1),
            pymunk.Segment(static,(1200,0),(1200,800),1),
            pymunk.Segment(static,(0,800),(1200,800),1)
        ]

        for wall in walls:
            wall.elasticity=1.0
            space.add(wall)

        tannins=[]
        irons=[]
        joints=[]

        # ===== 입자 생성 =====
        def make_tannin():
            body=pymunk.Body(1,pymunk.moment_for_circle(1,0,15))
            body.position=random.uniform(0,1200),random.uniform(0,800)
            body.velocity=random.uniform(-80,80),random.uniform(-80,80)
            shape=pymunk.Circle(body,15)
            shape.collision_type=T
            shape.fe_count=0
            space.add(body,shape)
            tannins.append(shape)

        def make_iron():
            body=pymunk.Body(1,pymunk.moment_for_circle(1,0,4))
            body.position=random.uniform(0,1200),random.uniform(0,800)
            body.velocity=random.uniform(-80,80),random.uniform(-80,80)
            shape=pymunk.Circle(body,4)
            shape.collision_type=F
            shape.t_count=0
            space.add(body,shape)
            irons.append(shape)

        for _ in range(FE_FIXED):
            make_iron()

        for _ in range(int(FE_FIXED*ratio)):
            make_tannin()

        # ===== 반응 =====
        def react_tf(arbiter,space,data):
            s1,s2=arbiter.shapes
            t,f=(s1,s2) if s1.collision_type==T else (s2,s1)

            if t.fe_count>=10 or f.t_count>=3:
                return True

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

        precip_samples=[]
        fe_samples=[]

        # ===== 시뮬레이션 =====
        for step in range(TOTAL_STEPS):

            space.step(DT)

            # 해리
            for j in joints[:]:
                if random.random()<K_OFF:
                    j.t.fe_count-=1
                    j.f.t_count-=1
                    space.remove(j)
                    joints.remove(j)

            if step>=MEASURE_START and step%MEASURE_INTERVAL==0:

                clusters=get_clusters(tannins,irons,joints)

                precip_t=0
                for c in clusters:
                    t_count=sum(1 for x in c if x in tannins)
                    if t_count>=5:
                        precip_t+=t_count

                bound_fe=sum(1 for f in irons if f.t_count>0)

                precip_samples.append(precip_t)
                fe_samples.append(bound_fe/FE_FIXED)

        avg_precip=sum(precip_samples)/len(precip_samples)
        avg_fe_removal=sum(fe_samples)/len(fe_samples)

        precip_repeat.append(avg_precip)
        fe_repeat.append(avg_fe_removal)

    mean_precip=statistics.mean(precip_repeat)
    std_precip=statistics.stdev(precip_repeat)

    mean_removal=statistics.mean(fe_repeat)
    std_removal=statistics.stdev(fe_repeat)

    print(f"Ratio={ratio:.1f}  "
          f"Avg_Precip_T={mean_precip:.1f} ± {std_precip:.1f}  "
          f"Avg_Fe_Removal={mean_removal:.3f} ± {std_removal:.3f}")
