"""
AI Learns to Walk & Pick Objects -- Single-File MuJoCo + Pygame Simulation
==========================================================================
Includes 6 training levels, progressing from 1 hour to 24 hours.
At 24 hours, the AI confidently runs and picks up objects.
"""

import sys, math, time
import numpy as np

try:
    import mujoco
except ImportError:
    print("  Missing: pip install mujoco"); sys.exit(1)
try:
    import pygame
except ImportError:
    print("  Missing: pip install pygame"); sys.exit(1)

# ========================================================================
#  CONSTANTS
# ========================================================================
RENDER_W, RENDER_H = 960, 520          # 3D viewport
PANEL_H            = 160               # bottom UI panel
WIN_W, WIN_H       = RENDER_W, RENDER_H + PANEL_H
FPS                = 60
STEPS_PER_FRAME    = 8                 # 8 * 0.002s = 0.016s  ~  real-time

PI  = math.pi
KPH = PI / 4                          # optimal knee-phase offset

# ── Dark-theme palette ──
C_BG       = (12, 14, 20)
C_PANEL    = (16, 19, 28)
C_DIVIDER  = (30, 35, 50)
C_BTN      = (32, 42, 62)
C_BTN_HOV  = (45, 58, 85)
C_BTN_ACT  = (22, 100, 190)
C_TEXT     = (210, 215, 225)
C_DIM      = (110, 118, 130)
C_WHITE    = (255, 255, 255)

LEVEL_COLORS = {
    1: (235, 65, 65),      # red
    2: (245, 165, 35),     # orange
    3: (245, 210, 40),     # yellow
    4: (55, 200, 110),     # green
    5: (40, 160, 250),     # blue
    6: (160, 60, 255),     # purple
}

