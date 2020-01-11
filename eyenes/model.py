from keras.models import Sequential
from keras.layers import Dense

from keras.models import Sequential, Model
from keras.layers import Dense, Conv2D, LSTM, MaxPooling2D, AveragePooling2D, ZeroPadding2D, Flatten, Reshape
from keras.layers import Softmax, Input, Concatenate, Embedding, Activation, Lambda, Input
from keras.utils import to_categorical
from keras.optimizers import RMSprop
from keras.models import model_from_json
from keras.initializers import glorot_uniform

import numpy as np
import random

class AgentModel:
    
    model = None
    eye_model = None
    action_model = None
    input_shape = None
    output_dim = None
    activation = None
    buffer = None
    eye_output_dim = None
    layer_prob = None
    
    def __init__(self, buffer, input_shape, output_dim, eye_output_dim = 64, activation = 'relu'):
        self.buffer = buffer
        w, h, c = input_shape
        self.input_shape = (w, h, c*buffer)
        self.output_dim = output_dim
        self.activation = activation
        self.layer_prob = .25
        if eye_output_dim == None:
            self.eye_output_dim = output_dim
        else:
            self.eye_output_dim = eye_output_dim
        self.start_model()
        
    
    def start_eye_model(self):
        w, h, _ = self.input_shape
        max_dim = max([w,h])
        activation = self.activation

        self.eye_model = Sequential()

        self.eye_model.add(Lambda(lambda x: x/255., input_shape = self.input_shape))        
        self.eye_model.add(ZeroPadding2D(padding = ((max_dim - w)//2, (max_dim - h)//2)))
        self.eye_model.add(MaxPooling2D((4,4)))

        self.eye_model.add(Conv2D(4, 4, strides=(2, 2), padding="same", activation=activation))
        self.eye_model.add(Conv2D(8, 4, strides=(2, 2), padding="same", activation=activation))
        self.eye_model.add(Conv2D(16,4, strides=(2, 2), padding="same", activation=activation))
        self.eye_model.add(Conv2D(32,4, strides=(2, 2), padding="same", activation=activation))
        self.eye_model.add(Conv2D(64,4, strides=(2, 2), padding="same", activation=activation))

        self.eye_model.add(Flatten())
        self.eye_model.add(Dense(self.eye_output_dim, activation= activation))

    def start_action_model(self):
        
        output_imgs = []
        for i in range(self.buffer):
            output_imgs.append(Input((self.eye_output_dim,)))
        
        output = Concatenate(axis = -1)(output_imgs)
        output = Reshape([self.buffer, self.eye_output_dim])(output)
        output = LSTM(self.eye_output_dim, activation = self.activation)(output)
        output = Dense(self.output_dim, activation = self.activation)(output)
        
        self.action_model = Model(inputs = output_imgs, outputs = output)

    def start_model(self):
        if self.eye_model == None:
            self.start_eye_model()
        
        if self.action_model == None:
            self.start_action_model()
            
        input_imgs = []
        for i in range(self.buffer):
            input_imgs.append(Input(self.input_shape))

        output_imgs = []
        for input_img in input_imgs:
            output_img = input_img
            for layer in self.eye_model.layers:
                output_img = layer(output_img)
            output_imgs.append(output_img)
            
        output = output_imgs
        for layer in self.action_model.layers:
            output = layer(output)
            
        self.model = Model(inputs = input_imgs, outputs = output)        
        
    def mutate(self, freq, intensity):
        mutated_weights = []
        for weight in self.model.get_weights():
            A = np.random.choice([0,1], p=[1-freq, freq], size = np.shape(weight))
            A = A*intensity
            glorot = glorot_uniform().__call__(np.shape(weight))
            if random.random() < self.layer_prob:
                mutated_weights.append(A*glorot + (1-A)*weight)
            else:
                mutated_weights.append(weight)

        self.model.set_weights(mutated_weights)
            
    def summary(self):
        return self.model.summary()
    
    def get_weights(self):
        return self.model.get_weights()
    
    def set_weights(self, weights):
        return self.model.set_weights(weights)
    
    def predict(self, inputs):
        return self.model.predict(inputs)