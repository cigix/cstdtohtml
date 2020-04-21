all: c17.html

%.html: %.pdf cstdtohtml
	./cstdtohtml $< $@

got.html: c17.pdf cstdtohtml
	./cstdtohtml $< got.html || true

check: got.html ref
	@head -n $$(wc -l ref | cut -d' ' -f1) got.html > got_trunc
	@diff -su ref got_trunc |& less -FS || true
	@rm got_trunc

new_ref: got.html
	cp got.html ref
