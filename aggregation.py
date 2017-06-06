import sys, getopt
import csv

def main(argv):
    inputfile = 'swissnuclearexit_25s.csv'
    outputfile = 'data.csv'
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print 'usage : -i <inputfile> -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'usage : -i <inputfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    input_header_author_name = "author_name"
    input_header_additions = "additions"
    input_header_churns = "churns"
    output_header_author_name = "user"
    output_header_additions = "adds"
    output_header_churns = "churns"
    output_header_churn_rate = "churn_rate"

    contributions = {}

    with open(inputfile) as f:
        reader = csv.DictReader(f)
        for row in reader:
            contributor = row[input_header_author_name]
            additions = int(row[input_header_additions])
            churns = int(row[input_header_churns])
            if contributor in contributions:
                contributions[contributor][output_header_additions] += additions
                contributions[contributor][output_header_churns] += churns
            else:
                contributions[contributor] = {
                    output_header_additions: additions,
                    output_header_churns: churns,
                    output_header_churn_rate: 0
                }

    ofile = open(outputfile, "wb")
    writer = csv.writer(ofile, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow((output_header_author_name, output_header_additions, output_header_churns, output_header_churn_rate))

    for key, value in contributions.items():
        additions = value[output_header_additions]
        churns = value[output_header_churns]
        writer.writerow((key, additions, churns, float(churns) / additions))

    ofile.close()

if __name__ == "__main__":
    main(sys.argv[1:])
