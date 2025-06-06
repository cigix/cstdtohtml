all: c23.html

%.html: %.pdf cstdtohtml $(wildcard *.py)
	./cstdtohtml $< $@

got.html: c23.pdf cstdtohtml $(wildcard *.py)
	./cstdtohtml $< got.html || true

check: got.html ref
	@head -n $$(wc -l ref | cut -d' ' -f1) got.html > got_trunc
	@diff --color=always -suw ref got_trunc |& less -FSR || true
	@rm got_trunc

new_ref: got.html
	cp got.html ref

clean:
	$(RM) c23.html got.html ref
	$(RM) -r __pycache__

.PHONY: all check new_ref clean
