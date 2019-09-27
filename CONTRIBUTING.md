# Contribution Guide

Generally, any kind of contribution is welcome.

However, this project has some standards which you should not violate to get
your improvements merged:

1. Use `black` for code formatting. Arguments for `black` are as follows:
"black --check -l 120 . --exclude=".*_pb2.py"".

2. Use `pylint` for statical analysis. Arguments for `pylint` are following:
"pylint exonum --max-line-length=120
--disable=fixme,bad-continuation,too-few-public-methods".

3. Use `mypy` for type checking. Arguments for `mypy` are as follows:
"mypy --ignore-missing-imports --disallow-untyped-defs ./exonum ./examples".

4. Check that docs can be built with `sphinx` with no warnings. To check, run:

```sh
cd docs
make html
```

The mentioned rules do not apply to tests. Keeping test code passing all the
lints will cause too much overhead.

However, use common sense when updating test code and try to keep it readable.