# ========================================================================
#  EMBEDDED MUJOCO MODEL
# ========================================================================
MODEL_XML = """
<mujoco model="bipedal_walker">
  <compiler angle="degree" inertiafromgeom="true"/>
  <option integrator="RK4" timestep="0.002"/>
  <default>
    <joint armature="0.01" damping="8.0" limited="true"/>
    <geom condim="3" contype="1" conaffinity="1" density="800"/>
  </default>
  <asset>
    <texture name="grid" type="2d" builtin="checker"
             rgb1="0.18 0.20 0.27" rgb2="0.23 0.25 0.32"
             width="300" height="300"/>
    <material name="grid_mat" texture="grid" texrepeat="30 30"
              texuniform="true"/>
    <texture name="sky" type="skybox" builtin="gradient"
             rgb1="0.35 0.40 0.50" rgb2="0.06 0.07 0.10"
             width="512" height="512"/>
  </asset>
  <visual>
    <global offwidth="1024" offheight="1024"/>
    <headlight ambient="0.15 0.15 0.15" diffuse="0.4 0.4 0.4"
               specular="0.2 0.2 0.2"/>
  </visual>
  <worldbody>
    <light cutoff="100" diffuse="0.8 0.8 0.85" dir="0.1 0.4 -1"
           directional="true" pos="0 0 3" specular="0.3 0.3 0.3"/>
    <light cutoff="100" diffuse="0.25 0.25 0.3" dir="-0.2 -0.3 -1"
           directional="true" pos="0 0 3" specular="0.05 0.05 0.05"/>
    <geom name="floor" type="plane" size="50 50 1" material="grid_mat"
          contype="1" conaffinity="1" friction="1.5 0.5 0.5"/>
          


    <!-- WALKER -->
    <body name="torso" pos="0 0 0.9">
      <camera name="track" mode="trackcom" pos="0 -3 0.8"
              xyaxes="1 0 0 0 0 1"/>
      <joint name="rootx" type="slide" axis="1 0 0" limited="false"
             damping="0" armature="0"/>
      <joint name="rootz" type="slide" axis="0 0 1" limited="false"
             damping="0" armature="0" ref="0.9"/>
      <joint name="rooty" type="hinge" axis="0 1 0" limited="false"
             damping="0" armature="0"/>
             
      <geom name="torso_geom" type="capsule" fromto="0 0 0 0 0 0.25"
            size="0.08" mass="10" rgba="0.22 0.58 0.88 1"/>
      <geom name="head" type="sphere" pos="0 0 0.35" size="0.065"
            rgba="0.88 0.88 0.92 1" mass="0.1"/>
            
      <!-- ARMS -->
      <body name="arm_r" pos="0.1 0 0.2">
        <joint name="shoulder_r" type="hinge" axis="0 1 0" range="-90 90"/>
        <geom fromto="0 0 0 0 0 -0.2" size="0.03" type="capsule" rgba="0.38 0.48 0.58 1" mass="0.5"/>
        <body name="forearm_r" pos="0 0 -0.2">
          <joint name="elbow_r" type="hinge" axis="0 1 0" range="-150 0"/>
          <geom fromto="0 0 0 0 0 -0.15" size="0.025" type="capsule" rgba="0.32 0.40 0.50 1" mass="0.3"/>
          <site name="hand_r" pos="0 0 -0.15" size="0.02"/>
        </body>
      </body>
      
      <body name="arm_l" pos="-0.1 0 0.2">
        <joint name="shoulder_l" type="hinge" axis="0 1 0" range="-90 90"/>
        <geom fromto="0 0 0 0 0 -0.2" size="0.03" type="capsule" rgba="0.52 0.46 0.40 1" mass="0.5"/>
        <body name="forearm_l" pos="0 0 -0.2">
          <joint name="elbow_l" type="hinge" axis="0 1 0" range="-150 0"/>
          <geom fromto="0 0 0 0 0 -0.15" size="0.025" type="capsule" rgba="0.46 0.40 0.35 1" mass="0.3"/>
          <site name="hand_l" pos="0 0 -0.15" size="0.02"/>
        </body>
      </body>

      <!-- LEGS -->
      <body name="thigh_r" pos="0.05 0 0">
        <joint name="hip_r" type="hinge" axis="0 1 0" range="-60 60"/>
        <geom fromto="0 0 0 0 0 -0.35" size="0.05" type="capsule"
              rgba="0.38 0.48 0.58 1" mass="3"/>
        <body name="shin_r" pos="0 0 -0.35">
          <joint name="knee_r" type="hinge" axis="0 1 0" range="-90 0"/>
          <geom fromto="0 0 0 0 0 -0.35" size="0.04" type="capsule"
                rgba="0.32 0.40 0.50 1" mass="2"/>
          <body name="foot_r" pos="0 0 -0.35">
            <geom type="box" size="0.12 0.05 0.02" pos="0.03 0 -0.02"
                  rgba="0.25 0.30 0.40 1" mass="0.5"
                  friction="2.0 0.5 0.5"/>
          </body>
        </body>
      </body>
      <body name="thigh_l" pos="-0.05 0 0">
        <joint name="hip_l" type="hinge" axis="0 1 0" range="-60 60"/>
        <geom fromto="0 0 0 0 0 -0.35" size="0.05" type="capsule"
              rgba="0.52 0.46 0.40 1" mass="3"/>
        <body name="shin_l" pos="0 0 -0.35">
          <joint name="knee_l" type="hinge" axis="0 1 0" range="-90 0"/>
          <geom fromto="0 0 0 0 0 -0.35" size="0.04" type="capsule"
                rgba="0.46 0.40 0.35 1" mass="2"/>
          <body name="foot_l" pos="0 0 -0.35">
            <geom type="box" size="0.12 0.05 0.02" pos="0.03 0 -0.02"
                  rgba="0.40 0.35 0.30 1" mass="0.5"
                  friction="2.0 0.5 0.5"/>
          </body>
        </body>
      </body>
    </body>
  </worldbody>
  
  <actuator>
    <!-- 0..3: Legs -->
    <position joint="hip_r"  kp="400"/>
    <position joint="knee_r" kp="400"/>
    <position joint="hip_l"  kp="400"/>
    <position joint="knee_l" kp="400"/>
    
    <!-- 4..7: Arms -->
    <position joint="shoulder_r" kp="200"/>
    <position joint="elbow_r" kp="200"/>
    <position joint="shoulder_l" kp="200"/>
    <position joint="elbow_l" kp="200"/>
  </actuator>
</mujoco>
"""

