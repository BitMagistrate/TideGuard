# Summary

<!-- Short paragraph: what changed and why. Reference issue numbers. -->

## What changed

- ...

## How to verify

- [ ] `make lint`
- [ ] `make test`
- [ ] `make benchmark` (if model code changed)
- [ ] `pnpm --filter @tideguard/web build` (if web changed)
- [ ] Screenshots / videos attached (if UI changed)

## Risk register

- [ ] No new privacy-sensitive fields added.
- [ ] No new external network calls without timeout/retry.
- [ ] No new licence introduced.

## Checklist

- [ ] My commit messages are explanatory (not "fix").
- [ ] I have added or updated tests if applicable.
- [ ] I have run `pre-commit run --all-files` locally.
