#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this file. If not, see <http://www.gnu.org/licenses/>.
#
#   Copyright © 2014-2020 The University of Tromsø & the Norwegian Sámi Parliament
#   http://giellatekno.uit.no & http://divvun.no
#
#   ADDENDUM: Magnus Breder Birkenes, National Library of Norway
#   Updated tokenise() with a new flatten function, using itertools chain - much faster

"""An implementation of the ``N-Gram-Based Text Categorization'' algorithm.

Original article:

Cavnar, W. B. and J. M. Trenkle, ``N-Gram-Based Text
Categorization'' In Proceedings of Third Annual Symposium on
Document Analysis and Information Retrieval, Las Vegas, NV, UNLV
Publications/Reprographics, pp. 161-175, 11-13 April 1994.

Original Perl implementation and article available from
http://odur.let.rug.nl/~vannoord/TextCat/
"""

from __future__ import absolute_import, print_function, unicode_literals
from typing import Optional, List

import argparse
import codecs
import glob
import gzip
import os
import re
import sys

import six

from . import util
import itertools

here = os.path.dirname(__file__)


def pretty_tbl(table):
    return ", ".join("{}:{}".format(k, v) for k, v in table)


def ensure_unicode(text):
    """Make sure text is unicode

    Helper for functions that should be able to operate on either utf-8
    encoded bytes or decoded unicode objects
    """
    if type(text) == bytes:
        return text.decode('utf-8')
    else:
        assert (type(text) == six.text_type)
        return text


class NGramModel(object):
    SPLITCHARS = re.compile(
        r"[][}{)(>< \n\t:;!.?_,¶§%&£€$¹°½¼¾©←→▪➢√|#–‒…·•@~\\/”“«»\"0-9=*+‑-]")
    NB_NGRAMS = 400
    MISSING_VALUE = 400

    def __init__(self, arg={}, lang='input'):
        self.lang = lang  # for debugging
        self.unicode_warned = 0

    def of_text(self, text):
        self.finish(self.freq_of_text(ensure_unicode(text), {}))
        return self

    def of_freq(self, freq):
        self.finish(freq)
        return self

    def of_text_file(self, fil):
        self.finish(self.freq_of_text_file(fil))
        return self

    def of_model_file(self, fil, fname):
        raise NotImplementedError(
            "You have to subclass and override of_model_file")

    def freq_of_model_file(self, fil, fname, gram_column, freq_column):
        freq = {}
        for nl, strline in enumerate(fil.readlines()):
            line = strline.strip()
            if line == u"":
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError("%s:%d invalid line, was split to %s" %
                                 (fname, nl + 1, parts))
            try:
                g = parts[gram_column]
                f = int(parts[freq_column])
                freq[g] = f
            except ValueError as e:
                raise ValueError("%s: %d %s" % (fname, nl + 1, e))
        return freq

    def tokenise(self, text):
        """Tokenise the text

        Since we use split() when loading the model file, we also use split()
        on the input text; this includes whitespace (like byte order
        marks) that might not all be in SPLITCHARS
        """
        tokens = (re.split(self.SPLITCHARS, t) for t in text.split())
        return list(itertools.chain.from_iterable(tokens))

    def freq_of_text(self, text, freq):
        """This should update freq and return it."""
        raise NotImplementedError(
            "You have to subclass and override freq_of_text")

    def to_model_file(self, fil, fname):
        raise NotImplementedError(
            "You have to subclass and override to_model_file")

    def freq_of_text_file(self, fil):
        freq = {}
        for nl, strline in enumerate(fil.readlines()):
            try:
                line = strline
            except UnicodeDecodeError as e:
                if self.unicode_warned == 0:
                    util.note("WARNING: Line {} gave {}, skipping ... "
                              "(not warning again)".format(nl, e))
                self.unicode_warned += 1
                continue
            freq = self.freq_of_text(line, freq)
        if self.unicode_warned != 0:
            util.note("Saw {} UnicodeDecodeErrors".format(self.unicode_warned))
        return freq

    def finish(self, freq):
        self.ngrams = {
            gram: rank
            for rank, (gram, freq) in enumerate(
                util.sort_by_value(freq, reverse=True)[:self.NB_NGRAMS])
            if gram != ""
        }
        # Only store the top NB_NGRAMS with frequency:
        self.freq = {gram: freq[gram] for gram in self.ngrams}
        self.ngramskeyset = set(self.ngrams.keys())

    def compare(self, unknown):
        missing_count = len(unknown.ngramskeyset - self.ngramskeyset)
        d_missing = self.MISSING_VALUE * missing_count
        d_found = sum(
            abs(rank - self.ngrams[gram])
            for gram, rank in six.iteritems(unknown.ngrams)
            if gram in self.ngrams)
        # util.print_frame(debug=missing_count)
        # util.print_frame(debug=d_missing)
        # util.print_frame(debug=d_found)

        return d_missing + d_found


