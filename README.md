# markov_text_generator

## About
There are a number of Markov chain based random text generators on GitHub. This one is mainly a personal project. I had already thought about ways to randomly generate text for one of my other projects and writing one seemed like a fun idea to work with a (semi?) supervised learning based algorithm so I decided to give it go. This is largely a fork of the code snippet at https://gist.github.com/agiliq/131679#file-gistfile1-py and also inspired by https://github.com/codebox/markov-text

Markov chains, in the context of this program, are n-grams (ie. sets of n consecutive words) parsed from the text. For example, let's take n=2: given a sample text file as input, the generator first looks for all pairs of consecutive words from it and stores them as a training dataset. To create text, the generator first picks a random pair from the dataset as a seed and continues by choosing 2-grams whose first words matches the latest word added to the text. This way any 2 consecutive words from the generated text also appear together somewhere in the input file.

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
python text_generator.py data/training/fairytales --train
```
This creates a .cache file, which is an sqlite database of the n-grams parsed from the source texts.

Then, run
```
python text_generator.py data/training/fairytales --generate p n
```
which generates text with ```p``` paragraphs of approximately ```n``` words each.

### Additional Notes
 * The training target can be a folder of .txt files or a single .txt file. You can also pass an optional ```--depth``` argument with a value of 1,2 or 3 to determine how far back the script should look when looking for n-grams, ie. this is a value for n-1.
 * The first argument when generating can be either the folder used to train the generator, as above, or the .cache built during training.
 * When run without a positional argument, ie. ```python text_generator.py``` the program provides a simple UI to run a previously trained generator.
