import json
from os import walk
from os.path import isfile, join
from collections import deque

import sys
import argparse
import logging
import os
import re
import collections
import json
import conll
import util
from preprocess import *

def convert_coref_ua_to_json(UA_PATH, JSON_PATH, MODEL="spanbert_large"):
	if MODEL == "spanbert_large":
		convert_coref_ua_to_json_spanbert_large(UA_PATH, JSON_PATH)
	else:
		raise NotImplementedError

def convert_coref_ua_to_json_spanbert_large(UA_PATH, JSON_PATH):
	
	key_docs, key_doc_sents = get_all_docs(UA_PATH)
	
	with open(JSON_PATH, "w") as output_file:
		for doc in key_doc_sents:
			print(doc)
			document = get_document(doc, key_docs[doc], 'english', 512, tokenizer)
			output_file.write(json.dumps(document))
			output_file.write('\n')
			
def convert_bridg_ua_to_json(UA_PATH, JSON_PATH, MODEL="dali_bridging"):
	if MODEL == "dali_bridging":
		convert_bridg_ua_to_json_dali_bridging(UA_PATH, JSON_PATH)
	else:
		raise NotImplementedError
			
			
def convert_bridg_ua_to_json_dali_bridging(UA_PATH, JSON_PATH):
	
	key_docs, key_doc_sents = get_all_docs(UA_PATH)

	doc_coref_infos = {}
	doc_non_referrig_infos = {}
	doc_bridging_infos = {}

	keep_singletons = True

	keep_non_referring = True

	keep_split_antecedent = True

	for doc in key_docs:
		key_clusters, key_bridging_pairs = get_doc_markables(doc, key_docs[doc], True, True)

		(key_clusters, key_non_referrings, key_removed_non_referring,
			key_removed_singletons) = process_clusters(
			key_clusters, keep_singletons, keep_non_referring,keep_split_antecedent)

		key_mention_key_cluster = get_markable_assignments(key_clusters)

		doc_coref_infos[doc] = (key_clusters + [[i] for i in key_non_referrings], [])
		doc_non_referrig_infos[doc] = key_non_referrings

		doc_bridging_infos[doc] = (key_bridging_pairs, [])


	bridging_jsons = []

	for doc in doc_bridging_infos.keys():
		bridging_pairs = []
		coref_clusters = []
		mens = []
		for k, v in doc_bridging_infos[doc][0].items():
			bridging_pairs.append([[k.start, k.end], [v.start, v.end]])

		for clus in doc_coref_infos[doc][0]:
			cluster = []
			for men in clus:
				mens.append([men.start, men.end])
				if men.start > -1 and men.end > -1:
					cluster.append([men.start, men.end])
			coref_clusters.append(cluster)

		bridging_jsons.append({
			"clusters": coref_clusters,
			"bridging_pairs": bridging_pairs,
			"doc_key": doc,
			"sentences": key_doc_sents[doc]
		})

	with open(JSON_PATH, "w") as output_file:
		for doc in bridging_jsons:
			output_file.write(json.dumps(doc))
			output_file.write('\n')
			
			
def convert_coref_json_to_ua(JSON_PATH, UA_PATH):	
	data = []
	ua_all_lines = []

	with open(JSON_PATH, "r") as f:
		for r in f.readlines():
			json_doc = json.loads(r.strip())
			ua_all_lines += convert_coref_json_to_ua_doc(json_doc) + ["\n"]

		with open(UA_PATH, "w") as f:
			for line in ua_all_lines:
				f.write(line + "\n")


# newdoc id = Trains_91/dia5-2
# sent_id = dia5-2-1
# text = M : okay

# (EntityID=1|MarkableID=markable_727|Min=1|SemType=dn)

def convert_coref_json_to_ua_doc(json_doc):
	# TODO: Include metadata
	# TODO: Include sentence breaks 


	pred_clusters = [tuple(tuple(m) for m in cluster) for cluster in json_doc['predicted_clusters']]
	men_to_pred = {m: clus for c, clus in enumerate(pred_clusters) for m in clus}

	lines = []
	lines.append("# global.columns = ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC IDENTITY BRIDGING DISCOURSE_DEIXIS REFERENCE NOM_SEM")
	lines.append("# newdoc id = " + json_doc['doc_key'])
