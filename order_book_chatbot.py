# -*- coding: utf-8 -*-
#from textblob import TextBlob
#from attributegetter import *
#from generatengrams import ngrammatch
#from Contexts import *
import json
#from Intents import *
import random
import os
import re

!unzip Chatbot_V3.zip

class Context(object):

	def __init__(self,name):
		self.lifespan = 2
		self.name = name
		self.active = False

	def activate_context(self):
		self.active = True

	def deactivate_context(self):
		self.active = False

		def decrease_lifespan(self):
			self.lifespan -= 1
			if self.lifespan==0:
				self.deactivate_context()

class FirstGreeting(Context):

	def __init__(self):
		self.lifespan = 1
		self.name = 'FirstGreeting'
		self.active = True

class GetRegNo(Context):

	def __init__(self):
		print('Hi')
		self.lifespan = 1
		self.name = 'GetRegNo'
		self.active = True

class IntentComplete(Context):

	def __init__(self):
		self.lifespan = 1
		self.name = 'IntentComplete'
		self.active = True

class SpellConformation(Context):

	def __init__(self,index,CorrectWord,user_input,context):
		self.lifespan = 1
		self.name = 'SpellConformation'
		self.active = True
		self.index = index
		self.correct = CorrectWord
		self.tobecorrected = user_input
		self.contexttobestored = context

import os

limit = 3

def ngrams(lines):
    global limit
    ngrams = []
    for i in range(1, limit+1):
        ndict = {}
        for line in lines:
            nline = ['<START>']*i + line + ['<END>']*i
            for x in range(len(nline)- i) :
                key = '_'.join(nline[x:x+i])
                if key in ndict.keys():
                    ndict[key] += 1
                else:
                    ndict[key] = 1
        ngrams += [ndict]
    return ngrams

def cleanLines(lines):
    for i in range(len(lines)):
        lines[i] = lines[i][:-1].split()
        for x in range(len(lines[i])):
            lines[i][x] = lines[i][x].lower()
    return lines

def score(uinput, tngramsdict):
    global limit
    scores = []
    uinput = [uinput.lower().split()]
    cur_ngramsdict = ngrams(uinput)
    for key in tngramsdict:
        ngramsdict = tngramsdict[key]
        fscore = 0.0
        for i in range(len(cur_ngramsdict)):
            cur_dict = cur_ngramsdict[i]
            ansdict = ngramsdict[i]

            precision = 0
            for i in cur_dict.keys():
                if i in ansdict.keys():
                    precision+=1

            recall = 0
            for i in ansdict.keys():
                if i in cur_dict.keys():
                    recall+=1

            fscore += 1.0/float((len(ansdict.keys())/float(precision) + len(ansdict.keys())/float(recall)))
        scores+= [(key,fscore)]
    return scores

def init():
    ngramsdict = {}
    path = './intents/'
   

    for fil in os.listdir(path):
        if fil.endswith('.dat'):
            with open(path + fil) as f:
                lines = f.readlines()
                lines = cleanLines(lines)
                ngramsdict[''.join(fil.split('.')[:-1])] = ngrams(lines)
    return ngramsdict

def ngrammatch(uinput):
    ngramsdict = init()
    scores = score(uinput, ngramsdict)
    #print scores
    return scores

from abc import ABCMeta, abstractmethod
class Intent(object):


	def __init__(self, name, params, action):
		self.name = name
		self.action = action
		self.params = []
		for param in params:
			# print param['required']
			self.params += [Parameter(param)]

class Parameter():
	def __init__(self, info):
		self.name = info['name']
		self.placeholder = info['placeholder']
		self.prompts = info['prompts']
		self.required = info['required']
		self.context = info['context']

def check_actions(current_intent, attributes, context):
    '''This function performs the action for the intent
    as mentioned in the intent config file'''
    '''Performs actions pertaining to current intent
    for action in current_intent.actions:
        if action.contexts_satisfied(active_contexts):
            return perform_action()
    '''

    context = IntentComplete()
    return 'action: ' + current_intent.action, context

def check_required_params(current_intent, attributes, context):
    '''Collects attributes pertaining to the current intent'''
    
    for para in current_intent.params:
        if para.required:
            if para.name not in attributes:
                #Example of where the context is born, implemented in Contexts.py
                if para.name=='RegNo':
                    context = GetRegNo()
                #returning a random prompt from available choices.
                return random.choice(para.prompts), context

    return None, context