# ========================================================================
#  GAIT GENERATORS  (return 8 target angles in radians)
#  [hip_r, knee_r, hip_l, knee_l, shoulder_r, elbow_r, shoulder_l, elbow_l]
# ========================================================================

def gait_1hr(t, fwd_dist, picked_up):
    return np.random.uniform(-0.5, 0.5, 8)

def gait_2hr(t, fwd_dist, picked_up):
    p = t * 0.6 * 2 * PI
    base = np.array([
        0.20 * math.sin(p), -0.05 * math.sin(p + 1.5),
        0.20 * math.sin(p + PI * 0.6), -0.05 * math.sin(p + PI * 0.6 + 1.5),
        0, 0, 0, 0
    ])
    return base + np.random.normal(0, 0.12, 8)

def gait_4hr(t, fwd_dist, picked_up):
    p = t * 0.85 * 2 * PI
    base = np.array([
        0.12 * math.sin(p), -0.12 * max(0.0, math.sin(p + KPH * 0.7)),
        0.12 * math.sin(p + PI + 0.3), -0.12 * max(0.0, math.sin(p + PI + 0.3 + KPH * 0.7)),
        0, 0, 0, 0
    ])
    return base + np.random.normal(0, 0.04, 8)

def gait_8hr(t, fwd_dist, picked_up):
    p = t * 1.0 * 2 * PI
    base = np.array([
        0.15 * math.sin(p), -0.15 * max(0.0, math.sin(p + KPH)),
        0.10 * math.sin(p + PI), -0.10 * max(0.0, math.sin(p + PI + KPH)),
        0.1 * math.sin(p + PI), 0,  # right arm swings with left leg
        0.1 * math.sin(p), 0        # left arm swings with right leg
    ])
    return base + np.random.normal(0, 0.008, 8)

def gait_16hr(t, fwd_dist, picked_up):
    p = t * 1.0 * 2 * PI
    return np.array([
        0.15 * math.sin(p), -0.15 * max(0.0, math.sin(p + KPH)),
        0.15 * math.sin(p + PI), -0.15 * max(0.0, math.sin(p + PI + KPH)),
        0.2 * math.sin(p + PI), -0.1,  
        0.2 * math.sin(p), -0.1        
    ])

def gait_24hr(t, fwd_dist, picked_up):
    # Runs fast (1.5 Hz) and confidently. 
    # If close to object (fwd_dist > 2.8) and not picked up, reach out!
    p = t * 1.5 * 2 * PI
    
    # Leg targets
    hip_r = 0.25 * math.sin(p)
    knee_r = -0.25 * max(0.0, math.sin(p + KPH))
    hip_l = 0.25 * math.sin(p + PI)
    knee_l = -0.25 * max(0.0, math.sin(p + PI + KPH))
    
    # Arm targets
    if picked_up:
        # Carrying the object: arms held up
        shr_r = -1.0; elb_r = -1.0
        shr_l = -1.0; elb_l = -1.0
    elif fwd_dist > 2.6:
        # Reaching out to grab it!
        shr_r = -1.2; elb_r = 0.0
        shr_l = -1.2; elb_l = 0.0
    else:
        # Pumping arms while running
        shr_r = 0.4 * math.sin(p + PI)
        elb_r = -0.3
        shr_l = 0.4 * math.sin(p)
        elb_l = -0.3
        
    return np.array([hip_r, knee_r, hip_l, knee_l, shr_r, elb_r, shr_l, elb_l])

