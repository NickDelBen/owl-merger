
############### README ################
# For combining and merging grades to an OWL uploadable zip file
# author:  0xMartian
#
# Instructions for use:
#   1. Each marker should download the folder with attached feedback comments text file
#         Do not include students without submissions!
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
name_extractor = re.compile(r"^\s*(.*?)\((.*?)\)\s*$")
grade_extractor = re.compile(r"^\s*Q(.*?)\s*:\s*([\d\.]*)/([\d\.]*)\s*(.*)$")

# Combines comments from all markers of a student to one item
def combine_comments (student_directory, grade_folders):
	answers = {}
	# Get the grades for this student by each marker
	for grade_folder in grade_folders:
		# Open the comments file for this student by the current marker
		comment_path = os.path.join(grade_folder, student_directory, "comments.txt")
		with open(comment_path, "r") as comments_file:
			for comments_line in comments_file:
				# Parse this comment in the comments file
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
def merge_grades (grade_folders):

	# Using one of the merge target folders as reference start merging all the grades
	students = {}
	for student_name in os.listdir(grade_folders[0]):
		if os.path.isdir(os.path.join(grade_folders[0], student_name)):
			parsed_name = name_extractor.match(student_name).groups()
			students[parsed_name[1]] = {
				"folder": student_name,
				"comments": combine_comments(student_name, grade_folders)
			}

	# Analyze each student and combine their comments and grade
	for student_id in students:
		fin_grade, fin_comment = analyze_comments(students[student_id])
		students[student_id]["final_grade"] = fin_grade
		students[student_id]["final_comment"] = fin_comment

	return students


def create_archive (grade_file, output_path, merged_grades):
	# Create a reandom temporary folder for our marking
	folder_name = ''.join(random.choice('0123456789ABCDEF') for _ in range(32))
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
			new_row[4] = "{0:.1f}".format(100.0 * dat["final_grade"][0] / dat["final_grade"][1])
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
	# First arg is folder with mark list
	mark_file = os.path.abspath(sys.argv[1])
	# Second arg is path to write output zip
	zip_folder_fixed = sys.argv[2][:-4] if sys.argv[2].lower()[-4:] == ".zip" else sys.argv[2]
	# The folders of the different markers for the assignment
	comment_folders = [os.path.abspath(folder_path) for folder_path in sys.argv[3:]]
	# Ensure mark file exists
	if not os.path.isfile(mark_file):
		print("'{0}' is not a valid file".format(sys.argv[1]))
		exit(1)
	# Ensure output file does not exist
	if os.path.exists(os.path.abspath(zip_folder_fixed)):
		print("Specified output path {0} already exists".format(sys.argv[2]))
		exit(1)
	# Ensure the mark fodlers are valid
	for idx, path in enumerate(comment_folders):
		if not os.path.isdir(path):
			print("'{0}' is not a valid directory".format(sys.argv[idx + 3]))
			exit(1)
	# Preform the merge operation
	students = merge_grades(comment_folders)
	# Compile the merged grades to a zip that can be uploaded to OWL
	with open(mark_file, "r") as grades_in:
		zip_path, no_submission = create_archive (grades_in, zip_folder_fixed, students)
		print("Compiled zip archive to be uploaded to OWL saved to:\n    {0}".format(zip_path))
	exit(0)