def input_processor(user_input, context, attributes, intent):
    '''Spellcheck and entity extraction functions go here'''
    
    #uinput = TextBlob(user_input).correct().string
    
    #update the attributes, abstract over the entities in user input
    attributes, cleaned_input = getattributes(user_input, context, attributes)
    
    return attributes, cleaned_input

def loadIntent(path, intent):
    with open(path) as fil:
        dat = json.load(fil)
        intent = dat[intent]
        return Intent(intent['intentname'],intent['Parameters'], intent['actions'])

def intentIdentifier(clean_input, context,current_intent):
    clean_input = clean_input.lower()
    
    #Scoring Algorithm, can be changed.
    scores = ngrammatch(clean_input)
    
    #choosing here the intent with the highest score
    scores = sorted_by_second = sorted(scores, key=lambda tup: tup[1])
    # print clean_input
    #print 'scores', scores
    

     if(current_intent==None):
        if(clean_input=='search'):
            return loadIntent('params/newparams.cfg','TheatreSearch')
        if(clean_input=='movie'):
            return loadIntent('params/newparams.cfg','movieBook')
        else:
            return loadIntent('params/newparams.cfg',scores[-1][0])
    else:
        #If current intent is not none, stick with the ongoing intent
        return current_intent

def getattributes(uinput,context,attributes):
    '''This function marks the entities in user input, and updates
    the attributes dictionary'''
    #Can use context to context specific attribute fetching
    if context.name.startswith('IntentComplete'):
        return attributes, uinput
    else:
        #Code can be optimised here, loading the same files each time suboptimal 
        files = os.listdir('./entities/')
        entities = {}
        for fil in files:
            if fil == ".ipynb_checkpoints":
                continue
            lines = open('./entities/'+fil).readlines()
            for i, line in enumerate(lines):
                lines[i] = line[:-1]
            entities[fil[:-4]] = '|'.join(lines)

        #Extract entity and update it in attributes dict
        for entity in entities:
            for i in entities[entity].split('|'):
                if i.lower() in uinput.lower():
                    attributes[entity] = i
        for entity in entities:
                uinput = re.sub(entities[entity],r'$'+entity,uinput,flags=re.IGNORECASE)

        #Example of where the context is being used to do conditional branching.
        if context.name=='GetRegNo' and context.active:
            print(attributes)
            match = re.search('[0-9]+', uinput)
            if match:
                uinput = re.sub('[0-9]+', '$regno', uinput)
                attributes['RegNo'] = match.group()
                context.active = False

        return attributes, uinput

class Session:
    def __init__(self, attributes=None, active_contexts=[FirstGreeting(), IntentComplete() ]):
        
        '''Initialise a default session'''
        
        #Active contexts not used yet, can use it to have multiple contexts
        self.active_contexts = active_contexts
        
        #Contexts are flags which control dialogue flow, see Contexts.py        
        self.context = FirstGreeting()
        
        #Intent tracks the current state of dialogue
        #self.current_intent = First_Greeting()
        self.current_intent = None
        
        #attributes hold the information collected over the conversation
        self.attributes = {}
        
    def update_contexts(self):
        '''Not used yet, but is intended to maintain active contexts'''
        for context in self.active_contexts:
            if context.active:
                context.decrease_lifespan()

    def reply(self, user_input):
        '''Generate response to user input'''
        
        self.attributes, clean_input = input_processor(user_input, self.context, self.attributes, self.current_intent)
        
        self.current_intent = intentIdentifier(clean_input, self.context, self.current_intent)
        
        prompt, self.context = check_required_params(self.current_intent, self.attributes, self.context)

        #prompt being None means all parameters satisfied, perform the intent action
        if prompt is None:
            if self.context.name!='IntentComplete':
                prompt, self.context = check_actions(self.current_intent, self.attributes, self.context)
        
        #Resets the state after the Intent is complete
        if self.context.name=='IntentComplete':
            self.attributes = {}
            self.context = FirstGreeting()
            self.current_intent = None
        
        return prompt

session = Session()

print ('BOT: Hi! How may I assist you?')

while True:
    
    inp = input('User: ')
    print ('BOT:', session.reply(inp))
