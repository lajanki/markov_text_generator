# markov_text_generator

A random text generator based on Markov Chains. Given a sample text as input this script will generate similar text. For instance, the following text was generated from a set of Donald Trump's tweets
```
Clinton failed over T.V., much like failed 47% candidate Mitt Romney.
These nasty, angry, jealous failures have ZERO investments in Russia.
```

Markov chains, in the context of this program, are ngrams parsed from input text. The program looks for sets of n consecutive words (the ngrams) in the input training data and keeps track of their successors. In order to generate text, the script can then lookup an ngram and a random successor and keep looping the process for every n words generated. This leads to output where every n-1 consecutive words appeared somewhere in the input training data. The result is usually somewhat syntactically correct (in that it seems to consist of valid sentences), but is often without meaning. For Donald Trump's tweets this seems to work well enough.


## Usage
First, install dependencies in a virtualenv and activate the new environment
```
python3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Using the program consists of two phases: training and generating.

1. Training requires training data: a plain text file containing the text to mimic. Two sample files, a selection of fairytales and a set of Donald Trump's tweets are provided in `data/training` directory.

To train a genrator run
```
python main.py --train <train-data> <n>
```
where `<train-data>` is a training file in the training directory and `<n>` is the size of the ngram to split the text into. For instance,
```
python main.py --train realDonaldTrump.txt
```
In this case `n` will default to `3`.
This outputs a model `realDonaldTrump.dat` in `data/cache`. The model contains information about the ngrams and their successor (it's really just a json file of all n-1 successive words as keys and a list of successors as values)

2. To generate text using the above model, run
```
python main.py --generate realDonaldTrump.dat 30 3
```
This generates 3 paragraphs of about 30 words each (actual number of words is pulled from a normal distribution).


### Running unit tests
Unit tests can be run with
```
python -m unittest tests/test*.py
```

### Training data parsers
Included are also a set of parsers to fetch input training data from various sources:
 1. folders of plain text files in `data/training`
 2. famous poems from https://allpoetry.com/classics/famous_poems
 3. Steam store game descriptions
 4. Tweets from a user's timeline

To use one of the parsers, run `parse_input.py`. See
```
python parse_input.py -h
```
for help.

Running any of the above parsers will generate an output plain text file in `data/training` which can be used as an input to the trainer. Note that parsing tweets requires valid Twitter API keys and access tokens in `twitter_keys.json`, see https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html.



