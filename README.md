# Extract code from RFC source

This is a simple python module that provides functions for extracting the
content of `<sourcecode>` or `<artwork>` blobs.

```python3
for blob in extract(filename, ["http-message"]):
	print(f"Found message at line {blob.line}")
	print(str(blob))
```

There is a command-line utility here as well.