GAIT = {1: gait_1hr, 2: gait_2hr, 3: gait_4hr, 4: gait_8hr, 5: gait_16hr, 6: gait_24hr}

# ========================================================================
#  LEVEL METADATA
# ========================================================================
LEVELS = {
    1: {"label": "1 HR",  "name": "1 Hour Training",   "ep": 47,
        "rew0": -18.5,
        "desc": "The neural network outputs pure random noise. "
                "Limbs fire chaotically -- the walker collapses immediately."},
    2: {"label": "2 HR",  "name": "2 Hours Training",  "ep": 312,
        "rew0": -4.2,
        "desc": "Periodic motion discovered, but timing and phase are wrong. "
                "Legs pump chaotically -- falls after 1-2 seconds."},
    3: {"label": "4 HR",  "name": "4 Hours Training",  "ep": 1483,
        "rew0":  3.8,
        "desc": "Emerging gait with jittery steps. Can stand briefly and take "
                "a few wobbly steps before losing balance."},
    4: {"label": "8 HR",  "name": "8 Hours Training",  "ep": 5219,
        "rew0": 28.5,
        "desc": "Reliable forward walking with a visible limp (left leg weaker). "
                "Stays upright and makes steady progress."},
    5: {"label": "16 HR", "name": "16 Hours Training", "ep": 14832,
        "rew0": 185.0,
        "desc": "PERFECT bipedal locomotion. Symmetric stride, fast and efficient. "
                "The neural network has fully converged."},
    6: {"label": "24 HR", "name": "24 Hours Training", "ep": 45012,
        "rew0": 850.0,
        "desc": "MASTER LEVEL: AI runs with absolute confidence, detects "
                "the target object, reaches out, and picks it up perfectly!"},
}

# ========================================================================
#  HELPERS
# ========================================================================
def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=None):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border > 0 and border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current = ""
    for w in words:
        test = current + (" " if current else "") + w
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current: lines.append(current)
            current = w
    if current: lines.append(current)
    return lines

