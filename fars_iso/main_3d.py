"""
main_3d.py -- FARS Hospital Digital Twin: Ursina 3D Simulation
Self-contained entry point in fars_iso. No dependency on full_simulation/.
Usage: python main_3d.py
"""
import sys, os, math, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursina import *
from iso_navigation import get_all_room_nodes, get_node_position, get_all_nodes
from iso_tasks import TaskManager
from iso_llm import detect_model, get_model_name, submit_command, poll_results
from ursina_world import HospitalWorld
from ursina_robots import RobotAgent
from ursina_humans import HumanAgent
from ursina_dashboard import DashboardUI

# ======================================================================
class CameraController(Entity):
    def __init__(self):
        super().__init__()
        self.distance=90; self.target_distance=90
        self.angle_x=55; self.target_angle_x=55
        self.angle_y=-30; self.target_angle_y=-30
        self.target=Vec3(5,0,5); self.desired_target=Vec3(5,0,5)
        camera.orthographic=False; camera.fov=55

    def update(self):
        dt=time.dt
        self.target=lerp(self.target,self.desired_target,dt*4)
        self.distance=lerp(self.distance,self.target_distance,dt*4)
        self.angle_x=lerp(self.angle_x,self.target_angle_x,dt*4)
        self.angle_y=lerp(self.angle_y,self.target_angle_y,dt*4)
        if mouse.middle:
            if held_keys['shift']:
                sp=0.5*self.target_distance
                px=-mouse.velocity[0]*sp; pz=-mouse.velocity[1]*sp
                rad=math.radians(self.target_angle_y)
                self.desired_target+=(Vec3(math.sin(rad),0,math.cos(rad))*pz+Vec3(math.cos(rad),0,-math.sin(rad))*px)
            else:
                self.target_angle_y+=mouse.velocity[0]*80
                self.target_angle_x-=mouse.velocity[1]*80
                self.target_angle_x=clamp(self.target_angle_x,10,85)
        if held_keys['+']: self.target_distance-=40*dt
        if held_keys['-']: self.target_distance+=40*dt
        self.target_distance=clamp(self.target_distance,15,150)
        rx=math.radians(self.angle_x); ry=math.radians(self.angle_y)
        camera.position=Vec3(self.target.x+self.distance*math.sin(ry)*math.cos(rx),self.target.y+self.distance*math.sin(rx),self.target.z-self.distance*math.cos(ry)*math.cos(rx))
        camera.look_at(self.target); camera.rotation_z=0

    def go_to_node(self, node_name):
        try:
            x,z=get_node_position(node_name)
            self.desired_target=Vec3(x,0,z); self.target_distance=40; self.target_angle_x=45
        except: pass

    def input(self, key):
        if not globals().get('typing_mode',False):
            if key=='scroll up': self.distance-=8
            if key=='scroll down': self.distance+=8

# ======================================================================
robots=[]; humans=[]; task_mgr=None; dashboard=None
patients_assisted_count=0; typing_mode=False; selected_robot_index=0; cam=None

def setup():
    global robots,humans,task_mgr,dashboard,cam
    HospitalWorld()
    RobotAgent.all_robots=[]
    for i in range(5): robots.append(RobotAgent(i))
    HumanAgent.all_humans=[]; HumanAgent._id_counter=0
    rooms=get_all_room_nodes()
    for i in range(15): humans.append(HumanAgent('patient',rooms[i%len(rooms)]))
    for _ in range(6): humans.append(HumanAgent('doctor'))
    for _ in range(6): humans.append(HumanAgent('nurse'))
    for _ in range(6): humans.append(HumanAgent('visitor'))
    task_mgr=TaskManager(); dashboard=DashboardUI(); cam=CameraController()

def update():
    global patients_assisted_count
    dt=time.dt
    if dt<=0: return
    for result in poll_results():
        src=result.pop('_src','fallback')
        if 'error' in result:
            if dashboard: dashboard.show_feedback(f"[ERROR] {result['error']}",is_error=True)
        else:
            task_mgr.create_task(result['task_type'],result['location_node'],result['priority'],result['description'])
            loc=result['location_node']
            tag=f"[AI:{src.upper()}]"
            if dashboard:
                dashboard.show_feedback(f'{tag} Robot dispatched to {loc} ({result["task_type"]})')
                task_mgr.add_alert(f'{tag} {result["description"]}')
            _highlight_room(loc)
            if cam: cam.go_to_node(loc)
    for h in humans: h.update(dt)
    task_mgr.auto_generate_from_humans(humans,dt)
    task_mgr.assign_tasks(robots)
    for r in robots: r.update(dt)
    completed=task_mgr.check_completed(robots)
    for t in completed:
        patients_assisted_count+=1
        for h in humans:
            if h.current_node==t.location_node and h.needs_help: h.fulfill_help(); break
    if dashboard:
        active=sum(1 for r in robots if r.state not in ('idle','charging'))
        m=task_mgr.get_metrics()
        dashboard.update_hud(active,len(robots),patients_assisted_count,m['completed'],m['avg_response_time'])
        dashboard.update_queue(task_mgr.get_queue_display())
        dashboard.update_active(task_mgr.get_active_display())
        dashboard.update_robots([r.get_info() for r in robots])
        dashboard.update_alerts(task_mgr.get_recent_alerts())
        if dashboard.detail_visible and 0<=selected_robot_index<len(robots):
            dashboard.show_robot_detail(robots[selected_robot_index].get_info())

def input(key):
    global typing_mode,selected_robot_index
    if key=='tab':
        typing_mode=not typing_mode
        dashboard.cam_mode.text='TYPING MODE -- Press TAB to exit' if typing_mode else 'CAM: Overview | Scroll=Zoom | Middle=Orbit | Shift+Middle=Pan'
        return
    if typing_mode:
        if key=='enter':
            cmd=dashboard.get_and_clear_command()
            if cmd: handle_command(cmd)
        else: dashboard.handle_text_input(key)
        return
    if key=='left mouse down':
        for i,r in enumerate(robots):
            if r.entity.hovered:
                selected_robot_index=i; dashboard.show_robot_detail(r.get_info())
                if cam: cam.go_to_node(r.current_node); break
    if key=='escape': dashboard.hide_robot_detail()
    for i in range(min(9,len(robots))):
        if key==str(i+1):
            selected_robot_index=i; dashboard.show_robot_detail(robots[i].get_info())
            if cam: cam.go_to_node(robots[i].current_node)

def _highlight_room(node_name):
    try:
        x,z=get_node_position(node_name)
        ring=Entity(model='cube',scale=(8,0.15,8),position=(x,0.2,z),color=color.rgb32(0,255,200),unlit=True,alpha=0.5)
        ring.animate_scale((12,0.15,12),duration=1.0,curve=curve.out_expo)
        ring.animate('alpha',0,duration=1.5,curve=curve.linear)
        destroy(ring,delay=2.0)
    except: pass

def handle_command(text):
    if dashboard: dashboard.show_feedback(f"[AI] Sending to {get_model_name()}...")
    submit_command(text)

if __name__=='__main__':
    app=Ursina(title='FARS Campus Digital Twin',borderless=False,fullscreen=False,development_mode=False,size=(1920,1080))
    window.color=color.rgb32(18,22,32); window.fps_counter.enabled=True
    setup()
    for r in robots: r.entity.collider='box'
    app.run()
