#!/usr/bin/python

import re
import random
import sys

tempMapping = {}

mapping = {}

starts = []

def fixCaps(word):
    if word.isupper() and word != "I":
        word = word.lower()
    elif word [0].isupper():
        word = word.lower().capitalize()
    else:
        word = word.lower()
    return word

def toHashKey(lst):
    return tuple(lst)

def wordlist(filename):
    f = open(filename, 'r')
    wordlist = [fixCaps(w) for w in re.findall(r"[\w']+|[.,!?;]", f.read())]
    f.close()
    return wordlist

def addItemToTempMapping(history, word):
    global tempMapping
    while len(history) > 0:
        first = toHashKey(history)
        if first in tempMapping:
            if word in tempMapping[first]:
                tempMapping[first][word] += 1.0
            else:
                tempMapping[first][word] = 1.0
        else:
            tempMapping[first] = {}
            tempMapping[first][word] = 1.0
        history = history[1:]

def buildMapping(wordlist, markovLength):
    global tempMapping
    starts.append(wordlist [0])
    for i in range(1, len(wordlist) - 1):
        if i <= markovLength:
            history = wordlist[: i + 1]
        else:
            history = wordlist[i - markovLength + 1 : i + 1]
        follow = wordlist[i + 1]
        if history[-1] == "." and follow not in ".,!?;":
            starts.append(follow)
        addItemToTempMapping(history, follow)
    for first, followset in tempMapping.iteritems():
        total = sum(followset.values())
        mapping[first] = dict([(k, v / total) for k, v in followset.iteritems()])

def next(prevList):
    sum = 0.0
    retval = ""
    index = random.random()
    while toHashKey(prevList) not in mapping:
        prevList.pop(0)
    for k, v in mapping[toHashKey(prevList)].iteritems():
        sum += v
        if sum >= index and retval == "":
            retval = k
    return retval

def genSentence(markovLength):
    curr = random.choice(starts)
    sent = curr.capitalize()
    prevList = [curr]
    while (curr not in ".!?"):
        curr = next(prevList)
        prevList.append(curr)
        if len(prevList) > markovLength:
            prevList.pop(0)
        if (curr not in ".,!?;"):
            sent += " " # Add spaces between words (but not punctuation)
        sent += curr
    return sent

def generateSentences(wordlist_file,markovLength=5):
    import os

    buildMapping(wordlist(wordlist_file), markovLength)
    sentences = ""
    while len(sentences) < 256:
        x=0
        while x < 1:
            sentences += genSentence(markovLength) + '  '
            x+=1
    return sentences[0:800].strip() if len(sentences) >= 800 else sentences.strip()