#     lines.append("turn_id = " + json_doc['doc_key'].split()[1] + "-t1")
#     lines.append("speaker = -")
#     lines.append("sent_id = " + json_doc['doc_key'].split()[1] + "-1")
	markable_id = 1
	entity_id = 1

	coref_strs = [""]*len(json_doc['tokens'])

	for clus in pred_clusters:
		for (start,end) in clus:
			start = json_doc['subtoken_map'][start]
			end = json_doc['subtoken_map'][end]

			coref_strs[start] += "(EntityID={}|MarkableID=markable_{}".format(entity_id, markable_id)
			markable_id += 1
			if start == end:
				coref_strs[end] += ")"
			else:
				coref_strs[end] = ")" + coref_strs[end]

		entity_id += 1


	for _id, token in enumerate(json_doc['tokens']):                      
		if coref_strs[_id] == "":
			coref_strs[_id] = "_"
		sentence = "{}  {}  _  _  _  _  _  _  _  _  {}  _  _  _".format(_id, token, coref_strs[_id])
		lines.append(sentence)

	return lines

def convert_bridg_json_to_ua(JSON_PATH, UA_PATH):	
	data = []
	ua_all_lines = []

	with open(JSON_PATH, "r") as f:
		for r in f.readlines():
			json_doc = json.loads(r.strip())
			ua_all_lines += convert_bridg_json_to_ua_doc(json_doc) + ["\n"]

		with open(UA_PATH, "w") as f:
			for line in ua_all_lines:
				f.write(line + "\n")

# (MarkableID=markable_42|MentionAnchor=markable_393)

def convert_bridg_json_to_ua_doc(json_doc):
	# TODO: Include metadata
	# TODO: Include sentence breaks 

	json_doc['tokens'] = [word for sent in json_doc['sentences'] for word in sent]

	print(json_doc['doc_key'])


	pred_clusters = [tuple(tuple(m) for m in cluster) for cluster in json_doc['clusters']]
	men_to_pred = {m: clus for c, clus in enumerate(pred_clusters) for m in clus}

	lines = []
	lines.append("# global.columns = ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC IDENTITY BRIDGING DISCOURSE_DEIXIS REFERENCE NOM_SEM")
	lines.append("# newdoc id = " + json_doc['doc_key'])
#     lines.append("turn_id = " + json_doc['doc_key'].split()[1] + "-t1")
#     lines.append("speaker = -")
#     lines.append("sent_id = " + json_doc['doc_key'].split()[1] + "-1")
	markable_id = 1
	entity_id = 1
	a = 1

	men_mark_map = {}

	bridg_strs = [""]*len(json_doc['tokens'])
	coref_strs = [""]*len(json_doc['tokens'])

	for clus in pred_clusters:
		for (start,end) in clus:
			if True: #start < len(json_doc['tokens']) and end < len(json_doc['tokens']):
				coref_strs[start] += "(EntityID={}|MarkableID=markable_{}".format(entity_id, markable_id)
				men_mark_map[(start, end)] = markable_id
				if start == end:
					coref_strs[end] += ")"
				else:
					coref_strs[end] = ")" + coref_strs[end]

			markable_id += 1

		entity_id += 1

	for pairs in json_doc['bridging_pairs']:
		bridg_strs[pairs[0][0]] += "(MarkableID=markable_{}|MentionAnchor=markable_{}".format(men_mark_map[(pairs[0][0], pairs[0][1])], men_mark_map[(pairs[1][0], pairs[1][1])])

		if pairs[0][0] == pairs[0][1]:
			bridg_strs[pairs[0][1]] += ")"
		else:
			bridg_strs[pairs[0][1]] = ")" + bridg_strs[pairs[0][1]]

	for _id, token in enumerate(json_doc['tokens']):                      
		if bridg_strs[_id] == "":
			bridg_strs[_id] = "_"
		sentence = "{}  {}  _  _  _  _  _  _  _  _  {}  {}  _  _".format(_id, token, coref_strs[_id], bridg_strs[_id])
		lines.append(sentence)

	return lines