class CharModel(NGramModel):

    def of_model_file(self, fil, fname):
        self.finish(
            self.freq_of_model_file(fil, fname, gram_column=0, freq_column=1))
        return self

    def to_model_file(self, fil):
        lines = "".join([
            "%s\t%d\n" % (g, f)
            for g, f in util.sort_by_value(self.freq, reverse=True)
            if g != ''
        ])
        fil.write(lines)

    def freq_of_text(self, text, freq):
        words = self.tokenise(text)
        for word in words:
            _word_ = '_' + word + '_'
            size = len(_word_)
            for i in six.moves.range(size):
                for s in (1, 2, 3, 4):
                    sub = _word_[i:i + s]
                    freq[sub] = freq.get(sub, 0) + 1
                    if i + s >= size:
                        break
        return freq


class WordModel(NGramModel):
    NB_NGRAMS = 30000

    def of_model_file(self, fil, fname):
        self.finish(
            self.freq_of_model_file(fil, fname, gram_column=1, freq_column=0))
        return self

    def to_model_file(self, fil):
        lines = "".join([
            "%d\t%s\n" % (f, g)
            for g, f in util.sort_by_value(self.freq, reverse=True)
            if g != ''
        ])
        fil.write(lines)

    def freq_of_text(self, text, freq):
        words = self.tokenise(text)
        for word in words:
            freq[word] = freq.get(word, 0) + 1
        return freq

    def finish(self, freq):
        super(WordModel, self).finish(freq)
        # See text_cat.pl line 642ff; we invert and normalise the
        # ranking to make it possible to use compare_tc where one wm
        # is shorter than the other, e.g. if there is only a small
        # corpus for one language, or if we manually deleted some
        # words:
        n_words = len(self.ngrams)
        normaliser = float(n_words) / float(self.NB_NGRAMS)
        self.invrank = {
            gram: ((n_words - rank) / normaliser)
            for gram, rank in six.iteritems(self.ngrams)
        }

    def compare_tc(self, unknown_text, normaliser):
        """Implements line 442 of text_cat.pl

        `normaliser` is results[language] from CharModel
        """
        if normaliser <= 0:
            return normaliser
        else:
            unknown_freq = self.freq_of_text(unknown_text, {})
            return (sum(
                self.invrank[word]**2 * unknown_freq[word] * 100 / normaliser
                for word in unknown_freq.keys()
                if word in self.ngrams))


