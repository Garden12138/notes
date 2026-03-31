# Two-stage notes

The first attempt at a two-stage implementation failed when stage 2 launched a new Chromium instance with the same profile while stage 1 still held the profile lock.

## Wrong pattern

- stage 1: switch to `最多点赞`
- stage 2: launch a second persistent context using the same profile

This failed with Chromium `ProcessSingleton` / `SingletonLock` errors.

## Correct pattern

Use one browser instance for both stages:
- stage 1: switch UI state to `最多点赞`
- stage 2: continue search collection and detail crawling in the same page/context

This keeps the filtered UI state alive and avoids profile locking issues.
