A little script that scrapes the metadata from [the arXiv](http://arxiv.org)
and saves it in a form that is useful for statistical analysis.

Usage
-----

You'll need to install [NLTK](http://nltk.org) first and then run

```
python scrape.py
```

This will take many hours to run and it will save files of the form
`data/astro-ph/2007-05-10.txt.gz` with one abstract per line. Each row has the
tab-separated columns: arxiv id, space-separated categories, tokenized title,
and tokenized abstract.

Credits
-------

Copyright 2013 Dan Foreman-Mackey

Licensed under the terms of the MIT License (see `LICENSE`).
