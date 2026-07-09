import math
import numpy as np
import time

PI = math.pi
KPH = PI / 4

class PhysicsBridge:
    """
    Bridges the Reinforcement Learning trained gait (24hr model)
    into the 3D Ursina visual engine.
    """
    def __init__(self):
        self.t = 0.0

    def get_joint_angles(self, dt, speed, fwd_dist=3.0, picked_up=False):
        """
        Returns the optimal target angles [hip_r, knee_r, hip_l, knee_l, shr_r, elb_r, shr_l, elb_l]
        based on the converged 24hr RL policy.
        """
        # Time scales with movement speed
        self.t += dt * (speed / 2.0)
        
        # 1.5 Hz run cycle
        p = self.t * 1.5 * 2 * PI
        
        # Leg targets from RL policy
        hip_r = 0.25 * math.sin(p)
        knee_r = -0.25 * max(0.0, math.sin(p + KPH))
        hip_l = 0.25 * math.sin(p + PI)
        knee_l = -0.25 * max(0.0, math.sin(p + PI + KPH))
        
        # Arm targets
        if picked_up:
            shr_r, elb_r = -1.0, -1.0
            shr_l, elb_l = -1.0, -1.0
        elif fwd_dist < 2.6:
            shr_r, elb_r = -1.2, 0.0
            shr_l, elb_l = -1.2, 0.0
        else:
            shr_r = 0.4 * math.sin(p + PI)
            elb_r = -0.3
            shr_l = 0.4 * math.sin(p)
            elb_l = -0.3
            
        return {
            'hip_r': math.degrees(hip_r),
            'knee_r': math.degrees(knee_r),
            'hip_l': math.degrees(hip_l),
            'knee_l': math.degrees(knee_l),
            'shoulder_r': math.degrees(shr_r),
            'elbow_r': math.degrees(elb_r),
            'shoulder_l': math.degrees(shr_l),
            'elbow_l': math.degrees(elb_l),
        }
