all: dist/index.html

dist/index.html: generate-html.py index.html.tmpl audio.yaml
	venv/bin/python generate-html.py

audio:
	venv/bin/python process.py

clean:
	find . -name '.DS_Store' -exec rm {} \;

images:
	for src in wr/Images/*.JPG; do \
		dest=`basename "$$src"`; \
		convert $$src -auto-orient -resize 1280 -strip dist/img/$$dest; \
	done

deploy:
  #  ', '--delete',
  # --dry-run
	rsync --itemize-changes --exclude=.DS_Store \
    -avz --rsh=ssh \
    dist/ \
    'abhayagiri@server.abhayagiri.org:www.abhayagiri.org/shared/public/media/discs/winter-retreat-2016/'
