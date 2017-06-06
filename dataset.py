#!/usr/bin/python

import sys, getopt
from dateutil import parser
from datetime import timedelta
from dateutil.parser import parse
import git
import csv
import re
import time

def stripWhiteSpace(txt):
    return txt.replace(" ", "")

def stripDoubleSlash(txt):
    return txt.replace("//", "/")

def splitOldNewFilename(filename):
    oldFilename = filename
    newFilename = filename
    p = "{(.*)=>(.*)}"
    p2 = "(.*)=>(.*)"
    m = re.search(p, filename)
    m2 = re.search(p2, filename)
    if m:
        newFilename = stripDoubleSlash(stripWhiteSpace(newFilename.replace(m.group(), m.group(2))))
        oldFilename = stripDoubleSlash(stripWhiteSpace(oldFilename.replace(m.group(), m.group(1))))
    elif m2:
        newFilename = stripDoubleSlash(stripWhiteSpace(newFilename.replace(m2.group(), m2.group(2))))
        oldFilename = stripDoubleSlash(stripWhiteSpace(oldFilename.replace(m2.group(), m2.group(1))))
    return (oldFilename, newFilename)

def getModifiedLines(commit_hash, previous_commit_hash, oldFilename, newFilename, g):
    previous = previous_commit_hash + ":" + oldFilename
    actual = commit_hash + ":" + newFilename
    try:
        diff = g.diff('--unified=0', previous, actual)
    except:
        return []
    modifiedLines = []

    headerDiffs = re.findall("\n@@ (.*) @@", diff.encode('utf8')) # fetch all @@ ... @@ parts

    for h in headerDiffs:
        minus = h.find("-")
        comma = h.find(",")
        space = h[minus:].find(" ") + minus
        if (comma != -1 and comma < space):  # Multiple or zero line(s) to add
            noLine = int(h[minus + 1: comma])
            nbLine = int(h[comma + 1: space])
            modifiedLines += range(noLine, noLine + nbLine)
        else:  # Juste one line
            modifiedLines.append(int(h[minus + 1: h.find("+") - 1]))
    return modifiedLines


def computeChurns(commit_hash, previous_commit_hash, filename, author_name, date, daysDelta, g, deletions):
    if previous_commit_hash == "":
        return 0
    chunkLines = 0
    (oldFilename, newFilename) = splitOldNewFilename(filename)
    modifiedLines = getModifiedLines(commit_hash, previous_commit_hash, oldFilename, newFilename, g)
    if not modifiedLines:
        modifiedLines = range(1, deletions + 1)
    for line in modifiedLines:
        blame = g.blame('-L' + str(line) + ',+1', previous_commit_hash, '--', oldFilename).encode('utf8')
        author_pos = blame.find(author_name)
        if author_pos != -1:  # Same author
            date_pos = author_pos + len(author_name) + 1
            modif_dt = parser.parse(blame[date_pos: date_pos + len(date)])
            dt = parser.parse(date)
            delta = dt - modif_dt
            if delta < timedelta(days=daysDelta):
                chunkLines += 1
    return chunkLines


def main(argv):
    inputfile = ''
    outputfile = 'dataset.csv'
    sinceArg = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:s:", ["ifile=", "ofile=", "since="])
    except getopt.GetoptError:
        print 'usage : -i <inputfile> -o <outputfile> -s <since>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'usage : -i <inputfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-s", "--since"):
            sinceArg = '--since="' + parse(arg).strftime("%Y-%m-%dT%H:%M:%S") + '"'

    g = git.Git(inputfile)
    if sinceArg != '':
        loginfo = g.log('--pretty=format:%h%x09%s%x09%ae%x09%an%x09%ai%x09%p', '--numstat', '--reverse', sinceArg)
    else:
        loginfo = g.log('--pretty=format:%h%x09%s%x09%ae%x09%an%x09%ai%x09%p', '--numstat', '--reverse')


    ofile = open(outputfile, "wb")
    writer = csv.writer(ofile, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(
        ('commit_hash', 'commit_name', 'author_name', 'author_email', 'commit_date', 'filename', 'additions',
         'deletions', 'churns'))

    print "Start computing dataset with churns..."
    start = time.time()
    commit_hash = ""
    for line in loginfo.split('\n'):
        chunks = line.encode('utf8').split('\t')
        if len(chunks[0]) == 7:  # Header commit line
            commit_hash = chunks[0]
            commit_name = chunks[1]
            author_email = chunks[2]
            author_name = chunks[3]
            commit_date = chunks[4]
            parent_commit_hash = chunks[5]
        elif len(chunks) != 1:  # File line
            if (chunks[0] == '-'): continue
            additions = int(chunks[0])
            deletions = int(chunks[1])
            filename = chunks[2]
            churns = 0
            if deletions != 0 \
                    and not(filename.startswith(".")) \
                    and filename.find("/.") == -1:
                churns = computeChurns(commit_hash, parent_commit_hash, filename, author_name, commit_date, 21, g, deletions)
            writer.writerow(
                (commit_hash, commit_name, author_name, author_email, commit_date, filename, additions, deletions,
                 churns))

    end = time.time()
    print "The computation takes : ", end - start,  " s"

    ofile.close()


if __name__ == "__main__":
    main(sys.argv[1:])
