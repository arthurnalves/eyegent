from nes_py.wrappers import JoypadSpace
import gym_super_mario_bros
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
from gym import wrappers
from IPython.display import Video
import io
import base64
from IPython.display import HTML
import numpy as np
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
import copy

from agent_model import AgentModel

class Agent:
    
    eyemodel = None
    model = None
    state = None
    total_reward = None
    reward = None
    done = None
    info = None
    next_state = None
    update = None
    buffer = None
    freq = None
    intensity = None
    env = None
    ID = None
    lineage = None
    max_steps = None
    fps = None
    lazy_penalty = None
    
    def __init__(self, ID = -1, update = ['reward'], buffer = 3, max_steps = 500, freq = .25, intensity = .25, fps = 5):
        
        self.buffer = buffer
        self.freq = freq
        self.intensity = intensity
        self.env = self.make_env()
        self.start_model()
        self.update = update
        self.state = deque(maxlen = buffer*fps + 1)
        self.ID = ID
        self.max_steps = max_steps
        self.lineage = []
        self.fps = fps
        self.lazy_penalty = -30
        self.death_penalty = -50
        for _ in range(buffer):
            self.state.append(np.zeros(self.env.observation_space.shape))
        
        
    def make_env(self, mode = None, rom_id = 'SuperMarioBros-v0'):
        env = gym_super_mario_bros.make(rom_id)
        env = JoypadSpace(env, SIMPLE_MOVEMENT)
        if mode == 'monitor':
            env = wrappers.Monitor(env, directory, force = True)
        return env 
    
    def start_model(self):
        env = self.make_env()
        self.model = AgentModel(buffer = self.buffer, input_shape = env.observation_space.shape, output_dim = env.action_space.n)
    
    def get_buffered_images(self):
        buffered_states = []
        for i in range(self.buffer):
            buffered_states.append(self.state[(i + 1)*self.fps - 1])
        return buffered_states
    
    def take_action(self):
        input_imgs = []
        for input_img in self.get_buffered_images():
            input_imgs.append(np.expand_dims(input_img, axis = 0))
        prediction = self.model.predict(input_imgs)
        return np.argmax(prediction)

    def reset_data(self):
        for i in range(self.buffer*self.fps + 1):
            self.state.append(np.zeros(self.env.observation_space.shape))
        self.total_reward = 0
        self.reward = []
        self.done = []
        self.info = dict()
        self.next_state = []
    
    def gather_data(self, step, state, reward, done, info, next_state):
        self.total_reward += reward
        if step%self.fps == 0:
            self.state.append(np.array(state))

    def run(self, max_steps = 500, mode = None, directory = './gym-results/'):    
        env = self.make_env(mode = mode)
        self.reset_data()
        
        patience = 3
        resting = 0
        x_pos = 0
        state = env.reset()
        prev_state = state
        done = False
        for step in range(max_steps):

            if step%self.fps == 0:
                action = self.take_action()
                
            next_state, reward, done, info = env.step(action)
                            
            if info['x_pos'] > x_pos:
                x_pos = info['x_pos']
                resting = 0
                
            if abs(info['x_pos'] - x_pos) < 5:
                resting += 1
                
            if resting > patience*60:
                self.total_reward += self.lazy_penalty
                break
                
            if info['life'] < 2: 
                self.total_reward += self.death_penalty
                break

            self.gather_data(step, state, reward, done, info, next_state)
            prev_state = state
            state = next_state

            if mode == 'render':
                env.render()

        if mode == 'monitor':
            file_name = directory + 'openaigym.video.%s.video000000.mp4'% env.file_infix
            mp4 = Video(file_name, width = 600, height = 450)
            display(mp4)

        if mode == 'render':    
            env.close()
    
    def get_reward(self):
        if self.total_reward == None:
            self.run()
        return self.total_reward

    def itsame(self):
        return 'Mario!'
    
    def copy_model(self, other, new_ID):
        self.ID = new_ID
        self.lineage = copy.copy(other.lineage)
        if other.ID not in self.lineage:
            self.lineage.append(other.ID)
            
        self.model.set_weights(other.model.get_weights())

    def mutate(self):
        self.model.mutate(freq = self.freq, intensity = self.intensity)
        self.total_reward = None
        
    def print_state(self):
        fig = plt.figure(figsize=(16., 12.))
        grid = ImageGrid(fig, 111,  # similar to subplot(111)
                         nrows_ncols=(1, self.buffer),  # creates 2x2 grid of axes
                         axes_pad=0.1,)  # pad between axes in inch.

        
        for ax, im in zip(grid, self.get_buffered_images()):
            # Iterating over the grid returns the Axes.
            ax.imshow(im)
            ax.set_xticklabels([])
            ax.set_yticklabels([])
        plt.show()