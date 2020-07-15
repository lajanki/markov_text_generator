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

1. Training requires training data: a plain text file containing the text to mimic. Two sample files, a selection of fairytales and a set of Donald Trump's tweets are provided in `data/training/` directory.

To train a genrator run
```
python main.py train <train-data> <n>
```
where `<train-data>` is a training file in the training directory `data/training/` and `<n>` is the size of the ngram to split the text into. If not specified, ngram size defaults to `3`. For instance,
```
python main.py train @realDonaldTrump.txt
```
This outputs a model `@realDonaldTrump.dat` in `data/cache/`. The model contains information about the ngrams and their successor (it's really just a json file of all n-1 successive words as keys and a list of successors as values)

2. To generate text using the above model, run
```
python main.py generate @realDonaldTrump.dat 30 3
```
This generates 3 paragraphs of about 30 words each (actual number of words is pulled from a normal distribution).


### Running unit tests
Unit tests can be run with
```
python -m unittest tests/test*.py
```

### Parsers for training data
Included are also a set of parsers to fetch input training data from various sources:
 1. folders of plain text files in `data/training/`
 2. famous poems from https://allpoetry.com/classics/famous_poems
 3. Steam store game descriptions
 4. Twitter timelines, see below for further instructions.

To use one of the parsers, run `parse_input.py`. See
```
python parse_input.py -h
```
for help.

Running any of the above parsers will generate an output plain text file in `data/training/` which can be used as an input to the trainer.

#### Tweet parser
Apart from the the above parsers there's also a Twitter parser for parsing a user's Twitter timeline as training source data. The parsers fetches tweets posted after a the tweet id in `twitter/tweet_metadata.json`. Twitter API has limits on how many tweets can be fetched, so it is recommended to run the parser on a daily basis.

To get started, let's add @kanyewest as a source. First update the metadata file by adding a new handle with an initial, dummy values, of:
```
{
  "@kanyewest": {
    "created_at": "dummy date",
    "id": 1
}
```
Then, fetch tweets with
```
python parse_input.py twitter @kanyewest --fetch
```
This will store new tweets to a daily file in `twitter/@kanyewest/YYYY-MM/` and update `tweet_metadata.json` with the latest tweet fetched. The `id` value can also be set to a valid id as can be seen from the tweet url, but the Twitter API may not correctly fetch all tweets if the id is old enough.

Raw tweets can then be parsed to a single text file suitable for training with
```
python parse_input.py twitter @kanyewest --parse 2020-06 2
```
which parsers 2 latest folders starting from 2020-06. Alternatively, `previous_month` can be used as the month value to start parsing from the previous month as computed from execution date.

Note that parsing tweets requires valid Twitter API keys and access tokens in `twitter/twitter_keys.env`, see https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html.
