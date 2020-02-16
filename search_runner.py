
from encoder import *
from searcher import *

from tqdm import tqdm

import tensorflow as tf

import numpy as np

import os, sys, shutil

from logger import log

def load_tf_img_data(name, url):
    return tf.keras.utils.get_file(name, url, untar=True)

def get_flower_metadata():
    root = load_tf_img_data('flower_photos', 'https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz')
    log('Loaded image data to', root)

    # We will provide the images in the current directory
    shutil.copytree(root, './images', dirs_exist_ok=True)

    files = []
    fnames = []

    for i, elem in enumerate(os.walk(root)):
        dr, subdr, fs = elem

        if subdr: continue
        
        for f in fs:
            f = os.path.join(dr, f)
            files.append(f)
            fname = '/images' + f[len(root):]
            fnames.append(fname)

    return files, fnames

files, fnames = get_flower_metadata()

log('Found', len(files), 'images')

inc_enc = InceptionEncoder()
log('Built InceptionNet image encoder')

df = {}

# Count occurences
for f in fnames:
    label = f.split('/')[2]
    if label in df:
        df[label] += 1
    else:
        log('Discovered label', label)
        df[label] = 1

# Convert to frequency ratio
for t in df:
    df[t] /= len(fnames)
    print('Frequency of', t, 'is', df[t])

tok_enc = BasicTokenizingEncoder(tokens=list(df.keys()), df=df)
log('Build basic tokenizing text encoder')

def get_img2img_index(enc, files, fnames):
    images = np.array([enc.load_img(f) for f in tqdm(files)])
    log('Loaded images with block shape', images.shape)

    # I found that large batch sizes would completely consume a system's memory
    encoding = enc.encode(images, batch_size=4)
    log('Encoded brick to shape', encoding.shape)

    del images # Images are no longer required

    index = KDTreeSearcher()
    index.add(fnames, encoding)

    log('Built search tree containing', len(index.files), 'files')

    return index

def get_txt2img_index(enc, files, fnames):
    # I found that large batch sizes would completely consume a system's memory
    encoding = enc.encode([f.split('/')[2] for f in fnames])
    log('Generated tokenizations for', len(files), 'files')

    index = SetBasedCosineSimilaritySearcher()
    index.add(fnames, encoding)

    log('Built cosime similarity index containing', len(index.files), 'files')

    return index

import search_server

# Provide the encoder
search_server.set_param('encoders', {
    ('image', 'image') : inc_enc,
    ('text', 'image') : tok_enc,
})

# Provide the searchers
search_server.set_param('searchers', {
    ('image', 'image') : get_img2img_index(inc_enc, files, fnames),
    ('text', 'image') : get_txt2img_index(tok_enc, files, fnames)
})

search_server.run_server()


