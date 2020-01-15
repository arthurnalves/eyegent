from keras.models import Sequential
from keras.layers import Dense

from keras.models import Sequential, Model
from keras.layers import Dense, SeparableConv2D, Conv2D, LSTM, MaxPooling2D, AveragePooling2D, ZeroPadding2D, Flatten, Reshape
from keras.layers import Softmax, Input, Concatenate, Embedding, Activation, Lambda, Input
from keras.utils import to_categorical
from keras.optimizers import RMSprop
from keras.models import model_from_json
from keras.initializers import glorot_uniform
from keras.activations import relu

import numpy as np
import random

# Custom activation function
from keras.layers import Activation
from keras import backend as K
from keras.utils.generic_utils import get_custom_objects
from keras.backend import switch


from keras import backend as K

def custom_activation(x):
    return K.switch(x > 1, K.ones_like(x), K.switch(x < -1, -K.ones_like(x), K.zeros_like(x)))

class AgentModel:
    
    def __init__(self, buffer, input_shape, output_dim, black_and_white = False, eye_output_dim = 64):
        self.buffer = buffer
        w, h, c = input_shape
        self.black_and_white = black_and_white
        if self.black_and_white:
            self.input_shape = (w, h, buffer)
        else:
            self.input_shape = (w, h, c*buffer)

        self.output_dim = output_dim
        self.layer_prob = .25
        if eye_output_dim == None:
            self.eye_output_dim = output_dim
        else:
            self.eye_output_dim = eye_output_dim
        self.start_model()

    def start_model(self):
        w, h, _ = self.input_shape
        max_dim = max([w,h])

        c = self.input_shape[-1]

        self.model = Sequential()
        self.model.add(Lambda(lambda x: x/255., batch_input_shape = np.append(1, self.input_shape)))        
        self.model.add(ZeroPadding2D(padding = ((max_dim - w)//2, (max_dim - h)//2)))
        
        self.model.add(AveragePooling2D((2,2)))
        self.model.add(SeparableConv2D(c, 4, activation = 'relu', strides = (4,4), padding="same"))

        self.model.add(Conv2D(c*2, 16, activation = 'relu', strides=(2, 2), padding="same"))
        self.model.add(Conv2D(c*4, 8, activation = 'relu', strides=(2, 2), padding="same"))

        self.model.add(Flatten())
        self.model.add(Dense(100, activation = custom_activation))
        self.model.add(Dense(20, activation = custom_activation))
        #self.model.add(Reshape(np.append(1, self.eye_output_dim*2)))
        #self.model.add(LSTM(self.output_dim, activation = self.activation, stateful = True))
        self.model.add(Dense(self.output_dim, activation = custom_activation))
        
    def mutate(self, freq, intensity):
        mutated_weights = []
        for weight in self.model.get_weights():
            A = np.random.choice([0,1], p=[1-freq, freq], size = np.shape(weight))
            A = A*intensity
            glorot = glorot_uniform().__call__(np.shape(weight))
            if random.random() < self.layer_prob:
                mutated_weights.append(A*glorot)
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