class Classifier(object):
    """Guess which language a text is written in."""

    DROP_RATIO = 1.10

    def __init__(self,
                 folder: Optional[str] = None,
                 langs: List[str] = [],
                 verbose: bool = False):
        if folder is None:
            folder = os.path.join(here, 'lm')
        self.cmodels = {}
        self.wmodels = {}

        ext = '.lm'
        fnames = []

        folder_glob = os.path.join(folder, '*' + ext)
        found_fnames = glob.glob(os.path.normcase(folder_glob))
        if not found_fnames:
            raise ValueError("No language files found in %s" % (folder,))

        if not langs:
            fnames = found_fnames
        else:
            fnames = [os.path.join(folder, lang + ext) for lang in langs]
            not_found = set(fnames) - set(found_fnames)
            if not_found:
                raise ValueError("Unknown language(s): " + ", ".join(not_found))

        for fname in fnames:
            lang = util.basename_noext(fname, ext)
            with codecs.open(fname, 'r', encoding='utf8') as fname_stream:
                self.cmodels[lang] = CharModel(lang).of_model_file(
                    fname_stream, fname)
                if verbose:
                    util.note("Loaded %s" % (fname,))

            fname_wm = os.path.join(folder, lang + '.wm')
            # fname_wmgz = os.path.join(folder, lang+'.wm.gz')
            if os.path.exists(fname_wm):
                with codecs.open(fname_wm, 'r', encoding='utf8') as fname_wm_stream:
                    self.wmodels[lang] = WordModel(lang).of_model_file(
                        fname_wm_stream, fname_wm)
                    if verbose:
                        util.note("Loaded %s" % (fname_wm,))
            else:
                self.wmodels[lang] = WordModel(lang).of_freq({})

        if not self.cmodels:
            raise ValueError("No character models created!")
        else:
            self.langs = set(self.cmodels.keys())
            self.langs_warned = set()

    def get_langs(self, langs=[]):
        """Get the set of wanted languages.

        Args:
            langs (list of str): list of probable languages

        Returns:
            set: The set of languages that should be considered
        """
        if langs == []:
            return self.langs
        else:
            langs = set(langs)
            active_langs = self.langs & langs
            if len(langs) != len(active_langs):
                missing = langs - active_langs - self.langs_warned
                if missing:
                    # only warn once per lang
                    self.langs_warned.update(missing)
                    util.note("WARNING: No language model for {}".format(
                        "/".join(missing)))
            return active_langs

    def classify_full(self, intext, langs=[], verbose=False):
        active_langs = self.get_langs(langs)

        text = ensure_unicode(intext)
        ingram = CharModel().of_text(text)

        cscored = {
            lang: model.compare(ingram)
            for lang, model in six.iteritems(self.cmodels)
            if lang in active_langs
        }
        cranked = util.sort_by_value(cscored)
        cbest = cranked[0]
        cfiltered = {
            lang: score
            for lang, score in cranked
            if score <= cbest[1] * self.DROP_RATIO
        }

        if len(cfiltered) <= 1:
            if verbose:
                util.note("lm gave: {} as only result for input: {}".format(
                    cfiltered, text))
            return list(six.iteritems(cfiltered))
        else:
            # Along with compare_tc, implements text_cat.pl line
            # 442 and on:
            wscored = {
                lang: model.compare_tc(text, cscored[lang])
                for lang, model in six.iteritems(self.wmodels)
                if lang in cfiltered
            }
            cwcombined = {
                lang: (cscored[lang] - wscore)
                for lang, wscore in six.iteritems(wscored)
            }
            cwranked = util.sort_by_value(cwcombined)
            if verbose:
                if cranked[:len(cwranked)] == cwranked:
                    util.note("lm gave: {}\t\twm gave no change\t\tfor"
                              "input: {}".format(pretty_tbl(cranked), text))
                else:
                    util.note("lm gave: {}\t\twm-weighted to: "
                              "{}\t\tfor input: {}".format(
                                  pretty_tbl(cranked), pretty_tbl(cwranked),
                                  text))
            return cwranked

    def classify(self, text, langs=[], verbose=False) -> str:
        return self.classify_full(text, langs, verbose)[0][0]


class FolderTrainer(object):
    """Train the language guesser from a directory."""

    def __init__(self,
                 folder,
                 exts=['.txt', '.txt.gz'],
                 Model=CharModel,
                 verbose=False):
        self.models = {}

        for ext in exts:
            files = glob.glob(os.path.normcase(os.path.join(folder, '*' + ext)))
            for fname in files:
                if verbose:
                    msg = "Processing %s" % (fname,)
                    if os.path.getsize(fname) > 5000000:
                        msg += " (this may take a while)"
                    util.note(msg)
                    sys.stderr.flush()
                lang = util.basename_noext(fname, ext)
                self.models[lang] = Model(lang).of_text_file(
                    self.open_corpus(fname))

        if not self.models:
            raise Exception(
                "No suitable files found matching {}/*.{}{}{}!".format(
                    folder, "{", ",".join(exts), "}"))

    def open_corpus(self, fname):
        if fname.endswith('.gz'):
            return gzip.open(fname, 'rb')
        else:
            return codecs.open(fname, 'r', encoding='utf8')

    def save(self, folder, ext='.lm', verbose=False):
        for lang, model in six.iteritems(self.models):
            fname = os.path.join(folder, lang + ext)
            model.to_model_file(codecs.open(fname, 'w', encoding='utf8'))
        if verbose and self.models:
            util.note("Wrote {%s}%s" % (",".join(list(self.models.keys())),
                                        ext))


