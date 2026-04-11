SOURCES = cstdtohtml $(wildcard *.py)

all: c23.html

%.html: %.pdf $(SOURCES)
	./cstdtohtml $< $@

%.md: %.pdf $(SOURCES)
	./cstdtohtml --md $< $@

clean:
	$(RM) -r __pycache__ .cstdtohtml_raw

########## Regression test suite

tests/out/%.html tests/out/%.md: tests/in/%.pdf $(SOURCES)
	./cstdtohtml --html --md $< tests/out/$*.html tests/out/$*.md >/dev/null

IN = $(wildcard tests/in/*.pdf)
OUT_FROM_IN =  $(IN:tests/in/%.pdf=tests/out/%.html)
OUT_FROM_IN += $(IN:tests/in/%.pdf=tests/out/%.md)

check: $(OUT_FROM_IN)
	@for out in $^; do \
	  base="$$(basename $$out)" \
	  ref="tests/ref/$$base"; \
	  if cmp "$$ref" "$$out" >/dev/null; then \
	    echo -e "[\e[92mOK\e[0m] $$base"; \
	  else \
	    echo -e "[\e[91mKO\e[0m] $$base"; \
	    diff --color=always -suw "$$ref" "$$out" |& less -FSR; \
	  fi \
	done

ref: $(OUT_FROM_IN)
	$(RM) -r tests/ref/*
	cp tests/out/* tests/ref/

##########

.PHONY: all clean check ref
