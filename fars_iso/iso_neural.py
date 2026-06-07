"""
iso_neural.py -- Hollywood-style Neural Network Visualizer for FARS simulation.
Renders an animated 3-layer neural network (input → hidden → output) with
glowing nodes, weighted edges, reward signal bars. Styled like OpenAI RL videos.
"""
import pygame
import math
import random


class NeuralNetViz:
    """
    Renders a small animated neural network visualization.
    Layer sizes: 4 inputs → 6 hidden → 3 outputs
    """

    LAYER_SIZES = [4, 6, 3]
    OUTPUT_LABELS = ['NAV', 'TASK', 'CHRG']
    INPUT_LABELS  = ['BAT', 'DIST', 'PRI', 'LOAD']

    def __init__(self):
        # Activation values per node (0–1 range)
        self.activations = [
            [0.5] * n for n in self.LAYER_SIZES
        ]
        self._act_targets = [
            [random.random() for _ in range(n)] for n in self.LAYER_SIZES
        ]
        # Edge weights [from_layer][from_node][to_node]
        self.weights = []
        for l in range(len(self.LAYER_SIZES) - 1):
            layer_w = []
            for _ in range(self.LAYER_SIZES[l]):
                layer_w.append([random.uniform(-1, 1) for _ in range(self.LAYER_SIZES[l + 1])])
            self.weights.append(layer_w)

        self._weight_targets = [
            [[random.uniform(-1, 1) for _ in range(self.LAYER_SIZES[l + 1])]
             for _ in range(self.LAYER_SIZES[l])]
            for l in range(len(self.LAYER_SIZES) - 1)
        ]

        self._anim_time = 0.0
        self.reward_signal = 0.0
        self.reward_display = 0.0       # Smoothed version for bar
        self.episode = 0
        self.cumulative_reward = 0.0
        self._pulse_nodes = {}          # node (l, i) -> pulse_life (0–1)

    def update(self, dt, robot=None):
        """Update activations and weights from robot state."""
        self._anim_time += dt

        # Smooth activations toward targets
        for l, layer in enumerate(self.activations):
            for i in range(len(layer)):
                self.activations[l][i] += (
                    (self._act_targets[l][i] - self.activations[l][i]) * min(1, dt * 3)
                )

        # Smooth weights
        for l in range(len(self.weights)):
            for i in range(len(self.weights[l])):
                for j in range(len(self.weights[l][i])):
                    self.weights[l][i][j] += (
                        (self._weight_targets[l][i][j] - self.weights[l][i][j]) * min(1, dt * 2)
                    )

        # Pull from robot if provided
        if robot:
            self.reward_signal = robot.reward_signal
            self.episode = robot.episode_count
            self.cumulative_reward = robot.cumulative_reward

            # Map robot state to input activations
            self._act_targets[0][0] = robot.battery / 100.0
            self._act_targets[0][1] = 0.8 if robot.state in ('navigating', 'returning') else 0.2
            self._act_targets[0][2] = (robot.task.priority / 4.0) if robot.task else 0.1
            self._act_targets[0][3] = float(robot.state not in ('idle', 'charging'))

            # Output: which action is "winning"
            if robot.state == 'navigating':
                self._act_targets[2][0] = 0.9
                self._act_targets[2][1] = 0.3
                self._act_targets[2][2] = 0.1
            elif robot.state in ('guiding', 'delivering', 'assisting'):
                self._act_targets[2][0] = 0.3
                self._act_targets[2][1] = 0.9
                self._act_targets[2][2] = 0.1
            elif robot.state == 'charging':
                self._act_targets[2][0] = 0.1
                self._act_targets[2][1] = 0.1
                self._act_targets[2][2] = 0.9

            # Hidden layer — noisy, pulsing
            for i in range(6):
                phase = self._anim_time * (1.5 + i * 0.3) + i
                self._act_targets[1][i] = max(0, min(1,
                    0.5 + 0.4 * math.sin(phase) + random.uniform(-0.1, 0.1)
                ))

            # Spike weights on reward
            if robot.reward_signal > 0.5:
                self._weight_targets = [
                    [[random.uniform(-1, 1) for _ in range(self.LAYER_SIZES[l + 1])]
                     for _ in range(self.LAYER_SIZES[l])]
                    for l in range(len(self.LAYER_SIZES) - 1)
                ]
        else:
            # Autonomous drift
            if self._anim_time % 2.0 < dt * 60:
                self._act_targets = [
                    [random.uniform(0.1, 0.9) for _ in range(n)] for n in self.LAYER_SIZES
                ]

        self.reward_display += (self.reward_signal - self.reward_display) * min(1, dt * 8)

        # Decay pulse nodes
        for key in list(self._pulse_nodes.keys()):
            self._pulse_nodes[key] = max(0, self._pulse_nodes[key] - dt * 3)
            if self._pulse_nodes[key] <= 0:
                del self._pulse_nodes[key]

    def draw(self, surf, rect, robot_color=(0, 200, 255)):
        """Draw the neural network in the given rect."""
        x, y, w, h = rect

        # Background
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (8, 10, 18, 230), bg.get_rect(), border_radius=6)
        pygame.draw.rect(bg, (*robot_color, 60), bg.get_rect(), 1, border_radius=6)
        surf.blit(bg, (x, y))

        # Layout
        net_y_top = y + 12
        net_h = h - 50  # leave space for reward bar at bottom
        layer_count = len(self.LAYER_SIZES)

        # Compute node positions
        node_positions = []
        for l, count in enumerate(self.LAYER_SIZES):
            lx = x + w * (l + 1) / (layer_count + 1)
            positions = []
            for i in range(count):
                ly = net_y_top + net_h * (i + 1) / (count + 1)
                positions.append((int(lx), int(ly)))
            node_positions.append(positions)

        # Draw edges first
        for l in range(len(self.LAYER_SIZES) - 1):
            for i, (fx, fy) in enumerate(node_positions[l]):
                for j, (tx, ty) in enumerate(node_positions[l + 1]):
                    w_val = self.weights[l][i][j]  # -1 to 1
                    act_in = self.activations[l][i]
                    brightness = abs(w_val) * act_in
                    if w_val > 0:
                        ec = (int(40 + 80 * brightness), int(140 + 115 * brightness), int(80 + 120 * brightness))
                    else:
                        ec = (int(140 + 115 * brightness), int(40 + 50 * brightness), int(40 + 80 * brightness))
                    alpha = int(30 + 180 * brightness)
                    edge_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                    pygame.draw.line(edge_surf, (*ec, alpha), (fx, fy), (tx, ty), 1)
                    surf.blit(edge_surf, (0, 0))

        # Draw nodes
        node_r = 7
        for l, layer_positions in enumerate(node_positions):
            for i, (nx, ny) in enumerate(layer_positions):
                act = self.activations[l][i]
                # Glow
                if act > 0.3:
                    glow_r = int(node_r + 8 * act)
                    glow_surf = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
                    gc = (*robot_color, int(60 * act))
                    pygame.draw.circle(glow_surf, gc, (glow_r + 1, glow_r + 1), glow_r)
                    surf.blit(glow_surf, (nx - glow_r - 1, ny - glow_r - 1))

                # Node body
                bright = 0.3 + 0.7 * act
                nc = tuple(min(255, int(c * bright)) for c in robot_color)
                border_c = (min(255, int(c * 0.6)) for c in robot_color)
                pygame.draw.circle(surf, tuple(min(255, int(c * 0.15)) for c in robot_color),
                                   (nx, ny), node_r + 1)  # dark bg
                pygame.draw.circle(surf, nc, (nx, ny), node_r)

                # Label for input/output layers
                font_size = 8
                try:
                    f = pygame.font.SysFont('consolas', font_size)
                except Exception:
                    f = pygame.font.SysFont(None, font_size)

                if l == 0 and i < len(self.INPUT_LABELS):
                    lbl = f.render(self.INPUT_LABELS[i], True, (100, 110, 130))
                    surf.blit(lbl, (nx - node_r - lbl.get_width() - 2, ny - lbl.get_height() // 2))
                elif l == len(self.LAYER_SIZES) - 1 and i < len(self.OUTPUT_LABELS):
                    lbl = f.render(self.OUTPUT_LABELS[i], True, robot_color)
                    surf.blit(lbl, (nx + node_r + 3, ny - lbl.get_height() // 2))

        # Reward signal bar
        bar_y = y + h - 34
        try:
            f_sm = pygame.font.SysFont('consolas', 9)
        except Exception:
            f_sm = pygame.font.SysFont(None, 9)

        # Reward label
        rew_lbl = f_sm.render(f'REWARD  EP:{self.episode}  Σ:{self.cumulative_reward:.0f}', True, (120, 130, 150))
        surf.blit(rew_lbl, (x + 6, bar_y))
        bar_y += 12

        # Reward bar background
        bw = w - 12
        pygame.draw.rect(surf, (18, 20, 30), (x + 6, bar_y, bw, 8), border_radius=2)

        # Reward bar fill — glows gold when high
        fill = int(bw * self.reward_display)
        if fill > 0:
            pulse = 0.7 + 0.3 * math.sin(self._anim_time * 12)
            rew_c = (int(255 * pulse), int(200 * pulse), int(40 * self.reward_display * pulse))
            pygame.draw.rect(surf, rew_c, (x + 6, bar_y, fill, 8), border_radius=2)

        # Glow on bar when reward is high
        if self.reward_display > 0.3:
            glow_s = pygame.Surface((bw + 10, 18), pygame.SRCALPHA)
            gc = (255, 200, 40, int(60 * self.reward_display))
            pygame.draw.rect(glow_s, gc, glow_s.get_rect(), border_radius=3)
            surf.blit(glow_s, (x + 1, bar_y - 5))
