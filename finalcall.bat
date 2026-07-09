@echo off
set PYTHONIOENCODING=utf-8
echo Starting FARS Unified Robotics Platform...

start python "D:\fyeshi\project\rohit\simulation\r2d2_simulation_3d.py"
start python "D:\fyeshi\project\rohit\simulation\experiments\r2d2_simulation.py"
start python "D:\fyeshi\project\rohit\models\reinfrocement learning\walker_sim.py"
start python "D:\fyeshi\project\rohit\simulation\main_simulation.py"
start cmd /k "python D:\fyeshi\project\rohit\fars_platform\run.py --no-3d"

echo All simulations launched successfully!
