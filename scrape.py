#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility to download the metadata for every paper on the arXiv.

"""

from __future__ import (division, print_function, absolute_import,
                        unicode_literals)

__all__ = ["download"]

import os
import re
import time
import logging
import requests
import xml.etree.cElementTree as ET
from collections import defaultdict
from nltk.tokenize import word_tokenize, sent_tokenize

# Download constants
resume_re = re.compile(r".*<resumptionToken.*?>(.*?)</resumptionToken>.*")
url = "http://export.arxiv.org/oai2"

# Parse constant
record_tag = ".//{http://www.openarchives.org/OAI/2.0/}record"
format_tag = lambda t: ".//{http://arxiv.org/OAI/arXiv/}" + t
date_fmt = "%a, %d %b %Y %H:%M:%S %Z"


def download(start_date=None, max_tries=10):
    params = {"verb": "ListRecords", "metadataPrefix": "arXiv"}
    if start_date is not None:
        params["from"] = start_date

    failures = 0
    while True:
        # Send the request.
        r = requests.post(url, data=params)
        code = r.status_code

        # Asked to retry
        if code == 503:
            to = int(r.headers["retry-after"])
            logging.info("Got 503. Retrying after {0:d} seconds.".format(to))

            time.sleep(to)
            failures += 1
            if failures >= max_tries:
                logging.warn("Failed too many times...")
                break

        elif code == 200:
            failures = 0

            # Write the response to a file.
            content = r.text
            yield parse(content)

            # Look for a resumption token.
            token = resume_re.search(content)
            if token is None:
                break
            token = token.groups()[0]

            # If there isn't one, we're all done.
            if token == "":
                logging.info("All done.")
                break

            logging.info("Resumption token: {0}.".format(token))

            # If there is a resumption token, rebuild the request.
            params = {"verb": "ListRecords", "resumptionToken": token}

            # Pause so as not to get banned.
            to = 20
            logging.info("Sleeping for {0:d} seconds so as not to get banned."
                         .format(to))
            time.sleep(to)

        else:
            # Wha happen'?
            r.raise_for_status()


def parse(xml_data):
    tree = ET.fromstring(xml_data)
    results = []
    for i, r in enumerate(tree.findall(record_tag)):
        arxiv_id = r.find(format_tag("id")).text
        title = r.find(format_tag("title")).text
        abstract = r.find(format_tag("abstract")).text
        categories = r.find(format_tag("categories")).text
        results.append((arxiv_id, title, abstract, categories))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    bp = "dataset"
    try:
        os.makedirs(bp)
    except os.error:
        pass

    file_ids = defaultdict(int)
    counts = defaultdict(int)
    for data in download():
        for arxiv_id, title, abstract, categories in data:
            c = categories.split()[0].split(".")[0]
            path = os.path.join(bp, c.replace("/", "-"))
            try:
                os.makedirs(path)
            except os.error:
                pass
            counts[c] += 1
            if counts[c] % 1000 == 0:
                file_ids[c] += 1
            fid = file_ids[c]
            with open(os.path.join(path, "{0:08}.txt".format(fid)), "a") as f:
                f.write("\t".join([
                    arxiv_id,
                    categories,
                    " ".join(map(" ".join,
                                 map(word_tokenize,
                                     sent_tokenize(title)))),
                    " ".join(map(" ".join,
                                 map(word_tokenize,
                                     sent_tokenize(abstract)))),
                ]) + "\n")
