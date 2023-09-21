# DotChain - Python method chaining and piping with asyncio support.

# Install

`pip install dotchain`

# Usage

### Chain Synchronously

Call `.Result()` to get the value.

```python
value = DotChain(data | iterable).method().property.Result()
```

### Chain Asynchronously

Do not call `.Result()` when using `await`.

```python
value = await DotChain(data | iterable).method().property
```

> NOTE: Must be in an event loop to use `await`.

### Piping

`Pipe` can be called anywhere in the chain to start piping the data.

`Chain` can be called anywhere in the chain to start chaining the data again.

```python
# Piping
value = DotChain(data | iterable).Pipe.method().other_method().Result()

# Chaining and Piping
value = DotChain(data | iterable).method().property.Pipe.other_method().Chain.property.Result()
```

### Contexts

Contexts can be provided to resolve methods and properties so they can be used inline.

`With` can be called anywhere in the chain to add or clear contexts.

```python
import utils  # contains `log(...)`

value = DotChain(data | iterable).With(utils).method().log().Result()

value = DotChain(data | iterable).With({'utils': utils}).method().utils.log().Result()

value = DotChain(data | iterable).With(self).method().utils.log().Result()
```

### Call inline functions

```python
value = DotChain(data | iterable).method().Call(lambda item: item.property).Result()
```

# Examples

```python
from dotchain import DotChain
import log_utils

# Chaining
order = DotChain(user).get_order('123').cancel().Result()

# Chaining with Piping
email_result = DotChain(user).get_order('123').cancel().Pipe.send_email().Result()

# With lookup contexts
order = DotChain(user).With(log_utils).get_order('123').cancel().Pipe.log_cancel().Result()

order = DotChain(user).With({'log_it': lambda order: log_utils.log_cancel(order)}).Pipe.log_it().Result()

# Inline callables
order = DotChain(user).get_order('123').cancel().Pipe.Call(lambda order: log_utils.log_cancel(order)).Result()
```

> See [Tests](tests/dotchain/test_chain.py) for more examples and usage.
