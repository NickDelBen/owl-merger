
############### README ################
# For combining and merging grades to an OWL uploadable zip file
# author:  0xMartian
#
# Instructions for use:
#   1. Each marker should download the folder with attached feedback comments text file
#   2. For each question marked a line in comments.txt file in the students folder should be created:
#         Q1(a): 17/20 Missing details on the description
#         Q1(b): 10/10 
#         Q2: 0/5 Not sure what you were doing here
#      The format is obvious from the above examples I hope
#   3. The generated archive should be uplaoded to OWL with the following options selected
#         - Grade file (AND CSV)
#         - Feedback comments
#   This will upload the merged comments and grades to OWL
#
# Parameters
#     <mark_csv_file>   CSV Grade File download from OWL
#     <output_zip_path> Path for generated zip archive to be uploaded to OWL
#     <comment_folders> one or more paths of the student grade folders to be merged
#######################################

import os
import csv
import random
import shutil
import re

assignment_title_extractor = re.compile(r"^\s*\"(.*?)\".*$")
name_extractor = re.compile(r"^\s*(.*)\((.*?)\)\s*$")
grade_extractor = re.compile(r"^\s*Q(.*?)\s*:\s*([\d\.]*)/([\d\.]*)\s*(.*)$")

# Extract the comments from a specific comments file
def extract_comments (dir_path):
	answers = {}
	# Build full path to the comments file
	comment_path = os.path.join(dir_path, "comments.txt")
	with open(comment_path, "r") as comments_file:
		for comments_line in comments_file:
			# Parse the comments line
			parsed_comment = grade_extractor.match(comments_line.strip()).groups()
			answers[parsed_comment[0]] = {
				"grade": [float(parsed_comment[1]), float(parsed_comment[2])],
				"comment": parsed_comment[3]
			}
	return answers


# Analyzes a students comments to create a final comment and calculate assignment grade
def analyze_comments (student):
	final_comment = ""
	final_grade = [0.0, 0.0]
	for question_key in sorted([qk for qk in student["comments"]]):
		q = student["comments"][question_key]
		final_grade[0] += q["grade"][0]
		final_grade[1] += q["grade"][1]
		final_comment += "Q{0}: {1}/{2} {3}\n".format(question_key, q["grade"][0], q["grade"][1], q["comment"])
	return final_grade, final_comment


# Merges all grades for all students
def merge_grades (grade_file, grade_folders):

	# Using the grade csv as reference create an empty set for all the students
	grade_file_start = grade_file.tell()
	# Skip the headers of the csv file
	for _ in xrange(3):
		grade_file.readline()
	students = {}
	for row in csv.reader(grade_file, delimiter=',', quotechar='"'):
		students[row[0]] = {
			"folder": "",
			"comments": {}
		}
	# Seek to start of grades csv
	grade_file.seek(grade_file_start)

	# For each marker that needs their grades combined
	for grade_folder in grade_folders:
		# Iterate over all of the students that were marked by this marker
		for student_folder in os.listdir(grade_folder):
			# Check if this student had content marked
			full_path = os.path.join(grade_folder, student_folder)
			if os.path.isdir(full_path):
				parsed_name = name_extractor.match(student_folder).groups()
				# Ensure the student was found in the grades folder
				if parsed_name[1] not in students:
					continue
				# Store the path to this students folder
				students[parsed_name[1]]["folder"] = student_folder
				for key, val in extract_comments(full_path).iteritems():
					students[parsed_name[1]]["comments"][key] = val

	# Analyze each student and combine their comments and grade
	for student_id in students:
		fin_grade, fin_comment = analyze_comments(students[student_id])
		students[student_id]["final_grade"] = fin_grade
		students[student_id]["final_comment"] = fin_comment

	return students


