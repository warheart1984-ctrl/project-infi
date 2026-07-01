all: pdf

pdf:
	node ../../src/build_master.js
	pandoc ../../src/wolf1_v1.1.md \
	  --from markdown \
	  --to pdf \
	  --template=template.latex \
	  --metadata-file=metadata.yaml \
	  -o wolf1_v1.1.pdf

clean:
	rm -f wolf1_v1.1.pdf
