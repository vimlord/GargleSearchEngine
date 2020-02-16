
import tensorflow as tf
import numpy as np

import math, random

import os

from tensorflow.keras.preprocessing.image import load_img, img_to_array, save_img as save_image

class Encoder:
    def __call__(self, x, **args):
        return self.encode(x, **args)

    def preprocess(self, x, **args):
        # Default: do nothing
        return x

    def postprocess(self, y, **args):
        return y

    def encode(self, x, batch_size=None, **args):
        raise NotImplemented

class BasicTokenizingEncoder(Encoder):
    def __init__(self, tokens=[], df=None):
        self.tokens = tokens
        
        # Every token must occur in at least one document
        assert all(df[t] > 0 and df[t] <= 1 for t in tokens)
        
        if df is None:
            # Assume all tokens independently appear in 1/T of the documents.
            self.idf = {t : math.log(len(tokens)) for t in tokens}
        else:
            self.idf = {t : math.log(1. / df[t]) for t in tokens}

    def encode(self, x, **args):
        if isinstance(x, list):
            return [self.encode(v, **args) for v in x]

        # Split into tokens
        toks = x.lower().split()
        
        # Compute term frequency
        tf = [toks.count(t) for t in self.tokens]

        # Compute tf-idf of each token
        tfidf = [tf[i] * self.idf[t] for i, t in enumerate(self.tokens)]

        return np.array(tfidf)

class DeepEncoder(Encoder):
    def __init__(self, net=None):
        # Instantiate the network
        if net is None:
            net = self.create_encoder()
        self.net = net

    def create_encoder():
        raise Exception("Encoder network must be provided when a default builder is not present")

    def __call__(self, x, **args):
        return self.encode(x, **args)

    def preprocess(self, x, **args):
        # Default: do nothing
        return x

    def postprocess(self, y, **args):
        return y

    def encode(self, x, batch_size=None, **args):
        # Preprocess the input
        x = self.preprocess(x, **args)
        # Generate output
        y = self.net.predict(x, batch_size=batch_size)
        # Postprocess the output
        return self.postprocess(y, **args)

class InceptionEncoder(DeepEncoder):
    def create_encoder(self):
        return tf.keras.applications.InceptionV3(include_top=False, weights='imagenet')

    def load_img(self, fname, tgt_size=(224, 224)):
        # Load the file
        x = tf.keras.preprocessing.image.load_img(fname, target_size=tgt_size)
        return np.array(x, dtype='float32')

    def postprocess(self, x):
        return np.mean(np.mean(x, axis=-2), axis=-2)
    
    def preprocess(self, x, tgt_size=(224, 224), scale=127.5, shift=1.):
        if isinstance(x, str):
            x = self.load_img(x)

        if len(x.shape) == 3:
            x = np.expand_dims(x, axis=0)

        if tgt_size is not None and x[-3:-1] != tgt_size:
            x = tf.image.resize(x, tgt_size)

        # Preprocess the image
        return (x / scale) - shift