def create_archive (grade_file, output_path, merged_grades, normalize=False):
	# Create a reandom temporary folder for our marking
	while True:
		folder_name = ''.join(random.choice('0123456789ABCDEF') for _ in xrange(32))
		# Ensure our folder does not already exist
		if not os.path.isdir(folder_name):
			break
	
	folder_path = os.path.abspath(folder_name)
	os.makedirs(folder_path)

	# Read the assignment title from the file
	grade_file_start = grade_file.tell()
	assignment_title = assignment_title_extractor.match(grade_file.readline()).groups()[0]
	assignment_folder = os.path.abspath(os.path.join(folder_path, assignment_title))
	grade_file.seek(grade_file_start)

	# Create the assignment output folder
	os.makedirs(assignment_folder)

	# Open the output folder for the grades
	with open(os.path.abspath(os.path.join(assignment_folder, "grades.csv")), "w") as grades_out_csv:
		# Copy the header lines for the grades file
		for _ in xrange(3):
			grades_out_csv.write(grade_file.readline())

		# Create csv reader and writer
		csvreader = csv.reader(grade_file, delimiter=',', quotechar='"')
		csvwriter = csv.writer(grades_out_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

		unsubmitted = []
		# Iterate over all students in class
		for row in csvreader:
			# Keep track of students that did not submit
			if not row[0] in merged_grades:
				unsubmitted.append(row[0])
				continue
			# Copy student info over from grades csv but input the new grade
			dat = merged_grades[row[0]]
			new_row = row
			if normalize:
				new_row[4] = "{0:.1f}".format(100.0 * dat["final_grade"][0] / dat["final_grade"][1])
			else:
				new_row[4] = "{0:.1f}".format(dat["final_grade"][0])
			csvwriter.writerow(new_row)
			# Create the comments file and containing folder for this student
			student_folder_path = os.path.abspath(os.path.join(assignment_folder, dat["folder"]))
			os.makedirs(student_folder_path)
			comments_file_path = os.path.abspath(os.path.join(student_folder_path, "comments.txt"))
			with open(comments_file_path, "w") as student_comment_file:
				student_comment_file.write(dat["final_comment"])


	# Zip the folder into an uploadable form
	result_path = shutil.make_archive(output_path, "zip", folder_path, assignment_title)
	# Delete temporary folder
	shutil.rmtree(folder_path, ignore_errors=True)

	return result_path, unsubmitted


# If script executed get params from command line
if __name__ == "__main__":
	import sys

	# Ensure proper args
	if len(sys.argv) < 4:
		print("Inproper usage.\n    merger.py <mark_csv_file> <output_zip_path> <comment_folders>")
		print("Example:\n    merger.py grades.csv to_upload.zip asn1_nick asn1_saby")
		exit(1)
	# Second arg is path to write output zip (we remove zip portion for uniform behaviour)
	zip_folder_fixed = sys.argv[2][:-4] if sys.argv[2][-4:].lower() == ".zip" else sys.argv[2]
	# Ensure mark file exists
	if not os.path.isfile(sys.argv[1]):
		print("'{0}' is not a valid file".format(sys.argv[1]))
		exit(1)
	# Ensure output file does not exist
	if os.path.exists("{0}.zip".format(zip_folder_fixed)):
		print("Specified output path {0}.zip already exists".format(zip_folder_fixed))
		exit(1)
	# Ensure the mark folders are valid
	for comment_folder in sys.argv[3:]:
		if not os.path.isdir(comment_folder):
			print("'{0}' is not a valid directory".format(comment_folder))
			exit(1)
	with open(os.path.abspath(sys.argv[1]), "r") as grades_in:
		# Preform the merge operation
		students = merge_grades(grades_in, [os.path.abspath(comment_folder) for comment_folder in sys.argv[3:]])
		# Compile the merged grades to a zip that can be uploaded to OWL
		zip_path, no_submission = create_archive (grades_in, zip_folder_fixed, students)
		print("Compiled zip archive to be uploaded to OWL saved to:\n    {0}".format(zip_path))
	exit(0)
