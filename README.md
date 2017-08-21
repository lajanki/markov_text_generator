# markov_text_generator

## About
There are a number of Markov chain based random text generators on GitHub. This one is mainly a personal project. I had already thought about ways to randomly generate text for one of my other projects and writing one seemed like a fun idea to work with a (semi?) supervised learning based algorithm so I decided to give it go. This is largely a fork of the code snippet at https://gist.github.com/agiliq/131679#file-gistfile1-py and also inspired by https://github.com/codebox/markov-text

Markov chains, in the context of this program, are n-grams (ie. sets of n consecutive words) parsed from the text. For example, let's take n=2: given a sample text file as input, the generator first looks for all pairs of consecutive words from it and stores them as a training dataset. To create text, the generator first picks a random pair from the dataset as the initial two words. It then continues by choosing 2-grams whose first word matches the latest word added to the text. This way any 2 consecutive words from the generated text also appear together somewhere in the original input file.

In short, the generator attempts to mimic the source text. The result is usually somewhat syntactically correct (ie. it seems to consist of valid sentences), but is often without meaning. The following was generated from a set of popular poems:
```
Scooped homeless snows ag'in! — 'n rain she peers,
Far from — Curb it meets the sawn-off lock,
that endless space it is taken soon.
```
Generally, the longer the generated text is, the less sense it makes. For Donald Trump's tweets this seems to work well enough:
```
Clinton failed over T.V., much like failed 47% candidate Mitt Romney.
These nasty, angry, jealous failures have ZERO investments in Russia.
```
The sample text needs to be varied enough in order to give the generator more than one option when choosing the next word or the result will be very similar to the source.

## Usage
First train the generator with a sample text. A set of popular fairytales is provided in the data/training/fairytales folder.
```
python text_generator.py --train data/training/fairytales 2
```
This creates a fairytales.cache file in the data/cache folder. The cache file constains the n-grams (in this case n=2) parsed from the input texts.

Then, run
```
python text_generator.py --generate data/cache/fairytales.cache p n
```
which generates text with ```p``` paragraphs of approximately ```n``` words each. Actual length is taken from a Gaussian distribution with mean ```n``` and standard deviation ```n/4``` in order to introduce some variation.

Additionally, when run without a positional argument, ie. ```python text_generator.py``` the program provides a simple UI to run a previously trained generator.

 
## Requirements
The parse_input.py module contains some ad-hoc functions for parsing input files inside a folder as well as from various websites to format suitable for training. It requires [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) and [Twython](https://twython.readthedocs.io/en/latest/usage/install.html) to work.
