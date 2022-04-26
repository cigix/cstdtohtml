all: c17.html

%.html: %.pdf cstdtohtml $(wildcard *.py)
	./cstdtohtml $< $@

got.html: c17.pdf cstdtohtml
	./cstdtohtml $< got.html || true

check: got.html ref
	@head -n $$(wc -l ref | cut -d' ' -f1) got.html > got_trunc
	@diff --color=always -suw ref got_trunc |& less -FSR || true
	@rm got_trunc

new_ref: got.html
	cp got.html ref
