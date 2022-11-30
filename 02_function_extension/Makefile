
all: test examples

test:
	python3 compilerTests.py

examples: ex_mix ex_spill ex_non_spill

ex_%: %.s
	gcc $^ -o $@
	./$@; echo $$?

%.s: %.py
	python3 compiler.py $^ $@

clean:
	$(RM) compilation.log
	$(RM) *~ *.pyc *.s a.out ex_*
	$(RM) -r __pycache__ Languages/__pycache__