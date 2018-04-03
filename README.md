OWL Grading Merger
======
A simple script that allows different graders of the same assignment merge their grades and bulk upload to owl.
***

Preparing
------
**Each grader should bulk download the submissions with comments file from owl.**
 * For each question you grade add a line to that students comments.txt file with the following format:
 * `Q<q#>: x/y comment`
 * An example comments.txt could look like this:
	```
	Q1(a): 17/20 Missing details on the description
	Q1(b): 10/10 
	Q2: 0/5 Not sure what you were doing here
	```
 * Once everyone is finished marking all the different folders should be collected
 * The person collecting should download the `grades.csv` via bulk download for the assignment on OWL

Usage
------
**Using the script is simple just call it pointing to the collected files**

`# python merger.py <mark_csv_file> <output_zip_path> <comment_folders>`
 * Parameters:
	```
	<mark_csv_file>   CSV Grade File download from OWL
	<output_zip_path> Path for generated zip archive to be uploaded to OWL
	<comment_folders> one or more paths of the student grade folders to be merged
	```
 * A couple examples
	```
	python merger.py grades.csv output.zip asn1_nick asn1_andy ../yiwei_a2
	python merger.py ~/Downloads/grades.csv output.zip asn1_nick asn1_saby
	```


Submitting to OWL
------
**This will generate a zip file which should be uploaded to owl via the bulk upload option**
 * Make sure you have the following items selected when you upload to owl
 * Grade file (CSV)
 * Feedback comments
