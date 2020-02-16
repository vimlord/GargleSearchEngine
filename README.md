
# Introduction

This project contains an image search engine I implemented on the side. It allows for search using an image or text. I aimed to design it so it would be easy to modify or replace many of the components. The search component is implemented in Python, and provides a server for making requests against. The front-end is a NodeJS server that takes requests and routes them to the Python server. This could theoretically allow for distributing the search queries.

# Setup

To run this, you will need to have Python 3 and NodeJS available. I have run the code on Arch Linux to verify that it runs. You will also require some libraries:

```
pip install tensorflow tensorflow_datasets numpy scipy sklearn
npm install
```

To run the servers, you will need to need to have two sessions:

```
python search_runner.py
```

```
node web_server.py
```

# Features

The implementation as it stands only permits searching for image data. However, it should be possible to query for text data instead with the proper data. Searches can be done using text or images.

The code will utilize a dataset of flower photos by default. However, this can be adjusted in ```search_runner.py```, which sets up the indexing.

# Licenses

My code is implemented to use a set of example flower images provided by Tensorflow. These images are covered under a variety of licenses, mostly (from the looks of the ```LICENSE.md``` file) Creative Commons. I do not own these images, and any legal responsibilities of users of my code are not mine. Users may change the dataset, but I am not responsible for any legal ramifications of doing so.