class FileTrainer(object):
    """Train the language guesser from a file."""

    def __init__(self, fil, Model=CharModel, verbose=False):
        self.model = Model().of_text_file(fil)

    def save(self, fil, verbose=False):
        self.model.to_model_file(fil)


def proc(args):
    langs = [lang for lang in args.langs.split(",") if lang != ""]
    c = Classifier(folder=args.model_dir, langs=langs)
    if args.u is not None:
        c.DROP_RATIO = args.u
    if args.verbose:
        util.note("Drop ratio: {}".format(c.DROP_RATIO))
    if args.s:
        for line in sys.stdin:
            print(c.classify(ensure_unicode(line), verbose=args.verbose))
    else:
        print(
            c.classify(sys.stdin.read(), verbose=args.verbose))


def file_comp(args):
    if args.mtype == 'lm':
        FileTrainer(
            sys.stdin, Model=CharModel, verbose=args.verbose).save(
                sys.stdout, verbose=args.verbose)
    elif args.mtype == 'wm':
        FileTrainer(
            sys.stdin, Model=WordModel, verbose=args.verbose).save(
                sys.stdout, verbose=args.verbose)
    else:
        raise util.ArgumentError(
            "This shouldn't happen; mtype should be lm or wm")


def folder_comp(args):
    # Check that output dir exists *first* so we don't waste time on
    # training and only then crash :-)
    for d in [args.corp_dir, args.model_dir]:
        if not os.path.isdir(d):
            raise util.ArgumentError("{} is not a directory!".format(d))
    FolderTrainer(
        args.corp_dir, Model=CharModel, verbose=args.verbose).save(
            args.model_dir, ext='.lm', verbose=args.verbose)
    FolderTrainer(
        args.corp_dir, Model=WordModel, verbose=args.verbose).save(
            args.model_dir, ext='.wm', verbose=args.verbose)


def parse_options():
    parser = argparse.ArgumentParser(
        description='Create or use n-gram models for language classification.')

    parser.add_argument(
        '-V',
        '--verbose',
        help="Print some info to stderr",
        action="store_true")

    subparsers = parser.add_subparsers(
        help="(try e.g. 'proc -h' for help with that subcommand)")

    proc_parser = subparsers.add_parser('proc', help='Language classification')
    proc_parser.add_argument(
        'model_dir',
        help="Language model directory. Defaults to the "
        "directory {}.".format(os.path.join(here, 'lm/')),
        nargs='?')
    proc_parser.add_argument(
        '-u',
        help="Drop ratio (defaults to 1.1) -- when the "
        "character model of a language is this much "
        "worse than the best guess, we don't include "
        "it in the word model comparison.",
        type=float)
    proc_parser.add_argument(
        '-s',
        help="Classify on a line-by-line basis "
        "(rather than the whole input as one text).",
        action="store_true")
    proc_parser.add_argument(
        '-l',
        '--langs',
        help="Comma-separated list of languages to "
        "classify between (by default uses all "
        "languages in model_dir).",
        type=str,
        default="")
    proc_parser.set_defaults(func=proc)

    complm_parser = subparsers.add_parser(
        'complm', help='Compile character model from stdin to stdout.')
    complm_parser.set_defaults(func=file_comp)
    complm_parser.set_defaults(mtype='lm')

    compwm_parser = subparsers.add_parser(
        'compwm', help='Compile word model from stdin to stdout.')
    compwm_parser.set_defaults(func=file_comp)
    compwm_parser.set_defaults(mtype='wm')

    compdir_parser = subparsers.add_parser(
        'compdir', help='Compile language from directory.')
    compdir_parser.add_argument(
        'corp_dir', help='Directory to read corpora (*.txt) from.')
    compdir_parser.add_argument(
        'model_dir', help='Directory to write LM and WM files in.')
    compdir_parser.set_defaults(func=folder_comp)

    return parser.parse_args()


def main():
    args = parse_options()
    args.func(args)


if __name__ == "__main__":
    main()
