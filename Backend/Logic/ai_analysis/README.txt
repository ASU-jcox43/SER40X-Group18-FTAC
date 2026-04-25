This folder contains the AI Analysis portion of the project.
Analysis_Test is just a simple time test for analysis generation.
Downloaded_Analyses holds downloaded analyses.
It is not included in this repo for privacy, but you would include a text file called FTAC_Prompt.txt with the rubric's contents.
We are only using rubric_analyzer_anthropic, but I decided to leave the OpenAI version from our testing to get an example of what the old rubric looked like for scoring and format.
The following are in the files themselves, but I'll also put them here for clarity and structure.

Rubric Analyzer Anthropic:
# This is the main work AI analysis part of the project using Anthropic Claude.
# The idea is similar to the previous OpenAI test analysis part, but this instead imports in the official prompt,
# which right now is being opened as text. It is read, and then it can be called with download_analysis.
# Give download analysis the document, and then a True or False if it is a file that needs to be read or just text
# that is already ready to be analyzed. Give it some time, then it will create a document in the Downloaded_Analyses
# folder. It uses your Anthropic key as set by your system, so for example, I have my key set in Windows so that it uses
# it without me having to put anything in the public code. For testing purposes, feel free to paste in your code plainly
# but just make sure it never sees the public access.

Rubric Analyzer OpenAI:
# This file is not planned on being used anymore, but I kept it because I wanted to test OpenAI vs Anthropic at one
# point, and it has the old rubric I used before getting the official one.
# It uses the OpenAI API to use the rubric to analyze using each question, then creates a response in a JSON formatted
# string of text.


