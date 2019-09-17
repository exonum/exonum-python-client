# Contributing guide

Generally, any kind of contibution is welcomed.

However, this project has some standards which you should not violate to get your improvements merged:

1. Use `black` for code formatting. Arguments for `black` are following: "black --check -l 120 . --exclude=".*_pb2.py"".

2. Use `pylint` for statical analysis. Arguments for `pylint` are following: "pylint exonum --max-line-length=120 --disable=fixme,bad-continuation,too-few-public-methods".

3. Use `mypy` for type checking. Arguments for `mypy` are following: "mypy --ignore-missing-imports --disallow-untyped-defs ./exonum ./examples"

4. Check that docs can be built with `sphinx` with no warnings. To check, run:

```sh
cd docs
make html
```

As you can see, those rules aren't applied to tests. That's because it will be too much useless overhead to keep test code passing all the lints.

However, use a common sense when updating test code and try to keep it readable.
