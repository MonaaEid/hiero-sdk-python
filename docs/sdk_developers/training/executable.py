# _Executable Class Crash Course

## Table of Contents

- [Introduction to _Executable](#introduction-to-_executable)
- [Execution Flow](#execution-flow)
- [Retry Logic](#retry-logic)
- [Exponential backoff](#exponential-backoff)
- [Error Handling](#error-handling)
- [Logging & Debugging](#logging-&-debugging)
- [Practical Examples](#practical-examples)

## Introduction to _Executable
 * The _Executable class is the backbone of the Hedera SDK execution engine. It handles sending transactions and queries, retry logic, error mapping, and logging, allowing child classes (like Transaction and Query) to focus on business logic.



## Execution Flow

-How _execute(client) works
execution flow in the Hedera SDK:

The typical execution flow for transactions and queries using the Executable interface follows these steps:

1. **Build** → Create the transaction/query with required parameters
2. **FreezeWith(client)** → Locks the transaction for signing
3. **Sign(privateKey)** → Add required signatures
4. **Execute(client)** → Submit to the network
5. **GetReceipt(client)** → Confirm success/failure


-Node selection, gRPC method execution, and request building

-How child classes plug in via _make_request, _get_method, _map_response, etc.

## Retry Logic
 - Core Logic:
  1. Loop up to max_attempts times — The outer for loop tries the operation multiple times
  2. Exponential backoff — Each retry waits longer than the previous one
  3. Execute and check response — After execution, determine if we should retry, fail, or succeed
  4. Smart error handling — Different errors trigger different actions

<img width="500" height="500" alt="retry logic" src="https://github.com/user-attachments/assets/90f686e2-8867-4daa-a83f-9b0bd613fb16" />


**_Retry logic = Try the operation, wait progressively longer between attempts, pick a different node if needed, and give up after max attempts. This makes the system resilient to temporary network hiccups._**

-Handling network failures, gRPC errors, and node rotation

## Exponential backoff
Key Steps:

 * First retry: wait `_min_backoff` ms
 * Second retry: wait 2× that
 * Third retry: wait 4× that (doubling each time)
 * Stops growing at `_max_backoff`

  _(Why? Gives the network time to recover between attempts without hammering it immediately.)_

Execution States
  The response is checked via `_should_retry()` which returns one of four states:

| State          | Action                                  |                                        
| :--------------| :---------------------------------------| 
| **RETRY**      | `Wait (backoff), then loop again`       | 
| **FINISHED**   | `Success! Return the response`          | 
| **ERROR**      | `Permanent failure, raise exception`    |
| **EXPIRED**    | `Request expired, raise exception`      | 

Error Handling
```python
except grpc.RpcError as e:
    # Network/gRPC error occurred
    err_persistant = f"Status: {e.code()}, Details: {e.details()}"
    node = client.network._select_node()  # Switch nodes
    continue  # Retry with different node
```
If the [gRPC](https://en.wikipedia.org/wiki/GRPC) call itself fails, switch to a different network node and retry.

_##_ Error Handling

-Mapping network errors to Python exceptions

-Retryable vs fatal errors

-MaxAttemptsError and other exception cases

## Logging & Debugging

-Request ID tracking

-Attempt numbers, node info, backoff logging

-Tips for debugging transaction/query failures

## Practical Examples

-Illustrate how a child class (Transaction or Query) implements _Executable abstract methods

Step-by-step example of a transaction execution

-How the response is mapped back to a usable SDK object

-Visual Diagram (Optional but Recommended)

-Show _Executable as the parent class

-Child classes inheriting and plugging into the execution flow

-Flow of request → execution → retry → response mapping

Requirements

-Written in clear, beginner-friendly Markdown

-Include code snippets to illustrate concepts

-Include diagrams if possible

-Use Hedera-specific terminology appropriately

-Make it easy to follow for developers new to Hedera SDK

Optional: example scripts illustrating