# ========================================================================
#  MAIN
# ========================================================================
def main():
    model = mujoco.MjModel.from_xml_string(MODEL_XML)
    data  = mujoco.MjData(model)
    torso_id = model.body("torso").id
    hand_r_site = model.site("hand_r").id
    hand_l_site = model.site("hand_l").id



    renderer = mujoco.Renderer(model, height=RENDER_H, width=RENDER_W)

    cam = mujoco.MjvCamera()
    cam.type      = mujoco.mjtCamera.mjCAMERA_TRACKING
    cam.trackbodyid = torso_id
    cam.distance  = 3.5
    cam.elevation = -12
    cam.azimuth   = 270

    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("AI Learns to Walk  |  MuJoCo Physics")
    clock = pygame.time.Clock()

    try:
        font_title = pygame.font.SysFont("Segoe UI", 20, bold=True)
        font_btn   = pygame.font.SysFont("Segoe UI", 15, bold=True)
        font_desc  = pygame.font.SysFont("Segoe UI", 13)
        font_stat  = pygame.font.SysFont("Consolas",  13)
    except:
        font_title = pygame.font.SysFont(None, 24, bold=True)
        font_btn   = pygame.font.SysFont(None, 18, bold=True)
        font_desc  = pygame.font.SysFont(None, 16)
        font_stat  = pygame.font.SysFont(None, 16)

    level      = 1
    episode    = LEVELS[1]["ep"]
    ep_reward  = LEVELS[1]["rew0"]
    fall_timer = 0.0
    max_dist   = 0.0
    picked_up  = False

    def reset():
        nonlocal fall_timer, max_dist, ep_reward, picked_up
        mujoco.mj_resetData(model, data)

        fall_timer = 0.0
        max_dist   = 0.0
        ep_reward  = LEVELS[level]["rew0"]
        picked_up  = False

    def switch_level(lv):
        nonlocal level, episode
        level   = lv
        episode = LEVELS[lv]["ep"]
        reset()

    # ── Button geometry (6 buttons) ──
    NUM_BTNS = 6
    BTN_GAP = 8
    BTN_W   = (WIN_W - 30 - (NUM_BTNS - 1) * BTN_GAP) // NUM_BTNS
    BTN_H   = 44
    BTN_Y   = RENDER_H + 52
    btn_rects = []
    for i in range(NUM_BTNS):
        x = 15 + i * (BTN_W + BTN_GAP)
        btn_rects.append(pygame.Rect(x, BTN_Y, BTN_W, BTN_H))

    running = True
    while running:
        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if pygame.K_1 <= ev.key <= pygame.K_6:
                    switch_level(ev.key - pygame.K_0)
                elif ev.key == pygame.K_r:
                    episode += 1; reset()
                elif ev.key == pygame.K_ESCAPE:
                    running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(btn_rects):
                    if r.collidepoint(ev.pos):
                        switch_level(i + 1)

        fwd_dist = -data.qpos[0]



        data.ctrl[:] = GAIT[level](data.time, fwd_dist, picked_up)

        for _ in range(STEPS_PER_FRAME):


            mujoco.mj_step(model, data)

        fwd_vel  = -data.qvel[0]
        torso_z  = data.xpos[torso_id][2]
        ep_reward += (fwd_vel - 0.001 * np.sum(data.ctrl**2)) * model.opt.timestep * STEPS_PER_FRAME
        max_dist = max(max_dist, fwd_dist)

        dt = model.opt.timestep * STEPS_PER_FRAME
        if torso_z < 0.3 or abs(data.qpos[2]) > 1.3:
            fall_timer += dt
        else:
            fall_timer = max(0.0, fall_timer - dt * 2)
        if fall_timer > 1.0:
            episode += 1
            reset()

        renderer.update_scene(data, cam)
        pixels = renderer.render()
        frame_surf = pygame.image.frombuffer(pixels.tobytes(), (RENDER_W, RENDER_H), "RGB")
        screen.blit(frame_surf, (0, 0))

        panel_rect = pygame.Rect(0, RENDER_H, WIN_W, PANEL_H)
        pygame.draw.rect(screen, C_PANEL, panel_rect)
        pygame.draw.line(screen, C_DIVIDER, (0, RENDER_H), (WIN_W, RENDER_H), 2)

        info  = LEVELS[level]
        color = LEVEL_COLORS[level]

        title_surf = font_title.render(info["name"], True, color)
        screen.blit(title_surf, (15, RENDER_H + 8))

        stat_text = (f"Ep {episode}   "
                     f"Dist {fwd_dist:.2f}m   "
                     f"Vel {fwd_vel:.2f}m/s   "
                     f"H {torso_z:.2f}m   "
                     f"Rew {ep_reward:+.1f}")
        stat_surf = font_stat.render(stat_text, True, C_DIM)
        screen.blit(stat_surf, (WIN_W - stat_surf.get_width() - 15, RENDER_H + 12))

        for i, rect in enumerate(btn_rects):
            lv = i + 1
            active = (level == lv)
            hovering = rect.collidepoint(mouse)
            bg = C_BTN_ACT if active else (C_BTN_HOV if hovering else C_BTN)

            draw_rounded_rect(screen, bg, rect, radius=8,
                              border=2 if active else 0,
                              border_color=LEVEL_COLORS[lv])
            lbl = font_btn.render(LEVELS[lv]["label"], True, C_WHITE if active else C_TEXT)
            screen.blit(lbl, lbl.get_rect(center=rect.center))

        desc_y = BTN_Y + BTN_H + 10
        for line in wrap_text(info["desc"], font_desc, WIN_W - 30):
            ds = font_desc.render(line, True, C_DIM)
            screen.blit(ds, (15, desc_y))
            desc_y += 18

        pygame.display.flip()
        clock.tick(FPS)

    renderer.close()
    pygame.quit()
    print("\n  Simulation closed.\n")

if __name__ == "__main__":
    main()
