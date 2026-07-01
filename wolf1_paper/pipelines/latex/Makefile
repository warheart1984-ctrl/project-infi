all: sections pdf

sections:
	@for f in ../../src/sections/*.md; do \
	  pandoc "$$f" -f markdown -t latex -o "$${f%.md}.tex"; \
	done

pdf: sections
	latexmk -pdf wolf1_v1.1.tex

clean:
	latexmk -C