def discourse_deixis_rule_baseline(key_docs, key_doc_sents, output_path):

	with open(output_path, "w") as f:
		for doc in key_docs:
			markable_id = 1
			ant_markable_id = 10000
			entity_id = 1

			lines = []

			doc_words = [w.split()[1] for w in key_docs[doc]]

			word_to_sent_map = {}
			sent_to_end_word_map = {}

			total_word_id = 0

			for s, sent in enumerate(key_doc_sents[doc]):
				for w, word in enumerate(sent):
					word_to_sent_map[total_word_id] = s
					sent_to_end_word_map[s] = total_word_id           
					total_word_id += 1


			for i, w in enumerate(doc_words):
				line = key_docs[doc][i].split()

				for l, col in enumerate(line):
					try:
						assert len(line) == 15
					except:
						line.append("_")
					if l > 1:
						line[l] = "_"

				# Baseline Start
				if w in ["this", "that"]:

					cur_word_id = len(lines)

					cur_sent_id = word_to_sent_map[cur_word_id]

					if cur_sent_id - 1 >= 0:
						prev_sent_end = sent_to_end_word_map[cur_sent_id - 1]
					else:
						continue

					if cur_sent_id - 2 >= 0:
						prev_sent_start = sent_to_end_word_map[cur_sent_id - 2] + 1
					else:
						continue

					line[-3] = "(EntityID={}-DD|MarkableID=markable_{})".format(entity_id, markable_id)

					lines.append(line)

					if lines[prev_sent_start][12] == "_":
						lines[prev_sent_start][12] = "(EntityID={}-DD|MarkableID=dd_markable_{}".format(entity_id, ant_markable_id)
					elif lines[prev_sent_start][12][-1] == ")":
						lines[prev_sent_start][12] += "(EntityID={}-DD|MarkableID=dd_markable_{}".format(entity_id, ant_markable_id)
					else:
						lines[prev_sent_start][12] = "(EntityID={}-DD|MarkableID=dd_markable_{}".format(entity_id, ant_markable_id) + lines[prev_sent_start][12]

					if prev_sent_start == prev_sent_end:
						if lines[prev_sent_end][12] == "_":
							lines[prev_sent_end][12] = ")"
						else:
							lines[prev_sent_end][12] += ")"
					else:
						if lines[prev_sent_end][12] == "_":
							lines[prev_sent_end][12] = ")"
						else:
							lines[prev_sent_end][12] = ")" + lines[prev_sent_end][12]

					markable_id += 1
					entity_id += 1
					ant_markable_id += 1
				else:
					lines.append(line)


			f.write("# global.columns = ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC IDENTITY BRIDGING DISCOURSE_DEIXIS REFERENCE NOM_SEM\n")
			f.write("# newdoc id = " + doc + "\n")
			for s in lines:
				f.write(" ".join(s) + "\n")
				
def discourse_deixis_baseline(IN_PATH, PRED_PATH):
				
	key_docs, key_doc_sents = get_all_docs(IN_PATH)

	doc_coref_infos = {}
	doc_non_referrig_infos = {}
	doc_bridging_infos = {}

	keep_singletons = True

	keep_non_referring = True

	keep_split_antecedent = True

	for doc in key_docs:
	    print(doc)
		key_clusters, key_bridging_pairs = get_doc_markables(doc, key_docs[doc], True, keep_bridging = False, markable_column=12)

		(key_clusters, key_non_referrings, key_removed_non_referring,
			key_removed_singletons) = process_clusters(
			key_clusters, keep_singletons, keep_non_referring,keep_split_antecedent)

		key_mention_key_cluster = get_markable_assignments(key_clusters)

		doc_coref_infos[doc] = (key_clusters, [])
		doc_non_referrig_infos[doc] = key_non_referrings

	discourse_deixis_rule_baseline(key_docs, key_doc_sents, PRED_PATH)