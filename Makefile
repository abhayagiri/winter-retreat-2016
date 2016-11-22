audio:
	venv/bin/python process.py

markdown:
	venv/bin/python generate-markdown.py

clean:
	find . -name '.DS_Store' -exec rm {} \;
