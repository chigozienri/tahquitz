SINGLE = 28
# page number for "make single"

default:
	# There are not separate versions of the pdf for print and online. Neither version includes a cover as part of the pdf.
	make figures # renders any figure whose pdf is older than its svg
	./fruby tahquitz.rbtex >tahquitz.tex
	pdflatex tahquitz
	pdflatex tahquitz
	pdflatex tahquitz
	cp tahquitz.pdf ~/Lightandmatter/tahquitz
	make clean
	rm -f topo.jpg
	@echo "The pdf file has been copied to ~/Lightandmatter/tahquitz/tahquitz.pdf"

single:
	# Extract a single page to post on mountainproject.
	# Change SINGLE above to the relevant page number.
	pdfseparate -f $(SINGLE) -l $(SINGLE) tahquitz.pdf foo.pdf
	pdftoppm -r 300 foo.pdf z
	convert z-1.ppm topo.jpg
	rm -f foo.pdf z-1.ppm
	@echo "Output is in topo.jpg."
	make clean

figures:
	# Create pdf versions of the svg figures.
	# For this to work, the scripts in the scripts directory need to be executable.
	# Inkscape 0.47 or later is required.
	# To force rendering of all figures, even if they seem up to date, do FORCE=1 make figures
	perl -e 'foreach my $$f(<figs/*.svg>) {system("scripts/render_one_figure.pl $$f $(FORCE)")}'

clean:
	rm -f *~ *.aux *.log *.idx *.toc *.ilg *.bak *.toc tahquitz.tex

